"""
Integration tests for credit card API endpoints.

Tests:
  GET  /api/v1/cards              → COCRDLIC (list)
  GET  /api/v1/cards/{card_number} → COCRDSLC (view)
  PUT  /api/v1/cards/{card_number} → COCRDUPC (update)

Uses FastAPI TestClient with mocked services.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.errors import CardNotFoundError, CardOptimisticLockError
from app.schemas.credit_card import (
    CardDetailResponse,
    CardListItem,
    CardListResponse,
)


def make_card_list_response(count: int = 7) -> CardListResponse:
    """Build a mock CardListResponse."""
    items = [
        CardListItem(
            card_number=f"4111111111111{i:03d}0",
            card_number_masked=f"************{i:03d}0",
            account_id=10000000001 + i,
            active_status="Y",
        )
        for i in range(count)
    ]
    return CardListResponse(
        items=items,
        page=1,
        page_size=7,
        total_count=count,
        has_next=False,
        has_previous=False,
    )


def make_card_detail_response(card_number: str = "4111111111111001") -> CardDetailResponse:
    """Build a mock CardDetailResponse."""
    return CardDetailResponse(
        card_number=card_number,
        account_id=10000000001,
        card_embossed_name="JAMES E ANDERSON",
        active_status="Y",
        expiration_month=1,
        expiration_year=2027,
        expiration_day=28,
        updated_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


class TestListCards:
    """Tests for GET /api/v1/cards."""

    @pytest.mark.asyncio
    async def test_list_cards_success(self, client) -> None:
        """Happy path: returns paginated card list."""
        mock_response = make_card_list_response(7)

        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.list_cards",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await client.get("/api/v1/cards")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 7
        assert len(data["items"]) == 7

    @pytest.mark.asyncio
    async def test_list_cards_masked_numbers(self, client) -> None:
        """Card numbers in list must be masked per PCI-DSS."""
        mock_response = make_card_list_response(1)

        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.list_cards",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await client.get("/api/v1/cards")

        assert response.status_code == 200
        # Verify masked representation exists in response
        item = response.json()["items"][0]
        assert "card_number_masked" in item
        assert item["card_number_masked"].startswith("****")

    @pytest.mark.asyncio
    async def test_list_cards_with_account_filter(self, client) -> None:
        """account_id filter passed through to service."""
        mock_response = make_card_list_response(1)

        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.list_cards",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_service:
            response = await client.get("/api/v1/cards?account_id=10000000001")

        assert response.status_code == 200
        # Verify account_id was passed
        call_kwargs = mock_service.call_args.kwargs
        assert call_kwargs.get("account_id") == 10000000001

    @pytest.mark.asyncio
    async def test_list_cards_default_page_size_7(self, client) -> None:
        """Default page_size=7 matches COCRDLIC original 7-row display."""
        mock_response = make_card_list_response()

        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.list_cards",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_service:
            await client.get("/api/v1/cards")

        call_kwargs = mock_service.call_args.kwargs
        assert call_kwargs.get("page_size") == 7

    @pytest.mark.asyncio
    async def test_list_cards_unauthenticated_returns_401(self, client) -> None:
        """No token → 401."""
        client.headers.clear()
        response = await client.get("/api/v1/cards")
        assert response.status_code == 401


class TestGetCard:
    """Tests for GET /api/v1/cards/{card_number}."""

    @pytest.mark.asyncio
    async def test_get_card_success(self, client) -> None:
        """Happy path: returns card detail with expiry parts."""
        mock_response = make_card_detail_response()

        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.view_card",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await client.get("/api/v1/cards/4111111111111001")

        assert response.status_code == 200
        data = response.json()
        assert data["card_number"] == "4111111111111001"
        assert data["account_id"] == 10000000001
        assert data["expiration_month"] == 1
        assert data["expiration_year"] == 2027
        # updated_at present for optimistic lock
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_card_not_found_returns_404(self, client) -> None:
        """COBOL: COCRDSLC READ CARDDAT RESP=NOTFND → 404."""
        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.view_card",
            new_callable=AsyncMock,
            side_effect=CardNotFoundError("0000000000000000"),
        ):
            response = await client.get("/api/v1/cards/0000000000000000")

        assert response.status_code == 404
        assert response.json()["detail"]["error_code"] == "CARD_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_card_accessible_by_regular_user(self, regular_client) -> None:
        """Card view is accessible to regular users (not admin-only)."""
        mock_response = make_card_detail_response()

        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.view_card",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await regular_client.get("/api/v1/cards/4111111111111001")

        assert response.status_code == 200


class TestUpdateCard:
    """Tests for PUT /api/v1/cards/{card_number}."""

    def make_update_payload(
        self,
        lock_version: str = "2026-01-01T12:00:00+00:00",
    ) -> dict:
        """Build a valid card update payload."""
        return {
            "card_embossed_name": "JAMES E ANDERSON",
            "active_status": "Y",
            "expiration_month": 1,
            "expiration_year": 2027,
            "expiration_day": 28,
            "optimistic_lock_version": lock_version,
        }

    @pytest.mark.asyncio
    async def test_update_card_success(self, client) -> None:
        """Happy path: valid update returns updated card detail."""
        mock_response = make_card_detail_response()

        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.update_card",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await client.put(
                "/api/v1/cards/4111111111111001",
                json=self.make_update_payload(),
            )

        assert response.status_code == 200
        data = response.json()
        assert data["card_number"] == "4111111111111001"

    @pytest.mark.asyncio
    async def test_update_card_optimistic_lock_conflict_returns_409(self, client) -> None:
        """
        COBOL: COCRDUPC CCUP-OLD-DETAILS mismatch → SYNCPOINT ROLLBACK → 409.
        """
        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.update_card",
            new_callable=AsyncMock,
            side_effect=CardOptimisticLockError(),
        ):
            response = await client.put(
                "/api/v1/cards/4111111111111001",
                json=self.make_update_payload(
                    lock_version="2025-01-01T12:00:00+00:00"
                ),
            )

        assert response.status_code == 409
        assert response.json()["detail"]["error_code"] == "OPTIMISTIC_LOCK_CONFLICT"

    @pytest.mark.asyncio
    async def test_update_card_missing_lock_version_returns_422(self, client) -> None:
        """optimistic_lock_version is required in update request."""
        payload = {
            "card_embossed_name": "JAMES E ANDERSON",
            "active_status": "Y",
            "expiration_month": 1,
            "expiration_year": 2027,
            # missing optimistic_lock_version
        }
        response = await client.put("/api/v1/cards/4111111111111001", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_card_invalid_active_status_returns_422(self, client) -> None:
        """active_status must be Y or N."""
        payload = self.make_update_payload()
        payload["active_status"] = "X"  # invalid

        response = await client.put(
            "/api/v1/cards/4111111111111001", json=payload
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_card_expiry_month_out_of_range_returns_422(self, client) -> None:
        """COCRDUPC: expiration_month must be 1-12."""
        payload = self.make_update_payload()
        payload["expiration_month"] = 13  # invalid

        response = await client.put(
            "/api/v1/cards/4111111111111001", json=payload
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_card_expiry_year_out_of_range_returns_422(self, client) -> None:
        """COCRDUPC: expiration_year must be 1950-2099."""
        payload = self.make_update_payload()
        payload["expiration_year"] = 2100  # out of range

        response = await client.put(
            "/api/v1/cards/4111111111111001", json=payload
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_card_not_found_returns_404(self, client) -> None:
        """COBOL: COCRDUPC READ CARDDAT RESP=NOTFND → 404."""
        with patch(
            "app.api.endpoints.credit_cards.credit_card_service.update_card",
            new_callable=AsyncMock,
            side_effect=CardNotFoundError("0000000000000000"),
        ):
            response = await client.put(
                "/api/v1/cards/0000000000000000",
                json=self.make_update_payload(),
            )

        assert response.status_code == 404
