"""
Credit card repository — data access layer for the `credit_cards` table.

COBOL origin: Replaces EXEC CICS READ/WRITE/REWRITE/STARTBR/READNEXT DATASET(CARDDAT).
  COCRDLIC: STARTBR CARDDAT / READNEXT (7-row page browse) → list_by_filters (paginated)
  COCRDSLC: READ CARDDAT by CARD-NUM → get_by_number
  COCRDUPC: READ UPDATE CARDDAT → get_by_number, then REWRITE → update
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_card import CreditCard


class CreditCardRepository:
    """
    Data access operations for the `credit_cards` table.

    No business logic here — only SQLAlchemy queries.
    Pagination replaces the COCRDLIC STARTBR/READNEXT/READPREV/ENDBR browse pattern.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_filters(
        self,
        account_id: Optional[int] = None,
        card_number: Optional[str] = None,
        page: int = 1,
        page_size: int = 7,
    ) -> tuple[list[CreditCard], int]:
        """
        Paginated card list with optional filters.

        COBOL: COCRDLIC STARTBR CARDDAT RIDFLD(WS-CARD-RID-CARDNUM)
               READNEXT loop — 7 rows per page.
        account_id filter replaces: IF ACCT-NUMBER NOT = SPACES/ZEROS comparison.
        card_number filter replaces: IF CARD-NUMBER-O NOT = SPACES comparison.

        Returns (cards, total_count).
        """
        # Build base query
        base_stmt = select(CreditCard)
        count_stmt = select(func.count()).select_from(CreditCard)

        if account_id is not None:
            base_stmt = base_stmt.where(CreditCard.account_id == account_id)
            count_stmt = count_stmt.where(CreditCard.account_id == account_id)

        if card_number is not None:
            base_stmt = base_stmt.where(CreditCard.card_number == card_number)
            count_stmt = count_stmt.where(CreditCard.card_number == card_number)

        # Get total count
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar_one()

        # Apply pagination — replaces STARTBR offset + READNEXT limit pattern
        offset = (page - 1) * page_size
        base_stmt = (
            base_stmt.order_by(CreditCard.card_number).offset(offset).limit(page_size)
        )

        result = await self.db.execute(base_stmt)
        cards = list(result.scalars().all())

        return cards, total_count

    async def get_by_number(self, card_number: str) -> Optional[CreditCard]:
        """
        Fetch card by primary key.

        COBOL: EXEC CICS READ DATASET(CARDDAT) INTO(CARD-RECORD)
               RIDFLD(WS-CARD-NUM) RESP(WS-RESP)
        Returns None if not found (RESP=NOTFND → 404).
        """
        stmt = select(CreditCard).where(CreditCard.card_number == card_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        card_number: str,
        card_embossed_name: str,
        active_status: str,
        expiration_date: date,
        expiration_day: Optional[int],
    ) -> Optional[CreditCard]:
        """
        Update card fields.

        COBOL: EXEC CICS REWRITE DATASET(CARDDAT) FROM(CARD-RECORD)
        account_id is NOT updated here — it is PROT in COCRDUPC.
        updated_at is managed by the trigger (replaces CCUP-OLD-DETAILS snapshot).
        """
        stmt = (
            update(CreditCard)
            .where(CreditCard.card_number == card_number)
            .values(
                card_embossed_name=card_embossed_name,
                active_status=active_status,
                expiration_date=expiration_date,
                expiration_day=expiration_day,
            )
            .returning(CreditCard)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
