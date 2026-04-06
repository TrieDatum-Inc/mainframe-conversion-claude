"""
Pydantic schemas for Billing endpoints.

COBOL origin: COBIL00C — Online Bill Payment program.

Two-phase pattern:
  Phase 1 (GET balance): READ-ACCTDAT-FILE; display CURBAL; await confirmation
  Phase 2 (POST payment): CONFIRMI='Y'; READ CXACAIX; STARTBR/READPREV; WRITE TRANSACT; REWRITE ACCTDAT

Key COBIL00C business rules preserved:
  - account_id required (ACTIDINI blank → error)
  - ACCT-CURR-BAL > 0 required to make payment (WS-CONF-PAY-FLG guard)
  - Payment sets balance to ACCT-CURR-BAL - TRAN-AMT = 0 (full balance payment)
  - confirm='Y' required (CONFIRMI gate)
  - Transaction type_code '02', category '0002', source 'POS TERM' (all hardcoded in COBIL00C)
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


class BillingBalanceResponse(BaseModel):
    """
    Phase 1 response — account balance for display before confirmation.

    COBOL origin: COBIL00C READ-ACCTDAT-FILE path when CONFIRMI=SPACES.
      CURBAL → current_balance  (CURBALI output field on COBIL0A map)
    """

    account_id: int = Field(description="ACTIDINI — 11-digit account ID")
    current_balance: Decimal = Field(
        description="ACCT-CURR-BAL — displayed as CURBAL on COBIL0A map"
    )
    credit_limit: Optional[Decimal] = Field(None, description="ACCT-CREDIT-LIMIT")
    available_credit: Optional[Decimal] = Field(
        None,
        description="Computed: credit_limit - current_balance (not displayed in COBIL00C but useful for modern UI)",
    )

    model_config = {"from_attributes": True}


class BillPaymentRequest(BaseModel):
    """
    Phase 2 request — confirm payment execution.

    COBOL origin: COBIL00C PROCESS-ENTER-KEY when CONFIRMI='Y':
      - Reads CXACAIX to get card number
      - Generates transaction ID via sequence (fixes STARTBR/READPREV race condition)
      - Writes payment transaction to TRANSACT
      - Rewrites ACCTDAT with balance = 0

    confirm must be 'Y' — maps COBIL00C CONF-PAY-YES gate.
    account_id provided in URL path (not in body per REST convention).
    """

    confirm: Literal["Y"] = Field(
        ...,
        description=(
            "CONFIRMI — must be 'Y' to execute payment. "
            "Maps COBIL00C EVALUATE CONFIRMI WHEN 'Y'/'y' → SET CONF-PAY-YES."
        ),
    )


class BillPaymentResponse(BaseModel):
    """
    Payment execution result.

    COBOL origin: COBIL00C WRITE-TRANSACT-FILE success path.
      'Payment successful. Your Transaction ID is [N].' → message (in DFHGREEN color)
    """

    account_id: int
    previous_balance: Decimal = Field(
        description=(
            "ACCT-CURR-BAL before payment — stored as TRAN-AMT in the payment transaction. "
            "COBIL00C: COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT where TRAN-AMT = previous balance."
        )
    )
    new_balance: Decimal = Field(
        description=(
            "ACCT-CURR-BAL after payment — always 0 after full payment. "
            "COBIL00C: COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT = 0."
        )
    )
    transaction_id: str = Field(
        description=(
            "Generated transaction ID for the payment record. "
            "COBIL00C: 'Your Transaction ID is [N].' in success message."
        )
    )
    message: str = Field(
        description="Success message — maps COBIL00C ERRMSGO DFHGREEN success display."
    )

    model_config = {"from_attributes": True}
