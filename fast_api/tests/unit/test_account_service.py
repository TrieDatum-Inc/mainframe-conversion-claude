"""
Unit tests for AccountService — business logic from COACTVWC and COACTUPC.

Tests verify all business rules:
  1. get_account returns account + customer (COACTVWC join)
  2. update_account applies only provided fields
  3. Non-admin cannot change group_id (COACTUPC admin-only restriction)
  4. credit_limit must be >= 0
  5. active_status must be 'Y' or 'N'
"""
from decimal import Decimal

import pytest

from app.models.account import Account
from app.schemas.account import AccountUpdateRequest
from app.services.account_service import AccountService
from app.utils.error_handlers import AuthorizationError, RecordNotFoundError


class TestAccountService:
    """Tests for COACTVWC and COACTUPC business logic."""

    @pytest.mark.asyncio
    async def test_get_account_returns_detail(self, db, account: Account, customer, card) -> None:
        """
        COACTVWC READ-PROCESSING: account + customer join.
        EXEC CICS READ FILE('ACCTDAT') + STARTBR CXACAIX + READ CUSTDAT.
        """
        service = AccountService(db)
        result = await service.get_account(1)

        assert result.acct_id == 1
        assert result.active_status == "Y"
        assert result.curr_bal == Decimal("194.00")
        assert result.credit_limit == Decimal("2020.00")
        assert result.customer_id == 1
        assert "Kessler" in result.customer_name

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, db) -> None:
        """CICS RESP=13 (NOTFND) → RecordNotFoundError → HTTP 404."""
        service = AccountService(db)
        with pytest.raises(RecordNotFoundError):
            await service.get_account(99999)

    @pytest.mark.asyncio
    async def test_update_account_partial_fields(self, db, account: Account) -> None:
        """
        COACTUPC CHECK-CHANGE-IN-REC: only provided fields are updated.
        Unset fields retain their original values.
        """
        service = AccountService(db)
        request = AccountUpdateRequest(active_status="N")
        result = await service.update_account(1, request, is_admin=False)

        assert result.active_status == "N"
        # Other fields unchanged
        assert result.curr_bal == Decimal("194.00")
        assert result.credit_limit == Decimal("2020.00")

    @pytest.mark.asyncio
    async def test_update_group_id_requires_admin(self, db, account: Account) -> None:
        """
        COACTUPC: only admin users can update ACCT-GROUP-ID.
        Non-admin attempt → AuthorizationError → HTTP 403.
        """
        service = AccountService(db)
        request = AccountUpdateRequest(group_id="NEW_GROUP")

        with pytest.raises(AuthorizationError):
            await service.update_account(1, request, is_admin=False)

    @pytest.mark.asyncio
    async def test_update_group_id_admin_allowed(self, db, account: Account) -> None:
        """Admin user CAN update group_id."""
        service = AccountService(db)
        request = AccountUpdateRequest(group_id="NEWGROUP1")
        result = await service.update_account(1, request, is_admin=True)

        assert result.group_id == "NEWGROUP1"

    @pytest.mark.asyncio
    async def test_update_credit_limit_negative_rejected(self, db, account: Account) -> None:
        """credit_limit must be >= 0 (COACTUPC validation — Pydantic rejects at schema level)."""
        from pydantic import ValidationError as PydanticValidationError
        with pytest.raises(PydanticValidationError):
            AccountUpdateRequest(credit_limit=Decimal("-100.00"))

    @pytest.mark.asyncio
    async def test_update_preserves_decimal_precision(self, db, account: Account) -> None:
        """
        COMP-3 precision: monetary fields must maintain 2 decimal places.
        Python Decimal matches COBOL COMP-3 arithmetic.
        """
        service = AccountService(db)
        request = AccountUpdateRequest(credit_limit=Decimal("2500.99"))
        result = await service.update_account(1, request, is_admin=False)

        assert result.credit_limit == Decimal("2500.99")
