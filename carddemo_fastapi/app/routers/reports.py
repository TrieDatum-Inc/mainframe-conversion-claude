"""Report router porting COBOL program CORPT00C.

CORPT00C handles the report generation screen which accepts report type
(monthly, yearly, or custom date range) and a confirmation flag. On
confirmation it submits a batch report job. In the COBOL system this
triggered a batch CICS transaction; here it calls the report service.

This router replaces that screen with a REST endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.report import ReportRequest, ReportResponse
from app.services import report_service

router = APIRouter(tags=["reports"])


@router.post("/", response_model=ReportResponse)
def submit_report(
    body: ReportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ReportResponse:
    """Submit a report generation request.

    Ports COBOL program CORPT00C which handles the report request screen
    with a two-step confirm flow. Supports monthly, yearly, and custom
    date range reports. When confirm='Y', the report is generated and
    the report file name is returned.
    """
    return report_service.submit_report(
        db,
        report_type=body.report_type,
        start_month=body.start_month,
        start_day=body.start_day,
        start_year=body.start_year,
        end_month=body.end_month,
        end_day=body.end_day,
        end_year=body.end_year,
        confirm=body.confirm,
    )
