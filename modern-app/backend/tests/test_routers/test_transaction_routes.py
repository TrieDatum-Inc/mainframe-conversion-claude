"""Integration tests for transaction API endpoints."""

import pytest


class TestListTransactionsEndpoint:
    """GET /api/transactions"""

    async def test_requires_auth(self, client):
        resp = await client.get("/api/transactions")
        assert resp.status_code == 401

    async def test_returns_empty_page(self, client, auth_headers):
        resp = await client.get("/api/transactions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    async def test_returns_transactions(self, client, auth_headers, sample_transaction):
        resp = await client.get("/api/transactions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    async def test_pagination_page_size(self, client, auth_headers, multiple_transactions):
        resp = await client.get(
            "/api/transactions", params={"page_size": 5}, headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 5
        assert data["has_next"] is True

    async def test_filter_by_card_number(self, client, auth_headers, sample_transaction):
        resp = await client.get(
            "/api/transactions",
            params={"card_number": "4000002000000000"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1


class TestGetTransactionEndpoint:
    """GET /api/transactions/{transaction_id}"""

    async def test_requires_auth(self, client, sample_transaction):
        resp = await client.get("/api/transactions/0000000000000001")
        assert resp.status_code == 401

    async def test_found(self, client, auth_headers, sample_transaction):
        resp = await client.get(
            "/api/transactions/0000000000000001", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_id"] == "0000000000000001"
        assert data["merchant_name"] == "TEST MARKET"
        assert data["merchant_city"] == "NEW YORK"

    async def test_not_found_returns_404(self, client, auth_headers):
        resp = await client.get(
            "/api/transactions/9999999999999999", headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_all_detail_fields_present(self, client, auth_headers, sample_transaction):
        resp = await client.get(
            "/api/transactions/0000000000000001", headers=auth_headers
        )
        data = resp.json()
        required_fields = [
            "transaction_id", "card_number", "type_code", "category_code",
            "source", "description", "amount", "original_timestamp",
            "processing_timestamp", "merchant_id", "merchant_name",
            "merchant_city", "merchant_zip",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestCreateTransactionEndpoint:
    """POST /api/transactions"""

    async def test_requires_auth(self, client):
        resp = await client.post("/api/transactions", json={})
        assert resp.status_code == 401

    async def test_unconfirmed_returns_422(self, client, auth_headers, sample_transaction):
        payload = _valid_payload(confirmed=False)
        resp = await client.post(
            "/api/transactions", json=payload, headers=auth_headers
        )
        assert resp.status_code == 422

    async def test_confirmed_creates_transaction(self, client, auth_headers, sample_transaction):
        payload = _valid_payload(confirmed=True)
        resp = await client.post(
            "/api/transactions", json=payload, headers=auth_headers
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["transaction_id"] is not None
        assert len(data["transaction_id"]) == 16

    async def test_invalid_merchant_id_rejected(self, client, auth_headers, sample_transaction):
        payload = _valid_payload(confirmed=True)
        payload["merchant_id"] = "ABC123456"
        resp = await client.post(
            "/api/transactions", json=payload, headers=auth_headers
        )
        assert resp.status_code == 422

    async def test_amount_out_of_range_rejected(self, client, auth_headers, sample_transaction):
        payload = _valid_payload(confirmed=True)
        payload["amount"] = -200000000.00
        resp = await client.post(
            "/api/transactions", json=payload, headers=auth_headers
        )
        assert resp.status_code == 422

    async def test_neither_account_nor_card_rejected(self, client, auth_headers):
        payload = _valid_payload(confirmed=True)
        payload.pop("card_number", None)
        payload.pop("account_id", None)
        resp = await client.post(
            "/api/transactions", json=payload, headers=auth_headers
        )
        assert resp.status_code == 422


class TestBillPaymentPreviewEndpoint:
    """GET /api/bill-payment/preview/{account_id}"""

    async def test_requires_auth(self, client):
        resp = await client.get("/api/bill-payment/preview/00000001000")
        assert resp.status_code == 401

    async def test_preview_zero_balance(self, client, auth_headers):
        resp = await client.get(
            "/api/bill-payment/preview/00000001000", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["can_pay"] is False
        assert "nothing to pay" in data["message"].lower()


class TestBillPaymentEndpoint:
    """POST /api/bill-payment"""

    async def test_requires_auth(self, client):
        resp = await client.post(
            "/api/bill-payment", json={"account_id": "00000001000", "confirmed": True}
        )
        assert resp.status_code == 401

    async def test_unconfirmed_preview_only(self, client, auth_headers):
        resp = await client.post(
            "/api/bill-payment",
            json={"account_id": "00000001000", "confirmed": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_id"] == ""


class TestReportEndpoint:
    """POST /api/reports/transactions"""

    async def test_requires_auth(self, client):
        resp = await client.post(
            "/api/reports/transactions",
            json={"report_type": "monthly", "confirmed": True},
        )
        assert resp.status_code == 401

    async def test_unconfirmed_returns_422(self, client, auth_headers):
        resp = await client.post(
            "/api/reports/transactions",
            json={"report_type": "monthly", "confirmed": False},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_monthly_report_returns_data(self, client, auth_headers):
        resp = await client.post(
            "/api/reports/transactions",
            json={"report_type": "monthly", "confirmed": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data
        assert "total_transactions" in data
        assert data["report_type"] == "monthly"

    async def test_custom_missing_dates_returns_422(self, client, auth_headers):
        resp = await client.post(
            "/api/reports/transactions",
            json={"report_type": "custom", "confirmed": True},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_custom_end_before_start_returns_422(self, client, auth_headers):
        resp = await client.post(
            "/api/reports/transactions",
            json={
                "report_type": "custom",
                "start_date": "2024-06-01",
                "end_date": "2024-01-01",
                "confirmed": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_payload(**overrides) -> dict:
    base = {
        "card_number": "4000002000000000",
        "type_code": "01",
        "category_code": "0001",
        "source": "POS TERM",
        "description": "TEST PURCHASE",
        "amount": -75.00,
        "original_date": "2024-03-01",
        "processing_date": "2024-03-01",
        "merchant_id": "123456789",
        "merchant_name": "TEST MARKET",
        "merchant_city": "NEW YORK",
        "merchant_zip": "10001",
        "confirmed": True,
    }
    base.update(overrides)
    return base
