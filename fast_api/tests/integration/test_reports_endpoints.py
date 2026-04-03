"""Integration tests for report submission endpoints — CORPT00C (CR00) equivalent.

Uses httpx.AsyncClient with the FastAPI app directly.
DB calls are mocked via dependency overrides and repository patching.
"""
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.middleware.auth_middleware import get_current_user_info
from app.models.report_job import ReportJob
from app.repositories.report_job_repository import ReportJobRepository
from app.schemas.auth import UserInfo


def _make_valid_user() -> UserInfo:
    return UserInfo(
        user_id="USER0001",
        first_name="John",
        last_name="Doe",
        user_type="U",
    )


def _mock_auth_dependency():
    """Override get_current_user_info to return a test user (skip JWT validation)."""
    user = _make_valid_user()

    async def override():
        return user

    return override


def _make_report_job(
    job_id: int = 1,
    report_type: str = "monthly",
    start_date: date = date(2024, 6, 1),
    end_date: date = date(2024, 6, 30),
    status: str = "pending",
    submitted_by: str = "USER0001",
) -> ReportJob:
    return ReportJob(
        job_id=job_id,
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        status=status,
        submitted_by=submitted_by,
        submitted_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
async def client():
    """AsyncClient with auth dependency bypassed."""
    app.dependency_overrides[get_current_user_info] = _mock_auth_dependency()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()


# ============================================================
# POST /reports — Submit report
# ============================================================

class TestSubmitReportEndpoint:
    """Integration tests for POST /reports (CORPT00C SUBMIT-JOB-TO-INTRDR)."""

    async def test_monthly_report_returns_201(self, client: AsyncClient):
        """Monthly report submission returns 201 with job details."""
        job = _make_report_job(report_type="monthly")

        with patch.object(ReportJobRepository, "create", return_value=job):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.post(
                "/reports",
                json={"report_type": "monthly"},
            )
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 201
        data = response.json()
        assert data["report_type"] == "monthly"
        assert data["status"] == "pending"
        assert data["message_type"] == "success"
        assert "submitted for printing" in data["message"]

    async def test_yearly_report_returns_201(self, client: AsyncClient):
        """Yearly report submission returns 201."""
        job = _make_report_job(
            report_type="yearly",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

        with patch.object(ReportJobRepository, "create", return_value=job):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.post(
                "/reports",
                json={"report_type": "yearly"},
            )
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 201
        data = response.json()
        assert data["report_type"] == "yearly"

    async def test_custom_report_returns_201(self, client: AsyncClient):
        """Custom report with valid date range returns 201."""
        job = _make_report_job(
            report_type="custom",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )

        with patch.object(ReportJobRepository, "create", return_value=job):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.post(
                "/reports",
                json={
                    "report_type": "custom",
                    "start_date": "2024-01-01",
                    "end_date": "2024-03-31",
                },
            )
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 201
        data = response.json()
        assert data["report_type"] == "custom"

    async def test_custom_report_start_after_end_returns_422(self, client: AsyncClient):
        """BR-008: Custom report with start_date > end_date returns 422."""
        response = await client.post(
            "/reports",
            json={
                "report_type": "custom",
                "start_date": "2024-06-01",
                "end_date": "2024-03-01",
            },
        )
        assert response.status_code == 422

    async def test_custom_report_missing_start_date_returns_422(self, client: AsyncClient):
        """Custom report without start_date returns 422."""
        response = await client.post(
            "/reports",
            json={"report_type": "custom", "end_date": "2024-03-31"},
        )
        assert response.status_code == 422

    async def test_custom_report_missing_end_date_returns_422(self, client: AsyncClient):
        """Custom report without end_date returns 422."""
        response = await client.post(
            "/reports",
            json={"report_type": "custom", "start_date": "2024-01-01"},
        )
        assert response.status_code == 422

    async def test_custom_report_invalid_date_returns_422(self, client: AsyncClient):
        """BR-006/007: Invalid date (e.g., Feb 31) returns 422 (CSUTLDTC equivalent)."""
        response = await client.post(
            "/reports",
            json={
                "report_type": "custom",
                "start_date": "2024-02-31",  # invalid date
                "end_date": "2024-03-31",
            },
        )
        assert response.status_code == 422

    async def test_invalid_report_type_returns_422(self, client: AsyncClient):
        """Unknown report type returns 422."""
        response = await client.post(
            "/reports",
            json={"report_type": "quarterly"},
        )
        assert response.status_code == 422

    async def test_unauthenticated_returns_401(self):
        """Unauthenticated request returns 401."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            response = await c.post(
                "/reports",
                json={"report_type": "monthly"},
            )
        assert response.status_code == 401


# ============================================================
# GET /reports — List reports
# ============================================================

class TestListReportsEndpoint:
    """Integration tests for GET /reports."""

    async def test_list_reports_returns_200(self, client: AsyncClient):
        """List endpoint returns 200 with jobs array."""
        jobs = [
            _make_report_job(job_id=1, report_type="monthly"),
            _make_report_job(job_id=2, report_type="yearly"),
        ]

        with patch.object(ReportJobRepository, "list_recent", return_value=jobs):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.get("/reports")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert data["total"] == 2

    async def test_list_reports_empty(self, client: AsyncClient):
        """List endpoint returns empty array when no jobs."""
        with patch.object(ReportJobRepository, "list_recent", return_value=[]):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.get("/reports")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["jobs"] == []


# ============================================================
# GET /reports/{job_id} — Get single report
# ============================================================

class TestGetReportEndpoint:
    """Integration tests for GET /reports/{job_id}."""

    async def test_get_existing_job_returns_200(self, client: AsyncClient):
        """Returns 200 for existing job."""
        job = _make_report_job(job_id=42)

        with patch.object(ReportJobRepository, "get_by_id", return_value=job):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.get("/reports/42")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        assert response.json()["job_id"] == 42

    async def test_get_nonexistent_job_returns_404(self, client: AsyncClient):
        """Returns 404 for non-existent job."""
        with patch.object(ReportJobRepository, "get_by_id", return_value=None):
            app.dependency_overrides[get_db] = lambda: MagicMock()
            response = await client.get("/reports/999")
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 404
