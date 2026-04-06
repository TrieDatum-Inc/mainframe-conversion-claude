"""Tests for ReportService — CORPT00C business logic."""

from datetime import date

import pytest

from app.schemas.report import ReportRequest, ReportType
from app.services.report_service import ReportService


class TestResolveDateRange:
    """CORPT00C: monthly/yearly/custom date range derivation."""

    def test_monthly_range_first_last_day(self):
        service = ReportService(None)  # type: ignore[arg-type]
        request = ReportRequest(report_type=ReportType.MONTHLY, confirmed=True)
        # Monkey-patch _resolve_date_range with a known date
        today = date(2024, 3, 15)
        start, end = service._monthly_range(today)
        assert start == date(2024, 3, 1)
        assert end == date(2024, 3, 31)

    def test_monthly_range_february_non_leap(self):
        service = ReportService(None)  # type: ignore[arg-type]
        today = date(2023, 2, 10)
        start, end = service._monthly_range(today)
        assert start == date(2023, 2, 1)
        assert end == date(2023, 2, 28)

    def test_monthly_range_february_leap(self):
        service = ReportService(None)  # type: ignore[arg-type]
        today = date(2024, 2, 10)
        start, end = service._monthly_range(today)
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_yearly_range(self):
        service = ReportService(None)  # type: ignore[arg-type]
        today = date(2024, 6, 15)
        start, end = service._yearly_range(today)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 12, 31)

    def test_custom_range_uses_provided_dates(self):
        service = ReportService(None)  # type: ignore[arg-type]
        request = ReportRequest(
            report_type=ReportType.CUSTOM,
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 31),
            confirmed=True,
        )
        start, end = service._resolve_date_range(request)
        assert start == date(2024, 3, 1)
        assert end == date(2024, 3, 31)


class TestGenerateReport:
    """CORPT00C: report generation with real data."""

    async def test_empty_report(self, db_session):
        service = ReportService(db_session)
        request = ReportRequest(
            report_type=ReportType.CUSTOM,
            start_date=date(2099, 1, 1),
            end_date=date(2099, 12, 31),
            confirmed=True,
        )
        result = await service.generate_report(request)
        assert result.total_transactions == 0
        assert result.transactions == []

    async def test_report_with_transactions(self, db_session, multiple_transactions):
        service = ReportService(db_session)
        request = ReportRequest(
            report_type=ReportType.CUSTOM,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            confirmed=True,
        )
        result = await service.generate_report(request)
        assert result.total_transactions == 15
        assert result.report_type == ReportType.CUSTOM

    async def test_report_rows_have_required_fields(self, db_session, sample_transaction):
        service = ReportService(db_session)
        request = ReportRequest(
            report_type=ReportType.CUSTOM,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            confirmed=True,
        )
        result = await service.generate_report(request)
        assert result.total_transactions == 1
        row = result.transactions[0]
        assert row.transaction_id == "0000000000000001"
        assert row.card_number == "4000002000000000"
        assert row.merchant_name == "TEST MARKET"
