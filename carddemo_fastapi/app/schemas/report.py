"""Report schemas matching COBOL CORPT00C screen.

- ReportRequest: report generation input from CORPT00C
- ReportResponse: report generation result
"""

from typing import Optional

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Report request matching CORPT00C screen input.

    Supports monthly, yearly, and custom date range reports.
    """

    report_type: str = Field(
        ...,
        description="Report type: 'monthly', 'yearly', or 'custom'",
    )
    start_month: Optional[int] = Field(
        None, ge=1, le=12, description="Start month (1-12)"
    )
    start_day: Optional[int] = Field(
        None, ge=1, le=31, description="Start day (1-31)"
    )
    start_year: Optional[int] = Field(None, description="Start year (4-digit)")
    end_month: Optional[int] = Field(
        None, ge=1, le=12, description="End month (1-12)"
    )
    end_day: Optional[int] = Field(
        None, ge=1, le=31, description="End day (1-31)"
    )
    end_year: Optional[int] = Field(None, description="End year (4-digit)")
    confirm: str = Field(
        default="N",
        max_length=1,
        description="Confirmation flag: 'Y' to confirm, 'N' to preview (matches CORPT00C pattern)",
    )


class ReportDateRange(BaseModel):
    """Date range component for report response."""

    month: Optional[int] = Field(None, description="Month (1-12)")
    day: Optional[int] = Field(None, description="Day (1-31)")
    year: Optional[int] = Field(None, description="Year (4-digit)")


class ReportResponse(BaseModel):
    """Report generation response."""

    message: str = Field(..., description="Result message")
    report_type: Optional[str] = Field(None, description="Report type")
    start_date: Optional[ReportDateRange] = Field(None, description="Start date range")
    end_date: Optional[ReportDateRange] = Field(None, description="End date range")
