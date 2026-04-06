"""
Pydantic schemas for authorization request/response validation.

Mirrors the field layouts from:
- CCPAURQY (MQ authorization request message)
- CCPAURLY (MQ authorization response message)
- COPAU00 BMS screen fields (summary view)
- COPAU01 BMS screen fields (detail view)
"""

from datetime import date, time
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Decline reason codes — from COPAUS1C 10-entry lookup table
# ---------------------------------------------------------------------------

DECLINE_REASON_DESCRIPTIONS: dict[str, str] = {
    "00": "APPROVED",
    "31": "INVALID CARD",
    "41": "INSUFFICNT FUND",
    "42": "CARD NOT ACTIVE",
    "43": "ACCOUNT CLOSED",
    "44": "EXCED DAILY LMT",
    "51": "CARD FRAUD",
    "52": "MERCHANT FRAUD",
    "53": "LOST CARD",
    "90": "UNKNOWN",
}


# ---------------------------------------------------------------------------
# Authorization Processing (POST /api/authorizations/process)
# Replaces MQ CCPAURQY message layout from COPAUA0C
# ---------------------------------------------------------------------------


class AuthorizationProcessRequest(BaseModel):
    """Authorization request payload. Maps to CCPAURQY MQ message."""

    card_number: str = Field(..., min_length=13, max_length=16, description="Card number (PAN)")
    card_expiry: str = Field(..., pattern=r"^\d{2}/\d{2}$", description="Card expiry MM/YY")
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    auth_type: str = Field(default="SALE", max_length=4, description="Authorization type")
    message_type: str = Field(default="0110", max_length=6, description="ISO 8583 message type")
    pos_entry_mode: str = Field(default="0101", max_length=4, description="POS entry mode")
    processing_code: str = Field(default="000000", max_length=6, description="Processing code")
    mcc_code: str = Field(default="", max_length=4, description="Merchant category code")
    merchant_name: str = Field(default="", max_length=25, description="Merchant name")
    merchant_id: str = Field(default="", max_length=15, description="Merchant ID")
    merchant_city: str = Field(default="", max_length=25, description="Merchant city")
    merchant_state: str = Field(default="", max_length=2, description="Merchant state")
    merchant_zip: str = Field(default="", max_length=10, description="Merchant ZIP code")

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: str) -> str:
        """Card number must be numeric."""
        if not v.isdigit():
            raise ValueError("Card number must contain only digits")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Amount must be positive with at most 2 decimal places."""
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v.quantize(Decimal("0.01"))


class AuthorizationProcessResponse(BaseModel):
    """Authorization response payload. Maps to CCPAURLY MQ message."""

    transaction_id: str
    auth_response: str = Field(description="A=Approved, D=Declined")
    auth_response_code: str
    auth_response_reason: str
    auth_code: str
    transaction_amount: Decimal
    approved_amount: Decimal
    card_number: str
    decline_reason: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Authorization Detail Response
# Maps to COPAU01 BMS screen fields (COPAUS1C)
# ---------------------------------------------------------------------------


class AuthorizationDetailResponse(BaseModel):
    """Full authorization detail. Maps to COPAU01 BMS screen output fields."""

    id: int
    summary_id: int
    card_number: str
    auth_date: date
    auth_time: time
    auth_type: str
    card_expiry: str
    message_type: str
    auth_response_code: str
    auth_response_reason: str
    auth_code: str
    transaction_amount: Decimal
    approved_amount: Decimal
    pos_entry_mode: str
    auth_source: str
    mcc_code: str
    merchant_name: str
    merchant_id: str
    merchant_city: str
    merchant_state: str
    merchant_zip: str
    transaction_id: str
    match_status: str
    fraud_status: Optional[str]
    fraud_report_date: Optional[date]
    processing_code: str

    # Derived field: human-readable decline reason from code lookup
    decline_reason_description: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Authorization Summary Response
# Maps to COPAU00 BMS screen fields (COPAUS0C)
# Includes account context from VSAM ACCTDAT + CUSTDAT
# ---------------------------------------------------------------------------


class AuthorizationSummaryResponse(BaseModel):
    """
    Account-level authorization summary.
    Maps to COPAU00 BMS screen account context section (rows 5-12).
    """

    id: int
    account_id: str
    customer_id: str
    auth_status: str
    credit_limit: Decimal
    cash_limit: Decimal
    credit_balance: Decimal
    cash_balance: Decimal
    approved_count: int
    declined_count: int
    approved_amount: Decimal
    declined_amount: Decimal

    model_config = {"from_attributes": True}


class AuthorizationSummaryListItem(BaseModel):
    """Lightweight summary for list views."""

    id: int
    account_id: str
    customer_id: str
    auth_status: str
    approved_count: int
    declined_count: int
    approved_amount: Decimal
    declined_amount: Decimal

    model_config = {"from_attributes": True}


class PaginatedDetailResponse(BaseModel):
    """Paginated list of authorization details. Maps to COPAU00 rows 16-20 (5 per page)."""

    summary: AuthorizationSummaryResponse
    details: List[AuthorizationDetailResponse]
    page: int
    page_size: int
    total_count: int
    total_pages: int

    model_config = {"from_attributes": True}


class AuthorizationListResponse(BaseModel):
    """Top-level list of authorization summaries with pagination."""

    items: List[AuthorizationSummaryListItem]
    page: int
    page_size: int
    total_count: int
    total_pages: int


# ---------------------------------------------------------------------------
# Purge Request/Response (POST /api/authorizations/purge)
# Replaces batch CBPAUP0C — admin only
# ---------------------------------------------------------------------------


class PurgeRequest(BaseModel):
    """Purge expired authorization details older than expiry_days."""

    expiry_days: int = Field(
        default=5,
        ge=1,
        le=365,
        description="Purge details older than this many days (default 5, maps to P-EXPIRY-DAYS in CBPAUP0C)",
    )


class PurgeResponse(BaseModel):
    """Result of purge operation."""

    details_purged: int
    summaries_purged: int
    expiry_days: int
    message: str
