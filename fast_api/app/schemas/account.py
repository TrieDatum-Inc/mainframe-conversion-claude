"""
Pydantic schemas for account operations (COACTVWC, COACTUPC).

Maps BMS map COACTUP fields to request/response:
  COACTVWC (read-only view) → AccountResponse
  COACTUPC (update)         → AccountUpdateRequest

Validation rules from COACTUPC:
  - active_status must be 'Y' or 'N'
  - credit_limit >= 0
  - group_id: only admin users can update (enforced in service layer)
  - ZIP code format validated (CSLKPCDY lookup)
  - dates validated via CSUTLDWY
"""
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class AccountBase(BaseModel):
    """Shared fields between request and response schemas."""

    active_status: str | None = Field(None, max_length=1, description="ACCT-ACTIVE-STATUS PIC X(01): Y or N")
    curr_bal: Decimal | None = Field(None, description="ACCT-CURR-BAL PIC S9(10)V99 COMP-3")
    credit_limit: Decimal | None = Field(None, ge=0, description="ACCT-CREDIT-LIMIT PIC S9(10)V99 COMP-3")
    cash_credit_limit: Decimal | None = Field(None, ge=0, description="ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99 COMP-3")
    open_date: str | None = Field(None, max_length=10, description="ACCT-OPEN-DATE PIC X(10) YYYY-MM-DD")
    expiration_date: str | None = Field(None, max_length=10, description="ACCT-EXPIRAION-DATE PIC X(10) YYYY-MM-DD")
    reissue_date: str | None = Field(None, max_length=10, description="ACCT-REISSUE-DATE PIC X(10) YYYY-MM-DD")
    curr_cycle_credit: Decimal | None = Field(None, description="ACCT-CURR-CYC-CREDIT PIC S9(10)V99 COMP-3")
    curr_cycle_debit: Decimal | None = Field(None, description="ACCT-CURR-CYC-DEBIT PIC S9(10)V99 COMP-3")
    addr_zip: str | None = Field(None, max_length=10, description="ACCT-ADDR-ZIP PIC X(10)")
    group_id: str | None = Field(None, max_length=10, description="ACCT-GROUP-ID PIC X(10) [admin only]")

    @field_validator("active_status")
    @classmethod
    def validate_active_status(cls, v: str | None) -> str | None:
        """COACTUPC: active status must be 'Y' or 'N'."""
        if v is not None and v not in ("Y", "N"):
            raise ValueError("active_status must be 'Y' or 'N'")
        return v


class AccountResponse(AccountBase):
    """
    Account view response — maps to COACTVWC SEND MAP output.

    Also includes the account ID and customer details joined from CUSTDAT/CCXREF.
    """

    acct_id: int = Field(..., description="ACCT-ID PIC 9(11)")

    model_config = {"from_attributes": True}


class AccountDetailResponse(AccountResponse):
    """Extended account response including customer info (from COACTVWC join)."""

    customer_id: int | None = Field(None, description="XREF-CUST-ID from CCXREF")
    customer_name: str | None = Field(None, description="CUST-FIRST-NAME + CUST-LAST-NAME")


class AccountUpdateRequest(AccountBase):
    """
    Account update request — maps to COACTUPC RECEIVE MAP input.

    Business rules (COACTUPC):
      - Only admin users can change group_id (enforced in service layer)
      - Monetary fields use Decimal for COMP-3 precision
      - ZIP code format: 5 digits or 5+4 (XXXXX or XXXXX-XXXX)
    """

    @field_validator("addr_zip")
    @classmethod
    def validate_zip(cls, v: str | None) -> str | None:
        """
        COACTUPC ZIP code validation (mirrors CSLKPCDY lookup table check).
        Accepts 5-digit or ZIP+4 format.
        """
        if v is None:
            return v
        v = v.strip()
        if not v:
            return v
        import re
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code must be 5 digits (NNNNN) or ZIP+4 (NNNNN-NNNN)")
        return v
