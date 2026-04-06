"""
Data access layer for the transaction_types table.

COBOL origin: COTRTLIC (DB2 cursor SELECT) and COTRTUPC (SELECT/INSERT/UPDATE/DELETE).

This repository replaces all DB2 SQL operations from both programs:
  COTRTLIC 9400-OPEN-FORWARD-CURSOR + 8000-READ-FORWARD  → list_all (forward pagination)
  COTRTLIC 9500-OPEN-BACKWARD-CURSOR + 8100-READ-BACKWARDS → list_all (backward via page)
  COTRTLIC 9100-CHECK-FILTERS                             → (merged into list_all count query)
  COTRTUPC 9100-GET-TRANSACTION-TYPE                      → get_by_code
  COTRTUPC 9600-WRITE-PROCESSING (INSERT path)            → create
  COTRTUPC 9600-WRITE-PROCESSING (UPDATE path)            → update
  COTRTUPC 9800-DELETE-PROCESSING                         → delete

No business logic lives here — only database operations.
"""

from typing import Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction_type import TransactionType


class TransactionTypeRepository:
    """
    Repository for all transaction_types database operations.

    COBOL equivalent: EXEC SQL statements in COTRTLIC and COTRTUPC.
    All methods accept an async SQLAlchemy session (replaces DB2 connection/cursor).
    """

    async def list_all(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 7,
        type_code_filter: Optional[str] = None,
        description_filter: Optional[str] = None,
    ) -> tuple[list[TransactionType], int]:
        """
        Paginated list of transaction types with optional filters.

        COBOL origin: COTRTLIC 8000-READ-FORWARD and 9100-CHECK-FILTERS.
          Forward cursor: WHERE TR_TYPE >= :start_key ORDER BY TR_TYPE
          Description filter: LIKE '%filter%' (1230-EDIT-DESC wraps with %)
          Type code filter: exact match (1220-EDIT-TYPECD)

        Returns (items, total_count) — total_count replaces COTRTLIC's
        COUNT(1) check in 9100-CHECK-FILTERS for 'no records' detection.

        Bidirectional paging is handled by offset/limit (replaces forward/backward cursors).
        """
        base_query = select(TransactionType)

        # COTRTLIC 1220-EDIT-TYPECD: exact type code filter
        if type_code_filter:
            base_query = base_query.where(
                TransactionType.type_code == type_code_filter
            )

        # COTRTLIC 1230-EDIT-DESC: description LIKE '%filter%'
        # Original: WS-TYPE-DESC-FILTER wrapped with '%' on both sides
        if description_filter:
            base_query = base_query.where(
                TransactionType.description.ilike(f"%{description_filter}%")
            )

        # Count query for pagination metadata (replaces COTRTLIC 9100-CHECK-FILTERS COUNT)
        count_query = select(func.count()).select_from(base_query.subquery())
        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()

        # Data query with ORDER BY and pagination
        # COTRTLIC C-TR-TYPE-FORWARD cursor ORDER BY TR_TYPE ASC
        offset = (page - 1) * page_size
        data_query = (
            base_query
            .order_by(TransactionType.type_code.asc())
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(data_query)
        items = list(result.scalars().all())

        return items, total_count

    async def get_by_code(
        self,
        db: AsyncSession,
        type_code: str,
    ) -> Optional[TransactionType]:
        """
        Fetch a single transaction type record by primary key.

        COBOL origin: COTRTUPC 9100-GET-TRANSACTION-TYPE.
          SELECT TR_TYPE, TR_DESCRIPTION
          FROM CARDDEMO.TRANSACTION_TYPE
          WHERE TR_TYPE = :key

        Returns None when not found (replaces SQLCODE +100 / NOT FOUND condition).
        """
        result = await db.execute(
            select(TransactionType).where(TransactionType.type_code == type_code)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        type_code: str,
        description: str,
    ) -> TransactionType:
        """
        Insert a new transaction type record.

        COBOL origin: COTRTUPC 9700-INSERT-RECORD.
          INSERT INTO CARDDEMO.TRANSACTION_TYPE (TR_TYPE, TR_DESCRIPTION)
          VALUES (:DCL-TR-TYPE, :DCL-TR-DESCRIPTION)
          followed by EXEC CICS SYNCPOINT on success.

        Raises IntegrityError if type_code already exists (replaces SQLCODE -803 duplicate key).
        The service layer catches this and returns 409 Conflict.
        """
        new_type = TransactionType(type_code=type_code, description=description)
        db.add(new_type)
        await db.flush()  # Flush to get DB-assigned timestamps without full commit
        await db.refresh(new_type)
        return new_type

    async def update(
        self,
        db: AsyncSession,
        type_code: str,
        description: str,
    ) -> Optional[TransactionType]:
        """
        Update the description of an existing transaction type.

        COBOL origin: COTRTLIC 9200-UPDATE-RECORD and COTRTUPC 9600-WRITE-PROCESSING (UPDATE).
          UPDATE CARDDEMO.TRANSACTION_TYPE
          SET TR_DESCRIPTION = :DCL-TR-DESCRIPTION
          WHERE TR_TYPE = :DCL-TR-TYPE
          followed by EXEC CICS SYNCPOINT on SQLCODE=0.

        Returns the updated record, or None if not found (replaced by service-layer check).
        The updated_at timestamp is automatically refreshed by the database trigger.
        """
        stmt = (
            update(TransactionType)
            .where(TransactionType.type_code == type_code)
            .values(description=description)
            .returning(TransactionType)
        )
        result = await db.execute(stmt)
        updated = result.scalar_one_or_none()
        if updated:
            await db.refresh(updated)
        return updated

    async def delete(
        self,
        db: AsyncSession,
        type_code: str,
    ) -> bool:
        """
        Delete a transaction type record by type_code.

        COBOL origin: COTRTLIC 9300-DELETE-RECORD and COTRTUPC 9800-DELETE-PROCESSING.
          DELETE FROM CARDDEMO.TRANSACTION_TYPE
          WHERE TR_TYPE = :DCL-TR-TYPE
          SQLCODE -532: FK violation → 'Please delete associated child records first'
          SQLCODE 0:   EXEC CICS SYNCPOINT; success

        Raises IntegrityError on FK violation (transactions.transaction_type_code FK).
        The service layer catches this and returns 409 Conflict.

        Returns True if a row was deleted, False if not found.
        """
        stmt = (
            delete(TransactionType)
            .where(TransactionType.type_code == type_code)
            .returning(TransactionType.type_code)
        )
        result = await db.execute(stmt)
        deleted_key = result.scalar_one_or_none()
        return deleted_key is not None

    async def exists(
        self,
        db: AsyncSession,
        type_code: str,
    ) -> bool:
        """
        Check whether a transaction type exists by type_code.

        Used by the service to detect duplicates before INSERT
        (replaces COTRTUPC SELECT + SQLCODE check before deciding INSERT vs UPDATE).
        """
        result = await db.execute(
            select(TransactionType.type_code).where(
                TransactionType.type_code == type_code
            )
        )
        return result.scalar_one_or_none() is not None
