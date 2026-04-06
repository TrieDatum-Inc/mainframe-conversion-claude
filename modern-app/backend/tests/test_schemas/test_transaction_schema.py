"""Tests for transaction Pydantic schemas — validation rules from COTRN02C."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.transaction import TransactionCreate


class TestTransactionCreateAmount:
    """COTRN02C business rule: amount must be in format -99999999.99."""

    def test_valid_negative_amount(self):
        data = _base_payload(amount=Decimal("-45.67"))
        result = TransactionCreate(**data)
        assert result.amount == Decimal("-45.67")

    def test_valid_positive_amount(self):
        data = _base_payload(amount=Decimal("1234.56"))
        result = TransactionCreate(**data)
        assert result.amount == Decimal("1234.56")

    def test_amount_at_max_boundary(self):
        data = _base_payload(amount=Decimal("99999999.99"))
        result = TransactionCreate(**data)
        assert result.amount == Decimal("99999999.99")

    def test_amount_at_min_boundary(self):
        data = _base_payload(amount=Decimal("-99999999.99"))
        result = TransactionCreate(**data)
        assert result.amount == Decimal("-99999999.99")

    def test_amount_exceeds_max(self):
        data = _base_payload(amount=Decimal("100000000.00"))
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        assert "99999999.99" in str(exc_info.value)

    def test_amount_below_min(self):
        data = _base_payload(amount=Decimal("-100000000.00"))
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        assert "99999999.99" in str(exc_info.value)


class TestTransactionCreateMerchantId:
    """COTRN02C business rule: Merchant ID must be all numeric."""

    def test_valid_numeric_merchant_id(self):
        data = _base_payload(merchant_id="123456789")
        result = TransactionCreate(**data)
        assert result.merchant_id == "123456789"

    def test_merchant_id_with_letters_rejected(self):
        data = _base_payload(merchant_id="ABC123456")
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        assert "digits" in str(exc_info.value).lower()

    def test_empty_merchant_id_allowed(self):
        data = _base_payload(merchant_id="")
        result = TransactionCreate(**data)
        assert result.merchant_id == ""


class TestTransactionCreateAccountCardResolution:
    """COTRN02C business rule: either account_id OR card_number required."""

    def test_account_id_only_valid(self):
        data = _base_payload()
        data["account_id"] = "00000001000"
        data.pop("card_number", None)
        result = TransactionCreate(**data)
        assert result.account_id == "00000001000"

    def test_card_number_only_valid(self):
        data = _base_payload()
        data["card_number"] = "4000002000000000"
        data.pop("account_id", None)
        result = TransactionCreate(**data)
        assert result.card_number == "4000002000000000"

    def test_neither_account_nor_card_rejected(self):
        data = _base_payload()
        data.pop("account_id", None)
        data.pop("card_number", None)
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(**data)
        assert "account_id" in str(exc_info.value).lower() or "card_number" in str(exc_info.value).lower()

    def test_both_account_and_card_valid(self):
        data = _base_payload()
        data["account_id"] = "00000001000"
        data["card_number"] = "4000002000000000"
        result = TransactionCreate(**data)
        assert result.account_id == "00000001000"
        assert result.card_number == "4000002000000000"


class TestTransactionCreateDates:
    """Date validation mirrors CSUTLDTC (CEEDAYS wrapper)."""

    def test_valid_iso_dates(self):
        data = _base_payload(original_date=date(2024, 1, 15))
        result = TransactionCreate(**data)
        assert result.original_date == date(2024, 1, 15)

    def test_confirmed_default_false(self):
        data = _base_payload()
        result = TransactionCreate(**data)
        assert result.confirmed is False


class TestTransactionCreateConfirmation:
    """COBOL CONFIRM='Y' pattern maps to confirmed=True."""

    def test_confirmed_true(self):
        data = _base_payload(confirmed=True)
        result = TransactionCreate(**data)
        assert result.confirmed is True

    def test_confirmed_false_by_default(self):
        data = _base_payload()
        result = TransactionCreate(**data)
        assert result.confirmed is False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_payload(**overrides) -> dict:
    base = {
        "card_number": "4000002000000000",
        "type_code": "01",
        "category_code": "0001",
        "source": "POS TERM",
        "description": "TEST PURCHASE",
        "amount": Decimal("-50.00"),
        "original_date": date(2024, 1, 10),
        "processing_date": date(2024, 1, 10),
        "merchant_id": "123456789",
        "merchant_name": "TEST MERCHANT",
        "merchant_city": "TEST CITY",
        "merchant_zip": "10001",
    }
    base.update(overrides)
    return base
