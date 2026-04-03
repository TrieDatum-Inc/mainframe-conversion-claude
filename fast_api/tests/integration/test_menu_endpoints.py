"""Integration tests for menu endpoints — COMEN01C and COADM01C equivalents."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.auth import TokenPayload
from app.utils.security import create_access_token


def _make_token(user_id: str, user_type: str) -> str:
    """Helper to create a test JWT token."""
    return create_access_token(
        TokenPayload(
            sub=user_id,
            user_type=user_type,
            first_name="Test",
            last_name="User",
        )
    )


@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def admin_token() -> str:
    return _make_token("ADMIN001", "A")


@pytest.fixture
def user_token() -> str:
    return _make_token("USER0001", "U")


# ============================================================
# GET /menu/main — COMEN01C SEND-MENU-SCREEN
# ============================================================

class TestGetMainMenu:
    async def test_unauthenticated_request_returns_401(self, async_client):
        """COMEN01C BR-001: No COMMAREA → redirect to signon (401 in REST)."""
        response = await async_client.get("/menu/main")
        assert response.status_code == 401

    async def test_regular_user_gets_main_menu(self, async_client, user_token):
        response = await async_client.get(
            "/menu/main",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["menu_type"] == "main"
        assert data["transaction_id"] == "CM00"
        assert data["program_name"] == "COMEN01C"
        assert len(data["options"]) == 11

    async def test_admin_user_can_also_get_main_menu(self, async_client, admin_token):
        """Admin users can also view the main menu (no restriction in COMEN01C)."""
        response = await async_client.get(
            "/menu/main",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    async def test_main_menu_options_have_correct_structure(
        self, async_client, user_token
    ):
        response = await async_client.get(
            "/menu/main",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        data = response.json()
        option1 = data["options"][0]
        assert option1["option_number"] == 1
        assert option1["name"] == "Account View"
        assert option1["program_name"] == "COACTVWC"
        assert option1["required_user_type"] == "U"


# ============================================================
# POST /menu/main/navigate — COMEN01C PROCESS-ENTER-KEY
# ============================================================

class TestNavigateMainMenu:
    async def test_unauthenticated_returns_401(self, async_client):
        response = await async_client.post(
            "/menu/main/navigate", json={"option": 1}
        )
        assert response.status_code == 401

    async def test_valid_option_1_returns_route(self, async_client, user_token):
        """Option 1 (Account View) should return COACTVWC route."""
        response = await async_client.post(
            "/menu/main/navigate",
            json={"option": 1},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["option_selected"] == 1
        assert data["program_name"] == "COACTVWC"
        assert "/account/view" in data["route"]

    async def test_option_11_copaus0c_returns_error(self, async_client, user_token):
        """COMEN01C BR-005: Option 11 (COPAUS0C) not installed → 400."""
        response = await async_client.post(
            "/menu/main/navigate",
            json={"option": 11},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "not installed" in detail["message"]

    async def test_option_zero_rejected_by_schema(self, async_client, user_token):
        """BR-003: Option 0 is out of valid range."""
        response = await async_client.post(
            "/menu/main/navigate",
            json={"option": 0},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 422

    async def test_option_12_rejected_by_schema(self, async_client, user_token):
        """BR-003: Option 12 exceeds max (11)."""
        response = await async_client.post(
            "/menu/main/navigate",
            json={"option": 12},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 422


# ============================================================
# GET /menu/admin — COADM01C SEND-MENU-SCREEN
# ============================================================

class TestGetAdminMenu:
    async def test_unauthenticated_returns_401(self, async_client):
        response = await async_client.get("/menu/admin")
        assert response.status_code == 401

    async def test_regular_user_gets_403(self, async_client, user_token):
        """COSGN00C BR-006: Regular users cannot access admin menu."""
        response = await async_client.get(
            "/menu/admin",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    async def test_admin_user_gets_admin_menu(self, async_client, admin_token):
        response = await async_client.get(
            "/menu/admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["menu_type"] == "admin"
        assert data["transaction_id"] == "CA00"
        assert data["program_name"] == "COADM01C"
        assert len(data["options"]) == 6

    async def test_admin_menu_option_1_is_user_list(self, async_client, admin_token):
        """COADM02Y option 1 must be 'User List (Security)' → COUSR00C."""
        response = await async_client.get(
            "/menu/admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        data = response.json()
        opt1 = data["options"][0]
        assert opt1["name"] == "User List (Security)"
        assert opt1["program_name"] == "COUSR00C"


# ============================================================
# POST /menu/admin/navigate — COADM01C PROCESS-ENTER-KEY
# ============================================================

class TestNavigateAdminMenu:
    async def test_regular_user_cannot_navigate_admin(self, async_client, user_token):
        """Admin navigation blocked for regular users."""
        response = await async_client.post(
            "/menu/admin/navigate",
            json={"option": 1},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    async def test_admin_option_1_navigates_to_user_list(
        self, async_client, admin_token
    ):
        response = await async_client.post(
            "/menu/admin/navigate",
            json={"option": 1},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["program_name"] == "COUSR00C"
        assert "/admin/users/list" in data["route"]

    async def test_option_7_out_of_range_returns_400(self, async_client, admin_token):
        """COADM01C BR-003: Option 7 exceeds count of 6."""
        response = await async_client.post(
            "/menu/admin/navigate",
            json={"option": 7},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert "valid option" in response.json()["detail"]["message"]

    async def test_invalid_token_returns_401(self, async_client):
        response = await async_client.post(
            "/menu/admin/navigate",
            json={"option": 1},
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


# ============================================================
# Health endpoint
# ============================================================

class TestHealthEndpoint:
    async def test_health_returns_ok(self, async_client):
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
