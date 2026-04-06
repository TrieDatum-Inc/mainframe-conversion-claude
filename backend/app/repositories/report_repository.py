"""
Data access layer for report requests.

COBOL origin: CORPT00C WIRTE-JOBSUB-TDQ paragraph.

The original CORPT00C wrote JCL lines to TDQ QUEUE='JOBS' (CICS internal reader).
This repository replaces that with INSERT/SELECT on report_requests table.
No COBOL SELECT equivalent existed — CORPT00C had no status-check capability.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_request import ReportRequest


class ReportRepository:
    """
    Repository for report request persistence.

    COBOL equivalent: CORPT00C WIRTE-JOBSUB-TDQ (write) — no read equivalent existed.
    The read operations are new additions for the status polling feature.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_request(self, report_request: ReportRequest) -> ReportRequest:
        """
        Insert a new report request record.

        COBOL origin: CORPT00C WIRTE-JOBSUB-TDQ — builds JCL lines and writes
        each line to TDQ QUEUE='JOBS'. The batch TRANREPT job ran asynchronously.

        Modern equivalent: INSERT into report_requests with status='PENDING'.
        A BackgroundTask (registered in the API endpoint) processes the request
        asynchronously, preserving the fire-and-forget nature of TDQ submission.
        """
        self.db.add(report_request)
        await self.db.flush()
        await self.db.refresh(report_request)
        return report_request

    async def get_by_id(self, request_id: int) -> Optional[ReportRequest]:
        """
        Retrieve a report request by ID for status polling.

        No COBOL equivalent — CORPT00C had no feedback mechanism after TDQ write.
        This is a new capability added in the modern system.
        """
        result = await self.db.execute(
            select(ReportRequest).where(ReportRequest.request_id == request_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        request_id: int,
        status: str,
        result_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[ReportRequest]:
        """
        Update the status of a report request after background processing.

        No COBOL equivalent — TDQ jobs had no status tracking.
        Called by background worker when processing completes or fails.
        """
        report = await self.get_by_id(request_id)
        if not report:
            return None

        report.status = status
        if result_path is not None:
            report.result_path = result_path
        if error_message is not None:
            report.error_message = error_message

        if status in ("COMPLETED", "FAILED"):
            from datetime import datetime, timezone
            report.completed_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(report)
        return report
