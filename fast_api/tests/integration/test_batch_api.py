"""Integration tests for batch processing API endpoints.

Tests all 5 endpoints:
- POST /api/batch/transaction-posting
- POST /api/batch/transaction-report
- POST /api/batch/interest-calculation
- GET  /api/batch/export
- POST /api/batch/import
- GET  /api/batch/jobs/{job_id}
"""

from datetime import date, datetime, timezone

import pytest


class TestTransactionPostingEndpoint:
    """Tests for POST /api/batch/transaction-posting (CBTRN02C)."""

    @pytest.mark.asyncio
    async def test_post_valid_transaction_returns_200(
        self, client, sample_account, sample_xref
    ):
        """Valid transaction is posted successfully."""
        response = await client.post(
            "/api/batch/transaction-posting",
            json={
                "transactions": [{
                    "tran_id": "TXN0000000000001",
                    "tran_type_cd": "01",
                    "tran_cat_cd": "0001",
                    "tran_source": "POS",
                    "tran_desc": "Test purchase",
                    "tran_amt": "-50.00",
                    "tran_merchant_id": "000000001",
                    "tran_merchant_name": "Test Merchant",
                    "tran_merchant_city": "Test City",
                    "tran_merchant_zip": "12345",
                    "tran_card_num": "4111111111111111",
                    "tran_orig_ts": "2026-04-01T12:00:00Z",
                }]
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["transactions_posted"] == 1
        assert body["transactions_rejected"] == 0
        assert body["has_rejects"] is False

    @pytest.mark.asyncio
    async def test_post_invalid_card_returns_reject(self, client):
        """Unknown card number produces reject with reason 100."""
        response = await client.post(
            "/api/batch/transaction-posting",
            json={
                "transactions": [{
                    "tran_id": "TXN0000000000001",
                    "tran_type_cd": "01",
                    "tran_cat_cd": "0001",
                    "tran_source": "POS",
                    "tran_desc": "Test",
                    "tran_amt": "-50.00",
                    "tran_card_num": "9999999999999999",
                    "tran_orig_ts": "2026-04-01T12:00:00Z",
                }]
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["transactions_rejected"] == 1
        assert body["has_rejects"] is True
        assert body["rejects"][0]["reason_code"] == "100"

    @pytest.mark.asyncio
    async def test_post_empty_transactions_returns_400(self, client):
        """Empty transaction list returns 400 Bad Request."""
        response = await client.post(
            "/api/batch/transaction-posting",
            json={"transactions": []},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_post_expired_account_reason_103(
        self, client, expired_account, sample_xref_expired
    ):
        """Expired account rejects with reason 103."""
        response = await client.post(
            "/api/batch/transaction-posting",
            json={
                "transactions": [{
                    "tran_id": "TXN0000000000001",
                    "tran_type_cd": "01",
                    "tran_cat_cd": "0001",
                    "tran_source": "POS",
                    "tran_desc": "Test",
                    "tran_amt": "-50.00",
                    "tran_card_num": "4444444444444444",
                    "tran_orig_ts": "2026-04-01T12:00:00Z",
                }]
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["rejects"][0]["reason_code"] == "103"


class TestTransactionReportEndpoint:
    """Tests for POST /api/batch/transaction-report (CBTRN03C)."""

    @pytest.mark.asyncio
    async def test_report_with_no_transactions_returns_empty(
        self, client
    ):
        """Date range with no transactions returns empty report."""
        response = await client.post(
            "/api/batch/transaction-report",
            json={
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["totals"]["transaction_count"] == 0
        assert body["totals"]["grand_total"] == "0"

    @pytest.mark.asyncio
    async def test_report_invalid_date_range_returns_400(self, client):
        """start_date > end_date returns 400."""
        response = await client.post(
            "/api/batch/transaction-report",
            json={
                "start_date": "2026-12-31",
                "end_date": "2026-01-01",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_report_includes_formatted_text(
        self, client, sample_account, sample_xref, sample_transaction_types, sample_transaction_categories, db_session
    ):
        """Report includes 133-char-wide formatted text."""
        from app.models.transaction import Transaction
        # Insert a transaction in range
        tran = Transaction(
            tran_id="TXN0000000000001",
            tran_type_cd="01",
            tran_cat_cd="0001",
            tran_source="POS",
            tran_desc="Test",
            tran_amt=-50.00,
            tran_card_num="4111111111111111",
            tran_orig_ts=datetime(2026, 4, 1, tzinfo=timezone.utc),
            tran_proc_ts=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        db_session.add(tran)
        await db_session.commit()

        response = await client.post(
            "/api/batch/transaction-report",
            json={
                "start_date": "2026-04-01",
                "end_date": "2026-04-03",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["totals"]["transaction_count"] == 1
        assert "Daily Transaction Report" in body["report_text"]
        assert "Grand Total" in body["report_text"]


class TestInterestCalculationEndpoint:
    """Tests for POST /api/batch/interest-calculation (CBACT04C)."""

    @pytest.mark.asyncio
    async def test_interest_calculation_with_no_balances(self, client):
        """No category balances produces no interest transactions."""
        response = await client.post(
            "/api/batch/interest-calculation",
            json={"run_date": "2026-04-03"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["accounts_processed"] == 0
        assert body["interest_transactions_created"] == 0

    @pytest.mark.asyncio
    async def test_interest_calculation_creates_transactions(
        self,
        client,
        sample_account,
        sample_xref,
        sample_tcatbal,
        sample_disclosure_groups,
    ):
        """Interest calculation creates transactions and updates accounts."""
        response = await client.post(
            "/api/batch/interest-calculation",
            json={"run_date": "2026-04-03"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["accounts_processed"] == 1
        assert body["interest_transactions_created"] >= 1
        assert body["account_summaries"][0]["acct_id"] == "00000000001"


class TestExportEndpoint:
    """Tests for GET /api/batch/export (CBEXPORT)."""

    @pytest.mark.asyncio
    async def test_export_returns_200(self, client):
        """Export endpoint returns 200 even with no data."""
        response = await client.get("/api/batch/export")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_returns_all_entity_counts(
        self, client, sample_account, sample_xref, db_session
    ):
        """Export response includes correct entity counts."""
        from app.models.customer import Customer
        cust = Customer(cust_id="000000001", cust_first_name="Test", cust_last_name="User")
        db_session.add(cust)
        await db_session.commit()

        response = await client.get("/api/batch/export")
        assert response.status_code == 200
        body = response.json()
        assert body["accounts_exported"] == 1
        assert body["xrefs_exported"] == 1
        assert body["customers_exported"] == 1
        assert body["payload"]["branch_id"] == "0001"
        assert body["payload"]["region_code"] == "NORTH"


class TestImportEndpoint:
    """Tests for POST /api/batch/import (CBIMPORT)."""

    @pytest.mark.asyncio
    async def test_import_returns_200(self, client):
        """Import endpoint returns 200 with minimal payload."""
        response = await client.post(
            "/api/batch/import",
            json={
                "payload": {
                    "export_timestamp": "2026-04-03 12:00:00.00",
                    "branch_id": "0001",
                    "region_code": "NORTH",
                    "customers": [],
                    "accounts": [],
                    "xrefs": [],
                    "transactions": [],
                    "cards": [],
                    "total_records": 0,
                }
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"

    @pytest.mark.asyncio
    async def test_import_then_export_roundtrip(
        self, client, db_session
    ):
        """Import data and verify it can be exported back."""
        # First import
        import_response = await client.post(
            "/api/batch/import",
            json={
                "payload": {
                    "export_timestamp": "2026-04-03 12:00:00.00",
                    "branch_id": "0001",
                    "region_code": "NORTH",
                    "customers": [{
                        "cust_id": "000000099",
                        "cust_first_name": "RoundTrip",
                        "cust_middle_name": None,
                        "cust_last_name": "Test",
                        "cust_addr_line_1": "999 Import St",
                        "cust_addr_line_2": None,
                        "cust_addr_line_3": None,
                        "cust_addr_state_cd": "CA",
                        "cust_addr_country_cd": "USA",
                        "cust_addr_zip": "90210",
                        "cust_phone_num_1": None,
                        "cust_phone_num_2": None,
                        "cust_ssn": None,
                        "cust_govt_issued_id": None,
                        "cust_dob": None,
                        "cust_eft_account_id": None,
                        "cust_pri_card_holder_ind": "Y",
                        "cust_fico_credit_score": 700,
                    }],
                    "accounts": [],
                    "xrefs": [],
                    "transactions": [],
                    "cards": [],
                    "total_records": 1,
                }
            },
        )
        assert import_response.status_code == 200

        # Now export and verify customer is there
        export_response = await client.get("/api/batch/export")
        assert export_response.status_code == 200
        body = export_response.json()
        customer_ids = [c["cust_id"] for c in body["payload"]["customers"]]
        assert "000000099" in customer_ids


class TestJobStatusEndpoint:
    """Tests for GET /api/batch/jobs/{job_id}."""

    @pytest.mark.asyncio
    async def test_get_job_status_returns_200(self, client, db_session):
        """Can retrieve job status after running a batch operation."""
        # Run an operation to create a job
        resp = await client.post(
            "/api/batch/interest-calculation",
            json={"run_date": "2026-04-03"},
        )
        job_id = resp.json()["job_id"]

        status_resp = await client.get(f"/api/batch/jobs/{job_id}")
        assert status_resp.status_code == 200
        body = status_resp.json()
        assert body["job_id"] == job_id
        assert body["status"] == "completed"
        assert body["job_type"] == "interest_calculation"

    @pytest.mark.asyncio
    async def test_get_nonexistent_job_returns_404(self, client):
        """Non-existent job ID returns 404."""
        response = await client.get("/api/batch/jobs/99999")
        assert response.status_code == 404


class TestHealthEndpoint:
    """Tests for GET /health."""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client):
        """Health check returns 200 with healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
