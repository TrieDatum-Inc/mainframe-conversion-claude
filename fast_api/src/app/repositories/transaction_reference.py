"""Transaction type and category reference data access.

Maps CBTRN03C 1500-B-LOOKUP-TRANTYPE and 1500-C-LOOKUP-TRANCATG.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction_category import TransactionCategory
from app.models.transaction_type import TransactionType


class TransactionReferenceRepository:
    """Data access for transaction_types and transaction_categories tables."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_type(self, tran_type: str) -> TransactionType | None:
        """Random READ by type code.

        Maps CBTRN03C 1500-B-LOOKUP-TRANTYPE.
        COBOL abends on INVALID KEY; modern equivalent logs warning and returns None.
        """
        result = await self.db.execute(
            select(TransactionType).where(TransactionType.tran_type == tran_type)
        )
        return result.scalar_one_or_none()

    async def get_category(
        self, tran_type: str, tran_cat_cd: str
    ) -> TransactionCategory | None:
        """Random READ by composite key (type + category).

        Maps CBTRN03C 1500-C-LOOKUP-TRANCATG.
        COBOL abends on INVALID KEY; modern equivalent logs warning and returns None.
        """
        result = await self.db.execute(
            select(TransactionCategory).where(
                TransactionCategory.tran_type == tran_type,
                TransactionCategory.tran_cat_cd == tran_cat_cd,
            )
        )
        return result.scalar_one_or_none()
