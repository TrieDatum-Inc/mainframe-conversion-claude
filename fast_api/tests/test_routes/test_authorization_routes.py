"""
Integration tests for authorization_routes.py.

Endpoints tested:
  GET /authorizations                                <- COPAUS0C
  GET /authorizations/{acct_id}/details             <- COPAUS1C
  GET /authorizations/{acct_id}/details/{date}/{time} <- COPAUS1C detail
  POST /authorizations/fraud-flag                   <- COPAUS2C
  POST /authorizations/process                      <- COPAUA0C
"""

import pytest


class TestGetAuthSummariesEndpoint:
    """GET /authorizations — COPAUS0C."""

    @pytest.mark.asyncio
    async def test_returns_auth_summary_list(self, async_client, user_headers):
        resp = await async_client.get("/authorizations", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total_count" in body

    @pytest.mark.asyncio
    async def test_filter_by_account_id(self, async_client, user_headers):
        resp = await async_client.get(
            "/authorizations",
            params={"account_id": 10000000001},
            headers=user_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_count"] == 1
        assert body["items"][0]["acct_id"] == 10000000001

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        resp = await async_client.get("/authorizations")
        assert resp.status_code == 401


class TestGetAuthDetailsEndpoint:
    """GET /authorizations/{acct_id}/details — COPAUS1C list."""

    @pytest.mark.asyncio
    async def test_returns_detail_list_for_account(self, async_client, user_headers):
        resp = await async_client.get(
            "/authorizations/10000000001/details", headers=user_headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 2

    @pytest.mark.asyncio
    async def test_empty_list_for_unknown_account(self, async_client, user_headers):
        resp = await async_client.get(
            "/authorizations/99999999999/details", headers=user_headers
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetAuthDetailEndpoint:
    """GET /authorizations/{acct_id}/details/{date}/{time} — COPAUS1C."""

    @pytest.mark.asyncio
    async def test_returns_single_detail(self, async_client, user_headers):
        resp = await async_client.get(
            "/authorizations/10000000001/details/2024-01-15/10:30:00",
            headers=user_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["acct_id"] == 10000000001
        assert body["response_code"] == "00"

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, user_headers):
        resp = await async_client.get(
            "/authorizations/10000000001/details/2000-01-01/00:00:00",
            headers=user_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_fraud_flag(self, async_client, user_headers):
        resp = await async_client.get(
            "/authorizations/10000000001/details/2024-01-15/10:30:00",
            headers=user_headers,
        )
        body = resp.json()
        assert body["fraud_flag"] == "N"


class TestProcessAuthorizationEndpoint:
    """POST /authorizations/process — COPAUA0C."""

    @pytest.mark.asyncio
    async def test_approve_within_credit_limit(self, async_client, user_headers):
        body = {
            "card_num": "4111111111111001",
            "requested_amt": "100.00",
            "auth_type": "P",
        }
        resp = await async_client.post(
            "/authorizations/process", json=body, headers=user_headers
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["response_code"] == "00"
        assert float(result["approved_amt"]) == 100.00

    @pytest.mark.asyncio
    async def test_decline_exceeds_credit_limit(self, async_client, user_headers):
        body = {
            "card_num": "4111111111111001",
            "requested_amt": "9999.00",
            "auth_type": "P",
        }
        resp = await async_client.post(
            "/authorizations/process", json=body, headers=user_headers
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["response_code"] == "51"
        assert float(result["approved_amt"]) == 0.00

    @pytest.mark.asyncio
    async def test_unknown_card_returns_404(self, async_client, user_headers):
        body = {
            "card_num": "9999999999999999",
            "requested_amt": "100.00",
            "auth_type": "P",
        }
        resp = await async_client.post(
            "/authorizations/process", json=body, headers=user_headers
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_approved_has_tran_id(self, async_client, user_headers):
        body = {
            "card_num": "4111111111111002",
            "requested_amt": "50.00",
            "auth_type": "P",
        }
        resp = await async_client.post(
            "/authorizations/process", json=body, headers=user_headers
        )
        assert resp.status_code == 200
        result = resp.json()
        if result["response_code"] == "00":
            assert result["tran_id"] is not None

    @pytest.mark.asyncio
    async def test_declined_has_no_tran_id(self, async_client, user_headers):
        body = {
            "card_num": "4111111111111001",
            "requested_amt": "99999.00",
            "auth_type": "P",
        }
        resp = await async_client.post(
            "/authorizations/process", json=body, headers=user_headers
        )
        result = resp.json()
        assert result["tran_id"] is None

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        body = {"card_num": "4111111111111001", "requested_amt": "100.00", "auth_type": "P"}
        resp = await async_client.post("/authorizations/process", json=body)
        assert resp.status_code == 401


class TestFraudFlagEndpoint:
    """POST /authorizations/fraud-flag — COPAUS2C."""

    @pytest.mark.asyncio
    async def test_flag_fraud_returns_200(self, async_client, user_headers):
        body = {
            "acct_id": 10000000001,
            "auth_date": "2024-01-15",
            "auth_time": "10:30:00",
            "fraud_reason": "Suspicious pattern",
            "fraud_status": "P",
        }
        resp = await async_client.post(
            "/authorizations/fraud-flag", json=body, headers=user_headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_flag_fraud_updates_detail_record(self, async_client, user_headers):
        body = {
            "acct_id": 10000000001,
            "auth_date": "2024-01-15",
            "auth_time": "10:30:00",
            "fraud_reason": "Card cloning",
            "fraud_status": "C",
        }
        await async_client.post(
            "/authorizations/fraud-flag", json=body, headers=user_headers
        )

        # Check detail record now shows fraud_flag='Y'
        detail_resp = await async_client.get(
            "/authorizations/10000000001/details/2024-01-15/10:30:00",
            headers=user_headers,
        )
        assert detail_resp.status_code == 200
        assert detail_resp.json()["fraud_flag"] == "Y"

    @pytest.mark.asyncio
    async def test_nonexistent_detail_returns_404(self, async_client, user_headers):
        body = {
            "acct_id": 10000000001,
            "auth_date": "2000-01-01",
            "auth_time": "00:00:00",
            "fraud_reason": "Ghost",
            "fraud_status": "P",
        }
        resp = await async_client.post(
            "/authorizations/fraud-flag", json=body, headers=user_headers
        )
        assert resp.status_code == 404
