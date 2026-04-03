"""Unit tests for AccountService.

Tests all business logic paragraphs translated from COACTVWC and COACTUPC.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.services.account_service import AccountService, _check_concurrency, _normalize_acct_id
from app.utils.exceptions import (
    AccountNotFoundError,
    ConcurrentModificationError,
    CustomerNotFoundError,
    LockAcquisitionError,
)


# ---------------------------------------------------------------------------
# _normalize_acct_id — COBOL PIC 9(11) zero-padding
# ---------------------------------------------------------------------------

class TestNormalizeAcctId:
    def test_short_id_is_padded(self):
        assert _normalize_acct_id("1") == "00000000001"

    def test_eleven_digit_id_unchanged(self):
        assert _normalize_acct_id("00000000001") == "00000000001"

    def test_five_digit_id_padded(self):
        assert _normalize_acct_id("12345") == "00000012345"


# ---------------------------------------------------------------------------
# get_account_view — COACTVWC 9000-READ-ACCT equivalent
# ---------------------------------------------------------------------------

class TestGetAccountView:
    @pytest.mark.asyncio
    async def test_returns_view_when_account_found(
        self, account_service, mock_repo, sample_account_with_relations
    ):
        """Happy path: account + customer + cards all found."""
        mock_repo.get_account_with_relations.return_value = sample_account_with_relations

        result = await account_service.get_account_view("00000000001")

        assert result.acct_id == "00000000001"
        assert result.acct_active_status == "Y"
        assert result.customer is not None
        assert result.customer.cust_first_name == "James"
        # SSN formatted as XXX-XX-XXXX (1200-SETUP-SCREEN-VARS)
        assert result.customer.ssn_formatted == "123-45-6789"
        assert len(result.cards) == 1

    @pytest.mark.asyncio
    async def test_raises_not_found_when_account_missing(
        self, account_service, mock_repo
    ):
        """COBOL: DID-NOT-FIND-ACCT-IN-ACCTDAT."""
        mock_repo.get_account_with_relations.return_value = None

        with pytest.raises(AccountNotFoundError) as exc_info:
            await account_service.get_account_view("99999999999")

        assert "account master file" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_account_without_customer_returns_none_customer(
        self, account_service, mock_repo, sample_account_with_relations
    ):
        """COBOL: 'If customer not found, account data shown without customer section'."""
        from app.repositories.account_repository import AccountWithRelations
        no_cust = AccountWithRelations(
            account=sample_account_with_relations.account,
            customer=None,
            cards=sample_account_with_relations.cards,
        )
        mock_repo.get_account_with_relations.return_value = no_cust

        result = await account_service.get_account_view("00000000001")
        assert result.customer is None
        assert result.acct_id == "00000000001"

    @pytest.mark.asyncio
    async def test_id_is_normalized_before_lookup(
        self, account_service, mock_repo, sample_account_with_relations
    ):
        """Short account IDs must be zero-padded (COBOL PIC 9(11))."""
        mock_repo.get_account_with_relations.return_value = sample_account_with_relations

        await account_service.get_account_view("1")

        mock_repo.get_account_with_relations.assert_called_once_with("00000000001")


# ---------------------------------------------------------------------------
# _check_concurrency — COACTUPC 9700-CHECK-CHANGE-IN-REC equivalent
# ---------------------------------------------------------------------------

class TestCheckConcurrency:
    def test_passes_when_timestamps_match(self):
        ts = datetime(2024, 1, 1, 12, 0, 0)
        _check_concurrency(ts, ts, ts)  # should not raise

    def test_raises_when_account_updated_after_client_token(self):
        client_ts = datetime(2024, 1, 1, 12, 0, 0)
        newer_ts = datetime(2024, 1, 1, 12, 0, 1)

        with pytest.raises(ConcurrentModificationError) as exc_info:
            _check_concurrency(newer_ts, client_ts, client_ts)

        assert "Record changed by some one else" in exc_info.value.message

    def test_raises_when_customer_updated_after_client_token(self):
        client_ts = datetime(2024, 1, 1, 12, 0, 0)
        newer_ts = datetime(2024, 1, 1, 12, 0, 1)

        with pytest.raises(ConcurrentModificationError):
            _check_concurrency(client_ts, newer_ts, client_ts)

    def test_passes_when_account_updated_before_client_token(self):
        older_ts = datetime(2024, 1, 1, 11, 59, 59)
        client_ts = datetime(2024, 1, 1, 12, 0, 0)
        _check_concurrency(older_ts, older_ts, client_ts)  # should not raise


# ---------------------------------------------------------------------------
# update_account — COACTUPC 9600-WRITE-PROCESSING equivalent
# ---------------------------------------------------------------------------

class TestUpdateAccount:
    def _build_request(self, updated_at: datetime):
        from app.schemas.account import AccountUpdateRequest, SsnInput, PhoneInput
        return AccountUpdateRequest(
            updated_at=updated_at,
            acct_active_status="Y",
            acct_credit_limit=Decimal("10000.00"),
            acct_cash_credit_limit=Decimal("2000.00"),
            acct_curr_bal=Decimal("1250.75"),
            acct_curr_cyc_credit=Decimal("500.00"),
            acct_curr_cyc_debit=Decimal("1750.75"),
            acct_open_date=date(2020, 1, 15),
            acct_expiration_date=date(2026, 1, 31),
            acct_reissue_date=date(2024, 1, 31),
            acct_group_id="PREMIUM",
            cust_first_name="James",
            cust_middle_name="Earl",
            cust_last_name="Carter",
            cust_addr_line_1="1600 Pennsylvania Ave NW",
            cust_addr_state_cd="DC",
            cust_addr_country_cd="USA",
            cust_addr_zip="20500",
            cust_phone_num_1=PhoneInput(area_code="202", prefix="456", line_number="1111"),
            cust_ssn=SsnInput(part1="123", part2="45", part3="6789"),
            cust_dob=date(1960, 3, 15),
            cust_eft_account_id="1234567890",
            cust_pri_card_holder_ind="Y",
            cust_fico_credit_score=780,
        )

    @pytest.mark.asyncio
    async def test_successful_update_returns_committed_message(
        self, account_service, mock_repo, sample_account, sample_customer
    ):
        ts = datetime(2024, 1, 1, 12, 0, 0)
        sample_account.updated_at = ts
        sample_customer.updated_at = ts

        mock_repo.get_account_for_update.return_value = sample_account
        mock_repo.get_customer_id_by_account.return_value = "000000001"
        mock_repo.get_customer_for_update.return_value = sample_customer
        mock_repo.update_account.return_value = sample_account
        mock_repo.update_customer.return_value = sample_customer
        mock_repo.commit = AsyncMock()
        mock_repo.rollback = AsyncMock()

        request = self._build_request(updated_at=ts)
        result = await account_service.update_account("00000000001", request)

        assert result.message == "Changes committed to database"
        assert result.acct_id == "00000000001"

    @pytest.mark.asyncio
    async def test_raises_not_found_when_account_missing(
        self, account_service, mock_repo
    ):
        mock_repo.get_account_for_update.return_value = None

        request = self._build_request(updated_at=datetime(2024, 1, 1, 12, 0, 0))
        with pytest.raises(AccountNotFoundError):
            await account_service.update_account("99999999999", request)

    @pytest.mark.asyncio
    async def test_raises_concurrent_modification_when_record_changed(
        self, account_service, mock_repo, sample_account, sample_customer
    ):
        """9700-CHECK-CHANGE-IN-REC: DATA-WAS-CHANGED-BEFORE-UPDATE."""
        # Account was updated by another user after client fetched it
        sample_account.updated_at = datetime(2024, 1, 1, 12, 0, 1)
        sample_customer.updated_at = datetime(2024, 1, 1, 12, 0, 0)

        mock_repo.get_account_for_update.return_value = sample_account
        mock_repo.get_customer_id_by_account.return_value = "000000001"
        mock_repo.get_customer_for_update.return_value = sample_customer

        # Client token is earlier than actual updated_at
        request = self._build_request(updated_at=datetime(2024, 1, 1, 12, 0, 0))
        with pytest.raises(ConcurrentModificationError) as exc_info:
            await account_service.update_account("00000000001", request)

        assert "Record changed by some one else" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_raises_lock_error_on_db_operational_error(
        self, account_service, mock_repo
    ):
        """COULD-NOT-LOCK-ACCT-FOR-UPDATE: lock acquisition failure."""
        from sqlalchemy.exc import OperationalError
        mock_repo.get_account_for_update.side_effect = OperationalError(
            "could not obtain lock", None, None
        )

        request = self._build_request(updated_at=datetime(2024, 1, 1, 12, 0, 0))
        with pytest.raises(LockAcquisitionError):
            await account_service.update_account("00000000001", request)

    @pytest.mark.asyncio
    async def test_raises_customer_not_found_when_no_xref(
        self, account_service, mock_repo, sample_account
    ):
        """DID-NOT-FIND-CUST-IN-CUSTDAT: no cross-reference entry."""
        sample_account.updated_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_repo.get_account_for_update.return_value = sample_account
        mock_repo.get_customer_id_by_account.return_value = None

        request = self._build_request(updated_at=datetime(2024, 1, 1, 12, 0, 0))
        with pytest.raises(CustomerNotFoundError):
            await account_service.update_account("00000000001", request)
