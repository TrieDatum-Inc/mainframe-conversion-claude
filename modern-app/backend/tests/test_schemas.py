"""
Tests for authorization and fraud Pydantic schemas.

Validates all input validation rules that mirror COBOL field-level checks.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.authorization import (
    AuthorizationProcessRequest,
    PurgeRequest,
    DECLINE_REASON_DESCRIPTIONS,
)
from app.schemas.fraud import FraudActionRequest


class TestAuthorizationProcessRequestSchema:
    """Test CCPAURQY-equivalent request validation."""

    def test_valid_request(self):
        req = AuthorizationProcessRequest(
            card_number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("100.00"),
            merchant_name="TEST MERCHANT",
        )
        assert req.card_number == "4111111111111111"
        assert req.amount == Decimal("100.00")

    def test_card_number_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            AuthorizationProcessRequest(
                card_number="411",
                card_expiry="12/28",
                amount=Decimal("100.00"),
            )
        assert "card_number" in str(exc_info.value)

    def test_card_number_too_long(self):
        with pytest.raises(ValidationError):
            AuthorizationProcessRequest(
                card_number="41111111111111111",  # 17 digits
                card_expiry="12/28",
                amount=Decimal("100.00"),
            )

    def test_card_number_non_numeric(self):
        with pytest.raises(ValidationError) as exc_info:
            AuthorizationProcessRequest(
                card_number="411111111111111A",
                card_expiry="12/28",
                amount=Decimal("100.00"),
            )
        assert "digits" in str(exc_info.value).lower()

    def test_card_expiry_invalid_format(self):
        with pytest.raises(ValidationError):
            AuthorizationProcessRequest(
                card_number="4111111111111111",
                card_expiry="1228",  # missing slash
                amount=Decimal("100.00"),
            )

    def test_card_expiry_valid_format(self):
        req = AuthorizationProcessRequest(
            card_number="4111111111111111",
            card_expiry="01/29",
            amount=Decimal("50.00"),
        )
        assert req.card_expiry == "01/29"

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError):
            AuthorizationProcessRequest(
                card_number="4111111111111111",
                card_expiry="12/28",
                amount=Decimal("0.00"),
            )

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            AuthorizationProcessRequest(
                card_number="4111111111111111",
                card_expiry="12/28",
                amount=Decimal("-10.00"),
            )

    def test_amount_quantized_to_2_decimals(self):
        req = AuthorizationProcessRequest(
            card_number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("99.999"),
        )
        assert req.amount == Decimal("100.00")

    def test_default_auth_type(self):
        req = AuthorizationProcessRequest(
            card_number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("50.00"),
        )
        assert req.auth_type == "SALE"

    def test_merchant_name_max_length(self):
        with pytest.raises(ValidationError):
            AuthorizationProcessRequest(
                card_number="4111111111111111",
                card_expiry="12/28",
                amount=Decimal("50.00"),
                merchant_name="A" * 26,  # exceeds 25 chars
            )


class TestFraudActionRequestSchema:
    """Test COPAUS2C action flag validation."""

    def test_mark_action_valid(self):
        req = FraudActionRequest(action="mark")
        assert req.action == "mark"

    def test_remove_action_valid(self):
        req = FraudActionRequest(action="remove")
        assert req.action == "remove"

    def test_invalid_action_rejected(self):
        with pytest.raises(ValidationError):
            FraudActionRequest(action="delete")

    def test_empty_action_rejected(self):
        with pytest.raises(ValidationError):
            FraudActionRequest(action="")


class TestPurgeRequestSchema:
    """Test CBPAUP0C P-EXPIRY-DAYS parameter validation."""

    def test_default_expiry_days(self):
        req = PurgeRequest()
        assert req.expiry_days == 5  # CBPAUP0C default P-EXPIRY-DAYS=5

    def test_custom_expiry_days(self):
        req = PurgeRequest(expiry_days=10)
        assert req.expiry_days == 10

    def test_zero_days_rejected(self):
        with pytest.raises(ValidationError):
            PurgeRequest(expiry_days=0)

    def test_negative_days_rejected(self):
        with pytest.raises(ValidationError):
            PurgeRequest(expiry_days=-1)

    def test_over_max_days_rejected(self):
        with pytest.raises(ValidationError):
            PurgeRequest(expiry_days=366)


class TestDeclineReasonTable:
    """Test the 10-entry decline reason lookup table from COPAUS1C."""

    def test_all_10_codes_present(self):
        """COPAUS1C defines exactly 10 reason codes."""
        assert len(DECLINE_REASON_DESCRIPTIONS) == 10

    def test_approved_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["00"] == "APPROVED"

    def test_insufficient_fund_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["41"] == "INSUFFICNT FUND"

    def test_card_not_active_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["42"] == "CARD NOT ACTIVE"

    def test_account_closed_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["43"] == "ACCOUNT CLOSED"

    def test_card_fraud_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["51"] == "CARD FRAUD"

    def test_merchant_fraud_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["52"] == "MERCHANT FRAUD"

    def test_invalid_card_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["31"] == "INVALID CARD"

    def test_exceed_daily_limit_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["44"] == "EXCED DAILY LMT"

    def test_lost_card_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["53"] == "LOST CARD"

    def test_unknown_code(self):
        assert DECLINE_REASON_DESCRIPTIONS["90"] == "UNKNOWN"
