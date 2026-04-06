"""Validation helpers preserving COBOL business logic.

Mirrors the CSUTLDTC date validation (CEEDAYS IBM LE API wrapper) and
the amount format check from COTRN02C/COBIL00C.
"""

import re
from datetime import date
from decimal import Decimal, InvalidOperation


# COBOL amount pattern: optional sign, up to 8 digits, decimal, exactly 2 digits
# Maps to PIC S9(9)V99 COMP-3 but displayed as sign + 8d + '.' + 2d
_AMOUNT_PATTERN = re.compile(r"^[+-]?\d{1,8}\.\d{2}$")


def validate_amount_format(value: str) -> Decimal:
    """Validate and parse a COBOL-format amount string (-99999999.99).

    COTRN02C business rule:
        Amount must be in signed format: sign + 8 digits + decimal point + 2 digits.

    Returns:
        Parsed Decimal value.

    Raises:
        ValueError: if the format is invalid or out of range.
    """
    stripped = value.strip()
    if not _AMOUNT_PATTERN.match(stripped):
        raise ValueError(
            "Amount must be in format -99999999.99 "
            "(optional sign, up to 8 integer digits, decimal point, 2 decimal places)"
        )
    try:
        result = Decimal(stripped)
    except InvalidOperation:
        raise ValueError(f"Invalid amount value: {value!r}")

    if result < Decimal("-99999999.99") or result > Decimal("99999999.99"):
        raise ValueError("Amount out of allowed range -99999999.99 to +99999999.99")

    return result


def validate_merchant_id(merchant_id: str) -> str:
    """Validate merchant ID is all-numeric (COTRN02C business rule).

    COBOL: TRAN-MERCHANT-ID must be all numeric (9 digits).

    Raises:
        ValueError: if any non-digit characters are present.
    """
    if merchant_id and not merchant_id.isdigit():
        raise ValueError("Merchant ID must contain digits only")
    return merchant_id


def validate_date_string(date_str: str, field_name: str) -> date:
    """Validate a YYYY-MM-DD date string (mirrors CSUTLDTC date validation).

    COBOL CSUTLDTC wraps IBM LE CEEDAYS — validates that the date exists
    on the calendar. Python's date.fromisoformat achieves the same check.

    Raises:
        ValueError: if the date string is not a valid calendar date.
    """
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        raise ValueError(
            f"{field_name} must be a valid date in YYYY-MM-DD format, got: {date_str!r}"
        )
