from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction


class TransactionRepository:
    """
    Data access layer for the transactions table.
    Mirrors TRANSACT VSAM KSDS operations from COTRN00C/COTRN01C/COTRN02C.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, tran_id: str) -> Transaction | None:
        """Direct key read — mirrors CICS READ DATASET('TRANSACT') RIDFLD(TRAN-ID)."""
        result = await self._session.execute(
            select(Transaction).where(Transaction.tran_id == tran_id)
        )
        return result.scalar_one_or_none()

    async def get_page_forward(
        self,
        start_tran_id: str | None,
        page_size: int,
    ) -> list[Transaction]:
        """
        Fetch up to page_size records in ascending key order starting AT or AFTER start_tran_id.
        Mirrors CICS STARTBR + READNEXT loop in PROCESS-PAGE-FORWARD.
        When start_tran_id is None, reads from the beginning (LOW-VALUES equivalent).
        """
        stmt = select(Transaction).order_by(Transaction.tran_id.asc())
        if start_tran_id:
            stmt = stmt.where(Transaction.tran_id >= start_tran_id)
        stmt = stmt.limit(page_size + 1)  # fetch one extra to detect next page
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_page_backward(
        self,
        end_tran_id: str,
        page_size: int,
    ) -> list[Transaction]:
        """
        Fetch up to page_size records in descending key order starting AT or BEFORE end_tran_id.
        Mirrors CICS STARTBR + READPREV loop in PROCESS-PAGE-BACKWARD.
        Results are returned in ascending order for display.
        """
        stmt = (
            select(Transaction)
            .where(Transaction.tran_id <= end_tran_id)
            .order_by(Transaction.tran_id.desc())
            .limit(page_size + 1)
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        # Reverse to get ascending display order (COBOL fills rows 10 down to 1 then displays)
        rows.reverse()
        return rows

    async def get_last_transaction(self) -> Transaction | None:
        """
        Read highest-keyed record — mirrors COTRN02C ADD-TRANSACTION:
        TRAN-ID = HIGH-VALUES, STARTBR, READPREV.
        """
        result = await self._session.execute(
            select(Transaction).order_by(Transaction.tran_id.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_next_sequence_id(self) -> str:
        """
        Generate the next transaction ID.
        Mirrors COTRN02C auto-increment: read last record, add 1 to numeric ID.
        Returns a 16-digit zero-padded string matching PIC 9(16).
        """
        last = await self.get_last_transaction()
        if last is None:
            # Empty file — mirrors READPREV ENDFILE → ZEROS + 1
            next_id = 1
        else:
            try:
                next_id = int(last.tran_id) + 1
            except ValueError:
                # Fallback: use DB sequence
                result = await self._session.execute(text("SELECT nextval('transaction_id_seq')"))
                next_id = result.scalar_one()
        return str(next_id).zfill(16)

    async def create(self, transaction: Transaction) -> Transaction:
        """Write new transaction record — mirrors CICS WRITE DATASET('TRANSACT')."""
        self._session.add(transaction)
        await self._session.flush()
        await self._session.refresh(transaction)
        return transaction

    async def exists(self, tran_id: str) -> bool:
        """Check if a transaction ID already exists (DUPKEY detection)."""
        result = await self._session.execute(
            select(func.count()).where(Transaction.tran_id == tran_id)
        )
        return (result.scalar_one() or 0) > 0
