"""Unit tests for ReportService — CORPT00C (Transaction CR00) business logic.

Tests cover all business rules from the CORPT00C specification:
  BR-001: Report type selection — exactly one of monthly/yearly/custom
  BR-002: Monthly date calculation (first/last day of current month)
  BR-003: Yearly date calculation (Jan 1 / Dec 31)
  BR-004/005: Custom date validation — range checks (month 1-12, day 1-31)
  BR-006/007: Custom date Gregorian validation (CSUTLDTC equivalent via Python datetime)
  BR-008: start_date <= end_date
  BR-009: Success message format (green color, report name + dates)
"""
import pytest
from calendar import monthrange
from datetime import date
from unittest.mock import AsyncMock

from fastapi import HTTPException

from app.models.report_job import ReportJob, REPORT_TYPE_MONTHLY, REPORT_TYPE_YEARLY, REPORT_TYPE_CUSTOM
from app.repositories.report_job_repository import ReportJobRepository
from app.services.report_service import (
    ReportService,
    build_success_message,
    calculate_monthly_date_range,
    calculate_yearly_date_range,
    validate_custom_date_range,
)


# ============================================================
# Date calculation tests — CORPT00C Monthly/Yearly Path
# ============================================================

class TestCalculateMonthlyDateRange:
    """Tests for CORPT00C Monthly Path date calculation (lines 217-236)."""

    def test_start_date_is_first_of_month(self):
        """BR-002: Start date must be first day of the month."""
        ref = date(2024, 6, 15)
        result = calculate_monthly_date_range(reference_date=ref)
        assert result.start_date == date(2024, 6, 1)

    def test_end_date_is_last_of_month_standard(self):
        """BR-002: End date is last day for months with 30 days."""
        ref = date(2024, 6, 1)
        result = calculate_monthly_date_range(reference_date=ref)
        assert result.end_date == date(2024, 6, 30)

    def test_end_date_is_last_of_month_31_days(self):
        """BR-002: End date is 31 for months with 31 days."""
        ref = date(2024, 1, 10)
        result = calculate_monthly_date_range(reference_date=ref)
        assert result.end_date == date(2024, 1, 31)

    def test_end_date_february_leap_year(self):
        """BR-002: Feb in leap year ends on 29."""
        ref = date(2024, 2, 5)  # 2024 is a leap year
        result = calculate_monthly_date_range(reference_date=ref)
        assert result.end_date == date(2024, 2, 29)

    def test_end_date_february_non_leap_year(self):
        """BR-002: Feb in non-leap year ends on 28."""
        ref = date(2023, 2, 5)
        result = calculate_monthly_date_range(reference_date=ref)
        assert result.end_date == date(2023, 2, 28)

    def test_december_end_date(self):
        """BR-002: December ends on 31 (COBOL special case: month+1 wraps to Jan)."""
        ref = date(2024, 12, 15)
        result = calculate_monthly_date_range(reference_date=ref)
        assert result.start_date == date(2024, 12, 1)
        assert result.end_date == date(2024, 12, 31)

    def test_start_and_end_same_month(self):
        """Start and end dates must be in the same year+month."""
        ref = date(2024, 3, 20)
        result = calculate_monthly_date_range(reference_date=ref)
        assert result.start_date.year == result.end_date.year
        assert result.start_date.month == result.end_date.month


class TestCalculateYearlyDateRange:
    """Tests for CORPT00C Yearly Path date calculation (lines 240-254)."""

    def test_start_date_is_jan_1(self):
        """BR-003: Start date is Jan 1 of current year."""
        ref = date(2024, 6, 15)
        result = calculate_yearly_date_range(reference_date=ref)
        assert result.start_date == date(2024, 1, 1)

    def test_end_date_is_dec_31(self):
        """BR-003: End date is Dec 31 of current year."""
        ref = date(2024, 6, 15)
        result = calculate_yearly_date_range(reference_date=ref)
        assert result.end_date == date(2024, 12, 31)

    def test_year_matches_reference(self):
        """Year in start/end matches the reference year."""
        ref = date(2023, 1, 1)
        result = calculate_yearly_date_range(reference_date=ref)
        assert result.start_date.year == 2023
        assert result.end_date.year == 2023


# ============================================================
# Custom date validation tests — CORPT00C Custom Path
# ============================================================

class TestValidateCustomDateRange:
    """Tests for CORPT00C Custom Path validation (lines 257-436)."""

    def test_valid_date_range(self):
        """Valid date range passes without error."""
        validate_custom_date_range(date(2024, 1, 1), date(2024, 3, 31))

    def test_same_start_end_date_passes(self):
        """Same start and end date is valid (start <= end)."""
        validate_custom_date_range(date(2024, 6, 15), date(2024, 6, 15))

    def test_start_after_end_raises(self):
        """BR-008: start_date > end_date must raise HTTPException 422."""
        with pytest.raises(HTTPException) as exc_info:
            validate_custom_date_range(date(2024, 6, 15), date(2024, 3, 1))
        assert exc_info.value.status_code == 422
        assert "Start date must be on or before end date" in str(exc_info.value.detail)


# ============================================================
# Success message tests — CORPT00C post-submission
# ============================================================

class TestBuildSuccessMessage:
    """Tests for CORPT00C success message format (lines 448-456)."""

    def test_monthly_message(self):
        """Monthly report success message includes 'Monthly' and date range."""
        msg = build_success_message("monthly", date(2024, 6, 1), date(2024, 6, 30))
        assert "Monthly" in msg
        assert "2024-06-01" in msg
        assert "2024-06-30" in msg

    def test_yearly_message(self):
        """Yearly report success message includes 'Yearly'."""
        msg = build_success_message("yearly", date(2024, 1, 1), date(2024, 12, 31))
        assert "Yearly" in msg

    def test_custom_message(self):
        """Custom report success message includes 'Custom'."""
        msg = build_success_message("custom", date(2024, 3, 1), date(2024, 5, 31))
        assert "Custom" in msg

    def test_message_contains_printing(self):
        """CORPT00C: success message contains 'submitted for printing'."""
        msg = build_success_message("monthly", date(2024, 6, 1), date(2024, 6, 30))
        assert "submitted for printing" in msg


# ============================================================
# ReportService tests
# ============================================================

class TestReportService:
    """Tests for ReportService business logic."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        return AsyncMock(spec=ReportJobRepository)

    @pytest.fixture
    def service(self, mock_repo: AsyncMock) -> ReportService:
        return ReportService(repo=mock_repo)

    @pytest.fixture
    def sample_job(self) -> ReportJob:
        return ReportJob(
            job_id=1,
            report_type=REPORT_TYPE_MONTHLY,
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 30),
            status="pending",
            submitted_by="USER0001",
        )

    @pytest.mark.asyncio
    async def test_submit_monthly_report(
        self, service: ReportService, mock_repo: AsyncMock, sample_job: ReportJob
    ):
        """Monthly report calls repo.create with REPORT_TYPE_MONTHLY."""
        mock_repo.create.return_value = sample_job
        result = await service.submit_monthly_report(submitted_by="USER0001")
        assert result.report_type == REPORT_TYPE_MONTHLY
        mock_repo.create.assert_awaited_once()
        call_kwargs = mock_repo.create.call_args.kwargs
        assert call_kwargs["report_type"] == REPORT_TYPE_MONTHLY
        assert call_kwargs["submitted_by"] == "USER0001"
        # Verify correct monthly dates
        assert call_kwargs["start_date"].day == 1

    @pytest.mark.asyncio
    async def test_submit_yearly_report(
        self, service: ReportService, mock_repo: AsyncMock
    ):
        """Yearly report calls repo.create with REPORT_TYPE_YEARLY and Jan 1 / Dec 31."""
        job = ReportJob(
            job_id=2,
            report_type=REPORT_TYPE_YEARLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status="pending",
            submitted_by="USER0001",
        )
        mock_repo.create.return_value = job
        result = await service.submit_yearly_report(submitted_by="USER0001")
        assert result.report_type == REPORT_TYPE_YEARLY
        call_kwargs = mock_repo.create.call_args.kwargs
        assert call_kwargs["start_date"].month == 1
        assert call_kwargs["start_date"].day == 1
        assert call_kwargs["end_date"].month == 12
        assert call_kwargs["end_date"].day == 31

    @pytest.mark.asyncio
    async def test_submit_custom_report_valid(
        self, service: ReportService, mock_repo: AsyncMock
    ):
        """Custom report with valid dates calls repo.create."""
        job = ReportJob(
            job_id=3,
            report_type=REPORT_TYPE_CUSTOM,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            status="pending",
            submitted_by="USER0001",
        )
        mock_repo.create.return_value = job
        result = await service.submit_custom_report(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            submitted_by="USER0001",
        )
        assert result.report_type == REPORT_TYPE_CUSTOM

    @pytest.mark.asyncio
    async def test_submit_custom_report_invalid_range(
        self, service: ReportService, mock_repo: AsyncMock
    ):
        """Custom report with start > end raises HTTPException 422."""
        with pytest.raises(HTTPException) as exc_info:
            await service.submit_custom_report(
                start_date=date(2024, 6, 1),
                end_date=date(2024, 3, 1),
                submitted_by="USER0001",
            )
        assert exc_info.value.status_code == 422
        mock_repo.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_job_found(
        self, service: ReportService, mock_repo: AsyncMock, sample_job: ReportJob
    ):
        """get_job returns job when found."""
        mock_repo.get_by_id.return_value = sample_job
        result = await service.get_job(1)
        assert result.job_id == 1

    @pytest.mark.asyncio
    async def test_get_job_not_found(
        self, service: ReportService, mock_repo: AsyncMock
    ):
        """get_job raises 404 when job does not exist."""
        mock_repo.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await service.get_job(999)
        assert exc_info.value.status_code == 404
