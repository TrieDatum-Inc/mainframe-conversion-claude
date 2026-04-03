"""Unit tests for PaymentService — COBIL00C (Transaction CB00) business logic.

Tests cover all business rules from the COBIL00C specification:
  BR-001: Account ID must not be empty
  BR-002: Account lookup on every Enter press
  BR-003: Balance must be > 0 to allow payment ('You have nothing to pay...')
  BR-004: Payment is always for full balance (no partial payments)
  BR-005: Transaction ID = MAX(tran_id) + 1 (sequential, last+1)
  BR-006: Transaction codes: TRAN-TYPE-CD='02', TRAN-CAT-CD=2
  BR-007: Card number from CXACAIX cross-reference (not from user input)
  BR-008: Account balance becomes 0 after payment
  BR-009: Confirmation required (CONFIRM='Y' implied by POST call)
"""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.account import Account
from app.models.card_cross_reference import CardCrossReference
from app.models.transaction import (
    TRAN_TYPE_BILL_PAYMENT,
    TRAN_CAT_BILL_PAYMENT,
    TRAN_DESC_BILL_PAYMENT,
    TRAN_SOURCE_BILL_PAYMENT,
    Transaction,
)
from app.repositories.account_repository import AccountRepository
from app.repositories.card_cross_reference_repository import CardCrossReferenceRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.payment_service import PaymentService, _build_payment_transaction


# ============================================================
# Helper fixtures
# ============================================================

def make_account(
    acct_id: int = 10000000001,
    curr_bal: Decimal = Decimal("1250.75"),
    active_status: str = "Y",
) -> Account:
    acct = Account(
        acct_id=acct_id,
        active_status=active_status,
        curr_bal=curr_bal,
        credit_limit=Decimal("10000.00"),
        cash_credit_limit=Decimal("2000.00"),
        curr_cycle_credit=Decimal("0.00"),
        curr_cycle_debit=Decimal("1250.75"),
    )
    return acct


def make_xref(
    card_num: str = "4111111111111001",
    acct_id: int = 10000000001,
    cust_id: int = 100000001,
) -> CardCrossReference:
    return CardCrossReference(
        card_num=card_num,
        acct_id=acct_id,
        cust_id=cust_id,
    )


def make_transaction(tran_id: str = "0000000000000005") -> Transaction:
    return Transaction(
        tran_id=tran_id,
        tran_type_cd=TRAN_TYPE_BILL_PAYMENT,
        tran_cat_cd=TRAN_CAT_BILL_PAYMENT,
        source=TRAN_SOURCE_BILL_PAYMENT,
        description=TRAN_DESC_BILL_PAYMENT,
        amount=Decimal("1250.75"),
        card_num="4111111111111001",
        orig_timestamp=datetime.now(tz=timezone.utc),
        proc_timestamp=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def mock_account_repo() -> AsyncMock:
    return AsyncMock(spec=AccountRepository)


@pytest.fixture
def mock_xref_repo() -> AsyncMock:
    return AsyncMock(spec=CardCrossReferenceRepository)


@pytest.fixture
def mock_tran_repo() -> AsyncMock:
    return AsyncMock(spec=TransactionRepository)


@pytest.fixture
def service(
    mock_account_repo: AsyncMock,
    mock_xref_repo: AsyncMock,
    mock_tran_repo: AsyncMock,
) -> PaymentService:
    return PaymentService(
        account_repo=mock_account_repo,
        xref_repo=mock_xref_repo,
        transaction_repo=mock_tran_repo,
    )


# ============================================================
# _build_payment_transaction tests
# ============================================================

class TestBuildPaymentTransaction:
    """Tests for payment transaction record construction (COBIL00C lines 220-232)."""

    def test_transaction_type_is_02(self):
        """BR-006: TRAN-TYPE-CD must be '02' (bill payment)."""
        now = datetime.now(tz=timezone.utc)
        tran = _build_payment_transaction("0000000000000001", "4111111111111001", Decimal("500.00"), now)
        assert tran.tran_type_cd == "02"

    def test_transaction_cat_is_2(self):
        """BR-006: TRAN-CAT-CD must be 2."""
        now = datetime.now(tz=timezone.utc)
        tran = _build_payment_transaction("0000000000000001", "4111111111111001", Decimal("500.00"), now)
        assert tran.tran_cat_cd == 2

    def test_source_is_pos_term(self):
        """COBIL00C: TRAN-SOURCE = 'POS TERM'."""
        now = datetime.now(tz=timezone.utc)
        tran = _build_payment_transaction("0000000000000001", "4111111111111001", Decimal("500.00"), now)
        assert tran.source == "POS TERM"

    def test_description_is_bill_payment_online(self):
        """COBIL00C: TRAN-DESC = 'BILL PAYMENT - ONLINE'."""
        now = datetime.now(tz=timezone.utc)
        tran = _build_payment_transaction("0000000000000001", "4111111111111001", Decimal("500.00"), now)
        assert tran.description == "BILL PAYMENT - ONLINE"

    def test_merchant_id_is_999999999(self):
        """COBIL00C: TRAN-MERCHANT-ID = 999999999."""
        now = datetime.now(tz=timezone.utc)
        tran = _build_payment_transaction("0000000000000001", "4111111111111001", Decimal("500.00"), now)
        assert tran.merchant_id == 999999999

    def test_merchant_name_is_bill_payment(self):
        """COBIL00C: TRAN-MERCHANT-NAME = 'BILL PAYMENT'."""
        now = datetime.now(tz=timezone.utc)
        tran = _build_payment_transaction("0000000000000001", "4111111111111001", Decimal("500.00"), now)
        assert tran.merchant_name == "BILL PAYMENT"

    def test_merchant_city_and_zip_are_na(self):
        """COBIL00C: TRAN-MERCHANT-CITY = 'N/A', TRAN-MERCHANT-ZIP = 'N/A'."""
        now = datetime.now(tz=timezone.utc)
        tran = _build_payment_transaction("0000000000000001", "4111111111111001", Decimal("500.00"), now)
        assert tran.merchant_city == "N/A"
        assert tran.merchant_zip == "N/A"

    def test_tran_id_stored_correctly(self):
        """Transaction ID must be stored as provided."""
        now = datetime.now(tz=timezone.utc)
        tran = _build_payment_transaction("0000000000000042", "4111111111111001", Decimal("100.00"), now)
        assert tran.tran_id == "0000000000000042"

    def test_card_num_from_xref(self):
        """BR-007: Card number comes from cross-reference, not user input."""
        now = datetime.now(tz=timezone.utc)
        card_from_xref = "4111111111111002"
        tran = _build_payment_transaction("0000000000000001", card_from_xref, Decimal("500.00"), now)
        assert tran.card_num == card_from_xref

    def test_amount_equals_full_balance(self):
        """BR-004: Transaction amount equals the full balance."""
        now = datetime.now(tz=timezone.utc)
        balance = Decimal("3500.50")
        tran = _build_payment_transaction("0000000000000001", "4111111111111001", balance, now)
        assert tran.amount == balance

    def test_timestamps_set(self):
        """Both orig_timestamp and proc_timestamp are set to the same timestamp."""
        now = datetime.now(tz=timezone.utc)
        tran = _build_payment_transaction("0000000000000001", "4111111111111001", Decimal("100.00"), now)
        assert tran.orig_timestamp == now
        assert tran.proc_timestamp == now


# ============================================================
# PaymentService.get_account_balance tests
# ============================================================

class TestGetAccountBalance:
    """Tests for Phase 1 — account lookup (COBIL00C READ-ACCTDAT-FILE)."""

    @pytest.mark.asyncio
    async def test_returns_balance_when_account_found(
        self, service: PaymentService, mock_account_repo: AsyncMock
    ):
        """Phase 1: Returns current balance for valid account."""
        account = make_account(curr_bal=Decimal("1250.75"))
        mock_account_repo.get_by_id.return_value = account
        result = await service.get_account_balance("10000000001")
        assert result.curr_bal == Decimal("1250.75")
        assert result.acct_id == "10000000001"

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(
        self, service: PaymentService, mock_account_repo: AsyncMock
    ):
        """Phase 1: Returns 404 when account not found (NOTFND response)."""
        mock_account_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await service.get_account_balance("99999999999")
        assert exc_info.value.status_code == 404
        assert "NOT found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_info_message_when_zero_balance(
        self, service: PaymentService, mock_account_repo: AsyncMock
    ):
        """BR-003: Zero balance returns info message, not error."""
        account = make_account(curr_bal=Decimal("0.00"))
        mock_account_repo.get_by_id.return_value = account
        result = await service.get_account_balance("10000000004")
        assert result.curr_bal == Decimal("0.00")
        assert result.message is not None
        assert "nothing to pay" in result.message.lower()

    @pytest.mark.asyncio
    async def test_info_message_when_negative_balance(
        self, service: PaymentService, mock_account_repo: AsyncMock
    ):
        """BR-003: Negative balance also returns info message."""
        account = make_account(curr_bal=Decimal("-50.00"))
        mock_account_repo.get_by_id.return_value = account
        result = await service.get_account_balance("10000000001")
        assert result.message is not None


# ============================================================
# PaymentService.process_payment tests
# ============================================================

class TestProcessPayment:
    """Tests for Phase 2 — payment processing (COBIL00C CONF-PAY-YES path)."""

    @pytest.mark.asyncio
    async def test_successful_payment_full_flow(
        self,
        service: PaymentService,
        mock_account_repo: AsyncMock,
        mock_xref_repo: AsyncMock,
        mock_tran_repo: AsyncMock,
    ):
        """Full payment flow: account found, xref found, tran written, balance zeroed."""
        account = make_account(curr_bal=Decimal("1250.75"))
        xref = make_xref(card_num="4111111111111001")
        tran = make_transaction("0000000000000006")

        mock_account_repo.get_by_id.return_value = account
        mock_xref_repo.get_by_acct_id.return_value = xref
        mock_tran_repo.generate_next_tran_id.return_value = "0000000000000006"
        mock_tran_repo.create.return_value = tran
        mock_account_repo.zero_balance.return_value = make_account(curr_bal=Decimal("0.00"))

        result = await service.process_payment("10000000001")

        assert result.tran_id == "0000000000000006"
        assert result.payment_amount == Decimal("1250.75")
        assert result.new_balance == Decimal("0.00")
        assert result.message_type == "success"
        assert "Payment successful" in result.message
        assert "0000000000000006" in result.message

    @pytest.mark.asyncio
    async def test_raises_404_account_not_found(
        self, service: PaymentService, mock_account_repo: AsyncMock
    ):
        """Phase 2: 404 when account not found."""
        mock_account_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await service.process_payment("99999999999")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_422_when_zero_balance(
        self,
        service: PaymentService,
        mock_account_repo: AsyncMock,
    ):
        """BR-003: 422 when account balance is zero ('You have nothing to pay...')."""
        account = make_account(curr_bal=Decimal("0.00"))
        mock_account_repo.get_by_id.return_value = account
        with pytest.raises(HTTPException) as exc_info:
            await service.process_payment("10000000004")
        assert exc_info.value.status_code == 422
        assert "nothing to pay" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_raises_422_when_negative_balance(
        self,
        service: PaymentService,
        mock_account_repo: AsyncMock,
    ):
        """BR-003: 422 when account balance is negative."""
        account = make_account(curr_bal=Decimal("-10.00"))
        mock_account_repo.get_by_id.return_value = account
        with pytest.raises(HTTPException) as exc_info:
            await service.process_payment("10000000001")
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_raises_404_when_xref_not_found(
        self,
        service: PaymentService,
        mock_account_repo: AsyncMock,
        mock_xref_repo: AsyncMock,
    ):
        """Phase 2: 404 when card cross-reference not found."""
        account = make_account(curr_bal=Decimal("500.00"))
        mock_account_repo.get_by_id.return_value = account
        mock_xref_repo.get_by_acct_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await service.process_payment("10000000001")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_payment_amount_is_full_balance(
        self,
        service: PaymentService,
        mock_account_repo: AsyncMock,
        mock_xref_repo: AsyncMock,
        mock_tran_repo: AsyncMock,
    ):
        """BR-004: Payment amount must equal the full current balance."""
        balance = Decimal("3500.00")
        account = make_account(curr_bal=balance)
        xref = make_xref()
        tran = make_transaction("0000000000000007")
        tran.amount = balance

        mock_account_repo.get_by_id.return_value = account
        mock_xref_repo.get_by_acct_id.return_value = xref
        mock_tran_repo.generate_next_tran_id.return_value = "0000000000000007"
        mock_tran_repo.create.return_value = tran
        mock_account_repo.zero_balance.return_value = make_account(curr_bal=Decimal("0.00"))

        result = await service.process_payment("10000000002")
        assert result.payment_amount == balance

    @pytest.mark.asyncio
    async def test_zero_balance_after_payment(
        self,
        service: PaymentService,
        mock_account_repo: AsyncMock,
        mock_xref_repo: AsyncMock,
        mock_tran_repo: AsyncMock,
    ):
        """BR-008: Account balance is zero after payment."""
        account = make_account(curr_bal=Decimal("750.50"))
        xref = make_xref()
        tran = make_transaction("0000000000000008")

        mock_account_repo.get_by_id.return_value = account
        mock_xref_repo.get_by_acct_id.return_value = xref
        mock_tran_repo.generate_next_tran_id.return_value = "0000000000000008"
        mock_tran_repo.create.return_value = tran
        mock_account_repo.zero_balance.return_value = make_account(curr_bal=Decimal("0.00"))

        result = await service.process_payment("10000000003")
        assert result.new_balance == Decimal("0.00")
        # Verify zero_balance was called
        mock_account_repo.zero_balance.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_tran_type_and_cat_are_correct(
        self,
        service: PaymentService,
        mock_account_repo: AsyncMock,
        mock_xref_repo: AsyncMock,
        mock_tran_repo: AsyncMock,
    ):
        """BR-006: Written transaction has type='02' and cat=2."""
        account = make_account(curr_bal=Decimal("100.00"))
        xref = make_xref()
        tran = make_transaction("0000000000000009")
        tran.tran_type_cd = "02"
        tran.tran_cat_cd = 2

        mock_account_repo.get_by_id.return_value = account
        mock_xref_repo.get_by_acct_id.return_value = xref
        mock_tran_repo.generate_next_tran_id.return_value = "0000000000000009"
        mock_tran_repo.create.return_value = tran
        mock_account_repo.zero_balance.return_value = make_account(curr_bal=Decimal("0.00"))

        await service.process_payment("10000000001")
        # Verify the transaction created has correct type/cat
        create_call = mock_tran_repo.create.call_args[0][0]
        assert create_call.tran_type_cd == "02"
        assert create_call.tran_cat_cd == 2

    @pytest.mark.asyncio
    async def test_card_num_from_cross_reference(
        self,
        service: PaymentService,
        mock_account_repo: AsyncMock,
        mock_xref_repo: AsyncMock,
        mock_tran_repo: AsyncMock,
    ):
        """BR-007: Card number in transaction comes from CXACAIX, not user input."""
        account = make_account(curr_bal=Decimal("200.00"))
        xref = make_xref(card_num="4111111111111002")  # specific card from xref
        tran = make_transaction("0000000000000010")
        tran.card_num = "4111111111111002"

        mock_account_repo.get_by_id.return_value = account
        mock_xref_repo.get_by_acct_id.return_value = xref
        mock_tran_repo.generate_next_tran_id.return_value = "0000000000000010"
        mock_tran_repo.create.return_value = tran
        mock_account_repo.zero_balance.return_value = make_account(curr_bal=Decimal("0.00"))

        await service.process_payment("10000000001")
        create_call = mock_tran_repo.create.call_args[0][0]
        assert create_call.card_num == "4111111111111002"

    @pytest.mark.asyncio
    async def test_next_tran_id_incremented(
        self,
        service: PaymentService,
        mock_account_repo: AsyncMock,
        mock_xref_repo: AsyncMock,
        mock_tran_repo: AsyncMock,
    ):
        """BR-005: Transaction ID = last ID + 1."""
        account = make_account(curr_bal=Decimal("100.00"))
        xref = make_xref()
        tran = make_transaction("0000000000000006")

        mock_account_repo.get_by_id.return_value = account
        mock_xref_repo.get_by_acct_id.return_value = xref
        mock_tran_repo.generate_next_tran_id.return_value = "0000000000000006"
        mock_tran_repo.create.return_value = tran
        mock_account_repo.zero_balance.return_value = make_account(curr_bal=Decimal("0.00"))

        await service.process_payment("10000000001")
        mock_tran_repo.generate_next_tran_id.assert_awaited_once()
        create_call = mock_tran_repo.create.call_args[0][0]
        assert create_call.tran_id == "0000000000000006"
