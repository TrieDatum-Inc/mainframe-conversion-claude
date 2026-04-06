"""
Credit card API endpoints.

GET /api/v1/cards              → COCRDLIC (list, 7 per page)
GET /api/v1/cards/{card_number} → COCRDSLC (view)
PUT /api/v1/cards/{card_number} → COCRDUPC (update)

All endpoints require authentication. No admin restriction.
This is a thin controller layer — all business logic in credit_card_service.py.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.schemas.credit_card import CardDetailResponse, CardListResponse, CardUpdateRequest
from app.services import credit_card_service

router = APIRouter(prefix="/cards", tags=["Credit Cards"])


@router.get(
    "",
    response_model=CardListResponse,
    summary="List credit cards — COCRDLIC",
    description=(
        "Paginated card list. Default page_size=7 matches COCRDLIC WS-MAX-SCREEN-LINES=7. "
        "Card numbers masked in list view (PCI-DSS compliance). "
        "Filter by account_id (ACCTSID) or card_number prefix (CARDSID)."
    ),
)
async def list_cards(
    page: int = Query(1, ge=1),
    page_size: int = Query(7, ge=1, le=100),
    account_id: Optional[int] = Query(None, description="ACCTSID filter"),
    card_number: Optional[str] = Query(None, description="CARDSID prefix filter"),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> CardListResponse:
    """COCRDLIC STARTBR/READNEXT browse → paginated SQL query."""
    return await credit_card_service.list_cards(
        db=db,
        page=page,
        page_size=page_size,
        account_id=account_id,
        card_number=card_number,
    )


@router.get(
    "/{card_number}",
    response_model=CardDetailResponse,
    summary="View credit card — COCRDSLC",
    description=(
        "Fetch a single card record by card number. "
        "Returns updated_at as optimistic_lock_version for use in PUT. "
        "COBOL: EXEC CICS READ DATASET(CARDDAT) RIDFLD(CARD-NUM)."
    ),
)
async def get_card(
    card_number: str,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> CardDetailResponse:
    """COCRDSLC PROCESS-ENTER-KEY → READ DATASET(CARDDAT)."""
    return await credit_card_service.view_card(card_number, db)


@router.put(
    "/{card_number}",
    response_model=CardDetailResponse,
    summary="Update credit card — COCRDUPC",
    description=(
        "Update card fields. account_id is PROTECTED and cannot be changed (ACCTSID PROT). "
        "Validates embossed_name (alpha-only), expiry month (1-12), year (1950-2099). "
        "Returns 409 if optimistic lock version mismatches (CCUP-OLD-DETAILS check). "
        "EXPDAY hidden field preserved across updates."
    ),
)
async def update_card(
    card_number: str,
    request: CardUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> CardDetailResponse:
    """COCRDUPC: optimistic lock → validate → REWRITE DATASET(CARDDAT)."""
    return await credit_card_service.update_card(card_number, request, db)
