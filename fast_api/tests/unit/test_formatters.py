"""Unit tests for formatting utility functions.

These test the COBOL STRING-statement equivalents for SSN and phone formatting.
"""

import pytest
from app.schemas.account import PhoneInput
from app.utils.formatters import format_ssn, format_phone, parse_phone, parse_ssn


class TestFormatSsn:
    """Replicates STRING CUST-SSN(1:3) '-' CUST-SSN(4:2) '-' CUST-SSN(6:4)."""

    def test_formats_9_digit_ssn(self):
        assert format_ssn("123456789") == "123-45-6789"

    def test_pads_short_ssn(self):
        # "5678" zero-padded to 9 digits is "000005678" → "000-00-5678"
        assert format_ssn("5678") == "000-00-5678"

    def test_returns_none_for_none_input(self):
        assert format_ssn(None) is None

    def test_returns_none_for_empty_string(self):
        assert format_ssn("") is None


class TestFormatPhone:
    """Replicates COACTUPC phone formatting: '(' AREA-CODE ')' PREFIX '-' LINE."""

    def test_formats_phone_correctly(self):
        phone = PhoneInput(area_code="202", prefix="456", line_number="1111")
        assert format_phone(phone) == "(202)456-1111"

    def test_returns_none_for_none_input(self):
        assert format_phone(None) is None


class TestParsePhone:
    def test_parses_formatted_phone(self):
        result = parse_phone("(202)456-1111")
        assert result == {"area_code": "202", "prefix": "456", "line_number": "1111"}

    def test_returns_none_for_invalid_format(self):
        assert parse_phone("202-456-1111") is None

    def test_returns_none_for_none(self):
        assert parse_phone(None) is None


class TestParseSsn:
    def test_parses_9_digit_ssn(self):
        result = parse_ssn("123456789")
        assert result == {"part1": "123", "part2": "45", "part3": "6789"}

    def test_pads_short_ssn(self):
        result = parse_ssn("5678")
        assert result is not None
        assert len(result["part1"]) == 3

    def test_returns_none_for_none(self):
        assert parse_ssn(None) is None
