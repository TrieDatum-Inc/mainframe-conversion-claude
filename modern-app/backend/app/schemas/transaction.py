"""Pydantic schemas for transaction request / response validation.

Field constraints directly mirror COBOL BMS screen lengths and CVTRA05Y record layout.
"""

import re
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Constants matching COBOL field lengths (from CVTRA05Y and BMS definitions)
# ---------------------------------------------------------------------------
TRANSACTION_ID_LEN = 16
CARD_NUMBER_LEN = 16
ACCOUNT_ID_LEN = 11
TYPE_CODE_LEN = 2
CATEGORY_CODE_MAX = 4
SOURCE_MAX = 10
DESCRIPTION_MAX = 100
MERCHANT_ID_LEN = 9
MERCHANT_NAME_MAX = 50
MERCHANT_CITY_MAX = 50
MERCHANT_ZIP_MAX = 10

# TRAN-AMT: sign + 8 digits + decimal + 2 digits → range -99999999.99 to +99999999.99
AMOUNT_MAX = Decimal("99999999.99")
AMOUNT_MIN = Decimal("-99999999.99")


class TransactionBase(BaseModel):
    """Shared fields for transaction read/write operations."""

    type_code: str = Field(..., max_length=TYPE_CODE_LEN, description="Transaction type (e.g. '01'=Purchase, '02'=Payment)")
    category_code: str = Field(..., max_length=CATEGORY_CODE_MAX, description="Transaction category code (4 digits)")
    source: str = Field(default="", max_length=SOURCE_MAX, description="Transaction source (e.g. 'POS TERM')")
    description: str = Field(default="", max_length=DESCRIPTION_MAX, description="Transaction description")
    amount: Decimal = Field(..., description="Signed amount, range -99999999.99 to +99999999.99")
    merchant_id: str = Field(default="", max_length=MERCHANT_ID_LEN, description="Merchant ID (all numeric, 9 chars)")
    merchant_name: str = Field(default="", max_length=MERCHANT_NAME_MAX)
    merchant_city: str = Field(default="", max_length=MERCHANT_CITY_MAX)
    merchant_zip: str = Field(default="", max_length=MERCHANT_ZIP_MAX)
    card_number: str = Field(..., max_length=CARD_NUMBER_LEN, description="16-digit card number")
    original_timestamp: datetime
    processing_timestamp: datetime

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Enforce COBOL amount format: S9(9)V99 — max 8 integer digits + 2 decimal."""
        if v < AMOUNT_MIN or v > AMOUNT_MAX:
            raise ValueError(
                f"Amount must be between {AMOUNT_MIN} and {AMOUNT_MAX} "
                "(format: -99999999.99)"
            )
        return v

    @field_validator("merchant_id")
    @classmethod
    def validate_merchant_id_numeric(cls, v: str) -> str:
        """COBOL rule: TRAN-MERCHANT-ID must be all numeric."""
        if v and not v.isdigit():
            raise ValueError("Merchant ID must contain only digits")
        return v

    @field_validator("type_code")
    @classmethod
    def validate_type_code(cls, v: str) -> str:
        """Strip and upper-case type code."""
        return v.strip()

    @field_validator("category_code")
    @classmethod
    def validate_category_code(cls, v: str) -> str:
        """Strip category code."""
        return v.strip()


class TransactionCreate(BaseModel):
    """Request body for POST /api/transactions (COTRN02C add-transaction).

    Either account_id or card_number must be provided; the missing one is resolved
    via the card-to-account cross-reference table (CCXREF / CXACAIX).
    """

    account_id: str | None = Field(
        default=None,
        max_length=ACCOUNT_ID_LEN,
        description="11-digit account ID (provide account_id OR card_number)",
    )
    card_number: str | None = Field(
        default=None,
        max_length=CARD_NUMBER_LEN,
        description="16-digit card number (provide account_id OR card_number)",
    )
    type_code: str = Field(..., max_length=TYPE_CODE_LEN)
    category_code: str = Field(..., max_length=CATEGORY_CODE_MAX)
    source: str = Field(default="", max_length=SOURCE_MAX)
    description: str = Field(default="", max_length=DESCRIPTION_MAX)
    amount: Decimal = Field(..., description="Signed decimal, format: -99999999.99")
    original_date: date = Field(..., description="Original transaction date (YYYY-MM-DD)")
    processing_date: date = Field(..., description="Processing date (YYYY-MM-DD)")
    merchant_id: str = Field(default="", max_length=MERCHANT_ID_LEN)
    merchant_name: str = Field(default="", max_length=MERCHANT_NAME_MAX)
    merchant_city: str = Field(default="", max_length=MERCHANT_CITY_MAX)
    merchant_zip: str = Field(default="", max_length=MERCHANT_ZIP_MAX)
    # COBOL CONFIRM field: must be 'Y' to actually write the record
    confirmed: bool = Field(
        default=False,
        description="Set to true to commit the transaction (mirrors COBOL CONFIRM='Y')",
    )

    @model_validator(mode="after")
    def require_account_or_card(self) -> "TransactionCreate":
        """COBOL rule: either Account ID or Card Number must be provided."""
        if not self.account_id and not self.card_number:
            raise ValueError("Either account_id or card_number must be provided")
        return self

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v < AMOUNT_MIN or v > AMOUNT_MAX:
            raise ValueError(
                f"Amount must be between {AMOUNT_MIN} and {AMOUNT_MAX} "
                "(format: -99999999.99)"
            )
        return v

    @field_validator("merchant_id")
    @classmethod
    def validate_merchant_id_numeric(cls, v: str) -> str:
        if v and not v.isdigit():
            raise ValueError("Merchant ID must contain only digits")
        return v

    @field_validator("processing_date")
    @classmethod
    def validate_processing_date(cls, v: date) -> date:
        """Processing date must be a valid calendar date (validated by Python already)."""
        return v

    @field_validator("original_date")
    @classmethod
    def validate_original_date(cls, v: date) -> date:
        """Original date must be a valid calendar date."""
        return v


class TransactionListItem(BaseModel):
    """Single row in the transaction list (COTRN00C — 10 rows per page)."""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    card_number: str
    description: str
    amount: Decimal
    # Formatted date for display — mirrors COBOL MM/DD/YY display format
    original_date: str


class TransactionPage(BaseModel):
    """Paginated list response for GET /api/transactions."""

    items: list[TransactionListItem]
    page: int
    page_size: int
    total: int
    has_next: bool
    has_prev: bool


class TransactionDetail(BaseModel):
    """Full transaction detail (COTRN01C — all 13 output fields)."""

    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    card_number: str
    type_code: str
    category_code: str
    source: str
    description: str
    amount: Decimal
    original_timestamp: datetime
    processing_timestamp: datetime
    merchant_id: str
    merchant_name: str
    merchant_city: str
    merchant_zip: str
    created_at: datetime
    updated_at: datetime
