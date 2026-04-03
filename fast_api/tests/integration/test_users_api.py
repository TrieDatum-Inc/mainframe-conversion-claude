"""Integration tests for User Administration API endpoints.

Tests cover all HTTP behaviours for each endpoint:
    GET  /api/users          — COUSR00C (list, pagination, search)
    POST /api/users          — COUSR01C (add, duplicate, validation)
    GET  /api/users/{id}     — COUSR02C/03C (lookup, not-found)
    PUT  /api/users/{id}     — COUSR02C (update, no-change, not-found)
    DELETE /api/users/{id}   — COUSR03C (delete, not-found)

Also tests admin-only enforcement (403 for non-admin callers).
"""
import pytest

from tests.conftest import ADMIN_HEADERS


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# GET /api/users — COUSR00C
# ---------------------------------------------------------------------------


class TestListUsers:
    @pytest.mark.asyncio
    async def test_list_empty_database(self, client):
        """COUSR00C: empty USRSEC → empty page, no error."""
        response = await client.get("/api/users", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["users"] == []
        assert data["total_count"] == 0
        assert data["has_next_page"] is False
        assert data["has_prev_page"] is False

    @pytest.mark.asyncio
    async def test_list_with_seed_data(self, client, seed_users):
        """COUSR00C: all 5 seed users returned on first page."""
        response = await client.get("/api/users", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 5
        assert len(data["users"]) == 5

    @pytest.mark.asyncio
    async def test_default_page_size_is_10(self, client):
        """COUSR00C: default page_size=10 (COUSR00C shows 10 rows per screen)."""
        response = await client.get("/api/users", headers=ADMIN_HEADERS)
        data = response.json()
        assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_pagination_first_page(self, client, seed_users):
        """COUSR00C: page 1 returns correct users and metadata."""
        response = await client.get(
            "/api/users?page=1&page_size=3", headers=ADMIN_HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 3
        assert data["page"] == 1
        assert data["has_prev_page"] is False
        assert data["has_next_page"] is True

    @pytest.mark.asyncio
    async def test_pagination_last_page(self, client, seed_users):
        """COUSR00C: bottom-of-list guard — last page has no next page."""
        response = await client.get(
            "/api/users?page=2&page_size=3", headers=ADMIN_HEADERS
        )
        data = response.json()
        assert data["has_prev_page"] is True
        assert data["has_next_page"] is False

    @pytest.mark.asyncio
    async def test_users_ordered_by_user_id(self, client, seed_users):
        """COUSR00C: VSAM KSDS browse returns records in key (user_id) order."""
        response = await client.get("/api/users", headers=ADMIN_HEADERS)
        data = response.json()
        ids = [u["user_id"] for u in data["users"]]
        assert ids == sorted(ids)

    @pytest.mark.asyncio
    async def test_search_by_user_id(self, client, seed_users):
        """COUSR00C: non-blank search_user_id positions browse."""
        response = await client.get(
            "/api/users?search_user_id=user", headers=ADMIN_HEADERS
        )
        data = response.json()
        assert all(u["user_id"] >= "user" for u in data["users"])

    @pytest.mark.asyncio
    async def test_no_admin_returns_403(self, client, seed_users):
        """All COUSR0xC programs are admin-only (reached via COADM01C)."""
        response = await client.get("/api/users", headers={"X-User-Type": "U"})
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_no_auth_header_returns_403(self, client):
        """Missing X-User-Type header treated as non-admin."""
        response = await client.get("/api/users")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_password_not_in_list_response(self, client, seed_users):
        """Password must never appear in any response."""
        response = await client.get("/api/users", headers=ADMIN_HEADERS)
        for user in response.json()["users"]:
            assert "password" not in user


# ---------------------------------------------------------------------------
# POST /api/users — COUSR01C
# ---------------------------------------------------------------------------


class TestCreateUser:
    @pytest.mark.asyncio
    async def test_create_admin_user_success(self, client):
        """COUSR01C: valid admin user returns 201 with user data."""
        payload = {
            "first_name": "Alice",
            "last_name": "Admin",
            "user_id": "newadmin",
            "password": "SecretPwd",
            "user_type": "A",
        }
        response = await client.post("/api/users", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "newadmin"
        assert data["first_name"] == "Alice"
        assert data["user_type"] == "A"
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_create_regular_user_success(self, client):
        """COUSR01C: valid regular user created successfully."""
        payload = {
            "first_name": "Bob",
            "last_name": "User",
            "user_id": "newuser1",
            "password": "Password1",
            "user_type": "U",
        }
        response = await client.post("/api/users", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_duplicate_user_id_returns_409(self, client, seed_users):
        """COUSR01C WRITE-USER-SEC-FILE: DFHRESP(DUPKEY) → HTTP 409."""
        payload = {
            "first_name": "Dup",
            "last_name": "User",
            "user_id": "admin001",  # already exists
            "password": "password",
            "user_type": "U",
        }
        response = await client.post("/api/users", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 409
        assert "already exist" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_user_type_returns_422(self, client):
        """COBOL bug fix: user_type 'X' is not valid — must be 'A' or 'U'."""
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "user_id": "testuser",
            "password": "password",
            "user_type": "X",
        }
        response = await client.post("/api/users", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_first_name_returns_422(self, client):
        """COUSR01C validation step 1: First Name can NOT be empty."""
        payload = {
            "first_name": "",
            "last_name": "User",
            "user_id": "testuser",
            "password": "password",
            "user_type": "U",
        }
        response = await client.post("/api/users", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_last_name_returns_422(self, client):
        """COUSR01C validation step 2: Last Name can NOT be empty."""
        payload = {
            "first_name": "Test",
            "last_name": "",
            "user_id": "testuser",
            "password": "password",
            "user_type": "U",
        }
        response = await client.post("/api/users", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_user_id_returns_422(self, client):
        """COUSR01C validation step 3: User ID can NOT be empty."""
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "user_id": "",
            "password": "password",
            "user_type": "U",
        }
        response = await client.post("/api/users", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_user_id_exceeds_8_chars_returns_422(self, client):
        """COUSR01C: User ID is PIC X(08) — 9+ chars must be rejected."""
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "user_id": "toolongid",  # 9 chars
            "password": "password",
            "user_type": "U",
        }
        response = await client.post("/api/users", json=payload, headers=ADMIN_HEADERS)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_non_admin_returns_403(self, client):
        """Admin-only endpoint — regular user gets 403."""
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "user_id": "testuser",
            "password": "password",
            "user_type": "U",
        }
        response = await client.post(
            "/api/users", json=payload, headers={"X-User-Type": "U"}
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/users/{user_id} — COUSR02C/03C lookup
# ---------------------------------------------------------------------------


class TestGetUser:
    @pytest.mark.asyncio
    async def test_get_existing_user(self, client, seed_users):
        """COUSR02C/03C PROCESS-ENTER-KEY: fetch user for display."""
        response = await client.get("/api/users/admin001", headers=ADMIN_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "admin001"
        assert data["first_name"] == "Alice"
        assert "password" not in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_returns_404(self, client):
        """COUSR02C/03C: DFHRESP(NOTFND) → HTTP 404 with 'User ID NOT found'."""
        response = await client.get("/api/users/notexist", headers=ADMIN_HEADERS)
        assert response.status_code == 404
        assert "NOT found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_non_admin_returns_403(self, client, seed_users):
        response = await client.get(
            "/api/users/admin001", headers={"X-User-Type": "U"}
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT /api/users/{user_id} — COUSR02C
# ---------------------------------------------------------------------------


class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_update_first_name_success(self, client, seed_users):
        """COUSR02C: changed first_name triggers REWRITE, returns 200."""
        payload = {
            "first_name": "Updated",
            "last_name": "Administrator",
            "password": "NewPass01",
            "user_type": "A",
        }
        response = await client.put(
            "/api/users/admin001", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["first_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_user_type(self, client, seed_users):
        """COUSR02C: user_type change from U to A is persisted."""
        payload = {
            "first_name": "Carol",
            "last_name": "Smith",
            "password": "NewPass01",
            "user_type": "A",
        }
        response = await client.put(
            "/api/users/user0001", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["user_type"] == "A"

    @pytest.mark.asyncio
    async def test_no_changes_returns_422(self, client, seed_users):
        """COUSR02C: no-change guard → HTTP 422 'Please modify to update'."""
        # First fetch the user to get current values
        get_resp = await client.get("/api/users/user0002", headers=ADMIN_HEADERS)
        user = get_resp.json()

        # Submit the same values back (no actual change)
        payload = {
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "password": "User0002!",  # Same as seed data password
            "user_type": user["user_type"],
        }
        response = await client.put(
            "/api/users/user0002", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 422
        assert "modify" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_nonexistent_user_returns_404(self, client):
        """COUSR02C READ-USER-SEC-FILE: NOTFND → HTTP 404."""
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "password": "password",
            "user_type": "U",
        }
        response = await client.put(
            "/api/users/notexist", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_user_id_unchanged_after_update(self, client, seed_users):
        """COUSR02C: user_id is immutable VSAM key — must not change."""
        payload = {
            "first_name": "Updated",
            "last_name": "Smith",
            "password": "NewPass01",
            "user_type": "U",
        }
        response = await client.put(
            "/api/users/user0001", json=payload, headers=ADMIN_HEADERS
        )
        assert response.json()["user_id"] == "user0001"

    @pytest.mark.asyncio
    async def test_update_non_admin_returns_403(self, client, seed_users):
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "password": "password",
            "user_type": "U",
        }
        response = await client.put(
            "/api/users/user0001", json=payload, headers={"X-User-Type": "U"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_user_type_in_update_returns_422(self, client, seed_users):
        """COBOL bug fix: invalid user_type also rejected on update."""
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "password": "password",
            "user_type": "Z",
        }
        response = await client.put(
            "/api/users/user0001", json=payload, headers=ADMIN_HEADERS
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/users/{user_id} — COUSR03C
# ---------------------------------------------------------------------------


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_delete_existing_user_returns_204(self, client, seed_users):
        """COUSR03C PF5: user deleted, screen cleared (204 No Content)."""
        response = await client.delete("/api/users/user0003", headers=ADMIN_HEADERS)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_deleted_user_no_longer_accessible(self, client, seed_users):
        """COUSR03C: after DELETE, GET returns 404."""
        await client.delete("/api/users/user0003", headers=ADMIN_HEADERS)
        response = await client.get("/api/users/user0003", headers=ADMIN_HEADERS)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_returns_404(self, client):
        """COUSR03C DELETE-USER-SEC-FILE: DFHRESP(NOTFND) → HTTP 404."""
        response = await client.delete("/api/users/notexist", headers=ADMIN_HEADERS)
        assert response.status_code == 404
        # COBOL bug fixed: message says "Delete" not "Update"
        assert "NOT found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_non_admin_returns_403(self, client, seed_users):
        """COUSR03C is admin-only."""
        response = await client.delete(
            "/api/users/user0001", headers={"X-User-Type": "U"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_does_not_affect_other_users(self, client, seed_users):
        """COUSR03C: only the specified user is deleted."""
        await client.delete("/api/users/user0003", headers=ADMIN_HEADERS)
        # Other users still accessible
        response = await client.get("/api/users/user0001", headers=ADMIN_HEADERS)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_two_phase_confirmation_flow(self, client, seed_users):
        """COUSR03C two-phase: GET (confirm screen) then DELETE (PF5)."""
        # Phase 1: fetch user info for read-only confirmation screen (ENTER key)
        preview = await client.get("/api/users/user0002", headers=ADMIN_HEADERS)
        assert preview.status_code == 200
        assert preview.json()["user_id"] == "user0002"
        assert "password" not in preview.json()

        # Phase 2: confirm deletion (PF5)
        delete_resp = await client.delete("/api/users/user0002", headers=ADMIN_HEADERS)
        assert delete_resp.status_code == 204
