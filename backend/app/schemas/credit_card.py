"""
Pydantic schemas for Credit Card request/response DTOs.

COBOL origin: COCRDLIC (list), COCRDSLC (view), COCRDUPC (update).
BMS maps: CCRDLIA (list), CCRDSLA (view), CCRDUPA (update).

Key design decisions:
  - card_number masked in list responses (last 4 digits only) per PCI-DSS
  - account_id is read-only in update (PROT field in CCRDUPA BMS map)
  - expiration_month/year as separate integers (matching EXPMON/EXPYEAR BMS fields)
  - expiration_day maintained as hidden state (DRK PROT FSET in COCRDUP)
  - optimistic_lock_version = updated_at timestamp (replaces CCUP-OLD-DETAILS snapshot)
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class CardListItem(BaseModel):
    """
    Single row in COCRDLIC card list response.

    Maps CCRDLIA BMS list rows: CRDSELn, ACCTNOn, CRDNUMn, CRDSTSn.
    card_number_masked shows only last 4 digits for PCI-DSS compliance.
    Original COBOL displayed full card number — masked here for security.
    """

    card_number: str = Field(description="Full card number — use card_number_masked for display")
    card_number_masked: str = Field(
        description="CRDNUMn — last 4 digits only: ************XXXX"
    )
    account_id: int = Field(description="ACCTNOn — ACCT-ID 9(11)")
    active_status: str = Field(description="CRDSTSn — CARD-ACTIVE-STATUS X(1); Y/N")

    model_config = {"from_attributes": True}


class CardListResponse(BaseModel):
    """
    Paginated card list — replaces COCRDLIC 7-row STARTBR/READNEXT/READPREV pattern.

    Original COBOL showed exactly 7 rows per page (CRDSTP1–7 as page markers).
    Default page_size=7 matches original; configurable for modern use.
    """

    items: List[CardListItem]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool


class CardDetailResponse(BaseModel):
    """
    Full card detail — replaces COCRDSLC view and COCRDUPC initial display.

    CARDSID → card_number (16-char)
    ACCTSID → account_id (PROT in update — cannot be changed)
    CRDNAME → card_embossed_name
    CRDSTCD → active_status Y/N
    EXPMON → expiration_month 1-12
    EXPYEAR → expiration_year 4-digit
    EXPDAY → expiration_day (hidden DRK PROT FSET in COCRDUP; maintained in frontend state)

    updated_at serves as optimistic_lock_version (replaces CCUP-OLD-DETAILS snapshot).
    """

    card_number: str = Field(description="CARDSID — CARD-NUM X(16)")
    account_id: int = Field(
        description="ACCTSID — PROT in COCRDUPC; cannot be changed in update"
    )
    card_embossed_name: Optional[str] = Field(None, description="CRDNAME — CARD-EMBOSSED-NAME")
    active_status: str = Field(description="CRDSTCD — Y=active, N=inactive")
    expiration_month: int = Field(
        description="EXPMON — extracted from expiration_date; range 1-12"
    )
    expiration_year: int = Field(
        description="EXPYEAR — extracted from expiration_date; range 1950-2099"
    )
    expiration_day: Optional[int] = Field(
        None, description="EXPDAY — DRK PROT FSET hidden field; maintained in state"
    )
    updated_at: datetime = Field(
        description="Use as optimistic_lock_version in PUT request — replaces CCUP-OLD-DETAILS"
    )

    model_config = {"from_attributes": True}


class CardUpdateRequest(BaseModel):
    """
    Card update request — maps CCRDUPA BMS editable fields only.

    account_id is NOT included — it is PROT (cannot be changed) in COCRDUPC.
    COCRDUPC validates:
      - card_embossed_name: alpha-only (INSPECT CONVERTING)
      - expiration_month: 1-12
      - expiration_year: 1950-2099
      - optimistic_lock_version match (replaces CCUP-OLD-DETAILS snapshot comparison)
        → 409 Conflict if mismatch (replaces COCRDUPC SYNCPOINT ROLLBACK)

    expiration_day is included for hidden state preservation even though not shown in UI.
    """

    card_embossed_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="CRDNAME — alpha-only per COCRDUPC INSPECT CONVERTING validation",
    )
    active_status: Literal["Y", "N"] = Field(
        description="CRDSTCD — CARD-ACTIVE-STATUS; must be Y or N"
    )
    expiration_month: int = Field(
        ..., ge=1, le=12, description="EXPMON — 1-12 per COCRDUPC validation"
    )
    expiration_year: int = Field(
        ..., ge=1950, le=2099, description="EXPYEAR — 1950-2099 per COCRDUPC validation"
    )
    expiration_day: Optional[int] = Field(
        None, ge=1, le=31, description="EXPDAY — hidden field; from GET response state"
    )
    optimistic_lock_version: datetime = Field(
        description=(
            "updated_at from GET response — replaces CCUP-OLD-DETAILS snapshot comparison. "
            "Returns 409 if card was modified by another user since last fetch."
        )
    )
