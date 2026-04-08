"""
Pydantic schemas for report submission (CORPT00C — CICS transaction CR00).

Source program: app/cbl/CORPT00C.cbl
BMS map: CORPT00 / CORPT0A

CORPT00C function:
    Print transaction reports by submitting a batch JCL job via extra-partition
    Transient Data Queue (TDQ) named 'JOBS'. The JCL runs PROC=TRANREPT with
    parameterised date ranges.

Endpoint mapping:
    POST /api/v1/reports/transactions
        → CORPT00C PROCESS-ENTER-KEY (submits JCL via EXEC CICS WRITEQ TD QUEUE('JOBS'))
        → Replaced by FastAPI BackgroundTasks (equivalent async submission)

Business rules preserved:
    1. Report type must be 'monthly', 'yearly', or 'custom'
       (CORPT00C: WHEN MONTHLYI / YEARLYI / CUSTOMI)
    2. For 'monthly' — dates auto-computed: first day of current month to last day
       (CORPT00C: MOVE WS-CURDATE-YEAR/MONTH/DAY to WS-START/END-DATE)
    3. For 'yearly' — dates: YYYY-01-01 to YYYY-12-31
    4. For 'custom' — start_date and end_date required (SDTMMI/SDTDDI/SDTYYYYI fields)
    5. Month must be 1-12, Day must be 1-31 (CORPT00C field-level validations)
    6. All date fields validated as actual calendar dates (CALL 'CSUTLDTC')
    7. User must confirm before submission
       (CORPT00C: CONFIRMI OF CORPT0AI = 'Y' or 'y')
"""
import re
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ReportType(str, Enum):
    """
    CORPT00C report type selector.

    MONTHLYI  OF CORPT0AI NOT = SPACES → 'monthly'
    YEARLYI   OF CORPT0AI NOT = SPACES → 'yearly'
    CUSTOMI   OF CORPT0AI NOT = SPACES → 'custom'
    """

    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    """Report job lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportSubmitRequest(BaseModel):
    """
    Request body for POST /api/v1/reports/transactions.

    Maps to CORPT0A BMS map inputs:
      MONTHLYI  PIC X(1) — 'monthly' flag
      YEARLYI   PIC X(1) — 'yearly' flag
      CUSTOMI   PIC X(1) — 'custom' flag
      SDTMMI    PIC X(2) — start month
      SDTDDI    PIC X(2) — start day
      SDTYYYYI  PIC X(4) — start year
      EDTMMI    PIC X(2) — end month
      EDTDDI    PIC X(2) — end day
      EDTYYYYI  PIC X(4) — end year
    """

    report_type: ReportType = Field(
        ...,
        description="Report type: 'monthly' | 'yearly' | 'custom' (CORPT00C: MONTHLYI/YEARLYI/CUSTOMI)",
    )
    start_date: date | None = Field(
        None,
        description=(
            "Required for 'custom'. "
            "CORPT00C: SDTYYYYI-SDTMMI-SDTDDI (validated via CALL 'CSUTLDTC')"
        ),
    )
    end_date: date | None = Field(
        None,
        description=(
            "Required for 'custom'. "
            "CORPT00C: EDTYYYYI-EDTMMI-EDTDDI (validated via CALL 'CSUTLDTC')"
        ),
    )

    @model_validator(mode="after")
    def validate_custom_dates(self) -> "ReportSubmitRequest":
        """
        CORPT00C PROCESS-ENTER-KEY validation for custom date range.

        Rules:
          - If type == 'custom', start_date and end_date are required
          - Month: 1-12 (SDTMMI OF CORPT0AI > '12' → error)
          - Day: 1-31  (SDTDDI OF CORPT0AI > '31' → error)
          - Dates must be valid calendar dates (CALL 'CSUTLDTC')
          - start_date must be <= end_date (logical ordering check)
        """
        if self.report_type == ReportType.CUSTOM:
            if self.start_date is None:
                raise ValueError("start_date is required for 'custom' report type")
            if self.end_date is None:
                raise ValueError("end_date is required for 'custom' report type")
            if self.start_date > self.end_date:
                raise ValueError("start_date must not be after end_date")
        return self


class ReportJob(BaseModel):
    """
    Representation of a submitted report job.

    Equivalent to what CORPT00C returns after WIRTE-JOBSUB-TDQ succeeds:
    'Monthly report submitted for printing ...' message.
    """

    job_id: str = Field(..., description="Unique report job identifier")
    report_type: ReportType
    start_date: date = Field(..., description="Effective report start date (PARM-START-DATE)")
    end_date: date = Field(..., description="Effective report end date (PARM-END-DATE)")
    status: ReportStatus = Field(default=ReportStatus.PENDING)
    submitted_at: datetime = Field(..., description="Submission timestamp (EXEC CICS ASKTIME equivalent)")
    submitted_by: str = Field(..., description="User ID who submitted (CDEMO-USER-ID)")
    message: str = Field(default="", description="CORPT00C WS-MESSAGE equivalent")

    model_config = {"from_attributes": True}
