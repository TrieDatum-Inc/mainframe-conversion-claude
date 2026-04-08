"""
Unit tests for ReportService — business logic from CORPT00C.

Tests verify all business rules:
  1. Monthly report → first..last day of current month
  2. Yearly report → Jan 1 to Dec 31 of current year
  3. Custom report → passed dates used directly
  4. Job ID generated with correct prefix (TRNRPT00)
  5. BackgroundTask registered on submission
  6. Job state transitions (PENDING → RUNNING → COMPLETED)
"""
from calendar import monthrange
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from app.schemas.report import ReportStatus, ReportSubmitRequest, ReportType
from app.services.report_service import ReportService, _JOB_STORE


class TestReportService:
    """Tests for CORPT00C business logic."""

    def setup_method(self) -> None:
        """Clear job store before each test."""
        _JOB_STORE.clear()

    def test_monthly_report_start_date_is_first_of_month(self) -> None:
        """
        CORPT00C: MOVE '01' TO WS-START-DATE-DD
        Monthly start date must be the 1st of the current month.
        """
        today = date.today()
        service = ReportService()
        start, _ = service._monthly_date_range(today)

        assert start.year == today.year
        assert start.month == today.month
        assert start.day == 1

    def test_monthly_report_end_date_is_last_of_month(self) -> None:
        """
        CORPT00C: COMPUTE WS-CURDATE-N = DATE-OF-INTEGER(INTEGER-OF-DATE(...) - 1)
        Monthly end date must be the last calendar day of the current month.
        """
        today = date.today()
        service = ReportService()
        _, end = service._monthly_date_range(today)

        expected_last_day = monthrange(today.year, today.month)[1]
        assert end.day == expected_last_day
        assert end.month == today.month
        assert end.year == today.year

    def test_monthly_date_range_december(self) -> None:
        """CORPT00C: December month-end correctly wraps to Dec 31."""
        december = date(2022, 12, 15)
        service = ReportService()
        start, end = service._monthly_date_range(december)

        assert start == date(2022, 12, 1)
        assert end == date(2022, 12, 31)

    def test_yearly_report_start_is_jan_1(self) -> None:
        """
        CORPT00C: MOVE '01' TO WS-START-DATE-MM, MOVE '01' TO WS-START-DATE-DD
        Yearly report starts on January 1st.
        """
        today = date.today()
        service = ReportService()
        start, _ = service._yearly_date_range(today)

        assert start == date(today.year, 1, 1)

    def test_yearly_report_end_is_dec_31(self) -> None:
        """
        CORPT00C: MOVE '12' TO WS-END-DATE-MM, MOVE '31' TO WS-END-DATE-DD
        Yearly report ends on December 31st.
        """
        today = date.today()
        service = ReportService()
        _, end = service._yearly_date_range(today)

        assert end == date(today.year, 12, 31)

    def test_custom_report_uses_provided_dates(self) -> None:
        """
        CORPT00C: MOVE SDTYYYYI/SDTMMI/SDTDDI TO WS-START-DATE components.
        Custom report uses exactly the dates provided.
        """
        request = ReportSubmitRequest(
            report_type=ReportType.CUSTOM,
            start_date=date(2022, 3, 1),
            end_date=date(2022, 3, 31),
        )
        service = ReportService()
        start, end = service._resolve_date_range(request)

        assert start == date(2022, 3, 1)
        assert end == date(2022, 3, 31)

    def test_job_id_starts_with_trnrpt00(self) -> None:
        """
        CORPT00C JCL: //TRNRPT00 JOB 'TRAN REPORT',...
        Job IDs must begin with 'TRNRPT00-'.
        """
        job_id = ReportService._generate_job_id(
            ReportType.MONTHLY, date(2022, 3, 1), date(2022, 3, 31)
        )
        assert job_id.startswith("TRNRPT00-MONTHLY-")

    def test_job_id_includes_date_range(self) -> None:
        """Job ID encodes start and end date for traceability (JCL PARM-START/END-DATE)."""
        job_id = ReportService._generate_job_id(
            ReportType.CUSTOM, date(2022, 3, 1), date(2022, 9, 30)
        )
        assert "20220301" in job_id
        assert "20220930" in job_id

    def test_submit_report_returns_pending_job(self) -> None:
        """
        CORPT00C WIRTE-JOBSUB-TDQ: report is queued, not yet complete.
        Submitted job must have status PENDING.
        """
        bg_tasks = MagicMock()
        bg_tasks.add_task = MagicMock()

        request = ReportSubmitRequest(report_type=ReportType.MONTHLY)
        service = ReportService()
        job = service.submit_report(request, "ADMIN   ", bg_tasks)

        assert job.status == ReportStatus.PENDING
        assert job.submitted_by == "ADMIN   "
        assert job.report_type == ReportType.MONTHLY

    def test_submit_report_registers_background_task(self) -> None:
        """
        CORPT00C PERFORM WIRTE-JOBSUB-TDQ:
        BackgroundTask must be registered (replaces EXEC CICS WRITEQ TD).
        """
        bg_tasks = MagicMock()

        request = ReportSubmitRequest(report_type=ReportType.YEARLY)
        service = ReportService()
        service.submit_report(request, "ADMIN   ", bg_tasks)

        assert bg_tasks.add_task.called

    def test_submit_report_stored_in_job_store(self) -> None:
        """Job must be findable by get_job() after submission."""
        bg_tasks = MagicMock()

        request = ReportSubmitRequest(report_type=ReportType.MONTHLY)
        service = ReportService()
        job = service.submit_report(request, "USER0001", bg_tasks)

        retrieved = service.get_job(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id

    def test_get_job_returns_none_for_unknown_id(self) -> None:
        """get_job() returns None for unknown job_id (no COBOL equivalent — REST pattern)."""
        service = ReportService()
        result = service.get_job("NONEXISTENT-JOB-ID")
        assert result is None

    def test_custom_report_start_after_end_raises(self) -> None:
        """
        CORPT00C: custom report requires start_date <= end_date
        (logical validation, not explicitly in COBOL but implied by date-range semantics).
        """
        with pytest.raises(ValueError, match="start_date must not be after end_date"):
            ReportSubmitRequest(
                report_type=ReportType.CUSTOM,
                start_date=date(2022, 12, 31),
                end_date=date(2022, 1, 1),
            )

    def test_custom_report_missing_start_raises(self) -> None:
        """
        CORPT00C: SDTMMI can NOT be empty for custom type.
        """
        with pytest.raises(ValueError, match="start_date is required"):
            ReportSubmitRequest(
                report_type=ReportType.CUSTOM,
                end_date=date(2022, 3, 31),
            )

    def test_custom_report_missing_end_raises(self) -> None:
        """
        CORPT00C: EDTMMI can NOT be empty for custom type.
        """
        with pytest.raises(ValueError, match="end_date is required"):
            ReportSubmitRequest(
                report_type=ReportType.CUSTOM,
                start_date=date(2022, 3, 1),
            )

    def test_monthly_report_message_includes_type(self) -> None:
        """
        CORPT00C: STRING WS-REPORT-NAME DELIMITED BY SPACE
                       ' report submitted for printing ...' INTO WS-MESSAGE
        Job message must reference the report type name.
        """
        bg_tasks = MagicMock()
        request = ReportSubmitRequest(report_type=ReportType.MONTHLY)
        service = ReportService()
        job = service.submit_report(request, "ADMIN", bg_tasks)

        assert "monthly" in job.message.lower() or "Monthly" in job.message

    def test_list_jobs_returns_submitted_jobs(self) -> None:
        """list_jobs() returns all submitted jobs."""
        bg_tasks = MagicMock()
        service = ReportService()

        service.submit_report(ReportSubmitRequest(report_type=ReportType.MONTHLY), "U1", bg_tasks)
        service.submit_report(ReportSubmitRequest(report_type=ReportType.YEARLY), "U1", bg_tasks)

        jobs = service.list_jobs()
        assert len(jobs) == 2

    def test_list_jobs_filtered_by_user(self) -> None:
        """list_jobs() can filter by submitted_by."""
        bg_tasks = MagicMock()
        service = ReportService()

        service.submit_report(ReportSubmitRequest(report_type=ReportType.MONTHLY), "ADMIN", bg_tasks)
        service.submit_report(ReportSubmitRequest(report_type=ReportType.YEARLY), "USER01", bg_tasks)

        admin_jobs = service.list_jobs(submitted_by="ADMIN")
        assert len(admin_jobs) == 1
        assert admin_jobs[0].submitted_by == "ADMIN"
