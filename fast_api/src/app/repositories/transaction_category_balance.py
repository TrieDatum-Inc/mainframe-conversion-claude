"""Transaction category balance data access repository.

Maps CBTRN02C 2700-UPDATE-TCATBAL and CBACT04C sequential TCATBALF read.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction_category_balance import TransactionCategoryBalance


class TransactionCategoryBalanceRepository:
    """Data access for transaction_category_balances table (TCATBALF KSDS / CVTRA01Y)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(
        self, acct_id: str, tran_type_cd: str, tran_cat_cd: str
    ) -> TransactionCategoryBalance | None:
        """Random READ by composite key.

        Maps CBTRN02C 2700-UPDATE-TCATBAL READ by FD-TRAN-CAT-KEY.
        INVALID KEY (status '23') equivalent: returns None.
        """
        result = await self.db.execute(
            select(TransactionCategoryBalance).where(
                TransactionCategoryBalance.acct_id == acct_id,
                TransactionCategoryBalance.tran_type_cd == tran_type_cd,
                TransactionCategoryBalance.tran_cat_cd == tran_cat_cd,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        acct_id: str,
        tran_type_cd: str,
        tran_cat_cd: str,
        amount_delta: Decimal,
    ) -> TransactionCategoryBalance:
        """Create or update category balance.

        Maps CBTRN02C 2700-A-CREATE-TCATBAL-REC (new record)
        and 2700-B-UPDATE-TCATBAL-REC (existing: ADD DALYTRAN-AMT TO TRAN-CAT-BAL).
        """
        record = await self.get(acct_id, tran_type_cd, tran_cat_cd)
        if record is None:
            record = TransactionCategoryBalance(
                acct_id=acct_id,
                tran_type_cd=tran_type_cd,
                tran_cat_cd=tran_cat_cd,
                balance=amount_delta,
            )
            self.db.add(record)
        else:
            record.balance = (record.balance or Decimal("0")) + amount_delta

        await self.db.flush()
        return record

    async def get_all_ordered_by_account(self) -> list[TransactionCategoryBalance]:
        """Sequential read ordered by account ID.

        Maps CBACT04C main loop: TCATBALF sorted by TRANCAT-ACCT-ID.
        The account break detection requires sorted order.
        """
        result = await self.db.execute(
            select(TransactionCategoryBalance).order_by(
                TransactionCategoryBalance.acct_id,
                TransactionCategoryBalance.tran_type_cd,
                TransactionCategoryBalance.tran_cat_cd,
            )
        )
        return list(result.scalars().all())
