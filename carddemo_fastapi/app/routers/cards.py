"""Card router porting COBOL programs COCRDLIC, COCRDSLC, and COCRDUPC.

COCRDLIC lists cards with STARTBR/READNEXT pagination over the CARDDAT
VSAM file (CVACT02Y.cpy), optionally filtered by account ID.

COCRDSLC displays full card detail for a selected card number.

COCRDUPC allows updating card fields (embossed name, status, expiry).

This router replaces all three screens with REST endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.card import CardDetail, CardListItem, CardUpdate
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services import card_service

router = APIRouter(tags=["cards"])


@router.get("/", response_model=PaginatedResponse[CardListItem])
def list_cards(
    acct_id: Optional[int] = Query(None, description="Filter by account ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(7, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[CardListItem]:
    """List cards with optional account filter and pagination.

    Ports COBOL program COCRDLIC which uses STARTBR/READNEXT to browse
    the CARDDAT VSAM KSDS file with page-size of 7 records per screen.
    """
    return card_service.list_cards(db, acct_id=acct_id, page=page, page_size=page_size)


@router.get("/{card_num}", response_model=CardDetail)
def get_card_detail(
    card_num: str,
    acct_id: Optional[int] = Query(None, description="Account ID context"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> CardDetail:
    """Retrieve full detail for a specific card.

    Ports COBOL program COCRDSLC which reads the CARDDAT VSAM file
    by card number and displays all card fields.
    """
    return card_service.get_card_detail(db, card_num, acct_id=acct_id)


@router.put("/{card_num}", response_model=MessageResponse)
def update_card(
    card_num: str,
    body: CardUpdate,
    acct_id: int = Query(..., description="Account ID (required)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    """Update card fields.

    Ports COBOL program COCRDUPC which validates and rewrites the card
    record in the CARDDAT VSAM file. Requires both card_num and acct_id
    to locate the record.
    """
    return card_service.update_card(db, card_num, acct_id, body.model_dump(exclude_unset=True))
