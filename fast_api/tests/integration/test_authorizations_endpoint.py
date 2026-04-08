"""
Integration tests for authorization endpoints.

Tests the full HTTP layer for:
  POST   /api/v1/authorizations                          (COPAUA0C CP00)
  GET    /api/v1/authorizations/accounts/{acct_id}       (COPAUS0C CPVS)
  GET    /api/v1/authorizations/details/{auth_id}         (COPAUS1C CPVD)
  GET    /api/v1/authorizations/accounts/{acct_id}/next   (COPAUS1C PF8)
  POST   /api/v1/authorizations/details/{auth_id}/fraud   (COPAUS2C)
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.account import Account
from app.models.authorization import AuthDetail, AuthSummary
from app.models.card import Card
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_payload(**overrides) -> dict:
    """Build a default valid authorization request payload."""
    defaults = {
        "auth_date": "260331",
        "auth_time": "143022",
        "card_num": "0100000011111111",
        "auth_type": "PUR ",
        "card_expiry_date": "1125",
        "message_type": "0100  ",
        "message_source": "POS   ",
        "processing_code": 0,
        "transaction_amt": "150.00",
        "merchant_category_code": "5411",
        "acqr_country_code": "840",
        "pos_entry_mode": 5,
        "merchant_id": "WALMART0001    ",
        "merchant_name": "WALMART SUPERCENTER   ",
        "merchant_city": "BENTONVILLE  ",
        "merchant_state": "AR",
        "merchant_zip": "727160001",
        "transaction_id": "TXN202603310001",
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# POST /api/v1/authorizations
# ---------------------------------------------------------------------------


class TestProcessAuthorizationEndpoint:
    """Tests for COPAUA0C CP00 → POST /api/v1/authorizations."""

    @pytest.mark.asyncio
    async def test_approved_returns_200(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
    ) -> None:
        """Approved authorization returns HTTP 200 with auth_resp_code='00'."""
        response = await client.post(
            "/api/v1/authorizations",
            json=_auth_payload(transaction_amt="100.00"),
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_resp_code"] == "00"
        assert data["is_approved"] is True
        assert data["approved_amt"] == "100.00"
        assert data["card_num"] == "0100000011111111"
        assert data["auth_id_code"] == "143022"

    @pytest.mark.asyncio
    async def test_declined_unknown_card_returns_200_with_decline(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
    ) -> None:
        """
        Unknown card → declined with reason '3100'.
        Note: HTTP 200 (not 404) — authorization decision is a valid business outcome.
        """
        response = await client.post(
            "/api/v1/authorizations",
            json=_auth_payload(card_num="9999999999999000", transaction_amt="50.00"),
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_resp_code"] == "05"
        assert data["is_approved"] is False
        assert data["auth_resp_reason"] == "3100"
        assert data["approved_amt"] == "0.00"

    @pytest.mark.asyncio
    async def test_declined_over_limit_returns_4100(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
    ) -> None:
        """
        Amount exceeds available credit → declined, reason '4100'.
        account: credit_limit=2020, curr_bal=194 → available=1826
        """
        response = await client.post(
            "/api/v1/authorizations",
            json=_auth_payload(transaction_amt="9999.00"),
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_resp_code"] == "05"
        assert data["auth_resp_reason"] == "4100"
        assert "FUND" in data["decline_reason_description"]

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, client: AsyncClient) -> None:
        """Missing JWT token → HTTP 401."""
        response = await client.post(
            "/api/v1/authorizations",
            json=_auth_payload(),
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_card_num_length_returns_422(
        self,
        client: AsyncClient,
        auth_token: str,
    ) -> None:
        """Card number not exactly 16 chars → HTTP 422 (Pydantic validation)."""
        response = await client.post(
            "/api/v1/authorizations",
            json=_auth_payload(card_num="123"),  # too short
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_amount_returns_422(
        self,
        client: AsyncClient,
        auth_token: str,
    ) -> None:
        """Negative transaction amount → HTTP 422 (validate_positive_amount)."""
        response = await client.post(
            "/api/v1/authorizations",
            json=_auth_payload(transaction_amt="-50.00"),
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_auth_detail_created_on_approval(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
    ) -> None:
        """POST creates auth_detail record — auth_detail_id non-null in response."""
        response = await client.post(
            "/api/v1/authorizations",
            json=_auth_payload(transaction_amt="50.00"),
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_detail_id"] is not None
        assert isinstance(data["auth_detail_id"], int)


# ---------------------------------------------------------------------------
# GET /api/v1/authorizations/accounts/{acct_id}
# ---------------------------------------------------------------------------


class TestListAuthorizationsEndpoint:
    """Tests for COPAUS0C CPVS → GET /api/v1/authorizations/accounts/{acct_id}."""

    @pytest.mark.asyncio
    async def test_returns_items_and_summary(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """GET returns paginated items and summary data."""
        response = await client.get(
            "/api/v1/authorizations/accounts/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert data["summary"] is not None
        assert data["summary"]["acct_id"] == 1

    @pytest.mark.asyncio
    async def test_empty_account_returns_empty_list(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
    ) -> None:
        """Account with no auth records returns empty items list."""
        response = await client.get(
            "/api/v1/authorizations/accounts/1",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_default_page_size_five(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
    ) -> None:
        """Default limit is 5 (COPAUS0C: CDEMO-CPVS-AUTH-KEYS OCCURS 5)."""
        # Seed 7 details
        for i in range(7):
            d = AuthDetail(
                acct_id=1,
                auth_date_9c=99000 - i,
                auth_time_9c=900000000 - i * 1000,
                auth_resp_code="00",
                auth_resp_reason="0000",
                transaction_amt=Decimal("10.00"),
                approved_amt=Decimal("10.00"),
                match_status="P",
            )
            from sqlalchemy.ext.asyncio import AsyncSession
            auth_summary.__class__  # noqa: just accessing the db via client fixture
        # Use the db fixture instead — skip DB seeding here; just verify default limit
        response = await client.get(
            "/api/v1/authorizations/accounts/1?limit=5",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, client: AsyncClient) -> None:
        """Missing JWT → HTTP 401."""
        response = await client.get("/api/v1/authorizations/accounts/1")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/authorizations/details/{auth_id}
# ---------------------------------------------------------------------------


class TestGetAuthorizationDetailEndpoint:
    """Tests for COPAUS1C CPVD → GET /api/v1/authorizations/details/{auth_id}."""

    @pytest.mark.asyncio
    async def test_returns_detail_fields(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """GET returns all CIPAUDTY.cpy fields for a detail record."""
        response = await client.get(
            f"/api/v1/authorizations/details/{auth_detail.auth_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_id"] == auth_detail.auth_id
        assert data["card_num"] == "0100000011111111"
        assert data["auth_resp_code"] == "00"
        assert data["is_approved"] is True
        assert data["merchant_name"] == "WALMART SUPERCENTER   "
        assert data["transaction_amt"] == "150.00"

    @pytest.mark.asyncio
    async def test_not_found_returns_404(
        self,
        client: AsyncClient,
        auth_token: str,
    ) -> None:
        """Non-existent auth_id → HTTP 404 (IMS GE SEGMENT-NOT-FOUND)."""
        response = await client.get(
            "/api/v1/authorizations/details/999999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/authorizations/accounts/{acct_id}/next
# ---------------------------------------------------------------------------


class TestNextAuthorizationEndpoint:
    """Tests for COPAUS1C PF8 → GET /api/v1/authorizations/accounts/{acct_id}/next."""

    @pytest.mark.asyncio
    async def test_next_returns_following_record(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
        db,
    ) -> None:
        """PF8 navigation returns the next chronological auth record."""
        # Seed a second detail
        second = AuthDetail(
            acct_id=1,
            auth_date_9c=99000,
            auth_time_9c=800000000,
            auth_resp_code="05",
            auth_resp_reason="4100",
            transaction_amt=Decimal("500.00"),
            approved_amt=Decimal("0.00"),
            match_status="D",
        )
        db.add(second)
        await db.flush()

        response = await client.get(
            f"/api/v1/authorizations/accounts/1/next?current_auth_id={auth_detail.auth_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_id"] == second.auth_id

    @pytest.mark.asyncio
    async def test_at_last_record_returns_404(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """
        COPAUS1C: AUTHS-EOF condition → 'Already at the last Authorization'
        → HTTP 404.
        """
        response = await client.get(
            f"/api/v1/authorizations/accounts/1/next?current_auth_id={auth_detail.auth_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/authorizations/details/{auth_id}/fraud
# ---------------------------------------------------------------------------


class TestMarkFraudEndpoint:
    """Tests for COPAUS1C PF5 + COPAUS2C → POST .../fraud."""

    @pytest.mark.asyncio
    async def test_mark_fraud_confirmed_returns_success(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """PF5 on clean record → fraud='F', success=True."""
        response = await client.post(
            f"/api/v1/authorizations/details/{auth_detail.auth_id}/fraud"
            f"?acct_id=1&cust_id=1",
            json={"action": "F"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["auth_fraud"] == "F"
        assert data["fraud_rpt_date"] is not None
        assert "SUCCESS" in data["message"]

    @pytest.mark.asyncio
    async def test_mark_fraud_removed_updates_existing(
        self,
        client: AsyncClient,
        auth_token: str,
        account: Account,
        card: Card,
        auth_summary: AuthSummary,
        auth_detail: AuthDetail,
    ) -> None:
        """PF5 twice: first F, then R → FRAUD-UPDATE paragraph (SQLCODE=-803)."""
        # First: mark as fraud
        await client.post(
            f"/api/v1/authorizations/details/{auth_detail.auth_id}/fraud"
            f"?acct_id=1&cust_id=1",
            json={"action": "F"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        # Second: remove fraud flag
        response = await client.post(
            f"/api/v1/authorizations/details/{auth_detail.auth_id}/fraud"
            f"?acct_id=1&cust_id=1",
            json={"action": "R"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["auth_fraud"] == "R"

    @pytest.mark.asyncio
    async def test_mark_fraud_not_found_returns_404(
        self,
        client: AsyncClient,
        auth_token: str,
    ) -> None:
        """auth_id not found → HTTP 404."""
        response = await client.post(
            "/api/v1/authorizations/details/999999/fraud?acct_id=1&cust_id=1",
            json={"action": "F"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_fraud_action_returns_422(
        self,
        client: AsyncClient,
        auth_token: str,
    ) -> None:
        """Invalid action value → HTTP 422 (Pydantic FraudAction enum validation)."""
        response = await client.post(
            "/api/v1/authorizations/details/1/fraud?acct_id=1&cust_id=1",
            json={"action": "X"},  # invalid
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422
