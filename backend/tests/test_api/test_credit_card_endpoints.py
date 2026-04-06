"""
Integration tests for credit card endpoints.

Tests GET /api/v1/cards, GET /api/v1/cards/{card_number},
PUT /api/v1/cards/{card_number}.
"""

import pytest
from httpx import AsyncClient

from app.models.credit_card import CreditCard


class TestListCards:
    @pytest.mark.asyncio
    async def test_list_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/cards")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_cards_returns_masked_numbers(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_card: CreditCard,
    ):
        resp = await client.get("/api/v1/cards", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total_count"] >= 1
        # Verify masking
        for item in data["items"]:
            masked = item["card_number_masked"]
            assert masked.count("*") >= 1
            # Last 4 digits should match
            assert masked[-4:] == item["card_number"][-4:]

    @pytest.mark.asyncio
    async def test_list_default_page_size_is_7(
        self,
        client: AsyncClient,
        user_headers: dict,
    ):
        resp = await client.get("/api/v1/cards", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 7  # COCRDLIC WS-MAX-SCREEN-LINES=7

    @pytest.mark.asyncio
    async def test_list_filter_by_account_id(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_card: CreditCard,
    ):
        resp = await client.get(
            f"/api/v1/cards?account_id={sample_card.account_id}",
            headers=user_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["account_id"] == sample_card.account_id


class TestGetCard:
    @pytest.mark.asyncio
    async def test_get_card_not_found(
        self,
        client: AsyncClient,
        user_headers: dict,
    ):
        resp = await client.get("/api/v1/cards/9999999999999999", headers=user_headers)
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"]["error_code"] == "CARD_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_card_success(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_card: CreditCard,
    ):
        resp = await client.get(
            f"/api/v1/cards/{sample_card.card_number}",
            headers=user_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["card_number"] == sample_card.card_number.strip()
        assert data["account_id"] == sample_card.account_id
        assert "updated_at" in data  # optimistic lock version present
        assert data["expiration_month"] == 12
        assert data["expiration_year"] == 2026


class TestUpdateCard:
    @pytest.mark.asyncio
    async def test_update_card_success(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_card: CreditCard,
    ):
        # First get the card to get updated_at (optimistic lock version)
        get_resp = await client.get(
            f"/api/v1/cards/{sample_card.card_number}",
            headers=user_headers,
        )
        assert get_resp.status_code == 200
        lock_version = get_resp.json()["updated_at"]

        # Now update
        resp = await client.put(
            f"/api/v1/cards/{sample_card.card_number}",
            headers=user_headers,
            json={
                "card_embossed_name": "JANE DOE",
                "active_status": "Y",
                "expiration_month": 6,
                "expiration_year": 2027,
                "optimistic_lock_version": lock_version,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["card_embossed_name"] == "JANE DOE"
        assert data["expiration_month"] == 6
        assert data["expiration_year"] == 2027

    @pytest.mark.asyncio
    async def test_update_card_optimistic_lock_conflict(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_card: CreditCard,
    ):
        # Use an old/wrong lock version
        resp = await client.put(
            f"/api/v1/cards/{sample_card.card_number}",
            headers=user_headers,
            json={
                "card_embossed_name": "JOHN DOE",
                "active_status": "Y",
                "expiration_month": 12,
                "expiration_year": 2026,
                "optimistic_lock_version": "2020-01-01T00:00:00",  # stale version
            },
        )
        assert resp.status_code == 409
        data = resp.json()
        assert data["detail"]["error_code"] == "OPTIMISTIC_LOCK_ERROR"

    @pytest.mark.asyncio
    async def test_update_card_rejects_invalid_name(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_card: CreditCard,
    ):
        resp = await client.put(
            f"/api/v1/cards/{sample_card.card_number}",
            headers=user_headers,
            json={
                "card_embossed_name": "JOHN123",  # digits not allowed
                "active_status": "Y",
                "expiration_month": 12,
                "expiration_year": 2026,
                "optimistic_lock_version": "2026-01-01T12:00:00",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_update_card_account_id_unchanged(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_card: CreditCard,
    ):
        """Verify account_id is PROT — cannot be changed via update."""
        get_resp = await client.get(
            f"/api/v1/cards/{sample_card.card_number}",
            headers=user_headers,
        )
        original_account_id = get_resp.json()["account_id"]
        lock_version = get_resp.json()["updated_at"]

        # account_id not included in request body (PROT) — backend ignores it even if sent
        resp = await client.put(
            f"/api/v1/cards/{sample_card.card_number}",
            headers=user_headers,
            json={
                "card_embossed_name": "JOHN DOE",
                "active_status": "N",
                "expiration_month": 12,
                "expiration_year": 2026,
                "optimistic_lock_version": lock_version,
            },
        )
        assert resp.status_code == 200
        # account_id must be unchanged
        assert resp.json()["account_id"] == original_account_id
