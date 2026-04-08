"""
Integration tests for /api/v1/cards (COCRDLIC, COCRDSLC, COCRDUPC).
"""
import pytest


class TestCardsEndpoint:

    @pytest.mark.asyncio
    async def test_get_card_success(self, client, card, auth_token) -> None:
        """GET /api/v1/cards/{card_num} — COCRDSLC."""
        response = await client.get(
            "/api/v1/cards/0100000011111111",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["card_num"] == "0100000011111111"
        assert data["active_status"] == "Y"
        assert data["acct_id"] == 1

    @pytest.mark.asyncio
    async def test_get_card_not_found(self, client, auth_token) -> None:
        """CICS RESP=13 NOTFND → HTTP 404."""
        response = await client.get(
            "/api/v1/cards/0000000000000000",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_cards_by_account(self, client, card, auth_token) -> None:
        """GET /api/v1/cards?account_id=1 — COCRDLIC CARDAIX browse."""
        response = await client.get(
            "/api/v1/cards?account_id=1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(item["acct_id"] == 1 for item in data["items"])

    @pytest.mark.asyncio
    async def test_update_card_active_status(self, client, card, auth_token) -> None:
        """PUT /api/v1/cards/{card_num} — COCRDUPC."""
        response = await client.put(
            "/api/v1/cards/0100000011111111",
            json={"active_status": "N"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["active_status"] == "N"

    @pytest.mark.asyncio
    async def test_update_card_embossed_name(self, client, card, auth_token) -> None:
        """COCRDUPC: update CARD-EMBOSSED-NAME."""
        response = await client.put(
            "/api/v1/cards/0100000011111111",
            json={"embossed_name": "I KESSLER"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["embossed_name"] == "I KESSLER"

    @pytest.mark.asyncio
    async def test_update_card_invalid_status(self, client, card, auth_token) -> None:
        """CARD-ACTIVE-STATUS 88-level: only 'Y' or 'N' accepted."""
        response = await client.put(
            "/api/v1/cards/0100000011111111",
            json={"active_status": "X"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422


class TestTransactionsEndpoint:

    @pytest.mark.asyncio
    async def test_list_transactions(self, client, transaction, auth_token) -> None:
        """GET /api/v1/transactions — COTRN00C browse."""
        response = await client.get(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_transaction(self, client, transaction, auth_token) -> None:
        """GET /api/v1/transactions/{id} — COTRN01C."""
        tran_id = transaction.tran_id.strip()
        response = await client.get(
            f"/api/v1/transactions/{tran_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] is not None

    @pytest.mark.asyncio
    async def test_create_transaction(
        self, client, account, card, tran_type, auth_token
    ) -> None:
        """POST /api/v1/transactions — COTRN02C."""
        response = await client.post(
            "/api/v1/transactions",
            json={
                "type_cd": "01",
                "cat_cd": 1,
                "source": "POS TERM",
                "description": "Test purchase",
                "amount": "75.50",
                "card_num": "0100000011111111",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert float(data["amount"]) == 75.50
        assert data["acct_id"] == 1

    @pytest.mark.asyncio
    async def test_payment_endpoint(
        self, client, account, card, tran_type, auth_token
    ) -> None:
        """POST /api/v1/transactions/payment — COBIL00C."""
        response = await client.post(
            "/api/v1/transactions/payment",
            json={"account_id": 1, "payment_amount": "50.00"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["type_cd"] == "02"
        assert float(data["amount"]) == 50.00
