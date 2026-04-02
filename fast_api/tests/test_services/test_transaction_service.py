"""
Tests for transaction_service.py — maps COTRN00C, COTRN01C, COTRN02C, COBIL00C.

Business rules tested:
  COTRN02C-001: card_num direct lookup (Path 1)
  COTRN02C-002: acct_id -> CXACAIX lookup (Path 2)
  COTRN02C-003: new tran_id = last + 1, zero-padded to 16 chars
  COTRN02C-004: must provide card_num OR acct_id
  COTRN02C-005: transaction type code must exist
  COBIL00C-001: account must be active
  COBIL00C-002: payment amount must not exceed balance
  COBIL00C-003: creates PR transaction, updates curr_bal
  ID-GEN-001: first transaction gets ID 0000000000000001
  ID-GEN-002: increments numerically from last ID
"""

from decimal import Decimal

import pytest

from app.core.exceptions import (
    AccountInactiveError,
    BusinessValidationError,
    ResourceNotFoundError,
)
from app.domain.services.transaction_service import (
    _generate_tran_id,
    _resolve_card_num,
    add_transaction,
    get_transaction_detail,
    list_transactions,
    process_bill_payment,
)
from app.schemas.transaction_schemas import BillPaymentRequest, TransactionAddRequest


# ---------------------------------------------------------------------------
# _generate_tran_id — COTRN02C READPREV + increment
# ---------------------------------------------------------------------------


class TestGenerateTranId:
    def test_first_transaction_id(self):
        """When no prior transactions, ID is 0000000000000001."""
        result = _generate_tran_id(None)
        assert result == "0000000000000001"
        assert len(result) == 16

    def test_increments_from_last_id(self):
        result = _generate_tran_id("0000000000000004")
        assert result == "0000000000000005"

    def test_increments_from_arbitrary_id(self):
        result = _generate_tran_id("0000000000000099")
        assert result == "0000000000000100"

    def test_result_is_always_16_chars(self):
        for last in ("0000000000000001", "0000000000009999", "0000000000000000"):
            result = _generate_tran_id(last)
            assert len(result) == 16

    def test_large_id_increment(self):
        result = _generate_tran_id("0000000000999999")
        assert result == "0000000001000000"

    def test_zero_padded_output(self):
        result = _generate_tran_id("0000000000000001")
        # Must start with zeros
        assert result.startswith("000")


# ---------------------------------------------------------------------------
# _resolve_card_num
# ---------------------------------------------------------------------------


class TestResolveCardNum:
    @pytest.mark.asyncio
    async def test_resolves_by_card_num_directly(self, seeded_db):
        """COTRN02C Path 1: direct card_num -> card lookup."""
        result = await _resolve_card_num("4111111111111001", None, seeded_db)
        assert result == "4111111111111001"

    @pytest.mark.asyncio
    async def test_resolves_by_acct_id_via_xref(self, seeded_db):
        """COTRN02C Path 2: acct_id -> CXACAIX -> card_num."""
        result = await _resolve_card_num(None, 10000000001, seeded_db)
        assert result == "4111111111111001"

    @pytest.mark.asyncio
    async def test_neither_card_nor_acct_raises_validation_error(self, seeded_db):
        """Must provide card_num OR acct_id."""
        with pytest.raises(BusinessValidationError) as exc_info:
            await _resolve_card_num(None, None, seeded_db)
        assert "card_num" in str(exc_info.value.field or "")

    @pytest.mark.asyncio
    async def test_unknown_card_num_raises_not_found(self, seeded_db):
        with pytest.raises(ResourceNotFoundError):
            await _resolve_card_num("9999999999999999", None, seeded_db)

    @pytest.mark.asyncio
    async def test_unknown_acct_id_raises_not_found(self, seeded_db):
        with pytest.raises(ResourceNotFoundError):
            await _resolve_card_num(None, 99999999999, seeded_db)


# ---------------------------------------------------------------------------
# add_transaction
# ---------------------------------------------------------------------------


class TestAddTransaction:
    @pytest.mark.asyncio
    async def test_add_transaction_by_card_num(self, seeded_db):
        req = TransactionAddRequest(
            card_num="4111111111111001",
            tran_type_cd="DB",
            tran_cat_cd=1,
            tran_amt=Decimal("50.00"),
            tran_desc="Test purchase",
            tran_source="TEST",
        )
        result = await add_transaction(req, seeded_db)
        assert result.tran_id is not None
        assert len(result.tran_id) == 16
        assert result.tran_amt == Decimal("50.00")
        assert result.card_num == "4111111111111001"

    @pytest.mark.asyncio
    async def test_add_transaction_by_acct_id(self, seeded_db):
        req = TransactionAddRequest(
            acct_id=10000000002,
            tran_type_cd="DB",
            tran_cat_cd=9,
            tran_amt=Decimal("100.00"),
            tran_desc="Online purchase",
            tran_source="WEB",
        )
        result = await add_transaction(req, seeded_db)
        assert result.tran_id is not None
        assert result.card_num == "4111111111111002"

    @pytest.mark.asyncio
    async def test_new_tran_id_is_sequential(self, seeded_db):
        """COTRN02C: new tran_id = last_tran_id + 1."""
        req = TransactionAddRequest(
            card_num="4111111111111001",
            tran_type_cd="DB",
            tran_cat_cd=1,
            tran_amt=Decimal("25.00"),
            tran_source="TEST",
        )
        result = await add_transaction(req, seeded_db)
        # Last seed tran_id is 0000000000000004; new should be 0000000000000005
        assert int(result.tran_id) == 5

    @pytest.mark.asyncio
    async def test_invalid_tran_type_raises_not_found(self, seeded_db):
        req = TransactionAddRequest(
            card_num="4111111111111001",
            tran_type_cd="ZZ",
            tran_cat_cd=1,
            tran_amt=Decimal("50.00"),
        )
        with pytest.raises(ResourceNotFoundError):
            await add_transaction(req, seeded_db)

    @pytest.mark.asyncio
    async def test_tran_type_uppercased(self, seeded_db):
        """COTRN02C uppercases type code before storing."""
        req = TransactionAddRequest(
            card_num="4111111111111001",
            tran_type_cd="db",
            tran_cat_cd=1,
            tran_amt=Decimal("10.00"),
        )
        result = await add_transaction(req, seeded_db)
        assert result.tran_type_cd == "DB"


# ---------------------------------------------------------------------------
# get_transaction_detail (COTRN01C)
# ---------------------------------------------------------------------------


class TestGetTransactionDetail:
    @pytest.mark.asyncio
    async def test_returns_transaction_by_id(self, seeded_db):
        result = await get_transaction_detail("0000000000000001", seeded_db)
        assert result.tran_id == "0000000000000001"
        assert result.tran_amt == Decimal("75.50")

    @pytest.mark.asyncio
    async def test_not_found_raises_resource_not_found(self, seeded_db):
        with pytest.raises(ResourceNotFoundError):
            await get_transaction_detail("9999999999999999", seeded_db)


# ---------------------------------------------------------------------------
# list_transactions (COTRN00C)
# ---------------------------------------------------------------------------


class TestListTransactions:
    @pytest.mark.asyncio
    async def test_lists_transactions(self, seeded_db):
        result = await list_transactions(seeded_db, page_size=10)
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_filter_by_card_num(self, seeded_db):
        result = await list_transactions(
            seeded_db,
            page_size=10,
            card_num_filter="4111111111111001",
        )
        for item in result.items:
            assert item.card_num == "4111111111111001"

    @pytest.mark.asyncio
    async def test_page_size_limits_results(self, seeded_db):
        result = await list_transactions(seeded_db, page_size=2)
        assert len(result.items) <= 2

    @pytest.mark.asyncio
    async def test_no_filter_returns_all(self, seeded_db):
        result = await list_transactions(seeded_db, page_size=100)
        assert len(result.items) == 4  # seed data has 4 transactions


# ---------------------------------------------------------------------------
# process_bill_payment (COBIL00C)
# ---------------------------------------------------------------------------


class TestProcessBillPayment:
    @pytest.mark.asyncio
    async def test_successful_partial_payment(self, seeded_db):
        """COBIL00C: creates PR transaction, reduces balance."""
        req = BillPaymentRequest(account_id=10000000001, payment_amount=Decimal("100.00"))
        result = await process_bill_payment(req, seeded_db)
        assert result.transaction_id is not None
        assert result.previous_balance == Decimal("-1500.00")
        # Balance increases (becomes less negative) by payment amount
        assert result.new_balance == Decimal("-1400.00")

    @pytest.mark.asyncio
    async def test_payment_on_inactive_account_fails(self, seeded_db):
        """COBIL00C: account must be active."""
        req = BillPaymentRequest(account_id=10000000003, payment_amount=Decimal("50.00"))
        with pytest.raises(AccountInactiveError):
            await process_bill_payment(req, seeded_db)

    @pytest.mark.asyncio
    async def test_payment_exceeds_balance_fails(self, seeded_db):
        """COBIL00C: payment amount <= current balance."""
        req = BillPaymentRequest(
            account_id=10000000001,
            payment_amount=Decimal("9999.00"),  # Way more than 1500 balance
        )
        with pytest.raises(BusinessValidationError) as exc_info:
            await process_bill_payment(req, seeded_db)
        assert "payment_amount" in str(exc_info.value.field or "")

    @pytest.mark.asyncio
    async def test_payment_creates_pr_transaction(self, seeded_db):
        """COBIL00C: creates transaction with type 'PR'."""
        req = BillPaymentRequest(account_id=10000000001, payment_amount=Decimal("200.00"))
        result = await process_bill_payment(req, seeded_db)
        # Verify created tran exists and has correct type
        tran = await get_transaction_detail(result.transaction_id, seeded_db)
        assert tran.tran_type_cd == "PR"
        assert tran.tran_amt == Decimal("-200.00")  # Negative = credit

    @pytest.mark.asyncio
    async def test_payment_on_zero_balance_account_fails(self, seeded_db):
        """Account 2 has zero balance — any payment exceeds balance."""
        req = BillPaymentRequest(account_id=10000000002, payment_amount=Decimal("1.00"))
        with pytest.raises(BusinessValidationError):
            await process_bill_payment(req, seeded_db)

    @pytest.mark.asyncio
    async def test_account_not_found_raises_not_found(self, seeded_db):
        req = BillPaymentRequest(account_id=99999999999, payment_amount=Decimal("10.00"))
        with pytest.raises(ResourceNotFoundError):
            await process_bill_payment(req, seeded_db)
