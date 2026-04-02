"""
Integration tests for transaction_routes.py.

Endpoints tested:
  GET /transactions                    <- COTRN00C (list, paginated)
  GET /transactions/{tran_id}          <- COTRN01C (view)
  POST /transactions                   <- COTRN02C (add)
  POST /billing/pay                    <- COBIL00C (bill payment)
  POST /reports/generate               <- CORPT00C

HTTP status codes:
  200 - success
  401 - no/invalid token
  404 - not found
  422 - business validation failure
"""

from decimal import Decimal

import pytest


class TestListTransactionsEndpoint:
    """GET /transactions — COTRN00C."""

    @pytest.mark.asyncio
    async def test_returns_transaction_list(self, async_client, user_headers):
        resp = await async_client.get("/transactions", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        resp = await async_client.get("/transactions")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_filter_by_card_num(self, async_client, user_headers):
        resp = await async_client.get(
            "/transactions",
            params={"card_num": "4111111111111001"},
            headers=user_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        for item in body["items"]:
            assert item["card_num"] == "4111111111111001"

    @pytest.mark.asyncio
    async def test_page_size_parameter(self, async_client, user_headers):
        resp = await async_client.get(
            "/transactions",
            params={"page_size": 2},
            headers=user_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) <= 2

    @pytest.mark.asyncio
    async def test_response_has_pagination_fields(self, async_client, user_headers):
        resp = await async_client.get("/transactions", headers=user_headers)
        body = resp.json()
        assert "has_next_page" in body
        assert "first_tran_id" in body
        assert "last_tran_id" in body


class TestGetTransactionDetailEndpoint:
    """GET /transactions/{tran_id} — COTRN01C."""

    @pytest.mark.asyncio
    async def test_returns_transaction_detail(self, async_client, user_headers):
        resp = await async_client.get(
            "/transactions/0000000000000001", headers=user_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["tran_id"] == "0000000000000001"
        assert float(body["tran_amt"]) == 75.50

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, user_headers):
        resp = await async_client.get(
            "/transactions/9999999999999999", headers=user_headers
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        resp = await async_client.get("/transactions/0000000000000001")
        assert resp.status_code == 401


class TestAddTransactionEndpoint:
    """POST /transactions — COTRN02C."""

    @pytest.mark.asyncio
    async def test_add_transaction_by_card_num(self, async_client, user_headers):
        body = {
            "card_num": "4111111111111001",
            "tran_type_cd": "DB",
            "tran_cat_cd": 1,
            "tran_amt": "50.00",
            "tran_desc": "Test purchase",
            "tran_source": "TEST",
        }
        resp = await async_client.post("/transactions", json=body, headers=user_headers)
        assert resp.status_code == 201
        result = resp.json()
        assert result["tran_id"] is not None
        assert len(result["tran_id"]) == 16

    @pytest.mark.asyncio
    async def test_add_transaction_by_acct_id(self, async_client, user_headers):
        """COTRN02C Path 2: acct_id -> CXACAIX lookup."""
        body = {
            "acct_id": 10000000002,
            "tran_type_cd": "DB",
            "tran_cat_cd": 9,
            "tran_amt": "25.00",
        }
        resp = await async_client.post("/transactions", json=body, headers=user_headers)
        assert resp.status_code == 201
        result = resp.json()
        assert result["card_num"] == "4111111111111002"

    @pytest.mark.asyncio
    async def test_no_card_or_acct_returns_422(self, async_client, user_headers):
        """Must provide card_num OR acct_id."""
        body = {
            "tran_type_cd": "DB",
            "tran_cat_cd": 1,
            "tran_amt": "50.00",
        }
        resp = await async_client.post("/transactions", json=body, headers=user_headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_tran_type_returns_404(self, async_client, user_headers):
        body = {
            "card_num": "4111111111111001",
            "tran_type_cd": "ZZ",
            "tran_cat_cd": 1,
            "tran_amt": "50.00",
        }
        resp = await async_client.post("/transactions", json=body, headers=user_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        resp = await async_client.post("/transactions", json={})
        assert resp.status_code == 401


class TestBillingPayEndpoint:
    """POST /billing/pay — COBIL00C."""

    @pytest.mark.asyncio
    async def test_successful_payment_returns_200(self, async_client, user_headers):
        body = {"account_id": 10000000001, "payment_amount": "100.00"}
        resp = await async_client.post("/billing/pay", json=body, headers=user_headers)
        assert resp.status_code == 200
        result = resp.json()
        assert result["transaction_id"] is not None

    @pytest.mark.asyncio
    async def test_payment_updates_balance(self, async_client, user_headers):
        body = {"account_id": 10000000001, "payment_amount": "200.00"}
        resp = await async_client.post("/billing/pay", json=body, headers=user_headers)
        assert resp.status_code == 200
        result = resp.json()
        # previous_balance is -1500 or modified by earlier tests, new should be higher
        assert float(result["new_balance"]) > float(result["previous_balance"])

    @pytest.mark.asyncio
    async def test_inactive_account_returns_422(self, async_client, user_headers):
        """COBIL00C: account must be active."""
        body = {"account_id": 10000000003, "payment_amount": "50.00"}
        resp = await async_client.post("/billing/pay", json=body, headers=user_headers)
        assert resp.status_code in (422, 409)

    @pytest.mark.asyncio
    async def test_payment_exceeds_balance_returns_422(self, async_client, user_headers):
        body = {"account_id": 10000000001, "payment_amount": "99999.00"}
        resp = await async_client.post("/billing/pay", json=body, headers=user_headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_account_not_found_returns_404(self, async_client, user_headers):
        body = {"account_id": 99999999999, "payment_amount": "100.00"}
        resp = await async_client.post("/billing/pay", json=body, headers=user_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        body = {"account_id": 10000000001, "payment_amount": "100.00"}
        resp = await async_client.post("/billing/pay", json=body)
        assert resp.status_code == 401


class TestReportGenerateEndpoint:
    """POST /reports/generate — CORPT00C."""

    @pytest.mark.asyncio
    async def test_generate_report_returns_200(self, async_client, admin_headers):
        body = {}
        resp = await async_client.post(
            "/reports/generate", json=body, headers=admin_headers
        )
        assert resp.status_code == 200
        result = resp.json()
        assert "total_transactions" in result
        assert "total_amount" in result

    @pytest.mark.asyncio
    async def test_report_with_card_filter(self, async_client, admin_headers):
        body = {"card_num": "4111111111111001"}
        resp = await async_client.post(
            "/reports/generate", json=body, headers=admin_headers
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["total_transactions"] >= 0
