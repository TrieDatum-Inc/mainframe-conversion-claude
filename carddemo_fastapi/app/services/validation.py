"""Validation utilities ported from COBOL copybooks.

Ports validation logic from:
- CSUTLDWY.cpy / CSUTLDPY.cpy: Date validation with leap year support
- COACTUPC.cbl: SSN, phone, signed numeric, alpha/alphanum field validation
- COCRDUPC.cbl: Card name (alpha+spaces), expiry month/year validation
- CORPT00C.cbl: Report date range validation

All error messages are preserved verbatim from the COBOL source.
"""

import calendar
from decimal import Decimal, InvalidOperation
from typing import Tuple, Optional


def validate_date_ccyymmdd(date_str: str) -> Tuple[bool, str]:
    """Validate a date in CCYYMMDD or YYYY-MM-DD format.

    Ports CSUTLDWY.cpy EDIT-DATE-CCYYMMDD logic including:
    - Month must be 1-12
    - Day must be valid for the month
    - Leap year handling for February
    - Year must be reasonable (1900-2099)

    Returns:
        (is_valid, error_message)
    """
    if not date_str or date_str.strip() == "":
        return False, "Date can NOT be empty"

    # Handle both CCYYMMDD and YYYY-MM-DD formats
    clean = date_str.replace("-", "").strip()

    if len(clean) != 8:
        return False, "Not a valid date format"

    if not clean.isdigit():
        return False, "Not a valid date - must be numeric"

    year = int(clean[0:4])
    month = int(clean[4:6])
    day = int(clean[6:8])

    # Year validation (EDIT-YEAR-CCYY)
    if year < 1900 or year > 2099:
        return False, "Not a valid Year"

    # Month validation (EDIT-MONTH)
    if month < 1 or month > 12:
        return False, "Not a valid Month"

    # Day validation (EDIT-DAY) with leap year from CSUTLDWY
    if day < 1:
        return False, "Not a valid Day"

    # Get max days for month (handles leap year via calendar module)
    max_day = calendar.monthrange(year, month)[1]
    if day > max_day:
        return False, "Not a valid Day"

    return True, ""


def validate_date_components(
    month: Optional[int],
    day: Optional[int],
    year: Optional[int],
    prefix: str = "",
) -> Tuple[bool, str]:
    """Validate individual date components (month, day, year).

    Ports CORPT00C report date validation logic.

    Args:
        month: Month (1-12)
        day: Day (1-31, validated against month)
        year: 4-digit year
        prefix: Error message prefix (e.g. 'Start Date - ' or 'End Date - ')
    """
    if month is None:
        return False, f"{prefix}Month can NOT be empty"
    if day is None:
        return False, f"{prefix}Day can NOT be empty"
    if year is None:
        return False, f"{prefix}Year can NOT be empty"

    if not isinstance(month, int) or month < 1 or month > 12:
        return False, f"{prefix}Not a valid Month"

    if not isinstance(year, int) or year < 1900 or year > 2099:
        return False, f"{prefix}Not a valid Year"

    if not isinstance(day, int) or day < 1:
        return False, f"{prefix}Not a valid Day"

    max_day = calendar.monthrange(year, month)[1]
    if day > max_day:
        return False, f"{prefix}Not a valid Day"

    return True, ""


def validate_us_phone(phone: str) -> Tuple[bool, str]:
    """Validate US phone number format.

    Ports WS-EDIT-US-PHONE-NUM from COACTUPC:
    - Format: (xxx)xxx-xxxx or xxx-xxx-xxxx or 10 digits
    - Area code cannot start with 0 or 1

    Returns:
        (is_valid, error_message)
    """
    if not phone or phone.strip() == "":
        return True, ""  # Phone is optional

    # Strip formatting characters
    digits = "".join(c for c in phone if c.isdigit())

    if len(digits) != 10:
        return False, "Phone number must be 10 digits"

    area_code = int(digits[0:3])
    if area_code < 200:
        return False, "Phone Area code is not valid"

    return True, ""


def validate_ssn(ssn_str: str) -> Tuple[bool, str]:
    """Validate US Social Security Number.

    Ports WS-EDIT-US-SSN from COACTUPC:
    - Must be 9 digits
    - First 3 digits: cannot be 000, 666, or 900-999
    - Middle 2 digits: cannot be 00
    - Last 4 digits: cannot be 0000

    Returns:
        (is_valid, error_message)
    """
    if not ssn_str or ssn_str.strip() == "":
        return True, ""  # SSN is optional in some contexts

    digits = ssn_str.strip()
    if not digits.isdigit() or len(digits) != 9:
        return False, "SSN must be 9 digits"

    part1 = int(digits[0:3])
    part2 = int(digits[3:5])
    part3 = int(digits[5:9])

    if part1 == 0 or part1 == 666 or (900 <= part1 <= 999):
        return False, "SSN first part is not valid"

    if part2 == 0:
        return False, "SSN middle part is not valid"

    if part3 == 0:
        return False, "SSN last part is not valid"

    return True, ""


def validate_signed_decimal(value: str) -> Tuple[bool, Decimal, str]:
    """Validate a signed decimal number matching COBOL PIC S9(n)V99.

    Ports WS-EDIT-SIGNED-NUMBER-9V2-X from COACTUPC.
    Allows optional sign prefix (+/-) and decimal point.

    Returns:
        (is_valid, parsed_value, error_message)
    """
    if not value or value.strip() == "":
        return False, Decimal("0"), "Amount can NOT be empty"

    clean = value.strip()
    try:
        result = Decimal(clean)
        return True, result, ""
    except InvalidOperation:
        return False, Decimal("0"), "Not a valid numeric value"


def validate_alpha_only(value: str) -> Tuple[bool, str]:
    """Validate that a string contains only alphabetic characters and spaces.

    Ports FLG-ALPHA-ISVALID from COACTUPC and COCRDUPC card name validation.

    Returns:
        (is_valid, error_message)
    """
    if not value or value.strip() == "":
        return True, ""

    for ch in value:
        if not (ch.isalpha() or ch == " "):
            return False, "can only contain alphabets and spaces"

    return True, ""


def validate_yes_no(value: str) -> Tuple[bool, str]:
    """Validate that a value is Y or N.

    Ports COACTUPC account status and COCRDUPC card status validation.

    Returns:
        (is_valid, error_message)
    """
    if value and value.upper() not in ("Y", "N"):
        return False, "must be Y or N"
    return True, ""


def validate_confirmation(value: str) -> Tuple[bool, str]:
    """Validate confirmation field (Y/N).

    Ports confirmation logic from COBIL00C, COTRN02C, CORPT00C.

    Returns:
        (is_valid, error_message)
    """
    if not value or value.strip() == "" or value.strip().upper() in ("Y", "N"):
        return True, ""
    return False, "Invalid value. Valid values are (Y/N)"


def validate_acct_id(acct_id_str: str) -> Tuple[bool, int, str]:
    """Validate account ID is numeric and non-zero 11-digit.

    Ports COACTVWC / COACTUPC account ID validation.

    Returns:
        (is_valid, parsed_value, error_message)
    """
    if not acct_id_str or acct_id_str.strip() == "":
        return False, 0, "Acct ID can NOT be empty"

    clean = acct_id_str.strip()
    if not clean.isdigit():
        return False, 0, "Acct ID must be Numeric"

    value = int(clean)
    if value == 0:
        return False, 0, "Acct ID must be non-zero"

    return True, value, ""


def validate_card_num(card_num_str: str) -> Tuple[bool, str, str]:
    """Validate card number is 16-digit numeric.

    Ports COCRDSLC / COCRDUPC card number validation.

    Returns:
        (is_valid, cleaned_value, error_message)
    """
    if not card_num_str or card_num_str.strip() == "":
        return False, "", "Card number can NOT be empty"

    clean = card_num_str.strip()
    if not clean.isdigit():
        return False, "", "Card number must be Numeric"

    if len(clean) != 16:
        return False, "", "Card number if supplied must be 16 digit"

    return True, clean, ""


def validate_card_expiry_month(month_str: str) -> Tuple[bool, str]:
    """Validate card expiry month (1-12).

    Ports COCRDUPC validation.
    """
    if not month_str or month_str.strip() == "":
        return True, ""

    clean = month_str.strip()
    if not clean.isdigit():
        return False, "Card expiry month must be between 1 and 12"

    month = int(clean)
    if month < 1 or month > 12:
        return False, "Card expiry month must be between 1 and 12"

    return True, ""


def validate_card_expiry_year(year_str: str) -> Tuple[bool, str]:
    """Validate card expiry year (1950-2099).

    Ports COCRDUPC validation.
    """
    if not year_str or year_str.strip() == "":
        return True, ""

    clean = year_str.strip()
    if not clean.isdigit():
        return False, "Invalid card expiry year"

    year = int(clean)
    if year < 1950 or year > 2099:
        return False, "Invalid card expiry year"

    return True, ""


def validate_not_empty(value: str, field_name: str) -> Tuple[bool, str]:
    """Validate that a field is not empty or spaces.

    Generic validation used across multiple COBOL programs.
    """
    if not value or value.strip() == "":
        return False, f"{field_name} can NOT be empty"
    return True, ""


def validate_numeric_string(value: str, field_name: str) -> Tuple[bool, str]:
    """Validate that a string contains only numeric characters.

    Used for transaction IDs, merchant IDs, etc.
    """
    if not value or value.strip() == "":
        return True, ""

    if not value.strip().isdigit():
        return False, f"{field_name} must be Numeric"

    return True, ""
