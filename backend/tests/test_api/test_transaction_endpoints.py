"""
Integration tests for transaction, billing, and report API endpoints.

Tests are organized by endpoint and cover:
  - Happy path (200/201/202 responses)
  - Error cases (404, 422, 409)
  - Authentication required (401)
  - Business rules from COBOL source
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from app.exceptions.errors import (
    AccountNotFoundError,
    CardNotFoundError,
    NothingToPayError,
    TransactionNotFoundError,
    TransactionTypeNotFoundError,
)


# =============================================================================
# Helpers
# =============================================================================

def transaction_detail_payload():
    return {
        "card_number": "4111111111111001",
        "transaction_type_code": "01",
        "transaction_category_code": "1001",
        "transaction_source": "POS TERM",
        "description": "TEST PURCHASE FROM API TEST",
        "amount": "-52.47",
        "original_date": "2026-04-01",
        "processed_date": "2026-04-02",
        "merchant_id": "100000001",
        "merchant_name": "TEST MERCHANT",
        "merchant_city": "NEW YORK",
        "merchant_zip": "10001",
        "confirm": "Y",
    }


# =============================================================================
# GET /api/v1/transactions — COTRN00C
# =============================================================================


class TestListTransactionsEndpoint:
    async def test_requires_authentication(self, client_no_auth):
        """COTRN00C: EIBCALEN=0 → unauthorized (401)."""
        resp = await client_no_auth.get("/api/v1/transactions")
        assert resp.status_code == 401

    async def test_returns_200_with_valid_token(self, client):
        """COTRN00C: valid token returns list."""
        with patch(
            "app.api.endpoints.transactions.TransactionService"
        ) as MockService:
            mock_svc = AsyncMock()
            MockService.return_value = mock_svc
            mock_response = MagicMock()
            mock_response.dict.return_value = {
                "items": [],
                "page": 1,
                "page_size": 10,
                "total_count": 0,
                "has_next": False,
                "has_previous": False,
            }
            mock_response.model_dump.return_value = mock_response.dict.return_value
            mock_svc.list_transactions.return_value = mock_response

            resp = await client.get("/api/v1/transactions")
            assert resp.status_code == 200

    async def test_default_page_size_is_10(self, client):
        """COTRN00C: 10 rows per page (POPULATE-TRAN-DATA loop limit)."""
        with patch(
            "app.api.endpoints.transactions.TransactionService"
        ) as MockService:
            mock_svc = AsyncMock()
            MockService.return_value = mock_svc
            mock_svc.list_transactions.return_value = MagicMock(
                model_dump=lambda: {
                    "items": [],
                    "page": 1,
                    "page_size": 10,
                    "total_count": 0,
                    "has_next": False,
                    "has_previous": False,
                }
            )
            resp = await client.get("/api/v1/transactions")
            # Verify service called with default page_size=10
            call_kwargs = mock_svc.list_transactions.call_args.kwargs
            assert call_kwargs.get("page_size", 10) == 10


# =============================================================================
# GET /api/v1/transactions/{transaction_id} — COTRN01C
# =============================================================================


class TestGetTransactionEndpoint:
    async def test_requires_authentication(self, client_no_auth):
        """COTRN01C: EIBCALEN=0 → 401."""
        resp = await client_no_auth.get("/api/v1/transactions/0000000000000001")
        assert resp.status_code == 401

    async def test_returns_404_for_unknown_id(self, client):
        """COTRN01C: READ RESP=NOTFND → 404."""
        with patch(
            "app.api.endpoints.transactions.TransactionService"
        ) as MockService:
            mock_svc = AsyncMock()
            MockService.return_value = mock_svc
            mock_svc.get_transaction.side_effect = TransactionNotFoundError("9999999999999999")

            resp = await client.get("/api/v1/transactions/9999999999999999")
            assert resp.status_code == 404
            body = resp.json()
            assert body["detail"]["error_code"] == "TRANSACTION_NOT_FOUND"


# =============================================================================
# POST /api/v1/transactions — COTRN02C
# =============================================================================


class TestCreateTransactionEndpoint:
    async def test_requires_authentication(self, client_no_auth):
        """COTRN02C: EIBCALEN=0 → 401."""
        resp = await client_no_auth.post(
            "/api/v1/transactions", json=transaction_detail_payload()
        )
        assert resp.status_code == 401

    async def test_returns_422_when_confirm_not_y(self, client):
        """COTRN02C: CONFIRMI != 'Y' → 422."""
        payload = transaction_detail_payload()
        payload["confirm"] = "N"
        resp = await client.post("/api/v1/transactions", json=payload)
        assert resp.status_code == 422

    async def test_returns_422_when_amount_zero(self, client):
        """COTRN02C VALIDATE-INPUT-FIELDS: TRNAMI = 0 → 422."""
        payload = transaction_detail_payload()
        payload["amount"] = "0.00"
        resp = await client.post("/api/v1/transactions", json=payload)
        assert resp.status_code == 422

    async def test_returns_422_when_neither_card_nor_account(self, client):
        """COTRN02C: both CARDINPI and ACCTIDOI blank → 422."""
        payload = transaction_detail_payload()
        del payload["card_number"]
        resp = await client.post("/api/v1/transactions", json=payload)
        assert resp.status_code == 422

    async def test_returns_422_when_processed_before_original(self, client):
        """COTRN02C: TRNPROCI < TRNORIGI → 422."""
        payload = transaction_detail_payload()
        payload["original_date"] = "2026-04-05"
        payload["processed_date"] = "2026-04-04"  # before original
        resp = await client.post("/api/v1/transactions", json=payload)
        assert resp.status_code == 422

    async def test_returns_404_when_card_not_found(self, client):
        """COTRN02C LOOKUP-ACCT-FROM-CARD: CCXREF NOTFND → 404."""
        with patch(
            "app.api.endpoints.transactions.TransactionService"
        ) as MockService:
            mock_svc = AsyncMock()
            MockService.return_value = mock_svc
            mock_svc.create_transaction.side_effect = CardNotFoundError("9999999999999999")

            resp = await client.post(
                "/api/v1/transactions", json=transaction_detail_payload()
            )
            assert resp.status_code == 404

    async def test_returns_201_on_success(self, client):
        """COTRN02C: successful WRITE → 201 Created."""
        with patch(
            "app.api.endpoints.transactions.TransactionService"
        ) as MockService:
            mock_svc = AsyncMock()
            MockService.return_value = mock_svc
            mock_result = MagicMock()
            mock_result.transaction_id = "0000000000000099"
            mock_result.card_number = "4111111111111001"
            mock_result.transaction_type_code = "01"
            mock_result.transaction_category_code = "1001"
            mock_result.transaction_source = "POS TERM"
            mock_result.description = "TEST PURCHASE FROM API TEST"
            mock_result.amount = Decimal("-52.47")
            mock_result.original_date = date(2026, 4, 1)
            mock_result.processed_date = date(2026, 4, 2)
            mock_result.merchant_id = "100000001"
            mock_result.merchant_name = "TEST MERCHANT"
            mock_result.merchant_city = "NEW YORK"
            mock_result.merchant_zip = "10001"
            mock_result.created_at = None
            mock_result.updated_at = None
            mock_svc.create_transaction.return_value = mock_result

            resp = await client.post(
                "/api/v1/transactions", json=transaction_detail_payload()
            )
            assert resp.status_code == 201


# =============================================================================
# GET /api/v1/billing/{account_id}/balance — COBIL00C Phase 1
# =============================================================================


class TestGetBalanceEndpoint:
    async def test_requires_authentication(self, client_no_auth):
        """COBIL00C: EIBCALEN=0 → 401."""
        resp = await client_no_auth.get("/api/v1/billing/10000000001/balance")
        assert resp.status_code == 401

    async def test_returns_404_for_unknown_account(self, client):
        """COBIL00C READ-ACCTDAT-FILE: NOTFND → 404."""
        with patch(
            "app.api.endpoints.billing.BillingService"
        ) as MockService:
            mock_svc = AsyncMock()
            MockService.return_value = mock_svc
            mock_svc.get_balance.side_effect = AccountNotFoundError(99999999999)

            resp = await client.get("/api/v1/billing/99999999999/balance")
            assert resp.status_code == 404
            body = resp.json()
            assert body["detail"]["error_code"] == "ACCOUNT_NOT_FOUND"


# =============================================================================
# POST /api/v1/billing/{account_id}/payment — COBIL00C Phase 2
# =============================================================================


class TestProcessPaymentEndpoint:
    async def test_requires_authentication(self, client_no_auth):
        """COBIL00C: EIBCALEN=0 → 401."""
        resp = await client_no_auth.post(
            "/api/v1/billing/10000000001/payment", json={"confirm": "Y"}
        )
        assert resp.status_code == 401

    async def test_returns_422_when_confirm_not_y(self, client):
        """COBIL00C: CONFIRMI != 'Y' → 422."""
        resp = await client.post(
            "/api/v1/billing/10000000001/payment", json={"confirm": "N"}
        )
        assert resp.status_code == 422

    async def test_returns_422_when_nothing_to_pay(self, client):
        """COBIL00C: ACCT-CURR-BAL <= 0 → 'You have nothing to pay...' → 422."""
        with patch(
            "app.api.endpoints.billing.BillingService"
        ) as MockService:
            mock_svc = AsyncMock()
            MockService.return_value = mock_svc
            mock_svc.process_payment.side_effect = NothingToPayError(10000000001)

            resp = await client.post(
                "/api/v1/billing/10000000001/payment", json={"confirm": "Y"}
            )
            assert resp.status_code == 422
            body = resp.json()
            assert body["detail"]["error_code"] == "NOTHING_TO_PAY"


# =============================================================================
# POST /api/v1/reports/request — CORPT00C
# =============================================================================


class TestSubmitReportEndpoint:
    async def test_requires_authentication(self, client_no_auth):
        """CORPT00C: EIBCALEN=0 → 401."""
        resp = await client_no_auth.post(
            "/api/v1/reports/request",
            json={"report_type": "M", "confirm": "Y"},
        )
        assert resp.status_code == 401

    async def test_returns_422_when_confirm_not_y(self, client):
        """CORPT00C: CONFIRMI != 'Y' → 422."""
        resp = await client.post(
            "/api/v1/reports/request",
            json={"report_type": "M", "confirm": "N"},
        )
        assert resp.status_code == 422

    async def test_returns_422_for_invalid_report_type(self, client):
        """CORPT00C: report_type must be M, Y, or C."""
        resp = await client.post(
            "/api/v1/reports/request",
            json={"report_type": "X", "confirm": "Y"},
        )
        assert resp.status_code == 422

    async def test_returns_202_on_success(self, client):
        """CORPT00C: WRITEQ TD JOBS success → 202 Accepted."""
        with patch(
            "app.api.endpoints.reports.ReportService"
        ) as MockService:
            mock_svc = AsyncMock()
            MockService.return_value = mock_svc
            from datetime import datetime
            mock_result = MagicMock()
            mock_result.request_id = 42
            mock_result.report_type = "M"
            mock_result.start_date = date(2026, 4, 1)
            mock_result.end_date = date(2026, 4, 30)
            mock_result.status = "PENDING"
            mock_result.requested_at = datetime.now()
            mock_result.message = "Report request submitted successfully."
            mock_svc.request_report.return_value = mock_result

            resp = await client.post(
                "/api/v1/reports/request",
                json={"report_type": "M", "confirm": "Y"},
            )
            assert resp.status_code == 202

    async def test_custom_report_requires_end_gte_start(self, client):
        """CORPT00C custom: end_date < start_date → 422."""
        resp = await client.post(
            "/api/v1/reports/request",
            json={
                "report_type": "C",
                "start_date": "2026-04-05",
                "end_date": "2026-04-01",  # before start
                "confirm": "Y",
            },
        )
        assert resp.status_code == 422


# =============================================================================
# Fixtures (tests in this file use the shared conftest fixtures + these extras)
# =============================================================================

@pytest.fixture
async def client_no_auth(db_session):
    """Client without any authorization headers."""
    from httpx import ASGITransport, AsyncClient
    from app.database import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
