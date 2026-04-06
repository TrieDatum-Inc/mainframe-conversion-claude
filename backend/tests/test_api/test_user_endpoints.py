"""
Integration tests for GET/POST/PUT/DELETE /api/v1/users endpoints.

These tests use the FastAPI TestClient against the full application stack
with a SQLite in-memory database (overriding the real PostgreSQL connection).

COBOL program mapping:
  GET    /users              → COUSR00C (CU00)
  GET    /users/{user_id}    → COUSR02C (CU02) read path
  POST   /users              → COUSR01C (CU01)
  PUT    /users/{user_id}    → COUSR02C (CU02) update path
  DELETE /users/{user_id}    → COUSR03C (CU03)
"""

import pytest
from httpx import AsyncClient

from app.models.user import User


# =============================================================================
# GET /api/v1/users — list users
# =============================================================================


class TestListUsersEndpoint:
    async def test_returns_200_with_empty_list(self, client: AsyncClient):
        """COUSR00C: empty USRSEC → empty list response, status 200."""
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total_count"] == 0

    async def test_returns_paginated_users(
        self, client: AsyncClient, multiple_users: list[User]
    ):
        """COUSR00C: 12 users; first page returns 10."""
        resp = await client.get("/api/v1/users?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 10
        assert data["total_count"] == 12
        assert data["has_next"] is True
        assert data["has_previous"] is False

    async def test_second_page_returns_remaining(
        self, client: AsyncClient, multiple_users: list[User]
    ):
        """COUSR00C PF8: second page shows remaining 2 users."""
        resp = await client.get("/api/v1/users?page=2&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["has_next"] is False
        assert data["has_previous"] is True

    async def test_user_id_filter_applied(
        self, client: AsyncClient, multiple_users: list[User]
    ):
        """COUSR00C: USRIDINI filter → results start at or after filter value."""
        resp = await client.get("/api/v1/users?user_id_filter=USER0010")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["user_id"] >= "USER0010"

    async def test_returns_403_for_regular_user(
        self, regular_client: AsyncClient
    ):
        """
        Admin-only access check: regular user (user_type='U') must get 403.
        COBOL origin: COUSR00C only reachable from COADM01C (admin menu).
        """
        resp = await regular_client.get("/api/v1/users")
        assert resp.status_code == 403

    async def test_returns_401_without_token(self, client: AsyncClient):
        """COUSR00C: EIBCALEN=0 → return to login. Maps to 401."""
        from httpx import AsyncClient as RawClient, ASGITransport
        from app.main import app

        async with RawClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as unauthenticated:
            resp = await unauthenticated.get("/api/v1/users")
        assert resp.status_code == 401

    async def test_response_never_contains_password(
        self, client: AsyncClient, sample_admin_user: User
    ):
        """Security: password_hash must never appear in list response."""
        resp = await client.get("/api/v1/users")
        data = resp.json()
        for item in data["items"]:
            assert "password" not in item
            assert "password_hash" not in item


# =============================================================================
# GET /api/v1/users/{user_id} — get single user
# =============================================================================


class TestGetUserEndpoint:
    async def test_returns_user_when_found(
        self, client: AsyncClient, sample_admin_user: User
    ):
        """COUSR02C: READ RESP=NORMAL → 200 with user data."""
        resp = await client.get("/api/v1/users/ADMIN001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "ADMIN001"
        assert data["first_name"] == "System"

    async def test_returns_404_when_not_found(self, client: AsyncClient):
        """COUSR02C: READ RESP=NOTFND → 'User ID NOT found...' → 404."""
        resp = await client.get("/api/v1/users/NOBODY99")
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"]["error_code"] == "USER_NOT_FOUND"

    async def test_returns_403_for_regular_user(
        self, regular_client: AsyncClient, sample_admin_user: User
    ):
        """Admin-only: regular user cannot read user details."""
        resp = await regular_client.get("/api/v1/users/ADMIN001")
        assert resp.status_code == 403

    async def test_response_has_no_password_field(
        self, client: AsyncClient, sample_admin_user: User
    ):
        """Security: single-user response excludes password."""
        resp = await client.get("/api/v1/users/ADMIN001")
        data = resp.json()
        assert "password" not in data
        assert "password_hash" not in data


# =============================================================================
# POST /api/v1/users — create user
# =============================================================================


class TestCreateUserEndpoint:
    def _create_payload(self, **overrides) -> dict:
        defaults = {
            "user_id": "NEWUSR01",
            "first_name": "New",
            "last_name": "User",
            "password": "Secure123!",
            "user_type": "U",
        }
        defaults.update(overrides)
        return defaults

    async def test_creates_user_returns_201(self, client: AsyncClient):
        """COUSR01C WRITE-USER-SEC-FILE RESP=NORMAL → 201 Created."""
        resp = await client.post("/api/v1/users", json=self._create_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == "NEWUSR01"

    async def test_returns_409_on_duplicate_user_id(
        self, client: AsyncClient, sample_admin_user: User
    ):
        """
        COUSR01C: RESP=DUPKEY/DUPREC → 'User ID already exist...' → 409.
        """
        resp = await client.post(
            "/api/v1/users",
            json=self._create_payload(user_id="ADMIN001"),
        )
        assert resp.status_code == 409
        data = resp.json()
        assert data["detail"]["error_code"] == "USER_ALREADY_EXISTS"

    async def test_returns_422_for_blank_first_name(self, client: AsyncClient):
        """COUSR01C: FNAMEI blank → 'First Name can NOT be empty...' → 422."""
        resp = await client.post(
            "/api/v1/users",
            json=self._create_payload(first_name="  "),
        )
        assert resp.status_code == 422

    async def test_returns_422_for_blank_last_name(self, client: AsyncClient):
        """COUSR01C: LNAMEI blank → 'Last Name can NOT be empty...' → 422."""
        resp = await client.post(
            "/api/v1/users",
            json=self._create_payload(last_name=""),
        )
        assert resp.status_code == 422

    async def test_returns_422_for_invalid_user_type(self, client: AsyncClient):
        """COUSR01C: USRTYPEI not 'A' or 'U' → 422."""
        resp = await client.post(
            "/api/v1/users",
            json=self._create_payload(user_type="X"),
        )
        assert resp.status_code == 422

    async def test_returns_422_for_user_id_too_long(self, client: AsyncClient):
        """COUSR01C: user_id max 8 chars (VSAM key field X(08))."""
        resp = await client.post(
            "/api/v1/users",
            json=self._create_payload(user_id="TOOLONGID9"),
        )
        assert resp.status_code == 422

    async def test_returns_403_for_regular_user(self, regular_client: AsyncClient):
        """Admin-only: regular user cannot create users."""
        resp = await regular_client.post(
            "/api/v1/users", json=self._create_payload()
        )
        assert resp.status_code == 403

    async def test_response_has_no_password(self, client: AsyncClient):
        """Security: create response must not include password."""
        resp = await client.post("/api/v1/users", json=self._create_payload())
        data = resp.json()
        assert "password" not in data
        assert "password_hash" not in data


# =============================================================================
# PUT /api/v1/users/{user_id} — update user
# =============================================================================


class TestUpdateUserEndpoint:
    def _update_payload(self, **overrides) -> dict:
        defaults = {
            "first_name": "Updated",
            "last_name": "Name",
            "user_type": "U",
        }
        defaults.update(overrides)
        return defaults

    async def test_updates_user_returns_200(
        self, client: AsyncClient, sample_regular_user: User
    ):
        """COUSR02C: modified field → REWRITE → 200."""
        resp = await client.put(
            "/api/v1/users/USER0001",
            json=self._update_payload(first_name="Changed"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "Changed"

    async def test_returns_404_for_missing_user(self, client: AsyncClient):
        """COUSR02C: READ NOTFND before UPDATE → 'User ID NOT found...' → 404."""
        resp = await client.put(
            "/api/v1/users/NOBODY99",
            json=self._update_payload(),
        )
        assert resp.status_code == 404

    async def test_returns_422_when_no_changes(
        self, client: AsyncClient, sample_regular_user: User
    ):
        """
        COUSR02C: USR-MODIFIED-NO → 'Please modify to update...' → 422.
        """
        resp = await client.put(
            "/api/v1/users/USER0001",
            json={
                "first_name": "John",
                "last_name": "Smith",
                "user_type": "U",
            },
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["detail"]["error_code"] == "NO_CHANGES_DETECTED"

    async def test_optional_password_update(
        self, client: AsyncClient, sample_regular_user: User
    ):
        """COUSR02C: non-blank password provided → new hash stored."""
        resp = await client.put(
            "/api/v1/users/USER0001",
            json=self._update_payload(password="NewPassword99!"),
        )
        assert resp.status_code == 200

    async def test_returns_403_for_regular_user(
        self, regular_client: AsyncClient, sample_regular_user: User
    ):
        """Admin-only: regular user cannot update users."""
        resp = await regular_client.put(
            "/api/v1/users/USER0001",
            json=self._update_payload(),
        )
        assert resp.status_code == 403


# =============================================================================
# DELETE /api/v1/users/{user_id} — delete user
# =============================================================================


class TestDeleteUserEndpoint:
    async def test_deletes_user_returns_200(
        self, client: AsyncClient, sample_regular_user: User
    ):
        """COUSR03C: DELETE RESP=NORMAL → 200 with success message."""
        resp = await client.delete("/api/v1/users/USER0001")
        assert resp.status_code == 200
        data = resp.json()
        assert "deleted" in data["message"].lower() or "USER0001" in data["message"]

    async def test_returns_404_for_missing_user(self, client: AsyncClient):
        """COUSR03C: READ NOTFND before DELETE → 'User ID NOT found...' → 404."""
        resp = await client.delete("/api/v1/users/NOBODY99")
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"]["error_code"] == "USER_NOT_FOUND"

    async def test_user_no_longer_exists_after_delete(
        self, client: AsyncClient, sample_regular_user: User
    ):
        """COUSR03C: record removed; subsequent GET returns 404."""
        await client.delete("/api/v1/users/USER0001")
        resp = await client.get("/api/v1/users/USER0001")
        assert resp.status_code == 404

    async def test_returns_403_for_regular_user(
        self, regular_client: AsyncClient, sample_regular_user: User
    ):
        """Admin-only: regular user cannot delete users."""
        resp = await regular_client.delete("/api/v1/users/USER0001")
        assert resp.status_code == 403

    async def test_delete_error_message_references_delete_not_update(
        self, client: AsyncClient
    ):
        """
        COUSR03C bug fix verification:
        Original DELETE-USER-SEC-FILE OTHER branch said 'Unable to Update User...'
        The 404 error response for this modern system must not say 'Update'.
        """
        resp = await client.delete("/api/v1/users/NOBODY99")
        data = resp.json()
        # Error message should reference the user not being found, not "update"
        detail_msg = data["detail"]["message"].lower()
        assert "update" not in detail_msg
