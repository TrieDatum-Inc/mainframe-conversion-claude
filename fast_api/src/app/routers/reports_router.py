"""Reports router — REST API endpoints for CORPT00C (Transaction CR00).

Endpoints:
  POST /reports          — Submit a report job (monthly/yearly/custom)
  GET  /reports          — List recent report jobs
  GET  /reports/{job_id} — Get a specific report job

CORPT00C two-step confirmation flow mapping:
  Step 1 (screen display): Frontend renders the form with report type options
  Step 2 (CONFIRM=Y): Frontend shows confirmation dialog; on confirm calls POST /reports
  The CONFIRM check is enforced by requiring the user to explicitly submit the form.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.report_job_repository import ReportJobRepository
from app.middleware.auth_middleware import get_current_user_info
from app.schemas.auth import UserInfo
from app.schemas.reports import (
    ReportJobListResponse,
    ReportJobResponse,
    ReportSubmitRequest,
)
from app.services.report_service import ReportService, build_success_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports (CORPT00C / CR00)"])


def _get_report_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ReportService:
    """Dependency injection for ReportService."""
    return ReportService(repo=ReportJobRepository(db))


@router.post(
    "",
    response_model=ReportJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a report job (CORPT00C SUBMIT-JOB-TO-INTRDR equivalent)",
    description=(
        "Submits a transaction report job. "
        "Replaces the CORPT00C JCL write to TDQ JOBS queue. "
        "**CONFIRM=Y** is implied by the user submitting this request. "
        "\n\nReport types:\n"
        "- `monthly`: Auto-calculates current month range (first to last day)\n"
        "- `yearly`: Auto-calculates current year range (Jan 1 to Dec 31)\n"
        "- `custom`: User-supplied date range with full validation"
    ),
)
async def submit_report(
    request: ReportSubmitRequest,
    current_user: Annotated[UserInfo, Depends(get_current_user_info)],
    service: Annotated[ReportService, Depends(_get_report_service)],
) -> ReportJobResponse:
    """Submit a report job.

    CORPT00C PROCESS-ENTER-KEY dispatch:
      MONTHLY → submit_monthly_report()
      YEARLY  → submit_yearly_report()
      CUSTOM  → submit_custom_report() with date validation
    """
    submitted_by = current_user.user_id

    if request.report_type == "monthly":
        job = await service.submit_monthly_report(submitted_by=submitted_by)
    elif request.report_type == "yearly":
        job = await service.submit_yearly_report(submitted_by=submitted_by)
    else:
        # custom — start_date and end_date validated non-null by schema
        job = await service.submit_custom_report(
            start_date=request.start_date,  # type: ignore[arg-type]
            end_date=request.end_date,  # type: ignore[arg-type]
            submitted_by=submitted_by,
        )

    success_msg = build_success_message(
        report_type=job.report_type,
        start_date=job.start_date,
        end_date=job.end_date,
    )

    return ReportJobResponse(
        job_id=job.job_id,
        report_type=job.report_type,
        start_date=job.start_date,
        end_date=job.end_date,
        status=job.status,
        submitted_by=job.submitted_by,
        submitted_at=job.submitted_at,
        message=success_msg,
        message_type="success",
    )


@router.get(
    "",
    response_model=ReportJobListResponse,
    summary="List recent report jobs",
)
async def list_reports(
    current_user: Annotated[UserInfo, Depends(get_current_user_info)],
    service: Annotated[ReportService, Depends(_get_report_service)],
    limit: int = 20,
) -> ReportJobListResponse:
    """List recent report submissions."""
    jobs = await service.list_jobs(limit=limit)
    responses = [
        ReportJobResponse(
            job_id=j.job_id,
            report_type=j.report_type,
            start_date=j.start_date,
            end_date=j.end_date,
            status=j.status,
            submitted_by=j.submitted_by,
            submitted_at=j.submitted_at,
            message=build_success_message(j.report_type, j.start_date, j.end_date),
            message_type="success",
        )
        for j in jobs
    ]
    return ReportJobListResponse(jobs=responses, total=len(responses))


@router.get(
    "/{job_id}",
    response_model=ReportJobResponse,
    summary="Get a report job by ID",
)
async def get_report(
    job_id: int,
    current_user: Annotated[UserInfo, Depends(get_current_user_info)],
    service: Annotated[ReportService, Depends(_get_report_service)],
) -> ReportJobResponse:
    """Retrieve a specific report job."""
    job = await service.get_job(job_id)
    return ReportJobResponse(
        job_id=job.job_id,
        report_type=job.report_type,
        start_date=job.start_date,
        end_date=job.end_date,
        status=job.status,
        submitted_by=job.submitted_by,
        submitted_at=job.submitted_at,
        message=build_success_message(job.report_type, job.start_date, job.end_date),
        message_type="success",
    )
