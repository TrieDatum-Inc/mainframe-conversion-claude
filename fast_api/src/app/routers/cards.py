"""
HTTP route handlers for the Credit Card module.
GET  /api/cards                → COCRDLIC (CCLI)
GET  /api/cards/{card_num}     → COCRDSLC (CCDL)
PUT  /api/cards/{card_num}     → COCRDUPC (CCUP)
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.card_repository import CardRepository
from app.schemas.card import CardDetail, CardListResponse, CardUpdateRequest, CardUpdateResponse
from app.services.card_service import CardService
from app.utils.exceptions import CardNotFoundError, CardUpdateLockError, ConcurrentModificationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cards", tags=["cards"])


def _get_card_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CardService:
    return CardService(CardRepository(db))


@router.get("", response_model=CardListResponse, summary="List credit cards (paginated)")
async def list_cards(
    service: Annotated[CardService, Depends(_get_card_service)],
    cursor: Annotated[str | None, Query(description="Card number to start from (STARTBR GTEQ cursor)")] = None,
    acct_id: Annotated[str | None, Query(description="Filter by account ID (11-digit numeric)", min_length=11, max_length=11)] = None,
    card_num_filter: Annotated[str | None, Query(description="Filter by exact card number (16-digit numeric)", min_length=16, max_length=16)] = None,
    page_size: Annotated[int, Query(description="Records per page (default 7)", ge=1, le=50)] = 7,
    page: Annotated[int, Query(description="Current page number (informational)", ge=1)] = 1,
) -> CardListResponse:
    try:
        return await service.list_cards(cursor=cursor, page_size=page_size, acct_id=acct_id, card_num_filter=card_num_filter, page=page)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/{card_num}", response_model=CardDetail, summary="Get credit card detail")
async def get_card_detail(card_num: str, service: Annotated[CardService, Depends(_get_card_service)]) -> CardDetail:
    try:
        return await service.get_card_detail(card_num)
    except CardNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{card_num}", response_model=CardUpdateResponse, summary="Update credit card details")
async def update_card(
    card_num: str,
    request: CardUpdateRequest,
    service: Annotated[CardService, Depends(_get_card_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CardUpdateResponse:
    try:
        result = await service.update_card(card_num=card_num, request=request)
        await db.commit()
        return result
    except CardNotFoundError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConcurrentModificationError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Record was changed by another user since last read. Please refresh and try again.") from exc
    except CardUpdateLockError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Changes unsuccessful. Please try again.") from exc
