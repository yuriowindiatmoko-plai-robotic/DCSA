# app/schemas/edit_request.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict, List
from uuid import UUID


class EditRequestCreate(BaseModel):
    """Simplified schema for creating edit requests"""
    order_id: UUID
    requested_changes: List[Dict[str, Any]]  # Array of changes: [{"staff_allocation_changes": {...}}, {"menu_details_changes": {...}}]


class EditRequestRead(BaseModel):
    edit_request_id: UUID
    order_id: UUID
    institution_id: UUID
    original_breakdown: Dict[str, Any]
    requested_changes: Dict[str, Any]
    change_reason: Optional[str]
    submitted_at: datetime
    sla_status: str
    approval_status: str
    submitted_by: UUID
    approved_by: Optional[UUID]
    approval_comment: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class EditRequestApproval(BaseModel):
    """For simple approve/reject"""
    pass


class EditRequestAcceptWithNote(BaseModel):
    approval_comment: str

