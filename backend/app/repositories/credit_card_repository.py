"""
CreditCard repository — CARDDAT VSAM KSDS operations.

COBOL origin:
  list_by_filters()   → COCRDLIC STARTBR/READNEXT browse (7 rows/page)
  get_by_number()     → COCRDSLC READ DATASET(CARDDAT) RIDFLD(CARD-NUM)
  update()            → COCRDUPC REWRITE DATASET(CARDDAT)

Note: account_id is intentionally NOT in the update method parameters —
      ACCTSID is PROT in COCRDUPC and cannot be changed.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_card import CreditCard


class CreditCardRepository:
    """
    Data access object for the `credit_cards` table.

    list_by_filters() replaces COCRDLIC's STARTBR/READNEXT browse.
    Default page_size=7 matches COCRDLIC WS-MAX-SCREEN-LINES=7.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_filters(
        self,
        page: int,
        page_size: int,
        account_id: int | None = None,
        card_number_prefix: str | None = None,
    ) -> tuple[list[CreditCard], int]:
        """
        Paginated card list with optional filters.

        COCRDLIC browse:
          EXEC CICS STARTBR DATASET(CARDDAT) RIDFLD(CARD-NUM)
          LOOP: EXEC CICS READNEXT → display up to 7 rows
          EXEC CICS ENDBR

        Filters:
          ACCTSID (COCRDLIC row 6) → account_id filter
          CARDSID (COCRDLIC row 7) → card_number prefix match
        """
        query = select(CreditCard)

        if account_id is not None:
            query = query.where(CreditCard.account_id == account_id)
        if card_number_prefix:
            query = query.where(CreditCard.card_number.like(f"{card_number_prefix}%"))

        query = query.order_by(CreditCard.card_number)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_by_number(self, card_number: str) -> CreditCard | None:
        """
        EXEC CICS READ DATASET(CARDDAT) INTO(CARD-RECORD)
               RIDFLD(WS-CARD-NUM).

        COCRDSLC PROCESS-ENTER-KEY paragraph.
        """
        result = await self.db.execute(
            select(CreditCard).where(CreditCard.card_number == card_number)
        )
        return result.scalar_one_or_none()

    async def update(self, card: CreditCard) -> CreditCard:
        """
        EXEC CICS REWRITE DATASET(CARDDAT) FROM(CARD-RECORD).

        account_id is intentionally NOT updated — ACCTSID is PROT in COCRDUPC.
        SQLAlchemy only updates fields that have been modified on the object.
        The caller must NOT modify card.account_id.
        """
        await self.db.flush()
        await self.db.refresh(card)
        return card
