"""
Transaction type endpoints — derived from COTRTLIC and COTRTUPC.

Source programs:
  app/app-transaction-type-db2/cbl/COTRTLIC.cbl  — List/browse (CICS CTLI)
  app/app-transaction-type-db2/cbl/COTRTUPC.cbl  — Update/delete (CICS CTTU)

CICS transaction IDs: CTLI (list), CTTU (update)

DB2 table: CARDDEMO.TRANSACTION_TYPE (TR_TYPE CHAR(2), TR_DESCRIPTION CHAR(50))

Endpoint mapping:
  GET  /api/v1/transaction-types           → COTRTLIC (C-TR-TYPE-FORWARD cursor browse)
  GET  /api/v1/transaction-types/{type_cd} → COTRTUPC 9000-READ-TRANTYPE
  PUT  /api/v1/transaction-types/{type_cd} → COTRTUPC 9600-WRITE-PROCESSING (UPDATE)
  POST /api/v1/transaction-types           → COTRTUPC TTUP-CREATE-NEW-RECORD (INSERT)
  DELETE /api/v1/transaction-types/{type_cd} → COTRTLIC 9300-DELETE-RECORD (DELETE)

All endpoints require admin access (CDEMO-USRTYP-ADMIN).
COTRTLIC is reachable from COADM01C option 3 (admin only).
"""
from fastapi import APIRouter, Query

from app.dependencies import AdminUser, DBSession
from app.schemas.transaction_type import (
    TransactionTypeListResponse,
    TransactionTypeResponse,
    TransactionTypeUpdateRequest,
)
from app.services.transaction_type_service import MAX_PAGE_SIZE, TransactionTypeService

router = APIRouter(
    prefix="/transaction-types",
    tags=["Transaction Types (COTRTLIC/COTRTUPC)"],
)


@router.get(
    "",
    response_model=TransactionTypeListResponse,
    summary="Browse transaction types (COTRTLIC / CTLI)",
    responses={
        200: {"description": "Paginated transaction type list"},
    },
)
async def list_transaction_types(
    db: DBSession,
    current_user: AdminUser,
    cursor: str | None = Query(
        None,
        description=(
            "Keyset cursor — last TR_TYPE from previous page "
            "(COTRTLIC WS-CA-LAST-TR-CODE for PF8, WS-CA-FIRST-TR-CODE for PF7)"
        ),
    ),
    direction: str = Query(
        "forward",
        pattern="^(forward|backward)$",
        description="'forward' = PF8 next page, 'backward' = PF7 prev page",
    ),
    limit: int = Query(
        MAX_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Page size (COTRTLIC: WS-MAX-SCREEN-LINES = {MAX_PAGE_SIZE})",
    ),
    type_cd: str | None = Query(
        None,
        max_length=2,
        description=(
            "Exact TR_TYPE filter (COTRTLIC WS-TYPE-CD-FILTER; "
            "FLG-TYPEFILTER-ISVALID = '1' when set)"
        ),
    ),
    desc_filter: str | None = Query(
        None,
        max_length=50,
        description=(
            "TR_DESCRIPTION LIKE filter (COTRTLIC WS-TYPE-DESC-FILTER; "
            "FLG-DESCFILTER-ISVALID = '1' when set)"
        ),
    ),
) -> TransactionTypeListResponse:
    """
    Browse transaction types with cursor-keyset pagination.

    Derived from COTRTLIC 8000-READ-FORWARD paragraph using DB2 cursor:

    COBOL:
      DECLARE C-TR-TYPE-FORWARD CURSOR FOR
        SELECT TR_TYPE, TR_DESCRIPTION
        FROM   CARDDEMO.TRANSACTION_TYPE
        WHERE  TR_TYPE >= :WS-START-KEY
        AND    ((:WS-EDIT-TYPE-FLAG='1' AND TR_TYPE=:WS-TYPE-CD-FILTER) OR ...)
        AND    ((:WS-EDIT-DESC-FLAG='1' AND TR_DESCRIPTION LIKE TRIM(:WS-TYPE-DESC-FILTER)) OR ...)
        ORDER  BY TR_TYPE
      FETCH FIRST 7 ROWS ONLY (WS-MAX-SCREEN-LINES)

    Cursor is WS-CA-LAST-TR-CODE for next page, WS-CA-FIRST-TR-CODE for prev page.
    CA-NEXT-PAGE-EXISTS (WS-CA-NEXT-PAGE-IND='Y') is reflected in next_cursor presence.
    """
    service = TransactionTypeService(db)
    return await service.list_transaction_types(
        cursor=cursor,
        direction=direction,
        limit=limit,
        type_cd_filter=type_cd,
        desc_filter=desc_filter,
    )


@router.get(
    "/{type_cd}",
    response_model=TransactionTypeResponse,
    summary="Get transaction type detail (COTRTUPC 9000-READ-TRANTYPE / CTTU)",
    responses={
        200: {"description": "Transaction type record"},
        404: {"description": "Not found (SQLCODE=100, COTRTUPC: 'No record found for this key')"},
    },
)
async def get_transaction_type(
    type_cd: str,
    db: DBSession,
    current_user: AdminUser,
) -> TransactionTypeResponse:
    """
    Retrieve a single transaction type by code.

    Derived from COTRTUPC 9000-READ-TRANTYPE paragraph:

    COBOL:
      EXEC SQL
          SELECT TR_TYPE, TR_DESCRIPTION
          INTO   :TTUP-OLD-TTYP-TYPE, :TTUP-OLD-TTYP-TYPE-DESC
          FROM   CARDDEMO.TRANSACTION_TYPE
          WHERE  TR_TYPE = :TTUP-NEW-TTYP-TYPE
      END-EXEC
      IF SQLCODE = 100 → SET TTUP-DETAILS-NOT-FOUND TO TRUE
                         SET WS-RECORD-NOT-FOUND TO TRUE

    type_cd is TR_TYPE CHAR(2) — e.g., '01', '02'.
    Zero-padded if single digit (COTRTUPC: MOVE WS-EDIT-NUMERIC-2 TO TTUP-NEW-TTYP-TYPE).
    """
    service = TransactionTypeService(db)
    return await service.get_transaction_type(type_cd)


@router.put(
    "/{type_cd}",
    response_model=TransactionTypeResponse,
    summary="Update transaction type description (COTRTUPC 9600-WRITE-PROCESSING / CTTU)",
    responses={
        200: {"description": "Transaction type updated"},
        404: {"description": "Transaction type not found"},
        409: {"description": "Concurrent update conflict"},
        422: {"description": "Validation error (blank or non-alphanumeric description)"},
    },
)
async def update_transaction_type(
    type_cd: str,
    request: TransactionTypeUpdateRequest,
    db: DBSession,
    current_user: AdminUser,
) -> TransactionTypeResponse:
    """
    Update a transaction type description.

    Derived from COTRTUPC 9600-WRITE-PROCESSING paragraph:

    COBOL:
      EXEC SQL
          UPDATE CARDDEMO.TRANSACTION_TYPE
          SET    TR_DESCRIPTION = :TTUP-NEW-TTYP-TYPE-DESC
          WHERE  TR_TYPE = :TTUP-OLD-TTYP-TYPE
      END-EXEC
      EVALUATE SQLCODE
          WHEN 0   → SET TTUP-CHANGES-OKAYED-AND-DONE TO TRUE ('Changes committed to database')
          WHEN 100 → SET TTUP-CHANGES-OKAYED-LOCK-ERROR TO TRUE ('Could not lock record')
          WHEN OTHER → SET TTUP-CHANGES-OKAYED-BUT-FAILED TO TRUE ('Update of record failed')

    type_cd (TR_TYPE) is the key — only TR_DESCRIPTION is updatable.
    COTRTUPC validates description via 1230-EDIT-ALPHANUM-REQD before calling this.
    No-change detection: if new description matches existing (case-insensitive),
    returns current record unchanged (COTRTUPC 1205-COMPARE-OLD-NEW).
    """
    service = TransactionTypeService(db)
    return await service.update_transaction_type(type_cd, request)


@router.post(
    "",
    response_model=TransactionTypeResponse,
    status_code=201,
    summary="Create transaction type (COTRTUPC TTUP-CREATE-NEW-RECORD / CTTU)",
    responses={
        201: {"description": "Transaction type created"},
        409: {"description": "Duplicate TR_TYPE (CICS DUPREC)"},
        422: {"description": "Validation error (non-numeric, zero, or blank)"},
    },
)
async def create_transaction_type(
    request: TransactionTypeUpdateRequest,
    type_cd: str = Query(..., max_length=2, description="New TR_TYPE code (2-char numeric)"),
    db: DBSession = ...,
    current_user: AdminUser = ...,
) -> TransactionTypeResponse:
    """
    Create a new transaction type.

    Derived from COTRTUPC TTUP-CREATE-NEW-RECORD flow:

    COBOL:
      WHEN CCARD-AID-PFK05 AND TTUP-DETAILS-NOT-FOUND
        SET TTUP-CREATE-NEW-RECORD TO TRUE
      WHEN CCARD-AID-PFK05 AND TTUP-CHANGES-OK-NOT-CONFIRMED
        PERFORM 9600-WRITE-PROCESSING  ← executes INSERT via EXEC SQL INSERT

    type_cd must be:
      - 2-digit numeric string (COTRTUPC 1245-EDIT-NUM-REQD)
      - non-zero (FUNCTION NUMVAL != 0)
    description must pass 1230-EDIT-ALPHANUM-REQD validation.
    """
    service = TransactionTypeService(db)
    return await service.create_transaction_type(type_cd, request.description)


@router.delete(
    "/{type_cd}",
    status_code=204,
    summary="Delete transaction type (COTRTLIC 9300-DELETE-RECORD / CTLI)",
    responses={
        204: {"description": "Transaction type deleted"},
        404: {"description": "Not found"},
    },
)
async def delete_transaction_type(
    type_cd: str,
    db: DBSession,
    current_user: AdminUser,
) -> None:
    """
    Delete a transaction type record.

    Derived from COTRTLIC 9300-DELETE-RECORD paragraph:

    COBOL:
      EXEC SQL
          DELETE FROM CARDDEMO.TRANSACTION_TYPE
          WHERE TR_TYPE IN (:WS-TYPE-CD-DELETE-KEYS...)
      END-EXEC
      EVALUATE SQLCODE
          WHEN 0 → SET CA-DELETE-SUCCEEDED TO TRUE
                   SET WS-INFORM-DELETE-SUCCESS TO TRUE
          WHEN OTHER → (RECORD-DELETE-FAILED error handling)

    Triggered in COTRTLIC when user marks a row with 'D' action flag
    (WS-EDIT-SELECT(I) = LIT-DELETE-FLAG = 'D') and presses F10 to confirm.
    """
    service = TransactionTypeService(db)
    await service.delete_transaction_type(type_cd)
