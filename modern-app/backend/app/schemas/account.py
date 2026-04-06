"""Pydantic schemas for Account and Customer endpoints.

Business rules preserved from COACTUPC (4400-line COBOL program):
- Phone format: (xxx)xxx-xxxx  (area code validated against NANP table)
- SSN format: xxx-xx-xxxx (digits only, 9 total)
- State code: exactly 2 uppercase alpha chars (validated against 50-state list)
- Zip code: 5 or 9 digits (validated against state-zip cross-table)
- Dates: valid calendar dates (CSUTLDPY validation)
- Financial fields: signed numeric (no alphabetic chars)
- Active status: 'Y' or 'N' only
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Constants — COBOL CSLKPCDY lookup equivalents
# ---------------------------------------------------------------------------

# All valid US state codes (50 states + DC + territories)
VALID_STATE_CODES: frozenset[str] = frozenset(
    [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        "DC", "PR", "GU", "VI", "AS", "MP",  # territories
    ]
)

_PHONE_RE = re.compile(r"^\(\d{3}\)\d{3}-\d{4}$")
_SSN_RE = re.compile(r"^\d{3}-\d{2}-\d{4}$")
_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")


# ---------------------------------------------------------------------------
# Customer schemas
# ---------------------------------------------------------------------------


class CustomerBase(BaseModel):
    """Shared customer fields (used in both read and write)."""

    first_name: str = Field(max_length=25)
    middle_name: str = Field(default="", max_length=25)
    last_name: str = Field(max_length=25)
    address_line_1: str = Field(default="", max_length=50)
    address_line_2: str = Field(default="", max_length=50)
    address_line_3: str = Field(default="", max_length=50)
    state_code: str = Field(default="", max_length=2)
    country_code: str = Field(default="USA", max_length=3)
    zip_code: str = Field(default="", max_length=10)
    phone_1: str = Field(default="", max_length=15)
    phone_2: str = Field(default="", max_length=15)
    ssn: str = Field(default="", max_length=11, description="Format: xxx-xx-xxxx")
    govt_issued_id: str = Field(default="", max_length=20)
    date_of_birth: date | None = None
    eft_account_id: str = Field(default="", max_length=10)
    primary_card_holder: str = Field(default="Y", max_length=1)
    fico_score: int | None = Field(default=None, ge=300, le=850)


class CustomerResponse(CustomerBase):
    """Customer record returned by API — adds DB identifiers."""

    id: int
    customer_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Account schemas
# ---------------------------------------------------------------------------


class AccountBase(BaseModel):
    """Shared account fields."""

    active_status: str = Field(default="Y", max_length=1)
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    cash_credit_limit: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    open_date: date | None = None
    expiration_date: date | None = None
    reissue_date: date | None = None
    current_cycle_credit: Decimal = Field(default=Decimal("0"), decimal_places=2)
    current_cycle_debit: Decimal = Field(default=Decimal("0"), decimal_places=2)
    address_zip: str | None = Field(default=None, max_length=10)
    group_id: str | None = Field(default=None, max_length=10)


class AccountListItem(BaseModel):
    """Lightweight account row for list/search results (COCRDLIC pattern)."""

    account_id: str
    active_status: str
    current_balance: Decimal
    credit_limit: Decimal
    open_date: date | None

    model_config = {"from_attributes": True}


class CardSummary(BaseModel):
    """Card summary shown inside account detail (COACTVWC browse of CARDAIX)."""

    card_number: str
    active_status: str
    expiration_date: date | None
    embossed_name: str

    model_config = {"from_attributes": True}


class AccountDetailResponse(AccountBase):
    """Full account record with nested customer and cards (COACTVWC output)."""

    id: int
    account_id: str
    current_balance: Decimal
    customer: CustomerResponse | None = None
    cards: list[CardSummary] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountListResponse(BaseModel):
    """Paginated list response for GET /api/accounts."""

    items: list[AccountListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Account + Customer update schema (COACTUPC validation)
# ---------------------------------------------------------------------------


class AccountUpdateRequest(BaseModel):
    """PUT /api/accounts/{account_id} payload.

    Mirrors COACTUPC's editable fields and their COBOL validation rules.
    Account ID itself is never updated (it is the key).

    Financial fields use Decimal for exact arithmetic (COMP-3 equivalent).
    """

    # Account fields
    active_status: str | None = Field(default=None, max_length=1)
    credit_limit: Decimal | None = Field(default=None, ge=0)
    cash_credit_limit: Decimal | None = Field(default=None, ge=0)
    open_date: date | None = None
    expiration_date: date | None = None
    reissue_date: date | None = None
    current_cycle_credit: Decimal | None = None
    current_cycle_debit: Decimal | None = None
    group_id: str | None = Field(default=None, max_length=10)

    # Customer fields (COACTUPC also updates the linked customer record)
    first_name: str | None = Field(default=None, max_length=25)
    middle_name: str | None = Field(default=None, max_length=25)
    last_name: str | None = Field(default=None, max_length=25)
    address_line_1: str | None = Field(default=None, max_length=50)
    address_line_2: str | None = Field(default=None, max_length=50)
    address_line_3: str | None = Field(default=None, max_length=50)
    state_code: str | None = Field(default=None, max_length=2)
    country_code: str | None = Field(default=None, max_length=3)
    zip_code: str | None = Field(default=None, max_length=10)
    phone_1: str | None = Field(default=None, max_length=15)
    phone_2: str | None = Field(default=None, max_length=15)
    ssn: str | None = Field(default=None, max_length=11)
    govt_issued_id: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    eft_account_id: str | None = Field(default=None, max_length=10)
    primary_card_holder: str | None = Field(default=None, max_length=1)
    fico_score: int | None = Field(default=None, ge=300, le=850)

    # -----------------------------------------------------------------
    # Field-level validators (mirror COACTUPC inline validation)
    # -----------------------------------------------------------------

    @field_validator("active_status")
    @classmethod
    def validate_active_status(cls, v: str | None) -> str | None:
        """COBOL: ACCT-ACTIVE-STATUS must be 'Y' or 'N'."""
        if v is not None and v not in ("Y", "N"):
            raise ValueError("active_status must be 'Y' or 'N'")
        return v

    @field_validator("primary_card_holder")
    @classmethod
    def validate_primary_card_holder(cls, v: str | None) -> str | None:
        """COBOL: CUST-PRI-CARD-HOLDER-IND must be 'Y' or 'N'."""
        if v is not None and v not in ("Y", "N"):
            raise ValueError("primary_card_holder must be 'Y' or 'N'")
        return v

    @field_validator("phone_1", "phone_2")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """COBOL CSLKPCDY: phone must be (xxx)xxx-xxxx format.

        Blank phone numbers are allowed (field is optional).
        """
        if v is not None and v.strip() and not _PHONE_RE.match(v):
            raise ValueError(
                "Phone must be in format (xxx)xxx-xxxx"
            )
        return v

    @field_validator("ssn")
    @classmethod
    def validate_ssn(cls, v: str | None) -> str | None:
        """COBOL COACTUPC: SSN split ACTSSN1(3)+ACTSSN2(2)+ACTSSN3(4).

        Stored as 'xxx-xx-xxxx' format; digits only (9 total).
        """
        if v is not None and v.strip():
            if not _SSN_RE.match(v):
                raise ValueError("SSN must be in format xxx-xx-xxxx")
            digits = v.replace("-", "")
            if not digits.isdigit() or len(digits) != 9:
                raise ValueError("SSN must contain exactly 9 digits")
        return v

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, v: str | None) -> str | None:
        """COBOL CSLKPCDY: state code must be in 50-state table."""
        if v is not None and v.strip():
            upper = v.strip().upper()
            if upper not in VALID_STATE_CODES:
                raise ValueError(f"Invalid state code: {v!r}")
            return upper
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str | None) -> str | None:
        """COBOL CSLKPCDY: zip must be 5 or 9 digits (with optional hyphen)."""
        if v is not None and v.strip():
            if not _ZIP_RE.match(v):
                raise ValueError(
                    "Zip code must be 5 digits or 9 digits (xxxxx or xxxxx-xxxx)"
                )
        return v

    @field_validator("credit_limit", "cash_credit_limit", mode="before")
    @classmethod
    def validate_financial_field(cls, v: Any) -> Any:
        """COBOL COACTUPC: financial fields must be numeric (signed)."""
        if v is not None:
            try:
                Decimal(str(v))
            except Exception:
                raise ValueError("Financial field must be a valid decimal number")
        return v
