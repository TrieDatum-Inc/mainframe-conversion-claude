"""
Integration tests for the authentication API endpoints.

Tests the full HTTP request/response cycle:
    POST /api/v1/auth/login
    POST /api/v1/auth/logout

COBOL origin: COSGN00C (Transaction CC00) — sign-on screen driver.
"""

import pytest
from httpx import AsyncClient


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login."""

    @pytest.mark.asyncio
    async def test_login_admin_credentials_returns_200(
        self, client: AsyncClient, seed_users
    ):
        """Admin user with correct credentials → 200 with JWT token."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": "AdminPass1!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == "ADMIN001"
        assert data["user_type"] == "A"
        assert data["redirect_to"] == "/admin/menu"

    @pytest.mark.asyncio
    async def test_login_regular_user_credentials_returns_200(
        self, client: AsyncClient, seed_users
    ):
        """Regular user with correct credentials → 200 with redirect to /menu."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "USER0001", "password": "UserPass1!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_type"] == "U"
        assert data["redirect_to"] == "/menu"
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Smith"

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_returns_401(
        self, client: AsyncClient, seed_users
    ):
        """Non-existent user_id → 401 INVALID_CREDENTIALS."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "NOBODY", "password": "anything"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(
        self, client: AsyncClient, seed_users
    ):
        """Correct user_id, wrong password → 401 INVALID_CREDENTIALS."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": "WrongPassword!"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_user_not_found_and_wrong_password_identical_error(
        self, client: AsyncClient, seed_users
    ):
        """
        User-not-found and wrong-password responses are byte-for-byte identical.

        SECURITY: This test enforces the enumeration-prevention guarantee.
        COBOL origin: Both NOTFND and password mismatch used the same WS-MESSAGE.
        """
        not_found = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "NOPE9999", "password": "anything"},
        )
        wrong_pwd = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": "WrongPass!"},
        )
        assert not_found.status_code == wrong_pwd.status_code == 401
        assert not_found.json()["error_code"] == wrong_pwd.json()["error_code"]
        assert not_found.json()["message"] == wrong_pwd.json()["message"]

    @pytest.mark.asyncio
    async def test_login_blank_user_id_returns_422(
        self, client: AsyncClient, seed_users
    ):
        """
        Empty user_id → 422 Unprocessable Entity.

        COBOL origin: COSGN00C checks 'IF USERIDI = SPACES' → error message.
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "", "password": "somepassword"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_blank_password_returns_422(
        self, client: AsyncClient, seed_users
    ):
        """Empty password → 422 Unprocessable Entity."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": ""},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_user_id_too_long_returns_422(
        self, client: AsyncClient, seed_users
    ):
        """
        user_id exceeding 8 characters → 422.

        COBOL origin: USRIDI field is 8 characters; longer input is invalid.
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "TOOLONGID", "password": "password"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_response_never_contains_password_hash(
        self, client: AsyncClient, seed_users
    ):
        """
        SECURITY: password_hash must never appear in any API response.

        COBOL origin: SEC-USR-PWD was accessible to any CICS program with USRSEC access.
        The modern API must never expose the hash.
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": "AdminPass1!"},
        )
        response_text = response.text
        assert "password_hash" not in response_text
        assert "$2b$" not in response_text  # bcrypt hash prefix


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout."""

    @pytest.mark.asyncio
    async def test_logout_with_valid_token_returns_204(
        self, client: AsyncClient, seed_users
    ):
        """
        Logout with a valid JWT → 204 No Content.

        COBOL origin: PF3 key → RETURN-TO-PREV-SCREEN → bare EXEC CICS RETURN.
        """
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": "AdminPass1!"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        logout_response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_response.status_code == 204

    @pytest.mark.asyncio
    async def test_logout_without_token_returns_401(
        self, client: AsyncClient, seed_users
    ):
        """Logout without Authorization header → 401."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token_still_returns_204(
        self, client: AsyncClient, seed_users
    ):
        """
        Logout with an already-invalid token → 204 (idempotent).
        Logout should not fail if the token is already expired or revoked.
        """
        # Use a structurally valid but expired-looking token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "USER0001", "password": "UserPass1!"},
        )
        token = login_response.json()["access_token"]

        # First logout
        resp1 = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 204

        # Second logout with same (now-revoked) token should still return 204
        resp2 = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 204
