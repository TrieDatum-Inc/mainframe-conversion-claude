"""
Integration tests for GET /api/v1/admin/menu (COADM01C / CA00).

Tests verify HTTP-level behavior:
  1. 200 OK with menu structure for admin users
  2. 403 Forbidden for non-admin users
  3. 401 Unauthorized for unauthenticated requests
  4. Menu option count = 8 (CDEMO-ADMIN-OPT-COUNT)
  5. Option display text format '{num:02d}. {name}'
  6. Option resolution endpoint /admin/menu/{option}
  7. Invalid option → 422
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.services.admin_service import _ADMIN_OPT_COUNT


class TestAdminMenuEndpoint:
    """Integration tests for COADM01C admin menu API."""

    @pytest.mark.asyncio
    async def test_get_admin_menu_returns_200_for_admin(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        COADM01C SEND-MENU-SCREEN: admin user gets menu (CDEMO-USRTYP-ADMIN = 'A').
        """
        response = await client.get(
            "/api/v1/admin/menu",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_admin_menu_forbidden_for_regular_user(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """
        COADM01C: Non-admin (CDEMO-USRTYP-USER) should not access admin menu.
        HTTP 403 Forbidden.
        """
        response = await client.get(
            "/api/v1/admin/menu",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_admin_menu_unauthorized_without_token(
        self, client: AsyncClient
    ) -> None:
        """Unauthenticated request → 401."""
        response = await client.get("/api/v1/admin/menu")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_menu_contains_correct_option_count(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        COADM01C: CDEMO-ADMIN-OPT-COUNT PIC 9(02) VALUE 8 — must return 8 options.
        """
        response = await client.get(
            "/api/v1/admin/menu",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert data["option_count"] == _ADMIN_OPT_COUNT
        assert len(data["menu_items"]) == _ADMIN_OPT_COUNT

    @pytest.mark.asyncio
    async def test_menu_transaction_id_is_ca00(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        COADM01C: WS-TRANID PIC X(04) VALUE 'CA00'.
        """
        response = await client.get(
            "/api/v1/admin/menu",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert data["transaction_id"] == "CA00"

    @pytest.mark.asyncio
    async def test_menu_items_have_display_text(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        COADM01C BUILD-MENU-OPTIONS: display_text = '{num:02d}. {name}'.
        """
        response = await client.get(
            "/api/v1/admin/menu",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        for item in data["menu_items"]:
            num = item["option_number"]
            assert item["display_text"].startswith(f"{num:02d}. ")

    @pytest.mark.asyncio
    async def test_menu_items_have_rest_endpoints_when_installed(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """Installed options must have a rest_endpoint for client navigation (XCTL replacement)."""
        response = await client.get(
            "/api/v1/admin/menu",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        for item in data["menu_items"]:
            if item["is_installed"]:
                assert item["rest_endpoint"], f"Option {item['option_number']} missing rest_endpoint"

    @pytest.mark.asyncio
    async def test_get_option_1_resolves_correctly(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        COADM01C PROCESS-ENTER-KEY: WS-OPTION=1 → COUSR00C (User Management).
        """
        response = await client.get(
            "/api/v1/admin/menu/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["option_number"] == 1
        assert data["is_installed"] is True

    @pytest.mark.asyncio
    async def test_option_zero_returns_422(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        COADM01C: IF WS-OPTION = ZEROS → 'Please enter a valid option number...'
        """
        response = await client.get(
            "/api/v1/admin/menu/0",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_option_above_max_returns_422(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        COADM01C: IF WS-OPTION > CDEMO-ADMIN-OPT-COUNT → error.
        """
        response = await client.get(
            f"/api/v1/admin/menu/{_ADMIN_OPT_COUNT + 1}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422
