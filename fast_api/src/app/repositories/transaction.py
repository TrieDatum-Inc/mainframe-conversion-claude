"""Transaction data access repository.

Maps CBTRN02C 2900-WRITE-TRANSACTION-FILE, CBACT04C 1300-B-WRITE-TX,
and CBTRN03C sequential TRANSACT-FILE read.
"""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction


class TransactionRepository:
    """Data access for transactions table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, tran_id: str) -> Transaction | None:
        """Random read by transaction ID."""
        result = await self.db.execute(
            select(Transaction).where(Transaction.tran_id == tran_id)
        )
        return result.scalar_one_or_none()

    async def insert(self, transaction: Transaction) -> Transaction:
        """Write transaction record. Maps CBTRN02C 2900-WRITE-TRANSACTION-FILE."""
        self.db.add(transaction)
        await self.db.flush()
        return transaction

    async def get_by_date_range(self, start_date: date, end_date: date) -> list[Transaction]:
        """Sequential read filtered by processing date range.

        Maps CBTRN03C date range filter:
          IF TRAN-PROC-TS(1:10) >= WS-START-DATE AND <= WS-END-DATE
        Ordered by card_num then proc_ts for account break detection.
        """
        result = await self.db.execute(
            select(Transaction)
            .where(
                Transaction.tran_proc_ts >= datetime.combine(start_date, datetime.min.time()),
                Transaction.tran_proc_ts <= datetime.combine(end_date, datetime.max.time()),
            )
            .order_by(Transaction.tran_card_num, Transaction.tran_proc_ts)
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[Transaction]:
        """Sequential read of all transactions. Maps CBEXPORT 5000-EXPORT-TRANSACTIONS."""
        result = await self.db.execute(
            select(Transaction).order_by(Transaction.tran_id)
        )
        return list(result.scalars().all())
