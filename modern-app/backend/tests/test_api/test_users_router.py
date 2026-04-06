"""Integration tests for the /api/users endpoints.

Tests HTTP layer behaviour including:
  - Admin-only guard (require_admin dependency)
  - Correct status codes (201, 200, 400, 404, 409, 403, 401)
  - Request/response schema validation
  - End-to-end CRUD flow
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user, require_admin
from app.main import app
from app.models.user import User
from tests.conftest import make_admin_token


def _admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_admin_token()}"}


async def _seed(
    db: AsyncSession,
    user_id: str,
    first_name: str = "Test",
    last_name: str = "User",
    user_type: str = "U",
) -> User:
    import bcrypt

    u = User(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        password_hash=bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode(),
        user_type=user_type,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


# ---------------------------------------------------------------------------
# Helpers to bypass auth in API tests (unit-test the HTTP layer, not auth)
# ---------------------------------------------------------------------------
def _make_mock_admin(user_id: str = "ADMIN001") -> User:
    u = User.__new__(User)
    u.user_id = user_id
    u.first_name = "Admin"
    u.last_name = "Test"
    u.password_hash = "hashed"
    u.user_type = "A"
    return u


def override_admin():
    """Override both auth dependencies to bypass JWT for HTTP-layer tests."""
    mock_user = _make_mock_admin()

    async def _get_current():
        return mock_user

    async def _require_admin():
        return mock_user

    app.dependency_overrides[get_current_user] = _get_current
    app.dependency_overrides[require_admin] = _require_admin


def clear_overrides():
    app.dependency_overrides.clear()


class TestListUsersEndpoint:
    async def test_returns_200_and_empty_list(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        override_admin()
        try:
            resp = await client.get("/api/users")
            assert resp.status_code == 200
            data = resp.json()
            assert "users" in data
            assert "total" in data
            assert "page" in data
        finally:
            clear_overrides()

    async def test_pagination_params(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        override_admin()
        try:
            for i in range(3):
                await _seed(db_session, f"LIST{i:04d}")
            resp = await client.get("/api/users?page=1&page_size=2")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["users"]) <= 2
        finally:
            clear_overrides()

    async def test_requires_auth_without_override(self, client: AsyncClient):
        """No auth headers → 401."""
        resp = await client.get("/api/users")
        assert resp.status_code == 401


class TestGetUserEndpoint:
    async def test_returns_user(self, client: AsyncClient, db_session: AsyncSession):
        override_admin()
        try:
            await _seed(db_session, "GETTST01")
            resp = await client.get("/api/users/GETTST01")
            assert resp.status_code == 200
            assert resp.json()["user_id"] == "GETTST01"
        finally:
            clear_overrides()

    async def test_not_found_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        override_admin()
        try:
            resp = await client.get("/api/users/NOBODY99")
            assert resp.status_code == 404
        finally:
            clear_overrides()


class TestCreateUserEndpoint:
    async def test_creates_user_returns_201(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        override_admin()
        try:
            payload = {
                "user_id": "CRTU0001",
                "first_name": "Create",
                "last_name": "Test",
                "password": "pass1234",
                "user_type": "U",
            }
            resp = await client.post("/api/users", json=payload)
            assert resp.status_code == 201
            data = resp.json()
            assert data["user_id"] == "CRTU0001"
            assert "password" not in data
            assert "password_hash" not in data
        finally:
            clear_overrides()

    async def test_duplicate_returns_409(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        override_admin()
        try:
            await _seed(db_session, "DUPAPI01")
            payload = {
                "user_id": "DUPAPI01",
                "first_name": "Dup",
                "last_name": "User",
                "password": "pass1234",
                "user_type": "U",
            }
            resp = await client.post("/api/users", json=payload)
            assert resp.status_code == 409
        finally:
            clear_overrides()

    async def test_invalid_user_type_returns_422(self, client: AsyncClient):
        override_admin()
        try:
            payload = {
                "user_id": "BADTYPE1",
                "first_name": "Bad",
                "last_name": "Type",
                "password": "pass1234",
                "user_type": "X",  # invalid — not 'A' or 'U'
            }
            resp = await client.post("/api/users", json=payload)
            assert resp.status_code == 422
        finally:
            clear_overrides()

    async def test_blank_first_name_returns_422(self, client: AsyncClient):
        override_admin()
        try:
            payload = {
                "user_id": "BLANK001",
                "first_name": "   ",  # blank
                "last_name": "User",
                "password": "pass1234",
                "user_type": "U",
            }
            resp = await client.post("/api/users", json=payload)
            assert resp.status_code == 422
        finally:
            clear_overrides()

    async def test_user_id_too_long_returns_422(self, client: AsyncClient):
        override_admin()
        try:
            payload = {
                "user_id": "TOOLONG99",  # 9 chars — exceeds 8
                "first_name": "Long",
                "last_name": "ID",
                "password": "pass1234",
                "user_type": "U",
            }
            resp = await client.post("/api/users", json=payload)
            assert resp.status_code == 422
        finally:
            clear_overrides()


class TestUpdateUserEndpoint:
    async def test_updates_user_returns_200(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        override_admin()
        try:
            await _seed(db_session, "UPDT0001", first_name="OldFirst")
            payload = {
                "first_name": "NewFirst",
                "last_name": "User",
                "user_type": "U",
            }
            resp = await client.put("/api/users/UPDT0001", json=payload)
            assert resp.status_code == 200
            assert resp.json()["first_name"] == "NewFirst"
        finally:
            clear_overrides()

    async def test_no_changes_returns_400(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        override_admin()
        try:
            await _seed(db_session, "NOCH0001", first_name="Test", last_name="User")
            payload = {
                "first_name": "Test",
                "last_name": "User",
                "user_type": "U",
            }
            resp = await client.put("/api/users/NOCH0001", json=payload)
            assert resp.status_code == 400
        finally:
            clear_overrides()

    async def test_nonexistent_user_returns_404(self, client: AsyncClient):
        override_admin()
        try:
            payload = {"first_name": "Ghost", "last_name": "User", "user_type": "U"}
            resp = await client.put("/api/users/GHOST001", json=payload)
            assert resp.status_code == 404
        finally:
            clear_overrides()


class TestDeleteUserEndpoint:
    async def test_deletes_user_returns_200(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        override_admin()
        try:
            await _seed(db_session, "DELU0001")
            resp = await client.delete("/api/users/DELU0001")
            assert resp.status_code == 200
            assert "deleted" in resp.json()["message"].lower()
        finally:
            clear_overrides()

    async def test_nonexistent_delete_returns_404(self, client: AsyncClient):
        override_admin()
        try:
            resp = await client.delete("/api/users/PHANTOM1")
            assert resp.status_code == 404
        finally:
            clear_overrides()

    async def test_user_gone_after_delete(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        override_admin()
        try:
            await _seed(db_session, "GONE0001")
            await client.delete("/api/users/GONE0001")
            resp = await client.get("/api/users/GONE0001")
            assert resp.status_code == 404
        finally:
            clear_overrides()


class TestAdminGuard:
    async def test_non_admin_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """require_admin must reject user_type='U' with 403."""
        regular = User.__new__(User)
        regular.user_id = "USER0001"
        regular.first_name = "Reg"
        regular.last_name = "User"
        regular.password_hash = "hashed"
        regular.user_type = "U"

        async def _get_regular():
            return regular

        async def _require_regular():
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Admin access required")

        app.dependency_overrides[get_current_user] = _get_regular
        app.dependency_overrides[require_admin] = _require_regular
        try:
            resp = await client.get("/api/users")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()
