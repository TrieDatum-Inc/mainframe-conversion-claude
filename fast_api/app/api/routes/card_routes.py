"""
Card routes.
Maps COCRDLIC (CCLI), COCRDSLC (CCDL), COCRDUPC (CCUP) programs.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_user
from app.core.exceptions import (
    BusinessValidationError,
    DuplicateKeyError,
    ResourceNotFoundError,
)
from app.domain.services.card_service import (
    create_card,
    get_card_detail,
    list_cards,
    update_card,
)
from app.infrastructure.database import get_db
from app.schemas.auth_schemas import UserContext
from app.schemas.card_schemas import (
    CardCreateRequest,
    CardListResponse,
    CardUpdateRequest,
    CardView,
)

router = APIRouter(prefix="/cards", tags=["Cards (COCRDLIC/COCRDSLC/COCRDUPC)"])


@router.get(
    "",
    response_model=CardListResponse,
    status_code=status.HTTP_200_OK,
    summary="List cards (COCRDLIC - CCLI)",
    description="""
    Paginated credit card list.

    COCRDLIC supports two modes:
    - Admin mode (no filter): all cards across all accounts
    - Filtered mode: cards for a specific account

    Pagination: 7 rows per page (WS-MAX-SCREEN-LINES in COCRDLIC).
    Navigation: forward (PF8) and backward (PF7).

    Selection from original screen:
    - 'S' = view (COCRDSLC) -> use GET /cards/{card_num}
    - 'U' = update (COCRDUPC) -> use PUT /cards/{card_num}
    """,
)
async def list_cards_endpoint(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    start_card_num: Optional[str] = Query(None, max_length=16, description="Start key for forward pagination"),
    end_card_num: Optional[str] = Query(None, max_length=16, description="End key for backward pagination"),
    direction: str = Query("forward", description="'forward' (PF8) or 'backward' (PF7)"),
    page_size: int = Query(7, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> CardListResponse:
    return await list_cards(
        db=db,
        page_size=page_size,
        start_card_num=start_card_num,
        account_id_filter=account_id,
        direction=direction,
        end_card_num=end_card_num,
    )


@router.get(
    "/{card_num}",
    response_model=CardView,
    status_code=status.HTTP_200_OK,
    summary="View card detail (COCRDSLC - CCDL)",
    description="Read-only card detail display.",
)
async def get_card(
    card_num: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> CardView:
    try:
        return await get_card_detail(card_num, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )


@router.put(
    "/{card_num}",
    response_model=CardView,
    status_code=status.HTTP_200_OK,
    summary="Update card (COCRDUPC - CCUP)",
    description="""
    Update card record.

    COCRDUPC 7-state machine:
    - NOT-FETCHED -> SHOW -> CHANGES-NOT-OK -> OK-NOT-CONFIRMED -> DONE/LOCK-ERR/FAILED

    Optimistic concurrency: concurrent modifications return HTTP 409.
    Editable fields: embossed_name, expiration_date, active_status.
    """,
)
async def update_card_endpoint(
    card_num: str,
    request: CardUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> CardView:
    try:
        return await update_card(card_num, request, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )
    except BusinessValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "CDERR422", "message": exc.message},
        )


@router.post(
    "",
    response_model=CardView,
    status_code=status.HTTP_201_CREATED,
    summary="Create card",
    description="Create a new card with cross-reference (CBIMPORT equivalent).",
)
async def create_card_endpoint(
    request: CardCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> CardView:
    try:
        return await create_card(request, db)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "CDERR070", "message": exc.message},
        )
