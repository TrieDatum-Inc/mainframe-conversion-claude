"""
Transaction repository — data access layer for TRANSACT VSAM file operations.

Maps CICS file operations:
  EXEC CICS READ    FILE(TRANSACT) RIDFLD(TRAN-ID)     → get_by_id()
  EXEC CICS WRITE   FILE(TRANSACT) FROM(TRAN-RECORD)   → create()
  EXEC CICS STARTBR FILE(TRANSACT) RIDFLD(TRAN-ID) GTEQ → list_paginated() (keyset)
  EXEC CICS READNEXT FILE(TRANSACT)                    → list_paginated() forward

Source programs: COTRN00C, COTRN01C, COTRN02C, COBIL00C
"""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.utils.cobol_compat import cobol_move_x
from app.utils.error_handlers import RecordNotFoundError


class TransactionRepository:
    """Data access object for the `transactions` table (TRANSACT VSAM)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, tran_id: str) -> Transaction:
        """
        EXEC CICS READ FILE('TRANSACT') INTO(TRAN-RECORD) RIDFLD(WS-TRAN-ID)

        COTRN01C view-transaction paragraph.
        RESP=13 (NOTFND) → RecordNotFoundError.
        """
        tran_id_padded = cobol_move_x(tran_id, 16)
        txn = await self._db.get(Transaction, tran_id_padded)
        if txn is None:
            raise RecordNotFoundError(f"Transaction not found (id={tran_id!r})")
        return txn

    async def create(self, transaction: Transaction) -> Transaction:
        """
        EXEC CICS WRITE FILE('TRANSACT') FROM(TRAN-RECORD)

        Used by COTRN02C (manual entry) and COBIL00C (bill payment).
        TRAN-ID must be unique (16-char key).
        """
        self._db.add(transaction)
        await self._db.flush()
        return transaction

    async def list_paginated(
        self,
        cursor: str | None = None,
        limit: int = 10,
        card_num: str | None = None,
        acct_id: int | None = None,
        direction: str = "forward",
    ) -> tuple[list[Transaction], int, bool]:
        """
        EXEC CICS STARTBR FILE('TRANSACT') RIDFLD(WS-TRAN-ID) GTEQ
        EXEC CICS READNEXT FILE('TRANSACT') INTO(TRAN-RECORD)

        COTRN00C browse-transactions paragraph.
        Keyset pagination on TRAN-ID (ascending sequential browse).

        CDEMO-CT00-TRNID-FIRST / CDEMO-CT00-TRNID-LAST track page boundaries.

        Args:
            cursor: Last tran_id from previous page (CDEMO-CT00-TRNID-LAST).
            limit: Page size (COTRN00C: 10 rows per screen).
            card_num: Filter by TRAN-CARD-NUM (COTRN00C card filter).
            acct_id: Filter by account ID (derived field).

        Returns:
            Tuple of (transaction list, total count).
        """
        base_filters = []
        if card_num:
            base_filters.append(Transaction.card_num == cobol_move_x(card_num, 16))
        if acct_id:
            base_filters.append(Transaction.acct_id == acct_id)

        count_stmt = select(func.count(Transaction.tran_id)).where(*base_filters)
        total = (await self._db.execute(count_stmt)).scalar_one()

        stmt = select(Transaction).where(*base_filters)
        if direction == "backward":
            stmt = stmt.order_by(Transaction.tran_id.desc())
            if cursor:
                stmt = stmt.where(Transaction.tran_id < cobol_move_x(cursor, 16))
        else:
            stmt = stmt.order_by(Transaction.tran_id)
            if cursor:
                stmt = stmt.where(Transaction.tran_id > cobol_move_x(cursor, 16))
        stmt = stmt.limit(limit + 1)

        result = await self._db.execute(stmt)
        rows = list(result.scalars().all())
        has_more = len(rows) > limit
        rows = rows[:limit]
        if direction == "backward":
            rows = list(reversed(rows))
        return rows, total, has_more

    async def get_total_amount_by_account(self, acct_id: int) -> Decimal:
        """Sum of all transaction amounts for an account."""
        stmt = select(func.sum(Transaction.amount)).where(Transaction.acct_id == acct_id)
        result = (await self._db.execute(stmt)).scalar_one_or_none()
        return result or Decimal("0.00")
