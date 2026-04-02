"""
Integration tests for card_routes.py — COCRDLIC, COCRDSLC, COCRDUPC.

Endpoints tested:
  GET /cards                   <- COCRDLIC (list, 7/page)
  GET /cards/{card_num}        <- COCRDSLC (view)
  PUT /cards/{card_num}        <- COCRDUPC (update)
  POST /cards                  <- (create with xref)
"""

import pytest


class TestListCardsEndpoint:
    """GET /cards — COCRDLIC."""

    @pytest.mark.asyncio
    async def test_returns_card_list(self, async_client, user_headers):
        resp = await async_client.get("/cards", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    @pytest.mark.asyncio
    async def test_default_page_size_is_seven(self, async_client, user_headers):
        """COCRDLIC: 7 rows per page."""
        resp = await async_client.get("/cards", headers=user_headers)
        body = resp.json()
        assert len(body["items"]) <= 7

    @pytest.mark.asyncio
    async def test_filter_by_acct_id(self, async_client, user_headers):
        resp = await async_client.get(
            "/cards",
            params={"acct_id": 10000000001},
            headers=user_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        for item in body["items"]:
            assert item["acct_id"] == 10000000001

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        resp = await async_client.get("/cards")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_response_has_pagination_fields(self, async_client, user_headers):
        resp = await async_client.get("/cards", headers=user_headers)
        body = resp.json()
        assert "has_next_page" in body
        assert "first_card_num" in body
        assert "last_card_num" in body


class TestGetCardDetailEndpoint:
    """GET /cards/{card_num} — COCRDSLC."""

    @pytest.mark.asyncio
    async def test_returns_card_detail(self, async_client, user_headers):
        resp = await async_client.get(
            "/cards/4111111111111001", headers=user_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["card_num"] == "4111111111111001"
        assert body["acct_id"] == 10000000001

    @pytest.mark.asyncio
    async def test_returns_cvv_cd(self, async_client, user_headers):
        resp = await async_client.get(
            "/cards/4111111111111001", headers=user_headers
        )
        body = resp.json()
        assert body["cvv_cd"] == 123

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, user_headers):
        resp = await async_client.get(
            "/cards/9999999999999999", headers=user_headers
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        resp = await async_client.get("/cards/4111111111111001")
        assert resp.status_code == 401


class TestUpdateCardEndpoint:
    """PUT /cards/{card_num} — COCRDUPC."""

    @pytest.mark.asyncio
    async def test_update_card_active_status(self, async_client, user_headers):
        body = {
            "active_status": "N",
            "embossed_name": "JOHN A DOE",
        }
        resp = await async_client.put(
            "/cards/4111111111111001", json=body, headers=user_headers
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["active_status"] == "N"

    @pytest.mark.asyncio
    async def test_update_embossed_name(self, async_client, user_headers):
        body = {
            "active_status": "Y",
            "embossed_name": "JONATHAN A DOE",
        }
        resp = await async_client.put(
            "/cards/4111111111111001", json=body, headers=user_headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, user_headers):
        body = {"active_status": "Y", "embossed_name": "GHOST"}
        resp = await async_client.put(
            "/cards/9999999999999999", json=body, headers=user_headers
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        body = {"active_status": "Y", "embossed_name": "TEST"}
        resp = await async_client.put("/cards/4111111111111001", json=body)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_active_status_returns_422(self, async_client, user_headers):
        body = {"active_status": "X", "embossed_name": "TEST"}
        resp = await async_client.put(
            "/cards/4111111111111001", json=body, headers=user_headers
        )
        assert resp.status_code == 422
