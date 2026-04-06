"""Card service — business logic for credit card operations.

Migrated from COBOL programs:
  COCRDLIC  — BROWSE CARDDAT/CARDAIX (7-per-page paginated list)
  COCRDSLC  — READ CARDDAT by card number (detail view)
  COCRDUPC  — READ/REWRITE CARDDAT (update embossed name, status, expiry)

Key COBOL validation rules preserved:
  - Expiry month: 1-12 (VALID-MONTH VALUE 1 THRU 12)
  - Expiry year: 1950-2099 (VALID-YEAR VALUE 1950 THRU 2099)
  - Status: 'Y' or 'N' (FLG-YES-NO-VALID)
  - Name: non-blank
  - Account number: PROTECTED — never updated via this service
"""

import math
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.schemas.card import (
    CardDetailResponse,
    CardListItem,
    CardListResponse,
    CardUpdateRequest,
)

# Default day for expiry date — COBOL EXPDAY is system-maintained (DRK,PROT)
_EXPIRY_DAY = 1


# ---------------------------------------------------------------------------
# List / filter (COCRDLIC browse pattern)
# ---------------------------------------------------------------------------


async def list_cards(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 7,  # COCRDLIC: exactly 7 rows per page
    account_id_filter: str | None = None,
    card_number_filter: str | None = None,
) -> CardListResponse:
    """Return paginated cards, optionally filtered by account or card number.

    COBOL COCRDLIC:
      - No filter: STARTBR CARDDAT, READNEXT 7 rows, ENDBR
      - Account filter: STARTBR CARDAIX by CARD-ACCT-ID, READNEXT 7 rows
      - Card filter: partial match on CARD-NUM
    """
    base_query = select(Card)

    if account_id_filter:
        base_query = base_query.where(Card.account_id == account_id_filter)

    if card_number_filter:
        base_query = base_query.where(
            Card.card_number.like(f"{card_number_filter}%")
        )

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        base_query.order_by(Card.card_number).offset(offset).limit(page_size)
    )
    cards = result.scalars().all()

    items = [
        CardListItem(
            card_number=c.card_number,
            account_id=c.account_id,
            embossed_name=c.embossed_name,
            active_status=c.active_status,
            expiration_date=c.expiration_date,
        )
        for c in cards
    ]

    return CardListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


# ---------------------------------------------------------------------------
# Fetch card detail (COCRDSLC READ CARDDAT)
# ---------------------------------------------------------------------------


async def get_card_detail(
    db: AsyncSession, card_number: str
) -> CardDetailResponse | None:
    """Fetch full card record by card number.

    COBOL COCRDSLC: READ CARDDAT by CARD-NUM key.
    Returns None if card not found (NOTFND condition).
    """
    result = await db.execute(
        select(Card).where(Card.card_number == card_number)
    )
    card = result.scalar_one_or_none()
    if card is None:
        return None

    return CardDetailResponse(
        id=card.id,
        card_number=card.card_number,
        account_id=card.account_id,
        cvv_code=card.cvv_code,
        embossed_name=card.embossed_name,
        active_status=card.active_status,
        expiration_date=card.expiration_date,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


# ---------------------------------------------------------------------------
# Update card (COCRDUPC READ/REWRITE CARDDAT)
# ---------------------------------------------------------------------------


async def update_card(
    db: AsyncSession,
    card_number: str,
    payload: CardUpdateRequest,
) -> CardDetailResponse | None:
    """Update editable card fields.

    COBOL COCRDUPC PF5 save flow:
      1. READ CARDDAT WITH UPDATE (lock record)
      2. MOVE CRDNAME -> CARD-EMBOSSED-NAME
      3. MOVE CRDSTCD -> CARD-ACTIVE-STATUS
      4. Compose expiry date from EXPMON + EXPYEAR + EXPDAY(system)
      5. REWRITE CARDDAT

    Account number (ACCTSID) is PROTECTED — not in payload, never modified.
    """
    result = await db.execute(
        select(Card).where(Card.card_number == card_number)
    )
    card = result.scalar_one_or_none()
    if card is None:
        return None

    _apply_card_updates(card, payload)

    await db.flush()
    await db.refresh(card)

    return CardDetailResponse(
        id=card.id,
        card_number=card.card_number,
        account_id=card.account_id,
        cvv_code=card.cvv_code,
        embossed_name=card.embossed_name,
        active_status=card.active_status,
        expiration_date=card.expiration_date,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


def _apply_card_updates(card: Card, payload: CardUpdateRequest) -> None:
    """Apply non-None fields from payload to the card ORM object.

    Expiry date is synthesized from month + year (EXPDAY = 1, system default).
    COBOL keeps EXPDAY as a DRK hidden field that is system-maintained.
    """
    if payload.embossed_name is not None:
        card.embossed_name = payload.embossed_name.strip()

    if payload.active_status is not None:
        card.active_status = payload.active_status

    new_expiry = _compute_expiry(
        card.expiration_date,
        payload.expiry_month,
        payload.expiry_year,
    )
    if new_expiry is not None:
        card.expiration_date = new_expiry


def _compute_expiry(
    current: date | None,
    new_month: int | None,
    new_year: int | None,
) -> date | None:
    """Synthesize expiry date from month/year components.

    COBOL BMS: EXPMON(2) + EXPYEAR(4) + EXPDAY(2, DRK, system-maintained=01).
    If only one component is provided, use the other from current date.
    """
    if new_month is None and new_year is None:
        return None  # No change requested

    base_month = current.month if current else 1
    base_year = current.year if current else 2025

    month = new_month if new_month is not None else base_month
    year = new_year if new_year is not None else base_year

    return date(year, month, _EXPIRY_DAY)
