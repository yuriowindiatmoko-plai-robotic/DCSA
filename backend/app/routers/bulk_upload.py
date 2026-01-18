# app/routers/bulk_upload.py
"""Bulk upload endpoints for CSV order import."""
import io
import csv
import logging
from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.db.engine import SessionLocal
from app.models.order import Order
from app.models.institution import Institution
from app.models.user import User
from app.schemas.order import (
    BulkUploadPreviewResponse,
    BulkUploadPreviewItem,
    BulkUploadSubmitRequest,
    BulkUploadSubmitResponse,
    BulkUploadOrderItem
)
from app.utils.csv_parser import (
    validate_csv_headers,
    parse_csv_row,
    detect_csv_format,
    CSVParseError
)
from app.dependencies import get_current_user, require_dk_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders/bulk", tags=["bulk-upload"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/preview", response_model=BulkUploadPreviewResponse)
async def preview_bulk_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Preview bulk order upload from CSV file.

    Performs a dry-run validation of the CSV file and returns:
    - Parsed order data
    - Validation errors
    - Validation warnings
    - Detected CSV format

    Does NOT create any orders in the database.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    # Read file content
    try:
        content = await file.read()
        csv_text = content.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to read CSV file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read CSV file: {str(e)}"
        )

    # Parse CSV
    try:
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(csv_reader)
    except Exception as e:
        logger.error(f"Failed to parse CSV: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV format: {str(e)}"
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty"
        )

    # Get headers
    headers = list(rows[0].keys()) if rows else []

    # Validate headers
    is_valid, header_errors = validate_csv_headers(headers)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV headers: {'; '.join(header_errors)}"
        )

    # Detect CSV format
    csv_format = detect_csv_format(headers)

    # Parse rows
    preview_data: List[BulkUploadPreviewItem] = []
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    total_portion = 0
    valid_orders: List[Dict[str, Any]] = []  # Only valid orders ready for submit

    db = next(get_db())

    for idx, row in enumerate(rows, start=1):
        parsed_data, error_msg = parse_csv_row(row, idx, headers)

        if error_msg:
            validation_errors.append(error_msg)
            preview_data.append(
                BulkUploadPreviewItem(
                    row_number=idx,
                    institution_name=row.get('institution_name', ''),
                    order_date=row.get('order_date', ''),
                    total_portion=0,
                    dropping_location_food=row.get('dropping_location_main', ''),
                    staff_allocation={},
                    status="error",
                    error_message=error_msg
                )
            )
            continue

        # Verify institution exists
        institution = db.query(Institution).filter(
            Institution.name == parsed_data['institution_name']
        ).first()

        if not institution:
            error_msg = (
                f"Row {idx}: Institution '{parsed_data['institution_name']}' "
                f"not found in database"
            )
            validation_errors.append(error_msg)
            preview_data.append(
                BulkUploadPreviewItem(
                    row_number=idx,
                    institution_name=parsed_data['institution_name'],
                    order_date=parsed_data['order_date'],
                    total_portion=parsed_data['total_portion'],
                    dropping_location_food=parsed_data['dropping_location_food'],
                    staff_allocation=parsed_data['staff_allocation'],
                    menu_details=parsed_data['menu_details'],
                    special_notes=parsed_data['special_notes'],
                    status="error",
                    error_message=error_msg
                )
            )
            continue

        # Check for warnings (e.g., large orders)
        if parsed_data['total_portion'] > 500:
            validation_warnings.append(
                f"Row {idx}: Large order detected ({parsed_data['total_portion']} portions)"
            )
            item_status = "warning"
        else:
            item_status = "ok"

        # Add to preview data
        preview_data.append(
            BulkUploadPreviewItem(
                row_number=idx,
                institution_name=parsed_data['institution_name'],
                order_date=parsed_data['order_date'],
                order_type=parsed_data['order_type'],
                total_portion=parsed_data['total_portion'],
                dropping_location_food=parsed_data['dropping_location_food'],
                staff_allocation=parsed_data['staff_allocation'],
                menu_details=parsed_data['menu_details'],
                special_notes=parsed_data['special_notes'],
                status=item_status
            )
        )

        # Add to valid orders for submit
        valid_orders.append(BulkUploadOrderItem(
            institution_name=parsed_data['institution_name'],
            order_date=parsed_data['order_date'],
            order_type=parsed_data['order_type'],
            total_portion=parsed_data['total_portion'],
            dropping_location_food=parsed_data['dropping_location_food'],
            staff_allocation=parsed_data['staff_allocation'],
            menu_details=parsed_data['menu_details'],
            special_notes=parsed_data['special_notes']
        ))

        total_portion += parsed_data['total_portion']

    db.close()

    # Determine overall success
    has_critical_errors = any(
        err.startswith("Row") and "not found in database" not in err
        for err in validation_errors
    )

    # Filter out institution errors as warnings instead
    critical_errors = [
        err for err in validation_errors
        if "not found in database" not in err
    ]
    institution_warnings = [
        err for err in validation_errors
        if "not found in database" in err
    ]

    return BulkUploadPreviewResponse(
        success=len(critical_errors) == 0,
        csv_format=csv_format,
        parsed_rows=len(rows),
        preview_data=preview_data,
        validation_errors=critical_errors,
        validation_warnings=validation_warnings + institution_warnings,
        total_portion=total_portion,
        orders=valid_orders  # Include parsed orders ready for submit
    )


@router.post("/submit", response_model=BulkUploadSubmitResponse)
async def submit_bulk_upload(
    request: BulkUploadSubmitRequest,
    current_user: User = Depends(require_dk_admin)
):
    """
    Submit bulk order upload from parsed order objects.

    Creates all orders in the database within a transaction.
    If any order fails to create, the entire transaction is rolled back.

    Requires DK_ADMIN or SUPER_ADMIN role.
    """
    logger.info(f"📤 Received bulk upload request: {len(request.orders)} orders")

    if not request.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload must be confirmed"
        )

    if not request.orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Orders list is empty"
        )

    # Log the first order for debugging
    if request.orders:
        logger.info(f"📋 First order data: {request.orders[0]}")

    # Parse all orders
    orders_to_create = []
    total_portion = 0

    db = next(get_db())

    try:
        for idx, order_data in enumerate(request.orders, start=1):
            logger.info(f"Processing order {idx}: {order_data.institution_name}")

            # Pydantic model already validates required fields
            institution_name = order_data.institution_name

            # Get institution
            institution = db.query(Institution).filter(
                Institution.name == institution_name
            ).first()

            if not institution:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Order {idx}: Institution '{institution_name}' not found"
                )

            # Convert staff_allocation to dict for SQLAlchemy
            staff_alloc_dict = {
                role: {
                    "total": item.total,
                    "serving_type": item.serving_type,
                    "drop_off_location": item.drop_off_location
                }
                for role, item in order_data.staff_allocation.items()
            }

            # Convert menu_details to dict for SQLAlchemy
            menu_details_dict = None
            if order_data.menu_details:
                menu_details_dict = {
                    category: [
                        {"menu": item.menu, "total_qty": item.total_qty}
                        for item in items
                    ]
                    for category, items in order_data.menu_details.items()
                }

            # Create order object
            order = Order(
                institution_id=institution.institution_id,
                order_date=order_data.order_date,
                order_type=order_data.order_type,
                total_portion=order_data.total_portion,
                staff_allocation=staff_alloc_dict,
                menu_details=menu_details_dict,
                dropping_location_food=order_data.dropping_location_food,
                special_notes=order_data.special_notes,
                status="DRAFT",
                created_by=current_user.id
            )

            orders_to_create.append(order)
            total_portion += order_data.total_portion

        logger.info(f"Creating {len(orders_to_create)} orders...")

        # Bulk insert in transaction
        db.bulk_save_objects(orders_to_create, return_defaults=True)
        db.commit()

        # Get order IDs
        order_ids = [order.order_id for order in orders_to_create]

        logger.info(
            f"Bulk upload completed: {len(order_ids)} orders created, "
            f"{total_portion} total portions"
        )

        return BulkUploadSubmitResponse(
            success=True,
            orders_created=len(order_ids),
            order_ids=[str(order_id) for order_id in order_ids],
            total_portion=total_portion,
            message=f"Successfully created {len(order_ids)} orders"
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk upload failed: {str(e)}"
        )
    finally:
        db.close()
