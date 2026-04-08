"""
Integration tests for /api/v1/admin/users (COUSR00C-03C).
All endpoints require admin access (user_type='A').
"""
import pytest


class TestUsersEndpoint:

    @pytest.mark.asyncio
    async def test_list_users_requires_admin(self, client, user_token) -> None:
        """User management is admin-only (COADM01C admin menu access)."""
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_users_admin_success(self, client, admin_user, regular_user, auth_token) -> None:
        """COUSR00C: admin can browse users."""
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    @pytest.mark.asyncio
    async def test_create_user(self, client, auth_token) -> None:
        """COUSR01C: admin creates new user."""
        response = await client.post(
            "/api/v1/admin/users",
            json={"user_id": "NEWUSER", "password": "Pass1234", "user_type": "U",
                  "first_name": "New", "last_name": "User"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "NEWUSER"
        assert data["user_type"] == "U"
        assert "password" not in data  # Never return password

    @pytest.mark.asyncio
    async def test_create_duplicate_user_returns_409(self, client, admin_user, auth_token) -> None:
        """COUSR01C: EXEC CICS WRITE RESP=14 DUPREC → HTTP 409."""
        response = await client.post(
            "/api/v1/admin/users",
            json={"user_id": "ADMIN", "password": "Admin123", "user_type": "A"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_user(self, client, regular_user, auth_token) -> None:
        """COUSR02C: admin updates user fields."""
        response = await client.put(
            "/api/v1/admin/users/USER0001",
            json={"first_name": "Updated"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["first_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_delete_user(self, client, regular_user, auth_token) -> None:
        """COUSR03C: admin deletes user → HTTP 204."""
        response = await client.delete(
            "/api/v1/admin/users/USER0001",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_returns_404(self, client, auth_token) -> None:
        """COUSR03C: EXEC CICS READ RESP=13 NOTFND → HTTP 404."""
        response = await client.delete(
            "/api/v1/admin/users/NOBODY",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_success(self, client, admin_user, auth_token) -> None:
        """GET single user by ID."""
        response = await client.get(
            "/api/v1/admin/users/ADMIN",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "ADMIN"
        assert data["is_admin"] is True
