"""Batch job tracking data access repository."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch_job import BatchJob, DailyReject


class BatchJobRepository:
    """Data access for batch_jobs and daily_rejects tables."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_job(self, job_type: str) -> BatchJob:
        """Create a new batch job record with 'running' status."""
        job = BatchJob(
            job_type=job_type,
            status="running",
            started_at=datetime.now(tz=timezone.utc),
            created_at=datetime.now(tz=timezone.utc),
        )
        self.db.add(job)
        await self.db.flush()
        return job

    async def complete_job(
        self,
        job_id: int,
        records_processed: int,
        records_rejected: int,
        result_summary: dict,
    ) -> BatchJob | None:
        """Mark job as completed and record statistics."""
        job = await self.get_by_id(job_id)
        if not job:
            return None

        job.status = "completed"
        job.completed_at = datetime.now(tz=timezone.utc)
        job.records_processed = records_processed
        job.records_rejected = records_rejected
        job.result_summary = result_summary

        await self.db.flush()
        return job

    async def fail_job(self, job_id: int, error: str) -> BatchJob | None:
        """Mark job as failed with error details."""
        job = await self.get_by_id(job_id)
        if not job:
            return None

        job.status = "failed"
        job.completed_at = datetime.now(tz=timezone.utc)
        job.result_summary = {"error": error}

        await self.db.flush()
        return job

    async def get_by_id(self, job_id: int) -> BatchJob | None:
        """Retrieve batch job by ID."""
        result = await self.db.execute(
            select(BatchJob).where(BatchJob.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def insert_reject(
        self,
        job_id: int,
        tran_id: str,
        card_num: str,
        reason_code: str,
        reason_desc: str,
        original_data: dict,
    ) -> DailyReject:
        """Write a reject record. Maps CBTRN02C 2500-WRITE-REJECT-REC."""
        reject = DailyReject(
            batch_job_id=job_id,
            tran_id=tran_id,
            card_num=card_num,
            reason_code=reason_code,
            reason_desc=reason_desc,
            original_data=original_data,
            created_at=datetime.now(tz=timezone.utc),
        )
        self.db.add(reject)
        await self.db.flush()
        return reject
