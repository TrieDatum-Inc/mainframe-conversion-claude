"""ReportJob ORM model — maps to the `report_jobs` table.

Modern equivalent for CORPT00C TDQ JOBS submission:
  COBOL: EXEC CICS WRITEQ TD QUEUE('JOBS') — writes JCL to internal reader
  Modern: INSERT INTO report_jobs — creates async job record for background processing

The embedded JCL in CORPT00C (lines 83-125) defined:
  PROC=TRANREPT → STEP05R (SORT with TRAN-CARD-NUM, TRAN-PROC-DT) + STEP10R (CBTRN03C report gen)
Modern equivalent: background task reads transactions filtered by date range, generates report.
"""
from datetime import date, datetime

from sqlalchemy import DATE, TIMESTAMP, VARCHAR, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# Report status constants (replaces JCL job states)
REPORT_STATUS_PENDING = "pending"
REPORT_STATUS_RUNNING = "running"
REPORT_STATUS_COMPLETED = "completed"
REPORT_STATUS_FAILED = "failed"

# Report type constants (mirrors CORPT00C WS-REPORT-NAME)
REPORT_TYPE_MONTHLY = "monthly"
REPORT_TYPE_YEARLY = "yearly"
REPORT_TYPE_CUSTOM = "custom"


class ReportJob(Base):
    """Maps to report_jobs table.

    CORPT00C SUBMIT-JOB-TO-INTRDR equivalent:
      - Confirmation check (CONFIRMI = 'Y') done before calling service
      - Date range parameters injected into JCL (PARM-START-DATE-1/2, PARM-END-DATE-1/2)
      - Modern: stored as start_date / end_date columns + report_type
    """

    __tablename__ = "report_jobs"

    job_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="Auto-generated job ID (replaces JCL job name TRNRPT00)",
    )
    report_type: Mapped[str] = mapped_column(
        VARCHAR(20),
        nullable=False,
        comment="Report type: 'monthly', 'yearly', 'custom' (maps WS-REPORT-NAME)",
    )
    start_date: Mapped[date] = mapped_column(
        DATE,
        nullable=False,
        comment="Report date range start (maps PARM-START-DATE in JCL inline data)",
    )
    end_date: Mapped[date] = mapped_column(
        DATE,
        nullable=False,
        comment="Report date range end (maps PARM-END-DATE in JCL inline data)",
    )
    status: Mapped[str] = mapped_column(
        VARCHAR(20),
        nullable=False,
        server_default=text("'pending'"),
        comment="Job status: pending/running/completed/failed",
    )
    submitted_by: Mapped[str | None] = mapped_column(
        VARCHAR(8),
        nullable=True,
        comment="User ID who submitted (from JWT token, maps CDEMO-USERID)",
    )
    submitted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Submission timestamp (maps CORPT00C ASKTIME/FORMATTIME)",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Completion timestamp",
    )
    result_path: Mapped[str | None] = mapped_column(
        VARCHAR(255),
        nullable=True,
        comment="Path to generated report file (replaces GDG TRANREPT output)",
    )
