"""Tests for report schemas — CORPT00C business rule validation."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.report import ReportRequest, ReportType


class TestReportRequest:
    """CORPT00C: custom mode requires both dates; end >= start."""

    def test_monthly_report_no_dates_required(self):
        req = ReportRequest(report_type=ReportType.MONTHLY, confirmed=True)
        assert req.report_type == ReportType.MONTHLY
        assert req.start_date is None

    def test_yearly_report_no_dates_required(self):
        req = ReportRequest(report_type=ReportType.YEARLY, confirmed=True)
        assert req.report_type == ReportType.YEARLY

    def test_custom_requires_both_dates(self):
        with pytest.raises(ValidationError) as exc_info:
            ReportRequest(report_type=ReportType.CUSTOM, confirmed=True)
        assert "start_date" in str(exc_info.value).lower() or "end_date" in str(exc_info.value).lower()

    def test_custom_with_only_start_date_rejected(self):
        with pytest.raises(ValidationError):
            ReportRequest(
                report_type=ReportType.CUSTOM,
                start_date=date(2024, 1, 1),
                confirmed=True,
            )

    def test_custom_valid_dates(self):
        req = ReportRequest(
            report_type=ReportType.CUSTOM,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            confirmed=True,
        )
        assert req.start_date == date(2024, 1, 1)
        assert req.end_date == date(2024, 1, 31)

    def test_custom_end_before_start_rejected(self):
        """CORPT00C: validate end date >= start date."""
        with pytest.raises(ValidationError) as exc_info:
            ReportRequest(
                report_type=ReportType.CUSTOM,
                start_date=date(2024, 2, 1),
                end_date=date(2024, 1, 1),
                confirmed=True,
            )
        assert "end_date" in str(exc_info.value).lower() or "greater" in str(exc_info.value).lower()

    def test_custom_same_start_end_valid(self):
        """Boundary: same day is valid (end >= start)."""
        req = ReportRequest(
            report_type=ReportType.CUSTOM,
            start_date=date(2024, 6, 15),
            end_date=date(2024, 6, 15),
            confirmed=True,
        )
        assert req.start_date == req.end_date

    def test_confirmed_defaults_false(self):
        req = ReportRequest(report_type=ReportType.MONTHLY)
        assert req.confirmed is False
