"""
Integration tests for account_routes.py.

Endpoints tested:
  GET /accounts/{acct_id}  <- COACTVWC (read-only 3-step read)
  PUT /accounts/{acct_id}  <- COACTUPC (update with 35+ validations)

HTTP status codes:
  200 - success
  401 - no token
  404 - account not found
  422 - validation error
"""

import pytest


class TestGetAccountEndpoint:
    """GET /accounts/{acct_id} — COACTVWC."""

    @pytest.mark.asyncio
    async def test_returns_account_and_customer(self, async_client, user_headers):
        resp = await async_client.get("/accounts/10000000001", headers=user_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "account" in body
        assert "customer" in body
        assert body["account"]["acct_id"] == 10000000001

    @pytest.mark.asyncio
    async def test_returns_card_num_from_xref(self, async_client, user_headers):
        """COACTVWC step 1: READ CXACAIX to get card_num."""
        resp = await async_client.get("/accounts/10000000001", headers=user_headers)
        body = resp.json()
        assert body["card_num"] == "4111111111111001"

    @pytest.mark.asyncio
    async def test_returns_customer_data(self, async_client, user_headers):
        """COACTVWC step 3: READ CUSTDAT."""
        resp = await async_client.get("/accounts/10000000001", headers=user_headers)
        body = resp.json()
        assert body["customer"]["first_name"] == "John"
        assert body["customer"]["last_name"] == "Doe"

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client, user_headers):
        resp = await async_client.get("/accounts/99999999999", headers=user_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        resp = await async_client.get("/accounts/10000000001")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_account_is_still_readable(self, async_client, user_headers):
        """COACTVWC: no filter on active_status — reads all accounts."""
        resp = await async_client.get("/accounts/10000000003", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["account"]["active_status"] == "N"


class TestUpdateAccountEndpoint:
    """PUT /accounts/{acct_id} — COACTUPC."""

    def _build_update_body(self, **acct_overrides):
        return {
            "account": {
                "active_status": "Y",
                "curr_bal": "0.00",
                "credit_limit": "5000.00",
                "cash_credit_limit": "2000.00",
                "open_date": "2020-01-01",
                "expiration_date": "2025-12-31",
                "reissue_date": None,
                "curr_cycle_credit": "0.00",
                "curr_cycle_debit": "0.00",
                "addr_zip": "62701",
                "group_id": "GRP001",
                **acct_overrides,
            },
            "customer": {
                "first_name": "John",
                "middle_name": "A",
                "last_name": "Doe",
                "addr_line1": "123 Main St",
                "addr_line2": None,
                "addr_line3": "Springfield",
                "addr_state_cd": "IL",
                "addr_country_cd": "USA",
                "addr_zip": "62701",
                "phone_num1": "(217)555-1234",
                "phone_num2": None,
                "ssn": 123456789,
                "govt_issued_id": None,
                "dob": "1985-06-15",
                "eft_account_id": None,
                "pri_card_holder": "Y",
                "fico_score": 720,
            },
        }

    @pytest.mark.asyncio
    async def test_successful_update_returns_200(self, async_client, user_headers):
        body = self._build_update_body(credit_limit="6000.00")
        resp = await async_client.put(
            "/accounts/10000000001", json=body, headers=user_headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_persists_credit_limit_change(self, async_client, user_headers):
        body = self._build_update_body(credit_limit="7500.00", cash_credit_limit="2000.00")
        resp = await async_client.put(
            "/accounts/10000000001", json=body, headers=user_headers
        )
        assert resp.status_code == 200
        result = resp.json()
        assert float(result["account"]["credit_limit"]) == 7500.00

    @pytest.mark.asyncio
    async def test_negative_credit_limit_returns_422(self, async_client, user_headers):
        body = self._build_update_body(credit_limit="-100.00")
        resp = await async_client.put(
            "/accounts/10000000001", json=body, headers=user_headers
        )
        assert resp.status_code in (422, 422)

    @pytest.mark.asyncio
    async def test_cash_exceeds_credit_returns_422(self, async_client, user_headers):
        body = self._build_update_body(
            credit_limit="1000.00",
            cash_credit_limit="5000.00",
        )
        resp = await async_client.put(
            "/accounts/10000000001", json=body, headers=user_headers
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_expiration_before_open_returns_422(self, async_client, user_headers):
        body = self._build_update_body(
            open_date="2022-01-01",
            expiration_date="2021-12-31",
        )
        resp = await async_client.put(
            "/accounts/10000000001", json=body, headers=user_headers
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_state_code_returns_422(self, async_client, user_headers):
        body = self._build_update_body()
        body["customer"]["addr_state_cd"] = "ZZ"
        resp = await async_client.put(
            "/accounts/10000000001", json=body, headers=user_headers
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_not_found_account_returns_404(self, async_client, user_headers):
        body = self._build_update_body()
        resp = await async_client.put(
            "/accounts/99999999999", json=body, headers=user_headers
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, async_client):
        body = self._build_update_body()
        resp = await async_client.put("/accounts/10000000001", json=body)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_phone_format_returns_422(self, async_client, user_headers):
        """CSLKPCDY phone format: (999)999-9999."""
        body = self._build_update_body()
        body["customer"]["phone_num1"] = "555-1234"  # Wrong format
        resp = await async_client.put(
            "/accounts/10000000001", json=body, headers=user_headers
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_fico_below_300_returns_422(self, async_client, user_headers):
        body = self._build_update_body()
        body["customer"]["fico_score"] = 299
        resp = await async_client.put(
            "/accounts/10000000001", json=body, headers=user_headers
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_fico_above_850_returns_422(self, async_client, user_headers):
        body = self._build_update_body()
        body["customer"]["fico_score"] = 851
        resp = await async_client.put(
            "/accounts/10000000001", json=body, headers=user_headers
        )
        assert resp.status_code == 422
