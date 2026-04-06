"""
Integration tests for account API endpoints.

Tests: GET /api/v1/accounts/{account_id}, PUT /api/v1/accounts/{account_id}
COBOL programs: COACTVWC (view), COACTUPC (update)

Uses FastAPI TestClient with mocked services.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.errors import (
    AccountNoChangesDetectedError,
    AccountNotFoundError,
    CustomerNotFoundError,
)
from app.schemas.account import AccountViewResponse, CustomerDetailResponse


def make_view_response(account_id: int = 10000000001) -> AccountViewResponse:
    """Build a mock AccountViewResponse for testing."""
    customer = CustomerDetailResponse(
        customer_id=100000001,
        ssn_masked="***-**-6789",
        date_of_birth=date(1975, 4, 12),
        fico_score=750,
        first_name="James",
        middle_name="Edward",
        last_name="Anderson",
        address_line_1="123 Main St",
        address_line_2=None,
        city="New York",
        state_code="NY",
        zip_code="10001",
        country_code="USA",
        phone_1="212-555-0101",
        phone_2=None,
        government_id_ref="DL123456789",
        eft_account_id="EFT0000001",
        primary_card_holder="Y",
    )
    return AccountViewResponse(
        account_id=account_id,
        active_status="Y",
        open_date=date(2020, 1, 15),
        expiration_date=date(2025, 1, 15),
        reissue_date=date(2023, 1, 15),
        credit_limit=Decimal("10000.00"),
        cash_credit_limit=Decimal("2000.00"),
        current_balance=Decimal("1234.56"),
        curr_cycle_credit=Decimal("500.00"),
        curr_cycle_debit=Decimal("1734.56"),
        group_id="GROUP001",
        updated_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        customer=customer,
    )


class TestGetAccount:
    """Tests for GET /api/v1/accounts/{account_id}."""

    @pytest.mark.asyncio
    async def test_get_account_success(self, client) -> None:
        """Happy path: returns account + customer details."""
        mock_response = make_view_response()

        with patch(
            "app.api.endpoints.accounts.account_service.view_account",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await client.get("/api/v1/accounts/10000000001")

        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == 10000000001
        assert data["active_status"] == "Y"
        # SSN must be masked in response
        assert data["customer"]["ssn_masked"] == "***-**-6789"
        assert "ssn" not in data["customer"]

    @pytest.mark.asyncio
    async def test_get_account_not_found_returns_404(self, client) -> None:
        """COBOL: COACTVWC READ-ACCT-BY-ACCT-ID RESP=NOTFND → 404."""
        with patch(
            "app.api.endpoints.accounts.account_service.view_account",
            new_callable=AsyncMock,
            side_effect=AccountNotFoundError(99999999999),
        ):
            response = await client.get("/api/v1/accounts/99999999999")

        assert response.status_code == 404
        assert response.json()["detail"]["error_code"] == "ACCOUNT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_account_no_customer_returns_404(self, client) -> None:
        """COBOL: COACTVWC READ-CUST-BY-CUST-ID RESP=NOTFND → 404."""
        with patch(
            "app.api.endpoints.accounts.account_service.view_account",
            new_callable=AsyncMock,
            side_effect=CustomerNotFoundError(10000000001),
        ):
            response = await client.get("/api/v1/accounts/10000000001")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_account_requires_auth(self, regular_client) -> None:
        """Regular users can also access account view (not admin-only)."""
        mock_response = make_view_response()

        with patch(
            "app.api.endpoints.accounts.account_service.view_account",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await regular_client.get("/api/v1/accounts/10000000001")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_account_unauthenticated_returns_401(self, client) -> None:
        """No token → 401."""
        client.headers.clear()
        response = await client.get("/api/v1/accounts/10000000001")
        assert response.status_code == 401


class TestUpdateAccount:
    """Tests for PUT /api/v1/accounts/{account_id}."""

    def make_update_payload(self) -> dict:
        """Build a valid account update payload."""
        return {
            "active_status": "Y",
            "open_date": "2020-01-15",
            "expiration_date": "2025-01-15",
            "reissue_date": "2023-01-15",
            "credit_limit": "10000.00",
            "cash_credit_limit": "2000.00",
            "current_balance": "1234.56",
            "curr_cycle_credit": "500.00",
            "curr_cycle_debit": "1734.56",
            "group_id": "GROUP001",
            "customer": {
                "customer_id": 100000001,
                "first_name": "James",
                "middle_name": "Edward",
                "last_name": "Anderson",
                "address_line_1": "123 Main St",
                "city": "New York",
                "state_code": "NY",
                "zip_code": "10001",
                "country_code": "USA",
                "phone_1": "212-555-0101",
                "ssn_part1": "123",
                "ssn_part2": "45",
                "ssn_part3": "6789",
                "date_of_birth": "1975-04-12",
                "fico_score": 750,
                "primary_card_holder": "Y",
            },
        }

    @pytest.mark.asyncio
    async def test_update_account_success(self, client) -> None:
        """Happy path: valid update returns updated account."""
        mock_response = make_view_response()

        with patch(
            "app.api.endpoints.accounts.account_service.update_account",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            response = await client.put(
                "/api/v1/accounts/10000000001", json=self.make_update_payload()
            )

        assert response.status_code == 200
        assert response.json()["account_id"] == 10000000001

    @pytest.mark.asyncio
    async def test_update_account_no_changes_returns_422(self, client) -> None:
        """COBOL: COACTUPC WS-DATACHANGED-FLAG = 'N' → 422."""
        with patch(
            "app.api.endpoints.accounts.account_service.update_account",
            new_callable=AsyncMock,
            side_effect=AccountNoChangesDetectedError(),
        ):
            response = await client.put(
                "/api/v1/accounts/10000000001", json=self.make_update_payload()
            )

        assert response.status_code == 422
        assert response.json()["detail"]["error_code"] == "NO_CHANGES_DETECTED"

    @pytest.mark.asyncio
    async def test_update_account_invalid_ssn_returns_422(self, client) -> None:
        """COACTUPC SSN validation: part1 not 000 → 422."""
        payload = self.make_update_payload()
        payload["customer"]["ssn_part1"] = "000"  # invalid — COACTUPC validation

        response = await client.put(
            "/api/v1/accounts/10000000001", json=payload
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_invalid_ssn_666_returns_422(self, client) -> None:
        """COACTUPC SSN validation: part1 not 666 → 422."""
        payload = self.make_update_payload()
        payload["customer"]["ssn_part1"] = "666"

        response = await client.put(
            "/api/v1/accounts/10000000001", json=payload
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_invalid_ssn_900_range_returns_422(self, client) -> None:
        """COACTUPC SSN validation: part1 not in 900-999 range → 422."""
        payload = self.make_update_payload()
        payload["customer"]["ssn_part1"] = "950"

        response = await client.put(
            "/api/v1/accounts/10000000001", json=payload
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_cash_limit_exceeds_credit_limit_returns_422(
        self, client
    ) -> None:
        """COACTUPC: cash_credit_limit must not exceed credit_limit → 422."""
        payload = self.make_update_payload()
        payload["credit_limit"] = "1000.00"
        payload["cash_credit_limit"] = "2000.00"  # exceeds credit_limit

        response = await client.put(
            "/api/v1/accounts/10000000001", json=payload
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_account_fico_out_of_range_returns_422(self, client) -> None:
        """COACTUPC: FICO score must be 300-850 → 422."""
        payload = self.make_update_payload()
        payload["customer"]["fico_score"] = 200  # below 300

        response = await client.put(
            "/api/v1/accounts/10000000001", json=payload
        )

        assert response.status_code == 422
