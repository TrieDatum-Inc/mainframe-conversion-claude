"""Integration tests for GET /api/accounts/{acct_id} and PUT /api/accounts/{acct_id}.

Uses httpx AsyncClient against the FastAPI app with mocked service layer.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.schemas.account import AccountDetailResponse, AccountUpdateResponse, CustomerInfo, CardInfo
from app.utils.exceptions import (
    AccountNotFoundError,
    ConcurrentModificationError,
    LockAcquisitionError,
)


@pytest.fixture
def sample_account_response() -> AccountDetailResponse:
    return AccountDetailResponse(
        acct_id="00000000001",
        acct_active_status="Y",
        acct_curr_bal=Decimal("1250.75"),
        acct_credit_limit=Decimal("10000.00"),
        acct_cash_credit_limit=Decimal("2000.00"),
        acct_open_date=date(2020, 1, 15),
        acct_expiration_date=date(2026, 1, 31),
        acct_reissue_date=date(2024, 1, 31),
        acct_curr_cyc_credit=Decimal("500.00"),
        acct_curr_cyc_debit=Decimal("1750.75"),
        acct_addr_zip="20500",
        acct_group_id="PREMIUM",
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        customer=CustomerInfo(
            cust_id="000000001",
            cust_first_name="James",
            cust_last_name="Carter",
            ssn_formatted="123-45-6789",
            cust_fico_credit_score=780,
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        ),
        cards=[
            CardInfo(
                card_num="4111111111111001",
                card_embossed_name="JAMES E CARTER",
                card_expiration_date=date(2026, 1, 31),
                card_active_status="Y",
            )
        ],
    )


@pytest.fixture
def valid_update_payload() -> dict:
    return {
        "updated_at": "2024-01-01T12:00:00",
        "acct_active_status": "Y",
        "acct_credit_limit": "10000.00",
        "acct_cash_credit_limit": "2000.00",
        "acct_curr_bal": "1250.75",
        "acct_curr_cyc_credit": "500.00",
        "acct_curr_cyc_debit": "1750.75",
        "acct_open_date": "2020-01-15",
        "acct_expiration_date": "2026-01-31",
        "acct_reissue_date": "2024-01-31",
        "acct_group_id": "PREMIUM",
        "cust_first_name": "James",
        "cust_middle_name": "Earl",
        "cust_last_name": "Carter",
        "cust_addr_line_1": "1600 Pennsylvania Ave NW",
        "cust_addr_state_cd": "DC",
        "cust_addr_country_cd": "USA",
        "cust_addr_zip": "20500",
        "cust_phone_num_1": {"area_code": "202", "prefix": "456", "line_number": "1111"},
        "cust_ssn": {"part1": "123", "part2": "45", "part3": "6789"},
        "cust_dob": "1960-03-15",
        "cust_eft_account_id": "1234567890",
        "cust_pri_card_holder_ind": "Y",
        "cust_fico_credit_score": 780,
    }


# ---------------------------------------------------------------------------
# GET /api/accounts/{acct_id} tests
# ---------------------------------------------------------------------------

class TestGetAccount:
    @pytest.mark.asyncio
    async def test_returns_200_for_valid_account(self, sample_account_response):
        with patch(
            "app.routers.accounts.AccountService.get_account_view",
            new_callable=AsyncMock,
            return_value=sample_account_response,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/accounts/00000000001")

        assert response.status_code == 200
        data = response.json()
        assert data["acct_id"] == "00000000001"
        assert data["customer"]["cust_first_name"] == "James"
        assert data["customer"]["ssn_formatted"] == "123-45-6789"
        assert len(data["cards"]) == 1

    @pytest.mark.asyncio
    async def test_returns_404_for_missing_account(self):
        with patch(
            "app.routers.accounts.AccountService.get_account_view",
            new_callable=AsyncMock,
            side_effect=AccountNotFoundError("Account not found"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/accounts/99999999999")

        assert response.status_code == 404
        assert "Account not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_returns_400_for_non_numeric_acct_id(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/accounts/ABCDEFGHIJK")

        assert response.status_code == 400
        assert "11 digit number" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_returns_400_for_zero_acct_id(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/accounts/00000000000")

        assert response.status_code == 400
        assert "non zero" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_short_acct_id_is_normalized(self, sample_account_response):
        """COBOL PIC 9(11): '1' should be treated as '00000000001'."""
        with patch(
            "app.routers.accounts.AccountService.get_account_view",
            new_callable=AsyncMock,
            return_value=sample_account_response,
        ) as mock_view:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/accounts/1")

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# PUT /api/accounts/{acct_id} tests
# ---------------------------------------------------------------------------

class TestUpdateAccount:
    @pytest.mark.asyncio
    async def test_returns_200_on_successful_update(self, valid_update_payload):
        update_response = AccountUpdateResponse(
            message="Changes committed to database",
            acct_id="00000000001",
            updated_at=datetime(2024, 1, 1, 12, 0, 1),
        )
        with patch(
            "app.routers.accounts.AccountService.update_account",
            new_callable=AsyncMock,
            return_value=update_response,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.put(
                    "/api/accounts/00000000001", json=valid_update_payload
                )

        assert response.status_code == 200
        assert response.json()["message"] == "Changes committed to database"

    @pytest.mark.asyncio
    async def test_returns_409_on_concurrent_modification(self, valid_update_payload):
        with patch(
            "app.routers.accounts.AccountService.update_account",
            new_callable=AsyncMock,
            side_effect=ConcurrentModificationError(
                "Record changed by some one else. Please review"
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.put(
                    "/api/accounts/00000000001", json=valid_update_payload
                )

        assert response.status_code == 409
        assert "Record changed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_returns_423_on_lock_failure(self, valid_update_payload):
        with patch(
            "app.routers.accounts.AccountService.update_account",
            new_callable=AsyncMock,
            side_effect=LockAcquisitionError("Could not lock account record for update"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.put(
                    "/api/accounts/00000000001", json=valid_update_payload
                )

        assert response.status_code == 423

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_fico_score(self, valid_update_payload):
        """1275-EDIT-FICO-SCORE: range 300-850."""
        invalid = {**valid_update_payload, "cust_fico_credit_score": 100}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put("/api/accounts/00000000001", json=invalid)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_active_status(self, valid_update_payload):
        """1220-EDIT-YESNO: must be Y or N."""
        invalid = {**valid_update_payload, "acct_active_status": "X"}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put("/api/accounts/00000000001", json=invalid)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_ssn(self, valid_update_payload):
        """1265-EDIT-US-SSN: part1 cannot be 666."""
        invalid = {
            **valid_update_payload,
            "cust_ssn": {"part1": "666", "part2": "45", "part3": "6789"},
        }
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put("/api/accounts/00000000001", json=invalid)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_for_future_dob(self, valid_update_payload):
        """EDIT-DATE-OF-BIRTH: must not be in the future."""
        from datetime import timedelta
        future_date = (date.today() + timedelta(days=1)).isoformat()
        invalid = {**valid_update_payload, "cust_dob": future_date}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put("/api/accounts/00000000001", json=invalid)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_422_for_invalid_state_code(self, valid_update_payload):
        """1270-EDIT-US-STATE-CD."""
        invalid = {**valid_update_payload, "cust_addr_state_cd": "ZZ"}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put("/api/accounts/00000000001", json=invalid)

        assert response.status_code == 422
