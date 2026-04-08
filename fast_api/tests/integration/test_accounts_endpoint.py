"""
Integration tests for /api/v1/accounts (COACTVWC / COACTUPC).
"""
import pytest


class TestAccountsEndpoint:

    @pytest.mark.asyncio
    async def test_get_account_success(self, client, account, customer, card, auth_token) -> None:
        """GET /api/v1/accounts/1 — COACTVWC view."""
        response = await client.get(
            "/api/v1/accounts/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["acct_id"] == 1
        assert data["active_status"] == "Y"
        assert float(data["curr_bal"]) == 194.00
        assert data["customer_id"] == 1
        assert "Kessler" in data["customer_name"]

    @pytest.mark.asyncio
    async def test_get_account_not_found(self, client, auth_token) -> None:
        """CICS RESP=13 NOTFND → HTTP 404."""
        response = await client.get(
            "/api/v1/accounts/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_account_active_status(self, client, account, auth_token) -> None:
        """PUT /api/v1/accounts/1 — COACTUPC update active status."""
        response = await client.put(
            "/api/v1/accounts/1",
            json={"active_status": "N"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["active_status"] == "N"

    @pytest.mark.asyncio
    async def test_update_group_id_requires_admin(self, client, account, user_token) -> None:
        """COACTUPC: non-admin cannot update group_id → HTTP 403."""
        response = await client.put(
            "/api/v1/accounts/1",
            json={"group_id": "NEWGROUP1"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_group_id_as_admin(self, client, account, auth_token) -> None:
        """COACTUPC: admin CAN update group_id."""
        response = await client.put(
            "/api/v1/accounts/1",
            json={"group_id": "NEWGROUP1"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["group_id"] == "NEWGROUP1"

    @pytest.mark.asyncio
    async def test_update_invalid_active_status(self, client, account, auth_token) -> None:
        """active_status must be 'Y' or 'N' — 88-level condition validation."""
        response = await client.put(
            "/api/v1/accounts/1",
            json={"active_status": "X"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422
