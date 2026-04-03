from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card_cross_reference import CardCrossReference


class CardXrefRepository:
    """
    Data access layer for card_cross_references table.
    Mirrors both CCXREF (primary key lookup by card_num) and
    CXACAIX (alternate-index lookup by acct_id) from COTRN02C.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_card_num(self, card_num: str) -> CardCrossReference | None:
        """
        Lookup by card number — mirrors READ-CCXREF-FILE:
        EXEC CICS READ DATASET('CCXREF') RIDFLD(XREF-CARD-NUM).
        """
        result = await self._session.execute(
            select(CardCrossReference).where(
                CardCrossReference.xref_card_num == card_num
            )
        )
        return result.scalar_one_or_none()

    async def get_by_acct_id(self, acct_id: str) -> CardCrossReference | None:
        """
        Lookup by account ID — mirrors READ-CXACAIX-FILE:
        EXEC CICS READ DATASET('CXACAIX') RIDFLD(XREF-ACCT-ID).
        """
        result = await self._session.execute(
            select(CardCrossReference).where(
                CardCrossReference.xref_acct_id == acct_id
            )
        )
        return result.scalar_one_or_none()
