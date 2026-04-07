"""
Account and Customer schemas.

COBOL origin: COACTVWC (view) + COACTUPC (update).
Maps CACTVWA BMS map fields and CVACT01Y/CVCUS01Y copybook fields.

Key rules preserved from COACTUPC:
  - SSN part1 cannot be 000, 666, or 900-999 (IRS invalid ranges)
  - FICO score must be 300-850
  - cash_credit_limit <= credit_limit
  - SSN is masked in all responses (***-**-XXXX)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# Customer response — nested in AccountViewResponse
# SSN always masked, never returned plain
# =============================================================================

class CustomerDetailResponse(BaseModel):
    """
    Customer details nested in account view response.
    Maps CVCUS01Y copybook fields displayed in CACTVWA BMS map.
    SSN is always returned masked (***-**-XXXX).
    """
    customer_id: int
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    ssn_masked: str           # Always ***-**-XXXX — never plain text
    date_of_birth: Optional[str] = None
    fico_score: Optional[int] = None
    primary_card_holder: str  # Y/N
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    address_line_3: Optional[str] = None
    city: Optional[str] = None       # derived from address_line_3 if available
    state_code: Optional[str] = None
    zip_code: Optional[str] = None
    country_code: Optional[str] = None
    phone_1: Optional[str] = None
    phone_2: Optional[str] = None
    government_id_ref: Optional[str] = None
    eft_account_id: Optional[str] = None

    model_config = {"from_attributes": True}


# =============================================================================
# Account view response — COACTVWC
# =============================================================================

class AccountViewResponse(BaseModel):
    """
    Full account view response — COACTVWC output.
    Joins ACCTDAT + CUSTDAT + CARDXREF data sources.
    Maps all CACTVWA ASKIP display fields.
    """
    account_id: int
    active_status: str          # ACSTTUS — Y/N
    credit_limit: Decimal       # ACRDLIM — S9(10)V99
    cash_credit_limit: Decimal  # ACSHLIM
    current_balance: Decimal    # ACURBAL
    curr_cycle_credit: Decimal  # ACRCYCR
    curr_cycle_debit: Decimal   # ACRCYDB
    open_date: Optional[str] = None           # ADTOPEN PIC X(10)
    expiration_date: Optional[str] = None     # AEXPDT
    reissue_date: Optional[str] = None        # AREISDT
    group_id: Optional[str] = None            # AADDGRP
    updated_at: str                           # optimistic lock version for PUT
    customer: CustomerDetailResponse

    model_config = {"from_attributes": True}


# =============================================================================
# Account update request — COACTUPC
# 15+ validation rules preserved exactly
# =============================================================================

class CustomerUpdateRequest(BaseModel):
    """
    Customer fields in the account update request.
    COACTUPC validates these fields before REWRITE CUSTDAT.

    SSN validation (COBOL rules):
      - Part 1 (3 digits) cannot be 000, 666, or 900-999
      - Part 2 (2 digits) cannot be 00
      - Part 3 (4 digits) cannot be 0000
    """
    first_name: str = Field(..., min_length=1, max_length=25)
    middle_name: Optional[str] = Field(None, max_length=25)
    last_name: str = Field(..., min_length=1, max_length=25)
    address_line_1: Optional[str] = Field(None, max_length=50)
    address_line_2: Optional[str] = Field(None, max_length=50)
    address_line_3: Optional[str] = Field(None, max_length=50)
    state_code: Optional[str] = Field(None, max_length=2)
    country_code: Optional[str] = Field(None, max_length=3)
    zip_code: Optional[str] = Field(None, max_length=10)
    phone_1: Optional[str] = Field(None, max_length=15)
    phone_2: Optional[str] = Field(None, max_length=15)
    ssn_part1: Optional[str] = Field(None, pattern=r"^\d{3}$")   # NNN
    ssn_part2: Optional[str] = Field(None, pattern=r"^\d{2}$")   # NN
    ssn_part3: Optional[str] = Field(None, pattern=r"^\d{4}$")   # NNNN
    government_id_ref: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[str] = None
    eft_account_id: Optional[str] = Field(None, max_length=10)
    primary_card_holder: Optional[str] = Field(None, pattern=r"^[YN]$")
    fico_score: Optional[int] = Field(None, ge=300, le=850)

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_date_of_birth_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISO date format for date_of_birth (YYYY-MM-DD)."""
        if v is None or v == "":
            return None
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date format '{v}': expected YYYY-MM-DD")
        return v

    @model_validator(mode="after")
    def validate_ssn_parts(self) -> "CustomerUpdateRequest":
        """
        Validate SSN according to COACTUPC rules.
        Only validates if all three parts are provided.

        COBOL origin: COACTUPC SSN-PART1/2/3 validation paragraphs.
        """
        p1, p2, p3 = self.ssn_part1, self.ssn_part2, self.ssn_part3

        # If any SSN part is provided, all must be provided
        parts_provided = [p for p in [p1, p2, p3] if p is not None]
        if 0 < len(parts_provided) < 3:
            raise ValueError("All three SSN parts (NNN, NN, NNNN) must be provided together")

        if p1 and p2 and p3:
            # COBOL rule: part1 cannot be 000
            if p1 == "000":
                raise ValueError("SSN area number cannot be 000")
            # COBOL rule: part1 cannot be 666
            if p1 == "666":
                raise ValueError("SSN area number cannot be 666")
            # COBOL rule: part1 cannot be 900-999
            if 900 <= int(p1) <= 999:
                raise ValueError("SSN area number 900-999 is not valid")
            # COBOL rule: part2 cannot be 00
            if p2 == "00":
                raise ValueError("SSN group number cannot be 00")
            # COBOL rule: part3 cannot be 0000
            if p3 == "0000":
                raise ValueError("SSN serial number cannot be 0000")

        return self


class AccountUpdateRequest(BaseModel):
    """
    Account update request body — COACTUPC.
    Validates account fields and delegates customer sub-fields.

    COBOL rule: cash_credit_limit must not exceed credit_limit.
    """
    optimistic_lock_version: str = Field(
        ...,
        description="ISO datetime from GET response updated_at — prevents concurrent overwrites",
    )
    active_status: Optional[str] = Field(None, pattern=r"^[YN]$")
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    cash_credit_limit: Optional[Decimal] = Field(None, ge=0)
    open_date: Optional[str] = None
    expiration_date: Optional[str] = None
    reissue_date: Optional[str] = None
    group_id: Optional[str] = Field(None, max_length=10)
    customer: CustomerUpdateRequest

    @field_validator("open_date", "expiration_date", "reissue_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that date strings are ISO format (YYYY-MM-DD).
        Raises ValueError early so clients receive 422 instead of silent no-op.
        """
        if v is None or v == "":
            return None
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid date format '{v}': expected YYYY-MM-DD")
        return v

    @model_validator(mode="after")
    def validate_cash_limit_vs_credit_limit(self) -> "AccountUpdateRequest":
        """
        COACTUPC rule: cash credit limit cannot exceed credit limit.
        COBOL: IF ACCT-CASH-CREDIT-LIMIT > ACCT-CREDIT-LIMIT → error.
        """
        if (
            self.cash_credit_limit is not None
            and self.credit_limit is not None
            and self.cash_credit_limit > self.credit_limit
        ):
            raise ValueError("Cash credit limit cannot exceed credit limit")
        return self
