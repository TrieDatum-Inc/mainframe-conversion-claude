"""
Card-account cross-reference repository.

COBOL origin: Replaces EXEC CICS READ/STARTBR DATASET(CARDAIX/CARDXREF).
  COACTVWC: STARTBR CARDAIX by account_id → find all cards for account
  COTRN02C: READ CCXREF by card_number → get account_id for transaction

VSAM AIX (alternate index) on XREF-ACCT-ID is replaced by
idx_cardxref_account PostgreSQL index.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card_xref import CardAccountXref


class CardXrefRepository:
    """
    Data access operations for the `card_account_xref` table.

    No business logic here — only SQLAlchemy queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_card(self, card_number: str) -> Optional[CardAccountXref]:
        """
        Fetch xref record by card number (primary key).

        COBOL: EXEC CICS READ DATASET(CARDXREF) INTO(CARD-XREF-RECORD)
               RIDFLD(WS-CARD-NUM)
        Used by COTRN02C to look up account_id for a given card_number.
        """
        stmt = select(CardAccountXref).where(CardAccountXref.card_number == card_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_cards_by_account(self, account_id: int) -> List[CardAccountXref]:
        """
        Fetch all xref records for a given account_id.

        COBOL: EXEC CICS STARTBR DATASET(CARDAIX) RIDFLD(WS-ACCT-ID)
               READNEXT loop until account_id changes.
        Uses idx_cardxref_account index (replaces VSAM AIX on XREF-ACCT-ID).
        Used by COACTVWC to enumerate cards associated with an account.
        """
        stmt = (
            select(CardAccountXref)
            .where(CardAccountXref.account_id == account_id)
            .order_by(CardAccountXref.card_number)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
