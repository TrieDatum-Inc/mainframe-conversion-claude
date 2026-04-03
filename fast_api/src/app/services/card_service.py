"""
Business logic layer for the Credit Card module.
Implements COCRDLIC, COCRDSLC, and COCRDUPC flows.
"""
import logging
from datetime import datetime

from app.models.card import Card
from app.repositories.card_repository import CardRepository
from app.schemas.card import (
    CardDetail, CardListItem, CardListResponse,
    CardUpdateRequest, CardUpdateResponse,
)
from app.utils.exceptions import (
    CardNotFoundError, CardUpdateLockError, ConcurrentModificationError,
)

logger = logging.getLogger(__name__)


def _card_to_detail(card: Card) -> CardDetail:
    expiry_month: int | None = None
    expiry_year: int | None = None
    expiry_day: int | None = None
    if card.card_expiration_date:
        expiry_month = card.card_expiration_date.month
        expiry_year = card.card_expiration_date.year
        expiry_day = card.card_expiration_date.day
    return CardDetail(
        card_num=card.card_num,
        card_acct_id=card.card_acct_id,
        card_cvv_cd=card.card_cvv_cd,
        card_embossed_name=card.card_embossed_name,
        card_active_status=card.card_active_status,
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        expiry_day=expiry_day,
        updated_at=card.updated_at,
    )


class CardService:
    def __init__(self, repository: CardRepository) -> None:
        self._repo = repository

    async def list_cards(
        self,
        cursor: str | None,
        page_size: int,
        acct_id: str | None,
        card_num_filter: str | None,
        page: int = 1,
    ) -> CardListResponse:
        """9000-READ-FORWARD equivalent with optional filters."""
        rows, has_next_page, next_cursor = await self._repo.list_cards_forward(
            cursor=cursor, page_size=page_size, acct_id=acct_id, card_num_filter=card_num_filter,
        )
        items = [
            CardListItem(card_num=row.card_num, card_acct_id=row.card_acct_id, card_active_status=row.card_active_status)
            for row in rows
        ]
        return CardListResponse(
            items=items, page=page, page_size=page_size,
            has_next_page=has_next_page, next_cursor=next_cursor,
            prev_cursor=cursor, total_on_page=len(items),
        )

    async def get_card_detail(self, card_num: str) -> CardDetail:
        """9100-GETCARD-BYACCTCARD equivalent."""
        card = await self._repo.get_card_by_num(card_num)
        return _card_to_detail(card)

    async def update_card(self, card_num: str, request: CardUpdateRequest) -> CardUpdateResponse:
        """
        9200-WRITE-PROCESSING three phases:
        Phase 3a: get_card_for_update (SELECT FOR UPDATE NOWAIT)
        Phase 3b: _check_concurrent_modification (9300-CHECK-CHANGE-IN-REC)
        Phase 3c: update_card (REWRITE FILE)
        """
        locked_card = await self._repo.get_card_for_update(card_num)
        self._check_concurrent_modification(locked_card, request.updated_at, card_num)

        # Preserve original expiry day (hidden EXPDAY field — never user-editable)
        expiry_day = locked_card.card_expiration_date.day if locked_card.card_expiration_date else 1

        updated_card = await self._repo.update_card(
            card_num=card_num,
            embossed_name=request.card_embossed_name,
            active_status=request.card_active_status,
            expiry_month=request.expiry_month,
            expiry_year=request.expiry_year,
            expiry_day=expiry_day,
        )

        expiry_month: int | None = None
        expiry_year_val: int | None = None
        expiry_day_val: int | None = None
        if updated_card.card_expiration_date:
            expiry_month = updated_card.card_expiration_date.month
            expiry_year_val = updated_card.card_expiration_date.year
            expiry_day_val = updated_card.card_expiration_date.day

        return CardUpdateResponse(
            card_num=updated_card.card_num,
            card_acct_id=updated_card.card_acct_id,
            card_embossed_name=updated_card.card_embossed_name,
            card_active_status=updated_card.card_active_status,
            expiry_month=expiry_month,
            expiry_year=expiry_year_val,
            expiry_day=expiry_day_val,
            updated_at=updated_card.updated_at,
            message="Changes committed to database",
        )

    @staticmethod
    def _check_concurrent_modification(
        locked_card: Card, client_updated_at: datetime, card_num: str,
    ) -> None:
        """
        9300-CHECK-CHANGE-IN-REC equivalent.
        Uses updated_at as the lock token (replaces CVV+name+expiry+status snapshot).
        """
        db_ts = locked_card.updated_at
        client_ts = client_updated_at
        if db_ts.replace(microsecond=0) != client_ts.replace(microsecond=0):
            logger.info("Concurrent modification detected for card %s: db_ts=%s client_ts=%s", card_num, db_ts, client_ts)
            raise ConcurrentModificationError(card_num, refreshed_card=locked_card)
