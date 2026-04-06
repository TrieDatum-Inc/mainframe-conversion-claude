"""
Unit tests for credit_card_service.py.

Tests COCRDLIC (list), COCRDSLC (view), COCRDUPC (update) business logic.
Card masking, optimistic lock, alpha-only name validation.
"""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.exceptions.errors import NotFoundError, OptimisticLockError
from app.schemas.credit_card import CardUpdateRequest
from app.services.credit_card_service import (
    _mask_card_number,
    _build_expiry_date,
    _check_optimistic_lock,
    list_cards,
    view_card,
    update_card,
)


# =============================================================================
# Card number masking — PCI-DSS
# =============================================================================

class TestMaskCardNumber:
    def test_masks_16_digit_card(self):
        assert _mask_card_number("4185540994448062") == "************8062"

    def test_preserves_last_4(self):
        result = _mask_card_number("1234567890123456")
        assert result.endswith("3456")
        assert result.startswith("*")

    def test_handles_empty(self):
        assert _mask_card_number("") == ""

    def test_handles_short_card(self):
        assert _mask_card_number("123") == "123"


# =============================================================================
# Expiry date construction — EXPMON + EXPYEAR + EXPDAY
# =============================================================================

class TestBuildExpiryDate:
    def test_builds_valid_date(self):
        result = _build_expiry_date(12, 2026, 31)
        assert result == date(2026, 12, 31)

    def test_clamps_day_to_month_end(self):
        # February 2026 has 28 days
        result = _build_expiry_date(2, 2026, 31)
        assert result == date(2026, 2, 28)

    def test_defaults_day_to_1_if_none(self):
        result = _build_expiry_date(6, 2025, None)
        assert result == date(2025, 6, 1)

    def test_returns_none_for_missing_month(self):
        assert _build_expiry_date(None, 2026, 15) is None

    def test_returns_none_for_missing_year(self):
        assert _build_expiry_date(12, None, 15) is None


# =============================================================================
# Optimistic lock check — CCUP-OLD-DETAILS comparison
# =============================================================================

class TestCheckOptimisticLock:
    def test_raises_when_timestamps_differ(self):
        card = MagicMock()
        card.updated_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        old_version = "2026-01-01T11:00:00"  # different time
        with pytest.raises(OptimisticLockError):
            _check_optimistic_lock(card, old_version)

    def test_passes_when_timestamps_match(self):
        card = MagicMock()
        card.updated_at = datetime(2026, 1, 1, 12, 0, 0)
        lock_version = "2026-01-01T12:00:00"
        # Should not raise
        _check_optimistic_lock(card, lock_version)

    def test_raises_on_invalid_version_string(self):
        card = MagicMock()
        card.updated_at = datetime(2026, 1, 1, 12, 0, 0)
        with pytest.raises(OptimisticLockError):
            _check_optimistic_lock(card, "not-a-datetime")


# =============================================================================
# Alpha-only validation — INSPECT CONVERTING equivalent
# =============================================================================

class TestEmbossedNameValidation:
    def test_rejects_digits_in_name(self):
        with pytest.raises(Exception):
            CardUpdateRequest(
                card_embossed_name="JOHN123",
                active_status="Y",
                expiration_month=12,
                expiration_year=2026,
                optimistic_lock_version="2026-01-01T12:00:00",
            )

    def test_rejects_special_chars(self):
        with pytest.raises(Exception):
            CardUpdateRequest(
                card_embossed_name="JOHN@DOE",
                active_status="Y",
                expiration_month=12,
                expiration_year=2026,
                optimistic_lock_version="2026-01-01T12:00:00",
            )

    def test_accepts_letters_and_spaces(self):
        req = CardUpdateRequest(
            card_embossed_name="JOHN DOE",
            active_status="Y",
            expiration_month=12,
            expiration_year=2026,
            optimistic_lock_version="2026-01-01T12:00:00",
        )
        assert req.card_embossed_name == "JOHN DOE"

    def test_uppercases_name(self):
        req = CardUpdateRequest(
            card_embossed_name="john doe",
            active_status="Y",
            expiration_month=12,
            expiration_year=2026,
            optimistic_lock_version="2026-01-01T12:00:00",
        )
        assert req.card_embossed_name == "JOHN DOE"

    def test_rejects_blank_name(self):
        with pytest.raises(Exception):
            CardUpdateRequest(
                card_embossed_name="   ",
                active_status="Y",
                expiration_month=12,
                expiration_year=2026,
                optimistic_lock_version="2026-01-01T12:00:00",
            )


# =============================================================================
# Expiry validation
# =============================================================================

class TestExpiryValidation:
    def test_rejects_month_zero(self):
        with pytest.raises(Exception):
            CardUpdateRequest(
                card_embossed_name="JOHN DOE",
                active_status="Y",
                expiration_month=0,
                expiration_year=2026,
                optimistic_lock_version="2026-01-01T12:00:00",
            )

    def test_rejects_month_thirteen(self):
        with pytest.raises(Exception):
            CardUpdateRequest(
                card_embossed_name="JOHN DOE",
                active_status="Y",
                expiration_month=13,
                expiration_year=2026,
                optimistic_lock_version="2026-01-01T12:00:00",
            )

    def test_rejects_year_before_1950(self):
        with pytest.raises(Exception):
            CardUpdateRequest(
                card_embossed_name="JOHN DOE",
                active_status="Y",
                expiration_month=12,
                expiration_year=1949,
                optimistic_lock_version="2026-01-01T12:00:00",
            )

    def test_rejects_year_after_2099(self):
        with pytest.raises(Exception):
            CardUpdateRequest(
                card_embossed_name="JOHN DOE",
                active_status="Y",
                expiration_month=12,
                expiration_year=2100,
                optimistic_lock_version="2026-01-01T12:00:00",
            )
