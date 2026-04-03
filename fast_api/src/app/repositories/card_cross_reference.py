"""Card cross-reference data access repository.

Maps CBTRN02C 1500-A-LOOKUP-XREF, CBACT04C 1110-GET-XREF-DATA,
and CBTRN03C 1500-A-LOOKUP-XREF.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card_cross_reference import CardCrossReference


class CardCrossReferenceRepository:
    """Data access for card_cross_references table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_card_num(self, card_num: str) -> CardCrossReference | None:
        """Random READ by card number (primary key).

        Maps CBTRN02C 1500-A-LOOKUP-XREF and CBTRN03C 1500-A-LOOKUP-XREF.
        INVALID KEY equivalent: returns None.
        """
        result = await self.db.execute(
            select(CardCrossReference).where(
                CardCrossReference.xref_card_num == card_num
            )
        )
        return result.scalar_one_or_none()

    async def get_by_acct_id(self, acct_id: str) -> CardCrossReference | None:
        """Random READ by account ID (alternate key).

        Maps CBACT04C 1110-GET-XREF-DATA which reads XREF-FILE by FD-XREF-ACCT-ID.
        Returns first matching xref (assumes one card per account for interest calc).
        """
        result = await self.db.execute(
            select(CardCrossReference).where(
                CardCrossReference.xref_acct_id == acct_id
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[CardCrossReference]:
        """Sequential read of all xrefs. Maps CBEXPORT 4000-EXPORT-XREFS."""
        result = await self.db.execute(
            select(CardCrossReference).order_by(CardCrossReference.xref_card_num)
        )
        return list(result.scalars().all())

    async def upsert(self, xref: CardCrossReference) -> CardCrossReference:
        """Insert or update a cross-reference record."""
        existing = await self.get_by_card_num(xref.xref_card_num)
        if existing:
            existing.xref_cust_id = xref.xref_cust_id
            existing.xref_acct_id = xref.xref_acct_id
            await self.db.flush()
            return existing
        self.db.add(xref)
        await self.db.flush()
        return xref
