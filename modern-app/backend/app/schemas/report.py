"""Pydantic schemas for transaction reports (CORPT00C).

Three report modes matching the COBOL MONTHLY/YEARLY/CUSTOM selection:
  - monthly: current month's first day → last day
  - yearly:  Jan 1 → Dec 31 of current year
  - custom:  caller-supplied start_date / end_date (both required)
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ReportType(str, Enum):
    """Maps to the three COBOL radio-button fields: MONTHLY, YEARLY, CUSTOM."""

    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ReportRequest(BaseModel):
    """Request body for POST /api/reports/transactions.

    COBOL business rule: CONFIRM='Y' is required before submission.
    For custom mode, start_date and end_date must both be provided and
    end_date must be >= start_date.
    """

    report_type: ReportType
    start_date: date | None = Field(
        default=None,
        description="Required for 'custom' report type (YYYY-MM-DD)",
    )
    end_date: date | None = Field(
        default=None,
        description="Required for 'custom' report type (YYYY-MM-DD)",
    )
    confirmed: bool = Field(
        default=False,
        description="Must be true to generate report (mirrors COBOL CONFIRM='Y')",
    )

    @model_validator(mode="after")
    def validate_custom_dates(self) -> "ReportRequest":
        """COBOL rule: custom mode requires both dates; end_date >= start_date."""
        if self.report_type == ReportType.CUSTOM:
            if not self.start_date or not self.end_date:
                raise ValueError(
                    "start_date and end_date are required for custom report type"
                )
            if self.end_date < self.start_date:
                raise ValueError("end_date must be greater than or equal to start_date")
        return self


class ReportTransactionRow(BaseModel):
    """A single transaction row in the report output."""

    transaction_id: str
    card_number: str
    type_code: str
    category_code: str
    description: str
    amount: float
    original_date: str
    processing_date: str
    merchant_name: str
    merchant_city: str


class ReportResult(BaseModel):
    """Response for POST /api/reports/transactions."""

    report_type: ReportType
    start_date: date
    end_date: date
    total_transactions: int
    total_amount: float
    transactions: list[ReportTransactionRow]
    generated_at: str
