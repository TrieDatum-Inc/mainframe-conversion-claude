"""
Card endpoints — derived from COCRDLIC, COCRDSLC, COCRDUPC.

Source programs:
  app/cbl/COCRDLIC.cbl — Card List (CICS transaction CC0L)
  app/cbl/COCRDSLC.cbl — Card Select/View (CICS transaction CC0S)
  app/cbl/COCRDUPC.cbl — Card Update (CICS transaction CC0U)

BMS maps: COCRDLI, COCRDSL

Endpoint mapping:
  GET  /api/v1/cards                → COCRDLIC (browse CARDAIX by account or list all)
  GET  /api/v1/cards/{card_num}     → COCRDSLC (read single card)
  PUT  /api/v1/cards/{card_num}     → COCRDUPC (update card fields)
"""
from fastapi import APIRouter, Query

from app.dependencies import CurrentUser, DBSession
from app.schemas.card import CardListResponse, CardResponse, CardUpdateRequest
from app.services.card_service import CardService

router = APIRouter(prefix="/cards", tags=["Cards (COCRDLIC/COCRDSLC/COCRDUPC)"])


@router.get(
    "",
    response_model=CardListResponse,
    summary="List/browse cards (COCRDLIC)",
    responses={
        200: {"description": "Paginated card list"},
    },
)
async def list_cards(
    db: DBSession,
    current_user: CurrentUser,
    account_id: int | None = Query(None, description="Filter by CARD-ACCT-ID (browse CARDAIX)"),
    cursor: str | None = Query(None, description="Keyset cursor — last card_num from previous page"),
    limit: int = Query(10, ge=1, le=100, description="Page size (COCRDLIC: 7 rows per screen)"),
    direction: str = Query("forward", pattern="^(forward|backward)$", description="READNEXT or READPREV"),
) -> CardListResponse:
    """
    Browse cards with optional account filter.

    Derived from COCRDLIC BROWSE-CARDS paragraph:
      EXEC CICS STARTBR FILE('CARDAIX') RIDFLD(CARD-ACCT-ID) GTEQ
      EXEC CICS READNEXT/READPREV FILE('CARDAIX') INTO(CARD-RECORD)

    Keyset pagination on CARD-NUM (the CARDAIX alt-index key is CARD-ACCT-ID,
    browse returns records sorted by CARD-NUM within the account).

    CDEMO-CL00-CARDNUM-FIRST / CDEMO-CL00-CARDNUM-LAST track page boundaries.
    """
    service = CardService(db)
    return await service.list_cards(
        account_id=account_id, cursor=cursor, limit=limit, direction=direction
    )


@router.get(
    "/{card_num}",
    response_model=CardResponse,
    summary="View card details (COCRDSLC)",
    responses={
        200: {"description": "Card details"},
        404: {"description": "Card not found (CICS RESP=13 NOTFND)"},
    },
)
async def get_card(
    card_num: str,
    db: DBSession,
    current_user: CurrentUser,
) -> CardResponse:
    """
    Retrieve card details by card number.

    Derived from COCRDSLC READ-CARD-DATA paragraph:
      EXEC CICS READ FILE('CARDDAT') INTO(CARD-RECORD) RIDFLD(CARD-NUM)

    card_num is CARD-NUM PIC X(16) — padded to exactly 16 characters.
    """
    service = CardService(db)
    return await service.get_card(card_num)


@router.put(
    "/{card_num}",
    response_model=CardResponse,
    summary="Update card (COCRDUPC)",
    responses={
        200: {"description": "Card updated"},
        404: {"description": "Card not found (CICS RESP=13 NOTFND)"},
        422: {"description": "Validation error"},
    },
)
async def update_card(
    card_num: str,
    request: CardUpdateRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> CardResponse:
    """
    Update card fields.

    Derived from COCRDUPC PROCESS-ENTER-KEY → EXEC CICS REWRITE FILE('CARDDAT').

    Updatable fields (per COCRDUPC BMS map):
      - embossed_name (CARD-EMBOSSED-NAME)
      - active_status (CARD-ACTIVE-STATUS: 'Y'/'N')

    Read-then-rewrite pattern: COCRDUPC reads card first via COCRDSLC XCTL,
    then REWRITEs after user input is validated.
    """
    service = CardService(db)
    return await service.update_card(card_num, request)
