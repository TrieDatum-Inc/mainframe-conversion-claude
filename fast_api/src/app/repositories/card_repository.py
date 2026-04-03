"""
Data access layer for the cards table.
SQL equivalents of COBOL VSAM browse operations.
"""
import logging
from datetime import date

from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.utils.exceptions import CardNotFoundError, CardUpdateLockError

logger = logging.getLogger(__name__)


class CardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_cards_forward(
        self,
        cursor: str | None,
        page_size: int,
        acct_id: str | None = None,
        card_num_filter: str | None = None,
    ) -> tuple[list[Card], bool, str | None]:
        """
        STARTBR GTEQ + READNEXT equivalent.
        Returns (page_items, has_next_page, next_cursor).
        Fetches page_size+1 rows to implement the lookahead probe from 9000-READ-FORWARD.
        """
        stmt = select(Card).order_by(Card.card_num)
        if cursor:
            stmt = stmt.where(Card.card_num >= cursor)
        if acct_id:
            stmt = stmt.where(Card.card_acct_id == acct_id)
        if card_num_filter:
            stmt = stmt.where(Card.card_num == card_num_filter)
        stmt = stmt.limit(page_size + 1)

        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        has_next_page = len(rows) > page_size
        next_cursor: str | None = None
        if has_next_page:
            next_cursor = rows[page_size].card_num
            rows = rows[:page_size]

        return rows, has_next_page, next_cursor

    async def get_card_by_num(self, card_num: str) -> Card:
        """READ FILE BY KEY — raises CardNotFoundError on DFHRESP(NOTFND)."""
        result = await self._session.execute(select(Card).where(Card.card_num == card_num))
        card = result.scalar_one_or_none()
        if card is None:
            raise CardNotFoundError(card_num)
        return card

    async def get_card_for_update(self, card_num: str) -> Card:
        """SELECT ... FOR UPDATE NOWAIT — READ FILE UPDATE equivalent."""
        try:
            result = await self._session.execute(
                select(Card).where(Card.card_num == card_num).with_for_update(nowait=True)
            )
        except OperationalError as exc:
            logger.warning("Lock contention for card %s: %s", card_num, exc)
            raise CardUpdateLockError(card_num) from exc

        card = result.scalar_one_or_none()
        if card is None:
            raise CardNotFoundError(card_num)
        return card

    async def update_card(
        self,
        card_num: str,
        embossed_name: str,
        active_status: str,
        expiry_month: int,
        expiry_year: int,
        expiry_day: int,
    ) -> Card:
        """REWRITE FILE equivalent. expiry_day is always from original record (hidden EXPDAY)."""
        expiration_date = date(expiry_year, expiry_month, expiry_day)
        await self._session.execute(
            update(Card).where(Card.card_num == card_num).values(
                card_embossed_name=embossed_name,
                card_active_status=active_status,
                card_expiration_date=expiration_date,
            )
        )
        await self._session.flush()
        return await self.get_card_by_num(card_num)
