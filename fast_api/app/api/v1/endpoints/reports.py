"""
Report endpoints — derived from CORPT00C (CICS transaction CR00).

Source program: app/cbl/CORPT00C.cbl
BMS map: CORPT00 / CORPT0A

CICS transaction ID: CR00

Endpoint mapping:
  POST /api/v1/reports/transactions → CORPT00C PROCESS-ENTER-KEY
  GET  /api/v1/reports/transactions/{job_id} → (no COBOL equivalent, REST observability)

CORPT00C replaces:
  EXEC CICS WRITEQ TD QUEUE('JOBS') FROM(JCL-RECORD) → FastAPI BackgroundTasks

Business rules (CORPT00C SUBMIT-JOB-TO-INTRDR):
  1. Report type 'monthly' → first..last day of current month
  2. Report type 'yearly' → current year Jan 1 to Dec 31
  3. Report type 'custom' → explicit start/end dates (validated YYYY-MM-DD)
  4. User must confirm (CONFIRMI = 'Y') — enforced by request body confirm field
  5. Returns job_id immediately; processing continues in background

Admin-only:
  COADM01C dispatches to CORPT00C for admin users.
  CDEMO-USRTYP-ADMIN required — enforced via AdminUser dependency.
"""
from fastapi import APIRouter, BackgroundTasks

from app.dependencies import CurrentUser, DBSession
from app.schemas.report import ReportJob, ReportSubmitRequest
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports (CORPT00C/CR00)"])


@router.post(
    "/transactions",
    response_model=ReportJob,
    status_code=202,
    summary="Submit transaction report job (CORPT00C / CR00)",
    responses={
        202: {"description": "Report job accepted and queued for processing"},
        403: {"description": "Admin access required (CDEMO-USRTYP-ADMIN)"},
        422: {"description": "Validation error (e.g., invalid date range, missing custom dates)"},
    },
)
async def submit_transaction_report(
    request: ReportSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DBSession,
) -> ReportJob:
    """
    Submit a transaction report generation job.

    Derived from CORPT00C PROCESS-ENTER-KEY → SUBMIT-JOB-TO-INTRDR paragraph:

    COBOL:
      WHEN MONTHLYI OF CORPT0AI NOT = SPACES → compute month date range
      WHEN YEARLYI  OF CORPT0AI NOT = SPACES → compute year date range
      WHEN CUSTOMI  OF CORPT0AI NOT = SPACES → validate SDTMMI/DD/YYYY, EDTMMI/DD/YYYY
      IF CONFIRMI OF CORPT0AI = 'Y' OR 'y'  → PERFORM WIRTE-JOBSUB-TDQ
        EXEC CICS WRITEQ TD QUEUE('JOBS') FROM(JCL-RECORD)

    FastAPI equivalent:
      Validates dates → creates ReportJob → registers BackgroundTask.

    HTTP 202 mirrors the asynchronous nature of JCL submission:
    the response is returned before the report is generated.

    Request body example:
      {"report_type": "monthly"}
      {"report_type": "custom", "start_date": "2022-01-01", "end_date": "2022-03-31"}
    """
    service = ReportService()
    return service.submit_report(request, current_user.sub, background_tasks)


@router.get(
    "/transactions/{job_id}",
    response_model=ReportJob,
    summary="Get report job status",
    responses={
        200: {"description": "Report job details"},
        404: {"description": "Job not found"},
    },
)
async def get_report_job(
    job_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> ReportJob:
    """
    Retrieve the status of a submitted report job.

    No direct COBOL equivalent — CORPT00C had no way to query TDQ job status.
    Added for REST API observability (check if background report has completed).

    HTTP 404 if job_id does not exist.
    """
    from fastapi import HTTPException

    service = ReportService()
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Report job not found: {job_id!r}")
    return job
