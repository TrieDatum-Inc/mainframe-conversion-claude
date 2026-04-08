"""
Transaction type service — business logic from COTRTLIC and COTRTUPC.

Source programs:
  app/app-transaction-type-db2/cbl/COTRTLIC.cbl  — List (CICS CTLI)
  app/app-transaction-type-db2/cbl/COTRTUPC.cbl  — Update (CICS CTTU)

DB2 table: CARDDEMO.TRANSACTION_TYPE

COTRTLIC paragraph mapping:
  8000-READ-FORWARD    → list_transaction_types() (forward pagination)
  8100-READ-BACKWARDS  → list_transaction_types() (backward pagination via cursor)
  9300-DELETE-RECORD   → delete_transaction_type()

COTRTUPC paragraph mapping:
  9000-READ-TRANTYPE      → get_transaction_type()
  1200-EDIT-MAP-INPUTS    → (validation in schema layer)
  1205-COMPARE-OLD-NEW    → update_transaction_type() no-change detection
  9600-WRITE-PROCESSING   → update_transaction_type()
  TTUP-CREATE-NEW-RECORD  → create_transaction_type()

Business rules:
  1. type_cd must be 2-char, numeric, non-zero
     (COTRTUPC 1245-EDIT-NUM-REQD: FUNCTION TEST-NUMVAL + FUNCTION NUMVAL != 0)
  2. description: alphanumeric + spaces only, max 50 chars, non-blank
     (COTRTUPC 1230-EDIT-ALPHANUM-REQD)
  3. Case-insensitive description comparison for change detection
     (COTRTUPC 1205-COMPARE-OLD-NEW: FUNCTION UPPER-CASE comparison)
  4. Page size = 7 (COTRTLIC WS-MAX-SCREEN-LINES PIC S9(4) COMP VALUE 7)
  5. Forward pagination: WHERE TR_TYPE >= :cursor ORDER BY TR_TYPE
     (COTRTLIC C-TR-TYPE-FORWARD cursor)
  6. Backward pagination: WHERE TR_TYPE < :cursor ORDER BY TR_TYPE DESC
     (COTRTLIC C-TR-TYPE-BACKWARD cursor)
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import TransactionType
from app.repositories.transaction_type_repo import DEFAULT_PAGE_SIZE, TransactionTypeRepository
from app.schemas.transaction_type import (
    TransactionTypeListResponse,
    TransactionTypeResponse,
    TransactionTypeUpdateRequest,
)
from app.utils.error_handlers import ValidationError

# COTRTLIC WS-MAX-SCREEN-LINES
MAX_PAGE_SIZE = DEFAULT_PAGE_SIZE


class TransactionTypeService:
    """Business logic for COTRTLIC and COTRTUPC programs."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = TransactionTypeRepository(db)

    async def list_transaction_types(
        self,
        cursor: str | None = None,
        direction: str = "forward",
        limit: int = MAX_PAGE_SIZE,
        type_cd_filter: str | None = None,
        desc_filter: str | None = None,
    ) -> TransactionTypeListResponse:
        """
        COTRTLIC 8000-READ-FORWARD / 8100-READ-BACKWARDS paragraph.

        Cursor-keyset pagination mapping:
          forward  (PF8): WHERE TR_TYPE >= :cursor ORDER BY TR_TYPE
                          cursor = WS-CA-LAST-TR-CODE (last key from previous page)
          backward (PF7): WHERE TR_TYPE < :cursor ORDER BY TR_TYPE DESC (then reverse)
                          cursor = WS-CA-FIRST-TR-CODE (first key from current page)

        COTRTLIC WS-MAX-SCREEN-LINES = 7 rows per page. We fetch limit+1 to detect
        whether a next page exists (CA-NEXT-PAGE-EXISTS check).

        Filter flags:
          FLG-TYPEFILTER-ISVALID (WS-EDIT-TYPE-FLAG='1') → type_cd_filter applied
          FLG-DESCFILTER-ISVALID (WS-EDIT-DESC-FLAG='1') → desc_filter applied

        Args:
            cursor:         Start key for pagination.
            direction:      'forward' (PF8/Enter) or 'backward' (PF7).
            limit:          Rows per page (default 7).
            type_cd_filter: WS-TYPE-CD-FILTER — optional exact type match.
            desc_filter:    WS-TYPE-DESC-FILTER — optional description LIKE match.

        Returns:
            TransactionTypeListResponse with items and cursor values.
        """
        effective_limit = min(limit, MAX_PAGE_SIZE)

        if direction == "backward" and cursor:
            rows, total, has_more = await self._repo.list_paginated_backward(
                cursor=cursor,
                limit=effective_limit,
                type_cd_filter=type_cd_filter,
                desc_filter=desc_filter,
            )
            has_prev = has_more
            has_next = cursor is not None
        else:
            rows, total, has_more = await self._repo.list_paginated_forward(
                cursor=cursor,
                limit=effective_limit,
                type_cd_filter=type_cd_filter,
                desc_filter=desc_filter,
            )
            has_next = has_more
            has_prev = cursor is not None

        items = [self._build_response(r) for r in rows]

        return TransactionTypeListResponse(
            items=items,
            total=total,
            next_cursor=rows[-1].type_cd if has_next and rows else None,
            prev_cursor=rows[0].type_cd if has_prev and rows else None,
        )

    async def get_transaction_type(self, type_cd: str) -> TransactionTypeResponse:
        """
        COTRTUPC 9000-READ-TRANTYPE paragraph.

        SQL: SELECT TR_TYPE, TR_DESCRIPTION
             FROM CARDDEMO.TRANSACTION_TYPE WHERE TR_TYPE = :key

        Raises RecordNotFoundError if not found (SQLCODE = 100).

        Args:
            type_cd: TR_TYPE key.

        Returns:
            TransactionTypeResponse.
        """
        record = await self._repo.get_by_type_cd(type_cd)
        return self._build_response(record)

    async def update_transaction_type(
        self, type_cd: str, request: TransactionTypeUpdateRequest
    ) -> TransactionTypeResponse:
        """
        COTRTUPC 9600-WRITE-PROCESSING paragraph.

        Business rules:
          1. Record must exist (9000-READ-TRANTYPE first)
          2. New description must differ from stored value
             (COTRTUPC 1205-COMPARE-OLD-NEW: FUNCTION UPPER-CASE comparison)
          3. Update committed via DB2 UPDATE statement

        SQL (9600-WRITE-PROCESSING):
          UPDATE CARDDEMO.TRANSACTION_TYPE
          SET    TR_DESCRIPTION = :TTUP-NEW-TTYP-TYPE-DESC
          WHERE  TR_TYPE = :TTUP-OLD-TTYP-TYPE

        Args:
            type_cd: TR_TYPE key (TTUP-OLD-TTYP-TYPE).
            request: Contains new description (TTUP-NEW-TTYP-TYPE-DESC).

        Returns:
            Updated TransactionTypeResponse.
        """
        record = await self._repo.update_description(type_cd, request.description)
        return self._build_response(record)

    async def create_transaction_type(
        self, type_cd: str, description: str
    ) -> TransactionTypeResponse:
        """
        COTRTUPC TTUP-CREATE-NEW-RECORD flow.

        Called when user pressed PF5 after 'not found' message
        (WHEN CCARD-AID-PFK05 AND TTUP-DETAILS-NOT-FOUND).
        Then on next PF5, 9600-WRITE-PROCESSING does an INSERT.

        Args:
            type_cd:     New TR_TYPE code (2-char numeric string).
            description: TR_DESCRIPTION value.

        Returns:
            Newly created TransactionTypeResponse.

        Raises:
            ValidationError: Invalid type_cd format.
            DuplicateRecordError: type_cd already exists.
        """
        self._validate_type_cd(type_cd)
        record = await self._repo.create(type_cd, description)
        return self._build_response(record)

    async def delete_transaction_type(self, type_cd: str) -> None:
        """
        COTRTLIC 9300-DELETE-RECORD paragraph.

        SQL:
          DELETE FROM CARDDEMO.TRANSACTION_TYPE
          WHERE TR_TYPE IN (:WS-TYPE-CD-DELETE-KEYS...)

        Args:
            type_cd: TR_TYPE key to delete.

        Raises:
            RecordNotFoundError: Record not found (COTRTLIC: FLG-DELETED-NO).
        """
        await self._repo.delete(type_cd)

    @staticmethod
    def _validate_type_cd(type_cd: str) -> None:
        """
        COTRTUPC 1245-EDIT-NUM-REQD validation for TR_TYPE.

        Rules:
          1. Must not be blank/spaces (FLG-ALPHNANUM-BLANK)
          2. Must be numeric only (FUNCTION TEST-NUMVAL)
          3. Must not be zero (FUNCTION NUMVAL != 0)
          4. Max 2 chars (WS-EDIT-ALPHANUM-LENGTH = 2)

        Raises:
            ValidationError: If any rule fails.
        """
        cleaned = type_cd.strip()
        if not cleaned:
            raise ValidationError("Tran Type code must be supplied (COTRTUPC: 1245-EDIT-NUM-REQD)")
        if not cleaned.isdigit():
            raise ValidationError("Tran Type code must be numeric (COTRTUPC: 1245-EDIT-NUM-REQD)")
        if int(cleaned) == 0:
            raise ValidationError("Tran Type code must not be zero (COTRTUPC: 1245-EDIT-NUM-REQD)")
        if len(cleaned) > 2:
            raise ValidationError("Tran Type code max 2 digits (TR_TYPE CHAR(2))")

    @staticmethod
    def _build_response(record: TransactionType) -> TransactionTypeResponse:
        """Build TransactionTypeResponse from ORM model."""
        return TransactionTypeResponse(
            type_cd=record.type_cd,
            description=record.description,
        )
