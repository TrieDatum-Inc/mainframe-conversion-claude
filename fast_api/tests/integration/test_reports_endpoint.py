"""
Integration tests for POST /api/v1/reports/transactions (CORPT00C / CR00).

Tests verify HTTP-level behavior including:
  1. 202 Accepted for valid monthly/yearly/custom requests
  2. 403 Forbidden for non-admin users (CDEMO-USRTYP-ADMIN required)
  3. 401 Unauthorized for unauthenticated requests
  4. 422 for invalid/missing custom dates
  5. Response body matches ReportJob schema
  6. GET /api/v1/reports/transactions/{job_id} returns job status
"""
import pytest
from httpx import AsyncClient

from app.models.account import Account
from app.models.card import Card
from app.models.user import User
from app.services.report_service import _JOB_STORE


@pytest.fixture(autouse=True)
def clear_job_store() -> None:
    """Clear job store before each test to avoid cross-test pollution."""
    _JOB_STORE.clear()
    yield
    _JOB_STORE.clear()


class TestReportsEndpoint:
    """Integration tests for CORPT00C report submission API."""

    @pytest.mark.asyncio
    async def test_submit_monthly_report_returns_202(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        CORPT00C: WHEN MONTHLYI OF CORPT0AI NOT = SPACES → submit monthly report.
        Admin user submitting monthly report gets 202 Accepted.
        """
        response = await client.post(
            "/api/v1/reports/transactions",
            json={"report_type": "monthly"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_submit_yearly_report_returns_202(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        CORPT00C: WHEN YEARLYI OF CORPT0AI NOT = SPACES → submit yearly report.
        """
        response = await client.post(
            "/api/v1/reports/transactions",
            json={"report_type": "yearly"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_submit_custom_report_with_dates_returns_202(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        CORPT00C: WHEN CUSTOMI OF CORPT0AI NOT = SPACES → submit with explicit dates.
        """
        response = await client.post(
            "/api/v1/reports/transactions",
            json={
                "report_type": "custom",
                "start_date": "2022-01-01",
                "end_date": "2022-03-31",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_submit_report_response_has_job_id(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        CORPT00C: //TRNRPT00 JOB — response must include a job_id.
        """
        response = await client.post(
            "/api/v1/reports/transactions",
            json={"report_type": "monthly"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert "job_id" in data
        assert data["job_id"].startswith("TRNRPT00-")

    @pytest.mark.asyncio
    async def test_submit_report_response_status_pending(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        CORPT00C: job written to TDQ means it's queued, not yet processed.
        Initial status must be 'pending'.
        """
        response = await client.post(
            "/api/v1/reports/transactions",
            json={"report_type": "yearly"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_non_admin_user_forbidden(
        self, client: AsyncClient, user_token: str
    ) -> None:
        """
        COADM01C dispatches to CORPT00C for admin users only.
        Non-admin must receive 403 Forbidden.
        """
        response = await client.post(
            "/api/v1/reports/transactions",
            json={"report_type": "monthly"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_request_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Unauthenticated request (no JWT) → 401."""
        response = await client.post(
            "/api/v1/reports/transactions",
            json={"report_type": "monthly"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_custom_report_missing_start_date_returns_422(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        CORPT00C: SDTMMI OF CORPT0AI = SPACES → 'Start Date - Month can NOT be empty...'
        """
        response = await client.post(
            "/api/v1/reports/transactions",
            json={"report_type": "custom", "end_date": "2022-03-31"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_custom_report_start_after_end_returns_422(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """start_date > end_date is invalid (logical ordering violation)."""
        response = await client.post(
            "/api/v1/reports/transactions",
            json={
                "report_type": "custom",
                "start_date": "2022-12-31",
                "end_date": "2022-01-01",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_report_job_by_id(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """
        GET /api/v1/reports/transactions/{job_id} returns the submitted job.
        No COBOL equivalent — REST observability endpoint.
        """
        submit_response = await client.post(
            "/api/v1/reports/transactions",
            json={"report_type": "monthly"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        job_id = submit_response.json()["job_id"]

        get_response = await client.get(
            f"/api/v1/reports/transactions/{job_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["job_id"] == job_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_job_returns_404(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """Unknown job_id → 404 Not Found."""
        response = await client.get(
            "/api/v1/reports/transactions/NONEXISTENT-JOB",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_monthly_report_includes_date_range(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        """Response must include computed start_date and end_date."""
        from datetime import date

        response = await client.post(
            "/api/v1/reports/transactions",
            json={"report_type": "monthly"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        data = response.json()
        assert "start_date" in data
        assert "end_date" in data
        # start must be day 1
        start = date.fromisoformat(data["start_date"])
        assert start.day == 1
