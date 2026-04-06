"""
Unit tests for the transaction type service layer.

COBOL origin tested: COTRTLIC and COTRTUPC business logic paragraphs.

Tests are organized by service function, covering:
  - list_transaction_types: pagination, filters, empty results
  - get_transaction_type: found, not found
  - create_transaction_type: success, duplicate, validation
  - update_transaction_type: success, not found, no change, optimistic lock
  - delete_transaction_type: success, not found, FK constraint
  - Helper: _check_optimistic_lock, _check_description_changed
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.errors import (
    TransactionTypeAlreadyExistsError,
    TransactionTypeHasDependentsError,
    TransactionTypeNoChangesError,
    TransactionTypeNotFoundError,
    TransactionTypeOptimisticLockError,
)
from app.models.transaction_type import TransactionType
from app.schemas.transaction_type import (
    TransactionTypeCreateRequest,
    TransactionTypeListResponse,
    TransactionTypeResponse,
    TransactionTypeUpdateRequest,
)
from app.services import transaction_type_service


def make_tt(
    type_code: str = "01",
    description: str = "Purchase",
    updated_at: datetime | None = None,
) -> TransactionType:
    """Factory for TransactionType ORM objects used in mocked repository calls."""
    now = updated_at or datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    tt = TransactionType(type_code=type_code, description=description)
    # Bypass SQLAlchemy instrumentation to set server-set fields for test purposes
    object.__setattr__(tt, "created_at", now)
    object.__setattr__(tt, "updated_at", now)
    return tt


# ---------------------------------------------------------------------------
# list_transaction_types tests
# COBOL origin: COTRTLIC 8000-READ-FORWARD / 9100-CHECK-FILTERS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_returns_paginated_results():
    """
    COTRTLIC: 8000-READ-FORWARD returns up to WS-MAX-SCREEN-LINES=7 rows.
    Modern: paginated list with has_next/has_previous metadata.
    """
    db = AsyncMock()
    items = [make_tt(f"{i:02d}", f"Type {i}") for i in range(1, 8)]

    with patch.object(
        transaction_type_service._repository,
        "list_all",
        new=AsyncMock(return_value=(items, 10)),
    ):
        result = await transaction_type_service.list_transaction_types(
            db=db, page=1, page_size=7
        )

    assert isinstance(result, TransactionTypeListResponse)
    assert len(result.items) == 7
    assert result.total_count == 10
    assert result.has_next is True
    assert result.has_previous is False
    assert result.page == 1
    assert result.page_size == 7
    assert result.first_item_key == "01"
    assert result.last_item_key == "07"


@pytest.mark.asyncio
async def test_list_last_page_has_no_next():
    """COTRTLIC: CA-LAST-PAGE-SHOWN — last page has no next page."""
    db = AsyncMock()
    items = [make_tt("08", "Type 8"), make_tt("09", "Type 9"), make_tt("10", "Type 10")]

    with patch.object(
        transaction_type_service._repository,
        "list_all",
        new=AsyncMock(return_value=(items, 10)),
    ):
        result = await transaction_type_service.list_transaction_types(
            db=db, page=2, page_size=7
        )

    assert result.has_next is False
    assert result.has_previous is True
    assert result.page == 2


@pytest.mark.asyncio
async def test_list_empty_result():
    """
    COTRTLIC 9100-CHECK-FILTERS: no records found for filter conditions.
    Returns empty list with total_count=0.
    """
    db = AsyncMock()

    with patch.object(
        transaction_type_service._repository,
        "list_all",
        new=AsyncMock(return_value=([], 0)),
    ):
        result = await transaction_type_service.list_transaction_types(
            db=db, type_code_filter="99"
        )

    assert result.items == []
    assert result.total_count == 0
    assert result.has_next is False
    assert result.has_previous is False
    assert result.first_item_key is None
    assert result.last_item_key is None


@pytest.mark.asyncio
async def test_list_passes_filters_to_repository():
    """COTRTLIC 1220-EDIT-TYPECD + 1230-EDIT-DESC: filters are forwarded to the repo."""
    db = AsyncMock()
    mock_list = AsyncMock(return_value=([], 0))

    with patch.object(transaction_type_service._repository, "list_all", new=mock_list):
        await transaction_type_service.list_transaction_types(
            db=db,
            type_code_filter="02",
            description_filter="payment",
        )

    mock_list.assert_awaited_once_with(
        db,
        page=1,
        page_size=7,
        type_code_filter="02",
        description_filter="payment",
    )


# ---------------------------------------------------------------------------
# get_transaction_type tests
# COBOL origin: COTRTUPC 9100-GET-TRANSACTION-TYPE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_returns_existing_record():
    """COTRTUPC TTUP-SHOW-DETAILS: existing record is found and returned."""
    db = AsyncMock()
    tt = make_tt("01", "Purchase")

    with patch.object(
        transaction_type_service._repository,
        "get_by_code",
        new=AsyncMock(return_value=tt),
    ):
        result = await transaction_type_service.get_transaction_type(db=db, type_code="01")

    assert isinstance(result, TransactionTypeResponse)
    assert result.type_code == "01"
    assert result.description == "Purchase"


@pytest.mark.asyncio
async def test_get_raises_not_found():
    """COTRTUPC TTUP-DETAILS-NOT-FOUND: SQLCODE +100 → TransactionTypeNotFoundError (404)."""
    db = AsyncMock()

    with patch.object(
        transaction_type_service._repository,
        "get_by_code",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(TransactionTypeNotFoundError):
            await transaction_type_service.get_transaction_type(db=db, type_code="99")


# ---------------------------------------------------------------------------
# create_transaction_type tests
# COBOL origin: COTRTUPC 9700-INSERT-RECORD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_succeeds_for_new_code():
    """COTRTUPC TTUP-CREATE-NEW-RECORD → 9700-INSERT-RECORD: new type code is inserted."""
    db = AsyncMock()
    new_tt = make_tt("15", "Online Purchase")
    request = TransactionTypeCreateRequest(type_code="15", description="Online Purchase")

    with (
        patch.object(
            transaction_type_service._repository,
            "exists",
            new=AsyncMock(return_value=False),
        ),
        patch.object(
            transaction_type_service._repository,
            "create",
            new=AsyncMock(return_value=new_tt),
        ),
    ):
        result = await transaction_type_service.create_transaction_type(db=db, request=request)

    assert result.type_code == "15"
    assert result.description == "Online Purchase"


@pytest.mark.asyncio
async def test_create_raises_conflict_for_existing_code():
    """COTRTUPC: Duplicate type_code → TransactionTypeAlreadyExistsError (409)."""
    db = AsyncMock()
    request = TransactionTypeCreateRequest(type_code="01", description="Duplicate")

    with patch.object(
        transaction_type_service._repository,
        "exists",
        new=AsyncMock(return_value=True),
    ):
        with pytest.raises(TransactionTypeAlreadyExistsError):
            await transaction_type_service.create_transaction_type(db=db, request=request)


def test_create_request_rejects_zero_code():
    """COTRTUPC 1210-EDIT-TRANTYPE: type_code=0 is invalid."""
    with pytest.raises(ValueError, match="must not be zero"):
        TransactionTypeCreateRequest(type_code="00", description="Zero")


def test_create_request_rejects_non_numeric_code():
    """COTRTUPC 1245-EDIT-NUM-REQD: non-numeric type_code is invalid."""
    with pytest.raises(ValueError):
        TransactionTypeCreateRequest(type_code="AB", description="Bad")


def test_create_request_rejects_special_chars_in_description():
    """COTRTUPC 1230-EDIT-ALPHANUM-REQD: special characters in description are invalid."""
    with pytest.raises(ValueError):
        TransactionTypeCreateRequest(type_code="01", description="Sale & Refund!")


def test_create_request_rejects_blank_description():
    """COTRTUPC 1230-EDIT-ALPHANUM-REQD: blank description is invalid."""
    with pytest.raises(ValueError):
        TransactionTypeCreateRequest(type_code="01", description="   ")


def test_create_request_rejects_too_long_description():
    """COTRTUPC: TR_DESCRIPTION VARCHAR(50): max 50 chars."""
    with pytest.raises(ValueError):
        TransactionTypeCreateRequest(type_code="01", description="A" * 51)


def test_create_request_accepts_valid_code_and_description():
    """COTRTUPC: Valid code '02' with alphanumeric description passes all validators."""
    req = TransactionTypeCreateRequest(type_code="02", description="Bill Payment")
    assert req.type_code == "02"
    assert req.description == "Bill Payment"


# ---------------------------------------------------------------------------
# update_transaction_type tests
# COBOL origin: COTRTLIC 9200-UPDATE-RECORD + COTRTUPC 9600-WRITE-PROCESSING
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_succeeds_with_changed_description():
    """COTRTLIC 9200-UPDATE-RECORD: description is updated when valid and different."""
    db = AsyncMock()
    lock_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    current = make_tt("01", "Purchase", updated_at=lock_ts)
    updated = make_tt("01", "Standard Purchase", updated_at=lock_ts)
    request = TransactionTypeUpdateRequest(
        description="Standard Purchase",
        optimistic_lock_version=lock_ts,
    )

    with (
        patch.object(
            transaction_type_service._repository,
            "get_by_code",
            new=AsyncMock(return_value=current),
        ),
        patch.object(
            transaction_type_service._repository,
            "update",
            new=AsyncMock(return_value=updated),
        ),
    ):
        result = await transaction_type_service.update_transaction_type(
            db=db, type_code="01", request=request
        )

    assert result.description == "Standard Purchase"


@pytest.mark.asyncio
async def test_update_raises_not_found():
    """COTRTLIC 9200-UPDATE-RECORD SQLCODE +100: record not found → 404."""
    db = AsyncMock()
    request = TransactionTypeUpdateRequest(
        description="New Desc",
        optimistic_lock_version=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    with patch.object(
        transaction_type_service._repository,
        "get_by_code",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(TransactionTypeNotFoundError):
            await transaction_type_service.update_transaction_type(
                db=db, type_code="99", request=request
            )


@pytest.mark.asyncio
async def test_update_raises_no_changes_when_same_description():
    """
    COTRTLIC WS-MESG-NO-CHANGES-DETECTED: description matches current value → 422.
    COTRTUPC 1205-COMPARE-OLD-NEW: case-insensitive comparison.
    """
    db = AsyncMock()
    lock_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    current = make_tt("01", "Purchase", updated_at=lock_ts)
    request = TransactionTypeUpdateRequest(
        description="PURCHASE",  # Same as "Purchase" case-insensitive
        optimistic_lock_version=lock_ts,
    )

    with patch.object(
        transaction_type_service._repository,
        "get_by_code",
        new=AsyncMock(return_value=current),
    ):
        with pytest.raises(TransactionTypeNoChangesError):
            await transaction_type_service.update_transaction_type(
                db=db, type_code="01", request=request
            )


@pytest.mark.asyncio
async def test_update_raises_optimistic_lock_conflict():
    """
    COTRTLIC WS-DATACHANGED-FLAG: another user modified the record → 409.
    Detected when client's updated_at is significantly different from server's.
    """
    db = AsyncMock()
    server_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    client_ts = server_ts - timedelta(minutes=5)  # 5 minutes older = stale
    current = make_tt("01", "Purchase", updated_at=server_ts)
    request = TransactionTypeUpdateRequest(
        description="New Description",
        optimistic_lock_version=client_ts,
    )

    with patch.object(
        transaction_type_service._repository,
        "get_by_code",
        new=AsyncMock(return_value=current),
    ):
        with pytest.raises(TransactionTypeOptimisticLockError):
            await transaction_type_service.update_transaction_type(
                db=db, type_code="01", request=request
            )


def test_update_request_rejects_special_chars():
    """COTRTUPC 1230-EDIT-ALPHANUM-REQD: special chars in description → validation error."""
    with pytest.raises(ValueError):
        TransactionTypeUpdateRequest(
            description="Sale & Credit!",
            optimistic_lock_version=datetime(2026, 1, 1),
        )


# ---------------------------------------------------------------------------
# delete_transaction_type tests
# COBOL origin: COTRTLIC 9300-DELETE-RECORD + COTRTUPC 9800-DELETE-PROCESSING
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_succeeds_for_existing_type():
    """COTRTLIC 9300-DELETE-RECORD SQLCODE=0: successful delete returns 204."""
    db = AsyncMock()
    current = make_tt("01", "Purchase")

    with (
        patch.object(
            transaction_type_service._repository,
            "get_by_code",
            new=AsyncMock(return_value=current),
        ),
        patch.object(
            transaction_type_service._repository,
            "delete",
            new=AsyncMock(return_value=True),
        ),
    ):
        # Should not raise any exception
        await transaction_type_service.delete_transaction_type(db=db, type_code="01")


@pytest.mark.asyncio
async def test_delete_raises_not_found():
    """COTRTUPC 9800-DELETE-PROCESSING: not found → TransactionTypeNotFoundError (404)."""
    db = AsyncMock()

    with patch.object(
        transaction_type_service._repository,
        "get_by_code",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(TransactionTypeNotFoundError):
            await transaction_type_service.delete_transaction_type(db=db, type_code="99")


@pytest.mark.asyncio
async def test_delete_raises_has_dependents_on_fk_violation():
    """
    COTRTLIC 9300-DELETE-RECORD SQLCODE -532: FK constraint violation.
    'Please delete associated child records first'
    Raised when transactions.transaction_type_code references this type_code.
    """
    from sqlalchemy.exc import IntegrityError

    db = AsyncMock()
    current = make_tt("01", "Purchase")

    with (
        patch.object(
            transaction_type_service._repository,
            "get_by_code",
            new=AsyncMock(return_value=current),
        ),
        patch.object(
            transaction_type_service._repository,
            "delete",
            new=AsyncMock(side_effect=IntegrityError("FK", None, None)),
        ),
    ):
        with pytest.raises(TransactionTypeHasDependentsError):
            await transaction_type_service.delete_transaction_type(db=db, type_code="01")
