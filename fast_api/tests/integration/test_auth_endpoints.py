"""Integration tests for authentication endpoints — COSGN00C equivalent.

Uses httpx.AsyncClient with the FastAPI app directly.
DB calls are mocked via FastAPI dependency overrides.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import MagicMock, patch

from app.main import app
from app.models.user import User
from app.utils.security import hash_password, create_access_token
from app.schemas.auth import TokenPayload
from app.database import get_db
from app.repositories.user_repository import UserRepository


def _make_user(user_id: str, password_plain: str, user_type: str,
               first_name: str = "Test", last_name: str = "User") -> User:
    return User(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        password=hash_password(password_plain),
        user_type=user_type,
    )


def _override_db_with_user(user: User | None):
    """Return a FastAPI dependency override that yields a mock DB session.

    The mock session returns the given user when UserRepository.get_by_id is called.
    We patch at the repository layer to avoid SQLAlchemy async complexity.
    """
    async def mock_get_db():
        # This yields a fake session — the actual SQL is intercepted at repo level
        yield MagicMock()

    return mock_get_db


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ============================================================
# POST /auth/login
# ============================================================

class TestLoginEndpoint:
    """Integration tests for /auth/login (COSGN00C PROCESS-ENTER-KEY)."""

    async def test_valid_admin_login_returns_200(self, client):
        """Admin login should return 200 with JWT token and /admin-menu redirect."""
        admin = _make_user("ADMIN001", "ADMIN001", "A", "System", "Administrator")

        with patch.object(UserRepository, "get_by_id", return_value=admin):
            app.dependency_overrides[get_db] = _override_db_with_user(admin)
            response = await client.post(
                "/auth/login",
                json={"user_id": "ADMIN001", "password": "ADMIN001"},
            )
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["redirect_to"] == "/admin-menu"
        assert data["user"]["user_type"] == "A"

    async def test_valid_regular_user_login_returns_200(self, client):
        """Regular user login should return 200 with /main-menu redirect."""
        user = _make_user("USER0001", "USER0001", "U", "John", "Doe")

        with patch.object(UserRepository, "get_by_id", return_value=user):
            app.dependency_overrides[get_db] = _override_db_with_user(user)
            response = await client.post(
                "/auth/login",
                json={"user_id": "USER0001", "password": "USER0001"},
            )
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["redirect_to"] == "/main-menu"
        assert data["user"]["user_type"] == "U"

    async def test_unknown_user_returns_401(self, client):
        """BR-004: Unknown user should return 401 with 'not found' message."""
        with patch.object(UserRepository, "get_by_id", return_value=None):
            app.dependency_overrides[get_db] = _override_db_with_user(None)
            response = await client.post(
                "/auth/login",
                json={"user_id": "UNKNOWN1", "password": "PASSWORD"},
            )
            app.dependency_overrides.clear()

        assert response.status_code == 401
        assert "not found" in response.json()["detail"].lower()

    async def test_wrong_password_returns_401(self, client):
        """BR-005: Wrong password should return 401."""
        user = _make_user("USER0001", "CORRECT1", "U")

        with patch.object(UserRepository, "get_by_id", return_value=user):
            app.dependency_overrides[get_db] = _override_db_with_user(user)
            response = await client.post(
                "/auth/login",
                json={"user_id": "USER0001", "password": "WRONGPWD"},
            )
            app.dependency_overrides.clear()

        assert response.status_code == 401
        assert "Wrong Password" in response.json()["detail"]

    async def test_blank_user_id_returns_422(self, client):
        """BR-001: Blank user_id should return 422 Unprocessable Entity."""
        response = await client.post(
            "/auth/login",
            json={"user_id": "   ", "password": "PASSWORD"},
        )
        assert response.status_code == 422

    async def test_blank_password_returns_422(self, client):
        """BR-002: Blank password should return 422 Unprocessable Entity."""
        response = await client.post(
            "/auth/login",
            json={"user_id": "USER0001", "password": "   "},
        )
        assert response.status_code == 422

    async def test_user_id_too_long_returns_422(self, client):
        """COBOL PIC X(08): user_id longer than 8 chars rejected."""
        response = await client.post(
            "/auth/login",
            json={"user_id": "TOOLONGID", "password": "PASS1234"},
        )
        assert response.status_code == 422

    async def test_lowercase_credentials_work_via_uppercasing(self, client):
        """BR-003: Lowercase user_id and password are uppercased before lookup."""
        user = _make_user("USER0001", "USER0001", "U", "John", "Doe")
        calls = []

        async def mock_get_by_id(self_repo, user_id):
            calls.append(user_id)
            return user

        with patch.object(UserRepository, "get_by_id", mock_get_by_id):
            app.dependency_overrides[get_db] = _override_db_with_user(user)
            response = await client.post(
                "/auth/login",
                json={"user_id": "user0001", "password": "user0001"},
            )
            app.dependency_overrides.clear()

        assert response.status_code == 200
        # BR-003: lookup was done with uppercased ID
        assert calls[0] == "USER0001"


# ============================================================
# POST /auth/logout
# ============================================================

class TestLogoutEndpoint:
    """Integration tests for /auth/logout (COSGN00C PF3 handler)."""

    async def test_logout_requires_auth(self, client):
        """Logout without token should return 401."""
        response = await client.post("/auth/logout")
        assert response.status_code == 401

    async def test_logout_with_valid_token_returns_200(self, client):
        """Valid token logout should return 200 with thank-you message."""
        token = create_access_token(
            TokenPayload(
                sub="USER0001", user_type="U",
                first_name="John", last_name="Doe"
            )
        )
        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "CardDemo" in data["message"]

    async def test_logout_message_matches_cobol_thank_you(self, client):
        """COSGN00C BR-007: PF3 sends CCDA-MSG-THANK-YOU message."""
        token = create_access_token(
            TokenPayload(
                sub="USER0001", user_type="U",
                first_name="John", last_name="Doe"
            )
        )
        response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = response.json()
        # Must contain the CardDemo app name (from CCDA-MSG-THANK-YOU equivalent)
        assert "CardDemo" in data["message"]


# ============================================================
# GET /auth/me
# ============================================================

class TestGetMeEndpoint:
    """Integration tests for /auth/me."""

    async def test_get_me_without_token_returns_401(self, client):
        response = await client.get("/auth/me")
        assert response.status_code == 401

    async def test_get_me_returns_user_info_from_token(self, client):
        token = create_access_token(
            TokenPayload(
                sub="ADMIN001", user_type="A",
                first_name="System", last_name="Admin"
            )
        )
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "ADMIN001"
        assert data["user_type"] == "A"
        assert data["first_name"] == "System"

    async def test_invalid_token_returns_401(self, client):
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        assert response.status_code == 401
