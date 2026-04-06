"""
SQLAlchemy ORM model for the `report_requests` table.

COBOL origin: CORPT00C TDQ-based batch job submission (WIRTE-JOBSUB-TDQ paragraph).
  The original program wrote JCL lines to the CICS internal reader TDQ QUEUE='JOBS'
  to launch the TRANREPT batch job asynchronously. There was no state tracking —
  the user had no way to check whether the batch job completed.

  This table replaces that pattern with a persistent request record that supports
  status polling and result storage. The replacement for WIRTE-JOBSUB-TDQ is a
  background task (FastAPI BackgroundTasks) that processes the request asynchronously,
  preserving the asynchronous nature of the original JCL submission.

  Key CORPT00C fields mapped:
    CONFIRMI     → not stored; required='Y' to create record (validated in service)
    SDTMMI/SDTDDI/SDTYYY1I  → start_date DATE (assembled from 3 fields)
    EDTMMI/EDTDDI/EDTYYYY1I → end_date DATE (assembled from 3 fields; default = last day prior month)
    MONTHLYI / YEARLYI / CUSTOMI → report_type CHAR(1): 'M', 'Y', 'C'

  The JCLLIB reference 'AWS.M2.CARDDEMO.PROC' is replaced by result_path which
  stores the generated report file path after completion.
"""

from datetime import date, datetime

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReportRequest(Base):
    """
    Persistent report request record — replaces CORPT00C JCL TDQ submission.

    CORPT00C submitted a TRANREPT batch job via TDQ JOBS with no feedback mechanism.
    This table provides the same async submission pattern with status tracking.

    report_type values:
      'M' = Monthly  (MONTHLYI radio button on CORPT0A map)
      'Y' = Yearly   (YEARLYI radio button)
      'C' = Custom   (CUSTOMI radio button — requires explicit start_date/end_date)

    status values:
      'PENDING'   = job submitted, not yet picked up by background worker
      'RUNNING'   = background worker is processing
      'COMPLETED' = report generated successfully
      'FAILED'    = processing failed; see error_message
    """

    __tablename__ = "report_requests"

    __table_args__ = (
        # Maps CORPT00C: report type must be M, Y, or C
        CheckConstraint(
            "report_type IN ('M', 'Y', 'C')",
            name="chk_rptreq_type",
        ),
        # Maps CORPT00C: status transitions
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')",
            name="chk_rptreq_status",
        ),
        # Maps CORPT00C: custom reports require both dates and end >= start
        CheckConstraint(
            (
                "report_type != 'C' OR "
                "(start_date IS NOT NULL AND end_date IS NOT NULL AND end_date >= start_date)"
            ),
            name="chk_rptreq_custom_dates",
        ),
    )

    request_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="BIGSERIAL primary key — no COBOL equivalent; added for modern state tracking.",
    )
    report_type: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        comment=(
            "CORPT00C: MONTHLYI='M', YEARLYI='Y', CUSTOMI='C'. "
            "Maps the 3-radio-button selection on CORPT0A screen."
        ),
    )
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment=(
            "CORPT00C: assembled from SDTYYY1I+SDTMMI+SDTDDI as YYYYMMDD. "
            "Null = no lower bound (permitted in CORPT00C when both date fields blank)."
        ),
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment=(
            "CORPT00C: assembled from EDTYYYY1I+EDTMMI+EDTDDI. "
            "If blank: CALCULATE-END-DATE computes last day of prior month. "
            "Required when report_type='C'."
        ),
    )
    requested_by: Mapped[str] = mapped_column(
        String(8),
        ForeignKey("users.user_id", name="fk_rptreq_user"),
        nullable=False,
        comment="User ID of the requesting user (from JWT sub claim). Maps CSUSR01Y signed-on user.",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        comment=(
            "Processing status. CORPT00C had no status field — this is a modern addition. "
            "PENDING = equivalent to WRITEQ TD QUEUE('JOBS') just issued."
        ),
    )
    result_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment=(
            "Path or URL to generated report file. "
            "Replaces the JCLLIB 'AWS.M2.CARDDEMO.PROC' TRANREPT output dataset."
        ),
    )
    error_message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Error details if status='FAILED'. No COBOL equivalent (TDQ errors were silent).",
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp of request creation — when the TDQ write would have occurred.",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when background processing completed. No COBOL equivalent.",
    )

    def __repr__(self) -> str:
        return (
            f"ReportRequest(request_id={self.request_id!r}, "
            f"report_type={self.report_type!r}, status={self.status!r})"
        )
