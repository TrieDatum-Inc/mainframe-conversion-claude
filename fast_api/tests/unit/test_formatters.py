"""Unit tests for formatting utilities mirroring COBOL PIC +99999999.99."""

from decimal import Decimal

import pytest

from app.utils.formatters import format_amount, normalize_amount_str


class TestFormatAmount:
    """Mirrors WS-TRAN-AMT PIC +99999999.99 display editing."""

    def test_negative_amount(self):
        # COBOL PIC +99999999.99: sign + 8 integer digits + '.' + 2 decimal digits
        assert format_amount(Decimal("-52.47")) == "-00000052.47"

    def test_positive_amount(self):
        assert format_amount(Decimal("250.00")) == "+00000250.00"

    def test_zero(self):
        assert format_amount(Decimal("0.00")) == "+00000000.00"

    def test_large_negative(self):
        result = format_amount(Decimal("-99999999.99"))
        assert result.startswith("-")
        assert "99999999" in result

    def test_small_amount(self):
        assert format_amount(Decimal("-12.50")) == "-00000012.50"


class TestNormalizeAmountStr:
    """Mirrors FUNCTION NUMVAL-C then WS-TRAN-AMT-E re-display."""

    def test_normalizes_negative(self):
        result = normalize_amount_str("-00000052.47")
        assert result == "-00000052.47"

    def test_normalizes_positive(self):
        result = normalize_amount_str("+00000250.00")
        assert result == "+00000250.00"

    def test_passes_through_invalid(self):
        result = normalize_amount_str("INVALID")
        assert result == "INVALID"
