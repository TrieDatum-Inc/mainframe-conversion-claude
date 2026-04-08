"""
Unit tests for TransactionService — business logic from COTRN00C-02C and COBIL00C.

Tests verify all business rules:
  1. list_transactions — keyset pagination (STARTBR/READNEXT)
  2. get_transaction — RESP=13 on not found
  3. create_transaction — card active check, xref lookup, TRAN-ID generation
  4. process_bill_payment — balance check, TRANSACT write, ACCTDAT rewrite
"""
from decimal import Decimal

import pytest

from app.models.account import Account
from app.models.card import Card
from app.models.transaction import Transaction
from app.schemas.transaction import BillPaymentRequest, TransactionCreateRequest
from app.services.transaction_service import TransactionService
from app.utils.error_handlers import RecordNotFoundError, ValidationError


class TestTransactionService:
    """Tests for COTRN00C-02C and COBIL00C business logic."""

    @pytest.mark.asyncio
    async def test_list_transactions_returns_paginated(
        self, db, account: Account, card: Card, transaction: Transaction, tran_type
    ) -> None:
        """
        COTRN00C: STARTBR/READNEXT returns items with total count.
        """
        service = TransactionService(db)
        result = await service.list_transactions(limit=10)

        assert result.total >= 1
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self, db) -> None:
        """CICS RESP=13 (NOTFND) → RecordNotFoundError."""
        service = TransactionService(db)
        with pytest.raises(RecordNotFoundError):
            await service.get_transaction("DOESNOTEXIST1234")

    @pytest.mark.asyncio
    async def test_create_transaction_active_card(
        self, db, account: Account, card: Card, tran_type
    ) -> None:
        """
        COTRN02C: create transaction for active card succeeds.
        TRAN-ID generated, card xref looked up for account ID.
        """
        service = TransactionService(db)
        request = TransactionCreateRequest(
            type_cd="01",
            cat_cd=1,
            source="POS TERM",
            description="Test purchase at TestStore",
            amount=Decimal("99.99"),
            card_num="0100000011111111",
        )
        result = await service.create_transaction(request, "ADMIN")

        assert result.tran_id is not None
        assert len(result.tran_id.strip()) <= 16
        assert result.amount == Decimal("99.99")
        assert result.acct_id == 1  # From card xref

    @pytest.mark.asyncio
    async def test_create_transaction_inactive_card_rejected(
        self, db, account: Account, card: Card, inactive_card: Card, tran_type
    ) -> None:
        """
        CBTRN01C: IF CARD-ACTIVE-STATUS NOT = 'Y' → reject transaction.
        """
        service = TransactionService(db)
        request = TransactionCreateRequest(
            type_cd="01",
            cat_cd=1,
            amount=Decimal("50.00"),
            card_num="9999999999999999",
        )
        with pytest.raises(ValidationError) as exc_info:
            await service.create_transaction(request, "ADMIN")

        assert "not active" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_transaction_zero_amount_rejected(
        self, db, account: Account, card: Card, tran_type
    ) -> None:
        """COTRN02C: transaction amount must not be zero."""
        with pytest.raises(Exception):
            TransactionCreateRequest(
                type_cd="01",
                cat_cd=1,
                amount=Decimal("0.00"),
                card_num="0100000011111111",
            )

    @pytest.mark.asyncio
    async def test_bill_payment_reduces_balance(
        self, db, account: Account, card: Card, tran_type
    ) -> None:
        """
        COBIL00C PROCESS-PAYMENT:
          ACCT-CURR-BAL = ACCT-CURR-BAL - payment_amount
          ACCT-CURR-CYC-CREDIT = ACCT-CURR-CYC-CREDIT + payment_amount
        """
        service = TransactionService(db)
        initial_balance = Decimal(str(account.curr_bal))  # 194.00

        request = BillPaymentRequest(account_id=1, payment_amount=Decimal("50.00"))
        result = await service.process_bill_payment(request, "USER0001")

        # Verify transaction was created
        assert result.amount == Decimal("50.00")
        assert result.type_cd == "02"  # Payment transaction type

        # Verify balance was reduced (EXEC CICS REWRITE FILE(ACCTDAT))
        await db.refresh(account)
        assert account.curr_bal == initial_balance - Decimal("50.00")
        assert account.curr_cycle_credit == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_bill_payment_exceeds_balance_rejected(
        self, db, account: Account, card: Card
    ) -> None:
        """
        COBIL00C validation: payment_amount must be <= ACCT-CURR-BAL.
        account.curr_bal = 194.00 → payment of 200.00 rejected.
        """
        service = TransactionService(db)
        request = BillPaymentRequest(account_id=1, payment_amount=Decimal("200.00"))

        with pytest.raises(ValidationError) as exc_info:
            await service.process_bill_payment(request, "USER0001")

        assert "exceeds" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_bill_payment_negative_amount_rejected(self) -> None:
        """COBIL00C: payment_amount must be positive (schema validation)."""
        with pytest.raises(Exception):
            BillPaymentRequest(account_id=1, payment_amount=Decimal("-50.00"))
