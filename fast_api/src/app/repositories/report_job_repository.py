"""ReportJob repository — data access for report_jobs table.

Maps the CORPT00C TDQ JOBS write operation to database persistence.
"""
import logging
from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_job import ReportJob

logger = logging.getLogger(__name__)


class ReportJobRepository:
    """Data access for the report_jobs table.

    CORPT00C WIRTE-JOBSUB-TDQ equivalent:
      EXEC CICS WRITEQ TD QUEUE('JOBS') FROM(JCL-RECORD) LENGTH(80)
      → INSERT INTO report_jobs (report_type, start_date, end_date, submitted_by)
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        report_type: str,
        start_date: date,
        end_date: date,
        submitted_by: str | None,
    ) -> ReportJob:
        """Create a new report job record.

        Maps CORPT00C SUBMIT-JOB-TO-INTRDR (line 462):
          After CONFIRM='Y' check passes, writes JCL lines to TDQ JOBS.
          Modern: inserts a pending report_jobs row.
        """
        job = ReportJob(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            status="pending",
            submitted_by=submitted_by,
        )
        self._session.add(job)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def list_recent(self, limit: int = 20) -> list[ReportJob]:
        """Retrieve most recent report jobs for display."""
        result = await self._session.execute(
            select(ReportJob)
            .order_by(desc(ReportJob.submitted_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, job_id: int) -> ReportJob | None:
        """Fetch report job by primary key."""
        result = await self._session.execute(
            select(ReportJob).where(ReportJob.job_id == job_id)
        )
        return result.scalar_one_or_none()
