"""
Unit tests for app/services/report_service.py

COBOL origin mapping:
  test_request_report_*     → CORPT00C PROCESS-ENTER-KEY + WIRTE-JOBSUB-TDQ
  test_calculate_end_date_* → CORPT00C CALCULATE-END-DATE paragraph
  test_resolve_date_range_* → CORPT00C date assembly + defaults

Critical assertions:
  - CORPT00C: blank end date → last day of prior month (CALCULATE-END-DATE)
  - CORPT00C: monthly/yearly dates auto-derived
  - CORPT00C: custom report requires dates
  - CORPT00C: confirm='Y' required (Pydantic schema-level)
  - Report created with status='PENDING' (replaces TDQ WRITEQ)
"""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.exceptions.errors import ReportRequestNotFoundError
from app.schemas.report import ReportRequestCreate
from app.services.report_service import ReportService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def service(mock_db):
    return ReportService(mock_db)


def make_report_request(**kwargs):
    """Build a valid ReportRequestCreate."""
    defaults = {
        "report_type": "M",
        "confirm": "Y",
    }
    defaults.update(kwargs)
    return ReportRequestCreate(**defaults)


# =============================================================================
# request_report tests — CORPT00C PROCESS-ENTER-KEY + WIRTE-JOBSUB-TDQ
# =============================================================================


class TestRequestReport:
    async def test_creates_monthly_report_request(self, service):
        """CORPT00C MONTHLYI: creates PENDING request with current month range."""
        today = date.today()
        mock_report = MagicMock()
        mock_report.request_id = 1
        mock_report.report_type = "M"
        mock_report.start_date = today.replace(day=1)
        mock_report.end_date = today
        mock_report.status = "PENDING"
        mock_report.requested_at = MagicMock()

        service.repo = AsyncMock()
        service.repo.create_request.return_value = mock_report

        result = await service.request_report(
            make_report_request(report_type="M"), requested_by="USER0001"
        )

        assert result.request_id == 1
        assert result.status == "PENDING"
        assert "submitted" in result.message.lower()

    async def test_creates_yearly_report_request(self, service):
        """CORPT00C YEARLYI: creates PENDING request with current year range."""
        today = date.today()
        mock_report = MagicMock()
        mock_report.request_id = 2
        mock_report.report_type = "Y"
        mock_report.start_date = date(today.year, 1, 1)
        mock_report.end_date = date(today.year, 12, 31)
        mock_report.status = "PENDING"
        mock_report.requested_at = MagicMock()

        service.repo = AsyncMock()
        service.repo.create_request.return_value = mock_report

        result = await service.request_report(
            make_report_request(report_type="Y"), requested_by="USER0001"
        )

        assert result.status == "PENDING"

    async def test_creates_custom_report_with_dates(self, service):
        """CORPT00C CUSTOMI: custom report with explicit date range."""
        mock_report = MagicMock()
        mock_report.request_id = 3
        mock_report.report_type = "C"
        mock_report.start_date = date(2026, 1, 1)
        mock_report.end_date = date(2026, 3, 31)
        mock_report.status = "PENDING"
        mock_report.requested_at = MagicMock()

        service.repo = AsyncMock()
        service.repo.create_request.return_value = mock_report

        result = await service.request_report(
            make_report_request(
                report_type="C",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31),
            ),
            requested_by="USER0001",
        )

        service.repo.create_request.assert_called_once()
        created = service.repo.create_request.call_args.args[0]
        assert created.start_date == date(2026, 1, 1)
        assert created.end_date == date(2026, 3, 31)

    async def test_confirm_required_at_schema_level(self):
        """CORPT00C: CONFIRMI must be 'Y' — schema-level Literal['Y']."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            ReportRequestCreate(
                report_type="M",
                confirm="N",  # invalid
            )

    async def test_custom_report_requires_end_date_gte_start(self):
        """CORPT00C: end_date >= start_date (safety check — original CORPT00C didn't validate this)."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            ReportRequestCreate(
                report_type="C",
                start_date=date(2026, 4, 1),
                end_date=date(2026, 3, 1),  # before start
                confirm="Y",
            )

    async def test_requested_by_stored_in_record(self, service):
        """CORPT00C: report request associated with signed-on user."""
        mock_report = MagicMock()
        mock_report.request_id = 5
        mock_report.report_type = "M"
        mock_report.start_date = date(2026, 4, 1)
        mock_report.end_date = date(2026, 4, 30)
        mock_report.status = "PENDING"
        mock_report.requested_at = MagicMock()

        service.repo = AsyncMock()
        service.repo.create_request.return_value = mock_report

        await service.request_report(
            make_report_request(report_type="M"), requested_by="USER0042"
        )

        created = service.repo.create_request.call_args.args[0]
        assert created.requested_by == "USER0042"


# =============================================================================
# CALCULATE-END-DATE tests — CORPT00C CALCULATE-END-DATE paragraph
# =============================================================================


class TestCalculateEndDate:
    def test_last_day_prior_month_from_first(self, service):
        """
        CORPT00C CALCULATE-END-DATE:
        FUNCTION DATE-OF-INTEGER(FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1)
        When today = 2026-04-01: prior month end = 2026-03-31.
        """
        today = date(2026, 4, 1)
        result = service._calculate_last_day_prior_month(today)
        assert result == date(2026, 3, 31)

    def test_last_day_prior_month_from_mid_month(self, service):
        """
        CORPT00C CALCULATE-END-DATE: first of current month - 1 day.
        When today = 2026-04-15: prior month end = 2026-03-31.
        """
        today = date(2026, 4, 15)
        result = service._calculate_last_day_prior_month(today)
        assert result == date(2026, 3, 31)

    def test_last_day_prior_month_handles_january(self, service):
        """
        CORPT00C CALCULATE-END-DATE: January → prior year December 31.
        When today = 2026-01-10: prior month end = 2025-12-31.
        """
        today = date(2026, 1, 10)
        result = service._calculate_last_day_prior_month(today)
        assert result == date(2025, 12, 31)

    def test_last_day_prior_month_handles_march(self, service):
        """
        CORPT00C: March → February last day (leap year aware).
        2024 is leap year: Feb 29.
        """
        today = date(2024, 3, 15)
        result = service._calculate_last_day_prior_month(today)
        assert result == date(2024, 2, 29)  # 2024 is leap year

    def test_last_day_prior_month_handles_non_leap_march(self, service):
        """2026 is not leap year: Feb 28."""
        today = date(2026, 3, 15)
        result = service._calculate_last_day_prior_month(today)
        assert result == date(2026, 2, 28)


# =============================================================================
# _resolve_date_range tests — CORPT00C date assembly
# =============================================================================


class TestResolveDateRange:
    def test_monthly_derives_current_month(self, service):
        """CORPT00C MONTHLYI: start = first of month, end = last of month."""
        request = make_report_request(report_type="M")
        today = date.today()
        start, end = service._resolve_date_range(request)

        assert start == today.replace(day=1)
        assert end is not None
        assert end.month == today.month

    def test_yearly_derives_current_year(self, service):
        """CORPT00C YEARLYI: start = Jan 1, end = Dec 31 of current year."""
        request = make_report_request(report_type="Y")
        today = date.today()
        start, end = service._resolve_date_range(request)

        assert start == date(today.year, 1, 1)
        assert end == date(today.year, 12, 31)

    def test_custom_uses_provided_dates(self, service):
        """CORPT00C CUSTOMI: explicit dates used as-is."""
        request = make_report_request(
            report_type="C",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
        )
        start, end = service._resolve_date_range(request)

        assert start == date(2026, 2, 1)
        assert end == date(2026, 2, 28)

    def test_custom_with_blank_end_defaults_to_prior_month(self, service):
        """
        CORPT00C CALCULATE-END-DATE: if EDTMMI/EDTDDI/EDTYYYY1I all blank,
        end = last day of prior month.
        """
        request = make_report_request(
            report_type="C",
            start_date=date(2026, 1, 1),
            end_date=None,  # blank
        )
        start, end = service._resolve_date_range(request)

        assert start == date(2026, 1, 1)
        assert end is not None
        # end should be last day of prior month from today
        today = date.today()
        expected_end = service._calculate_last_day_prior_month(today)
        assert end == expected_end


# =============================================================================
# get_report_status tests
# =============================================================================


class TestGetReportStatus:
    async def test_returns_status(self, service):
        """No COBOL equivalent — new status polling capability."""
        mock_report = MagicMock()
        mock_report.request_id = 1
        mock_report.report_type = "M"
        mock_report.start_date = date(2026, 3, 1)
        mock_report.end_date = date(2026, 3, 31)
        mock_report.requested_by = "USER0001"
        mock_report.status = "COMPLETED"
        mock_report.result_path = "/reports/2026-03.pdf"
        mock_report.error_message = None
        mock_report.requested_at = MagicMock()
        mock_report.completed_at = MagicMock()

        service.repo = AsyncMock()
        service.repo.get_by_id.return_value = mock_report

        result = await service.get_report_status(1)

        assert result.request_id == 1
        assert result.status == "COMPLETED"

    async def test_raises_not_found_for_missing_request(self, service):
        """No COBOL equivalent — new capability: 404 if request not found."""
        service.repo = AsyncMock()
        service.repo.get_by_id.return_value = None

        with pytest.raises(ReportRequestNotFoundError):
            await service.get_report_status(9999)
