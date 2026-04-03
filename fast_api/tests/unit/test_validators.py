"""Unit tests for Pydantic schema validators.

Tests all field-level validation rules from COACTUPC spec section 7:
  - 1220-EDIT-YESNO: Y/N fields
  - 1225-EDIT-ALPHA-REQD: required alpha fields
  - 1235-EDIT-ALPHA-OPT: optional alpha fields
  - 1245-EDIT-NUM-REQD: required numeric fields
  - 1260-EDIT-US-PHONE-NUM: phone number validation
  - 1265-EDIT-US-SSN: SSN validation
  - 1270-EDIT-US-STATE-CD: state code validation
  - 1275-EDIT-FICO-SCORE: FICO range 300-850
  - EDIT-DATE-OF-BIRTH: not future date
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from pydantic import ValidationError

from app.schemas.account import (
    AccountUpdateRequest,
    PhoneInput,
    SsnInput,
)


def _base_request(**overrides) -> dict:
    """Return a valid request dict; override individual fields for tests."""
    base = {
        "updated_at": datetime(2024, 1, 1, 12, 0, 0),
        "acct_active_status": "Y",
        "acct_credit_limit": Decimal("10000.00"),
        "acct_cash_credit_limit": Decimal("2000.00"),
        "acct_curr_bal": Decimal("1250.75"),
        "acct_curr_cyc_credit": Decimal("500.00"),
        "acct_curr_cyc_debit": Decimal("1750.75"),
        "acct_open_date": date(2020, 1, 15),
        "acct_expiration_date": date(2026, 1, 31),
        "acct_reissue_date": date(2024, 1, 31),
        "acct_group_id": "PREMIUM",
        "cust_first_name": "James",
        "cust_middle_name": "Earl",
        "cust_last_name": "Carter",
        "cust_addr_line_1": "1600 Pennsylvania Ave NW",
        "cust_addr_state_cd": "DC",
        "cust_addr_country_cd": "USA",
        "cust_addr_zip": "20500",
        "cust_phone_num_1": {"area_code": "202", "prefix": "456", "line_number": "1111"},
        "cust_ssn": {"part1": "123", "part2": "45", "part3": "6789"},
        "cust_dob": date(1960, 3, 15),
        "cust_eft_account_id": "1234567890",
        "cust_pri_card_holder_ind": "Y",
        "cust_fico_credit_score": 780,
    }
    base.update(overrides)
    return base


class TestActiveStatusValidation:
    """1220-EDIT-YESNO: Account status must be Y or N."""

    def test_y_is_valid(self):
        r = AccountUpdateRequest(**_base_request(acct_active_status="Y"))
        assert r.acct_active_status == "Y"

    def test_n_is_valid(self):
        r = AccountUpdateRequest(**_base_request(acct_active_status="N"))
        assert r.acct_active_status == "N"

    def test_lowercase_is_upcased(self):
        r = AccountUpdateRequest(**_base_request(acct_active_status="y"))
        assert r.acct_active_status == "Y"

    def test_invalid_value_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            AccountUpdateRequest(**_base_request(acct_active_status="X"))
        assert "Account Active Status must be Y or N" in str(exc_info.value)


class TestNameValidation:
    """1225-EDIT-ALPHA-REQD / 1235-EDIT-ALPHA-OPT: name fields."""

    def test_valid_first_name(self):
        r = AccountUpdateRequest(**_base_request(cust_first_name="Mary"))
        assert r.cust_first_name == "Mary"

    def test_name_with_space_is_valid(self):
        r = AccountUpdateRequest(**_base_request(cust_first_name="Mary Ann"))
        assert r.cust_first_name == "Mary Ann"

    def test_name_with_digit_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            AccountUpdateRequest(**_base_request(cust_first_name="Mary1"))
        assert "alphabets and spaces" in str(exc_info.value)

    def test_blank_first_name_raises(self):
        with pytest.raises(ValidationError):
            AccountUpdateRequest(**_base_request(cust_first_name="   "))

    def test_optional_middle_name_none_is_valid(self):
        r = AccountUpdateRequest(**_base_request(cust_middle_name=None))
        assert r.cust_middle_name is None

    def test_optional_middle_name_with_digit_raises(self):
        with pytest.raises(ValidationError):
            AccountUpdateRequest(**_base_request(cust_middle_name="Ann1"))


class TestStateCodeValidation:
    """1270-EDIT-US-STATE-CD: valid US state codes."""

    def test_valid_state_code(self):
        r = AccountUpdateRequest(**_base_request(cust_addr_state_cd="NY"))
        assert r.cust_addr_state_cd == "NY"

    def test_lowercase_state_upcased(self):
        r = AccountUpdateRequest(**_base_request(cust_addr_state_cd="ny"))
        assert r.cust_addr_state_cd == "NY"

    def test_invalid_state_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            AccountUpdateRequest(**_base_request(cust_addr_state_cd="ZZ"))
        assert "not a valid US state code" in str(exc_info.value)

    def test_dc_is_valid(self):
        r = AccountUpdateRequest(**_base_request(cust_addr_state_cd="DC"))
        assert r.cust_addr_state_cd == "DC"


class TestFicoScoreValidation:
    """1275-EDIT-FICO-SCORE: must be 300-850."""

    def test_minimum_fico_is_valid(self):
        r = AccountUpdateRequest(**_base_request(cust_fico_credit_score=300))
        assert r.cust_fico_credit_score == 300

    def test_maximum_fico_is_valid(self):
        r = AccountUpdateRequest(**_base_request(cust_fico_credit_score=850))
        assert r.cust_fico_credit_score == 850

    def test_below_minimum_raises(self):
        with pytest.raises(ValidationError):
            AccountUpdateRequest(**_base_request(cust_fico_credit_score=299))

    def test_above_maximum_raises(self):
        with pytest.raises(ValidationError):
            AccountUpdateRequest(**_base_request(cust_fico_credit_score=851))


class TestSsnValidation:
    """1265-EDIT-US-SSN: SSN part rules."""

    def test_valid_ssn(self):
        ssn = SsnInput(part1="123", part2="45", part3="6789")
        assert ssn.part1 == "123"

    def test_part1_zero_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            SsnInput(part1="000", part2="45", part3="6789")
        assert "000" in str(exc_info.value)

    def test_part1_666_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            SsnInput(part1="666", part2="45", part3="6789")
        assert "666" in str(exc_info.value)

    def test_part1_900_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            SsnInput(part1="900", part2="45", part3="6789")
        assert "900" in str(exc_info.value).lower() or "900" in str(exc_info.value)

    def test_non_numeric_part1_raises(self):
        with pytest.raises(ValidationError):
            SsnInput(part1="abc", part2="45", part3="6789")


class TestPhoneValidation:
    """1260-EDIT-US-PHONE-NUM: NANP area code validation."""

    def test_valid_phone(self):
        phone = PhoneInput(area_code="202", prefix="456", line_number="1111")
        assert phone.area_code == "202"

    def test_area_code_below_200_raises(self):
        with pytest.raises(ValidationError):
            PhoneInput(area_code="100", prefix="456", line_number="1111")

    def test_n11_area_code_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            PhoneInput(area_code="211", prefix="456", line_number="1111")
        assert "N11" in str(exc_info.value)

    def test_non_numeric_prefix_raises(self):
        with pytest.raises(ValidationError):
            PhoneInput(area_code="202", prefix="abc", line_number="1111")


class TestDobValidation:
    """EDIT-DATE-OF-BIRTH: date of birth must not be in the future."""

    def test_past_dob_is_valid(self):
        r = AccountUpdateRequest(**_base_request(cust_dob=date(1990, 1, 1)))
        assert r.cust_dob == date(1990, 1, 1)

    def test_today_is_valid(self):
        r = AccountUpdateRequest(**_base_request(cust_dob=date.today()))
        assert r.cust_dob == date.today()

    def test_future_dob_raises(self):
        future = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            AccountUpdateRequest(**_base_request(cust_dob=future))
        assert "future" in str(exc_info.value).lower()


class TestZipValidation:
    def test_valid_5_digit_zip(self):
        r = AccountUpdateRequest(**_base_request(cust_addr_zip="20500"))
        assert r.cust_addr_zip == "20500"

    def test_invalid_zip_raises(self):
        with pytest.raises(ValidationError):
            AccountUpdateRequest(**_base_request(cust_addr_zip="ABCDE"))

    def test_all_zeros_raises(self):
        with pytest.raises(ValidationError):
            AccountUpdateRequest(**_base_request(cust_addr_zip="00000"))
