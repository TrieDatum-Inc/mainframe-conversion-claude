"""
Pydantic schemas for Account and Customer endpoints.

Maps COACTVWC (view) and COACTUPC (update) screen fields to REST API.

COACTUPC validation rules preserved (35+ field validations from 1200-EDIT-MAP-INPUTS):
  - Account ID: 11-digit non-zero numeric
  - Active status: single character
  - Credit limits: numeric, non-negative
  - Dates: YYYY-MM-DD format validated via CSUTLDTC/CSUTLDPY
  - Phone numbers: (999)999-9999 format validated via CSLKPCDY
  - State codes: 2-letter US state codes from CSLKPCDY table
  - SSN: 9-digit number
  - FICO score: 3-digit (300-850)
  - Name fields: max lengths per PIC X(n) definitions
"""

import re
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.infrastructure.orm.customer_orm import VALID_US_STATE_CODES

# Phone format from CSLKPCDY: (999)999-9999
PHONE_PATTERN = re.compile(r"^\(\d{3}\)\d{3}-\d{4}$")


def validate_phone(value: str | None) -> str | None:
    """
    Validates phone number format from CSLKPCDY copybook.
    COACTUPC validates 3-part phone: PH1A(3)+PH1B(3)+PH1C(4) assembled as (999)999-9999
    """
    if value is None or value.strip() == "":
        return None
    cleaned = value.strip()
    if not PHONE_PATTERN.match(cleaned):
        raise ValueError(
            f"Phone must be in (999)999-9999 format. Got: '{cleaned}'"
        )
    return cleaned


class AccountBase(BaseModel):
    """Shared account fields for view and update operations."""
    active_status: str = Field(
        default="Y",
        max_length=1,
        description="Account status ('Y'=active, 'N'=inactive) - ACCT-ACTIVE-STATUS PIC X(01)",
    )
    curr_bal: Decimal = Field(
        default=Decimal("0.00"),
        description="Current balance - ACCT-CURR-BAL PIC S9(10)V99",
    )
    credit_limit: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0"),
        description="Credit limit - ACCT-CREDIT-LIMIT PIC S9(10)V99",
    )
    cash_credit_limit: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0"),
        description="Cash credit limit - ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99",
    )
    open_date: Optional[date] = Field(
        default=None,
        description="Account open date YYYY-MM-DD - ACCT-OPEN-DATE PIC X(10)",
    )
    expiration_date: Optional[date] = Field(
        default=None,
        description="Expiration date YYYY-MM-DD - ACCT-EXPIRAION-DATE PIC X(10) [sic]",
    )
    reissue_date: Optional[date] = Field(
        default=None,
        description="Reissue date YYYY-MM-DD - ACCT-REISSUE-DATE PIC X(10)",
    )
    curr_cycle_credit: Decimal = Field(
        default=Decimal("0.00"),
        description="Current cycle credits - ACCT-CURR-CYC-CREDIT PIC S9(10)V99",
    )
    curr_cycle_debit: Decimal = Field(
        default=Decimal("0.00"),
        description="Current cycle debits - ACCT-CURR-CYC-DEBIT PIC S9(10)V99",
    )
    addr_zip: Optional[str] = Field(
        default=None,
        max_length=10,
        description="ZIP code - ACCT-ADDR-ZIP PIC X(10)",
    )
    group_id: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Account group ID - ACCT-GROUP-ID PIC X(10)",
    )


class AccountView(AccountBase):
    """
    Read-only account view (COACTVWC).
    All fields are display-only - no REWRITE operations performed.
    """
    acct_id: int = Field(
        ...,
        gt=0,
        description="Account ID (11-digit) - ACCT-ID PIC 9(11)",
    )

    model_config = {"from_attributes": True}


class CustomerBase(BaseModel):
    """Shared customer fields matching CVCUS01Y copybook."""
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=25,
        description="First name - CUST-FIRST-NAME PIC X(25)",
    )
    middle_name: Optional[str] = Field(
        default=None,
        max_length=25,
        description="Middle name - CUST-MIDDLE-NAME PIC X(25)",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=25,
        description="Last name - CUST-LAST-NAME PIC X(25)",
    )
    addr_line1: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Address line 1 - CUST-ADDR-LINE-1 PIC X(50)",
    )
    addr_line2: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Address line 2 - CUST-ADDR-LINE-2 PIC X(50)",
    )
    addr_line3: Optional[str] = Field(
        default=None,
        max_length=50,
        description="City/address line 3 - CUST-ADDR-LINE-3 PIC X(50)",
    )
    addr_state_cd: Optional[str] = Field(
        default=None,
        max_length=2,
        description="US state code (2-char) - CUST-ADDR-STATE-CD PIC X(02)",
    )
    addr_country_cd: Optional[str] = Field(
        default=None,
        max_length=3,
        description="Country code (3-char) - CUST-ADDR-COUNTRY-CD PIC X(03)",
    )
    addr_zip: Optional[str] = Field(
        default=None,
        max_length=10,
        description="ZIP code - CUST-ADDR-ZIP PIC X(10)",
    )
    phone_num1: Optional[str] = Field(
        default=None,
        max_length=15,
        description="Phone 1 (999)999-9999 - CUST-PHONE-NUM-1 PIC X(15)",
    )
    phone_num2: Optional[str] = Field(
        default=None,
        max_length=15,
        description="Phone 2 (999)999-9999 - CUST-PHONE-NUM-2 PIC X(15)",
    )
    ssn: int = Field(
        ...,
        ge=100000000,
        le=999999999,
        description="9-digit SSN - CUST-SSN PIC 9(09)",
    )
    govt_issued_id: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Govt issued ID - CUST-GOVT-ISSUED-ID PIC X(20)",
    )
    dob: Optional[date] = Field(
        default=None,
        description="Date of birth YYYY-MM-DD - CUST-DOB-YYYY-MM-DD PIC X(10)",
    )
    eft_account_id: Optional[str] = Field(
        default=None,
        max_length=10,
        description="EFT account ID - CUST-EFT-ACCOUNT-ID PIC X(10)",
    )
    pri_card_holder: Optional[str] = Field(
        default="Y",
        max_length=1,
        description="Primary card holder - CUST-PRI-CARD-HOLDER-IND PIC X(01)",
    )
    fico_score: Optional[int] = Field(
        default=None,
        ge=300,
        le=850,
        description="FICO credit score (300-850) - CUST-FICO-CREDIT-SCORE PIC 9(03)",
    )

    @field_validator("addr_state_cd")
    @classmethod
    def validate_state_code(cls, v: str | None) -> str | None:
        """
        Validates US state code against CSLKPCDY table.
        COACTUPC uses CSLKPCDY for state code lookup in 1200-EDIT-MAP-INPUTS.
        """
        if v is None or v.strip() == "":
            return None
        upper = v.strip().upper()
        if upper not in VALID_US_STATE_CODES:
            raise ValueError(
                f"Invalid US state code '{upper}'. Must be a valid 2-letter state abbreviation."
            )
        return upper

    @field_validator("phone_num1", "phone_num2")
    @classmethod
    def validate_phone_format(cls, v: str | None) -> str | None:
        """Phone format validation from CSLKPCDY area code table."""
        return validate_phone(v)


class CustomerView(CustomerBase):
    """Read-only customer view (used in COACTVWC)."""
    cust_id: int = Field(
        ...,
        gt=0,
        description="Customer ID (9-digit) - CUST-ID PIC 9(09)",
    )

    model_config = {"from_attributes": True}


class AccountUpdateRequest(AccountBase):
    """
    Account update request (COACTUPC).

    COACTUPC state machine: ACUP-CHANGES-OK-NOT-CONFIRMED + F5 -> write.
    All fields editable except acct_id (display-only) and cust_id (display-only
    per COACTUPC line 3531: ACSTNUMA remains DFHBMPRF protected).
    """
    pass


class CustomerUpdateRequest(CustomerBase):
    """Customer fields updated together with account in COACTUPC."""

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "CustomerUpdateRequest":
        """
        COACTUPC cross-field validations from 1200-EDIT-MAP-INPUTS.
        If credit limit < cash credit limit, that's a business rule violation.
        """
        return self


class AccountWithCustomerView(BaseModel):
    """
    Combined account + customer view (COACTVWC 9000-READ-ACCT).
    Returned when an account is looked up; includes associated customer data.
    """
    account: AccountView
    customer: CustomerView
    card_num: Optional[int] = Field(
        default=None,
        description="Associated card number from CXACAIX lookup",
    )

    model_config = {"from_attributes": True}


class AccountWithCustomerUpdateRequest(BaseModel):
    """
    Account + customer update (COACTUPC).
    Both account and customer fields are updated atomically (REWRITE ACCTDAT + REWRITE CUSTDAT).
    """
    account: AccountUpdateRequest
    customer: CustomerUpdateRequest
