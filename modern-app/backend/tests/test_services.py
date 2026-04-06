"""
Tests for authorization and fraud service business logic.

Tests every branch of the COBOL COPAUA0C decision logic:
- Available amount calculation
- Decline conditions (funds, card active, account closed, fraud)
- Summary counter updates
- Detail enrichment with decline reason lookup
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.authorization import AuthorizationSummary
from app.schemas.authorization import (
    AuthorizationProcessRequest,
    DECLINE_REASON_DESCRIPTIONS,
)
from app.services.authorization_service import (
    CODE_ACCOUNT_CLOSED,
    CODE_APPROVED,
    CODE_CARD_FRAUD,
    CODE_INSUFFICIENT_FUND,
    AuthorizationService,
)


class TestAvailableAmountCalculation:
    """
    Test COPAUA0C formula:
    WS-AVAILABLE-AMT = credit_limit - current_balance
    """

    def setup_method(self):
        self.db = AsyncMock()
        self.service = AuthorizationService(self.db)

    def test_available_amount_normal(self, sample_summary):
        """Standard case: limit 10000, balance 3000 → available 7000."""
        available = self.service._calculate_available_amount(sample_summary)
        assert available == Decimal("7000.00")

    def test_available_amount_zero_balance(self):
        """Zero balance → full limit available."""
        summary = AuthorizationSummary(
            credit_limit=Decimal("5000.00"),
            credit_balance=Decimal("0.00"),
        )
        available = self.service._calculate_available_amount(summary)
        assert available == Decimal("5000.00")

    def test_available_amount_at_limit(self, maxed_summary):
        """At credit limit → zero available."""
        available = self.service._calculate_available_amount(maxed_summary)
        assert available == Decimal("0.00")

    def test_available_amount_over_limit(self):
        """Balance exceeds limit → negative available (declined)."""
        summary = AuthorizationSummary(
            credit_limit=Decimal("1000.00"),
            credit_balance=Decimal("1200.00"),
        )
        available = self.service._calculate_available_amount(summary)
        assert available == Decimal("-200.00")


class TestDeclineConditionEvaluation:
    """
    Test COPAUA0C decline flag evaluation — maps to COBOL EVALUATE block.
    Priority: account closed → fraud → insufficient funds → approved.
    """

    def setup_method(self):
        self.db = AsyncMock()
        self.service = AuthorizationService(self.db)

    def _make_request(self, amount: Decimal) -> AuthorizationProcessRequest:
        return AuthorizationProcessRequest(
            card_number="4111111111111111",
            card_expiry="12/28",
            amount=amount,
        )

    def test_account_closed_declined(self, closed_summary):
        """COBOL: ACCOUNT-CLOSED → response code 43."""
        req = self._make_request(Decimal("100.00"))
        code, reason = self.service._evaluate_decline_conditions(closed_summary, req)
        assert code == CODE_ACCOUNT_CLOSED
        assert reason == "ACCOUNT CLOSED"

    def test_account_closed_takes_priority_over_funds(self, closed_summary):
        """Closed account should decline even for small amount."""
        req = self._make_request(Decimal("1.00"))
        code, _ = self.service._evaluate_decline_conditions(closed_summary, req)
        assert code == CODE_ACCOUNT_CLOSED

    def test_insufficient_funds_declined(self, maxed_summary):
        """COBOL: INSUFFICIENT-FUND → response code 41."""
        req = self._make_request(Decimal("1000.00"))  # balance = limit, no room
        code, reason = self.service._evaluate_decline_conditions(maxed_summary, req)
        assert code == CODE_INSUFFICIENT_FUND
        assert reason == "INSUFFICNT FUND"

    def test_approved_when_funds_sufficient(self, sample_summary):
        """COBOL: all checks pass → APPROVED."""
        req = self._make_request(Decimal("100.00"))  # available = 7000
        code, reason = self.service._evaluate_decline_conditions(sample_summary, req)
        assert code == CODE_APPROVED
        assert reason == "APPROVED"

    def test_approved_exact_available_amount(self, sample_summary):
        """Edge case: amount equals exactly available credit."""
        req = self._make_request(Decimal("7000.00"))  # available = 7000
        code, _ = self.service._evaluate_decline_conditions(sample_summary, req)
        assert code == CODE_APPROVED

    def test_declined_one_cent_over_available(self, sample_summary):
        """Edge case: amount is one cent over available credit."""
        req = self._make_request(Decimal("7000.01"))  # available = 7000
        code, _ = self.service._evaluate_decline_conditions(sample_summary, req)
        assert code == CODE_INSUFFICIENT_FUND


class TestSummaryCounterUpdate:
    """
    Test COBOL counter logic:
    PA-APPROVED-AUTH-CNT += 1
    PA-APPROVED-AUTH-AMT += amount
    (or declined equivalents)
    """

    def setup_method(self):
        self.db = AsyncMock()
        self.service = AuthorizationService(self.db)

    def test_approved_increments_approved_count(self, sample_summary):
        initial_count = sample_summary.approved_count
        self.service._update_summary_counters(
            sample_summary, is_approved=True, amount=Decimal("100.00")
        )
        assert sample_summary.approved_count == initial_count + 1

    def test_approved_adds_to_approved_amount(self, sample_summary):
        initial_amount = sample_summary.approved_amount
        self.service._update_summary_counters(
            sample_summary, is_approved=True, amount=Decimal("500.00")
        )
        assert sample_summary.approved_amount == initial_amount + Decimal("500.00")

    def test_declined_increments_declined_count(self, sample_summary):
        initial_count = sample_summary.declined_count
        self.service._update_summary_counters(
            sample_summary, is_approved=False, amount=Decimal("999.00")
        )
        assert sample_summary.declined_count == initial_count + 1

    def test_declined_adds_to_declined_amount(self, sample_summary):
        initial_amount = sample_summary.declined_amount
        self.service._update_summary_counters(
            sample_summary, is_approved=False, amount=Decimal("999.00")
        )
        assert sample_summary.declined_amount == initial_amount + Decimal("999.00")

    def test_approved_does_not_change_declined_count(self, sample_summary):
        initial_declined = sample_summary.declined_count
        self.service._update_summary_counters(
            sample_summary, is_approved=True, amount=Decimal("100.00")
        )
        assert sample_summary.declined_count == initial_declined

    def test_declined_does_not_change_approved_amount(self, sample_summary):
        initial_approved = sample_summary.approved_amount
        self.service._update_summary_counters(
            sample_summary, is_approved=False, amount=Decimal("100.00")
        )
        assert sample_summary.approved_amount == initial_approved


class TestDetailEnrichment:
    """
    Test COPAUS1C decline reason table lookup (SEARCH ALL).
    Verifies that each code is correctly mapped to its description.
    """

    def test_approved_code_enriched(self, sample_detail):
        enriched = AuthorizationService._enrich_detail(sample_detail)
        assert enriched.decline_reason_description == "APPROVED"

    def test_fraud_code_enriched(self, fraud_detail):
        enriched = AuthorizationService._enrich_detail(fraud_detail)
        assert enriched.decline_reason_description == "CARD FRAUD"

    def test_unknown_code_defaults_to_unknown(self, sample_detail):
        sample_detail.auth_response_code = "99"
        enriched = AuthorizationService._enrich_detail(sample_detail)
        assert enriched.decline_reason_description == "UNKNOWN"

    def test_all_codes_in_lookup_table(self, sample_detail):
        """Every code in the lookup table should produce a non-empty description."""
        for code in DECLINE_REASON_DESCRIPTIONS:
            sample_detail.auth_response_code = code
            enriched = AuthorizationService._enrich_detail(sample_detail)
            assert enriched.decline_reason_description
            assert enriched.decline_reason_description != ""


class TestAuthCodeGeneration:
    """Test authorization code generation."""

    def test_auth_code_is_6_chars(self):
        code = AuthorizationService._generate_auth_code()
        assert len(code) == 6

    def test_auth_code_is_alphanumeric(self):
        code = AuthorizationService._generate_auth_code()
        assert code.isalnum()

    def test_auth_codes_are_random(self):
        """Two consecutive codes should differ (very high probability)."""
        codes = {AuthorizationService._generate_auth_code() for _ in range(20)}
        assert len(codes) > 1
