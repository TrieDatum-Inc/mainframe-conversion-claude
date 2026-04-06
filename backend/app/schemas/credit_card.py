"""
Credit card schemas.

COBOL origin:
  COCRDLIC (card list)   — CardListItem, CardListResponse
  COCRDSLC (card view)   — CardDetailResponse
  COCRDUPC (card update) — CardUpdateRequest

Key COCRDUPC rules:
  - account_id is PROT — NOT included in update request
  - CRDNAME must be alpha-only (INSPECT CONVERTING equivalent)
  - EXPMON 1-12, EXPYEAR 1950-2099
  - optimistic_lock_version = updated_at from GET response
  - EXPDAY (hidden DRK PROT FSET) preserved in state and sent back
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class CardListItem(BaseModel):
    """
    Single row in card list — COCRDLIC CCRDLIA BMS map row fields.
    card_number_masked for PCI-DSS display; card_number for API navigation.
    """
    card_number: str            # Full card number (for navigation links)
    card_number_masked: str     # CRDNUMn — ************XXXX display
    account_id: int             # ACCTNOn
    active_status: str          # CRDSTSn — Y/N

    model_config = {"from_attributes": True}


class CardListResponse(BaseModel):
    """
    Paginated card list — COCRDLIC.
    page_size=7 matches WS-MAX-SCREEN-LINES=7 in original COCRDLIC.
    """
    items: list[CardListItem]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool


class CardDetailResponse(BaseModel):
    """
    Card detail response — COCRDSLC / COCRDUPC.
    updated_at used as optimistic_lock_version in PUT (replaces CCUP-OLD-DETAILS snapshot).
    ACCTSID is PROT in COCRDUPC — account_id shown read-only.
    """
    card_number: str            # CARDSID
    account_id: int             # ACCTSID — PROT in COCRDUPC
    customer_id: int
    card_embossed_name: Optional[str] = None   # CRDNAME
    active_status: str                         # CRDSTCD — Y/N
    expiration_date: Optional[str] = None      # full date YYYY-MM-DD for display
    expiration_month: Optional[int] = None     # EXPMON — 1-12
    expiration_year: Optional[int] = None      # EXPYEAR
    expiration_day: Optional[int] = None       # EXPDAY — DRK PROT FSET hidden field
    updated_at: str                            # ISO datetime = optimistic_lock_version

    model_config = {"from_attributes": True}


class CardUpdateRequest(BaseModel):
    """
    Card update request — COCRDUPC CCRDUPA editable fields.

    account_id is intentionally NOT here — ACCTSID is PROT in COCRDUPC.
    optimistic_lock_version = updated_at from GET (replaces CCUP-OLD-DETAILS).
    """
    card_embossed_name: str = Field(
        ..., min_length=1, max_length=50,
        description="CRDNAME — alpha-only validated (INSPECT CONVERTING in COCRDUPC)",
    )
    active_status: Literal["Y", "N"] = Field(
        ..., description="CRDSTCD — Y=Active, N=Inactive",
    )
    expiration_month: int = Field(
        ..., ge=1, le=12,
        description="EXPMON — 1-12",
    )
    expiration_year: int = Field(
        ..., ge=1950, le=2099,
        description="EXPYEAR — 1950-2099",
    )
    expiration_day: Optional[int] = Field(
        None, ge=1, le=31,
        description="EXPDAY — hidden DRK PROT FSET field; pass back unchanged",
    )
    optimistic_lock_version: str = Field(
        ...,
        description="ISO datetime from GET response (replaces CCUP-OLD-DETAILS snapshot)",
    )

    @field_validator("card_embossed_name")
    @classmethod
    def validate_alpha_only(cls, value: str) -> str:
        """
        COBOL origin: COCRDUPC uses INSPECT CONVERTING to validate alpha-only name.
        Only letters and spaces permitted.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("Embossed name cannot be blank")
        if not all(c.isalpha() or c.isspace() for c in stripped):
            raise ValueError("Embossed name must contain only letters and spaces")
        return stripped.upper()
