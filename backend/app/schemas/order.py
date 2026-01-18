# app/schemas/order.py
from pydantic import BaseModel, root_validator
from datetime import date, datetime
from typing import Optional, Any, Dict, List
from uuid import UUID


class StaffAllocationItem(BaseModel):
    total: int
    drop_off_location: str
    serving_type: str


class MenuItem(BaseModel):
    menu: str
    total_qty: int


class MenuDetails(BaseModel):
    heavy_meal: List[MenuItem] = []
    snack: List[MenuItem] = []
    beverages: List[MenuItem] = []


class OrderBase(BaseModel):
    order_date: date
    order_type: str = "REGULAR"
    total_portion: int
    staff_allocation: Dict[str, StaffAllocationItem]
    menu_details: Optional[MenuDetails] = None
    dropping_location_food: Optional[str] = None
    special_notes: Optional[str] = None

    @root_validator
    def validate_portion_sum(cls, values):
        """Ensure total_portion equals sum of all staff_allocation totals"""
        staff_allocation = values.get("staff_allocation", {})
        total_portion = values.get("total_portion", 0)
        
        if staff_allocation:
            calculated_sum = sum(
                item.total if hasattr(item, "total") else item.get("total", 0)
                for item in staff_allocation.values()
            )
            if calculated_sum != total_portion:
                raise ValueError(
                    f"total_portion ({total_portion}) must equal sum of staff_allocation totals ({calculated_sum})"
                )
        return values


class OrderCreate(OrderBase):
    institution_id: UUID


class OrderUpdate(BaseModel):
    order_date: Optional[date] = None
    order_type: Optional[str] = None
    total_portion: Optional[int] = None
    staff_allocation: Optional[Dict[str, StaffAllocationItem]] = None
    menu_details: Optional[MenuDetails] = None
    dropping_location_food: Optional[str] = None
    special_notes: Optional[str] = None

    @root_validator
    def validate_portion_sum_if_both_present(cls, values):
        """If both total_portion and staff_allocation are provided, validate sum"""
        staff_allocation = values.get("staff_allocation")
        total_portion = values.get("total_portion")
        
        if total_portion is not None and staff_allocation is not None:
            calculated_sum = sum(
                item.total if hasattr(item, "total") else item.get("total", 0)
                for item in staff_allocation.values()
            )
            if calculated_sum != total_portion:
                raise ValueError(
                    f"total_portion ({total_portion}) must equal sum of staff_allocation totals ({calculated_sum})"
                )
        return values


class OrderRead(BaseModel):
    order_id: UUID
    institution_id: UUID
    institution_name: Optional[str] = None
    order_date: date
    order_type: str
    total_portion: int
    staff_allocation: Dict[str, Any]
    menu_details: Optional[Dict[str, Any]] = None
    dropping_location_food: Optional[str]
    status: str
    created_by: UUID
    submitted_at: Optional[datetime]
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    special_notes: Optional[str]
    is_locked: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class OrderStatusUpdate(BaseModel):
    status: str


class OrderSubmit(BaseModel):
    """Empty body - just triggers submission"""
    pass


class BulkDeleteRequest(BaseModel):
    order_ids: List[UUID]


class OrderStatusUpdateById(BaseModel):
    order_id: UUID
    status: str


# ============================================================================
# BULK UPLOAD SCHEMAS
# ============================================================================

class BulkUploadStaffAllocation(BaseModel):
    """Staff allocation for bulk upload (simplified, no UUID)."""
    total: int
    serving_type: str
    drop_off_location: str


class BulkUploadMenuItem(BaseModel):
    """Menu item for bulk upload (simplified, no UUID)."""
    menu: str
    total_qty: int


class BulkUploadOrderItem(BaseModel):
    """Single order item for bulk upload."""
    institution_name: str
    order_date: str
    order_type: str = "REGULAR"
    total_portion: int
    dropping_location_food: str
    staff_allocation: Dict[str, BulkUploadStaffAllocation]
    menu_details: Optional[Dict[str, List[BulkUploadMenuItem]]] = None
    special_notes: Optional[str] = None


class BulkUploadPreviewItem(BaseModel):
    """Single item in bulk upload preview."""
    row_number: int
    institution_name: str
    order_date: str
    order_type: str = "REGULAR"
    total_portion: int
    dropping_location_food: str
    staff_allocation: Dict[str, Any]
    menu_details: Optional[Dict[str, Any]] = None
    special_notes: Optional[str] = None
    status: str = "ok"  # ok, warning, error
    error_message: Optional[str] = None


class BulkUploadPreviewResponse(BaseModel):
    """Response from bulk upload preview endpoint."""
    success: bool
    csv_format: str
    parsed_rows: int
    preview_data: List[BulkUploadPreviewItem]
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    total_portion: int = 0
    orders: List[BulkUploadOrderItem] = []  # Parsed orders ready for submit


class BulkUploadSubmitRequest(BaseModel):
    """Request for bulk upload submit."""
    orders: List[BulkUploadOrderItem]
    confirmed: bool = True


class BulkUploadSubmitResponse(BaseModel):
    """Response from bulk upload submit."""
    success: bool
    orders_created: int
    order_ids: List[UUID]
    total_portion: int
    message: str = ""

