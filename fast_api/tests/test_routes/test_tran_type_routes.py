"""
Integration tests for tran_type_routes.py — COTRTLIC, COTRTUPC.

Endpoints tested:
  GET /transaction-types                   <- COTRTLIC (list, 7/page)
  POST /transaction-types                  <- COTRTUPC (add, admin only)
  GET /transaction-types/{tran_type_cd}    <- COTRTUPC (view)
  PUT /transaction-types/{tran_type_cd}    <- COTRTUPC (update, admin only)
  DELETE /transaction-types/{tran_type_cd} <- COTRTUPC (delete, admin only)
"""

import pytest


class TestListTransactionTypesEndpoint:
    """GET /transaction-types — COTRTLIC."""

    @pytest.mark.asyncio
    async def test_returns_type_list(self, async_client, user_headers):
        resp = await async_client.get("/transaction-types", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    @pytest.mark.asyncio
    async def test_default_page_size_is_seven(self, async_client, user_headers):
        """COTRTLIC: 7 rows per page."""
        resp = await async_client.get("/transaction-types", headers=user_headers)
        body = resp.json()
        assert len(body["items"]) <= 7

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        resp = await async_client.get("/transaction-types")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_response_has_pagination_fields(self, async_client, user_headers):
        resp = await async_client.get("/transaction-types", headers=user_headers)
        body = resp.json()
        assert "has_next_page" in body


class TestCreateTransactionTypeEndpoint:
    """POST /transaction-types — COTRTUPC INSERT."""

    @pytest.mark.asyncio
    async def test_admin_can_create_type(self, async_client, admin_headers):
        body = {"tran_type_cd": "XT", "tran_type_desc": "Extra Test Type"}
        resp = await async_client.post(
            "/transaction-types", json=body, headers=admin_headers
        )
        assert resp.status_code == 201
        result = resp.json()
        assert result["tran_type_cd"] == "XT"

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create(self, async_client, user_headers):
        body = {"tran_type_cd": "RT", "tran_type_desc": "Restricted Type"}
        resp = await async_client.post(
            "/transaction-types", json=body, headers=user_headers
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_duplicate_type_code_returns_409(self, async_client, admin_headers):
        body = {"tran_type_cd": "DB", "tran_type_desc": "Duplicate"}
        resp = await async_client.post(
            "/transaction-types", json=body, headers=admin_headers
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_type_code_max_2_chars(self, async_client, admin_headers):
        body = {"tran_type_cd": "TOO", "tran_type_desc": "Too long code"}
        resp = await async_client.post(
            "/transaction-types", json=body, headers=admin_headers
        )
        assert resp.status_code == 422


class TestGetTransactionTypeEndpoint:
    @pytest.mark.asyncio
    async def test_returns_type_by_code(self, async_client, user_headers):
        resp = await async_client.get("/transaction-types/DB", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["tran_type_cd"] == "DB"

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, user_headers):
        resp = await async_client.get("/transaction-types/ZZ", headers=user_headers)
        assert resp.status_code == 404


class TestUpdateTransactionTypeEndpoint:
    """PUT /transaction-types/{code} — COTRTUPC UPDATE."""

    @pytest.mark.asyncio
    async def test_admin_can_update_type(self, async_client, admin_headers):
        body = {"tran_type_desc": "Updated Purchase Description"}
        resp = await async_client.put(
            "/transaction-types/DB", json=body, headers=admin_headers
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["tran_type_desc"] == "Updated Purchase Description"

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update(self, async_client, user_headers):
        body = {"tran_type_desc": "Unauthorized Update"}
        resp = await async_client.put(
            "/transaction-types/DB", json=body, headers=user_headers
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, admin_headers):
        body = {"tran_type_desc": "Ghost Type"}
        resp = await async_client.put(
            "/transaction-types/ZZ", json=body, headers=admin_headers
        )
        assert resp.status_code == 404


class TestDeleteTransactionTypeEndpoint:
    """DELETE /transaction-types/{code} — COTRTUPC DELETE."""

    @pytest.mark.asyncio
    async def test_admin_can_delete_type(self, async_client, admin_headers):
        # Create a disposable type first
        body = {"tran_type_cd": "DL", "tran_type_desc": "Delete Me"}
        await async_client.post(
            "/transaction-types", json=body, headers=admin_headers
        )

        resp = await async_client.delete(
            "/transaction-types/DL", headers=admin_headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete(self, async_client, user_headers):
        resp = await async_client.delete(
            "/transaction-types/PR", headers=user_headers
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, admin_headers):
        resp = await async_client.delete(
            "/transaction-types/ZZ", headers=admin_headers
        )
        assert resp.status_code == 404
