"""Tests for bill payment schemas — COBIL00C business rule validation."""

import pytest
from pydantic import ValidationError

from app.schemas.bill_payment import BillPaymentRequest


class TestBillPaymentRequest:
    """COBIL00C: account_id max 11 chars, confirmed=True required to pay."""

    def test_valid_request_confirmed(self):
        req = BillPaymentRequest(account_id="00000001000", confirmed=True)
        assert req.account_id == "00000001000"
        assert req.confirmed is True

    def test_confirmed_defaults_false(self):
        req = BillPaymentRequest(account_id="00000001000")
        assert req.confirmed is False

    def test_account_id_too_long_rejected(self):
        with pytest.raises(ValidationError):
            BillPaymentRequest(account_id="123456789012")  # 12 chars, max 11
