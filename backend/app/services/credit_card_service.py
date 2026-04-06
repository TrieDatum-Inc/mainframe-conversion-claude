"""
Credit card service — COCRDLIC (list), COCRDSLC (view), COCRDUPC (update).

COBOL programs: COCRDLIC, COCRDSLC, COCRDUPC
VSAM dataset: CARDDAT (CVACT02Y copybook)

Key COCRDUPC rules preserved:
  - account_id is PROT — NEVER updated
  - CRDNAME alpha-only validation (INSPECT CONVERTING equivalent)
  - EXPMON 1-12, EXPYEAR 1950-2099 (validated in schema)
  - Optimistic lock via updated_at (replaces CCUP-OLD-DETAILS snapshot)
  - EXPDAY hidden DRK PROT FSET field preserved across updates

Cognitive complexity kept under 15 per function.
"""

from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import NotFoundError, OptimisticLockError
from app.models.credit_card import CreditCard
from app.repositories.credit_card_repository import CreditCardRepository
from app.schemas.credit_card import (
    CardDetailResponse,
    CardListItem,
    CardListResponse,
    CardUpdateRequest,
)


# =============================================================================
# Helpers
# =============================================================================

def _mask_card_number(card_number: str) -> str:
    """
    Mask card number showing only last 4 digits.

    COCRDLIC display: CRDNUMn field shows masked number per PCI-DSS.
    Example: '1234567890123456' → '************3456'
    """
    if not card_number or len(card_number) < 4:
        return card_number
    return f"{'*' * (len(card_number) - 4)}{card_number[-4:]}"


def _build_expiry_date(month: int | None, year: int | None, day: int | None) -> date | None:
    """
    Build expiration date from EXPMON + EXPYEAR + EXPDAY.

    EXPDAY is the hidden DRK PROT FSET field from COCRDUPC CCRDUPA map.
    If EXPDAY not provided or out of range for the month, defaults to last day of month.
    """
    if not month or not year:
        return None
    _, max_day = monthrange(year, month)
    safe_day = min(day or 1, max_day)
    return date(year, month, safe_day)


def _build_card_response(card: CreditCard) -> CardDetailResponse:
    """Build CardDetailResponse from CreditCard ORM model."""
    exp_month = None
    exp_year = None
    exp_day = card.expiration_day

    if card.expiration_date:
        exp_month = card.expiration_date.month
        exp_year = card.expiration_date.year
        if not exp_day:
            exp_day = card.expiration_date.day

    return CardDetailResponse(
        card_number=card.card_number.strip(),
        account_id=card.account_id,
        customer_id=card.customer_id,
        card_embossed_name=card.card_embossed_name,
        active_status=card.active_status,
        expiration_date=card.expiration_date.isoformat() if card.expiration_date else None,
        expiration_month=exp_month,
        expiration_year=exp_year,
        expiration_day=exp_day,
        updated_at=card.updated_at.isoformat(),
    )


def _parse_lock_version(version_str: str) -> datetime | None:
    """Parse ISO datetime string to datetime, returning None on parse failure."""
    try:
        # Handle both with and without timezone info
        if version_str.endswith("Z"):
            version_str = version_str[:-1] + "+00:00"
        return datetime.fromisoformat(version_str)
    except (ValueError, AttributeError):
        return None


# =============================================================================
# List cards — COCRDLIC
# =============================================================================

async def list_cards(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 7,
    account_id: int | None = None,
    card_number: str | None = None,
) -> CardListResponse:
    """
    Paginated card list.

    COCRDLIC: STARTBR/READNEXT browse with WS-MAX-SCREEN-LINES=7.
    Default page_size=7 preserves original display capacity.
    Card numbers masked per PCI-DSS (last 4 digits only in list).
    """
    repo = CreditCardRepository(db)
    cards, total = await repo.list_by_filters(
        page=page,
        page_size=page_size,
        account_id=account_id,
        card_number_prefix=card_number,
    )

    items = [
        CardListItem(
            card_number=card.card_number.strip(),
            card_number_masked=_mask_card_number(card.card_number.strip()),
            account_id=card.account_id,
            active_status=card.active_status,
        )
        for card in cards
    ]

    return CardListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_count=total,
        has_next=page * page_size < total,
        has_previous=page > 1,
    )


# =============================================================================
# View card — COCRDSLC
# =============================================================================

async def view_card(card_number: str, db: AsyncSession) -> CardDetailResponse:
    """
    Fetch a single card record.

    COCRDSLC PROCESS-ENTER-KEY:
      EXEC CICS READ DATASET(CARDDAT) INTO(CARD-RECORD)
             RIDFLD(WS-CARD-NUM) RESP(WS-RESP)

    Raises NotFoundError if card not found (RESP=DFHRESP(NOTFND)).
    """
    repo = CreditCardRepository(db)
    card = await repo.get_by_number(card_number)
    if card is None:
        raise NotFoundError("Card", card_number)
    return _build_card_response(card)


# =============================================================================
# Update card — COCRDUPC
# =============================================================================

def _check_optimistic_lock(
    card: CreditCard,
    lock_version: str,
) -> None:
    """
    Compare optimistic lock version to detect concurrent modification.

    COCRDUPC: compares CCUP-OLD-DETAILS snapshot with current record.
    Here: compare updated_at timestamp (truncated to seconds for ISO round-trip).

    Raises OptimisticLockError if timestamps differ.
    """
    request_ts = _parse_lock_version(lock_version)
    if request_ts is None:
        raise OptimisticLockError("Credit card")

    stored_ts = card.updated_at
    # Truncate microseconds — ISO string round-trip loses sub-second precision
    stored_sec = stored_ts.replace(microsecond=0, tzinfo=None)
    request_sec = request_ts.replace(microsecond=0, tzinfo=None)

    if stored_sec != request_sec:
        raise OptimisticLockError("Credit card")


async def update_card(
    card_number: str,
    request: CardUpdateRequest,
    db: AsyncSession,
) -> CardDetailResponse:
    """
    Update an existing credit card record.

    COCRDUPC flow:
      1. READ DATASET(CARDDAT) RIDFLD(CARD-NUM)
      2. Compare CCUP-OLD-DETAILS snapshot (optimistic lock)
      3. Validate CRDNAME alpha-only, EXPMON 1-12, EXPYEAR 1950-2099
         (validated at schema level — arrive here already clean)
      4. REWRITE DATASET(CARDDAT) — account_id NOT updated (PROT)
      5. Return updated response

    Rules:
      - account_id is NEVER modified (ACCTSID PROT in CCRDUPA)
      - EXPDAY stored back even if not visible to user
    """
    repo = CreditCardRepository(db)
    card = await repo.get_by_number(card_number)
    if card is None:
        raise NotFoundError("Card", card_number)

    _check_optimistic_lock(card, request.optimistic_lock_version)

    # Update editable fields — account_id intentionally excluded
    card.card_embossed_name = request.card_embossed_name
    card.active_status = request.active_status

    # Build new expiration_date from EXPMON + EXPYEAR + EXPDAY
    new_expiry = _build_expiry_date(
        request.expiration_month,
        request.expiration_year,
        request.expiration_day,
    )
    card.expiration_date = new_expiry
    card.expiration_day = request.expiration_day  # preserve EXPDAY hidden field

    updated = await repo.update(card)
    return _build_card_response(updated)
