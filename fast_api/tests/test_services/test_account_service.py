"""
Tests for account_service.py — maps COACTVWC and COACTUPC.

Business rules tested:
  COACTVWC: 3-step read sequence (CXACAIX -> ACCTDAT -> CUSTDAT)
  COACTUPC: 35+ field validations from 1200-EDIT-MAP-INPUTS
  - Credit limit non-negative
  - Cash credit limit <= credit limit
  - Expiration date >= open date
  - State code in CSLKPCDY table
  - FICO score 300-850
  - DOB must be in the past
  - Atomic REWRITE (ACCTDAT + CUSTDAT together)
"""

from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import BusinessValidationError, ResourceNotFoundError
from app.domain.services.account_service import (
    _validate_account_fields,
    _validate_customer_fields,
    get_account_with_customer,
    update_account_with_customer,
)
from app.schemas.account_schemas import AccountUpdateRequest, CustomerUpdateRequest

# ---------------------------------------------------------------------------
# Helpers: build minimal valid request objects
# ---------------------------------------------------------------------------


def make_account_req(**overrides) -> AccountUpdateRequest:
    defaults = {
        "active_status": "Y",
        "curr_bal": Decimal("0.00"),
        "credit_limit": Decimal("5000.00"),
        "cash_credit_limit": Decimal("2000.00"),
        "open_date": date(2020, 1, 1),
        "expiration_date": date(2025, 12, 31),
        "reissue_date": None,
        "curr_cycle_credit": Decimal("0.00"),
        "curr_cycle_debit": Decimal("0.00"),
        "addr_zip": "62701",
        "group_id": "GRP001",
    }
    defaults.update(overrides)
    return AccountUpdateRequest(**defaults)


def make_customer_req(**overrides) -> CustomerUpdateRequest:
    defaults = {
        "first_name": "John",
        "middle_name": "A",
        "last_name": "Doe",
        "addr_line1": "123 Main St",
        "addr_line2": None,
        "addr_line3": "Springfield",
        "addr_state_cd": "IL",
        "addr_country_cd": "USA",
        "addr_zip": "62701",
        "phone_num1": "(217)555-1234",
        "phone_num2": None,
        "ssn": 123456789,
        "govt_issued_id": None,
        "dob": date(1985, 6, 15),
        "eft_account_id": None,
        "pri_card_holder": "Y",
        "fico_score": 720,
    }
    defaults.update(overrides)
    return CustomerUpdateRequest(**defaults)


# ---------------------------------------------------------------------------
# Account field validations
# ---------------------------------------------------------------------------


class TestValidateAccountFields:
    """COACTUPC 1200-EDIT-MAP-INPUTS account-side validations."""

    def test_valid_request_returns_no_errors(self):
        req = make_account_req()
        assert _validate_account_fields(req) == []

    def test_negative_credit_limit_fails(self):
        req = make_account_req(credit_limit=Decimal("-1.00"))
        errors = _validate_account_fields(req)
        assert any("credit limit" in e.lower() for e in errors)

    def test_negative_cash_credit_limit_fails(self):
        req = make_account_req(cash_credit_limit=Decimal("-100.00"))
        errors = _validate_account_fields(req)
        assert any("cash credit" in e.lower() for e in errors)

    def test_cash_exceeds_credit_fails(self):
        req = make_account_req(credit_limit=Decimal("1000.00"), cash_credit_limit=Decimal("2000.00"))
        errors = _validate_account_fields(req)
        assert any("exceed" in e.lower() for e in errors)

    def test_expiration_before_open_fails(self):
        req = make_account_req(
            open_date=date(2022, 1, 1),
            expiration_date=date(2021, 12, 31),
        )
        errors = _validate_account_fields(req)
        assert any("expiration" in e.lower() for e in errors)

    def test_reissue_before_open_fails(self):
        req = make_account_req(
            open_date=date(2022, 1, 1),
            reissue_date=date(2021, 6, 1),
        )
        errors = _validate_account_fields(req)
        assert any("reissue" in e.lower() for e in errors)

    def test_expiration_equals_open_is_valid(self):
        req = make_account_req(
            open_date=date(2022, 1, 1),
            expiration_date=date(2022, 1, 1),
        )
        errors = _validate_account_fields(req)
        assert errors == []

    def test_zero_credit_limit_is_valid(self):
        req = make_account_req(credit_limit=Decimal("0.00"), cash_credit_limit=Decimal("0.00"))
        assert _validate_account_fields(req) == []

    def test_inactive_status_valid(self):
        req = make_account_req(active_status="N")
        assert _validate_account_fields(req) == []


# ---------------------------------------------------------------------------
# Customer field validations
# ---------------------------------------------------------------------------


class TestValidateCustomerFields:
    """COACTUPC 1200-EDIT-MAP-INPUTS customer-side validations."""

    def test_valid_request_returns_no_errors(self):
        req = make_customer_req()
        assert _validate_customer_fields(req) == []

    def test_invalid_state_code_fails(self):
        req = make_customer_req(addr_state_cd="XX")
        errors = _validate_customer_fields(req)
        assert any("state" in e.lower() for e in errors)

    def test_valid_state_codes_pass(self):
        for state in ("CA", "TX", "NY", "FL", "IL", "WA"):
            req = make_customer_req(addr_state_cd=state)
            errors = _validate_customer_fields(req)
            assert errors == [], f"State {state} should be valid"

    def test_fico_below_300_fails(self):
        req = make_customer_req(fico_score=299)
        errors = _validate_customer_fields(req)
        assert any("fico" in e.lower() for e in errors)

    def test_fico_above_850_fails(self):
        req = make_customer_req(fico_score=851)
        errors = _validate_customer_fields(req)
        assert any("fico" in e.lower() for e in errors)

    def test_fico_boundary_300_is_valid(self):
        req = make_customer_req(fico_score=300)
        assert _validate_customer_fields(req) == []

    def test_fico_boundary_850_is_valid(self):
        req = make_customer_req(fico_score=850)
        assert _validate_customer_fields(req) == []

    def test_fico_none_is_valid(self):
        req = make_customer_req(fico_score=None)
        assert _validate_customer_fields(req) == []

    def test_future_dob_fails(self):
        req = make_customer_req(dob=date(2099, 1, 1))
        errors = _validate_customer_fields(req)
        assert any("birth" in e.lower() or "dob" in e.lower() for e in errors)

    def test_today_dob_fails(self):
        req = make_customer_req(dob=date.today())
        errors = _validate_customer_fields(req)
        assert any("birth" in e.lower() or "past" in e.lower() for e in errors)

    def test_none_state_code_is_valid(self):
        req = make_customer_req(addr_state_cd=None)
        assert _validate_customer_fields(req) == []


# ---------------------------------------------------------------------------
# Service-level tests (requires DB)
# ---------------------------------------------------------------------------


class TestGetAccountWithCustomer:
    """Maps COACTVWC 9000-READ-ACCT three-step read."""

    @pytest.mark.asyncio
    async def test_returns_account_and_customer(self, seeded_db):
        result = await get_account_with_customer(10000000001, seeded_db)
        assert result.account.acct_id == 10000000001
        assert result.customer.cust_id == 100000001
        assert result.customer.last_name == "Doe"
        assert result.card_num == "4111111111111001"

    @pytest.mark.asyncio
    async def test_not_found_raises_resource_not_found(self, seeded_db):
        with pytest.raises(ResourceNotFoundError):
            await get_account_with_customer(99999999999, seeded_db)

    @pytest.mark.asyncio
    async def test_second_account_returns_correct_customer(self, seeded_db):
        result = await get_account_with_customer(10000000002, seeded_db)
        assert result.account.acct_id == 10000000002
        assert result.customer.cust_id == 100000002
        assert result.customer.last_name == "Smith"

    @pytest.mark.asyncio
    async def test_returns_correct_credit_limit(self, seeded_db):
        result = await get_account_with_customer(10000000001, seeded_db)
        assert result.account.credit_limit == Decimal("5000.00")


class TestUpdateAccountWithCustomer:
    """Maps COACTUPC REWRITE ACCTDAT + REWRITE CUSTDAT (atomic)."""

    @pytest.mark.asyncio
    async def test_successful_update(self, seeded_db):
        acct_req = make_account_req(
            credit_limit=Decimal("6000.00"),
            active_status="Y",
        )
        cust_req = make_customer_req(first_name="Johnny")

        result = await update_account_with_customer(
            10000000001, acct_req, cust_req, seeded_db
        )
        assert result.account.credit_limit == Decimal("6000.00")
        assert result.customer.first_name == "Johnny"

    @pytest.mark.asyncio
    async def test_validation_failure_raises_business_error(self, seeded_db):
        acct_req = make_account_req(credit_limit=Decimal("-100.00"))
        cust_req = make_customer_req()

        with pytest.raises(BusinessValidationError):
            await update_account_with_customer(
                10000000001, acct_req, cust_req, seeded_db
            )

    @pytest.mark.asyncio
    async def test_invalid_state_raises_business_error(self, seeded_db):
        acct_req = make_account_req()
        cust_req = make_customer_req(addr_state_cd="ZZ")

        with pytest.raises((BusinessValidationError, ValueError)):
            await update_account_with_customer(
                10000000001, acct_req, cust_req, seeded_db
            )

    @pytest.mark.asyncio
    async def test_not_found_raises_resource_not_found(self, seeded_db):
        acct_req = make_account_req()
        cust_req = make_customer_req()

        with pytest.raises(ResourceNotFoundError):
            await update_account_with_customer(
                99999999999, acct_req, cust_req, seeded_db
            )
