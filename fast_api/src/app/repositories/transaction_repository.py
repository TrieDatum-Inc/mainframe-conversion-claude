"""Transaction repository — data access for TRANSACT VSAM KSDS equivalent.

Maps CICS file commands from COBIL00C to async SQLAlchemy queries.
"""
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class TransactionRepository:
    """Data access for the transactions table.

    CICS equivalents for COBIL00C payment flow:
      STARTBR + READPREV + ENDBR → get_last_tran_id()
      WRITE-TRANSACT-FILE         → create()
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_last_tran_id(self) -> str | None:
        """Get the highest transaction ID in the table.

        COBIL00C pattern (lines 210-215):
          EXEC CICS STARTBR DATASET('TRANSACT') RIDFLD(TRAN-ID) HIGH-VALUES
          EXEC CICS READPREV → gets the last record
          EXEC CICS ENDBR
          If ENDFILE → TRAN-ID = ZEROS (first-ever transaction)

        PostgreSQL equivalent: SELECT MAX(tran_id) which finds the
        lexicographically highest value (same as browse-from-HIGH-VALUES).
        TRAN-ID is a 16-char left-zero-padded numeric string, so
        lexicographic MAX = numeric MAX.
        """
        result = await self._session.execute(
            select(func.max(Transaction.tran_id))
        )
        return result.scalar_one_or_none()

    async def generate_next_tran_id(self) -> str:
        """Generate next sequential transaction ID.

        COBIL00C lines 216-219:
          MOVE TRAN-ID TO WS-TRAN-ID-NUM (numeric)
          ADD 1 TO WS-TRAN-ID-NUM
          INITIALIZE TRAN-RECORD
          MOVE WS-TRAN-ID-NUM TO TRAN-ID

        WS-TRAN-ID-NUM is PIC 9(16), so max value is 9999999999999999.
        TRAN-ID is PIC X(16), stored left-zero-padded.
        If ENDFILE (no transactions exist), starts at '0000000000000001'.
        """
        last_id = await self.get_last_tran_id()
        if last_id is None:
            # COBIL00C: ENDFILE → MOVE ZEROS TO TRAN-ID, then ADD 1
            return "0000000000000001"
        next_num = int(last_id) + 1
        return str(next_num).zfill(16)

    async def create(self, transaction: Transaction) -> Transaction:
        """Insert a new transaction record.

        Maps: EXEC CICS WRITE DATASET('TRANSACT') FROM(TRAN-RECORD) RIDFLD(TRAN-ID)
        COBIL00C WRITE-TRANSACT-FILE paragraph (line 510).
        """
        self._session.add(transaction)
        await self._session.flush()  # Assigns generated values; does not commit
        await self._session.refresh(transaction)
        return transaction
