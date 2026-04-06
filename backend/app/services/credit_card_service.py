"""
Credit card service — all business logic for card list, view, and update.

COBOL origin:
  list_cards  → COCRDLIC POPULATE-USER-DATA: STARTBR/READNEXT 7-row paged browse
  view_card   → COCRDSLC PROCESS-ENTER-KEY: READ CARDDAT by CARD-NUM
  update_card → COCRDUPC PROCESS-ENTER-KEY → UPDATE-CARD: validate + REWRITE

COCRDUPC business rules:
  - card_embossed_name: alpha-only (INSPECT CONVERTING equivalent)
  - expiration_month: 1-12
  - expiration_year: 1950-2099
  - account_id: PROT — cannot be changed in update
  - optimistic lock: updated_at compared to CCUP-OLD-DETAILS snapshot
    → 409 if mismatch (SYNCPOINT ROLLBACK in original)
"""

import re
from calendar import monthrange
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import CardNotFoundError, CardOptimisticLockError
from app.repositories.credit_card_repository import CreditCardRepository
from app.schemas.credit_card import (
    CardDetailResponse,
    CardListItem,
    CardListResponse,
    CardUpdateRequest,
)


def _mask_card_number(card_number: str) -> str:
    """
    Mask card number for list display — show only last 4 digits.

    PCI-DSS: Never display full card number in list views.
    COCRDLIC displayed full card numbers — masked here for security.
    """
    if len(card_number) >= 4:
        return f"************{card_number[-4:]}"
    return card_number


def _build_card_detail(card: object) -> CardDetailResponse:
    """
    Build CardDetailResponse from a CreditCard ORM object.

    Extracts expiration_month and expiration_year from expiration_date.
    Preserves expiration_day (DRK PROT FSET hidden field from COCRDUP map).
    """
    exp_month = 1
    exp_year = 2024
    if card.expiration_date:
        exp_month = card.expiration_date.month
        exp_year = card.expiration_date.year

    return CardDetailResponse(
        card_number=card.card_number,
        account_id=card.account_id,
        card_embossed_name=card.card_embossed_name,
        active_status=card.active_status,
        expiration_month=exp_month,
        expiration_year=exp_year,
        expiration_day=card.expiration_day,
        updated_at=card.updated_at,
    )


def _validate_embossed_name(name: str) -> None:
    """
    Validate card embossed name is alpha/space/hyphen/apostrophe only.

    COBOL: COCRDUPC INSPECT CONVERTING on CRDNAME field.
    Raises ValueError if invalid characters found.
    """
    if not re.match(r"^[A-Za-z\s\-']+$", name):
        raise ValueError(
            "Card name must contain only letters, spaces, hyphens, or apostrophes"
        )


async def list_cards(
    db: AsyncSession,
    account_id: int | None = None,
    card_number: str | None = None,
    page: int = 1,
    page_size: int = 7,
) -> CardListResponse:
    """
    Paginated card list with optional filters.

    COBOL: COCRDLIC POPULATE-USER-DATA with STARTBR/READNEXT pattern.
    Original showed 7 rows per page (CRDSTP1-7 markers).
    Filters applied post-browse in COBOL; here applied in WHERE clause (more efficient).

    Returns CardListResponse with masked card numbers.
    """
    repo = CreditCardRepository(db)
    cards, total_count = await repo.list_by_filters(
        account_id=account_id,
        card_number=card_number,
        page=page,
        page_size=page_size,
    )

    items = [
        CardListItem(
            card_number=card.card_number,
            card_number_masked=_mask_card_number(card.card_number),
            account_id=card.account_id,
            active_status=card.active_status,
        )
        for card in cards
    ]

    return CardListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_count=total_count,
        has_next=(page * page_size) < total_count,
        has_previous=page > 1,
    )


async def view_card(card_number: str, db: AsyncSession) -> CardDetailResponse:
    """
    Fetch card detail by card number.

    COBOL: COCRDSLC PROCESS-ENTER-KEY → READ DATASET(CARDDAT) RIDFLD(WS-CARD-NUM).
    Returns 404 if card not found (maps RESP=NOTFND).
    """
    repo = CreditCardRepository(db)
    card = await repo.get_by_number(card_number)
    if card is None:
        raise CardNotFoundError(card_number)

    return _build_card_detail(card)


async def update_card(
    card_number: str,
    request: CardUpdateRequest,
    db: AsyncSession,
) -> CardDetailResponse:
    """
    Validate and update card fields.

    COBOL: COCRDUPC PROCESS-ENTER-KEY (7-state machine):
      1. Read current card record
      2. Compare optimistic_lock_version to updated_at (CCUP-OLD-DETAILS snapshot)
      3. Validate card_embossed_name alpha-only
      4. Validate expiration_month 1-12
      5. Validate expiration_year 1950-2099
      6. REWRITE CARDDAT (account_id NOT changed — PROT field)

    Returns 404 if card not found.
    Returns 409 if optimistic lock mismatch.
    """
    repo = CreditCardRepository(db)

    card = await repo.get_by_number(card_number)
    if card is None:
        raise CardNotFoundError(card_number)

    # Optimistic lock check — replaces COCRDUPC CCUP-OLD-DETAILS snapshot comparison
    # Compare truncated to seconds to avoid microsecond precision issues
    stored_ts = card.updated_at.replace(microsecond=0)
    request_ts = request.optimistic_lock_version.replace(microsecond=0)
    if stored_ts != request_ts:
        raise CardOptimisticLockError()

    # Validate card embossed name — COCRDUPC INSPECT CONVERTING
    _validate_embossed_name(request.card_embossed_name)

    # Build expiration date from month/year/day
    exp_day = request.expiration_day or 1
    # Clamp day to valid range for the month
    max_day = monthrange(request.expiration_year, request.expiration_month)[1]
    exp_day = min(exp_day, max_day)
    expiration_date = date(request.expiration_year, request.expiration_month, exp_day)

    updated_card = await repo.update(
        card_number=card_number,
        card_embossed_name=request.card_embossed_name,
        active_status=request.active_status,
        expiration_date=expiration_date,
        expiration_day=request.expiration_day,
    )

    if updated_card is None:
        raise CardNotFoundError(card_number)

    return _build_card_detail(updated_card)
