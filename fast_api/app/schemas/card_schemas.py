"""
Pydantic schemas for Credit Card endpoints.

Maps COCRDLIC (list), COCRDSLC (detail view), COCRDUPC (update) screen fields.

COCRDLIC: paginated list (7 rows per page), forward/backward navigation
COCRDSLC: card detail display - read-only
COCRDUPC: card update with 7-state machine and optimistic concurrency
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CardBase(BaseModel):
    """Core card fields from CVACT02Y copybook."""
    embossed_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Embossed name - CARD-EMBOSSED-NAME PIC X(50)",
    )
    expiration_date: Optional[date] = Field(
        default=None,
        description="Card expiration date - CARD-EXPIRAION-DATE PIC X(10) [sic]",
    )
    active_status: str = Field(
        default="Y",
        max_length=1,
        description="Card active status ('Y'/'N') - CARD-ACTIVE-STATUS PIC X(01)",
    )

    @field_validator("active_status")
    @classmethod
    def validate_active_status(cls, v: str) -> str:
        if v not in ("Y", "N"):
            raise ValueError("active_status must be 'Y' or 'N'")
        return v


class CardView(CardBase):
    """
    Card detail view (COCRDSLC).
    Read-only display of all card fields.
    """
    card_num: str = Field(
        ...,
        min_length=16,
        max_length=16,
        description="16-character card number - CARD-NUM PIC X(16)",
    )
    acct_id: int = Field(
        ...,
        gt=0,
        description="Associated account ID - CARD-ACCT-ID PIC 9(11)",
    )
    # CVV not exposed in responses (security)

    model_config = {"from_attributes": True}


class CardListItem(BaseModel):
    """
    Single row in COCRDLIC card list screen.

    COCRDLI BMS map row fields:
      CRDSEL   - selection field (S=view, U=update)
      ACCTNO   - account number
      CRDNUM   - card number
      CRDNAME  - card name (embossed)
      CRDSTCD  - card status
      EXPMON   - expiration month
      EXPYEAR  - expiration year
    """
    card_num: str = Field(..., max_length=16)
    acct_id: int
    embossed_name: Optional[str] = Field(default=None, max_length=50)
    active_status: str = Field(default="Y", max_length=1)
    expiration_date: Optional[date] = None

    model_config = {"from_attributes": True}


class CardListResponse(BaseModel):
    """
    Paginated card list response (COCRDLIC).
    COCRDLIC state: WS-CA-SCREEN-NUM, WS-CA-LAST-PAGE-DISPLAYED
    """
    items: List[CardListItem]
    page: int = Field(default=1, ge=1)
    has_next_page: bool = Field(default=False)
    first_card_num: Optional[str] = None
    last_card_num: Optional[str] = None
    account_filter: Optional[int] = None


class CardUpdateRequest(CardBase):
    """
    Card update request (COCRDUPC).
    COCRDUPC uses 7-state machine with optimistic concurrency:
    - State L: ACUP-CHANGES-OKAYED-LOCK-ERROR (concurrent modification detected)
    - Must supply card_num as path parameter
    """
    pass


class CardCreateRequest(BaseModel):
    """
    Create a new card record.
    Supports CBIMPORT batch import and direct card provisioning.
    """
    card_num: str = Field(
        ...,
        min_length=16,
        max_length=16,
        description="16-character card number - CARD-NUM PIC X(16)",
    )
    acct_id: int = Field(
        ...,
        gt=0,
        description="Account ID to associate this card - CARD-ACCT-ID PIC 9(11)",
    )
    cvv_cd: int = Field(
        ...,
        ge=0,
        le=999,
        description="CVV security code - CARD-CVV-CD PIC 9(03)",
    )
    embossed_name: Optional[str] = Field(default=None, max_length=50)
    expiration_date: Optional[date] = None
    active_status: str = Field(default="Y", max_length=1)
    cust_id: int = Field(
        ...,
        gt=0,
        description="Customer ID for cross-reference - XREF-CUST-ID PIC 9(09)",
    )

    @field_validator("active_status")
    @classmethod
    def validate_active_status(cls, v: str) -> str:
        if v not in ("Y", "N"):
            raise ValueError("active_status must be 'Y' or 'N'")
        return v
