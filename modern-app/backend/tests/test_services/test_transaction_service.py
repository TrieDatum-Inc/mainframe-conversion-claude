"""Tests for TransactionService — COTRN00C, COTRN01C, COTRN02C business logic."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.exceptions.handlers import TransactionNotFoundError
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import TransactionService
from app.utils.helpers import format_transaction_id


class TestListTransactions:
    """COTRN00C: paginated transaction list."""

    async def test_list_returns_page(self, db_session, multiple_transactions):
        service = TransactionService(db_session)
        page = await service.list_transactions(page=1, page_size=10)
        assert len(page.items) == 10
        assert page.total == 15
        assert page.has_next is True
        assert page.has_prev is False

    async def test_page_two(self, db_session, multiple_transactions):
        service = TransactionService(db_session)
        page = await service.list_transactions(page=2, page_size=10)
        assert len(page.items) == 5
        assert page.has_next is False
        assert page.has_prev is True

    async def test_filter_by_card_number(self, db_session, sample_transaction):
        service = TransactionService(db_session)
        page = await service.list_transactions(card_number="4000002000000000")
        assert len(page.items) == 1
        assert page.items[0].card_number == "4000002000000000"

    async def test_filter_by_transaction_id_prefix(self, db_session, multiple_transactions):
        service = TransactionService(db_session)
        page = await service.list_transactions(transaction_id_prefix="0000000000000001")
        # Prefix matches IDs starting with 0000000000000001 (1, 10-15)
        assert page.total >= 1

    async def test_empty_list(self, db_session):
        service = TransactionService(db_session)
        page = await service.list_transactions()
        assert page.items == []
        assert page.total == 0


class TestGetTransaction:
    """COTRN01C: single transaction detail lookup."""

    async def test_found(self, db_session, sample_transaction):
        service = TransactionService(db_session)
        detail = await service.get_transaction("0000000000000001")
        assert detail.transaction_id == "0000000000000001"
        assert detail.amount == Decimal("-45.67")
        assert detail.merchant_name == "TEST MARKET"

    async def test_not_found_raises_404(self, db_session):
        service = TransactionService(db_session)
        with pytest.raises(TransactionNotFoundError):
            await service.get_transaction("9999999999999999")

    async def test_all_fields_populated(self, db_session, sample_transaction):
        service = TransactionService(db_session)
        detail = await service.get_transaction("0000000000000001")
        assert detail.type_code == "01"
        assert detail.category_code == "0001"
        assert detail.source == "POS TERM"
        assert detail.merchant_id == "123456789"
        assert detail.merchant_city == "NEW YORK"
        assert detail.merchant_zip == "10001"


class TestGenerateTransactionId:
    """COTRN02C: STARTBR HIGH-VALUES + READPREV max+1 pattern."""

    async def test_first_transaction_gets_id_1(self, db_session):
        service = TransactionService(db_session)
        new_id = await service._generate_next_transaction_id()
        assert new_id == "0000000000000001"

    async def test_increments_from_existing(self, db_session, sample_transaction):
        service = TransactionService(db_session)
        new_id = await service._generate_next_transaction_id()
        assert new_id == "0000000000000002"

    async def test_id_is_zero_padded_to_16_chars(self, db_session):
        service = TransactionService(db_session)
        new_id = await service._generate_next_transaction_id()
        assert len(new_id) == 16
        assert new_id.startswith("0")


class TestCreateTransaction:
    """COTRN02C: create transaction with CONFIRM='Y' guard."""

    async def test_unconfirmed_raises_value_error(self, db_session):
        service = TransactionService(db_session)
        payload = _create_payload(confirmed=False)
        with pytest.raises(ValueError, match="confirmed"):
            await service.create_transaction(payload, "4000002000000000", "00000001000")

    async def test_confirmed_creates_record(self, db_session):
        service = TransactionService(db_session)
        payload = _create_payload(confirmed=True)
        detail = await service.create_transaction(payload, "4000002000000000", "00000001000")
        assert detail.transaction_id == "0000000000000001"
        assert detail.amount == Decimal("-75.00")
        assert detail.card_number == "4000002000000000"

    async def test_amount_preserved_exactly(self, db_session):
        service = TransactionService(db_session)
        payload = _create_payload(confirmed=True, amount=Decimal("-12345678.99"))
        detail = await service.create_transaction(payload, "4000002000000000", "00000001000")
        assert detail.amount == Decimal("-12345678.99")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_payload(**overrides) -> TransactionCreate:
    data = {
        "card_number": "4000002000000000",
        "type_code": "01",
        "category_code": "0001",
        "source": "POS TERM",
        "description": "TEST PURCHASE",
        "amount": Decimal("-75.00"),
        "original_date": date(2024, 3, 1),
        "processing_date": date(2024, 3, 1),
        "merchant_id": "123456789",
        "merchant_name": "TEST MARKET",
        "merchant_city": "NEW YORK",
        "merchant_zip": "10001",
        "confirmed": True,
    }
    data.update(overrides)
    return TransactionCreate(**data)
