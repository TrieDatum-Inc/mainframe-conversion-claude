"""
Unit tests for credit_card_service.py.

COBOL origin tested:
  COCRDLIC: list_cards (7-row paginated browse)
  COCRDSLC: view_card (READ CARDDAT by card_number)
  COCRDUPC: update_card (validate + optimistic lock + REWRITE)

Test coverage goals:
  - Card number masking in list responses (PCI-DSS)
  - Pagination: has_next/has_previous correct
  - 404: card not found
  - 409: optimistic lock conflict (CCUP-OLD-DETAILS mismatch)
  - Embossed name alpha-only validation (INSPECT CONVERTING equivalent)
  - account_id NOT updated (PROT field)
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.errors import CardNotFoundError, CardOptimisticLockError
from app.services import credit_card_service


def make_mock_card(
    card_number: str = "4111111111111001",
    account_id: int = 10000000001,
    active_status: str = "Y",
    exp_date_year: int = 2027,
    exp_date_month: int = 1,
    updated_at: datetime | None = None,
) -> MagicMock:
    """Create a mock CreditCard ORM object."""
    from datetime import date

    card = MagicMock()
    card.card_number = card_number
    card.account_id = account_id
    card.customer_id = 100000001
    card.card_embossed_name = "JAMES E ANDERSON"
    card.active_status = active_status
    card.expiration_date = date(exp_date_year, exp_date_month, 28)
    card.expiration_day = 28
    card.updated_at = updated_at or datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return card


class TestMaskCardNumber:
    """Tests for card number masking — PCI-DSS compliance."""

    def test_masks_standard_16_digit_card(self) -> None:
        """Show only last 4 digits — COCRDLIC displayed full number but modern PCI rules apply."""
        result = credit_card_service._mask_card_number("4111111111111001")
        assert result == "************1001"

    def test_masks_card_with_different_last_4(self) -> None:
        result = credit_card_service._mask_card_number("4111111111119999")
        assert result == "************9999"


class TestListCards:
    """Tests for list_cards — maps COCRDLIC POPULATE-USER-DATA."""

    @pytest.mark.asyncio
    async def test_list_cards_returns_masked_numbers(self) -> None:
        """Card numbers in list response must be masked."""
        mock_db = AsyncMock()
        mock_cards = [make_mock_card(card_number=f"411111111111{i:04d}") for i in range(7)]

        with patch.object(
            credit_card_service.CreditCardRepository,
            "list_by_filters",
            return_value=(mock_cards, 7),
        ):
            response = await credit_card_service.list_cards(
                db=mock_db, page=1, page_size=7
            )

        assert len(response.items) == 7
        for item in response.items:
            # All items should have masked card number
            assert item.card_number_masked.startswith("****")
            assert len(item.card_number_masked) == 16

    @pytest.mark.asyncio
    async def test_list_cards_pagination_has_next(self) -> None:
        """has_next=True when more records exist beyond current page."""
        mock_db = AsyncMock()
        mock_cards = [make_mock_card() for _ in range(7)]

        with patch.object(
            credit_card_service.CreditCardRepository,
            "list_by_filters",
            return_value=(mock_cards, 15),  # 15 total, 7 per page
        ):
            response = await credit_card_service.list_cards(
                db=mock_db, page=1, page_size=7
            )

        assert response.has_next is True
        assert response.has_previous is False
        assert response.total_count == 15

    @pytest.mark.asyncio
    async def test_list_cards_pagination_has_previous(self) -> None:
        """has_previous=True on page 2+."""
        mock_db = AsyncMock()
        mock_cards = [make_mock_card()]

        with patch.object(
            credit_card_service.CreditCardRepository,
            "list_by_filters",
            return_value=(mock_cards, 15),
        ):
            response = await credit_card_service.list_cards(
                db=mock_db, page=2, page_size=7
            )

        assert response.has_previous is True

    @pytest.mark.asyncio
    async def test_list_cards_with_account_filter(self) -> None:
        """account_id filter passed to repository — replaces COCRDLIC ACCTSID filter."""
        mock_db = AsyncMock()

        with patch.object(
            credit_card_service.CreditCardRepository,
            "list_by_filters",
            return_value=([], 0),
        ) as mock_list:
            await credit_card_service.list_cards(
                db=mock_db, account_id=10000000001, page=1, page_size=7
            )

        mock_list.assert_called_once_with(
            account_id=10000000001, card_number=None, page=1, page_size=7
        )


class TestViewCard:
    """Tests for view_card — maps COCRDSLC PROCESS-ENTER-KEY."""

    @pytest.mark.asyncio
    async def test_view_card_success(self) -> None:
        """Happy path: card found, returns full detail with expiration parts."""
        mock_db = AsyncMock()
        mock_card = make_mock_card()

        with patch.object(
            credit_card_service.CreditCardRepository,
            "get_by_number",
            return_value=mock_card,
        ):
            response = await credit_card_service.view_card(
                card_number="4111111111111001", db=mock_db
            )

        assert response.card_number == "4111111111111001"
        assert response.account_id == 10000000001
        assert response.expiration_month == 1  # extracted from expiration_date
        assert response.expiration_year == 2027
        assert response.active_status == "Y"

    @pytest.mark.asyncio
    async def test_view_card_not_found_raises_404(self) -> None:
        """COBOL: COCRDSLC READ CARDDAT RESP=NOTFND → 404."""
        mock_db = AsyncMock()

        with patch.object(
            credit_card_service.CreditCardRepository,
            "get_by_number",
            return_value=None,
        ):
            with pytest.raises(CardNotFoundError):
                await credit_card_service.view_card(
                    card_number="0000000000000000", db=mock_db
                )


class TestUpdateCard:
    """Tests for update_card — maps COCRDUPC UPDATE-CARD."""

    @pytest.mark.asyncio
    async def test_update_card_not_found_raises_404(self) -> None:
        """COBOL: COCRDUPC READ CARDDAT RESP=NOTFND → 404."""
        mock_db = AsyncMock()

        with patch.object(
            credit_card_service.CreditCardRepository,
            "get_by_number",
            return_value=None,
        ):
            with pytest.raises(CardNotFoundError):
                await credit_card_service.update_card(
                    card_number="0000000000000000",
                    request=MagicMock(),
                    db=mock_db,
                )

    @pytest.mark.asyncio
    async def test_update_card_optimistic_lock_conflict_raises_409(self) -> None:
        """
        COBOL: COCRDUPC CCUP-OLD-DETAILS snapshot mismatch → SYNCPOINT ROLLBACK → 409.
        updated_at in request differs from stored updated_at.
        """
        mock_db = AsyncMock()
        stored_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        stale_ts = datetime(2025, 12, 1, 12, 0, 0, tzinfo=timezone.utc)  # older

        mock_card = make_mock_card(updated_at=stored_ts)

        request = MagicMock()
        request.optimistic_lock_version = stale_ts

        with patch.object(
            credit_card_service.CreditCardRepository,
            "get_by_number",
            return_value=mock_card,
        ):
            with pytest.raises(CardOptimisticLockError):
                await credit_card_service.update_card(
                    card_number="4111111111111001",
                    request=request,
                    db=mock_db,
                )

    @pytest.mark.asyncio
    async def test_update_card_invalid_embossed_name_raises_value_error(self) -> None:
        """COBOL: COCRDUPC INSPECT CONVERTING validates alpha-only embossed name."""
        mock_db = AsyncMock()
        ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_card = make_mock_card(updated_at=ts)

        request = MagicMock()
        request.optimistic_lock_version = ts  # lock matches
        request.card_embossed_name = "INVALID123!@#"  # non-alpha chars
        request.active_status = "Y"
        request.expiration_month = 1
        request.expiration_year = 2027
        request.expiration_day = 28

        with patch.object(
            credit_card_service.CreditCardRepository,
            "get_by_number",
            return_value=mock_card,
        ):
            with pytest.raises(ValueError, match="alpha"):
                await credit_card_service.update_card(
                    card_number="4111111111111001",
                    request=request,
                    db=mock_db,
                )

    @pytest.mark.asyncio
    async def test_update_card_success(self) -> None:
        """Happy path: valid update, account_id NOT changed (PROT field)."""
        mock_db = AsyncMock()
        ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_card = make_mock_card(updated_at=ts)
        updated_card = make_mock_card(
            updated_at=datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        )
        updated_card.card_embossed_name = "JAMES UPDATED"
        updated_card.active_status = "N"

        request = MagicMock()
        request.optimistic_lock_version = ts
        request.card_embossed_name = "JAMES UPDATED"  # valid alpha
        request.active_status = "N"
        request.expiration_month = 6
        request.expiration_year = 2028
        request.expiration_day = 30

        with (
            patch.object(
                credit_card_service.CreditCardRepository,
                "get_by_number",
                return_value=mock_card,
            ),
            patch.object(
                credit_card_service.CreditCardRepository,
                "update",
                return_value=updated_card,
            ),
        ):
            response = await credit_card_service.update_card(
                card_number="4111111111111001",
                request=request,
                db=mock_db,
            )

        assert response.card_number == "4111111111111001"
        assert response.active_status == "N"
        # account_id unchanged — PROT field
        assert response.account_id == 10000000001


class TestValidateEmbossedName:
    """Tests for _validate_embossed_name — COCRDUPC INSPECT CONVERTING equivalent."""

    def test_valid_alpha_name(self) -> None:
        """Pure alpha with space and hyphen — valid."""
        credit_card_service._validate_embossed_name("JAMES EDWARD ANDERSON")
        credit_card_service._validate_embossed_name("MARY-JANE SMITH")

    def test_invalid_name_with_digits(self) -> None:
        """Digits not allowed in embossed name."""
        with pytest.raises(ValueError):
            credit_card_service._validate_embossed_name("JAMES123")

    def test_invalid_name_with_special_chars(self) -> None:
        """Special characters not allowed."""
        with pytest.raises(ValueError):
            credit_card_service._validate_embossed_name("JAMES!SMITH")
