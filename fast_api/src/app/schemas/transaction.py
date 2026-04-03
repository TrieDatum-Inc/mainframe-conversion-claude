import re
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import PaginationMeta


# ---------------------------------------------------------------------------
# List / read schemas
# ---------------------------------------------------------------------------

class TransactionListItem(BaseModel):
    """Minimal fields shown on COTRN0A screen (list row)."""

    tran_id: str
    tran_orig_ts: datetime
    tran_desc: str
    tran_amt: Decimal

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Response for GET /api/transactions — mirrors COTRN00C paginated output."""

    items: list[TransactionListItem]
    pagination: PaginationMeta


class TransactionDetail(BaseModel):
    """Full detail fields shown on COTRN1A screen."""

    tran_id: str
    tran_type_cd: str
    tran_cat_cd: str
    tran_source: str
    tran_desc: str
    tran_amt: Decimal
    tran_merchant_id: str
    tran_merchant_name: str
    tran_merchant_city: str
    tran_merchant_zip: str
    tran_card_num: str
    tran_orig_ts: datetime
    tran_proc_ts: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Validate (step 1: enter data — before confirmation)
# ---------------------------------------------------------------------------

class TransactionValidateRequest(BaseModel):
    """
    Input fields for COTRN02C VALIDATE-INPUT-KEY-FIELDS + VALIDATE-INPUT-DATA-FIELDS.
    Either acct_id or card_num must be provided (not both, not neither).
    """

    # Key identification — one of these must be provided (mirrors COTRN02C key entry)
    acct_id: str | None = Field(
        None,
        description="Account ID (11 digits). Mutually exclusive with card_num.",
        max_length=11,
    )
    card_num: str | None = Field(
        None,
        description="Card number (16 digits). Mutually exclusive with acct_id.",
        max_length=16,
    )

    # Transaction data fields (all required)
    tran_type_cd: str = Field(..., max_length=2, description="Transaction type code (numeric)")
    tran_cat_cd: str = Field(..., max_length=4, description="Category code (numeric)")
    tran_source: str = Field(..., max_length=10, description="Source channel")
    tran_desc: str = Field(..., max_length=100, description="Transaction description")
    tran_amt: str = Field(
        ...,
        max_length=12,
        description="Amount in format ±99999999.99",
    )
    tran_orig_dt: str = Field(
        ...,
        max_length=10,
        description="Origination date YYYY-MM-DD",
    )
    tran_proc_dt: str = Field(
        ...,
        max_length=10,
        description="Processing date YYYY-MM-DD",
    )
    tran_merchant_id: str = Field(..., max_length=9, description="Merchant ID (numeric)")
    tran_merchant_name: str = Field(..., max_length=50)
    tran_merchant_city: str = Field(..., max_length=50)
    tran_merchant_zip: str = Field(..., max_length=10)

    @model_validator(mode="after")
    def validate_key_fields(self) -> "TransactionValidateRequest":
        if not self.acct_id and not self.card_num:
            raise ValueError("Account or Card Number must be entered")
        return self

    @field_validator("acct_id")
    @classmethod
    def acct_id_must_be_numeric(cls, v: str | None) -> str | None:
        if v is not None and not v.strip().isdigit():
            raise ValueError("Account ID must be Numeric")
        return v

    @field_validator("card_num")
    @classmethod
    def card_num_must_be_numeric(cls, v: str | None) -> str | None:
        if v is not None and not v.strip().isdigit():
            raise ValueError("Card Number must be Numeric")
        return v

    @field_validator("tran_type_cd")
    @classmethod
    def tran_type_cd_must_be_numeric(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Type CD can NOT be empty")
        if not v.strip().isdigit():
            raise ValueError("Type CD must be Numeric")
        return v

    @field_validator("tran_cat_cd")
    @classmethod
    def tran_cat_cd_must_be_numeric(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Category CD can NOT be empty")
        if not v.strip().isdigit():
            raise ValueError("Category CD must be Numeric")
        return v

    @field_validator("tran_source")
    @classmethod
    def tran_source_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Source can NOT be empty")
        return v

    @field_validator("tran_desc")
    @classmethod
    def tran_desc_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description can NOT be empty")
        return v

    @field_validator("tran_amt")
    @classmethod
    def validate_amount_format(cls, v: str) -> str:
        """
        Mirrors COTRN02C VALIDATE-INPUT-DATA-FIELDS amount check:
          pos 1  : '-' or '+'
          pos 2-9: numeric
          pos 10 : '.'
          pos 11-12: numeric
        Error: 'Amount should be in format -99999999.99'
        """
        if not v.strip():
            raise ValueError("Amount can NOT be empty")
        pattern = r"^[+\-]\d{8}\.\d{2}$"
        if not re.match(pattern, v.strip()):
            raise ValueError("Amount should be in format -99999999.99")
        return v.strip()

    @field_validator("tran_orig_dt")
    @classmethod
    def validate_orig_date_format(cls, v: str) -> str:
        """
        Mirrors COTRN02C date format check for TORIGDTI:
          YYYY-MM-DD format, positions 1-4 numeric, pos 5 '-', etc.
        """
        if not v.strip():
            raise ValueError("Orig Date can NOT be empty")
        _validate_date_format(v.strip(), "Orig Date")
        return v.strip()

    @field_validator("tran_proc_dt")
    @classmethod
    def validate_proc_date_format(cls, v: str) -> str:
        """Mirrors COTRN02C date format check for TPROCDTI."""
        if not v.strip():
            raise ValueError("Proc Date can NOT be empty")
        _validate_date_format(v.strip(), "Proc Date")
        return v.strip()

    @field_validator("tran_merchant_id")
    @classmethod
    def merchant_id_must_be_numeric(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Merchant ID can NOT be empty")
        if not v.strip().isdigit():
            raise ValueError("Merchant ID must be Numeric")
        return v

    @field_validator("tran_merchant_name")
    @classmethod
    def merchant_name_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Merchant Name can NOT be empty")
        return v

    @field_validator("tran_merchant_city")
    @classmethod
    def merchant_city_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Merchant City can NOT be empty")
        return v

    @field_validator("tran_merchant_zip")
    @classmethod
    def merchant_zip_required(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Merchant Zip can NOT be empty")
        return v


def _validate_date_format(date_str: str, field_label: str) -> None:
    """
    Validate YYYY-MM-DD format and calendar correctness.
    Mirrors CSUTLDTC call in COTRN02C — message '2513' (tolerated) maps to
    the scenario where Python datetime.strptime succeeds, so no special case
    is needed here.
    """
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_str):
        raise ValueError(f"{field_label} should be in format YYYY-MM-DD")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_label} - Not a valid date")


# ---------------------------------------------------------------------------
# Create (step 2: confirmed add — Y pressed)
# ---------------------------------------------------------------------------

class TransactionCreate(TransactionValidateRequest):
    """
    Extends validate request with the Y confirmation flag.
    Mirrors the COTRN02C confirm step — only reached when user enters 'Y'.
    """

    confirm: str = Field(
        ...,
        max_length=1,
        description="Confirmation: must be 'Y' or 'y'",
    )

    @field_validator("confirm")
    @classmethod
    def confirm_must_be_yes(cls, v: str) -> str:
        if v.upper() == "Y":
            return v.upper()
        if v.upper() == "N" or not v.strip():
            raise ValueError("Confirm to add this transaction")
        raise ValueError("Invalid value. Valid values are (Y/N)")


# ---------------------------------------------------------------------------
# Validate response (card/account lookup result returned to UI)
# ---------------------------------------------------------------------------

class TransactionValidateResponse(BaseModel):
    """
    Returned after successful validation (before actual creation).
    The UI uses this to pre-populate confirmed card_num or acct_id.
    """

    resolved_card_num: str
    resolved_acct_id: str
    acct_active: bool
    normalized_amt: str  # amount formatted as +99999999.99 or -99999999.99
