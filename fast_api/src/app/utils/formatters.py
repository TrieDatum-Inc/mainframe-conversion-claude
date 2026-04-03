"""
Formatting utilities that mirror COBOL editing and display patterns.
"""

from decimal import Decimal, ROUND_HALF_UP


# COBOL PIC +99999999.99 — sign, 8 integer digits, decimal, 2 fractional digits
_AMOUNT_FORMAT_TEMPLATE = "{sign}{integer:08d}.{fraction:02d}"


def format_amount(amount: Decimal) -> str:
    """
    Format a Decimal amount as COBOL PIC +99999999.99 for display.
    Mirrors WS-TRAN-AMT in COTRN00C/COTRN01C/COTRN02C.
    Examples: Decimal('-52.47') -> '-00052.47', Decimal('250.00') -> '+00000250.00'
    """
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "+" if quantized >= 0 else "-"
    abs_val = abs(quantized)
    integer_part = int(abs_val)
    fraction_part = int((abs_val - integer_part) * 100)
    return _AMOUNT_FORMAT_TEMPLATE.format(
        sign=sign, integer=integer_part, fraction=fraction_part
    )


def normalize_amount_str(amount_str: str) -> str:
    """
    Normalize a user-entered ±99999999.99 string.
    Mirrors FUNCTION NUMVAL-C then WS-TRAN-AMT-E re-display in COTRN02C.
    """
    try:
        value = Decimal(amount_str.strip())
        return format_amount(value)
    except Exception:
        return amount_str
