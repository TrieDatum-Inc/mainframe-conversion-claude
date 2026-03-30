"""Tests for the validation utility functions in app.services.validation.

Ports field-level validation logic from COBOL copybooks CSUTLDWY.cpy,
CSUTLDPY.cpy (date validation with leap year support), and programs
COACTUPC (SSN, phone, signed numeric, alpha), COCRDUPC (card name),
and CORPT00C (report dates).
"""

from app.services.validation import (
    validate_alpha_only,
    validate_date_ccyymmdd,
    validate_ssn,
    validate_us_phone,
    validate_yes_no,
)


# ---------------------------------------------------------------------------
# Date validation (CSUTLDWY.cpy EDIT-DATE-CCYYMMDD)
# ---------------------------------------------------------------------------

def test_validate_date_valid():
    """Standard valid date '20230115' passes."""
    is_valid, err = validate_date_ccyymmdd("20230115")
    assert is_valid is True
    assert err == ""


def test_validate_date_invalid_month():
    """Month 13 is rejected with 'Not a valid Month'."""
    is_valid, err = validate_date_ccyymmdd("20231315")
    assert is_valid is False
    assert "Not a valid Month" in err


def test_validate_date_invalid_day():
    """Feb 30 is rejected (no month has 30 days in Feb)."""
    is_valid, err = validate_date_ccyymmdd("20230230")
    assert is_valid is False
    assert "Not a valid Day" in err


def test_validate_date_leap_year():
    """Feb 29, 2024 is valid (2024 is a leap year)."""
    is_valid, err = validate_date_ccyymmdd("20240229")
    assert is_valid is True
    assert err == ""


def test_validate_date_not_leap():
    """Feb 29, 2023 is invalid (2023 is NOT a leap year)."""
    is_valid, err = validate_date_ccyymmdd("20230229")
    assert is_valid is False
    assert "Not a valid Day" in err


# ---------------------------------------------------------------------------
# SSN validation (COACTUPC WS-EDIT-US-SSN)
# ---------------------------------------------------------------------------

def test_validate_ssn_valid():
    """Standard valid SSN '123456789' passes."""
    is_valid, err = validate_ssn("123456789")
    assert is_valid is True
    assert err == ""


def test_validate_ssn_invalid_000():
    """SSN starting with '000' is rejected (first part invalid)."""
    is_valid, err = validate_ssn("000456789")
    assert is_valid is False
    assert "first part" in err


def test_validate_ssn_invalid_666():
    """SSN starting with '666' is rejected (first part invalid)."""
    is_valid, err = validate_ssn("666456789")
    assert is_valid is False
    assert "first part" in err


def test_validate_ssn_invalid_900():
    """SSN starting with '900' is rejected (900-999 range invalid)."""
    is_valid, err = validate_ssn("900456789")
    assert is_valid is False
    assert "first part" in err


# ---------------------------------------------------------------------------
# Phone validation (COACTUPC WS-EDIT-US-PHONE-NUM)
# ---------------------------------------------------------------------------

def test_validate_phone_valid():
    """Standard valid US phone number passes."""
    is_valid, err = validate_us_phone("2025551234")
    assert is_valid is True
    assert err == ""


def test_validate_phone_invalid_area():
    """Area code '000' (< 200) is rejected."""
    is_valid, err = validate_us_phone("0005551234")
    assert is_valid is False
    assert "Area code" in err or "not valid" in err


# ---------------------------------------------------------------------------
# Alpha-only validation (COCRDUPC card name)
# ---------------------------------------------------------------------------

def test_validate_alpha_only():
    """Alpha characters and spaces pass; digits fail."""
    is_valid, err = validate_alpha_only("John Doe")
    assert is_valid is True
    assert err == ""

    is_valid, err = validate_alpha_only("John123")
    assert is_valid is False
    assert "alphabets" in err or "alpha" in err.lower()


# ---------------------------------------------------------------------------
# Yes/No validation (COACTUPC status fields)
# ---------------------------------------------------------------------------

def test_validate_yes_no():
    """'Y' and 'N' are valid; 'X' is invalid."""
    is_valid_y, _ = validate_yes_no("Y")
    assert is_valid_y is True

    is_valid_n, _ = validate_yes_no("N")
    assert is_valid_n is True

    is_valid_x, err = validate_yes_no("X")
    assert is_valid_x is False
    assert "Y or N" in err
