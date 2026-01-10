# app/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.db.engine import SessionLocal
from app.dependencies import require_dk_admin, get_current_user
from app.models.order import Order
from app.models.user import User
from app.models.institution import Institution
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderRead,
    OrderStatusUpdate,
    BulkDeleteRequest,
    OrderStatusUpdateById,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def calculate_total_from_allocation(staff_allocation: dict) -> int:
    """Calculate total portion from staff_allocation JSONB"""
    total = 0
    for category, data in staff_allocation.items():
        if isinstance(data, dict) and "total" in data:
            total += data["total"]
    return total


def order_to_dict_with_institution(order: Order) -> Dict[str, Any]:
    """Convert Order object to dict with institution_name included"""
    order_dict = {
        "order_id": order.order_id,
        "institution_id": order.institution_id,
        "institution_name": order.institution.name if order.institution else None,
        "order_date": order.order_date,
        "order_type": order.order_type,
        "total_portion": order.total_portion,
        "staff_allocation": order.staff_allocation,
        "menu_details": order.menu_details,
        "dropping_location_food": order.dropping_location_food,
        "status": order.status,
        "created_by": order.created_by,
        "submitted_at": order.submitted_at,
        "approved_by": order.approved_by,
        "approved_at": order.approved_at,
        "special_notes": order.special_notes,
        "is_locked": order.is_locked,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }
    return order_dict


# 3.1 Get Orders List
@router.get("/", response_model=list[OrderRead])
def get_orders(
    db: Session = Depends(get_db),
    institution_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    order_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = select(Order).options(joinedload(Order.institution))

    if institution_id:
        query = query.where(Order.institution_id == institution_id)
    if status:
        query = query.where(Order.status == status)
    if order_date:
        query = query.where(Order.order_date == order_date)

    query = query.order_by(Order.order_date.desc()).offset(skip).limit(limit)
    orders = db.execute(query).scalars().unique().all()

    # Manually construct response with institution_name
    result = [order_to_dict_with_institution(order) for order in orders]
    return result


# 3.2 Get Order Detail
@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: UUID, db: Session = Depends(get_db)):
    query = select(Order).options(joinedload(Order.institution)).where(Order.order_id == order_id)
    order = db.execute(query).scalars().unique().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_dict_with_institution(order)


# 3.3 Create Order (Draft)
@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    # TODO: Get from auth - using mock user for now
    created_by: UUID = Query(..., description="Creator user ID"),
):
    # Convert Pydantic StaffAllocationItem to dict for JSONB storage
    staff_allocation_dict = {
        k: v.dict() for k, v in order_data.staff_allocation.items()
    }

    # Convert menu_details to dict if provided
    menu_details_dict = None
    if order_data.menu_details:
        menu_details_dict = order_data.menu_details.dict()

    order = Order(
        institution_id=order_data.institution_id,
        order_date=order_data.order_date,
        order_type=order_data.order_type,
        total_portion=order_data.total_portion,
        staff_allocation=staff_allocation_dict,
        menu_details=menu_details_dict,
        dropping_location_food=order_data.dropping_location_food,
        special_notes=order_data.special_notes,
        created_by=created_by,
        status="DRAFT",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Load institution relationship and return with institution_name
    db.refresh(order, ["institution"])
    return order_to_dict_with_institution(order)


# 3.4 Submit Order
@router.post("/{order_id}/submit", response_model=OrderRead)
def submit_order(order_id: UUID, db: Session = Depends(get_db)):
    query = select(Order).options(joinedload(Order.institution)).where(Order.order_id == order_id)
    order = db.execute(query).scalars().unique().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=f"Only DRAFT orders can be submitted. Current status: {order.status}"
        )

    order.status = "ORDERED"
    order.submitted_at = datetime.utcnow()
    db.commit()
    return order_to_dict_with_institution(order)


# 3.5 Update Order (Draft Only or with RBAC for Edit Request)
@router.put("/{order_id}", response_model=OrderRead)
def update_order(
    order_id: UUID,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Order).options(joinedload(Order.institution)).where(Order.order_id == order_id)
    order = db.execute(query).scalars().unique().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # RBAC: Check if user is CLIENT_ADMIN
    if current_user.role == "CLIENT_ADMIN":
        # CLIENT_ADMIN can only edit if status is ORDERED and order_date < today
        if order.status != "ORDERED":
            raise HTTPException(
                status_code=403,
                detail=f"CLIENT_ADMIN can only edit orders with status ORDERED. Current status: {order.status}"
            )

        from datetime import date as date_module
        today = date_module.today()

        if order.order_date >= today:
            raise HTTPException(
                status_code=403,
                detail=f"Cannot edit: Order date ({order.order_date}) must be before today ({today})."
            )

        # Check if user belongs to the same institution
        if current_user.institution_id != order.institution_id:
            raise HTTPException(
                status_code=403,
                detail="CLIENT_ADMIN can only edit orders from their own institution"
            )

        # For CLIENT_ADMIN, automatically change status to REQUEST_TO_EDIT
        # and create an edit request
        # TODO: This will be implemented in a separate workflow
    else:
        # DK_ADMIN and SUPER_ADMIN can edit anytime
        pass

    # For now, only allow DRAFT updates
    # TODO: Implement edit request workflow for ORDERED status
    if order.status != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=f"Only DRAFT orders can be updated directly. Current status: {order.status}"
        )

    update_data = order_data.dict(exclude_unset=True)

    # Convert StaffAllocationItem to dict if present
    if "staff_allocation" in update_data and update_data["staff_allocation"]:
        staff_allocation_dict = {
            k: v.dict() if hasattr(v, "dict") else v
            for k, v in update_data["staff_allocation"].items()
        }
        update_data["staff_allocation"] = staff_allocation_dict

        # Recalculate total_portion if not explicitly provided
        if "total_portion" not in update_data:
            update_data["total_portion"] = calculate_total_from_allocation(staff_allocation_dict)

    # Convert menu_details to dict if present
    if "menu_details" in update_data and update_data["menu_details"]:
        if hasattr(update_data["menu_details"], "dict"):
            update_data["menu_details"] = update_data["menu_details"].dict()

    for key, value in update_data.items():
        setattr(order, key, value)

    db.commit()
    return order_to_dict_with_institution(order)


# 3.6 Delete Order (Draft Only)
@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: UUID, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=f"Only DRAFT orders can be deleted. Current status: {order.status}"
        )

    db.delete(order)
    db.commit()


# 3.7 Bulk Delete Orders (Admin Only)
@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_orders(
    bulk_request: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dk_admin),
):
    """
    Bulk delete orders. Only accessible to DK_ADMIN and SUPER_ADMIN.
    Can delete orders regardless of status.
    """
    if not bulk_request.order_ids:
        raise HTTPException(
            status_code=400,
            detail="No order IDs provided"
        )

    # Fetch all orders
    orders = db.execute(
        select(Order).where(Order.order_id.in_(bulk_request.order_ids))
    ).scalars().all()

    if not orders:
        raise HTTPException(
            status_code=404,
            detail="No orders found"
        )

    # Delete all orders
    for order in orders:
        db.delete(order)

    db.commit()


# PUT /api/order/status - Update Order Status (Admin Only)
@router.put("/status", response_model=OrderRead)
def update_order_status_by_body(
    status_data: OrderStatusUpdateById,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dk_admin),
):
    """
    Update order status via PUT /api/order/status with order_id in body.
    Only accessible to DK_ADMIN and SUPER_ADMIN.
    """
    query = select(Order).options(joinedload(Order.institution)).where(Order.order_id == status_data.order_id)
    order = db.execute(query).scalars().unique().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    valid_statuses = [
        "DRAFT", "REQUEST_TO_EDIT", "APPROVED_EDITED", "APPROVED",
        "REJECTED", "NOTED", "PROCESSING", "COOKING", "READY", "DELIVERED", "ORDERED"
    ]

    if status_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    order.status = status_data.status

    if status_data.status in ["APPROVED", "APPROVED_EDITED", "REJECTED", "NOTED"]:
        order.approved_by = current_user.id
        order.approved_at = datetime.utcnow()

    db.commit()
    return order_to_dict_with_institution(order)


# 5.1 Update Order Status (DK Admin) - Legacy endpoint with order_id in path
@router.put("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dk_admin),
):
    query = select(Order).options(joinedload(Order.institution)).where(Order.order_id == order_id)
    order = db.execute(query).scalars().unique().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    valid_statuses = [
        "DRAFT", "REQUEST_TO_EDIT", "APPROVED_EDITED", "APPROVED",
        "REJECTED", "NOTED", "PROCESSING", "COOKING", "READY", "DELIVERED", "ORDERED"
    ]

    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    order.status = status_update.status

    if status_update.status in ["APPROVED", "APPROVED_EDITED", "REJECTED", "NOTED"]:
        order.approved_by = current_user.id
        order.approved_at = datetime.utcnow()

    db.commit()
    return order_to_dict_with_institution(order)


# 5.2 Get Order Status Tracker
@router.get("/{order_id}/tracker")
def get_order_tracker(order_id: UUID, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Build status history/tracker
    tracker = {
        "order_id": str(order.order_id),
        "current_status": order.status,
        "timeline": [
            {"status": "DRAFT", "timestamp": order.created_at.isoformat(), "completed": True},
        ]
    }
    
    if order.submitted_at:
        tracker["timeline"].append({
            "status": "ORDERED",
            "timestamp": order.submitted_at.isoformat(),
            "completed": True
        })
    
    if order.approved_at:
        tracker["timeline"].append({
            "status": order.status,
            "timestamp": order.approved_at.isoformat(),
            "completed": True
        })

    return tracker


# PATCH /api/orders/{order_id}/notes - Update Special Notes (Admin Only)
@router.patch("/{order_id}/notes", response_model=OrderRead)
def update_special_notes(
    order_id: UUID,
    notes_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dk_admin),
):
    """
    Partial update for special_notes field only.
    Only accessible to DK_ADMIN and SUPER_ADMIN.
    """
    query = select(Order).options(joinedload(Order.institution)).where(Order.order_id == order_id)
    order = db.execute(query).scalars().unique().first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.special_notes = notes_data.get("special_notes")
    db.commit()
    return order_to_dict_with_institution(order)
