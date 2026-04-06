"""
Business logic service for transaction type management.

COBOL origin: COTRTLIC (list/update/delete) and COTRTUPC (add/update/delete).

This service replaces the 15-state COTRTUPC state machine with straightforward CRUD
operations. The original state machine (TTUP-DETAILS-NOT-FETCHED → TTUP-INVALID-SEARCH-KEYS
→ TTUP-DETAILS-NOT-FOUND → TTUP-SHOW-DETAILS → ... → TTUP-CHANGES-OKAYED-AND-DONE)
was a pseudo-conversational UI pattern required by CICS terminal sessions. In the
modern REST stack, each endpoint call is a single atomic operation.

State machine mapping:
  TTUP-DETAILS-NOT-FETCHED     → GET /transaction-types (fresh list)
  TTUP-DETAILS-NOT-FOUND       → POST /transaction-types (create new)
  TTUP-SHOW-DETAILS            → GET /transaction-types/{code} (view existing)
  TTUP-CHANGES-OK-NOT-CONFIRMED → PUT /transaction-types/{code} (update)
  TTUP-CONFIRM-DELETE          → (frontend modal replaces PF4 confirm step)
  TTUP-START-DELETE            → DELETE /transaction-types/{code}
  TTUP-CHANGES-OKAYED-AND-DONE → 200/201 response from PUT/POST
  TTUP-DELETE-DONE             → 204 No Content from DELETE
  SQLCODE -532                 → TransactionTypeHasDependentsError (409)
  SQLCODE -911 (deadlock)      → handled by SQLAlchemy retry / 500 response

All COBOL validation paragraphs (1200-EDIT-MAP-INPUTS, 1210-EDIT-TRANTYPE,
1230-EDIT-ALPHANUM-REQD) are primarily enforced via Pydantic field validators in
the schema layer. The service layer adds cross-model validations (uniqueness,
optimistic locking, no-change detection).
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import (
    TransactionTypeAlreadyExistsError,
    TransactionTypeHasDependentsError,
    TransactionTypeNoChangesError,
    TransactionTypeNotFoundError,
    TransactionTypeOptimisticLockError,
)
from app.models.transaction_type import TransactionType
from app.repositories.transaction_type_repository import TransactionTypeRepository
from app.schemas.transaction_type import (
    TransactionTypeCreateRequest,
    TransactionTypeListResponse,
    TransactionTypeResponse,
    TransactionTypeUpdateRequest,
)

logger = logging.getLogger(__name__)

_repository = TransactionTypeRepository()


def _to_response(tt: TransactionType) -> TransactionTypeResponse:
    """Convert ORM model to response schema."""
    return TransactionTypeResponse.model_validate(tt)


async def list_transaction_types(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 7,
    type_code_filter: Optional[str] = None,
    description_filter: Optional[str] = None,
) -> TransactionTypeListResponse:
    """
    Paginated list of transaction types with optional filters.

    COBOL origin: COTRTLIC 8000-READ-FORWARD / 8100-READ-BACKWARDS + 9100-CHECK-FILTERS.

    Page size defaults to 7 (WS-MAX-SCREEN-LINES = 7 in COTRTLIC).
    Forward and backward cursor paging is replaced by standard OFFSET/LIMIT pagination.

    Type code filter = exact match (replaces WS-EDIT-TYPE-FLAG = '1' condition).
    Description filter = ILIKE '%filter%' (replaces LIKE with % wrapping from 1230-EDIT-DESC).

    Returns a TransactionTypeListResponse including pagination metadata.
    """
    items, total_count = await _repository.list_all(
        db,
        page=page,
        page_size=page_size,
        type_code_filter=type_code_filter,
        description_filter=description_filter,
    )

    total_pages = max(1, (total_count + page_size - 1) // page_size)
    has_next = page < total_pages
    has_previous = page > 1

    first_key = items[0].type_code if items else None
    last_key = items[-1].type_code if items else None

    return TransactionTypeListResponse(
        items=[_to_response(item) for item in items],
        page=page,
        page_size=page_size,
        total_count=total_count,
        has_next=has_next,
        has_previous=has_previous,
        first_item_key=first_key,
        last_item_key=last_key,
    )


async def get_transaction_type(
    db: AsyncSession,
    type_code: str,
) -> TransactionTypeResponse:
    """
    Retrieve a single transaction type by type_code.

    COBOL origin: COTRTUPC 9000-READ-TRANTYPE → 9100-GET-TRANSACTION-TYPE.
      SELECT TR_TYPE, TR_DESCRIPTION FROM CARDDEMO.TRANSACTION_TYPE
      WHERE TR_TYPE = :key

    Raises TransactionTypeNotFoundError (404) if not found.
    Replaces SQLCODE +100 (NOT FOUND) → TTUP-DETAILS-NOT-FOUND state.
    """
    record = await _repository.get_by_code(db, type_code)
    if record is None:
        raise TransactionTypeNotFoundError(type_code)
    return _to_response(record)


async def create_transaction_type(
    db: AsyncSession,
    request: TransactionTypeCreateRequest,
) -> TransactionTypeResponse:
    """
    Create a new transaction type record.

    COBOL origin: COTRTUPC 9700-INSERT-RECORD.
      State: TTUP-CREATE-NEW-RECORD → PF5 → 9600-WRITE-PROCESSING → INSERT.

    Validation (Pydantic enforces field-level rules; service enforces uniqueness):
      1. type_code must be numeric 01-99, non-zero (Pydantic validator)
      2. description must be alphanumeric, non-blank (Pydantic validator)
      3. type_code must not already exist → 409 Conflict (replaces SQLCODE -803 check)

    On success: equivalent to TTUP-CHANGES-OKAYED-AND-DONE + EXEC CICS SYNCPOINT.
    """
    # Uniqueness check: replaces COTRTUPC SELECT before INSERT to detect existing records
    already_exists = await _repository.exists(db, request.type_code)
    if already_exists:
        raise TransactionTypeAlreadyExistsError(request.type_code)

    try:
        new_record = await _repository.create(
            db, type_code=request.type_code, description=request.description
        )
    except IntegrityError as exc:
        logger.warning("IntegrityError creating transaction type %s: %s", request.type_code, exc)
        raise TransactionTypeAlreadyExistsError(request.type_code) from exc

    logger.info("Created transaction type '%s'", request.type_code)
    return _to_response(new_record)


async def update_transaction_type(
    db: AsyncSession,
    type_code: str,
    request: TransactionTypeUpdateRequest,
) -> TransactionTypeResponse:
    """
    Update the description of an existing transaction type.

    COBOL origin: COTRTLIC 9200-UPDATE-RECORD + COTRTUPC 9600-WRITE-PROCESSING (UPDATE).
      State: ENTER with 'U' → PF10 → UPDATE TRANSACTION_TYPE SET TR_DESCRIPTION = ...

    Validation and checks:
      1. Record must exist → 404 (replaces SQLCODE +100 NOT FOUND)
      2. Optimistic lock check: client's updated_at must match server's current value
         (replaces COTRTLIC WS-DATACHANGED-FLAG + COTRTUPC 1205-COMPARE-OLD-NEW)
      3. New description must differ from current → 422 (replaces WS-MESG-NO-CHANGES-DETECTED)
      4. Description must be alphanumeric (Pydantic validator)

    On success: equivalent to EXEC CICS SYNCPOINT + TTUP-CHANGES-OKAYED-AND-DONE.
    """
    current = await _repository.get_by_code(db, type_code)
    if current is None:
        raise TransactionTypeNotFoundError(type_code)

    _check_optimistic_lock(current, request.optimistic_lock_version, type_code)
    _check_description_changed(current.description, request.description)

    try:
        updated = await _repository.update(db, type_code=type_code, description=request.description)
    except IntegrityError as exc:
        logger.warning("IntegrityError updating transaction type %s: %s", type_code, exc)
        raise

    if updated is None:
        # Concurrent delete between our SELECT and UPDATE
        raise TransactionTypeNotFoundError(type_code)

    logger.info("Updated transaction type '%s'", type_code)
    return _to_response(updated)


async def delete_transaction_type(
    db: AsyncSession,
    type_code: str,
) -> None:
    """
    Delete a transaction type record.

    COBOL origin: COTRTLIC 9300-DELETE-RECORD + COTRTUPC 9800-DELETE-PROCESSING.
      State: ENTER with 'D' → PF10 → DELETE FROM TRANSACTION_TYPE WHERE TR_TYPE = :key

    Checks:
      1. Record must exist → 404
      2. If transactions reference this type_code: FK violation → 409
         (replaces COTRTLIC SQLCODE -532: 'Please delete associated child records first')

    On success: equivalent to EXEC CICS SYNCPOINT + TTUP-DELETE-DONE. Returns 204.
    """
    # Existence check before delete (maps COTRTUPC 9000-READ-TRANTYPE before delete)
    current = await _repository.get_by_code(db, type_code)
    if current is None:
        raise TransactionTypeNotFoundError(type_code)

    try:
        deleted = await _repository.delete(db, type_code)
    except IntegrityError as exc:
        # COTRTLIC SQLCODE -532: FK violation from transactions.transaction_type_code
        logger.warning(
            "FK violation deleting transaction type '%s': %s", type_code, exc
        )
        raise TransactionTypeHasDependentsError(type_code) from exc

    if not deleted:
        # Concurrent delete between our SELECT and DELETE
        raise TransactionTypeNotFoundError(type_code)

    logger.info("Deleted transaction type '%s'", type_code)


def _check_optimistic_lock(
    current: TransactionType,
    client_version: datetime,
    type_code: str,
) -> None:
    """
    Compare client-provided updated_at with the server's current value.

    COBOL origin: COTRTLIC WS-DATACHANGED-FLAG and COTRTUPC 1205-COMPARE-OLD-NEW.
    In the original, the previous description was stored in COMMAREA and compared
    on the next submit. Here we use the updated_at timestamp as the concurrency token.

    Raises TransactionTypeOptimisticLockError (409) if the versions differ.
    """
    # Normalize both timestamps to UTC for comparison
    server_ts = current.updated_at
    client_ts = client_version

    # Strip timezone info for comparison if needed (SQLAlchemy returns tz-aware)
    if hasattr(server_ts, "replace") and server_ts.tzinfo and not client_ts.tzinfo:
        client_ts = client_ts.replace(tzinfo=server_ts.tzinfo)
    elif hasattr(client_ts, "replace") and client_ts.tzinfo and not server_ts.tzinfo:
        server_ts = server_ts.replace(tzinfo=None)

    if abs((server_ts - client_ts).total_seconds()) > 1:
        raise TransactionTypeOptimisticLockError(type_code)


def _check_description_changed(current_description: str, new_description: str) -> None:
    """
    Ensure the new description actually differs from the stored value.

    COBOL origin: COTRTLIC WS-MESG-NO-CHANGES-DETECTED.
    'No change detected with respect to database values.'
    Original checked using UPPER-CASE comparison (1205-COMPARE-OLD-NEW).

    Raises TransactionTypeNoChangesError (422) if descriptions are equal.
    """
    if current_description.strip().upper() == new_description.strip().upper():
        raise TransactionTypeNoChangesError()
