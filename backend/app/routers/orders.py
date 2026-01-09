# app/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.db.engine import SessionLocal
from app.dependencies import require_dk_admin
from app.models.order import Order
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderRead,
    OrderStatusUpdate,
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


# 3.1 Get Orders List
@router.get("/", response_model=list[OrderRead])
def get_orders(
    db: Session = Depends(get_db),
    institution_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = select(Order)
    
    if institution_id:
        query = query.where(Order.institution_id == institution_id)
    if status:
        query = query.where(Order.status == status)
    
    query = query.order_by(Order.order_date.desc()).offset(skip).limit(limit)
    orders = db.execute(query).scalars().all()
    return orders


# 3.2 Get Order Detail
@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: UUID, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


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
    
    order = Order(
        institution_id=order_data.institution_id,
        order_date=order_data.order_date,
        order_type=order_data.order_type,
        total_portion=order_data.total_portion,
        staff_allocation=staff_allocation_dict,
        dropping_location_food=order_data.dropping_location_food,
        special_notes=order_data.special_notes,
        created_by=created_by,
        status="DRAFT",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


# 3.4 Submit Order
@router.post("/{order_id}/submit", response_model=OrderRead)
def submit_order(order_id: UUID, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
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
    db.refresh(order)
    return order


# 3.5 Update Order (Draft Only)
@router.put("/{order_id}", response_model=OrderRead)
def update_order(
    order_id: UUID,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=f"Only DRAFT orders can be updated. Current status: {order.status}"
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
    
    for key, value in update_data.items():
        setattr(order, key, value)
    
    db.commit()
    db.refresh(order)
    return order


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


# 5.1 Update Order Status (DK Admin)
@router.put("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_dk_admin),
):
    order = db.get(Order, order_id)
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
    db.refresh(order)
    return order


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
