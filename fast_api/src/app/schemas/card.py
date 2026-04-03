"""
Pydantic schemas for Credit Card endpoints.
Validation rules mirror the COBOL field-level edits exactly.
"""
import re
from datetime import date, datetime
from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator


def _validate_card_num(v: str) -> str:
    v = v.strip()
    if not re.fullmatch(r"\d{16}", v):
        raise ValueError("Card number must be exactly 16 digits")
    return v


def _validate_acct_id(v: str) -> str:
    v = v.strip()
    if not re.fullmatch(r"\d{11}", v):
        raise ValueError("Account ID must be exactly 11 digits")
    return v


class CardListItem(BaseModel):
    card_num: str
    card_acct_id: str
    card_active_status: str
    model_config = {"from_attributes": True}


class CardListResponse(BaseModel):
    items: list[CardListItem]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    has_next_page: bool
    next_cursor: str | None = None
    prev_cursor: str | None = None
    total_on_page: int


class CardDetail(BaseModel):
    card_num: str
    card_acct_id: str
    card_cvv_cd: str | None = None
    card_embossed_name: str | None = None
    card_active_status: str
    expiry_month: int | None = None
    expiry_year: int | None = None
    expiry_day: int | None = None
    updated_at: datetime
    model_config = {"from_attributes": True}


class CardUpdateRequest(BaseModel):
    """
    PUT /api/cards/{card_num} body.
    Only editable fields from COCRDUPC Phase 2. Expiry day NOT sent by client.
    updated_at is the optimistic-lock token (replaces COBOL CVV+name+expiry+status snapshot).
    """
    card_embossed_name: Annotated[str, Field(min_length=1, max_length=50)]
    card_active_status: Annotated[str, Field(min_length=1, max_length=1)]
    expiry_month: Annotated[int, Field(ge=1, le=12)]
    expiry_year: Annotated[int, Field(ge=1950, le=2099)]
    updated_at: datetime

    @field_validator("card_embossed_name")
    @classmethod
    def name_must_be_alphabetic(cls, v: str) -> str:
        """Mirrors COBOL 1230-EDIT-NAME INSPECT CONVERTING check."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Card name not provided")
        if not re.fullmatch(r"[A-Za-z ]+", stripped):
            raise ValueError("Card name can only contain alphabets and spaces")
        return stripped.upper()

    @field_validator("card_active_status")
    @classmethod
    def status_must_be_y_or_n(cls, v: str) -> str:
        """Mirrors COBOL 1240-EDIT-CARDSTATUS FLG-YES-NO-VALID VALUES 'Y', 'N'."""
        v = v.upper()
        if v not in ("Y", "N"):
            raise ValueError("Card Active Status must be Y or N")
        return v


class CardUpdateResponse(BaseModel):
    card_num: str
    card_acct_id: str
    card_embossed_name: str | None
    card_active_status: str
    expiry_month: int | None
    expiry_year: int | None
    expiry_day: int | None
    updated_at: datetime
    message: str = "Changes committed to database"
    model_config = {"from_attributes": True}


class CardListQueryParams(BaseModel):
    cursor: str | None = None
    acct_id: str | None = None
    card_num_filter: str | None = None
    page_size: int = Field(default=7, ge=1, le=50)

    @field_validator("acct_id")
    @classmethod
    def validate_acct_id(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            v = v.strip()
            if not re.fullmatch(r"\d{11}", v):
                raise ValueError("ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER")
        return v

    @field_validator("card_num_filter")
    @classmethod
    def validate_card_num_filter(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            v = v.strip()
            if not re.fullmatch(r"\d{16}", v):
                raise ValueError("CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER")
        return v
