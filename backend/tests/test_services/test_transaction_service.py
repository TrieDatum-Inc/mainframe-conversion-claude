"""
Unit tests for app/services/transaction_service.py

COBOL origin mapping:
  test_list_transactions_*  → COTRN00C POPULATE-TRAN-DATA browse logic
  test_get_transaction_*    → COTRN01C PROCESS-ENTER-KEY (with BUG FIX: no READ UPDATE)
  test_create_transaction_* → COTRN02C ADD-TRANSACTION + VALIDATE-INPUT-FIELDS

TDD approach: tests define expected business behavior first.
Critical assertions:
  - COTRN01C BUG FIX: no exclusive lock on SELECT
  - COTRN02C: sequence-based ID generation (not STARTBR/READPREV race condition)
  - COTRN02C: account_id XOR card_number mutual exclusion
  - COTRN02C: amount != 0
  - COTRN02C: processed_date >= original_date
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.exceptions.errors import (
    CardNotFoundError,
    TransactionNotFoundError,
    TransactionTypeNotFoundError,
)
from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionDetailResponse,
    TransactionListResponse,
)
from app.services.transaction_service import TransactionService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    """Mock async SQLAlchemy session."""
    return AsyncMock()


@pytest.fixture
def service(mock_db):
    """TransactionService with mocked db."""
    return TransactionService(mock_db)


def make_transaction(
    transaction_id="0000000000000001",
    card_number="4111111111111001",
    type_code="01",
    amount=52.47,
    original_date=None,
    description="TEST PURCHASE",
):
    """Create a mock Transaction ORM object."""
    t = MagicMock()
    t.transaction_id = transaction_id
    t.card_number = card_number
    t.transaction_type_code = type_code
    t.transaction_category_code = "1001"
    t.transaction_source = "POS TERM"
    t.description = description
    t.amount = amount
    t.original_date = original_date or date(2026, 1, 15)
    t.processed_date = date(2026, 1, 16)
    t.merchant_id = "100000001"
    t.merchant_name = "TEST MERCHANT"
    t.merchant_city = "TEST CITY"
    t.merchant_zip = "12345"
    t.created_at = None
    t.updated_at = None
    return t


# =============================================================================
# list_transactions tests — COTRN00C POPULATE-TRAN-DATA
# =============================================================================


class TestListTransactions:
    async def test_returns_paginated_list(self, service):
        """COTRN00C: fills 10 rows per page."""
        transactions = [make_transaction(f"000000000000{i:04d}") for i in range(1, 11)]
        service.repo = AsyncMock()
        service.repo.list_transactions.return_value = (transactions, 25)

        result = await service.list_transactions(page=1, page_size=10)

        assert len(result.items) == 10
        assert result.total_count == 25
        assert result.has_next is True  # CDEMO-CT00-NEXT-PAGE-FLG='Y'
        assert result.has_previous is False
        assert result.page == 1

    async def test_has_next_false_on_last_page(self, service):
        """COTRN00C: CDEMO-CT00-NEXT-PAGE-FLG='N' when no more records."""
        transactions = [make_transaction(f"000000000000{i:04d}") for i in range(1, 6)]
        service.repo = AsyncMock()
        service.repo.list_transactions.return_value = (transactions, 5)

        result = await service.list_transactions(page=1, page_size=10)

        assert result.has_next is False  # CDEMO-CT00-NEXT-PAGE-FLG='N'

    async def test_has_previous_true_on_second_page(self, service):
        """COTRN00C: PF7 (previous page) should be enabled from page 2+."""
        transactions = [make_transaction(f"000000000000{i:04d}") for i in range(11, 21)]
        service.repo = AsyncMock()
        service.repo.list_transactions.return_value = (transactions, 25)

        result = await service.list_transactions(page=2, page_size=10)

        assert result.has_previous is True
        assert result.has_next is True

    async def test_tran_id_filter_passed_to_repo(self, service):
        """COTRN00C: TRNIDINI filter → STARTBR key WHERE id >= filter."""
        service.repo = AsyncMock()
        service.repo.list_transactions.return_value = ([], 0)

        await service.list_transactions(tran_id_filter="0000000000000010")

        service.repo.list_transactions.assert_called_once()
        call_kwargs = service.repo.list_transactions.call_args.kwargs
        assert call_kwargs["tran_id_filter"] == "0000000000000010"

    async def test_empty_list_when_no_transactions(self, service):
        """COTRN00C: STARTBR RESP=NOTFND → empty list."""
        service.repo = AsyncMock()
        service.repo.list_transactions.return_value = ([], 0)

        result = await service.list_transactions()

        assert result.items == []
        assert result.total_count == 0
        assert result.has_next is False

    async def test_first_and_last_item_keys_set(self, service):
        """COTRN00C: CDEMO-CT00-TRNID-FIRST and CDEMO-CT00-TRNID-LAST."""
        transactions = [
            make_transaction("0000000000000001"),
            make_transaction("0000000000000005"),
        ]
        service.repo = AsyncMock()
        service.repo.list_transactions.return_value = (transactions, 2)

        result = await service.list_transactions()

        assert result.first_item_key == "0000000000000001"
        assert result.last_item_key == "0000000000000005"

    async def test_invalid_page_raises_validation_error(self, service):
        """Page < 1 should raise validation error."""
        with pytest.raises(Exception):
            await service.list_transactions(page=0)


# =============================================================================
# get_transaction tests — COTRN01C PROCESS-ENTER-KEY
# =============================================================================


class TestGetTransaction:
    async def test_returns_transaction_detail(self, service):
        """COTRN01C: READ TRANSACT by TRNIDINI → populate all detail fields."""
        mock_transaction = make_transaction("0000000000000001")
        service.repo = AsyncMock()
        service.repo.get_by_id.return_value = mock_transaction

        result = await service.get_transaction("0000000000000001")

        assert result.transaction_id == "0000000000000001"
        assert result.card_number == "4111111111111001"
        assert result.amount == Decimal("52.47")

    async def test_raises_not_found_when_missing(self, service):
        """COTRN01C: READ RESP=NOTFND → TransactionNotFoundError → HTTP 404."""
        service.repo = AsyncMock()
        service.repo.get_by_id.return_value = None

        with pytest.raises(TransactionNotFoundError):
            await service.get_transaction("9999999999999999")

    async def test_raises_validation_error_on_blank_id(self, service):
        """COTRN01C: TRNIDINI=SPACES → 'Please enter a transaction ID'."""
        with pytest.raises(Exception):  # ValidationError
            await service.get_transaction("")

    async def test_raises_validation_error_on_whitespace_id(self, service):
        """COTRN01C: TRNIDINI all spaces → same error."""
        with pytest.raises(Exception):  # ValidationError
            await service.get_transaction("   ")

    async def test_no_lock_acquired_for_display(self, service):
        """
        COTRN01C BUG FIX: Original used READ UPDATE (exclusive lock) for display-only.
        Modern: plain SELECT — repo.get_by_id must NOT use FOR UPDATE.
        This test verifies the repo is called (not checking lock at service level).
        """
        mock_transaction = make_transaction()
        service.repo = AsyncMock()
        service.repo.get_by_id.return_value = mock_transaction

        await service.get_transaction("0000000000000001")

        # get_by_id called once — service delegates to repo (no duplicate lock call)
        service.repo.get_by_id.assert_called_once_with("0000000000000001")

    async def test_maps_all_detail_fields(self, service):
        """COTRN01C POPULATE-TRAN-FIELDS: all fields mapped from TRAN-RECORD."""
        mock_t = make_transaction()
        mock_t.transaction_category_code = "1001"
        mock_t.transaction_source = "POS TERM"
        mock_t.merchant_id = "100000001"
        mock_t.merchant_name = "TEST STORE"
        mock_t.merchant_city = "NEW YORK"
        mock_t.merchant_zip = "10001"

        service.repo = AsyncMock()
        service.repo.get_by_id.return_value = mock_t

        result = await service.get_transaction("0000000000000001")

        assert result.transaction_category_code == "1001"
        assert result.transaction_source == "POS TERM"
        assert result.merchant_id == "100000001"
        assert result.merchant_name == "TEST STORE"
        assert result.merchant_city == "NEW YORK"
        assert result.merchant_zip == "10001"


# =============================================================================
# create_transaction tests — COTRN02C ADD-TRANSACTION + VALIDATE-INPUT-FIELDS
# =============================================================================


def make_create_request(**overrides):
    """Build a valid TransactionCreateRequest with optional overrides."""
    defaults = {
        "card_number": "4111111111111001",
        "transaction_type_code": "01",
        "transaction_category_code": "1001",
        "transaction_source": "POS TERM",
        "description": "TEST PURCHASE ITEM",
        "amount": Decimal("-52.47"),
        "original_date": date(2026, 4, 1),
        "processed_date": date(2026, 4, 2),
        "merchant_id": "100000001",
        "merchant_name": "TEST MERCHANT",
        "merchant_city": "NEW YORK",
        "merchant_zip": "10001",
        "confirm": "Y",
    }
    defaults.update(overrides)
    return TransactionCreateRequest(**defaults)


class TestCreateTransaction:
    async def test_creates_transaction_with_card_number(self, service, mock_db):
        """COTRN02C: card_number provided → LOOKUP-ACCT-FROM-CARD → READ CCXREF."""
        request = make_create_request()
        created = make_transaction()

        service.repo = AsyncMock()
        service.repo.generate_transaction_id.return_value = "0000000000000099"
        service.repo.create.return_value = created

        mock_xref = MagicMock()
        mock_xref.account_id = 10000000001

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_xref
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock type validation as well
        mock_type = MagicMock()
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = mock_type
        mock_db.execute.side_effect = [mock_result, mock_result2]

        result = await service.create_transaction(request)

        service.repo.create.assert_called_once()

    async def test_raises_when_neither_card_nor_account(self):
        """
        COTRN02C: Card number blank AND account ID blank → error.
        This is validated at schema level (Pydantic @model_validator).
        """
        with pytest.raises(Exception):  # Pydantic ValidationError
            TransactionCreateRequest(
                transaction_type_code="01",
                description="test",
                amount=Decimal("-10.00"),
                original_date=date(2026, 1, 1),
                processed_date=date(2026, 1, 2),
                merchant_id="123456789",
                merchant_name="TEST",
                confirm="Y",
            )

    async def test_raises_when_amount_is_zero(self):
        """COTRN02C VALIDATE-INPUT-FIELDS: TRNAMI = 0 → error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            make_create_request(amount=Decimal("0.00"))

    async def test_raises_when_processed_before_original(self):
        """COTRN02C: TRNPROCI < TRNORIGI (CSUTLDTC date order) → error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            make_create_request(
                original_date=date(2026, 4, 5),
                processed_date=date(2026, 4, 4),  # before original
            )

    async def test_confirm_y_required(self):
        """COTRN02C: CONFIRMI must be 'Y' — gating condition before ADD-TRANSACTION."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            make_create_request(confirm="N")

    async def test_raises_card_not_found_when_xref_missing(self, service, mock_db):
        """COTRN02C LOOKUP-ACCT-FROM-CARD: CCXREF NOTFND → CardNotFoundError."""
        request = make_create_request(card_number="9999999999999999")
        service.repo = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # card not in xref
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(CardNotFoundError):
            await service.create_transaction(request)

    async def test_sequence_id_used_not_browse(self, service, mock_db):
        """
        COTRN02C BUG FIX: transaction_id generated via sequence, not STARTBR/READPREV.
        Verifies generate_transaction_id() is called.
        """
        request = make_create_request()
        created = make_transaction(transaction_id="0000000000000099")

        service.repo = AsyncMock()
        service.repo.generate_transaction_id.return_value = "0000000000000099"
        service.repo.create.return_value = created

        mock_xref = MagicMock()
        mock_xref.account_id = 10000000001
        mock_type = MagicMock()

        mock_result_xref = MagicMock()
        mock_result_xref.scalar_one_or_none.return_value = mock_xref
        mock_result_type = MagicMock()
        mock_result_type.scalar_one_or_none.return_value = mock_type
        mock_db.execute = AsyncMock(side_effect=[mock_result_xref, mock_result_type])

        await service.create_transaction(request)

        service.repo.generate_transaction_id.assert_called_once()

    async def test_raises_type_not_found_when_type_invalid(self, service, mock_db):
        """COTRN02C: invalid type_code → TransactionTypeNotFoundError."""
        request = make_create_request(transaction_type_code="99")
        service.repo = AsyncMock()

        mock_xref = MagicMock()
        mock_xref.account_id = 10000000001
        mock_result_xref = MagicMock()
        mock_result_xref.scalar_one_or_none.return_value = mock_xref

        # Type code not found
        mock_result_type = MagicMock()
        mock_result_type.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(side_effect=[mock_result_xref, mock_result_type])

        with pytest.raises(TransactionTypeNotFoundError):
            await service.create_transaction(request)


# =============================================================================
# get_last_transaction tests — COTRN02C PF5 COPY-LAST-TRAN-DATA
# =============================================================================


class TestGetLastTransaction:
    async def test_returns_last_transaction(self, service):
        """COTRN02C PF5: returns most recently created transaction."""
        mock_transaction = make_transaction("0000000000000050")
        service.repo = AsyncMock()
        service.repo.get_last_created.return_value = mock_transaction

        result = await service.get_last_transaction()

        assert result is not None
        assert result.transaction_id == "0000000000000050"

    async def test_returns_none_when_no_transactions(self, service):
        """COTRN02C PF5: no transactions yet → returns None (no pre-population)."""
        service.repo = AsyncMock()
        service.repo.get_last_created.return_value = None

        result = await service.get_last_transaction()

        assert result is None
