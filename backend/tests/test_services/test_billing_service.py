"""
Unit tests for app/services/billing_service.py

COBOL origin mapping:
  test_get_balance_*     → COBIL00C Phase 1 (READ-ACCTDAT-FILE, display CURBAL)
  test_process_payment_* → COBIL00C Phase 2 (CONF-PAY-YES: READ CXACAIX, WRITE TRANSACT,
                           COMPUTE ACCT-CURR-BAL = 0, REWRITE ACCTDAT)

Critical assertions:
  - COBIL00C: ACCT-CURR-BAL <= 0 → "You have nothing to pay..."
  - COBIL00C: full balance cleared to 0 after payment
  - COBIL00C: payment transaction has hardcoded type '02', source 'POS TERM', etc.
  - COBIL00C: transaction ID generated via sequence (not STARTBR/READPREV race)
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.exceptions.errors import (
    AccountNotFoundError,
    CardNotFoundError,
    NothingToPayError,
)
from app.schemas.billing import BillPaymentRequest
from app.services.billing_service import (
    BillingService,
    _PAYMENT_CATEGORY_CODE,
    _PAYMENT_DESCRIPTION,
    _PAYMENT_MERCHANT_CITY,
    _PAYMENT_MERCHANT_ID,
    _PAYMENT_MERCHANT_NAME,
    _PAYMENT_MERCHANT_ZIP,
    _PAYMENT_SOURCE,
    _PAYMENT_TYPE_CODE,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def service(mock_db):
    return BillingService(mock_db)


def make_account(account_id=10000000001, current_balance=150.00, credit_limit=5000.00):
    """Create mock Account ORM object."""
    account = MagicMock()
    account.account_id = account_id
    account.current_balance = current_balance
    account.credit_limit = credit_limit
    return account


# =============================================================================
# get_balance tests — COBIL00C Phase 1
# =============================================================================


class TestGetBalance:
    async def test_returns_balance(self, service):
        """COBIL00C: READ-ACCTDAT-FILE → display ACCT-CURR-BAL as CURBAL."""
        account = make_account(current_balance=350.00, credit_limit=5000.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_balance.return_value = account

        result = await service.get_balance(10000000001)

        assert result.account_id == 10000000001
        assert result.current_balance == Decimal("350.00")
        assert result.credit_limit == Decimal("5000.00")
        assert result.available_credit == Decimal("4650.00")

    async def test_raises_not_found_when_account_missing(self, service):
        """COBIL00C READ-ACCTDAT-FILE: NOTFND → 'Account ID NOT found...'."""
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_balance.return_value = None

        with pytest.raises(AccountNotFoundError):
            await service.get_balance(99999999999)

    async def test_raises_validation_error_on_zero_account_id(self, service):
        """COBIL00C: ACTIDINI blank → 'Acct ID can NOT be empty...'."""
        with pytest.raises(Exception):  # ServiceValidationError
            await service.get_balance(0)

    async def test_available_credit_computed(self, service):
        """Available credit = credit_limit - current_balance (modern addition)."""
        account = make_account(current_balance=1200.00, credit_limit=2000.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_balance.return_value = account

        result = await service.get_balance(10000000001)

        assert result.available_credit == Decimal("800.00")


# =============================================================================
# process_payment tests — COBIL00C Phase 2 (CONF-PAY-YES path)
# =============================================================================


class TestProcessPayment:
    def make_payment_request(self) -> BillPaymentRequest:
        return BillPaymentRequest(confirm="Y")

    async def test_processes_payment_successfully(self, service):
        """COBIL00C: full payment flow — WRITE TRANSACT + REWRITE ACCTDAT."""
        account = make_account(current_balance=350.00, credit_limit=5000.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = account
        service.billing_repo.get_card_for_account.return_value = "4111111111111001"
        service.billing_repo.update_account_balance.return_value = True

        service.transaction_repo = AsyncMock()
        service.transaction_repo.generate_transaction_id.return_value = "0000000000000099"
        mock_tran = MagicMock()
        mock_tran.transaction_id = "0000000000000099"
        service.transaction_repo.create.return_value = mock_tran

        result = await service.process_payment(10000000001, self.make_payment_request())

        assert result.account_id == 10000000001
        assert result.previous_balance == Decimal("350.00")
        assert result.new_balance == Decimal("0.00")  # COBIL00C: ACCT-CURR-BAL = 0
        assert result.transaction_id == "0000000000000099"
        assert "successful" in result.message.lower()

    async def test_raises_nothing_to_pay_when_balance_zero(self, service):
        """COBIL00C: IF ACCT-CURR-BAL <= 0: 'You have nothing to pay...'."""
        account = make_account(current_balance=0.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = account

        with pytest.raises(NothingToPayError):
            await service.process_payment(10000000001, self.make_payment_request())

    async def test_raises_nothing_to_pay_when_balance_negative(self, service):
        """COBIL00C: ACCT-CURR-BAL < 0 also triggers nothing-to-pay."""
        account = make_account(current_balance=-50.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = account

        with pytest.raises(NothingToPayError):
            await service.process_payment(10000000001, self.make_payment_request())

    async def test_raises_account_not_found(self, service):
        """COBIL00C READ-ACCTDAT-FILE: NOTFND → AccountNotFoundError."""
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = None

        with pytest.raises(AccountNotFoundError):
            await service.process_payment(99999999999, self.make_payment_request())

    async def test_raises_card_not_found_when_no_xref(self, service):
        """COBIL00C READ-CXACAIX-FILE: NOTFND → CardNotFoundError."""
        account = make_account(current_balance=100.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = account
        service.billing_repo.get_card_for_account.return_value = None  # no card in xref

        with pytest.raises(CardNotFoundError):
            await service.process_payment(10000000001, self.make_payment_request())

    async def test_payment_transaction_has_hardcoded_type_02(self, service):
        """
        COBIL00C hardcoded: TRAN-TYPE-CD = '02'
        The payment transaction must use type code '02'.
        """
        account = make_account(current_balance=100.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = account
        service.billing_repo.get_card_for_account.return_value = "4111111111111001"
        service.billing_repo.update_account_balance.return_value = True

        service.transaction_repo = AsyncMock()
        service.transaction_repo.generate_transaction_id.return_value = "0000000000000099"

        # Capture the transaction passed to create
        created_transactions = []
        async def capture_create(t):
            created_transactions.append(t)
            return t
        service.transaction_repo.create.side_effect = capture_create

        await service.process_payment(10000000001, self.make_payment_request())

        created = created_transactions[0]
        assert created.transaction_type_code == _PAYMENT_TYPE_CODE  # '02'
        assert created.transaction_category_code == _PAYMENT_CATEGORY_CODE  # '0002'
        assert created.transaction_source == _PAYMENT_SOURCE  # 'POS TERM'
        assert created.description == _PAYMENT_DESCRIPTION  # 'BILL PAYMENT - ONLINE'
        assert created.merchant_id == _PAYMENT_MERCHANT_ID  # '999999999'
        assert created.merchant_name == _PAYMENT_MERCHANT_NAME  # 'BILL PAYMENT'
        assert created.merchant_city == _PAYMENT_MERCHANT_CITY  # 'N/A'
        assert created.merchant_zip == _PAYMENT_MERCHANT_ZIP  # 'N/A'

    async def test_payment_amount_equals_previous_balance(self, service):
        """
        COBIL00C: TRAN-AMT = ACCT-CURR-BAL (full balance payment).
        The payment transaction amount must equal the account's current balance.
        """
        previous_balance = 487.32
        account = make_account(current_balance=previous_balance)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = account
        service.billing_repo.get_card_for_account.return_value = "4111111111111001"
        service.billing_repo.update_account_balance.return_value = True

        service.transaction_repo = AsyncMock()
        service.transaction_repo.generate_transaction_id.return_value = "0000000000000099"

        created_transactions = []
        async def capture_create(t):
            created_transactions.append(t)
            return t
        service.transaction_repo.create.side_effect = capture_create

        result = await service.process_payment(10000000001, self.make_payment_request())

        assert created_transactions[0].amount == float(Decimal(str(previous_balance)))
        assert result.previous_balance == Decimal(str(previous_balance))

    async def test_new_balance_is_zero_after_payment(self, service):
        """COBIL00C: COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT = 0."""
        account = make_account(current_balance=250.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = account
        service.billing_repo.get_card_for_account.return_value = "4111111111111001"
        service.billing_repo.update_account_balance.return_value = True

        service.transaction_repo = AsyncMock()
        service.transaction_repo.generate_transaction_id.return_value = "0000000000000099"
        mock_tran = MagicMock()
        mock_tran.transaction_id = "0000000000000099"
        service.transaction_repo.create.return_value = mock_tran

        result = await service.process_payment(10000000001, self.make_payment_request())

        # Verify update_account_balance called with 0
        service.billing_repo.update_account_balance.assert_called_once_with(
            10000000001, Decimal("0.00")
        )
        assert result.new_balance == Decimal("0.00")

    async def test_sequence_id_used_not_readprev(self, service):
        """
        COBIL00C BUG FIX: transaction ID from sequence, not STARTBR/READPREV.
        generate_transaction_id() must be called.
        """
        account = make_account(current_balance=100.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = account
        service.billing_repo.get_card_for_account.return_value = "4111111111111001"
        service.billing_repo.update_account_balance.return_value = True

        service.transaction_repo = AsyncMock()
        service.transaction_repo.generate_transaction_id.return_value = "0000000000000099"
        mock_tran = MagicMock()
        mock_tran.transaction_id = "0000000000000099"
        service.transaction_repo.create.return_value = mock_tran

        await service.process_payment(10000000001, self.make_payment_request())

        service.transaction_repo.generate_transaction_id.assert_called_once()

    async def test_success_message_contains_transaction_id(self, service):
        """COBIL00C success: 'Payment successful. Your Transaction ID is [N].'"""
        account = make_account(current_balance=100.00)
        service.billing_repo = AsyncMock()
        service.billing_repo.get_account_for_update.return_value = account
        service.billing_repo.get_card_for_account.return_value = "4111111111111001"
        service.billing_repo.update_account_balance.return_value = True

        service.transaction_repo = AsyncMock()
        service.transaction_repo.generate_transaction_id.return_value = "0000000000000099"
        mock_tran = MagicMock()
        mock_tran.transaction_id = "0000000000000099"
        service.transaction_repo.create.return_value = mock_tran

        result = await service.process_payment(10000000001, self.make_payment_request())

        assert "Payment successful" in result.message
        assert "99" in result.message  # int(0000000000000099) = 99
