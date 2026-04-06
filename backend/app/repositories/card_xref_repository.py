"""
CardXref repository — CARDXREF VSAM KSDS + CARDAIX AIX operations.

COBOL origin:
  get_by_card()         → EXEC CICS READ DATASET(CARDXREF) RIDFLD(XREF-CARD-NUM)
  get_cards_by_account() → EXEC CICS STARTBR DATASET(CARDAIX) RIDFLD(XREF-ACCT-ID)
                            + READNEXT loop
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card_xref import CardXref


class CardXrefRepository:
    """
    Data access object for the `card_account_xref` table.

    idx_cardxref_account replaces the VSAM CARDAIX Alternate Index
    on XREF-ACCT-ID, enabling account-based card lookup without VSAM browse.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_card(self, card_number: str) -> CardXref | None:
        """
        EXEC CICS READ DATASET(CARDXREF) INTO(CARD-XREF-RECORD)
               RIDFLD(XREF-CARD-NUM).
        """
        result = await self.db.execute(
            select(CardXref).where(CardXref.card_number == card_number)
        )
        return result.scalar_one_or_none()

    async def get_cards_by_account(self, account_id: int) -> list[CardXref]:
        """
        Browse CARDAIX (Alt Index on XREF-ACCT-ID) for all cards on an account.

        COBOL:
          EXEC CICS STARTBR DATASET(CARDAIX) RIDFLD(WS-ACCT-ID)
          LOOP: EXEC CICS READNEXT → collect XREF-CARD-NUM
          EXEC CICS ENDBR

        Replaced by: SELECT * FROM card_account_xref WHERE account_id = :id
        Uses idx_cardxref_account for performance.
        """
        result = await self.db.execute(
            select(CardXref).where(CardXref.account_id == account_id)
        )
        return list(result.scalars().all())
