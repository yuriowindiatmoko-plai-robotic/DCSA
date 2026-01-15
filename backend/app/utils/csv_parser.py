# app/utils/csv_parser.py
"""CSV parsing utilities for bulk order upload."""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVParseError(Exception):
    """Custom exception for CSV parsing errors."""
    pass


def parse_menu_items(cell_value: str) -> List[Dict[str, Any]]:
    """
    Parse menu items from CSV cell value.
    Format: "Kue Sus=110; Risoles=50" -> [{"menu": "Kue Sus", "total_qty": 110}, ...]
    """
    items_list = []

    if not isinstance(cell_value, str) or not cell_value.strip():
        return items_list

    # Split by semicolon
    entries = cell_value.split(';')

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        # Split by equals sign
        if '=' in entry:
            name, qty = entry.split('=', 1)
            try:
                items_list.append({
                    "menu": name.strip(),
                    "total_qty": int(qty.strip())
                })
            except ValueError:
                logger.warning(f"Could not parse menu item: {entry}")
                continue

    return items_list


def parse_staff_allocation(row: Dict[str, Any], columns: List[str]) -> Dict[str, Any]:
    """
    Parse staff allocation from CSV row dynamically.
    Detects columns matching pattern: sa_{role}_total, sa_{role}_type, sa_{role}_drop_loc

    Only includes roles where total > 0.

    Returns dict like: {"dosen": {"total": 20, "serving_type": "Box", "drop_off_location": "Pantry"}}
    """
    allocation = {}

    # Find all columns matching the pattern sa_*_total
    potential_roles = [
        col for col in columns
        if col.startswith('sa_') and col.endswith('_total')
    ]

    for col_total in potential_roles:
        # Extract role name: sa_dosen_total -> dosen
        role_name = col_total.replace('sa_', '').replace('_total', '')

        # Get total value
        total_val = row.get(col_total)

        # Skip if no total or total is 0 or empty
        if total_val is None or total_val == '':
            continue

        try:
            total_val = int(total_val)
            if total_val <= 0:
                continue
        except (ValueError, TypeError):
            logger.warning(f"Invalid total value for {role_name}: {total_val}")
            continue

        # Find matching type and location columns
        col_type = f"sa_{role_name}_type"
        col_loc = f"sa_{role_name}_drop_loc"

        # Get values (use None if missing)
        serving_type = row.get(col_type)
        drop_off_location = row.get(col_loc)

        # Only add if we have the required fields
        if serving_type and drop_off_location:
            allocation[role_name] = {
                "total": total_val,
                "serving_type": str(serving_type),
                "drop_off_location": str(drop_off_location)
            }
        else:
            logger.warning(
                f"Skipping {role_name}: missing type or location "
                f"(type={serving_type}, loc={drop_off_location})"
            )

    return allocation


def validate_csv_headers(headers: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate CSV headers and detect format.
    Returns: (is_valid, error_messages)
    """
    required_base_columns = [
        'no', 'institution_name', 'order_date', 'total_portions', 'dropping_location_main'
    ]

    errors = []

    # Check for required base columns
    for col in required_base_columns:
        if col not in headers:
            errors.append(f"Missing required column: {col}")

    # Check that at least one staff allocation column exists
    has_staff_allocation = any(
        col.startswith('sa_') and col.endswith('_total')
        for col in headers
    )

    if not has_staff_allocation:
        errors.append("No staff allocation columns found (e.g., sa_dosen_total)")

    return len(errors) == 0, errors


def parse_csv_row(
    row: Dict[str, Any],
    row_number: int,
    columns: List[str]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse a single CSV row into order data format.

    Returns: (parsed_data, error_message)
    """
    errors = []

    # Extract base fields
    institution_name = row.get('institution_name')
    order_date_str = row.get('order_date')
    total_portions = row.get('total_portions')
    dropping_location_main = row.get('dropping_location_main')
    special_notes = row.get('special_notes', '')

    # Validate required fields
    if not institution_name:
        errors.append("institution_name is required")
    if not order_date_str:
        errors.append("order_date is required")
    if not total_portions:
        errors.append("total_portions is required")
    if not dropping_location_main:
        errors.append("dropping_location_main is required")

    if errors:
        return None, f"Row {row_number}: " + "; ".join(errors)

    # Parse date
    try:
        order_date = datetime.strptime(str(order_date_str), '%Y-%m-%d').date()
    except ValueError:
        return None, f"Row {row_number}: Invalid date format '{order_date_str}'. Use YYYY-MM-DD."

    # Parse total portions
    try:
        total_portions = int(total_portions)
        if total_portions <= 0:
            return None, f"Row {row_number}: total_portions must be greater than 0"
    except (ValueError, TypeError):
        return None, f"Row {row_number}: Invalid total_portions value '{total_portions}'"

    # Parse staff allocation
    staff_allocation = parse_staff_allocation(row, columns)
    if not staff_allocation:
        return None, f"Row {row_number}: No valid staff allocation found"

    # Verify total portions matches sum of staff allocation
    calculated_total = sum(
        item['total'] for item in staff_allocation.values()
    )

    if calculated_total != total_portions:
        return None, (
            f"Row {row_number}: total_portions ({total_portions}) does not match "
            f"sum of staff allocation ({calculated_total})"
        )

    # Parse menu details
    menu_details = {}

    # Parse snack items
    snack_items = row.get('menu_snack_items')
    if snack_items:
        menu_details['snack'] = parse_menu_items(snack_items)

    # Parse beverage items
    beverage_items = row.get('menu_beverage_items')
    if beverage_items:
        menu_details['beverages'] = parse_menu_items(beverage_items)

    # Parse heavy meal items
    heavy_meal_items = row.get('menu_heavy_meal_items')
    if heavy_meal_items:
        menu_details['heavy_meal'] = parse_menu_items(heavy_meal_items)

    # Build parsed data
    parsed_data = {
        'row_number': row_number,
        'institution_name': institution_name,
        'order_date': order_date.isoformat(),
        'order_type': 'REGULAR',
        'total_portion': total_portions,
        'dropping_location_food': dropping_location_main,
        'staff_allocation': staff_allocation,
        'menu_details': menu_details if menu_details else None,
        'special_notes': special_notes if special_notes else None
    }

    return parsed_data, None


def detect_csv_format(headers: List[str]) -> str:
    """
    Detect CSV format based on column headers.
    Returns format identifier like 'sample_1', 'sample_2', etc.
    """
    # Count staff allocation groups
    staff_groups = set()
    for col in headers:
        if col.startswith('sa_') and col.endswith('_total'):
            role = col.replace('sa_', '').replace('_total', '')
            staff_groups.add(role)

    # Determine format based on staff groups
    if staff_groups == {'dosen', 'siswa', 'staff', 'satpam'}:
        return 'sample_1'

    if staff_groups == {'umum'}:
        return 'sample_2'

    if staff_groups == {'dosen', 'siswa', 'staff', 'satpam', 'tamu', 'kasir'}:
        return 'sample_3'

    if staff_groups == {'peserta', 'panitia'}:
        return 'sample_4'

    if staff_groups == {'umum'}:
        # Check if this is the simplified sample 5
        has_minimal_menu = all(
            col in headers
            for col in ['menu_snack_items', 'menu_beverage_items', 'menu_heavy_meal_items']
        )
        if has_minimal_menu:
            return 'sample_5'

    # Default to generic
    return 'generic'
