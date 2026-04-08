"""
Integration tests for POST /api/v1/auth/login (COSGN00C / CC00 transaction).
"""
import pytest


class TestAuthEndpoint:

    @pytest.mark.asyncio
    async def test_login_success(self, client, admin_user) -> None:
        """Valid credentials return JWT token with correct claims."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN", "password": "Admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_type"] == "A"
        assert data["user_id"] == "ADMIN"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client, admin_user) -> None:
        """COSGN00C: wrong password → 401 Unauthorized."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "ADMIN", "password": "WRONGPWD"},
        )
        assert response.status_code == 401
        assert "Wrong Password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_user_not_found_returns_401(self, client, admin_user) -> None:
        """COSGN00C: RESP=13 NOTFND → 401 (not 404, per COSGN00C behavior)."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "NOBODY", "password": "Admin123"},
        )
        assert response.status_code == 401
        assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_lowercase_user_id(self, client, admin_user) -> None:
        """COSGN00C: FUNCTION UPPER-CASE applied before lookup."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "admin", "password": "Admin123"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_login_empty_user_id_returns_422(self, client, admin_user) -> None:
        """COSGN00C: WHEN USERIDI = SPACES → validation error."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "", "password": "Admin123"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_token(self, client) -> None:
        """Endpoints require JWT Bearer token."""
        response = await client.get("/api/v1/accounts/1")
        assert response.status_code == 401
