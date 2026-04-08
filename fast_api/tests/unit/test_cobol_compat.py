"""
Unit tests for COBOL compatibility utilities.

Tests map directly to COBOL data handling patterns in the CardDemo application.
All edge cases match COBOL field boundaries and overpunch conventions.
"""
from decimal import Decimal

import pytest

from app.utils.cobol_compat import (
    calculate_monthly_interest,
    cobol_move_x,
    cobol_spaces_or_low_values,
    cobol_trim,
    cobol_upper,
    decode_overpunch,
    decode_plain_numeric,
    generate_transaction_id,
    pad_user_id,
    to_decimal,
)


class TestDecimalHandling:
    """Tests for COMP-3 packed decimal equivalents."""

    def test_to_decimal_from_int(self) -> None:
        """PIC S9(10)V99 — 2 decimal places."""
        assert to_decimal(194) == Decimal("194.00")

    def test_to_decimal_from_float(self) -> None:
        assert to_decimal(194.555) == Decimal("194.56")  # ROUND_HALF_UP

    def test_to_decimal_none(self) -> None:
        """None maps to COBOL ZERO / LOW-VALUES numeric."""
        assert to_decimal(None) == Decimal("0")

    def test_to_decimal_string(self) -> None:
        assert to_decimal("2020.00") == Decimal("2020.00")

    def test_to_decimal_scale_4(self) -> None:
        """PIC S9(04)V9999 — 4 decimal places for rate fields."""
        assert to_decimal("19.9999", scale=4) == Decimal("19.9999")


class TestMonthlyInterest:
    """
    Tests for CBACT04C interest calculation formula.
    Formula: interest = TRAN-CAT-BAL * DIS-INT-RATE / 100 / 12
    """

    def test_monthly_interest_basic(self) -> None:
        """
        CBACT04C: balance=194.00, rate=15.00% annual
        Monthly = 194.00 * 0.15 / 12 = 2.425 → 2.43 (ROUND_HALF_UP)
        """
        balance = Decimal("194.00")
        rate = Decimal("15.00")
        result = calculate_monthly_interest(balance, rate)
        assert result == Decimal("2.43")

    def test_monthly_interest_zero_rate(self) -> None:
        """Payment category (type_cd='02') has 0% interest."""
        result = calculate_monthly_interest(Decimal("500.00"), Decimal("0.00"))
        assert result == Decimal("0.00")

    def test_monthly_interest_high_rate(self) -> None:
        """Cash advance: 25% APR on $1000 = $20.83/month."""
        result = calculate_monthly_interest(Decimal("1000.00"), Decimal("25.00"))
        assert result == Decimal("20.83")

    def test_monthly_interest_negative_balance(self) -> None:
        """Credit/refund: negative balance results in negative interest."""
        result = calculate_monthly_interest(Decimal("-100.00"), Decimal("15.00"))
        assert result == Decimal("-1.25")


class TestFixedLengthStrings:
    """Tests for PIC X(n) field handling."""

    def test_cobol_move_x_pads(self) -> None:
        """COBOL MOVE to PIC X(8): shorter value right-padded with spaces."""
        assert cobol_move_x("ADMIN", 8) == "ADMIN   "

    def test_cobol_move_x_truncates(self) -> None:
        """COBOL MOVE to PIC X(8): longer value truncated."""
        assert cobol_move_x("TOOLONGVALUE", 8) == "TOOLONGV"

    def test_cobol_move_x_exact(self) -> None:
        assert cobol_move_x("ADMIN   ", 8) == "ADMIN   "

    def test_cobol_move_x_none(self) -> None:
        """None → SPACES (PIC X INITIAL VALUE SPACES)."""
        assert cobol_move_x(None, 8) == "        "

    def test_cobol_trim(self) -> None:
        """FUNCTION TRIM(field, TRAILING)."""
        assert cobol_trim("ADMIN   ") == "ADMIN"
        assert cobol_trim("") == ""
        assert cobol_trim(None) == ""

    def test_cobol_upper(self) -> None:
        """COSGN00C: FUNCTION UPPER-CASE(USERIDI) TO WS-USER-ID."""
        assert cobol_upper("admin") == "ADMIN"
        assert cobol_upper("Admin123") == "ADMIN123"

    def test_cobol_spaces_or_low_values_spaces(self) -> None:
        """COSGN00C: WHEN USERIDI = SPACES OR LOW-VALUES."""
        assert cobol_spaces_or_low_values("   ") is True
        assert cobol_spaces_or_low_values("") is True
        assert cobol_spaces_or_low_values(None) is True
        assert cobol_spaces_or_low_values("ADMIN") is False

    def test_pad_user_id_uppercase(self) -> None:
        """SEC-USR-ID normalization: uppercase, stripped."""
        assert pad_user_id("admin") == "ADMIN"
        assert pad_user_id("USER0001") == "USER0001"


class TestOverpunchDecoding:
    """
    Tests for COBOL overpunch sign notation from ASCII data files.
    These decode the actual values in acctdata.txt, custdata.txt, dailytran.txt.
    """

    def test_positive_zero_overpunch(self) -> None:
        """'{' = 0 with positive sign — accounts with 0 balance."""
        result = decode_overpunch("000000000{", implied_decimals=2)
        assert result == Decimal("0.00")

    def test_positive_nonzero(self) -> None:
        """acctdata.txt row 1: '00000001940{' → 194.00"""
        result = decode_overpunch("00000001940{", implied_decimals=2)
        assert result == Decimal("194.00")

    def test_positive_with_letter(self) -> None:
        """dailytran.txt: '0000000678H' → H=8 → 67.88"""
        result = decode_overpunch("0000000678H", implied_decimals=2)
        assert result == Decimal("67.88")

    def test_negative_zero_overpunch(self) -> None:
        """'}' = 0 with negative sign."""
        result = decode_overpunch("0000009190}", implied_decimals=2)
        assert result == Decimal("-919.00")

    def test_positive_large_amount(self) -> None:
        """acctdata.txt: '00000061300{' → 6130.00 (credit limit)."""
        result = decode_overpunch("00000061300{", implied_decimals=2)
        assert result == Decimal("6130.00")

    def test_plain_numeric_no_overpunch(self) -> None:
        """PIC 9(03) fields without sign."""
        assert decode_plain_numeric("274") == Decimal("274")
        assert decode_plain_numeric("  0") == Decimal("0")


class TestTransactionIdGeneration:
    """Tests for TRAN-ID generation (COBIL00C WS-TRAN-ID-NUM pattern)."""

    def test_tran_id_is_16_chars(self) -> None:
        """TRAN-ID is PIC X(16) — always exactly 16 characters."""
        from datetime import datetime
        tran_id = generate_transaction_id(12345, datetime(2022, 6, 10, 19, 27, 53))
        assert len(tran_id) == 16

    def test_tran_id_contains_account(self) -> None:
        """Transaction ID derived from account number (last 5 digits)."""
        from datetime import datetime
        tran_id = generate_transaction_id(99999, datetime(2022, 6, 10, 19, 27, 53))
        assert tran_id.startswith("99999")

    def test_tran_id_unique_per_timestamp(self) -> None:
        """Different timestamps produce different IDs."""
        from datetime import datetime
        id1 = generate_transaction_id(1, datetime(2022, 1, 1, 0, 0, 0))
        id2 = generate_transaction_id(1, datetime(2022, 1, 1, 0, 0, 1))
        assert id1 != id2
