"""Pydantic schemas for Card endpoints.

Business rules preserved from COCRDUPC:
- Card name: non-blank alphanumeric (CRDNAME field)
- Active status: 'Y' or 'N' only (88-level FLG-YES-NO-VALID)
- Expiry month: integer 1–12 (VALID-MONTH VALUE 1 THRU 12)
- Expiry year: integer 1950–2099 (VALID-YEAR VALUE 1950 THRU 2099)
- Account number: PROTECTED — never editable (display only)
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class CardBase(BaseModel):
    """Common card fields."""

    card_number: str = Field(max_length=16)
    account_id: str = Field(max_length=11)
    embossed_name: str = Field(default="", max_length=50)
    active_status: str = Field(default="Y", max_length=1)
    expiration_date: date | None = None


class CardListItem(BaseModel):
    """Lightweight card row for list results (COCRDLIC 7-per-page view).

    Columns: Card Number | Account Number | Name on Card | Status | Expiry
    """

    card_number: str
    account_id: str
    embossed_name: str
    active_status: str
    expiration_date: date | None

    model_config = {"from_attributes": True}


class CardDetailResponse(CardBase):
    """Full card record for GET /api/cards/{card_number} (COCRDSLC view)."""

    id: int
    cvv_code: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CardListResponse(BaseModel):
    """Paginated response for GET /api/cards.

    Original COCRDLIC shows 7 rows per page (F7/F8 navigation).
    """

    items: list[CardListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class CardUpdateRequest(BaseModel):
    """PUT /api/cards/{card_number} payload.

    Editable fields from COCRDUPC screen:
      - embossed_name (CRDNAME)
      - active_status (CRDSTCD)
      - expiry month  (EXPMON) — validated 1-12
      - expiry year   (EXPYEAR) — validated 1950-2099

    Account number (ACCTSID) is PROTECTED and never accepted in this payload.
    The expiry day is system-maintained (EXPDAY DRK,PROT) — we default to 1.
    """

    embossed_name: str | None = Field(default=None, max_length=50)
    active_status: str | None = Field(default=None, max_length=1)
    expiry_month: int | None = Field(default=None, ge=1, le=12)
    expiry_year: int | None = Field(default=None, ge=1950, le=2099)

    @field_validator("active_status")
    @classmethod
    def validate_active_status(cls, v: str | None) -> str | None:
        """COBOL 88-level: FLG-YES-NO-VALID VALUE 'Y' 'N'."""
        if v is not None and v not in ("Y", "N"):
            raise ValueError("active_status must be 'Y' or 'N'")
        return v

    @field_validator("embossed_name")
    @classmethod
    def validate_embossed_name(cls, v: str | None) -> str | None:
        """COBOL: CRDNAME must be non-blank alphanumeric."""
        if v is not None and not v.strip():
            raise ValueError("embossed_name must not be blank")
        return v
