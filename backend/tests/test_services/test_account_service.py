"""
Unit tests for account_service.py.

Tests COACTVWC (view) and COACTUPC (update) business logic.
SSN masking, change detection, validation rules.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.exceptions.errors import NoChangesDetectedError, NotFoundError
from app.services.account_service import (
    _mask_ssn,
    _apply_account_changes,
    _apply_customer_changes,
    view_account,
    update_account,
)


# =============================================================================
# SSN masking
# =============================================================================

class TestMaskSsn:
    def test_masks_valid_ssn(self):
        assert _mask_ssn("123-45-6789") == "***-**-6789"

    def test_masks_ssn_without_dashes(self):
        assert _mask_ssn("123456789") == "***-**-6789"

    def test_handles_none(self):
        assert _mask_ssn(None) == "***-**-****"

    def test_handles_empty_string(self):
        assert _mask_ssn("") == "***-**-****"

    def test_handles_short_ssn(self):
        assert _mask_ssn("123") == "***-**-****"


# =============================================================================
# View account — COACTVWC
# =============================================================================

class TestViewAccount:
    @pytest.mark.asyncio
    async def test_raises_not_found_when_account_missing(self):
        db = AsyncMock()
        with pytest.raises(NotFoundError) as exc_info:
            # Mock repositories to return None
            from unittest.mock import patch
            with patch("app.services.account_service.AccountRepository") as mock_repo_cls:
                mock_repo = mock_repo_cls.return_value
                mock_repo.get_by_id = AsyncMock(return_value=None)
                await view_account(99999, db)
        assert "99999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_customer_missing(self):
        db = AsyncMock()
        mock_account = MagicMock()
        mock_account.account_id = 1

        from unittest.mock import patch
        with patch("app.services.account_service.AccountRepository") as mock_acct_cls:
            with patch("app.services.account_service.CustomerRepository") as mock_cust_cls:
                mock_acct = mock_acct_cls.return_value
                mock_acct.get_by_id = AsyncMock(return_value=mock_account)
                mock_cust = mock_cust_cls.return_value
                mock_cust.get_by_account_id = AsyncMock(return_value=None)

                with pytest.raises(NotFoundError):
                    await view_account(1, db)


# =============================================================================
# Change detection — COACTUPC WS-DATACHANGED-FLAG
# =============================================================================

class TestApplyAccountChanges:
    def test_detects_status_change(self):
        account = MagicMock()
        account.active_status = "Y"
        account.credit_limit = 5000
        account.cash_credit_limit = 1000
        account.group_id = "ABC"
        account.open_date = None
        account.expiration_date = None
        account.reissue_date = None

        request = MagicMock()
        request.active_status = "N"
        request.credit_limit = None
        request.cash_credit_limit = None
        request.group_id = None
        request.open_date = None
        request.expiration_date = None
        request.reissue_date = None

        changed = _apply_account_changes(account, request)
        assert changed is True
        assert account.active_status == "N"

    def test_no_change_when_same_values(self):
        account = MagicMock()
        account.active_status = "Y"
        account.credit_limit = 5000
        account.cash_credit_limit = 1000
        account.group_id = "ABC"
        account.open_date = None
        account.expiration_date = None
        account.reissue_date = None

        request = MagicMock()
        request.active_status = "Y"
        request.credit_limit = 5000
        request.cash_credit_limit = 1000
        request.group_id = "ABC"
        request.open_date = None
        request.expiration_date = None
        request.reissue_date = None

        changed = _apply_account_changes(account, request)
        assert changed is False


# =============================================================================
# SSN validation — COACTUPC validation rules
# =============================================================================

class TestSsnValidation:
    def test_ssn_part1_cannot_be_000(self):
        from app.schemas.account import CustomerUpdateRequest
        with pytest.raises(Exception) as exc_info:
            CustomerUpdateRequest(
                first_name="John",
                last_name="Doe",
                ssn_part1="000",
                ssn_part2="45",
                ssn_part3="6789",
            )
        assert "000" in str(exc_info.value)

    def test_ssn_part1_cannot_be_666(self):
        from app.schemas.account import CustomerUpdateRequest
        with pytest.raises(Exception):
            CustomerUpdateRequest(
                first_name="John",
                last_name="Doe",
                ssn_part1="666",
                ssn_part2="45",
                ssn_part3="6789",
            )

    def test_ssn_part1_cannot_be_900_to_999(self):
        from app.schemas.account import CustomerUpdateRequest
        with pytest.raises(Exception):
            CustomerUpdateRequest(
                first_name="John",
                last_name="Doe",
                ssn_part1="900",
                ssn_part2="45",
                ssn_part3="6789",
            )

    def test_ssn_part2_cannot_be_00(self):
        from app.schemas.account import CustomerUpdateRequest
        with pytest.raises(Exception):
            CustomerUpdateRequest(
                first_name="John",
                last_name="Doe",
                ssn_part1="123",
                ssn_part2="00",
                ssn_part3="6789",
            )

    def test_ssn_part3_cannot_be_0000(self):
        from app.schemas.account import CustomerUpdateRequest
        with pytest.raises(Exception):
            CustomerUpdateRequest(
                first_name="John",
                last_name="Doe",
                ssn_part1="123",
                ssn_part2="45",
                ssn_part3="0000",
            )

    def test_valid_ssn_passes(self):
        from app.schemas.account import CustomerUpdateRequest
        req = CustomerUpdateRequest(
            first_name="John",
            last_name="Doe",
            ssn_part1="123",
            ssn_part2="45",
            ssn_part3="6789",
        )
        assert req.ssn_part1 == "123"


# =============================================================================
# Cash limit validation — COACTUPC
# =============================================================================

class TestCashLimitValidation:
    def test_cash_limit_exceeds_credit_limit_raises_error(self):
        from app.schemas.account import AccountUpdateRequest, CustomerUpdateRequest
        with pytest.raises(Exception):
            AccountUpdateRequest(
                credit_limit=1000,
                cash_credit_limit=2000,  # exceeds credit_limit
                customer=CustomerUpdateRequest(first_name="John", last_name="Doe"),
            )

    def test_equal_cash_and_credit_limit_passes(self):
        from app.schemas.account import AccountUpdateRequest, CustomerUpdateRequest
        req = AccountUpdateRequest(
            credit_limit=1000,
            cash_credit_limit=1000,
            customer=CustomerUpdateRequest(first_name="John", last_name="Doe"),
        )
        assert req.cash_credit_limit == req.credit_limit
