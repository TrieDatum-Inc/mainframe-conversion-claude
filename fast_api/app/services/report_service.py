"""
Report service — business logic from CORPT00C (CICS transaction CR00).

Source program: app/cbl/CORPT00C.cbl
Function: Submit batch transaction report jobs via async background tasks.

CORPT00C paragraph mapping:
  PROCESS-ENTER-KEY       → submit_report()
  SUBMIT-JOB-TO-INTRDR    → _build_jcl_params() + _dispatch_background_task()
  WIRTE-JOBSUB-TDQ        → background_generate_report() (replaces EXEC CICS WRITEQ TD)

Business rules preserved:
  1. Report type 'monthly' → auto-compute first..last day of current month
     (CORPT00C: ADD 1 TO WS-CURDATE-MONTH, DATE-OF-INTEGER - 1)
  2. Report type 'yearly' → auto-compute YYYY-01-01 to YYYY-12-31
     (CORPT00C: MOVE '01' TO WS-START-DATE-MM/DD, '12'/'31' TO WS-END-DATE-MM/DD)
  3. Report type 'custom' → validated start/end dates passed directly
     (CORPT00C: validate SDTMMI/DD/YYYY and EDTMMI/DD/YYYY via CALL 'CSUTLDTC')
  4. Confirmation required (CONFIRMI = 'Y' or 'y')
     — enforced at endpoint level via explicit confirm flag; service only runs on confirmed calls
  5. Submission produces an async job (replaces JCL written to TDQ 'JOBS')
  6. Job ID = unique string combining report type + date range + timestamp
     (equivalent to JOBNAME in JCL: '//TRNRPT00 JOB ...')
"""
import uuid
from calendar import monthrange
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from app.schemas.report import ReportJob, ReportStatus, ReportSubmitRequest, ReportType

if TYPE_CHECKING:
    from fastapi import BackgroundTasks


# ---------------------------------------------------------------------------
# In-memory job store (replace with DB table for production persistence)
# ---------------------------------------------------------------------------
# Equivalent to the TDQ 'JOBS' queue in CORPT00C — stores pending job metadata.
# In CORPT00C these are held in the JCL_RECORD stream written to the TD queue.
_JOB_STORE: dict[str, ReportJob] = {}


class ReportService:
    """
    Business logic for transaction report submission (CORPT00C).

    CORPT00C SUBMIT-JOB-TO-INTRDR writes JCL records to an extra-partition TDQ
    named 'JOBS', which triggers the TRANREPT batch procedure.  This service
    replaces that mechanism with FastAPI BackgroundTasks.
    """

    def submit_report(
        self,
        request: ReportSubmitRequest,
        submitted_by: str,
        background_tasks: "BackgroundTasks",
    ) -> ReportJob:
        """
        CORPT00C PROCESS-ENTER-KEY → SUBMIT-JOB-TO-INTRDR paragraph.

        Business rules:
          1. Compute effective start/end dates based on report_type
             ('monthly' → first/last of current month; 'yearly' → full year)
          2. Generate a unique job_id (equivalent to JOB card TRNRPT00 + timestamp)
          3. Register BackgroundTask to perform the actual report generation
             (replaces EXEC CICS WRITEQ TD QUEUE('JOBS') FROM(JCL-RECORD))
          4. Return ReportJob with PENDING status immediately

        Args:
            request:          Validated report submission request.
            submitted_by:     CDEMO-USER-ID of the submitting user.
            background_tasks: FastAPI BackgroundTasks injected by endpoint.

        Returns:
            ReportJob with job_id, dates, and status=PENDING.
        """
        start_date, end_date = self._resolve_date_range(request)
        job_id = self._generate_job_id(request.report_type, start_date, end_date)
        submitted_at = datetime.now(timezone.utc)

        job = ReportJob(
            job_id=job_id,
            report_type=request.report_type,
            start_date=start_date,
            end_date=end_date,
            status=ReportStatus.PENDING,
            submitted_at=submitted_at,
            submitted_by=submitted_by,
            message=(
                f"{request.report_type.value.capitalize()} report submitted for printing ..."
            ),
        )

        _JOB_STORE[job_id] = job

        # CORPT00C WIRTE-JOBSUB-TDQ → background_generate_report() async execution
        background_tasks.add_task(self._background_generate_report, job_id)

        return job

    def get_job(self, job_id: str) -> ReportJob | None:
        """
        Retrieve a previously submitted report job by ID.

        No direct COBOL equivalent — added for REST observability.
        CORPT00C had no way to query job status after TDQ write.

        Returns:
            ReportJob if found, None otherwise.
        """
        return _JOB_STORE.get(job_id)

    def list_jobs(self, submitted_by: str | None = None) -> list[ReportJob]:
        """
        List all submitted report jobs, optionally filtered by user.

        No direct COBOL equivalent (TDQ was write-only from CICS side).

        Args:
            submitted_by: Optional filter on submitting user ID.

        Returns:
            List of ReportJob entries.
        """
        jobs = list(_JOB_STORE.values())
        if submitted_by:
            jobs = [j for j in jobs if j.submitted_by == submitted_by]
        return sorted(jobs, key=lambda j: j.submitted_at, reverse=True)

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _resolve_date_range(self, request: ReportSubmitRequest) -> tuple[date, date]:
        """
        Compute effective start/end dates based on report_type.

        CORPT00C PROCESS-ENTER-KEY date computation logic:

        Monthly (WHEN MONTHLYI OF CORPT0AI NOT = SPACES):
          start = first day of current month (MOVE '01' TO WS-START-DATE-DD)
          end   = last day of current month  (DATE-OF-INTEGER(INTEGER-OF-DATE(next month day 1) - 1))

        Yearly (WHEN YEARLYI OF CORPT0AI NOT = SPACES):
          start = YYYY-01-01 (MOVE '01' TO WS-START-DATE-MM/DD)
          end   = YYYY-12-31 (MOVE '12'/'31' TO WS-END-DATE-MM/DD)

        Custom (WHEN CUSTOMI OF CORPT0AI NOT = SPACES):
          start = request.start_date (SDTYYYYI-SDTMMI-SDTDDI)
          end   = request.end_date   (EDTYYYYI-EDTMMI-EDTDDI)
        """
        today = date.today()

        if request.report_type == ReportType.MONTHLY:
            return self._monthly_date_range(today)
        if request.report_type == ReportType.YEARLY:
            return self._yearly_date_range(today)
        # CUSTOM — dates already validated by schema
        return request.start_date, request.end_date  # type: ignore[return-value]

    @staticmethod
    def _monthly_date_range(today: date) -> tuple[date, date]:
        """
        CORPT00C monthly date range computation.

        COBOL logic:
          MOVE WS-CURDATE-YEAR/MONTH TO WS-START-DATE-YYYY/MM
          MOVE '01' TO WS-START-DATE-DD
          ADD 1 TO WS-CURDATE-MONTH
          IF WS-CURDATE-MONTH > 12: ADD 1 TO WS-CURDATE-YEAR, MOVE 1 TO WS-CURDATE-MONTH
          COMPUTE WS-CURDATE-N = DATE-OF-INTEGER(INTEGER-OF-DATE(WS-CURDATE-N) - 1)
          → end date = last day of current month
        """
        year, month = today.year, today.month
        start = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end = date(year, month, last_day)
        return start, end

    @staticmethod
    def _yearly_date_range(today: date) -> tuple[date, date]:
        """
        CORPT00C yearly date range computation.

        COBOL logic:
          MOVE WS-CURDATE-YEAR TO WS-START-DATE-YYYY, WS-END-DATE-YYYY
          MOVE '01' TO WS-START-DATE-MM, WS-START-DATE-DD
          MOVE '12' TO WS-END-DATE-MM
          MOVE '31' TO WS-END-DATE-DD
        """
        return date(today.year, 1, 1), date(today.year, 12, 31)

    @staticmethod
    def _generate_job_id(
        report_type: ReportType, start_date: date, end_date: date
    ) -> str:
        """
        Generate a unique job identifier.

        Equivalent to JCL JOBNAME 'TRNRPT00' with a unique suffix.
        Format: TRNRPT00-{type}-{start}-{end}-{uuid4_short}

        CORPT00C JCL: //TRNRPT00 JOB 'TRAN REPORT',CLASS=A,...
        """
        suffix = str(uuid.uuid4())[:8].upper()
        return (
            f"TRNRPT00-{report_type.value.upper()}-"
            f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}-{suffix}"
        )

    @staticmethod
    async def _background_generate_report(job_id: str) -> None:
        """
        Background task that runs the report (replaces batch TRANREPT proc).

        CORPT00C WIRTE-JOBSUB-TDQ:
          EXEC CICS WRITEQ TD QUEUE('JOBS') FROM(JCL-RECORD)
          (writes up to 1000 lines of JCL to trigger PROC=TRANREPT)

        This function is the async equivalent — it runs the report generation
        logic that the batch JCL procedure (CBTRN02C/CBTRN03C) would perform.

        In production, replace this with actual report generation:
          - Query transactions between start_date and end_date
          - Aggregate by card/account as CBTRN02C/03C batch programs do
          - Write output report to storage (S3, file system, etc.)
        """
        job = _JOB_STORE.get(job_id)
        if not job:
            return

        # Transition to RUNNING
        _JOB_STORE[job_id] = job.model_copy(update={"status": ReportStatus.RUNNING})

        try:
            # Placeholder for actual report generation
            # In a real system, query transactions and build report here
            _JOB_STORE[job_id] = job.model_copy(update={"status": ReportStatus.COMPLETED})
        except Exception:
            _JOB_STORE[job_id] = job.model_copy(update={"status": ReportStatus.FAILED})
