"""Batch job tracking ORM models.

Maps JCL batch job execution to a persistent audit trail.
"""

from datetime import datetime

from sqlalchemy import CHAR, INTEGER, VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class BatchJob(Base):
    """Batch job execution record. Equivalent to JCL job step metadata."""

    __tablename__ = "batch_jobs"

    job_id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(VARCHAR(30))
    status: Mapped[str] = mapped_column(VARCHAR(20), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    records_processed: Mapped[int] = mapped_column(INTEGER, default=0)
    records_rejected: Mapped[int] = mapped_column(INTEGER, default=0)
    result_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(nullable=True)


class DailyReject(Base):
    """Rejected transaction record. Maps DALYREJS GDG output from CBTRN02C.

    Original COBOL record: 350-byte DALYTRAN + 80-byte validation trailer.
    Modern equivalent: reason_code + reason_desc + original_data (JSON).
    """

    __tablename__ = "daily_rejects"

    reject_id: Mapped[int] = mapped_column(INTEGER, primary_key=True, autoincrement=True)
    batch_job_id: Mapped[int | None] = mapped_column(
        ForeignKey("batch_jobs.job_id"), nullable=True
    )
    tran_id: Mapped[str | None] = mapped_column(VARCHAR(16), nullable=True)
    card_num: Mapped[str | None] = mapped_column(VARCHAR(16), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(CHAR(3), nullable=True)
    reason_desc: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    original_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(nullable=True)
