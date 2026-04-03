"""Formatting utilities.

These replicate COBOL STRING / INSPECT formatting logic used in screen population.
"""

from app.schemas.account import PhoneInput


def format_ssn(ssn_raw: str | None) -> str | None:
    """Format 9-digit SSN string as XXX-XX-XXXX.

    Replicates the STRING statement in COACTVWC 1200-SETUP-SCREEN-VARS:
        STRING CUST-SSN(1:3) '-' CUST-SSN(4:2) '-' CUST-SSN(6:4)
        DELIMITED BY SIZE INTO ACSTSSNO.

    Returns None if input is None or too short.
    """
    if not ssn_raw:
        return None
    digits = ssn_raw.strip().zfill(9)
    if len(digits) < 9:
        return ssn_raw
    return f"{digits[0:3]}-{digits[3:5]}-{digits[5:9]}"


def format_phone(phone: PhoneInput | None) -> str | None:
    """Format phone as (aaa)bbb-cccc.

    Replicates COACTUPC 9600-WRITE-PROCESSING phone formatting:
        STRING '(' AREA-CODE ')' PREFIX '-' LINE-NUMBER.
    """
    if phone is None:
        return None
    return f"({phone.area_code}){phone.prefix}-{phone.line_number}"


def parse_phone(phone_str: str | None) -> dict | None:
    """Parse (aaa)bbb-cccc string back into area/prefix/line parts.

    Used when pre-populating the update form with existing data.
    """
    if not phone_str:
        return None
    import re

    match = re.match(r"^\((\d{3})\)(\d{3})-(\d{4})$", phone_str.strip())
    if not match:
        return None
    return {
        "area_code": match.group(1),
        "prefix": match.group(2),
        "line_number": match.group(3),
    }


def parse_ssn(ssn_raw: str | None) -> dict | None:
    """Parse 9-digit SSN string into three parts for the update form.

    Mirrors the split SSN fields on the CACTUPA screen:
    ACTSSN1 (3 chars), ACTSSN2 (2 chars), ACTSSN3 (4 chars).
    """
    if not ssn_raw:
        return None
    digits = ssn_raw.strip().zfill(9)
    if len(digits) < 9:
        return None
    return {
        "part1": digits[0:3],
        "part2": digits[3:5],
        "part3": digits[5:9],
    }
