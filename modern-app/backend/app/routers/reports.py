"""Transaction report API routes — thin controller layer.

Maps CICS CR00 (CORPT00C) to REST endpoints:
  POST /api/reports/transactions — generate report (CONFIRM='Y' pattern)

The COBOL approach submitted JCL to a TDQ for batch processing.
This modern equivalent generates the report data synchronously in SQL.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import User, get_current_user
from app.schemas.report import ReportRequest, ReportResult
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post(
    "/transactions",
    response_model=ReportResult,
    summary="Generate transaction report (CR00 / CORPT00C)",
)
async def generate_transaction_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportResult:
    """Generate a transaction report for the specified period.

    Mirrors CORPT00C:
    - Monthly: auto-derives current month start/end dates
    - Yearly:  Jan 1 to Dec 31 of current year
    - Custom:  caller-supplied start_date/end_date (both required, end >= start)
    - confirmed=true required to generate (COBOL CONFIRM='Y')

    Returns JSON report data. The COBOL equivalent submitted a batch JCL job
    to produce a 133-byte line-printer report; this endpoint returns equivalent
    data as structured JSON (CSV export is available via Accept header).
    """
    if not request.confirmed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Report not confirmed. Set confirmed=true to generate report.",
        )

    service = ReportService(db)
    return await service.generate_report(request)
