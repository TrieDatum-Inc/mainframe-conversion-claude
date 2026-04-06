"""
Integration tests for authentication API endpoints.

Tests POST /api/v1/auth/login and POST /api/v1/auth/logout using
the HTTPX async test client with SQLite in-memory database.

These tests verify the full request-response cycle including:
- Request body parsing (Pydantic validation)
- Service layer delegation
- Response schema serialization
- HTTP status codes
- Error response format
"""

import pytest


class TestLoginEndpoint:
    """
    Tests for POST /api/v1/auth/login.
    Maps COSGN00C PROCESS-ENTER-KEY paragraph integration tests.
    """

    @pytest.mark.asyncio
    async def test_admin_login_returns_200_with_admin_redirect(self, client, admin_user):
        """
        Successful admin login: 200 OK, access_token present, redirect_to=/admin/menu.
        COBOL: SEC-USR-TYPE='A' → XCTL COADM01C → /admin/menu
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": "Admin1234"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == "ADMIN001"
        assert data["user_type"] == "A"
        assert data["redirect_to"] == "/admin/menu"
        assert data["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_regular_user_login_returns_200_with_menu_redirect(self, client, regular_user):
        """
        Successful regular user login: 200 OK, redirect_to=/menu.
        COBOL: SEC-USR-TYPE!='A' → XCTL COMEN01C → /menu
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "USER0001", "password": "User1234"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["redirect_to"] == "/menu"
        assert data["user_type"] == "U"

    @pytest.mark.asyncio
    async def test_login_unknown_user_returns_401(self, client):
        """
        User not found → 401 INVALID_CREDENTIALS.
        COBOL: IF RESP = DFHRESP(NOTFND) → 'Invalid User ID or Password'
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "NOBODY00", "password": "anypassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client, admin_user):
        """
        Wrong password → 401 INVALID_CREDENTIALS.
        COBOL: IF SEC-USR-PWD != WS-USER-PWD → 'Invalid User ID or Password'
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_empty_user_id_returns_422(self, client):
        """
        Empty user_id → 422 Unprocessable Entity.
        Maps Pydantic min_length=1 validation on user_id field.
        COBOL: IF WS-USER-ID = SPACES → error
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "", "password": "somepassword"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_empty_password_returns_422(self, client):
        """
        Empty password → 422 Unprocessable Entity.
        Maps Pydantic min_length=1 validation on password field.
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": ""},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_user_id_too_long_returns_422(self, client):
        """
        user_id > 8 chars → 422.
        Maps SEC-USR-ID PIC X(08) — max 8 characters.
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "TOOLONGID", "password": "somepassword"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_user_id_returns_422(self, client):
        """Missing required field → 422 validation error."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"password": "somepassword"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_password_returns_422(self, client):
        """Missing required password field → 422 validation error."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_response_never_contains_password_hash(self, client, admin_user):
        """
        SECURITY: password_hash must NEVER appear in any API response.
        This is a critical security control replacing plain-text USRSEC exposure.
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN001", "password": "Admin1234"},
        )

        assert response.status_code == 200
        response_text = response.text

        # Ensure bcrypt hash prefix never leaks
        assert "$2b$" not in response_text
        assert "password_hash" not in response_text
        assert "password" not in response_text


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout."""

    @pytest.mark.asyncio
    async def test_logout_with_valid_token_returns_200(
        self, client, admin_user, admin_auth_headers
    ):
        """
        Authenticated logout → 200 OK with thank-you message.
        COBOL: COSGN00C RETURN-TO-PREV-SCREEN → CCDA-MSG-THANK-YOU
        """
        response = await client.post("/api/v1/auth/logout", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "CardDemo" in data["message"] or admin_user.first_name in data["message"]

    @pytest.mark.asyncio
    async def test_logout_without_token_returns_401(self, client):
        """No JWT → 401 Unauthorized (no COMMAREA equivalent)."""
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token_returns_401(self, client):
        """Invalid JWT → 401 Unauthorized."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401


class TestMeEndpoint:
    """Tests for GET /api/v1/auth/me."""

    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, client, admin_user, admin_auth_headers):
        """Authenticated /me → returns user profile without password_hash."""
        response = await client.get("/api/v1/auth/me", headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "ADMIN001"
        assert data["user_type"] == "A"
        assert "password_hash" not in data
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_me_without_token_returns_401(self, client):
        """No JWT → 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
