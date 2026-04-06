"""Pydantic schemas for bill payment (COBIL00C).

Business rule: payment is ALWAYS for the full current balance — no partial payments.
"""

from decimal import Decimal

from pydantic import BaseModel, Field


class BillPaymentPreview(BaseModel):
    """Response for GET /api/bill-payment/preview/{account_id}.

    Shows the current account balance before the user confirms payment.
    Maps to the COBIL00C screen display of CURBAL (14-char field).
    """

    account_id: str
    current_balance: Decimal = Field(..., description="Current account balance (always full balance)")
    can_pay: bool = Field(..., description="False if balance <= 0 (COBOL: 'You have nothing to pay')")
    message: str = Field(default="", description="Informational message")


class BillPaymentRequest(BaseModel):
    """Request body for POST /api/bill-payment.

    COBOL CONFIRM='Y' pattern: the confirmed flag must be True for the payment
    to be processed and the transaction to be written.
    """

    account_id: str = Field(..., max_length=11, description="11-digit account ID")
    confirmed: bool = Field(
        default=False,
        description="Must be true to process payment (mirrors COBOL CONFIRM='Y')",
    )


class BillPaymentResult(BaseModel):
    """Response for POST /api/bill-payment after successful processing."""

    account_id: str
    card_number: str
    transaction_id: str = Field(..., description="Auto-generated transaction ID for the payment")
    amount_paid: Decimal = Field(..., description="Amount paid (full balance)")
    new_balance: Decimal = Field(default=Decimal("0.00"), description="Balance after payment (always 0)")
    message: str
