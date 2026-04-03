"""Pydantic schemas for the Bill Payment module (COBIL00C / CB00).

Maps BMS screen fields (COBIL0AI/COBIL0AO) to REST API request/response bodies.
All validation rules mirror the COBOL PROCESS-ENTER-KEY paragraph.
"""
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_validator


class AccountBalanceRequest(BaseModel):
    """Phase 1 — Account lookup request.

    Maps COBIL0AI ACTIDINI field (PIC 9(11), length 11).
    COBIL00C BR-001: account ID must not be empty.
    """

    acct_id: str

    @field_validator("acct_id")
    @classmethod
    def validate_acct_id(cls, v: str) -> str:
        """BR-001: ACTIDINI must not be spaces or low-values."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Acct ID can NOT be empty")
        if not stripped.isdigit():
            raise ValueError("Account ID must be numeric")
        if len(stripped) > 11:
            raise ValueError("Account ID must be at most 11 digits")
        return stripped


class AccountBalanceResponse(BaseModel):
    """Phase 1 response — account found, display current balance.

    Maps COBIL0AO CURBALI field (ASKIP, protected display).
    User sees this before deciding to confirm payment.
    """

    acct_id: str
    curr_bal: Decimal
    message: str | None = None
    message_type: Literal["error", "info", "success"] | None = None

    model_config = {"from_attributes": True}


class PaymentRequest(BaseModel):
    """Phase 2 — Payment confirmation request.

    Maps COBIL0AI:
      ACTIDINI (account ID)
      CONFIRMI = 'Y' or 'y' (COBIL00C line 173 EVALUATE)

    COBIL00C BR-009: CONFIRM must be 'Y' to process payment.
    Backend always treats this as confirmed=True (frontend only calls
    this endpoint when user has explicitly confirmed with Y).
    """

    acct_id: str

    @field_validator("acct_id")
    @classmethod
    def validate_acct_id(cls, v: str) -> str:
        """BR-001: account ID must not be empty."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Acct ID can NOT be empty")
        if not stripped.isdigit():
            raise ValueError("Account ID must be numeric")
        if len(stripped) > 11:
            raise ValueError("Account ID must be at most 11 digits")
        return stripped


class PaymentResponse(BaseModel):
    """Phase 2 response — payment processed successfully.

    Maps COBIL00C WRITE-TRANSACT-FILE success path:
      'Payment successful. Your Transaction ID is <TRAN-ID>.'
    Color: DFHGREEN (green) — message_type='success'.
    """

    tran_id: str
    acct_id: str
    payment_amount: Decimal
    new_balance: Decimal
    orig_timestamp: datetime
    message: str
    message_type: Literal["success", "error", "info"] = "success"

    model_config = {"from_attributes": True}
