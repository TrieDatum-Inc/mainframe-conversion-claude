"""
Unit tests for account_service.py.

COBOL origin tested:
  COACTVWC: view_account (READ ACCTDAT + READ CUSTDAT via xref)
  COACTUPC: update_account (15+ validation rules, WS-DATACHANGED-FLAG, atomic update)

Test coverage goals:
  - Happy path: view and update account
  - 404: account not found, customer not found
  - 422: no changes detected
  - SSN masking in view response
  - Cross-field validation: cash_limit <= credit_limit
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.errors import (
    AccountNoChangesDetectedError,
    AccountNotFoundError,
    CustomerNotFoundError,
)
from app.schemas.account import AccountUpdateRequest, CustomerUpdateRequest
from app.services import account_service


def make_mock_account(
    account_id: int = 10000000001,
    active_status: str = "Y",
    current_balance: Decimal = Decimal("1234.56"),
    credit_limit: Decimal = Decimal("10000.00"),
    cash_credit_limit: Decimal = Decimal("2000.00"),
) -> MagicMock:
    """Create a mock Account ORM object."""
    acct = MagicMock()
    acct.account_id = account_id
    acct.active_status = active_status
    acct.current_balance = current_balance
    acct.credit_limit = credit_limit
    acct.cash_credit_limit = cash_credit_limit
    acct.open_date = date(2020, 1, 15)
    acct.expiration_date = date(2025, 1, 15)
    acct.reissue_date = date(2023, 1, 15)
    acct.curr_cycle_credit = Decimal("500.00")
    acct.curr_cycle_debit = Decimal("1734.56")
    acct.zip_code = "10001"
    acct.group_id = "GROUP001"
    acct.updated_at = MagicMock()
    return acct


def make_mock_customer(customer_id: int = 100000001) -> MagicMock:
    """Create a mock Customer ORM object."""
    cust = MagicMock()
    cust.customer_id = customer_id
    cust.first_name = "James"
    cust.middle_name = "Edward"
    cust.last_name = "Anderson"
    cust.street_address_1 = "123 Main St"
    cust.street_address_2 = None
    cust.city = "New York"
    cust.state_code = "NY"
    cust.zip_code = "10001"
    cust.country_code = "USA"
    cust.phone_number_1 = "212-555-0101"
    cust.phone_number_2 = None
    cust.ssn = "123-45-6789"
    cust.date_of_birth = date(1975, 4, 12)
    cust.fico_score = 750
    cust.government_id_ref = "DL123456789"
    cust.eft_account_id = "EFT0000001"
    cust.primary_card_holder_flag = "Y"
    return cust


class TestMaskSsn:
    """Unit tests for the SSN masking utility."""

    def test_masks_standard_ssn(self) -> None:
        """COBOL: ACSTSSN masked display — only last 4 digits shown."""
        result = account_service._mask_ssn("123-45-6789")
        assert result == "***-**-6789"

    def test_masks_none_ssn(self) -> None:
        """Returns placeholder for None/empty SSN."""
        assert account_service._mask_ssn(None) == "***-**-****"
        assert account_service._mask_ssn("") == "***-**-****"

    def test_masks_malformed_ssn(self) -> None:
        """Returns placeholder for SSN that doesn't match NNN-NN-NNNN format."""
        result = account_service._mask_ssn("invalid")
        assert result == "***-**-****"


class TestViewAccount:
    """Tests for view_account service function — maps COACTVWC."""

    @pytest.mark.asyncio
    async def test_view_account_success(self) -> None:
        """Happy path: account + customer found, SSN masked in response."""
        mock_db = AsyncMock()
        mock_account = make_mock_account()
        mock_customer = make_mock_customer()

        with (
            patch.object(
                account_service.AccountRepository,
                "get_by_id",
                return_value=mock_account,
            ),
            patch.object(
                account_service.CustomerRepository,
                "get_by_account_id",
                return_value=mock_customer,
            ),
        ):
            response = await account_service.view_account(
                account_id=10000000001, db=mock_db
            )

        assert response.account_id == 10000000001
        assert response.active_status == "Y"
        assert response.credit_limit == Decimal("10000.00")
        # SSN masked — never expose plain SSN
        assert response.customer.ssn_masked == "***-**-6789"
        assert response.customer.first_name == "James"

    @pytest.mark.asyncio
    async def test_view_account_not_found_raises_404(self) -> None:
        """COBOL: COACTVWC READ-ACCT-BY-ACCT-ID RESP=NOTFND → 404."""
        mock_db = AsyncMock()

        with patch.object(
            account_service.AccountRepository, "get_by_id", return_value=None
        ):
            with pytest.raises(AccountNotFoundError):
                await account_service.view_account(account_id=99999999999, db=mock_db)

    @pytest.mark.asyncio
    async def test_view_account_no_customer_raises_404(self) -> None:
        """COBOL: COACTVWC READ-CUST-BY-CUST-ID RESP=NOTFND → 404."""
        mock_db = AsyncMock()
        mock_account = make_mock_account()

        with (
            patch.object(
                account_service.AccountRepository,
                "get_by_id",
                return_value=mock_account,
            ),
            patch.object(
                account_service.CustomerRepository,
                "get_by_account_id",
                return_value=None,
            ),
        ):
            with pytest.raises(CustomerNotFoundError):
                await account_service.view_account(
                    account_id=10000000001, db=mock_db
                )


class TestDetectAccountChanges:
    """Tests for change detection — maps COACTUPC WS-DATACHANGED-FLAG."""

    def test_detects_balance_change(self) -> None:
        """Any changed field returns True."""
        account = make_mock_account(current_balance=Decimal("1000.00"))
        request = MagicMock()
        request.active_status = account.active_status
        request.open_date = account.open_date
        request.expiration_date = account.expiration_date
        request.reissue_date = account.reissue_date
        request.credit_limit = account.credit_limit
        request.cash_credit_limit = account.cash_credit_limit
        request.current_balance = Decimal("2000.00")  # changed
        request.curr_cycle_credit = account.curr_cycle_credit
        request.curr_cycle_debit = account.curr_cycle_debit
        request.group_id = account.group_id

        assert account_service._detect_account_changes(account, request) is True

    def test_no_changes_returns_false(self) -> None:
        """All fields same → WS-DATACHANGED-FLAG = 'N' equivalent."""
        account = make_mock_account()
        request = MagicMock()
        request.active_status = account.active_status
        request.open_date = account.open_date
        request.expiration_date = account.expiration_date
        request.reissue_date = account.reissue_date
        request.credit_limit = account.credit_limit
        request.cash_credit_limit = account.cash_credit_limit
        request.current_balance = account.current_balance
        request.curr_cycle_credit = account.curr_cycle_credit
        request.curr_cycle_debit = account.curr_cycle_debit
        request.group_id = account.group_id

        assert account_service._detect_account_changes(account, request) is False


class TestUpdateAccount:
    """Tests for update_account service function — maps COACTUPC."""

    @pytest.mark.asyncio
    async def test_update_account_not_found_raises_404(self) -> None:
        """COBOL: COACTUPC READ-ACCT-BY-ACCT-ID RESP=NOTFND → 404."""
        mock_db = AsyncMock()

        with patch.object(
            account_service.AccountRepository, "get_by_id", return_value=None
        ):
            with pytest.raises(AccountNotFoundError):
                await account_service.update_account(
                    account_id=99999999999,
                    request=MagicMock(),
                    db=mock_db,
                )

    @pytest.mark.asyncio
    async def test_update_account_no_changes_raises_422(self) -> None:
        """COBOL: COACTUPC WS-DATACHANGED-FLAG = 'N' → 'No changes detected' → 422."""
        mock_db = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_account = make_mock_account()
        mock_customer = make_mock_customer()

        # Build a request that matches all current values exactly
        cust_req = MagicMock()
        cust_req.customer_id = mock_customer.customer_id
        cust_req.first_name = mock_customer.first_name
        cust_req.middle_name = mock_customer.middle_name
        cust_req.last_name = mock_customer.last_name
        cust_req.address_line_1 = mock_customer.street_address_1
        cust_req.address_line_2 = mock_customer.street_address_2
        cust_req.city = mock_customer.city
        cust_req.state_code = mock_customer.state_code
        cust_req.zip_code = mock_customer.zip_code
        cust_req.country_code = mock_customer.country_code
        cust_req.phone_1 = mock_customer.phone_number_1
        cust_req.phone_2 = mock_customer.phone_number_2
        cust_req.ssn_part1 = "123"
        cust_req.ssn_part2 = "45"
        cust_req.ssn_part3 = "6789"
        cust_req.date_of_birth = mock_customer.date_of_birth
        cust_req.fico_score = mock_customer.fico_score
        cust_req.government_id_ref = mock_customer.government_id_ref
        cust_req.eft_account_id = mock_customer.eft_account_id
        cust_req.primary_card_holder = mock_customer.primary_card_holder_flag

        request = MagicMock()
        request.active_status = mock_account.active_status
        request.open_date = mock_account.open_date
        request.expiration_date = mock_account.expiration_date
        request.reissue_date = mock_account.reissue_date
        request.credit_limit = mock_account.credit_limit
        request.cash_credit_limit = mock_account.cash_credit_limit
        request.current_balance = mock_account.current_balance
        request.curr_cycle_credit = mock_account.curr_cycle_credit
        request.curr_cycle_debit = mock_account.curr_cycle_debit
        request.group_id = mock_account.group_id
        request.customer = cust_req

        with (
            patch.object(
                account_service.AccountRepository,
                "get_by_id",
                return_value=mock_account,
            ),
            patch.object(
                account_service.CustomerRepository,
                "get_by_account_id",
                return_value=mock_customer,
            ),
        ):
            with pytest.raises(AccountNoChangesDetectedError):
                await account_service.update_account(
                    account_id=10000000001,
                    request=request,
                    db=mock_db,
                )
