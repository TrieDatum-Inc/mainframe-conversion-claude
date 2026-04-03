"""Pydantic schemas for the Report Submission module (CORPT00C / CR00).

Maps BMS screen fields (CORPT0AI/CORPT0AO) to REST API request/response bodies.
All validation rules mirror the COBOL PROCESS-ENTER-KEY paragraph.
"""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator


class MonthlyReportRequest(BaseModel):
    """Request to submit a monthly report.

    CORPT00C Monthly Path (lines 213-238):
      Start date = first day of current month (YYYY-MM-01)
      End date = last day of current month (via DATE-OF-INTEGER trick)
    No user-supplied dates — calculated server-side.
    """

    report_type: Literal["monthly"] = "monthly"


class YearlyReportRequest(BaseModel):
    """Request to submit a yearly report.

    CORPT00C Yearly Path (lines 239-255):
      Start date = YYYY-01-01
      End date = YYYY-12-31
    No user-supplied dates — calculated server-side.
    """

    report_type: Literal["yearly"] = "yearly"


class CustomReportRequest(BaseModel):
    """Request to submit a custom date range report.

    CORPT00C Custom Path validation rules (lines 257-436):
      BR-004: start_date month must be 1-12
      BR-004: start_date day must be 1-31
      BR-005: end_date month must be 1-12
      BR-005: end_date day must be 1-31
      BR-006: start_date must be a valid Gregorian date (CSUTLDTC equivalent)
      BR-007: end_date must be a valid Gregorian date (CSUTLDTC equivalent)
      BR-008: start_date must be <= end_date

    Note: Pydantic's date type inherently validates calendar correctness
    (e.g., Feb 31 is rejected), which is equivalent to CSUTLDTC behavior.
    """

    report_type: Literal["custom"] = "custom"
    start_date: date
    end_date: date

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: object) -> object:
        """Validate dates are provided — mirrors COBOL presence checks for 6 fields."""
        if v is None or v == "":
            raise ValueError("Date is required")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "CustomReportRequest":
        """BR-008: start_date <= end_date.

        CORPT00C does not explicitly check this in PROCESS-ENTER-KEY but
        the JCL sort would produce empty output if start > end, so we
        enforce it here as a proper validation.
        """
        if self.start_date > self.end_date:
            raise ValueError(
                "Start date must be on or before end date"
            )
        return self


class ReportSubmitRequest(BaseModel):
    """Unified report submission request.

    Maps CORPT0AI screen fields:
      MONTHLYI / YEARLYI / CUSTOMI → report_type
      SDTMM/SDTDD/SDTYYYY → start_date (custom only)
      EDTMM/EDTDD/EDTYYYY → end_date (custom only)
    """

    report_type: Literal["monthly", "yearly", "custom"]
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_custom_dates(self) -> "ReportSubmitRequest":
        """Custom report type requires both start and end dates."""
        if self.report_type == "custom":
            if self.start_date is None:
                raise ValueError("Start date is required for custom date range reports")
            if self.end_date is None:
                raise ValueError("End date is required for custom date range reports")
            if self.start_date > self.end_date:
                raise ValueError("Start date must be on or before end date")
        return self


class ReportJobResponse(BaseModel):
    """Response after successfully submitting a report job.

    Maps CORPT00C success message:
      '<ReportName> report submitted for printing ...'
    Color: DFHGREEN (green) — indicated by message_type='success'.
    """

    job_id: int
    report_type: str
    start_date: date
    end_date: date
    status: str
    submitted_by: str | None
    submitted_at: datetime
    message: str
    message_type: Literal["success", "error", "info"] = "success"

    model_config = {"from_attributes": True}


class ReportJobListResponse(BaseModel):
    """List of report jobs for display."""

    jobs: list[ReportJobResponse]
    total: int
