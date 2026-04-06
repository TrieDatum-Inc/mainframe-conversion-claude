"""Card API routes.

Maps COBOL programs to REST endpoints:
  COCRDLIC  (GET /api/cards)            — paginated card list (7 per page)
  COCRDSLC  (GET /api/cards/{number})   — card detail view
  COCRDUPC  (PUT /api/cards/{number})   — update card

All endpoints require JWT Bearer authentication (Depends(get_current_user)).

HTTP status code mapping:
  COBOL NOT-FOUND condition    -> 404
  COBOL validation error       -> 422
  COBOL REWRITE ok             -> 200
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.card import CardDetailResponse, CardListResponse, CardUpdateRequest
from app.services import card_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/cards", tags=["Cards"])


@router.get("", response_model=CardListResponse)
async def list_cards(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=7,
        ge=1,
        le=100,
        description="COCRDLIC default: 7 rows per page (F7/F8 paging)",
    ),
    account_id: str | None = Query(
        default=None,
        description="Filter by account ID (ACCTSID in COCRDLIC)",
    ),
    card_number: str | None = Query(
        default=None,
        description="Filter by card number prefix (CARDSID in COCRDLIC)",
    ),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> CardListResponse:
    """List credit cards with optional filters.

    COBOL COCRDLIC: BROWSE CARDDAT or CARDAIX (7 rows per page, F7/F8 nav).
    If account_id provided, uses CARDAIX alternate index by account.
    """
    return await card_service.list_cards(
        db,
        page=page,
        page_size=page_size,
        account_id_filter=account_id,
        card_number_filter=card_number,
    )


@router.get("/{card_number}", response_model=CardDetailResponse)
async def get_card(
    card_number: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> CardDetailResponse:
    """Get card detail by card number.

    COBOL COCRDSLC: READ CARDDAT by CARD-NUM.
    Returns 404 if card not found (COBOL NOTFND).
    """
    detail = await card_service.get_card_detail(db, card_number)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_number!r} not found",
        )
    return detail


@router.put("/{card_number}", response_model=CardDetailResponse)
async def update_card(
    card_number: str,
    payload: CardUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> CardDetailResponse:
    """Update editable card fields.

    COBOL COCRDUPC PF5 flow:
      - Editable: embossed_name (CRDNAME), active_status (CRDSTCD),
                  expiry month (EXPMON 1-12), expiry year (EXPYEAR 1950-2099)
      - Protected: account number (ACCTSID) — never sent in payload

    Returns 404 if card not found.
    Validation errors -> 422 (mirrors COACTUPC inline field highlights).
    """
    updated = await card_service.update_card(db, card_number, payload)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_number!r} not found",
        )
    return updated
