"""Tests for BillPaymentService — COBIL00C business logic."""

from decimal import Decimal

import pytest

from app.exceptions.handlers import NothingToPayError
from app.models.transaction import Transaction
from app.schemas.bill_payment import BillPaymentRequest
from app.services.bill_payment_service import (
    BILL_PAYMENT_DESCRIPTION,
    BILL_PAYMENT_MERCHANT_ID,
    BILL_PAYMENT_MERCHANT_NAME,
    BILL_PAYMENT_SOURCE,
    BILL_PAYMENT_TYPE_CODE,
    BillPaymentService,
)


class TestPreviewPayment:
    """COBIL00C: display CURBAL before confirmation."""

    async def test_no_transactions_means_zero_balance(self, db_session):
        service = BillPaymentService(db_session)
        preview = await service.preview_payment("00000001000")
        assert preview.current_balance == Decimal("0.00")
        assert preview.can_pay is False
        assert "nothing to pay" in preview.message.lower()


class TestCheckBalancePayable:
    """COBIL00C: balance <= 0 → reject payment."""

    def test_zero_balance_not_payable(self):
        service = BillPaymentService(None)  # type: ignore[arg-type]
        with pytest.raises(NothingToPayError):
            service._check_balance_payable(Decimal("0.00"))

    def test_negative_balance_not_payable(self):
        service = BillPaymentService(None)  # type: ignore[arg-type]
        with pytest.raises(NothingToPayError):
            service._check_balance_payable(Decimal("-10.00"))

    def test_positive_balance_payable(self):
        service = BillPaymentService(None)  # type: ignore[arg-type]
        # Should not raise
        service._check_balance_payable(Decimal("100.00"))


class TestBuildPaymentTransaction:
    """COBIL00C: hardcoded payment transaction fields."""

    def test_payment_type_code_is_02(self):
        service = BillPaymentService(None)  # type: ignore[arg-type]
        from datetime import datetime
        txn = service._build_payment_transaction(
            transaction_id="0000000000000001",
            card_number="4000002000000000",
            balance=Decimal("100.00"),
            timestamp=datetime(2024, 1, 15, 8, 0, 0),
        )
        assert txn.type_code == BILL_PAYMENT_TYPE_CODE
        assert txn.type_code == "02"

    def test_merchant_id_hardcoded(self):
        service = BillPaymentService(None)  # type: ignore[arg-type]
        from datetime import datetime
        txn = service._build_payment_transaction(
            transaction_id="0000000000000001",
            card_number="4000002000000000",
            balance=Decimal("100.00"),
            timestamp=datetime(2024, 1, 15, 8, 0, 0),
        )
        assert txn.merchant_id == BILL_PAYMENT_MERCHANT_ID
        assert txn.merchant_id == "999999999"

    def test_merchant_name_hardcoded(self):
        service = BillPaymentService(None)  # type: ignore[arg-type]
        from datetime import datetime
        txn = service._build_payment_transaction(
            transaction_id="0000000000000001",
            card_number="4000002000000000",
            balance=Decimal("100.00"),
            timestamp=datetime(2024, 1, 15, 8, 0, 0),
        )
        assert txn.merchant_name == BILL_PAYMENT_MERCHANT_NAME
        assert txn.description == BILL_PAYMENT_DESCRIPTION
        assert txn.source == BILL_PAYMENT_SOURCE

    def test_amount_equals_balance(self):
        service = BillPaymentService(None)  # type: ignore[arg-type]
        from datetime import datetime
        balance = Decimal("250.75")
        txn = service._build_payment_transaction(
            transaction_id="0000000000000001",
            card_number="4000002000000000",
            balance=balance,
            timestamp=datetime(2024, 1, 15, 8, 0, 0),
        )
        assert txn.amount == balance


class TestProcessPaymentUnconfirmed:
    """COBIL00C CONFIRM='N' → preview only, no write."""

    async def test_unconfirmed_returns_preview_data(self, db_session):
        service = BillPaymentService(db_session)
        request = BillPaymentRequest(account_id="00000001000", confirmed=False)
        result = await service.process_payment(request)
        # Should return without writing a transaction
        assert result.transaction_id == ""
        assert result.amount_paid == Decimal("0.00")
