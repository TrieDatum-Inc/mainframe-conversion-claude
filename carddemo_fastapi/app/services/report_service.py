"""Report service ported from CORPT00C.cbl.

CORPT00C: Submit reports (monthly, yearly, custom) with date range
          validation and a two-step confirmation flow.  For monthly
          and yearly report types the date range is auto-computed;
          for custom the caller supplies all six date components.
"""

import calendar
from datetime import date

from sqlalchemy.orm import Session

from app.exceptions import ValidationError
from app.services.validation import validate_date_components


def submit_report(
    db: Session,
    report_type: str,
    start_month: int | None = None,
    start_day: int | None = None,
    start_year: int | None = None,
    end_month: int | None = None,
    end_day: int | None = None,
    end_year: int | None = None,
    confirm: str = "N",
) -> dict:
    """Submit a report for printing, ported from CORPT00C.

    Flow:
    1. Validate report_type is 'monthly', 'yearly', or 'custom'
    2. For monthly/yearly: auto-compute date ranges
    3. For custom: validate all 6 date components
    4. Confirmation step
    5. Return success message

    Returns:
        dict with message (confirmation prompt or success).

    Raises:
        ValidationError: If report_type invalid, dates invalid,
                         or confirmation value invalid.
    """
    # 1. Validate report type
    valid_types = ("monthly", "yearly", "custom")
    if not report_type or report_type.lower() not in valid_types:
        raise ValidationError("Select a report type to print report")

    rtype = report_type.lower()
    today = date.today()

    # 2/3. Compute or validate date range
    if rtype == "monthly":
        # Auto-compute: first day to last day of current month
        start_month = today.month
        start_day = 1
        start_year = today.year
        end_month = today.month
        end_day = calendar.monthrange(today.year, today.month)[1]
        end_year = today.year

    elif rtype == "yearly":
        # Auto-compute: Jan 1 to Dec 31 of current year
        start_month = 1
        start_day = 1
        start_year = today.year
        end_month = 12
        end_day = 31
        end_year = today.year

    elif rtype == "custom":
        # Validate start date components
        is_valid, err = validate_date_components(
            start_month, start_day, start_year, prefix="Start Date - "
        )
        if not is_valid:
            raise ValidationError(err)

        # Validate end date components
        is_valid, err = validate_date_components(
            end_month, end_day, end_year, prefix="End Date - "
        )
        if not is_valid:
            raise ValidationError(err)

    # 4. Validate confirmation
    confirm_upper = confirm.upper() if confirm else ""
    if confirm_upper not in ("Y", "N", ""):
        raise ValidationError("Invalid value. Valid values are (Y/N)")

    if confirm_upper != "Y":
        return {
            "message": f"Please confirm to print the {rtype} report",
            "report_type": rtype,
            "start_date": {
                "month": start_month,
                "day": start_day,
                "year": start_year,
            },
            "end_date": {
                "month": end_month,
                "day": end_day,
                "year": end_year,
            },
        }

    # 5. Confirmed -- submit report
    display_type = rtype.capitalize()
    return {
        "message": f"{display_type} report submitted for printing",
        "report_type": rtype,
        "start_date": {
            "month": start_month,
            "day": start_day,
            "year": start_year,
        },
        "end_date": {
            "month": end_month,
            "day": end_day,
            "year": end_year,
        },
    }
