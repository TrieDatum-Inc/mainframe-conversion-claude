"""
Pydantic schemas for Report endpoints.

COBOL origin: CORPT00C — Transaction Report Request program (Transaction: CR00).

The original program:
  1. Accepted start/end date (as 3 separate fields: MM + DD + YYYY on screen)
  2. Required CONFIRMI='Y' before submission
  3. Wrote JCL lines to TDQ QUEUE='JOBS' (CICS internal reader)
  4. Batch TRANREPT job ran asynchronously — no status feedback

Modern replacement:
  1. Date range entered via proper date picker (assembled server-side)
  2. confirm='Y' still required
  3. INSERT into report_requests table; BackgroundTasks replaces TDQ
  4. Status polling endpoint replaces missing feedback mechanism

CORPT00C report type mapping:
  MONTHLYI radio button → report_type = 'M'
  YEARLYI radio button  → report_type = 'Y'
  CUSTOMI radio button  → report_type = 'C' (requires explicit start_date/end_date)
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class ReportRequestCreate(BaseModel):
    """
    Request body for POST /api/v1/reports/request.

    COBOL origin: CORPT00C PROCESS-ENTER-KEY input fields:
      MONTHLYI  → report_type='M'
      YEARLYI   → report_type='Y'
      CUSTOMI   → report_type='C'
      SDTMMI + SDTDDI + SDTYYY1I → start_date (assembled from 3 numeric fields)
      EDTMMI + EDTDDI + EDTYYYY1I → end_date (assembled; blank = last day prior month)
      CONFIRMI  → confirm (must be 'Y' — CORPT00C: "Please confirm your request...")

    CORPT00C date default rule:
      If end date blank: CALCULATE-END-DATE computes last day of prior month using
      FUNCTION DATE-OF-INTEGER(FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1).
      This is replicated in report_service.calculate_default_end_date().
    """

    report_type: Literal["M", "Y", "C"] = Field(
        ...,
        description=(
            "CORPT00C: MONTHLYI='M', YEARLYI='Y', CUSTOMI='C'. "
            "Maps the 3-radio-button selection on CORPT0A screen."
        ),
    )
    start_date: Optional[date] = Field(
        None,
        description=(
            "SDTMMI+SDTDDI+SDTYYY1I assembled as YYYYMMDD. "
            "Required when report_type='C'. "
            "Null = no lower bound (CORPT00C allowed blank start date)."
        ),
    )
    end_date: Optional[date] = Field(
        None,
        description=(
            "EDTMMI+EDTDDI+EDTYYYY1I assembled as YYYYMMDD. "
            "Required when report_type='C'. "
            "If null and report_type='C': service applies CORPT00C default (last day prior month)."
        ),
    )
    confirm: Literal["Y"] = Field(
        ...,
        description=(
            "CONFIRMI — must be 'Y' to submit. "
            "Replicates CORPT00C: 'Please confirm your request...' when not 'Y'."
        ),
    )

    @model_validator(mode="after")
    def validate_custom_date_range(self) -> "ReportRequestCreate":
        """
        Validate custom report requires both dates with end >= start.

        COBOL origin: CORPT00C PROCESS-ENTER-KEY date validation + CALCULATE-END-DATE.
        Note: CORPT00C did NOT validate start < end — that was left to batch TRANREPT.
        The modern API adds this safety check.
        """
        if self.report_type == "C":
            if not self.start_date and not self.end_date:
                # Both blank for custom — use defaults (service will calculate)
                pass
            elif self.start_date and self.end_date:
                if self.end_date < self.start_date:
                    raise ValueError(
                        "end_date must be >= start_date (CORPT00C: no date-order validation; added as safety check)"
                    )
        return self


class ReportRequestResponse(BaseModel):
    """
    Response after a report request is submitted.

    Returns 202 Accepted — the request is queued for background processing,
    replicating the asynchronous nature of the original TDQ JOBS submission.
    """

    request_id: int = Field(description="Assigned request ID for status polling")
    report_type: str = Field(description="Report type: M, Y, or C")
    start_date: Optional[date] = Field(None, description="Effective start date (after defaults applied)")
    end_date: Optional[date] = Field(None, description="Effective end date (after defaults applied)")
    status: str = Field(
        description=(
            "Initial status: PENDING. "
            "Replaces CORPT00C's void — original had no status concept after TDQ write."
        )
    )
    requested_at: datetime = Field(description="Timestamp when request was created")
    message: str = Field(
        description=(
            "Confirmation message. "
            "CORPT00C displayed a confirmation after WRITEQ TD QUEUE('JOBS') succeeded."
        )
    )

    model_config = {"from_attributes": True}


class ReportStatusResponse(BaseModel):
    """
    Status check response for GET /api/v1/reports/{report_id}.

    No COBOL equivalent — CORPT00C had no way to check job status.
    This is a modern addition that gives users visibility into report processing.
    """

    request_id: int
    report_type: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    requested_by: str
    status: str
    result_path: Optional[str] = None
    error_message: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
