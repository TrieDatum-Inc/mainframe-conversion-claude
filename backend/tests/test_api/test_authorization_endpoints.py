"""
API endpoint tests for the Authorization module.
Uses FastAPI TestClient with mocked service layer.
Tests HTTP status codes, request/response formats, and authentication.
"""
from datetime import date, datetime, time, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.models.authorization import AuthorizationDetail, AuthorizationSummary
from app.schemas.authorization import (
    AuthDetailResponse,
    AuthListItem,
    AuthListResponse,
    AuthSummaryResponse,
    FraudToggleResponse,
)
from app.utils.security import create_access_token


def make_auth_header(user_type: str = "U") -> dict:
    """Create auth header for tests."""
    token = create_access_token({"sub": "TESTUSER", "user_type": user_type})
    return {"Authorization": f"Bearer {token}"}


def make_summary_response() -> AuthSummaryResponse:
    return AuthSummaryResponse(
        account_id=10000000001,
        credit_limit=Decimal("10000.00"),
        cash_limit=Decimal("2000.00"),
        credit_balance=Decimal("3500.00"),
        cash_balance=Decimal("500.00"),
        approved_auth_count=12,
        declined_auth_count=2,
        approved_auth_amount=Decimal("4200.00"),
        declined_auth_amount=Decimal("350.00"),
    )


def make_list_item() -> AuthListItem:
    return AuthListItem(
        auth_id=1,
        transaction_id="TXN0000000001",
        card_number_masked="************1001",
        auth_date=date(2026, 3, 1),
        auth_time=time(10, 25, 33),
        auth_type="PURCHASE",
        approval_status="A",
        match_status="P",
        amount=Decimal("125.50"),
        fraud_status="N",
        fraud_status_display="",
    )


def make_detail_response() -> AuthDetailResponse:
    return AuthDetailResponse(
        auth_id=1,
        account_id=10000000001,
        card_number="4111111111111001",
        card_number_masked="************1001",
        auth_date=date(2026, 3, 1),
        auth_time=time(10, 25, 33),
        auth_response_code="00",
        approval_status="A",
        decline_reason="00-APPROVED",
        auth_code="AUTH01",
        amount=Decimal("125.50"),
        pos_entry_mode="0101",
        auth_source="POS",
        mcc_code="5411",
        card_expiry="03/28",
        auth_type="PURCHASE",
        transaction_id="TXN0000000001",
        match_status="P",
        fraud_status="N",
        fraud_status_display="",
        merchant_name="WHOLE FOODS MARKET",
        merchant_id="M000000001",
        merchant_city="SEATTLE",
        merchant_state="WA",
        merchant_zip="98101",
        processed_at=datetime(2026, 3, 1, 10, 25, 33, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 1, 10, 25, 33, tzinfo=timezone.utc),
    )


class TestGetAuthorizationSummaryList:
    """Tests for GET /api/v1/authorizations."""

    def test_requires_authentication(self) -> None:
        """No auth header → 401. Replaces COPAUS0C EIBCALEN=0 check."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/api/v1/authorizations")
        assert response.status_code == 401

    def test_returns_paginated_list(self, admin_token: str) -> None:
        """Returns paginated summaries for authenticated user."""
        client = TestClient(app, raise_server_exceptions=True)
        summary_resp = make_summary_response()

        expected = {
            "items": [summary_resp.model_dump()],
            "page": 1,
            "page_size": 5,
            "total_count": 1,
            "has_next": False,
            "has_previous": False,
        }

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.list_authorization_summaries",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            response = client.get(
                "/api/v1/authorizations",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200

    def test_regular_user_can_access(self, user_token: str) -> None:
        """Regular user can access — authorization is open to all users."""
        client = TestClient(app, raise_server_exceptions=True)
        expected = {
            "items": [],
            "page": 1,
            "page_size": 5,
            "total_count": 0,
            "has_next": False,
            "has_previous": False,
        }

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.list_authorization_summaries",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            response = client.get(
                "/api/v1/authorizations",
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 200

    def test_page_size_default_is_5(self, user_token: str) -> None:
        """Default page_size=5 matches COPAUS0C 5 rows per screen."""
        client = TestClient(app, raise_server_exceptions=True)
        expected = {
            "items": [],
            "page": 1,
            "page_size": 5,
            "total_count": 0,
            "has_next": False,
            "has_previous": False,
        }

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.list_authorization_summaries",
            new_callable=AsyncMock,
            return_value=expected,
        ) as mock_svc:
            client.get(
                "/api/v1/authorizations",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            _, kwargs = mock_svc.call_args
            assert kwargs.get("page_size", 5) == 5


class TestGetAuthorizationDetails:
    """Tests for GET /api/v1/authorizations/{account_id}/details."""

    def test_requires_authentication(self) -> None:
        """No auth → 401."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/api/v1/authorizations/10000000001/details")
        assert response.status_code == 401

    def test_returns_list_response(self, user_token: str) -> None:
        """Returns AuthListResponse with summary and items."""
        client = TestClient(app, raise_server_exceptions=True)
        expected = AuthListResponse(
            summary=make_summary_response(),
            items=[make_list_item()],
            page=1,
            page_size=5,
            total_count=1,
            has_next=False,
            has_previous=False,
        )

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.list_details_for_account",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            response = client.get(
                "/api/v1/authorizations/10000000001/details",
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "items" in data
        assert data["summary"]["account_id"] == 10000000001

    def test_account_not_found_returns_404(self, user_token: str) -> None:
        """Account not found → 404."""
        client = TestClient(app, raise_server_exceptions=True)

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.list_details_for_account",
            new_callable=AsyncMock,
            side_effect=HTTPException(
                status_code=404,
                detail={
                    "error_code": "AUTH_SUMMARY_NOT_FOUND",
                    "message": "Not found",
                    "details": [],
                },
            ),
        ):
            response = client.get(
                "/api/v1/authorizations/9999/details",
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 404


class TestGetAuthorizationDetail:
    """Tests for GET /api/v1/authorizations/detail/{auth_id}."""

    def test_requires_authentication(self) -> None:
        """No auth → 401."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.get("/api/v1/authorizations/detail/1")
        assert response.status_code == 401

    def test_returns_detail_response(self, user_token: str) -> None:
        """Returns AuthDetailResponse with all COPAU01 screen fields."""
        client = TestClient(app, raise_server_exceptions=True)
        detail_resp = make_detail_response()

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.get_authorization_detail",
            new_callable=AsyncMock,
            return_value=detail_resp,
        ):
            response = client.get(
                "/api/v1/authorizations/detail/1",
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_id"] == 1
        assert data["merchant_name"] == "WHOLE FOODS MARKET"
        assert data["decline_reason"] == "00-APPROVED"
        assert data["approval_status"] == "A"
        assert "card_number_masked" in data

    def test_not_found_returns_404(self, user_token: str) -> None:
        """Authorization not found → 404."""
        client = TestClient(app, raise_server_exceptions=True)

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.get_authorization_detail",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=404, detail={"error_code": "AUTH_DETAIL_NOT_FOUND", "message": "Not found", "details": []}),
        ):
            response = client.get(
                "/api/v1/authorizations/detail/9999",
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 404


class TestFraudToggle:
    """
    Tests for PUT /api/v1/authorizations/detail/{auth_id}/fraud.
    Replaces: COPAUS1C PF5 → COPAUS2C LINK flow.
    """

    def test_requires_authentication(self) -> None:
        """No auth → 401."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.put(
            "/api/v1/authorizations/detail/1/fraud",
            json={"current_fraud_status": "N"},
        )
        assert response.status_code == 401

    def test_toggle_n_to_f(self, user_token: str) -> None:
        """Toggle N→F returns new_fraud_status='F'."""
        client = TestClient(app, raise_server_exceptions=True)
        toggle_response = FraudToggleResponse(
            auth_id=1,
            previous_fraud_status="N",
            new_fraud_status="F",
            fraud_status_display="FRAUD",
            fraud_report_date=datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc),
            message="ADD SUCCESS",
        )

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.toggle_fraud_flag",
            new_callable=AsyncMock,
            return_value=toggle_response,
        ):
            response = client.put(
                "/api/v1/authorizations/detail/1/fraud",
                json={"current_fraud_status": "N"},
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["new_fraud_status"] == "F"
        assert data["fraud_status_display"] == "FRAUD"
        assert data["message"] == "ADD SUCCESS"

    def test_toggle_f_to_r(self, user_token: str) -> None:
        """Toggle F→R returns new_fraud_status='R'."""
        client = TestClient(app, raise_server_exceptions=True)
        toggle_response = FraudToggleResponse(
            auth_id=1,
            previous_fraud_status="F",
            new_fraud_status="R",
            fraud_status_display="REMOVED",
            fraud_report_date=datetime(2026, 3, 21, 12, 0, 0, tzinfo=timezone.utc),
            message="UPDT SUCCESS",
        )

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.toggle_fraud_flag",
            new_callable=AsyncMock,
            return_value=toggle_response,
        ):
            response = client.put(
                "/api/v1/authorizations/detail/1/fraud",
                json={"current_fraud_status": "F"},
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["new_fraud_status"] == "R"
        assert data["fraud_status_display"] == "REMOVED"

    def test_invalid_fraud_status_returns_422(self, user_token: str) -> None:
        """Invalid current_fraud_status → 422 validation error."""
        client = TestClient(app, raise_server_exceptions=True)
        response = client.put(
            "/api/v1/authorizations/detail/1/fraud",
            json={"current_fraud_status": "X"},  # invalid value
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 422

    def test_admin_can_toggle(self, admin_token: str) -> None:
        """Admin user can also toggle fraud flag."""
        client = TestClient(app, raise_server_exceptions=True)
        toggle_response = FraudToggleResponse(
            auth_id=1,
            previous_fraud_status="N",
            new_fraud_status="F",
            fraud_status_display="FRAUD",
            fraud_report_date=datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc),
            message="ADD SUCCESS",
        )

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.toggle_fraud_flag",
            new_callable=AsyncMock,
            return_value=toggle_response,
        ):
            response = client.put(
                "/api/v1/authorizations/detail/1/fraud",
                json={"current_fraud_status": "N"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        assert response.status_code == 200

    def test_conflict_returns_409(self, user_token: str) -> None:
        """Stale fraud status → 409 Conflict."""
        client = TestClient(app, raise_server_exceptions=True)

        with patch(
            "app.api.endpoints.authorizations.AuthorizationService.toggle_fraud_flag",
            new_callable=AsyncMock,
            side_effect=HTTPException(
                status_code=409,
                detail={
                    "error_code": "FRAUD_STATUS_MISMATCH",
                    "message": "Status mismatch",
                    "details": [],
                },
            ),
        ):
            response = client.put(
                "/api/v1/authorizations/detail/1/fraud",
                json={"current_fraud_status": "F"},
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 409
