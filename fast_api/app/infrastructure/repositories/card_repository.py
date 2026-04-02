"""
Card repository — data access layer.

Replaces VSAM KSDS EXEC CICS operations on:
  CARDDAT  (card master, primary key: CARD-NUM)
  CXACAIX  (card xref AIX; alternate index lookup by account ID)

COCRDLIC uses STARTBR/READNEXT/READPREV for paginated browsing.
This is replicated with offset-based pagination + keyset pagination.
"""

from typing import List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateKeyError, ResourceNotFoundError
from app.infrastructure.orm.card_orm import CardORM, CardXrefORM


class CardRepository:
    """
    Card VSAM KSDS operations (CARDDAT file).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_card_num(self, card_num: str) -> CardORM:
        """
        Read card by primary key.
        Equivalent to: EXEC CICS READ DATASET('CARDDAT') RIDFLD(card_num)
        """
        stmt = select(CardORM).where(CardORM.card_num == card_num)
        result = await self.db.execute(stmt)
        card = result.scalar_one_or_none()
        if card is None:
            raise ResourceNotFoundError("Card", card_num)
        return card

    async def get_by_card_num_or_none(self, card_num: str) -> Optional[CardORM]:
        """Read card; return None if not found."""
        stmt = select(CardORM).where(CardORM.card_num == card_num)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_account_id(self, acct_id: int) -> List[CardORM]:
        """
        Get all cards for an account.
        Equivalent to browsing CARDDAT with account-based AIX filter.
        """
        stmt = (
            select(CardORM)
            .where(CardORM.acct_id == acct_id)
            .order_by(CardORM.card_num)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_paginated_forward(
        self,
        page_size: int,
        start_card_num: Optional[str] = None,
        account_id_filter: Optional[int] = None,
    ) -> Tuple[List[CardORM], bool]:
        """
        Forward-paginated card list.
        Equivalent to COCRDLIC 9000-READ-FORWARD:
          EXEC CICS STARTBR DATASET('CARDDAT') RIDFLD(start_card_num)
          EXEC CICS READNEXT ... (up to page_size records)
          EXEC CICS ENDBR

        Returns (records, has_next_page).
        """
        conditions = []
        if start_card_num:
            conditions.append(CardORM.card_num >= start_card_num)
        if account_id_filter is not None:
            conditions.append(CardORM.acct_id == account_id_filter)

        stmt = (
            select(CardORM)
            .where(and_(*conditions) if conditions else True)
            .order_by(asc(CardORM.card_num))
            .limit(page_size + 1)  # fetch one extra to detect next page
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        has_next = len(rows) > page_size
        return rows[:page_size], has_next

    async def list_paginated_backward(
        self,
        page_size: int,
        end_card_num: str,
        account_id_filter: Optional[int] = None,
    ) -> Tuple[List[CardORM], bool]:
        """
        Backward-paginated card list.
        Equivalent to COCRDLIC 9100-READ-BACKWARDS:
          EXEC CICS STARTBR DATASET('CARDDAT') RIDFLD(end_card_num) GTEQ
          EXEC CICS READPREV ... (up to page_size records)
          EXEC CICS ENDBR

        Returns (records in forward order, has_previous_page).
        """
        conditions = [CardORM.card_num <= end_card_num]
        if account_id_filter is not None:
            conditions.append(CardORM.acct_id == account_id_filter)

        stmt = (
            select(CardORM)
            .where(and_(*conditions))
            .order_by(desc(CardORM.card_num))
            .limit(page_size + 1)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        has_prev = len(rows) > page_size
        # Return in ascending order for display
        return list(reversed(rows[:page_size])), has_prev

    async def create(self, card: CardORM, xref: CardXrefORM) -> CardORM:
        """
        Write new card + cross-reference records atomically.
        Equivalent to:
          EXEC CICS WRITE DATASET('CARDDAT')
          EXEC CICS WRITE DATASET('CXACAIX')
        Raises DuplicateKeyError if card_num already exists.
        """
        existing = await self.get_by_card_num_or_none(card.card_num)
        if existing is not None:
            raise DuplicateKeyError("Card", card.card_num)
        self.db.add(card)
        self.db.add(xref)
        await self.db.flush()
        return card

    async def update(self, card: CardORM) -> CardORM:
        """
        Update card record.
        Equivalent to: EXEC CICS REWRITE DATASET('CARDDAT')
        COCRDUPC state machine: ACUP-CHANGES-OKAYED-AND-DONE state after successful write.
        """
        await self.db.flush()
        return card

    async def get_xref_by_card_num(self, card_num: str) -> Optional[CardXrefORM]:
        """Get cross-reference record by card number."""
        stmt = select(CardXrefORM).where(CardXrefORM.card_num == card_num)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
