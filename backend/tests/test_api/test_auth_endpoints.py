"""
Integration tests for auth and user management endpoints.

Covers:
  POST /api/v1/auth/login   — COSGN00C
  POST /api/v1/auth/logout
  GET  /api/v1/auth/me
  GET  /api/v1/users
  GET  /api/v1/users/{user_id}
  POST /api/v1/users
  PUT  /api/v1/users/{user_id}
  DELETE /api/v1/users/{user_id}

Also covers:
  - dependencies.py error paths (invalid/missing token, non-admin access)
  - exceptions/handlers.py (all registered handlers)

Note: LoginRequest.password is max_length=8 (COBOL PASSWDI PIC X(8)).
Login fixtures use 8-char passwords (e.g. "Admin123") stored via hash_password.
The shared conftest admin_user/regular_user store 9-char hashes so we create
dedicated login-test users here with compliant passwords.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.security import hash_password


# Login-specific fixtures — test-only credentials, not real secrets
_LOGIN_ADMIN_PWD = "Admin123"  # noqa: S105 — 8 chars, COBOL PASSWDI constraint
_LOGIN_USER_PWD = "User1234"   # noqa: S105 — 8 chars
_WRONG_PWD = "WrongPas"        # noqa: S105 — intentionally wrong for 401 tests
_UNKNOWN_PWD = "Pass1234"      # noqa: S105 — used for unknown-user and create tests
_NEW_USER_PWD = "Pass1234"     # noqa: S105 — password for new-user creation tests
_DELETE_TMP_PWD = "pass"       # noqa: S105 — throwaway password for delete test


@pytest.fixture
async def login_admin(db_session: AsyncSession) -> User:
    """Admin user whose password fits the 8-char LoginRequest constraint."""
    user = User(
        user_id="LGNADM01",
        first_name="Login",
        last_name="Admin",
        password_hash=hash_password(_LOGIN_ADMIN_PWD),
        user_type="A",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def login_user(db_session: AsyncSession) -> User:
    """Regular user whose password fits the 8-char LoginRequest constraint."""
    user = User(
        user_id="LGNUSR01",
        first_name="Login",
        last_name="User",
        password_hash=hash_password(_LOGIN_USER_PWD),
        user_type="U",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


# =============================================================================
# Auth — POST /api/v1/auth/login
# =============================================================================

class TestLoginEndpoint:
    @pytest.mark.asyncio
    async def test_login_success(
        self, client: AsyncClient, login_admin: User
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"user_id": login_admin.user_id, "password": _LOGIN_ADMIN_PWD},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == login_admin.user_id

    @pytest.mark.asyncio
    async def test_login_invalid_password_returns_401(
        self, client: AsyncClient, login_admin: User
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"user_id": login_admin.user_id, "password": _WRONG_PWD},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["detail"]["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_unknown_user_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"user_id": "UNKNOWN1", "password": _UNKNOWN_PWD},
        )
        assert resp.status_code == 401
        data = resp.json()
        # Same error for both unknown user and wrong password — prevents enumeration
        assert data["detail"]["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_admin_gets_admin_redirect(
        self, client: AsyncClient, login_admin: User
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"user_id": login_admin.user_id, "password": _LOGIN_ADMIN_PWD},
        )
        assert resp.status_code == 200
        assert resp.json()["redirect_to"] == "/admin/menu"

    @pytest.mark.asyncio
    async def test_login_regular_user_gets_menu_redirect(
        self, client: AsyncClient, login_user: User
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"user_id": login_user.user_id, "password": _LOGIN_USER_PWD},
        )
        assert resp.status_code == 200
        assert resp.json()["redirect_to"] == "/menu"


# =============================================================================
# Auth — POST /api/v1/auth/logout
# =============================================================================

class TestLogoutEndpoint:
    @pytest.mark.asyncio
    async def test_logout_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_logout_success(
        self, client: AsyncClient, user_headers: dict, regular_user: User
    ):
        resp = await client.post("/api/v1/auth/logout", headers=user_headers)
        assert resp.status_code == 200
        assert "message" in resp.json()


# =============================================================================
# Auth — GET /api/v1/auth/me
# =============================================================================

class TestMeEndpoint:
    @pytest.mark.asyncio
    async def test_me_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_me_returns_user_id_and_type(
        self, client: AsyncClient, user_headers: dict, regular_user: User
    ):
        resp = await client.get("/api/v1/auth/me", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == regular_user.user_id
        assert data["user_type"] == regular_user.user_type


# =============================================================================
# dependencies.py error paths
# =============================================================================

class TestDependencyErrorPaths:
    @pytest.mark.asyncio
    async def test_missing_token_returns_403(self, client: AsyncClient):
        """No Authorization header at all → HTTPBearer returns 403."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.real.token"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["error_code"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_non_admin_cannot_access_admin_endpoint(
        self, client: AsyncClient, user_headers: dict
    ):
        """Regular user hitting admin-only endpoint → 403."""
        resp = await client.get("/api/v1/users", headers=user_headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_access_admin_endpoint(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.get("/api/v1/users", headers=admin_headers)
        assert resp.status_code == 200


# =============================================================================
# User Management — GET /api/v1/users (COUSR00C)
# =============================================================================

class TestListUsersEndpoint:
    @pytest.mark.asyncio
    async def test_list_users_requires_admin(
        self, client: AsyncClient, user_headers: dict
    ):
        resp = await client.get("/api/v1/users", headers=user_headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_users_returns_paginated_response(
        self, client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        resp = await client.get("/api/v1/users", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total_count" in data
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_users_with_filter(
        self, client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        resp = await client.get(
            f"/api/v1/users?user_id_filter={admin_user.user_id[:4]}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [u["user_id"] for u in data["items"]]
        assert admin_user.user_id in ids

    @pytest.mark.asyncio
    async def test_list_users_pagination(
        self, client: AsyncClient, admin_headers: dict, admin_user: User, regular_user: User
    ):
        resp = await client.get(
            "/api/v1/users?page=1&page_size=1",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 1


# =============================================================================
# User Management — GET /api/v1/users/{user_id} (COUSR02C read)
# =============================================================================

class TestGetUserEndpoint:
    @pytest.mark.asyncio
    async def test_get_user_success(
        self, client: AsyncClient, admin_headers: dict, regular_user: User
    ):
        resp = await client.get(
            f"/api/v1/users/{regular_user.user_id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == regular_user.user_id
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_get_user_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.get("/api/v1/users/NOBODY00", headers=admin_headers)
        assert resp.status_code == 404
        assert resp.json()["detail"]["error_code"] == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_user_requires_admin(
        self, client: AsyncClient, user_headers: dict, regular_user: User
    ):
        resp = await client.get(
            f"/api/v1/users/{regular_user.user_id}", headers=user_headers
        )
        assert resp.status_code == 403


# =============================================================================
# User Management — POST /api/v1/users (COUSR01C)
# =============================================================================

class TestCreateUserEndpoint:
    @pytest.mark.asyncio
    async def test_create_user_success(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "user_id": "NEWU0001",
                "first_name": "New",
                "last_name": "User",
                "password": _NEW_USER_PWD,
                "user_type": "U",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == "NEWU0001"
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_create_user_requires_admin(
        self, client: AsyncClient, user_headers: dict
    ):
        resp = await client.post(
            "/api/v1/users",
            headers=user_headers,
            json={
                "user_id": "NEWU0001",
                "first_name": "New",
                "last_name": "User",
                "password": _NEW_USER_PWD,
                "user_type": "U",
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_create_duplicate_user_returns_409(
        self, client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        """COUSR01C: DUPKEY → DuplicateResourceError → 409."""
        resp = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "user_id": admin_user.user_id,
                "first_name": "Dup",
                "last_name": "User",
                "password": _NEW_USER_PWD,
                "user_type": "U",
            },
        )
        assert resp.status_code == 409
        data = resp.json()
        assert data["detail"]["error_code"] == "USER_ALREADY_EXISTS"

    @pytest.mark.asyncio
    async def test_create_user_invalid_user_type_returns_422(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.post(
            "/api/v1/users",
            headers=admin_headers,
            json={
                "user_id": "NEWU0001",
                "first_name": "New",
                "last_name": "User",
                "password": _NEW_USER_PWD,
                "user_type": "X",  # invalid — only A or U
            },
        )
        assert resp.status_code == 422


# =============================================================================
# User Management — PUT /api/v1/users/{user_id} (COUSR02C update)
# =============================================================================

class TestUpdateUserEndpoint:
    @pytest.mark.asyncio
    async def test_update_user_success(
        self, client: AsyncClient, admin_headers: dict, regular_user: User
    ):
        resp = await client.put(
            f"/api/v1/users/{regular_user.user_id}",
            headers=admin_headers,
            json={
                "first_name": "Updated",
                "last_name": "Name",
                "user_type": "U",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_user_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.put(
            "/api/v1/users/NOBODY00",
            headers=admin_headers,
            json={"first_name": "X", "last_name": "Y", "user_type": "U"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_requires_admin(
        self, client: AsyncClient, user_headers: dict, regular_user: User
    ):
        resp = await client.put(
            f"/api/v1/users/{regular_user.user_id}",
            headers=user_headers,
            json={"first_name": "X", "last_name": "Y", "user_type": "U"},
        )
        assert resp.status_code == 403


# =============================================================================
# User Management — DELETE /api/v1/users/{user_id} (COUSR03C)
# =============================================================================

class TestDeleteUserEndpoint:
    @pytest.mark.asyncio
    async def test_delete_user_success(
        self, client: AsyncClient, admin_headers: dict, db_session
    ):
        from app.models.user import User
        from app.utils.security import hash_password

        # Create a throw-away user to delete
        user = User(
            user_id="DELTMP01",
            first_name="Del",
            last_name="Temp",
            password_hash=hash_password(_DELETE_TMP_PWD),
            user_type="U",
        )
        db_session.add(user)
        await db_session.flush()

        resp = await client.delete("/api/v1/users/DELTMP01", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "DELTMP01" in data["message"]

    @pytest.mark.asyncio
    async def test_delete_user_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.delete("/api/v1/users/NOBODY00", headers=admin_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_requires_admin(
        self, client: AsyncClient, user_headers: dict, regular_user: User
    ):
        resp = await client.delete(
            f"/api/v1/users/{regular_user.user_id}", headers=user_headers
        )
        assert resp.status_code == 403
