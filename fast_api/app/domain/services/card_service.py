"""
Card service — business logic layer.

Maps COCRDLIC (list), COCRDSLC (detail), COCRDUPC (update) programs.

COCRDLIC: paginated list, 7 rows/page, forward/backward
  - Admin mode: all cards
  - Filtered mode: cards for a specific account
COCRDSLC: read-only detail view
COCRDUPC: update with optimistic concurrency (7-state machine)
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessValidationError, ResourceNotFoundError
from app.infrastructure.orm.card_orm import CardORM, CardXrefORM
from app.infrastructure.repositories.card_repository import CardRepository
from app.schemas.card_schemas import (
    CardCreateRequest,
    CardListItem,
    CardListResponse,
    CardUpdateRequest,
    CardView,
)


async def list_cards(
    db: AsyncSession,
    page_size: int = 7,
    start_card_num: Optional[str] = None,
    account_id_filter: Optional[int] = None,
    direction: str = "forward",
    end_card_num: Optional[str] = None,
) -> CardListResponse:
    """
    Paginated card list.
    Maps COCRDLIC 9000-READ-FORWARD / 9100-READ-BACKWARDS.

    COCRDLIC state tracking:
      WS-CA-LAST-CARD-NUM / WS-CA-FIRST-CARD-NUM (for page boundary navigation)
      WS-CA-SCREEN-NUM (current page number)
      WS-CA-LAST-PAGE-DISPLAYED (0=last page shown, 9=not yet)
    """
    repo = CardRepository(db)

    if direction == "backward" and end_card_num:
        rows, has_prev = await repo.list_paginated_backward(
            page_size=page_size,
            end_card_num=end_card_num,
            account_id_filter=account_id_filter,
        )
    else:
        rows, has_next = await repo.list_paginated_forward(
            page_size=page_size,
            start_card_num=start_card_num,
            account_id_filter=account_id_filter,
        )
        has_prev = start_card_num is not None

    if not rows:
        return CardListResponse(items=[], page=1, has_next_page=False)

    items = [CardListItem.model_validate(r) for r in rows]

    return CardListResponse(
        items=items,
        page=1,
        has_next_page=has_next if direction == "forward" else False,
        first_card_num=rows[0].card_num if rows else None,
        last_card_num=rows[-1].card_num if rows else None,
        account_filter=account_id_filter,
    )


async def get_card_detail(card_num: str, db: AsyncSession) -> CardView:
    """
    Card detail view (COCRDSLC).
    Read-only: EXEC CICS READ DATASET('CARDDAT') RIDFLD(card_num).
    """
    repo = CardRepository(db)
    card = await repo.get_by_card_num(card_num)
    return CardView.model_validate(card)


def _validate_card_update(req: CardUpdateRequest) -> list[str]:
    """
    COCRDUPC field validations.
    Returns list of error messages.
    """
    errors = []
    if req.active_status not in ("Y", "N"):
        errors.append("Active status must be 'Y' or 'N'.")
    return errors


async def update_card(
    card_num: str,
    req: CardUpdateRequest,
    db: AsyncSession,
) -> CardView:
    """
    Update card record.
    Maps COCRDUPC update with optimistic concurrency.

    COCRDUPC 7-state machine states:
      State 'L' (LOCK-ERROR): concurrent modification detected
      State 'C' (DONE): successful write
      State 'F' (FAILED): REWRITE failed for other reason

    Optimistic concurrency is enforced at the DB level via SELECT + UPDATE.
    """
    errors = _validate_card_update(req)
    if errors:
        raise BusinessValidationError("; ".join(errors))

    repo = CardRepository(db)
    card = await repo.get_by_card_num(card_num)

    card.embossed_name = req.embossed_name
    card.expiration_date = req.expiration_date
    card.active_status = req.active_status

    updated = await repo.update(card)
    return CardView.model_validate(updated)


async def create_card(req: CardCreateRequest, db: AsyncSession) -> CardView:
    """
    Create a new card + cross-reference record.
    Used for card provisioning and batch import (CBIMPORT).
    """
    repo = CardRepository(db)

    card = CardORM(
        card_num=req.card_num,
        acct_id=req.acct_id,
        cvv_cd=req.cvv_cd,
        embossed_name=req.embossed_name,
        expiration_date=req.expiration_date,
        active_status=req.active_status,
    )
    xref = CardXrefORM(
        card_num=req.card_num,
        cust_id=req.cust_id,
        acct_id=req.acct_id,
    )

    created = await repo.create(card, xref)
    return CardView.model_validate(created)
