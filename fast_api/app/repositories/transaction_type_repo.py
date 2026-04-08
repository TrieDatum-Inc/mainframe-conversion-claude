"""
Transaction type repository — data access layer for CARDDEMO.TRANSACTION_TYPE.

Source programs: COTRTLIC, COTRTUPC
DB2 table: CARDDEMO.TRANSACTION_TYPE  (TR_TYPE CHAR(2), TR_DESCRIPTION CHAR(50))

DB2 operations mapped:
  DECLARE C-TR-TYPE-FORWARD CURSOR  → list_paginated_forward()
  DECLARE C-TR-TYPE-BACKWARD CURSOR → list_paginated_backward()
  9000-READ-TRANTYPE  (SELECT ... WHERE TR_TYPE = :key) → get_by_type_cd()
  9600-WRITE-PROCESSING (UPDATE ... SET TR_DESCRIPTION = ...) → update_description()
  9300-DELETE-RECORD  (DELETE ... WHERE TR_TYPE = :key)      → delete()

Pagination mirrors COTRTLIC WS-MAX-SCREEN-LINES = 7 rows per screen.
The WS-START-KEY / WS-CA-LAST-TR-CODE / WS-CA-FIRST-TR-CODE commarea fields
map directly to cursor-keyset pagination here.
"""
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import TransactionType
from app.utils.error_handlers import DuplicateRecordError, RecordNotFoundError

# COTRTLIC WS-MAX-SCREEN-LINES PIC S9(4) COMP VALUE 7
DEFAULT_PAGE_SIZE = 7


class TransactionTypeRepository:
    """Data access object for CARDDEMO.TRANSACTION_TYPE (PostgreSQL: transaction_types)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_type_cd(self, type_cd: str) -> TransactionType:
        """
        COTRTUPC 9000-READ-TRANTYPE paragraph.

        SQL:
          SELECT TR_TYPE, TR_DESCRIPTION
          FROM   CARDDEMO.TRANSACTION_TYPE
          WHERE  TR_TYPE = :TTUP-NEW-TTYP-TYPE

        SQLCODE = 100 (not found) → RecordNotFoundError.

        Args:
            type_cd: TR_TYPE value, 1-2 chars.

        Returns:
            TransactionType ORM instance.

        Raises:
            RecordNotFoundError: No record found (COTRTUPC: 'No record found for this key in database').
        """
        normalized = type_cd.strip().upper().zfill(2)
        result = await self._db.get(TransactionType, normalized)
        if result is None:
            raise RecordNotFoundError(
                f"Transaction type not found (type_cd={normalized!r})"
            )
        return result

    async def list_paginated_forward(
        self,
        cursor: str | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
        type_cd_filter: str | None = None,
        desc_filter: str | None = None,
    ) -> tuple[list[TransactionType], int, bool]:
        """
        COTRTLIC 8000-READ-FORWARD paragraph.

        Mirrors DB2 cursor C-TR-TYPE-FORWARD:
          SELECT TR_TYPE, TR_DESCRIPTION
          FROM   CARDDEMO.TRANSACTION_TYPE
          WHERE  TR_TYPE >= :WS-START-KEY
          AND    ((:WS-EDIT-TYPE-FLAG='1' AND TR_TYPE=:WS-TYPE-CD-FILTER) OR ...)
          AND    ((:WS-EDIT-DESC-FLAG='1' AND TR_DESCRIPTION LIKE ...) OR ...)
          ORDER  BY TR_TYPE
          FETCH  FIRST :WS-MAX-SCREEN-LINES ROWS ONLY

        Args:
            cursor: WS-START-KEY (WS-CA-LAST-TR-CODE from previous page).
                    None → start from beginning (CA-FIRST-PAGE).
            limit:  Page size (default 7 = WS-MAX-SCREEN-LINES).
            type_cd_filter: WS-TYPE-CD-FILTER — exact match on TR_TYPE.
            desc_filter:    WS-TYPE-DESC-FILTER — LIKE pattern on TR_DESCRIPTION.

        Returns:
            (list[TransactionType], total_count)
        """
        stmt = select(TransactionType).order_by(TransactionType.type_cd)
        count_stmt = select(func.count()).select_from(TransactionType)

        if cursor:
            stmt = stmt.where(TransactionType.type_cd > cursor.strip().zfill(2))

        if type_cd_filter and type_cd_filter.strip():
            normalized = type_cd_filter.strip().upper().zfill(2)
            stmt = stmt.where(TransactionType.type_cd == normalized)
            count_stmt = count_stmt.where(TransactionType.type_cd == normalized)

        if desc_filter and desc_filter.strip():
            pattern = f"%{desc_filter.strip()}%"
            stmt = stmt.where(TransactionType.description.ilike(pattern))
            count_stmt = count_stmt.where(TransactionType.description.ilike(pattern))

        # Fetch one extra to detect if next page exists
        stmt = stmt.limit(limit + 1)

        result = await self._db.execute(stmt)
        rows = list(result.scalars().all())
        has_more = len(rows) > limit
        rows = rows[:limit]

        total_result = await self._db.execute(count_stmt)
        total = total_result.scalar_one()

        return rows, total, has_more

    async def list_paginated_backward(
        self,
        cursor: str,
        limit: int = DEFAULT_PAGE_SIZE,
        type_cd_filter: str | None = None,
        desc_filter: str | None = None,
    ) -> tuple[list[TransactionType], int, bool]:
        """
        COTRTLIC 8100-READ-BACKWARDS paragraph.

        Mirrors DB2 cursor C-TR-TYPE-BACKWARD:
          SELECT TR_TYPE, TR_DESCRIPTION
          FROM   CARDDEMO.TRANSACTION_TYPE
          WHERE  TR_TYPE < :WS-START-KEY
          AND    ... (same filters)
          ORDER  BY TR_TYPE DESC

        Used for PF7 (page up) navigation.

        Args:
            cursor: WS-CA-FIRST-TR-CODE (first key on current page).
            limit:  Page size.
            type_cd_filter: Optional TR_TYPE exact match.
            desc_filter:    Optional TR_DESCRIPTION LIKE filter.

        Returns:
            (list[TransactionType] in ascending order, total_count)
        """
        stmt = (
            select(TransactionType)
            .where(TransactionType.type_cd < cursor.strip().zfill(2))
            .order_by(TransactionType.type_cd.desc())
        )
        count_stmt = select(func.count()).select_from(TransactionType)

        if type_cd_filter and type_cd_filter.strip():
            normalized = type_cd_filter.strip().upper().zfill(2)
            stmt = stmt.where(TransactionType.type_cd == normalized)
            count_stmt = count_stmt.where(TransactionType.type_cd == normalized)

        if desc_filter and desc_filter.strip():
            pattern = f"%{desc_filter.strip()}%"
            stmt = stmt.where(TransactionType.description.ilike(pattern))
            count_stmt = count_stmt.where(TransactionType.description.ilike(pattern))

        stmt = stmt.limit(limit + 1)

        result = await self._db.execute(stmt)
        rows = list(result.scalars().all())
        has_more = len(rows) > limit
        rows = rows[:limit]

        total_result = await self._db.execute(count_stmt)
        total = total_result.scalar_one()

        # Return in ascending order (reverse the DESC fetch)
        return list(reversed(rows)), total, has_more

    async def update_description(
        self, type_cd: str, new_description: str
    ) -> TransactionType:
        """
        COTRTUPC 9600-WRITE-PROCESSING paragraph.

        SQL:
          UPDATE CARDDEMO.TRANSACTION_TYPE
          SET    TR_DESCRIPTION = :TTUP-NEW-TTYP-TYPE-DESC
          WHERE  TR_TYPE = :TTUP-OLD-TTYP-TYPE

        COTRTUPC first verifies old record (9000-READ-TRANTYPE) then updates.
        Optimistic lock check: description must differ from stored value
        (COTRTUPC 1205-COMPARE-OLD-NEW logic).

        Args:
            type_cd:         TR_TYPE key (TTUP-OLD-TTYP-TYPE).
            new_description: New TR_DESCRIPTION (TTUP-NEW-TTYP-TYPE-DESC).

        Returns:
            Updated TransactionType instance.

        Raises:
            RecordNotFoundError: Record disappeared before update.
        """
        record = await self.get_by_type_cd(type_cd)

        # COTRTUPC 1205-COMPARE-OLD-NEW: detect if description actually changed
        # FUNCTION UPPER-CASE(FUNCTION TRIM(TTUP-NEW-TTYP-TYPE-DESC)) = ...
        if record.description.strip().upper() == new_description.strip().upper():
            # No actual change — COTRTUPC sets NO-CHANGES-DETECTED
            return record

        record.description = new_description[:50]
        await self._db.flush()
        await self._db.refresh(record)
        return record

    async def delete(self, type_cd: str) -> None:
        """
        COTRTLIC 9300-DELETE-RECORD paragraph.

        SQL:
          DELETE FROM CARDDEMO.TRANSACTION_TYPE
          WHERE TR_TYPE IN (:WS-TYPE-CD-DELETE-KEYS...)

        Args:
            type_cd: TR_TYPE key to delete.

        Raises:
            RecordNotFoundError: Record not found.
        """
        record = await self.get_by_type_cd(type_cd)
        await self._db.delete(record)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise DuplicateRecordError(
                f"Transaction type '{type_cd}' is in use by existing transactions and cannot be deleted."
            ) from exc

    async def create(self, type_cd: str, description: str) -> TransactionType:
        """
        COTRTUPC create-new-record flow (TTUP-CREATE-NEW-RECORD → 9600-WRITE-PROCESSING INSERT).

        SQL:
          INSERT INTO CARDDEMO.TRANSACTION_TYPE (TR_TYPE, TR_DESCRIPTION)
          VALUES (:type_cd, :description)

        Args:
            type_cd:     New TR_TYPE (2-char numeric string, zero-padded).
            description: TR_DESCRIPTION.

        Returns:
            Newly created TransactionType.

        Raises:
            DuplicateRecordError: TR_TYPE already exists.
        """
        normalized = type_cd.strip().upper().zfill(2)
        existing = await self._db.get(TransactionType, normalized)
        if existing is not None:
            raise DuplicateRecordError(
                f"Transaction type already exists (type_cd={normalized!r})"
            )
        record = TransactionType(type_cd=normalized, description=description[:50])
        self._db.add(record)
        await self._db.flush()
        await self._db.refresh(record)
        return record
