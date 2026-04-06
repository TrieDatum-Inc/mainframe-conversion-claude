"""
Data access layer for transactions.

COBOL origin: TRANSACT VSAM KSDS file operations from COTRN00C, COTRN01C, COTRN02C.

Key CICS command replacements:
  STARTBR/READNEXT/READPREV/ENDBR → paginated SELECT with LIMIT/OFFSET
  READ (with UPDATE lock — bug in COTRN01C) → plain SELECT (bug fix)
  WRITE with STARTBR/READPREV-generated ID → INSERT with sequence-generated ID

COTRN01C bug fix documented here:
  Original issued: EXEC CICS READ FILE('TRANSACT') ... UPDATE RESP RESP2
  for a display-only operation. This held an exclusive record lock unnecessarily.
  Replacement: plain SELECT with no lock.
"""

from datetime import date
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction


class TransactionRepository:
    """
    Repository for TRANSACT VSAM KSDS operations.

    COBOL equivalent:
      COTRN00C: STARTBR/READNEXT/READPREV/ENDBR → list_transactions
      COTRN01C: READ UPDATE (bug) → get_by_id (plain SELECT)
      COTRN02C: STARTBR/READPREV/WRITE → create (sequence-based INSERT)
      COBIL00C: STARTBR/READPREV/WRITE → create (same pattern)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_transactions(
        self,
        page: int = 1,
        page_size: int = 10,
        tran_id_filter: Optional[str] = None,
        card_number: Optional[str] = None,
        account_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        type_code: Optional[str] = None,
    ) -> tuple[list[Transaction], int]:
        """
        Paginated transaction list with optional filters.

        COBOL origin: COTRN00C POPULATE-TRAN-DATA paragraph.
          STARTBR TRANSACT RIDFLD(WS-TRAN-ID-SRCH) → WHERE transaction_id >= tran_id_filter
          READNEXT (10 times) → SELECT ... LIMIT 10 OFFSET (page-1)*10
          Look-ahead READNEXT → has_next determined by total_count > page * page_size
          ENDBR → session closed automatically

        COTRN00C browse behavior:
          - With filter: STARTBR at filter key, READNEXT forward = WHERE id >= filter
          - Without filter: STARTBR at LOW-VALUES = no WHERE clause (all records)
          - PF7 (backward): STARTBR at TRNID-FIRST, READPREV → page -= 1
          - PF8 (forward): STARTBR at TRNID-LAST, READNEXT → page += 1
          All replicated by standard SQL pagination.

        account_id filter: joins through card_account_xref to filter by account.
        """
        base_query = select(Transaction).order_by(Transaction.transaction_id.asc())

        # COTRN00C TRNIDINI filter: WHERE transaction_id >= filter (replaces STARTBR with key)
        if tran_id_filter:
            base_query = base_query.where(
                Transaction.transaction_id >= tran_id_filter
            )

        # Card number filter (direct FK)
        if card_number:
            base_query = base_query.where(Transaction.card_number == card_number)

        # Account filter via join to card_account_xref
        if account_id:
            from sqlalchemy.orm import aliased
            from app.models.card_xref import CardAccountXref
            base_query = base_query.join(
                CardAccountXref,
                Transaction.card_number == CardAccountXref.card_number,
            ).where(CardAccountXref.account_id == account_id)

        # Date range filters
        if start_date:
            base_query = base_query.where(Transaction.original_date >= start_date)
        if end_date:
            base_query = base_query.where(Transaction.original_date <= end_date)

        # Type code filter
        if type_code:
            base_query = base_query.where(
                Transaction.transaction_type_code == type_code
            )

        # Total count for pagination envelope
        count_query = select(func.count()).select_from(base_query.subquery())
        total_count = (await self.db.execute(count_query)).scalar_one()

        # Apply pagination
        offset = (page - 1) * page_size
        paginated = base_query.offset(offset).limit(page_size)
        result = await self.db.execute(paginated)
        transactions = list(result.scalars().all())

        return transactions, total_count

    async def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """
        Retrieve a single transaction by ID.

        COBOL origin: COTRN01C PROCESS-ENTER-KEY → READ TRANSACT by TRNIDINI.

        BUG FIX: Original COTRN01C issued READ UPDATE (exclusive lock) for a
        display-only operation. The lock was never used for REWRITE/DELETE.
        This replacement uses a plain SELECT — no lock acquired.

        COBOL: EXEC CICS READ FILE('TRANSACT') INTO(TRAN-RECORD)
               RIDFLD(WS-TRAN-ID) UPDATE RESP RESP2
        Modern: SELECT * FROM transactions WHERE transaction_id = ?
        """
        result = await self.db.execute(
            select(Transaction).where(Transaction.transaction_id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def generate_transaction_id(self) -> str:
        """
        Generate next transaction ID via PostgreSQL sequence.

        COBOL origin: COTRN02C ADD-TRANSACTION / COBIL00C:
          STARTBR TRANSACT RIDFLD(HIGH-VALUES) → position past last record
          READPREV TRANSACT → read last record (highest TRAN-ID)
          ENDBR
          MOVE TRAN-ID TO WS-TRAN-ID-NUM; ADD 1 → new ID

        BUG FIX: The STARTBR/READPREV/ADD-1 pattern is not atomic.
        Two concurrent tasks could both read the same last TRAN-ID and
        generate the same new ID. CICS WRITE DUPKEY was the failure indicator
        but no DUPKEY handling existed in COTRN02C (COBIL00C had handling).
        PostgreSQL NEXTVAL is atomic and safe for concurrent use.

        Format: zero-padded 16-digit string (matching TRAN-ID X(16) in COTRN02Y).
        Empty file case: sequence starts at 1 → '0000000000000001'
        (COTRN02C handled empty file by setting WS-NEW-TRAN-ID = '0000000000000001').
        """
        result = await self.db.execute(text("SELECT NEXTVAL('transaction_id_seq')"))
        seq_val = result.scalar_one()
        return str(seq_val).zfill(16)

    async def create(self, transaction: Transaction) -> Transaction:
        """
        Insert a new transaction record.

        COBOL origin: COTRN02C / COBIL00C WRITE-TRANSACT-FILE:
          EXEC CICS WRITE FILE(WS-TRANSACT-FILE) FROM(TRAN-RECORD)
                    RIDFLD(WS-NEW-TRAN-ID) RESP RESP2

        The transaction_id must be pre-populated via generate_transaction_id()
        before calling this method.
        """
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction

    async def get_last_created(self, limit: int = 1) -> Optional[Transaction]:
        """
        Get the most recently created transaction.

        COBOL origin: COTRN02C PF5 COPY-LAST-TRAN-DATA — copies the last
        successfully added transaction fields back to screen fields for reuse.

        Modern equivalent: SELECT ... ORDER BY transaction_id DESC LIMIT 1
        (transaction_id is sequential so highest = most recent).
        """
        result = await self.db.execute(
            select(Transaction)
            .order_by(Transaction.transaction_id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
