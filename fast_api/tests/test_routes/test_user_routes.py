"""
Integration tests for user_routes.py — COUSR00C-03C programs.

Endpoints tested:
  GET /users                    <- COUSR00C (list, 10/page, admin only)
  POST /users                   <- COUSR01C (create, admin only)
  GET /users/{usr_id}           <- COUSR02C (view, admin only)
  PUT /users/{usr_id}           <- COUSR02C (update, admin only)
  DELETE /users/{usr_id}        <- COUSR03C (delete, admin only)

Authorization:
  Admin ('A') has full access
  Regular user ('U') gets 403 Forbidden on all user management endpoints
"""

import pytest


class TestListUsersEndpoint:
    """GET /users — COUSR00C."""

    @pytest.mark.asyncio
    async def test_admin_can_list_users(self, async_client, admin_headers):
        resp = await async_client.get("/users", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    @pytest.mark.asyncio
    async def test_regular_user_cannot_list_users(self, async_client, user_headers):
        resp = await async_client.get("/users", headers=user_headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        resp = await async_client.get("/users")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_response_has_pagination_fields(self, async_client, admin_headers):
        resp = await async_client.get("/users", headers=admin_headers)
        body = resp.json()
        assert "has_next_page" in body

    @pytest.mark.asyncio
    async def test_page_size_default_is_ten(self, async_client, admin_headers):
        """COUSR00C: 10 rows per page."""
        resp = await async_client.get("/users", headers=admin_headers)
        body = resp.json()
        assert len(body["items"]) <= 10


class TestCreateUserEndpoint:
    """POST /users — COUSR01C."""

    @pytest.mark.asyncio
    async def test_admin_can_create_user(self, async_client, admin_headers):
        body = {
            "usr_id": "NEWUSR01",
            "first_name": "New",
            "last_name": "User",
            "password": "NewPass1",
            "usr_type": "U",
        }
        resp = await async_client.post("/users", json=body, headers=admin_headers)
        assert resp.status_code == 201
        result = resp.json()
        assert result["usr_id"] == "NEWUSR01"

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_users(self, async_client, user_headers):
        body = {
            "usr_id": "HACKATMP",
            "first_name": "Hacker",
            "last_name": "Attempt",
            "password": "Hack1234",
            "usr_type": "U",
        }
        resp = await async_client.post("/users", json=body, headers=user_headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_duplicate_user_id_returns_409(self, async_client, admin_headers):
        """COUSR01C: RESP=DUPREC -> HTTP 409."""
        body = {
            "usr_id": "SYSADM00",  # Already exists
            "first_name": "Dup",
            "last_name": "Admin",
            "password": "DupPass1",
            "usr_type": "A",
        }
        resp = await async_client.post("/users", json=body, headers=admin_headers)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_user_id_too_long_returns_422(self, async_client, admin_headers):
        """SEC-USR-ID PIC X(8) — max 8 chars."""
        body = {
            "usr_id": "TOOLONGID",
            "first_name": "Long",
            "last_name": "ID",
            "password": "Pass1234",
            "usr_type": "U",
        }
        resp = await async_client.post("/users", json=body, headers=admin_headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_user_type_returns_422(self, async_client, admin_headers):
        body = {
            "usr_id": "INVTYPE1",
            "first_name": "Inv",
            "last_name": "Type",
            "password": "Pass1234",
            "usr_type": "X",  # Must be 'A' or 'U'
        }
        resp = await async_client.post("/users", json=body, headers=admin_headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_password_not_returned_in_response(self, async_client, admin_headers):
        """Security: password hash must not be in API response."""
        body = {
            "usr_id": "NOPWDTST",
            "first_name": "NoPwd",
            "last_name": "Test",
            "password": "Secret12",
            "usr_type": "U",
        }
        resp = await async_client.post("/users", json=body, headers=admin_headers)
        assert resp.status_code == 201
        result = resp.json()
        assert "pwd_hash" not in result
        assert "password" not in result


class TestGetUserEndpoint:
    """GET /users/{usr_id} — COUSR02C."""

    @pytest.mark.asyncio
    async def test_admin_can_get_user(self, async_client, admin_headers):
        resp = await async_client.get("/users/SYSADM00", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["usr_id"] == "SYSADM00"

    @pytest.mark.asyncio
    async def test_regular_user_cannot_get_users(self, async_client, user_headers):
        resp = await async_client.get("/users/SYSADM00", headers=user_headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, admin_headers):
        resp = await async_client.get("/users/NOBODY00", headers=admin_headers)
        assert resp.status_code == 404


class TestUpdateUserEndpoint:
    """PUT /users/{usr_id} — COUSR02C update."""

    @pytest.mark.asyncio
    async def test_admin_can_update_user(self, async_client, admin_headers):
        body = {
            "first_name": "Updated",
            "last_name": "Jones",
            "usr_type": "U",
        }
        resp = await async_client.put(
            "/users/USER0002", json=body, headers=admin_headers
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["first_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_users(self, async_client, user_headers):
        body = {"first_name": "Hacked", "last_name": "Jones", "usr_type": "U"}
        resp = await async_client.put(
            "/users/USER0002", json=body, headers=user_headers
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, admin_headers):
        body = {"first_name": "Ghost", "last_name": "User", "usr_type": "U"}
        resp = await async_client.put(
            "/users/NOBODY00", json=body, headers=admin_headers
        )
        assert resp.status_code == 404


class TestDeleteUserEndpoint:
    """DELETE /users/{usr_id} — COUSR03C."""

    @pytest.mark.asyncio
    async def test_admin_can_delete_user(self, async_client, admin_headers):
        # Create a user to delete
        body = {
            "usr_id": "DELTEST1",
            "first_name": "Delete",
            "last_name": "Test",
            "password": "DelPass1",
            "usr_type": "U",
        }
        create_resp = await async_client.post("/users", json=body, headers=admin_headers)
        assert create_resp.status_code == 201

        # Delete it
        del_resp = await async_client.delete(
            "/users/DELTEST1", headers=admin_headers
        )
        assert del_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_users(self, async_client, user_headers):
        resp = await async_client.delete("/users/USER0002", headers=user_headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, admin_headers):
        resp = await async_client.delete("/users/NOBODY00", headers=admin_headers)
        assert resp.status_code == 404
