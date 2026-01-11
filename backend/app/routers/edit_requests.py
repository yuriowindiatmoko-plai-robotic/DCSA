# app/routers/edit_requests.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.db.engine import SessionLocal
from app.models.order import Order
from app.models.edit_request import EditRequest
from app.schemas.edit_request import (
    EditRequestCreate,
    EditRequestRead,
    EditRequestAcceptWithNote,
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


def determine_sla_status(order: Order) -> str:
    """
    Determine SLA status based on order submission time.
    REGULAR if within 48 hours of order_date, NOTED otherwise.
    """
    if order.submitted_at:
        # Check if edit request is within 48 hours before order_date
        deadline = datetime.combine(order.order_date, datetime.min.time()) - timedelta(hours=48)
        if datetime.utcnow() <= deadline:
            return "REGULAR"
    return "NOTED"


def merge_changes_to_order(order: Order, requested_changes: list, db: Session):
    """
    Merge requested_changes array into order.
    requested_changes format: [{"staff_allocation_changes": {...}}, {"menu_details_changes": {...}}]
    - Index 0: staff_allocation_changes (dict)
    - Index 1: menu_details_changes (dict)
    """
    # Index 0: staff_allocation_changes
    if len(requested_changes) > 0 and "staff_allocation_changes" in requested_changes[0]:
        order.staff_allocation = requested_changes[0]["staff_allocation_changes"]
        order.total_portion = calculate_total_from_allocation(requested_changes[0]["staff_allocation_changes"])

    # Index 1: menu_details_changes
    if len(requested_changes) > 1 and "menu_details_changes" in requested_changes[1]:
        order.menu_details = requested_changes[1]["menu_details_changes"]

    order.status = "APPROVED_EDITED"
    order.updated_at = datetime.utcnow()


# 4.1 Create Edit Request
@router.post("/", response_model=EditRequestRead, status_code=status.HTTP_201_CREATED)
def create_edit_request(
    edit_request_data: EditRequestCreate,
    db: Session = Depends(get_db),
    submitted_by: UUID = Query(..., description="Submitter user ID"),
):
    """
    Create edit request with simplified payload.

    Payload format:
    {
      "order_id": "{order_id}",
      "requested_changes": [
        { "staff_allocation_changes": { ...jsonb_content... } },
        { "menu_details_changes": { ...jsonb_content... } }
      ]
    }

    Auto-populates original_breakdown from the orders table.
    """
    # Get the order
    order = db.get(Order, edit_request_data.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check if order can be edited (not in final states)
    non_editable_statuses = ["DELIVERED", "COOKING", "READY"]
    if order.status in non_editable_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot create edit request for order with status: {order.status}"
        )

    # Determine SLA status
    sla_status = determine_sla_status(order)

    # Auto-populate original_breakdown from orders table
    # Copy staff_allocation and menu_details from the order
    original_breakdown = [
        {"staff_allocation": order.staff_allocation},
        {"menu_details": order.menu_details or {}}
    ]

    edit_request = EditRequest(
        order_id=order.order_id,
        institution_id=order.institution_id,
        original_breakdown=original_breakdown,
        requested_changes=edit_request_data.requested_changes,
        sla_status=sla_status,
        approval_status="PENDING",
        submitted_by=submitted_by,
    )

    # Update order status to indicate edit request
    order.status = "REQUEST_TO_EDIT"

    db.add(edit_request)
    db.commit()
    db.refresh(edit_request)
    return edit_request


# 4.2 Get Edit Request List
@router.get("/", response_model=list[EditRequestRead])
def get_edit_requests(
    db: Session = Depends(get_db),
    institution_id: Optional[UUID] = Query(None),
    order_id: Optional[UUID] = Query(None),
    created_at: Optional[datetime] = Query(None, description="Filter by created_at timestamp"),
    updated_at: Optional[datetime] = Query(None, description="Filter by updated_at timestamp"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get edit requests with optional filters.

    When order_id is provided, returns the most recent edit request for that order.
    Supports filtering by created_at and updated_at timestamps.
    """
    query = select(EditRequest)

    if institution_id:
        query = query.where(EditRequest.institution_id == institution_id)
    if order_id:
        query = query.where(EditRequest.order_id == order_id)
    if created_at:
        query = query.where(EditRequest.created_at >= created_at)
    if updated_at:
        query = query.where(EditRequest.updated_at >= updated_at)

    # Order by created_at DESC to get most recent first
    query = query.order_by(EditRequest.created_at.desc()).offset(skip).limit(limit)
    edit_requests = db.execute(query).scalars().all()
    return edit_requests


# 4.3 Get Pending Edit Requests (DK Admin)
@router.get("/pending", response_model=list[EditRequestRead])
def get_pending_edit_requests(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    query = (
        select(EditRequest)
        .where(EditRequest.approval_status == "PENDING")
        .order_by(EditRequest.submitted_at.asc())
        .offset(skip)
        .limit(limit)
    )
    edit_requests = db.execute(query).scalars().all()
    return edit_requests


# 4.4 Approve Edit Request
@router.post("/{edit_request_id}/approve", response_model=EditRequestRead)
def approve_edit_request(
    edit_request_id: UUID,
    db: Session = Depends(get_db),
    approved_by: UUID = Query(..., description="Admin user ID"),
):
    edit_request = db.get(EditRequest, edit_request_id)
    if not edit_request:
        raise HTTPException(status_code=404, detail="Edit request not found")
    
    if edit_request.approval_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Edit request is not pending. Current status: {edit_request.approval_status}"
        )
    
    # Get the order and merge changes
    order = db.get(Order, edit_request.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Merge requested_changes into order's staff_allocation
    merge_changes_to_order(order, edit_request.requested_changes, db)
    
    # Update edit request
    edit_request.approval_status = "APPROVED"
    edit_request.approved_by = approved_by
    edit_request.approved_at = datetime.utcnow()
    
    # Update order approval info
    order.approved_by = approved_by
    order.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(edit_request)
    return edit_request


# 4.5 Reject Edit Request
@router.post("/{edit_request_id}/reject", response_model=EditRequestRead)
def reject_edit_request(
    edit_request_id: UUID,
    db: Session = Depends(get_db),
    approved_by: UUID = Query(..., description="Admin user ID"),
):
    edit_request = db.get(EditRequest, edit_request_id)
    if not edit_request:
        raise HTTPException(status_code=404, detail="Edit request not found")
    
    if edit_request.approval_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Edit request is not pending. Current status: {edit_request.approval_status}"
        )
    
    # Get the order and revert status
    order = db.get(Order, edit_request.order_id)
    if order:
        order.status = "REJECTED"
    
    edit_request.approval_status = "REJECTED"
    edit_request.approved_by = approved_by
    edit_request.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(edit_request)
    return edit_request


# 4.6 Accept With Note (For NOTED SLA Status)
@router.post("/{edit_request_id}/accept-with-note", response_model=EditRequestRead)
def accept_with_note(
    edit_request_id: UUID,
    note_data: EditRequestAcceptWithNote,
    db: Session = Depends(get_db),
    approved_by: UUID = Query(..., description="Admin user ID"),
):
    edit_request = db.get(EditRequest, edit_request_id)
    if not edit_request:
        raise HTTPException(status_code=404, detail="Edit request not found")
    
    if edit_request.approval_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Edit request is not pending. Current status: {edit_request.approval_status}"
        )
    
    # Get the order and merge changes
    order = db.get(Order, edit_request.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Merge requested_changes into order's staff_allocation
    merge_changes_to_order(order, edit_request.requested_changes, db)
    order.status = "NOTED"
    
    # Update edit request
    edit_request.approval_status = "ACCEPTED_WITH_NOTE"
    edit_request.approval_comment = note_data.approval_comment
    edit_request.approved_by = approved_by
    edit_request.approved_at = datetime.utcnow()
    
    # Update order approval info
    order.approved_by = approved_by
    order.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(edit_request)
    return edit_request
