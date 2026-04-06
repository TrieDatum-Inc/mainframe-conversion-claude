"""
FastAPI endpoints for Report request operations.

COBOL origin: CORPT00C — Transaction Report Request (Transaction: CR00).

POST /api/v1/reports/request → replaces WIRTE-JOBSUB-TDQ (TDQ QUEUE='JOBS')
GET  /api/v1/reports/{report_id} → new capability (no COBOL equivalent)

Both endpoints require authentication. No admin restriction (CORPT00C accessible from COMEN01C).
"""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.report import ReportRequestCreate, ReportRequestResponse, ReportStatusResponse
from app.services.report_service import ReportService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "/request",
    response_model=ReportRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit report request (CORPT00C)",
    description=(
        "Submit a transaction report request. "
        "CORPT00C: WIRTE-JOBSUB-TDQ writes JCL to TDQ QUEUE='JOBS'. "
        "Modern: INSERT to report_requests + background task (same async pattern). "
        "confirm='Y' required. "
        "Custom reports require start_date and end_date. "
        "Monthly/yearly dates derived automatically. "
        "Blank end date defaults to last day of prior month (CORPT00C CALCULATE-END-DATE)."
    ),
)
async def submit_report_request(
    request: ReportRequestCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ReportRequestResponse:
    """
    Submit a report request.

    COBOL origin: CORPT00C PROCESS-ENTER-KEY + WIRTE-JOBSUB-TDQ.

    Processing (maps CORPT00C flow):
      1. Validate confirm='Y' (schema-level Literal['Y'])
      2. Validate dates for custom report (schema-level @model_validator)
      3. Apply CALCULATE-END-DATE default if end_date blank
      4. INSERT to report_requests with status='PENDING' (replaces WRITEQ TD)
      5. Register background task for async processing (replaces JES batch submission)
      6. Return 202 Accepted (fire-and-forget, same as TDQ submission)

    Returns 202 Accepted — processing happens asynchronously.
    Use GET /reports/{report_id} to check status.

    CORPT00C had no feedback mechanism after TDQ write —
    the user could not check if the batch job succeeded.
    This endpoint adds that capability via the status polling endpoint.
    """
    service = ReportService(db)
    response = await service.request_report(request, requested_by=current_user.get("sub", ""))

    # Register background task — replaces CORPT00C TDQ async job submission
    # The background worker processes the report asynchronously after response is sent
    background_tasks.add_task(
        _process_report_background,
        report_id=response.request_id,
    )

    return response


@router.get(
    "/{report_id}",
    response_model=ReportStatusResponse,
    summary="Get report status (new capability)",
    description=(
        "Check status of a submitted report request. "
        "No COBOL equivalent — CORPT00C had no feedback mechanism after TDQ submission. "
        "This is a new capability that gives users visibility into report processing."
    ),
)
async def get_report_status(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ReportStatusResponse:
    """
    Get the status of a report request.

    No COBOL equivalent. CORPT00C fired-and-forgot to TDQ QUEUE='JOBS'.
    Modern system provides status tracking: PENDING → RUNNING → COMPLETED/FAILED.
    """
    service = ReportService(db)
    return await service.get_report_status(report_id)


async def _process_report_background(report_id: int) -> None:
    """
    Background task for report processing.

    COBOL origin: Replaces the async TRANREPT batch job submitted via TDQ JOBS.
    The original job ran in JES completely independently. This background task
    runs in the same FastAPI process but after the HTTP response is sent.

    In production, this would be replaced by a proper task queue (Celery, etc.).
    For now, it simulates the async nature of the original TDQ submission.
    """
    # Background processing placeholder
    # In production: generate actual transaction report and update status
    # The report_id is used to update status in a separate DB session
    pass
