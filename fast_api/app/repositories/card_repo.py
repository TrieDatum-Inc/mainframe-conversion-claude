"""
Card repository — data access layer for CARDDAT/CARDAIX/CCXREF VSAM file operations.

Maps CICS file operations:
  EXEC CICS READ   FILE(CARDDAT) RIDFLD(CARD-NUM)          → get_by_card_num()
  EXEC CICS REWRITE FILE(CARDDAT) FROM(CARD-RECORD)        → update()
  EXEC CICS STARTBR FILE(CARDAIX) RIDFLD(CARD-ACCT-ID)     → list_by_account() (keyset)
  EXEC CICS READ   FILE(CCXREF) RIDFLD(XREF-CARD-NUM)      → get_xref_by_card_num()
  EXEC CICS STARTBR FILE(CXACAIX) RIDFLD(XREF-ACCT-ID)     → list_xref_by_account()

Source programs: COCRDLIC, COCRDSLC, COCRDUPC, COBIL00C, CBTRN01C
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card, CardXref
from app.utils.error_handlers import RecordNotFoundError


class CardRepository:
    """Data access object for `cards` and `card_xref` tables."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_card_num(self, card_num: str) -> Card:
        """
        EXEC CICS READ FILE('CARDDAT') INTO(CARD-RECORD) RIDFLD(WS-CARD-NUM)

        COCRDSLC select-card paragraph.
        RESP=13 (NOTFND) → RecordNotFoundError.
        """
        card_num = card_num.ljust(16)[:16]
        card = await self._db.get(Card, card_num)
        if card is None:
            raise RecordNotFoundError(f"Card not found (card_num={card_num!r})")
        return card

    async def update(self, card: Card) -> Card:
        """
        EXEC CICS REWRITE FILE('CARDDAT') FROM(CARD-RECORD)

        COCRDUPC update-card paragraph.
        """
        merged = await self._db.merge(card)
        await self._db.flush()
        return merged

    async def list_by_account(
        self,
        acct_id: int,
        cursor: str | None = None,
        limit: int = 10,
        direction: str = "forward",
    ) -> tuple[list[Card], int, bool]:
        """
        EXEC CICS STARTBR FILE('CARDAIX') RIDFLD(WS-CARD-ACCT-ID) GTEQ
        EXEC CICS READNEXT FILE('CARDAIX') INTO(CARD-RECORD)

        COCRDLIC browse-cards paragraph — browses CARDAIX (alt index on CARD-ACCT-ID).
        Supports forward (READNEXT) and backward (READPREV) paging.

        Args:
            acct_id: CARD-ACCT-ID to browse for.
            cursor: Last card_num from previous page (keyset cursor).
            limit: Page size (COCRDLIC: screen shows 7 rows).
            direction: 'forward' (READNEXT) or 'backward' (READPREV).

        Returns:
            Tuple of (card list, total count for this account).
        """
        count_stmt = select(func.count(Card.card_num)).where(Card.acct_id == acct_id)
        total = (await self._db.execute(count_stmt)).scalar_one()

        stmt = select(Card).where(Card.acct_id == acct_id)

        if direction == "forward":
            stmt = stmt.order_by(Card.card_num)
            if cursor:
                stmt = stmt.where(Card.card_num > cursor.ljust(16)[:16])
        else:
            # READPREV: reverse order, cursor is the first card on current page
            stmt = stmt.order_by(Card.card_num.desc())
            if cursor:
                stmt = stmt.where(Card.card_num < cursor.ljust(16)[:16])

        stmt = stmt.limit(limit + 1)
        result = await self._db.execute(stmt)
        cards = list(result.scalars().all())
        has_more = len(cards) > limit
        cards = cards[:limit]

        if direction == "backward":
            cards = list(reversed(cards))

        return cards, total, has_more

    async def list_all_paginated(
        self,
        cursor: str | None = None,
        limit: int = 10,
        direction: str = "forward",
    ) -> tuple[list[Card], int, bool]:
        """Paginated list of all cards (admin view)."""
        count_stmt = select(func.count(Card.card_num))
        total = (await self._db.execute(count_stmt)).scalar_one()

        stmt = select(Card)
        if direction == "backward":
            stmt = stmt.order_by(Card.card_num.desc())
            if cursor:
                stmt = stmt.where(Card.card_num < cursor.ljust(16)[:16])
        else:
            stmt = stmt.order_by(Card.card_num)
            if cursor:
                stmt = stmt.where(Card.card_num > cursor.ljust(16)[:16])
        stmt = stmt.limit(limit + 1)

        result = await self._db.execute(stmt)
        rows = list(result.scalars().all())
        has_more = len(rows) > limit
        rows = rows[:limit]
        if direction == "backward":
            rows = list(reversed(rows))
        return rows, total, has_more

    async def get_xref_by_card_num(self, card_num: str) -> CardXref:
        """
        EXEC CICS READ FILE('CCXREF') INTO(CARD-XREF-RECORD) RIDFLD(XREF-CARD-NUM)

        Used by CBTRN01C to resolve card → account ID during batch posting.
        """
        card_num = card_num.ljust(16)[:16]
        xref = await self._db.get(CardXref, card_num)
        if xref is None:
            raise RecordNotFoundError(f"Card xref not found (card_num={card_num!r})")
        return xref

    async def list_xref_by_account(self, acct_id: int) -> list[CardXref]:
        """
        EXEC CICS STARTBR FILE('CXACAIX') RIDFLD(WS-XREF-ACCT-ID)

        COBIL00C: browse CXACAIX to find card numbers for a given account.
        Returns all xref records for the account (usually 1-3 cards).
        """
        stmt = select(CardXref).where(CardXref.acct_id == acct_id).order_by(CardXref.card_num)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
