"""
COBOL compatibility utilities.

Provides Python equivalents for COBOL/CICS data handling patterns found throughout
the CardDemo application — packed decimal arithmetic, fixed-length string operations,
COBOL date formats, and sign handling for zoned/packed numeric fields.

References:
  - PIC S9(10)V99 COMP-3 fields → Python Decimal with 2 decimal places
  - PIC X(n) fields → Python str with right-space-padding to n chars
  - COBOL MOVE with truncation/padding → cobol_move_x()
  - FUNCTION UPPER-CASE → str.upper() (used in COSGN00C)
  - FUNCTION CURRENT-DATE → datetime.now()
"""
import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Union


# ---------------------------------------------------------------------------
# Decimal / Packed-Decimal (COMP-3) helpers
# ---------------------------------------------------------------------------

TWO_PLACES = Decimal("0.01")
FOUR_PLACES = Decimal("0.0001")


def to_decimal(value: Union[str, int, float, Decimal, None], scale: int = 2) -> Decimal:
    """
    Convert any numeric value to a Decimal with the given scale.

    Replicates COBOL PIC S9(n)V99 COMP-3 fixed-point semantics.
    Called wherever monetary amounts flow through the system.

    Args:
        value: Input value (raw string from DB, Python int/float, or None).
        scale: Number of decimal places (default 2, matching V99).

    Returns:
        Rounded Decimal, or Decimal("0") for None/empty.

    Example (from CBACT04C interest calculation):
        interest = to_decimal(bal) * to_decimal(rate) / 100 / 12
    """
    if value is None:
        return Decimal("0")
    quantizer = Decimal(10) ** -scale
    try:
        return Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return Decimal("0")


def cobol_multiply(a: Decimal, b: Decimal, scale: int = 2) -> Decimal:
    """
    COBOL COMPUTE equivalent: multiply two decimals and truncate to scale.

    COBOL MULTIPLY does not round intermediate results by default;
    ROUND_HALF_UP matches the ON SIZE ERROR rounding clause used in CBACT04C.
    """
    quantizer = Decimal(10) ** -scale
    return (a * b).quantize(quantizer, rounding=ROUND_HALF_UP)


def cobol_divide(dividend: Decimal, divisor: Decimal, scale: int = 2) -> Decimal:
    """
    COBOL DIVIDE equivalent with ROUND clause.
    Used in CBACT04C: interest = balance * rate / 100 / 12
    """
    if divisor == 0:
        raise ZeroDivisionError("COBOL DIVIDE: divisor is zero")
    quantizer = Decimal(10) ** -scale
    return (dividend / divisor).quantize(quantizer, rounding=ROUND_HALF_UP)


def calculate_monthly_interest(balance: Decimal, annual_rate_pct: Decimal) -> Decimal:
    """
    Monthly interest calculation from CBACT04C.

    Formula: interest = TRAN-CAT-BAL * DIS-INT-RATE / 100 / 12
    DIS-INT-RATE is stored as PIC S9(04)V99 — e.g., 1999 = 19.99%

    Args:
        balance: Transaction category balance (TRAN-CAT-BAL).
        annual_rate_pct: Annual interest rate percentage (DIS-INT-RATE / 100).

    Returns:
        Monthly interest amount rounded to 2 decimal places.
    """
    rate_decimal = cobol_divide(annual_rate_pct, Decimal("100"), scale=6)
    monthly_rate = cobol_divide(rate_decimal, Decimal("12"), scale=6)
    return cobol_multiply(balance, monthly_rate, scale=2)


# ---------------------------------------------------------------------------
# Fixed-length string (PIC X) helpers
# ---------------------------------------------------------------------------

def cobol_move_x(value: str | None, length: int) -> str:
    """
    Replicate COBOL MOVE for PIC X(n) fields: right-pad with spaces, truncate if longer.

    COBOL always pads alphanumeric fields to their declared length.
    Used for SEC-USR-ID (PIC X(08)), TRAN-ID (PIC X(16)), etc.

    Args:
        value: Input string (None treated as SPACES).
        length: Target PIC X field length.

    Returns:
        Exactly `length` characters, space-padded or right-truncated.
    """
    s = (value or "").ljust(length)
    return s[:length]


def cobol_trim(value: str | None) -> str:
    """
    Strip trailing spaces from a COBOL PIC X field value.
    Equivalent to FUNCTION TRIM(field, TRAILING).
    """
    return (value or "").rstrip()


def cobol_upper(value: str | None) -> str:
    """
    COBOL FUNCTION UPPER-CASE equivalent.
    Used in COSGN00C for user ID normalization before USRSEC lookup.
    """
    return (value or "").upper()


def cobol_spaces_or_low_values(value: str | None) -> bool:
    """
    Test whether a field contains only spaces or low-values (x'00').
    Used in COSGN00C: WHEN USERIDI OF COSGN0AI = SPACES OR LOW-VALUES
    """
    if value is None:
        return True
    stripped = value.replace("\x00", "")
    return stripped.strip() == ""


def pad_user_id(user_id: str) -> str:
    """
    Normalize user ID: uppercase and strip trailing spaces.
    Original COBOL stored as PIC X(08) with trailing spaces;
    modern DB stores without padding.
    """
    return user_id.upper().strip()[:8]


# ---------------------------------------------------------------------------
# Date conversion helpers
# ---------------------------------------------------------------------------

COBOL_DATE_FORMAT_YYYYMMDD = "%Y%m%d"
COBOL_DATE_FORMAT_MMDDYYYY = "%m%d%Y"
COBOL_DATE_FORMAT_ISO = "%Y-%m-%d"
COBOL_TS_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


def parse_cobol_date(value: str | None) -> date | None:
    """
    Parse COBOL date string in YYYY-MM-DD format (PIC X(10) date fields).

    ACCT-OPEN-DATE, ACCT-EXPIRAION-DATE, CUST-DOB-YYYY-MM-DD all use
    PIC X(10) with format YYYY-MM-DD as stored in the ASCII data files.
    """
    if not value or cobol_spaces_or_low_values(value):
        return None
    value = value.strip()
    for fmt in (COBOL_DATE_FORMAT_ISO, COBOL_DATE_FORMAT_YYYYMMDD, COBOL_DATE_FORMAT_MMDDYYYY):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_cobol_timestamp(value: str | None) -> datetime | None:
    """
    Parse COBOL timestamp string (TRAN-ORIG-TS, TRAN-PROC-TS — PIC X(26)).

    Format in dailytran.txt: '2022-06-10 19:27:53.000000'
    """
    if not value or cobol_spaces_or_low_values(value):
        return None
    value = value.strip()
    for fmt in (COBOL_TS_FORMAT, "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def format_cobol_date(d: date | None) -> str:
    """Format a Python date as COBOL PIC X(10) YYYY-MM-DD string."""
    if d is None:
        return " " * 10
    return d.strftime(COBOL_DATE_FORMAT_ISO)


# ---------------------------------------------------------------------------
# Zoned decimal / OVERPUNCH sign helpers
# ---------------------------------------------------------------------------
# The ASCII data files use OVERPUNCH notation for signed packed decimals:
# Positive overpunch: { = 0, A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, I=9
# Negative overpunch: } = 0, J=1, K=2, L=3, M=4, N=5, O=6, P=7, Q=8, R=9

_OVERPUNCH_POS = str.maketrans("{ABCDEFGHI", "0123456789")
_OVERPUNCH_NEG = str.maketrans("}JKLMNOPQR", "0123456789")

_POS_CHARS = frozenset("{ABCDEFGHI")
_NEG_CHARS = frozenset("}JKLMNOPQR")


def decode_overpunch(value: str, implied_decimals: int = 2) -> Decimal:
    """
    Decode COBOL overpunch (SIGN TRAILING SEPARATE) notation to Python Decimal.

    Used when parsing the raw ASCII data files (acctdata.txt, dailytran.txt).
    The last character of a signed numeric field encodes both the last digit
    and the sign.

    Args:
        value: Raw string containing overpunch characters.
        implied_decimals: Number of implied decimal places (V in PIC clause).

    Returns:
        Python Decimal with correct sign and scale.

    Examples:
        decode_overpunch("00000001940{", 2) → Decimal("194.00")  (positive)
        decode_overpunch("0000009190}", 2) → Decimal("-919.00")  (negative)
        decode_overpunch("0000000678H", 2) → Decimal("67.88")   (positive 8 at end)
    """
    if not value:
        return Decimal("0")
    value = value.strip()
    if not value:
        return Decimal("0")

    last = value[-1]
    digits = value[:-1]

    if last in _POS_CHARS:
        last_digit = last.translate(_OVERPUNCH_POS)
        sign = 1
    elif last in _NEG_CHARS:
        last_digit = last.translate(_OVERPUNCH_NEG)
        sign = -1
    else:
        # No overpunch — plain numeric
        last_digit = last
        sign = 1

    full_digits = digits + last_digit
    # Remove any non-digit characters (spaces, other filler)
    full_digits = re.sub(r"\D", "0", full_digits)

    if not full_digits:
        return Decimal("0")

    raw_int = int(full_digits)
    quantizer = Decimal(10) ** -implied_decimals
    result = Decimal(raw_int * sign) * quantizer
    return result.quantize(quantizer, rounding=ROUND_HALF_UP)


def decode_plain_numeric(value: str, implied_decimals: int = 0) -> Decimal:
    """
    Decode a plain COBOL DISPLAY numeric field (PIC 9(n)) to Decimal.
    Strips spaces and leading zeros.
    """
    if not value:
        return Decimal("0")
    clean = re.sub(r"\D", "0", value.strip())
    if not clean:
        return Decimal("0")
    raw = int(clean)
    if implied_decimals == 0:
        return Decimal(raw)
    quantizer = Decimal(10) ** -implied_decimals
    return (Decimal(raw) * quantizer).quantize(quantizer, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Transaction ID generation
# Mirrors COBIL00C: WS-TRAN-ID-NUM built from WS-ABS-TIME + account number
# ---------------------------------------------------------------------------

def generate_transaction_id(account_id: int, timestamp: datetime | None = None) -> str:
    """
    Generate a 16-character transaction ID.

    Mirrors COBIL00C logic: transaction ID is composed from account number
    and absolute timestamp (WS-ABS-TIME via EXEC CICS ASKTIME).

    Format: ACCTNNNNNNNNNTTTTT (account padded + timestamp microseconds)
    Result is exactly PIC X(16).
    """
    if timestamp is None:
        timestamp = datetime.now()
    ts_micro = timestamp.strftime("%m%d%H%M%S%f")[:11]
    acct_str = str(account_id).zfill(5)[-5:]
    tran_id = f"{acct_str}{ts_micro}"
    return cobol_move_x(tran_id, 16)
