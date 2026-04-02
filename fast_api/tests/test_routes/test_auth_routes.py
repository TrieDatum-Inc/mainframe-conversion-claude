"""
Integration tests for auth_routes.py — POST /auth/login.

Maps COSGN00C sign-on screen integration:
  - Correct HTTP method (POST)
  - Request body structure (user_id + password)
  - Response structure (access_token + user_type)
  - HTTP status codes (200 / 401)
  - Error response format
"""

import pytest


class TestLoginEndpoint:
    @pytest.mark.asyncio
    async def test_admin_login_returns_200(self, async_client):
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "SYSADM00", "password": "Admin123"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_login_returns_bearer_token(self, async_client):
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "SYSADM00", "password": "Admin123"},
        )
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_returns_user_type(self, async_client):
        """BR-SGN-004: user_type in response ('A' or 'U')."""
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "SYSADM00", "password": "Admin123"},
        )
        body = resp.json()
        assert body["user_type"] == "A"

    @pytest.mark.asyncio
    async def test_regular_user_login(self, async_client):
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "USER0001", "password": "Pass1234"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["user_type"] == "U"

    @pytest.mark.asyncio
    async def test_user_not_found_returns_401(self, async_client):
        """BR-SGN-006: RESP=NOTFND -> HTTP 401."""
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "NOBODY00", "password": "Pass1234"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(self, async_client):
        """BR-SGN-003: wrong password -> HTTP 401."""
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "USER0001", "password": "WrongPwd"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_error_response_has_error_code(self, async_client):
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "NOBODY00", "password": "AnyPass1"},
        )
        body = resp.json()
        assert "error_code" in body or "detail" in body

    @pytest.mark.asyncio
    async def test_user_id_case_insensitive(self, async_client):
        """BR-SGN-002: lowercase user_id is uppercased before lookup."""
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "sysadm00", "password": "Admin123"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_password_returns_422(self, async_client):
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "SYSADM00"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_user_id_returns_422(self, async_client):
        resp = await async_client.post(
            "/auth/login",
            json={"password": "Admin123"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_user_id_exceeding_8_chars_returns_422(self, async_client):
        """SEC-USR-ID PIC X(8) — max 8 chars."""
        resp = await async_client.post(
            "/auth/login",
            json={"user_id": "TOOLONGID", "password": "Admin123"},
        )
        assert resp.status_code == 422
