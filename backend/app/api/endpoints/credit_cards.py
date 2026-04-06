"""
Credit card API endpoints.

COBOL origin:
  GET /api/v1/cards              → COCRDLIC (paginated card list)
  GET /api/v1/cards/{card_number} → COCRDSLC (card detail view)
  PUT /api/v1/cards/{card_number} → COCRDUPC (card update)

All endpoints are accessible to ALL authenticated users (user_type A or U).
Authentication required via get_current_user dependency.

This is a thin controller layer — all business logic is in credit_card_service.py.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.credit_card import CardDetailResponse, CardListResponse, CardUpdateRequest
from app.services import credit_card_service
from app.api.dependencies import CurrentUser, get_current_user

router = APIRouter(prefix="/cards", tags=["Credit Cards"])


@router.get(
    "",
    response_model=CardListResponse,
    summary="List credit cards (paginated)",
    description=(
        "Paginated list of credit cards with optional account_id and card_number filters. "
        "Replaces COCRDLIC 7-row STARTBR/READNEXT/READPREV browse. "
        "Default page_size=7 matches original COCRDLIC display. "
        "Card numbers masked (last 4 digits only) per PCI-DSS."
    ),
)
async def list_cards(
    account_id: Optional[int] = Query(
        None, description="Filter by account ID — replaces ACCTSID filter in COCRDLIC"
    ),
    card_number: Optional[str] = Query(
        None, description="Filter by exact card number — replaces CARDSID filter in COCRDLIC"
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        7,
        ge=1,
        le=100,
        description="Results per page — default 7 matches COCRDLIC 7-row display",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CardListResponse:
    """
    GET /api/v1/cards

    COBOL: COCRDLIC POPULATE-USER-DATA with STARTBR/READNEXT/READPREV pattern.
    Optional account_id/card_number filters map to ACCTSID/CARDSID search fields.
    """
    return await credit_card_service.list_cards(
        db=db,
        account_id=account_id,
        card_number=card_number,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{card_number}",
    response_model=CardDetailResponse,
    summary="View card detail",
    description=(
        "Fetch full card detail for a given 16-digit card number. "
        "Replaces COCRDSLC PROCESS-ENTER-KEY (READ DATASET(CARDDAT) by CARD-NUM). "
        "Returns updated_at as optimistic_lock_version for use in update requests."
    ),
)
async def get_card(
    card_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CardDetailResponse:
    """
    GET /api/v1/cards/{card_number}

    COBOL: COCRDSLC READ DATASET(CARDDAT) RIDFLD(WS-CARD-NUM).
    Returns 404 if card not found.
    """
    return await credit_card_service.view_card(card_number=card_number, db=db)


@router.put(
    "/{card_number}",
    response_model=CardDetailResponse,
    summary="Update card fields",
    description=(
        "Update card embossed name, active status, and expiration date. "
        "Replaces COCRDUPC UPDATE-CARD (7-state machine). "
        "account_id is read-only — cannot be changed (PROT field in BMS CCRDUPA). "
        "Include optimistic_lock_version from GET response to prevent concurrent updates. "
        "Returns 409 Conflict if record was modified since last fetch."
    ),
)
async def update_card(
    card_number: str,
    request: CardUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> CardDetailResponse:
    """
    PUT /api/v1/cards/{card_number}

    COBOL: COCRDUPC PROCESS-ENTER-KEY:
      - Validate embossed name alpha-only (INSPECT CONVERTING)
      - Validate expiry month 1-12, year 1950-2099
      - Compare CCUP-OLD-DETAILS snapshot → 409 if mismatch (SYNCPOINT ROLLBACK)
      - REWRITE CARDDAT (account_id PROT — not updated)

    Returns updated CardDetailResponse with new updated_at.
    """
    return await credit_card_service.update_card(
        card_number=card_number,
        request=request,
        db=db,
    )
