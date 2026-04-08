"""
Pydantic schemas for card operations (COCRDLIC, COCRDSLC, COCRDUPC).

Maps COCRDLI/COCRDSL BMS maps to request/response schemas.

COCRDLIC: browse cards by account (CARDAIX alt-index browse)
  → GET /api/v1/cards?account_id=X&cursor=Y&limit=N

COCRDSLC: select/view single card
  → GET /api/v1/cards/{card_num}

COCRDUPC: update card (active status, embossed name)
  → PUT /api/v1/cards/{card_num}
"""
from pydantic import BaseModel, Field, field_validator

from app.utils.cobol_compat import cobol_upper


class CardBase(BaseModel):
    """Shared card fields."""

    acct_id: int | None = Field(None, description="CARD-ACCT-ID PIC 9(11)")
    cvv_cd: int | None = Field(None, ge=0, le=999, description="CARD-CVV-CD PIC 9(03)")
    embossed_name: str | None = Field(None, max_length=50, description="CARD-EMBOSSED-NAME PIC X(50)")
    expiration_date: str | None = Field(None, max_length=10, description="CARD-EXPIRAION-DATE PIC X(10) YYYY-MM-DD")
    active_status: str | None = Field(None, max_length=1, description="CARD-ACTIVE-STATUS PIC X(01): Y or N")

    @field_validator("active_status")
    @classmethod
    def validate_active_status(cls, v: str | None) -> str | None:
        """COCRDSLC: CARD-ACTIVE-STATUS 88-level: 'Y'=active, 'N'=inactive."""
        if v is not None and v not in ("Y", "N"):
            raise ValueError("active_status must be 'Y' or 'N'")
        return v


class CardResponse(CardBase):
    """
    Card view response — maps to COCRDSL BMS map SEND MAP output.
    """

    card_num: str = Field(..., description="CARD-NUM PIC X(16)")

    model_config = {"from_attributes": True}


class CardListResponse(BaseModel):
    """
    Paginated card list — maps to COCRDLI BMS map (10 rows per screen).

    Keyset pagination mirrors STARTBR/READNEXT on CARDAIX:
      next_cursor = last card_num on page (use as start for next STARTBR)
    """

    items: list[CardResponse]
    total: int
    next_cursor: str | None = Field(None, description="Keyset cursor: last card_num on this page")
    prev_cursor: str | None = Field(None, description="Keyset cursor: first card_num on this page")


class CardUpdateRequest(BaseModel):
    """
    Card update request — maps to COCRDUPC BMS map RECEIVE MAP.

    Only certain fields are updatable from COCRDUPC:
      CARD-EMBOSSED-NAME and CARD-ACTIVE-STATUS.
    """

    embossed_name: str | None = Field(None, max_length=50, description="CARD-EMBOSSED-NAME PIC X(50)")
    active_status: str | None = Field(None, max_length=1, description="CARD-ACTIVE-STATUS PIC X(01): Y or N")

    @field_validator("active_status")
    @classmethod
    def validate_active_status(cls, v: str | None) -> str | None:
        if v is not None and v not in ("Y", "N"):
            raise ValueError("active_status must be 'Y' or 'N'")
        return v
