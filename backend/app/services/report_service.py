"""
Business logic service for report requests.

COBOL origin: CORPT00C — Transaction Report Request program (Transaction: CR00).

Key CORPT00C behaviors replicated:
  1. CONFIRMI='Y' required (schema-level Literal['Y'] — already enforced)
  2. Date range validation (schema-level @model_validator)
  3. CALCULATE-END-DATE: if end date blank → last day of prior month
  4. WIRTE-JOBSUB-TDQ (misspelled in source) → INSERT to report_requests + BackgroundTask
  5. INITIALIZE-ALL-FIELDS after submission (field reset — UI concern, not service)

CORPT00C date default rule (CALCULATE-END-DATE paragraph):
  FUNCTION DATE-OF-INTEGER(FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1)
  This computes: integer of today → subtract 1 day → convert back to date
  When today is the 1st of a month, subtracting 1 day gives the last day of the prior month.
  The rule is: "last day of prior month" regardless of when in the month it is.
  Modern Python equivalent: first day of current month - timedelta(1).
"""

from calendar import monthrange
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import ReportRequestNotFoundError, ValidationError
from app.models.report_request import ReportRequest
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportRequestCreate, ReportRequestResponse, ReportStatusResponse


class ReportService:
    """
    Service handling CORPT00C report request business logic.

    The report submission is fire-and-forget (like TDQ WRITEQ) — the service
    creates the request record and returns immediately. Background processing
    is triggered by the API endpoint via FastAPI BackgroundTasks.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.repo = ReportRepository(db)
        self.db = db

    async def request_report(
        self, request: ReportRequestCreate, requested_by: str
    ) -> ReportRequestResponse:
        """
        Submit a report request.

        COBOL origin: CORPT00C PROCESS-ENTER-KEY:
          1. Validate CONFIRMI (schema-level)
          2. Validate date formats (schema-level)
          3. CALCULATE-END-DATE if end date blank
          4. WIRTE-JOBSUB-TDQ → INSERT report_request with status='PENDING'
          5. Display confirmation message ("Report submitted successfully")
          6. INITIALIZE-ALL-FIELDS (field reset — UI concern)

        The 'confirm' field is validated at schema level (Literal['Y']).
        Date range validation is at schema level (@model_validator).
        This method handles remaining CORPT00C logic: date defaults and persistence.
        """
        start_date, end_date = self._resolve_date_range(request)

        report_request = ReportRequest(
            report_type=request.report_type,
            start_date=start_date,
            end_date=end_date,
            requested_by=requested_by,
            status="PENDING",
        )

        created = await self.repo.create_request(report_request)

        return ReportRequestResponse(
            request_id=created.request_id,
            report_type=created.report_type,
            start_date=created.start_date,
            end_date=created.end_date,
            status=created.status,
            requested_at=created.requested_at,
            message=(
                f"Report request submitted successfully. Request ID: {created.request_id}. "
                f"Status will be updated as processing completes."
            ),
        )

    async def get_report_status(self, request_id: int) -> ReportStatusResponse:
        """
        Get the status of a report request.

        No COBOL equivalent — CORPT00C had no status feedback mechanism after
        TDQ submission. This is a new capability added in the modern system.
        """
        report = await self.repo.get_by_id(request_id)
        if not report:
            raise ReportRequestNotFoundError(request_id)

        return ReportStatusResponse(
            request_id=report.request_id,
            report_type=report.report_type,
            start_date=report.start_date,
            end_date=report.end_date,
            requested_by=report.requested_by,
            status=report.status,
            result_path=report.result_path,
            error_message=report.error_message,
            requested_at=report.requested_at,
            completed_at=report.completed_at,
        )

    def _resolve_date_range(
        self, request: ReportRequestCreate
    ) -> tuple[date | None, date | None]:
        """
        Resolve effective start and end dates based on report type.

        COBOL origin: CORPT00C PROCESS-ENTER-KEY + CALCULATE-END-DATE:

        For 'M' (Monthly): derive from current month
        For 'Y' (Yearly): derive from current year
        For 'C' (Custom):
          - If end_date blank: CALCULATE-END-DATE → last day of prior month
            (CORPT00C: FUNCTION DATE-OF-INTEGER(FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1))
          - If start_date blank: no lower bound (CORPT00C allowed this)
        """
        today = date.today()

        if request.report_type == "M":
            return self._get_monthly_range(today)
        elif request.report_type == "Y":
            return self._get_yearly_range(today)
        else:
            return self._get_custom_range(request, today)

    def _get_monthly_range(self, today: date) -> tuple[date, date]:
        """
        Get start/end for monthly report (current month).

        CORPT00C MONTHLYI: implied current month range.
        """
        start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        end = today.replace(day=last_day)
        return start, end

    def _get_yearly_range(self, today: date) -> tuple[date, date]:
        """
        Get start/end for yearly report (current year).

        CORPT00C YEARLYI: implied current year range.
        """
        start = date(today.year, 1, 1)
        end = date(today.year, 12, 31)
        return start, end

    def _get_custom_range(
        self, request: ReportRequestCreate, today: date
    ) -> tuple[date | None, date | None]:
        """
        Get start/end for custom date range report.

        CORPT00C CALCULATE-END-DATE paragraph:
          If EDTMMI/EDTDDI/EDTYYYY1I all blank:
            WS-END-DATE = FUNCTION DATE-OF-INTEGER(
                            FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1)
          This is equivalent to: first day of current month - 1 day = last day of prior month.

        CORPT00C allowed blank start date (no lower bound on batch job).
        """
        end_date = request.end_date
        if end_date is None:
            # CORPT00C CALCULATE-END-DATE: last day of prior month
            end_date = self._calculate_last_day_prior_month(today)

        return request.start_date, end_date

    def _calculate_last_day_prior_month(self, today: date) -> date:
        """
        Calculate last day of prior month.

        COBOL origin: CORPT00C CALCULATE-END-DATE paragraph:
          FUNCTION DATE-OF-INTEGER(FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1)
          This gives: first day of current month - 1 day = last day of prior month.

        Python equivalent: first of current month minus 1 day.
        """
        first_of_current_month = today.replace(day=1)
        last_day_prior_month = first_of_current_month - timedelta(days=1)
        return last_day_prior_month
