"""
FastAPI endpoints for Transaction Type Management (admin-only).

COBOL origin: COTRTLIC (Transaction: CTLI) and COTRTUPC (Transaction: CTTU).

Endpoint mapping:
  GET  /api/v1/transaction-types          → COTRTLIC 8000-READ-FORWARD (paginated list)
  GET  /api/v1/transaction-types/{code}   → COTRTUPC 9100-GET-TRANSACTION-TYPE (single record)
  POST /api/v1/transaction-types          → COTRTUPC 9700-INSERT-RECORD (create new)
  PUT  /api/v1/transaction-types/{code}   → COTRTUPC 9600-WRITE-PROCESSING UPDATE path
  DELETE /api/v1/transaction-types/{code} → COTRTLIC 9300-DELETE-RECORD / COTRTUPC 9800-DELETE

Access control: All endpoints require admin JWT (user_type='A').
  COBOL equivalent: Only reachable from COADM01C admin menu options 5 (CTLI) and 6 (CTTU).

This is a thin controller layer — all business logic is in transaction_type_service.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_admin
from app.database import get_db
from app.schemas.transaction_type import (
    TransactionTypeCreateRequest,
    TransactionTypeListResponse,
    TransactionTypeResponse,
    TransactionTypeUpdateRequest,
)
from app.services import transaction_type_service

router = APIRouter(
    prefix="/transaction-types",
    tags=["Transaction Types"],
)

# Type alias for admin dependency
AdminUser = Annotated[CurrentUser, Depends(require_admin)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "",
    response_model=TransactionTypeListResponse,
    summary="List transaction types (paginated)",
    description=(
        "Returns a paginated list of transaction types. "
        "Replaces COTRTLIC 7-row cursor-based paging (PF7/PF8). "
        "Admin only."
    ),
)
async def list_transaction_types(
    db: DbSession,
    _: AdminUser,
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=7, ge=1, le=7, description="Items per page (max 7; COTRTLIC WS-MAX-SCREEN-LINES)"
    ),
    type_code_filter: Optional[str] = Query(
        default=None,
        max_length=2,
        pattern=r"^[0-9]{1,2}$",
        description="Exact type code filter (COTRTLIC TRTYPE field → WHERE TR_TYPE = filter)",
    ),
    description_filter: Optional[str] = Query(
        default=None,
        max_length=50,
        description="Description substring filter (COTRTLIC TRDESC → LIKE '%%filter%%')",
    ),
) -> TransactionTypeListResponse:
    """
    GET /api/v1/transaction-types

    COBOL origin: COTRTLIC 8000-READ-FORWARD / 8100-READ-BACKWARDS + 9100-CHECK-FILTERS.
    Forward cursor paging (PF8) and backward cursor paging (PF7) are replaced
    by standard page/page_size query parameters.

    Filter behavior matches COTRTLIC:
      - type_code_filter: exact match (2-digit numeric)
      - description_filter: ILIKE '%filter%' (case-insensitive contains)
    """
    return await transaction_type_service.list_transaction_types(
        db=db,
        page=page,
        page_size=page_size,
        type_code_filter=type_code_filter,
        description_filter=description_filter,
    )


@router.get(
    "/{type_code}",
    response_model=TransactionTypeResponse,
    summary="Get a single transaction type",
    description=(
        "Retrieve a transaction type by its code. "
        "Replaces COTRTUPC 9100-GET-TRANSACTION-TYPE. "
        "Admin only."
    ),
)
async def get_transaction_type(
    type_code: str,
    db: DbSession,
    _: AdminUser,
) -> TransactionTypeResponse:
    """
    GET /api/v1/transaction-types/{type_code}

    COBOL origin: COTRTUPC 9000-READ-TRANTYPE → 9100-GET-TRANSACTION-TYPE.
    Replaces SELECT from CARDDEMO.TRANSACTION_TYPE WHERE TR_TYPE = :key.
    Returns 404 if not found (replaces SQLCODE +100 NOT FOUND → TTUP-DETAILS-NOT-FOUND).
    """
    return await transaction_type_service.get_transaction_type(db=db, type_code=type_code)


@router.post(
    "",
    response_model=TransactionTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction type",
    description=(
        "Create a new transaction type record. "
        "Replaces COTRTUPC TTUP-CREATE-NEW-RECORD state → 9700-INSERT-RECORD. "
        "Admin only."
    ),
)
async def create_transaction_type(
    request: TransactionTypeCreateRequest,
    db: DbSession,
    _: AdminUser,
) -> TransactionTypeResponse:
    """
    POST /api/v1/transaction-types

    COBOL origin: COTRTUPC state sequence:
      TTUP-DETAILS-NOT-FOUND (PF5) → TTUP-CREATE-NEW-RECORD
      → 9600-WRITE-PROCESSING → 9700-INSERT-RECORD
      → EXEC CICS SYNCPOINT → TTUP-CHANGES-OKAYED-AND-DONE

    Validation (Pydantic + service):
      - type_code: numeric 01-99, non-zero (COTRTUPC 1210-EDIT-TRANTYPE)
      - description: alphanumeric only, non-blank (COTRTUPC 1230-EDIT-ALPHANUM-REQD)
      - type_code must not already exist: 409 Conflict

    Returns 201 Created with the new record.
    """
    return await transaction_type_service.create_transaction_type(db=db, request=request)


@router.put(
    "/{type_code}",
    response_model=TransactionTypeResponse,
    summary="Update a transaction type description",
    description=(
        "Update the description of an existing transaction type. "
        "Replaces COTRTLIC 9200-UPDATE-RECORD (inline edit) and "
        "COTRTUPC 9600-WRITE-PROCESSING UPDATE path. "
        "Admin only."
    ),
)
async def update_transaction_type(
    type_code: str,
    request: TransactionTypeUpdateRequest,
    db: DbSession,
    _: AdminUser,
) -> TransactionTypeResponse:
    """
    PUT /api/v1/transaction-types/{type_code}

    COBOL origin: COTRTLIC 9200-UPDATE-RECORD (marking 'U' on list row + PF10 confirm):
      UPDATE CARDDEMO.TRANSACTION_TYPE
      SET TR_DESCRIPTION = :new_desc
      WHERE TR_TYPE = :type_code

    Checks (maps COTRTLIC/COTRTUPC validation):
      - Record must exist: 404 (SQLCODE +100 → TTUP-DETAILS-NOT-FOUND)
      - optimistic_lock_version must match server updated_at: 409 (replaces WS-DATACHANGED-FLAG)
      - New description must differ: 422 (replaces WS-MESG-NO-CHANGES-DETECTED)
      - Description must be alphanumeric (Pydantic validator)

    Returns 200 with updated record on success.
    """
    return await transaction_type_service.update_transaction_type(
        db=db, type_code=type_code, request=request
    )


@router.delete(
    "/{type_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction type",
    description=(
        "Delete a transaction type by code. "
        "Replaces COTRTLIC 9300-DELETE-RECORD and COTRTUPC 9800-DELETE-PROCESSING. "
        "Returns 409 if transactions reference this type code (FK constraint). "
        "Admin only."
    ),
)
async def delete_transaction_type(
    type_code: str,
    db: DbSession,
    _: AdminUser,
) -> None:
    """
    DELETE /api/v1/transaction-types/{type_code}

    COBOL origin: COTRTLIC 9300-DELETE-RECORD (marking 'D' + PF10 confirm):
      DELETE FROM CARDDEMO.TRANSACTION_TYPE WHERE TR_TYPE = :type_code
      SQLCODE 0: SYNCPOINT, success
      SQLCODE -532: FK violation → 'Please delete associated child records first'

    Returns 204 No Content on success.
    Returns 404 if not found.
    Returns 409 if transactions reference this type (SQLCODE -532 equivalent).
    """
    await transaction_type_service.delete_transaction_type(db=db, type_code=type_code)
