"""Bill payment schemas matching COBOL COBIL00C screen.

- BillPaymentRequest: input from COBIL00C bill pay screen
- BillPaymentResponse: result after bill payment processing
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class BillPaymentRequest(BaseModel):
    """Bill payment request matching COBIL00C input.

    The COBIL00C screen accepts an account ID and a confirmation flag.
    """

    acct_id: int = Field(..., description="Account ID to pay bill for")
    confirm: str = Field(
        default="N",
        max_length=1,
        description="Confirmation flag: 'Y' to confirm, 'N' to preview (matches COBIL00C pattern)",
    )


class BillPaymentResponse(BaseModel):
    """Bill payment response with balance details."""

    message: str = Field(..., description="Result message")
    tran_id: Optional[str] = Field(
        None, max_length=16, description="Generated transaction ID if payment was confirmed"
    )
    previous_balance: Optional[Decimal] = Field(
        None, description="Account balance before payment"
    )
    new_balance: Optional[Decimal] = Field(
        None, description="Account balance after payment"
    )
    acct_id: Optional[int] = Field(None, description="Account ID that was processed")
