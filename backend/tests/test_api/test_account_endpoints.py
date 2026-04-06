"""
Integration tests for account endpoints.

Tests GET /api/v1/accounts/{id} and PUT /api/v1/accounts/{id}.
"""

import pytest
from httpx import AsyncClient

from app.models.account import Account
from app.models.account_customer_xref import AccountCustomerXref
from app.models.customer import Customer


class TestGetAccount:
    @pytest.mark.asyncio
    async def test_get_account_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/accounts/100001")
        assert resp.status_code == 403 or resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_account_not_found(
        self,
        client: AsyncClient,
        admin_headers: dict,
        sample_account_customer_xref,
    ):
        resp = await client.get("/api/v1/accounts/999999", headers=admin_headers)
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
        assert data["detail"]["error_code"] == "ACCOUNT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_account_success(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_account_customer_xref,
        sample_account: Account,
        sample_customer: Customer,
    ):
        resp = await client.get(
            f"/api/v1/accounts/{sample_account.account_id}",
            headers=user_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["account_id"] == sample_account.account_id
        assert data["active_status"] == "Y"
        # SSN must be masked
        assert "***" in data["customer"]["ssn_masked"]
        assert "123456789" not in str(data["customer"])
        # Verify customer data
        assert data["customer"]["first_name"] == "John"
        assert data["customer"]["last_name"] == "Doe"


class TestUpdateAccount:
    @pytest.mark.asyncio
    async def test_update_no_changes_returns_422(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_account_customer_xref,
        sample_account: Account,
        sample_customer: Customer,
    ):
        # Send request with same values as existing data
        resp = await client.put(
            f"/api/v1/accounts/{sample_account.account_id}",
            headers=user_headers,
            json={
                "active_status": "Y",  # same as existing
                "customer": {
                    "first_name": "John",     # same as existing
                    "last_name": "Doe",       # same as existing
                },
            },
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["detail"]["error_code"] == "NO_CHANGES_DETECTED"

    @pytest.mark.asyncio
    async def test_update_account_status(
        self,
        client: AsyncClient,
        user_headers: dict,
        sample_account_customer_xref,
        sample_account: Account,
        sample_customer: Customer,
    ):
        resp = await client.put(
            f"/api/v1/accounts/{sample_account.account_id}",
            headers=user_headers,
            json={
                "active_status": "N",  # changed
                "customer": {
                    "first_name": "John",
                    "last_name": "Doe",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_status"] == "N"

    @pytest.mark.asyncio
    async def test_update_rejects_invalid_ssn_000(
        self,
        client: AsyncClient,
        user_headers: dict,
    ):
        resp = await client.put(
            "/api/v1/accounts/100001",
            headers=user_headers,
            json={
                "customer": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "ssn_part1": "000",  # invalid
                    "ssn_part2": "45",
                    "ssn_part3": "6789",
                },
            },
        )
        # Pydantic validation error
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_update_rejects_cash_limit_exceeds_credit(
        self,
        client: AsyncClient,
        user_headers: dict,
    ):
        resp = await client.put(
            "/api/v1/accounts/100001",
            headers=user_headers,
            json={
                "credit_limit": 1000,
                "cash_credit_limit": 9999,  # exceeds credit_limit
                "customer": {"first_name": "John", "last_name": "Doe"},
            },
        )
        assert resp.status_code == 422
