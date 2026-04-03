"""Report Submission service — business logic for CORPT00C (Transaction CR00).

All COBOL paragraph logic from PROCESS-ENTER-KEY and SUBMIT-JOB-TO-INTRDR
is preserved here as pure Python functions.

COBOL source: app/cbl/CORPT00C.cbl
BMS Mapset: CORPT00 / Map CORPT0A
"""
import logging
from calendar import monthrange
from datetime import date
from typing import NamedTuple

from fastapi import HTTPException, status

from app.models.report_job import (
    REPORT_TYPE_CUSTOM,
    REPORT_TYPE_MONTHLY,
    REPORT_TYPE_YEARLY,
    ReportJob,
)
from app.repositories.report_job_repository import ReportJobRepository

logger = logging.getLogger(__name__)


class DateRange(NamedTuple):
    """Start/end date pair — replaces PARM-START-DATE / PARM-END-DATE JCL params."""

    start_date: date
    end_date: date


def calculate_monthly_date_range(reference_date: date | None = None) -> DateRange:
    """Calculate date range for monthly report.

    CORPT00C Monthly Path (lines 217-236):
      Start date = first day of current month (YYYY-MM-01)
      End date = last day of current month

    COBOL technique:
      Move 01 to WS-START-DATE-DD
      Advance month by 1 (handle December → January of next year)
      Use DATE-OF-INTEGER(INTEGER-OF-DATE(...) - 1) to get last day of current month

    Python equivalent: use calendar.monthrange() to get the last day.
    """
    today = reference_date or date.today()
    start_date = today.replace(day=1)
    _, last_day = monthrange(today.year, today.month)
    end_date = today.replace(day=last_day)
    return DateRange(start_date=start_date, end_date=end_date)


def calculate_yearly_date_range(reference_date: date | None = None) -> DateRange:
    """Calculate date range for yearly report.

    CORPT00C Yearly Path (lines 240-254):
      Start date = YYYY-01-01 of current year
      End date = YYYY-12-31 of current year
    """
    today = reference_date or date.today()
    start_date = date(today.year, 1, 1)
    end_date = date(today.year, 12, 31)
    return DateRange(start_date=start_date, end_date=end_date)


def validate_custom_date_range(start_date: date, end_date: date) -> None:
    """Validate custom date range.

    CORPT00C Custom Path validation (lines 257-436):
      BR-006: start_date must be a valid Gregorian calendar date (CSUTLDTC equivalent)
      BR-007: end_date must be a valid Gregorian calendar date
      BR-008: start_date <= end_date

    Pydantic's date type already enforces calendar validity (Python datetime
    raises ValueError for invalid dates like Feb 31), so this function handles
    the range comparison rule that COBOL does not enforce but the spec implies.

    Note: COBOL CSUTLDTC severity '0000' = valid, non-'0000' with message
    number not '2513' = invalid. Python datetime validation is equivalent.
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Start date must be on or before end date",
        )


def build_success_message(report_type: str, start_date: date, end_date: date) -> str:
    """Build the success message shown after job submission.

    CORPT00C lines 448-456 (after successful SUBMIT-JOB-TO-INTRDR):
      WS-MESSAGE = '<ReportName> report submitted for printing ...'
    Color: DFHGREEN (green).
    """
    type_display = report_type.capitalize()
    return (
        f"{type_display} report submitted for printing "
        f"({start_date.isoformat()} to {end_date.isoformat()})"
    )


class ReportService:
    """Business logic for report submission (CORPT00C).

    CORPT00C transaction flow:
      1. Evaluate report type (MONTHLY / YEARLY / CUSTOM)
      2. Calculate or validate date range
      3. Check CONFIRM field = 'Y' (done in router/frontend before calling service)
      4. Submit job (write to TDQ JOBS → INSERT into report_jobs)
      5. Return success message with green color
    """

    def __init__(self, repo: ReportJobRepository) -> None:
        self._repo = repo

    async def submit_monthly_report(
        self, submitted_by: str | None
    ) -> ReportJob:
        """Submit a monthly transaction report.

        CORPT00C Monthly Path (lines 213-238).
        Confirmation check is handled by the router (user already confirmed).
        """
        date_range = calculate_monthly_date_range()
        return await self._repo.create(
            report_type=REPORT_TYPE_MONTHLY,
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            submitted_by=submitted_by,
        )

    async def submit_yearly_report(
        self, submitted_by: str | None
    ) -> ReportJob:
        """Submit a yearly transaction report.

        CORPT00C Yearly Path (lines 239-255).
        """
        date_range = calculate_yearly_date_range()
        return await self._repo.create(
            report_type=REPORT_TYPE_YEARLY,
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            submitted_by=submitted_by,
        )

    async def submit_custom_report(
        self,
        start_date: date,
        end_date: date,
        submitted_by: str | None,
    ) -> ReportJob:
        """Submit a custom date range report.

        CORPT00C Custom Path (lines 256-436).
        Date validation (calendar + range) must pass before writing job.
        """
        validate_custom_date_range(start_date, end_date)
        return await self._repo.create(
            report_type=REPORT_TYPE_CUSTOM,
            start_date=start_date,
            end_date=end_date,
            submitted_by=submitted_by,
        )

    async def list_jobs(self, limit: int = 20) -> list[ReportJob]:
        """List recent report jobs."""
        return await self._repo.list_recent(limit=limit)

    async def get_job(self, job_id: int) -> ReportJob:
        """Get a single report job by ID."""
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report job {job_id} not found",
            )
        return job
