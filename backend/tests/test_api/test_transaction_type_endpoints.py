"""
Integration tests for transaction type API endpoints.

Tests cover:
  - GET /api/v1/transaction-types (list, pagination, filters)
  - GET /api/v1/transaction-types/{type_code} (single record)
  - POST /api/v1/transaction-types (create)
  - PUT /api/v1/transaction-types/{type_code} (update)
  - DELETE /api/v1/transaction-types/{type_code} (delete)
  - Admin-only access enforcement (non-admin gets 403)
  - Input validation (422 for invalid fields)

COBOL origin: COTRTLIC (CTLI) and COTRTUPC (CTTU).
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.errors import (
    TransactionTypeAlreadyExistsError,
    TransactionTypeHasDependentsError,
    TransactionTypeNoChangesError,
    TransactionTypeNotFoundError,
    TransactionTypeOptimisticLockError,
)
from app.schemas.transaction_type import (
    TransactionTypeListResponse,
    TransactionTypeResponse,
)
from app.services import transaction_type_service

BASE_URL = "/api/v1/transaction-types"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tt_response(
    type_code: str = "01",
    description: str = "Purchase",
    updated_at: datetime | None = None,
) -> TransactionTypeResponse:
    now = updated_at or datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return TransactionTypeResponse(
        type_code=type_code,
        description=description,
        created_at=now,
        updated_at=now,
    )


def _make_list_response(items: list[TransactionTypeResponse], total: int = 10) -> TransactionTypeListResponse:
    return TransactionTypeListResponse(
        items=items,
        page=1,
        page_size=7,
        total_count=total,
        has_next=total > 7,
        has_previous=False,
        first_item_key=items[0].type_code if items else None,
        last_item_key=items[-1].type_code if items else None,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/transaction-types — List
# COBOL origin: COTRTLIC 8000-READ-FORWARD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_returns_200_for_admin(client):
    """Admin user can list transaction types."""
    mock_response = _make_list_response([_make_tt_response()], total=1)

    with patch.object(
        transaction_type_service,
        "list_transaction_types",
        new=AsyncMock(return_value=mock_response),
    ):
        resp = await client.get(BASE_URL)

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 7


@pytest.mark.asyncio
async def test_list_returns_403_for_regular_user(regular_client):
    """Non-admin user cannot access transaction type list (COADM01C gate)."""
    resp = await regular_client.get(BASE_URL)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "ADMIN_REQUIRED"


@pytest.mark.asyncio
async def test_list_returns_401_without_token(db_session):
    """Unauthenticated request returns 401."""
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    from app.database import get_db

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(BASE_URL)
        assert resp.status_code == 403  # HTTPBearer returns 403 for missing token
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_passes_filters(client):
    """Filters are forwarded to the service layer."""
    mock_response = _make_list_response([], total=0)
    mock_service = AsyncMock(return_value=mock_response)

    with patch.object(transaction_type_service, "list_transaction_types", new=mock_service):
        resp = await client.get(
            BASE_URL,
            params={"type_code_filter": "02", "description_filter": "payment"},
        )

    assert resp.status_code == 200
    mock_service.assert_awaited_once()
    call_kwargs = mock_service.call_args.kwargs
    assert call_kwargs.get("type_code_filter") == "02"
    assert call_kwargs.get("description_filter") == "payment"


@pytest.mark.asyncio
async def test_list_rejects_invalid_page_size(client):
    """page_size > 7 is rejected (COTRTLIC WS-MAX-SCREEN-LINES=7)."""
    resp = await client.get(BASE_URL, params={"page_size": 10})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_rejects_non_numeric_type_filter(client):
    """Non-numeric type_code_filter is rejected (COTRTLIC 1220-EDIT-TYPECD)."""
    resp = await client.get(BASE_URL, params={"type_code_filter": "AB"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/transaction-types/{type_code} — Single record
# COBOL origin: COTRTUPC 9100-GET-TRANSACTION-TYPE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_single_returns_200(client):
    """Admin can retrieve a transaction type by code."""
    mock_tt = _make_tt_response("01", "Purchase")

    with patch.object(
        transaction_type_service,
        "get_transaction_type",
        new=AsyncMock(return_value=mock_tt),
    ):
        resp = await client.get(f"{BASE_URL}/01")

    assert resp.status_code == 200
    data = resp.json()
    assert data["type_code"] == "01"
    assert data["description"] == "Purchase"
    assert "updated_at" in data  # Needed for optimistic lock in PUT


@pytest.mark.asyncio
async def test_get_single_returns_404_for_missing(client):
    """COTRTUPC TTUP-DETAILS-NOT-FOUND: missing record returns 404."""
    with patch.object(
        transaction_type_service,
        "get_transaction_type",
        new=AsyncMock(side_effect=TransactionTypeNotFoundError("99")),
    ):
        resp = await client.get(f"{BASE_URL}/99")

    assert resp.status_code == 404
    assert resp.json()["detail"]["error_code"] == "TRANSACTION_TYPE_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_single_returns_403_for_regular_user(regular_client):
    """Non-admin cannot get single transaction type."""
    resp = await regular_client.get(f"{BASE_URL}/01")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/transaction-types — Create
# COBOL origin: COTRTUPC 9700-INSERT-RECORD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_returns_201_on_success(client):
    """COTRTUPC TTUP-CHANGES-OKAYED-AND-DONE: successful insert returns 201."""
    mock_tt = _make_tt_response("15", "Online Purchase")

    with patch.object(
        transaction_type_service,
        "create_transaction_type",
        new=AsyncMock(return_value=mock_tt),
    ):
        resp = await client.post(
            BASE_URL,
            json={"type_code": "15", "description": "Online Purchase"},
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["type_code"] == "15"
    assert data["description"] == "Online Purchase"


@pytest.mark.asyncio
async def test_create_returns_409_for_duplicate(client):
    """COTRTUPC duplicate check: existing code → 409 Conflict."""
    with patch.object(
        transaction_type_service,
        "create_transaction_type",
        new=AsyncMock(side_effect=TransactionTypeAlreadyExistsError("01")),
    ):
        resp = await client.post(
            BASE_URL,
            json={"type_code": "01", "description": "Purchase"},
        )

    assert resp.status_code == 409
    assert resp.json()["detail"]["error_code"] == "TRANSACTION_TYPE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_create_rejects_zero_code(client):
    """COTRTUPC 1210-EDIT-TRANTYPE: type_code '00' is invalid → 422."""
    resp = await client.post(
        BASE_URL,
        json={"type_code": "00", "description": "Invalid"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_rejects_special_chars_in_description(client):
    """COTRTUPC 1230-EDIT-ALPHANUM-REQD: special chars → 422."""
    resp = await client.post(
        BASE_URL,
        json={"type_code": "05", "description": "Sale & Refund!"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_rejects_blank_description(client):
    """COTRTUPC 1230-EDIT-ALPHANUM-REQD: blank description → 422."""
    resp = await client.post(
        BASE_URL,
        json={"type_code": "05", "description": ""},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_returns_403_for_regular_user(regular_client):
    """Admin-only: non-admin create returns 403."""
    resp = await regular_client.post(
        BASE_URL,
        json={"type_code": "05", "description": "New Type"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /api/v1/transaction-types/{type_code} — Update
# COBOL origin: COTRTLIC 9200-UPDATE-RECORD + COTRTUPC 9600-WRITE-PROCESSING
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_returns_200_on_success(client):
    """COTRTLIC 9200-UPDATE-RECORD success: updated record returned."""
    lock_ts = "2026-01-01T12:00:00+00:00"
    mock_tt = _make_tt_response("01", "Standard Purchase")

    with patch.object(
        transaction_type_service,
        "update_transaction_type",
        new=AsyncMock(return_value=mock_tt),
    ):
        resp = await client.put(
            f"{BASE_URL}/01",
            json={
                "description": "Standard Purchase",
                "optimistic_lock_version": lock_ts,
            },
        )

    assert resp.status_code == 200
    assert resp.json()["description"] == "Standard Purchase"


@pytest.mark.asyncio
async def test_update_returns_404_for_missing(client):
    """COTRTLIC 9200-UPDATE-RECORD SQLCODE +100: not found → 404."""
    with patch.object(
        transaction_type_service,
        "update_transaction_type",
        new=AsyncMock(side_effect=TransactionTypeNotFoundError("99")),
    ):
        resp = await client.put(
            f"{BASE_URL}/99",
            json={
                "description": "Some Desc",
                "optimistic_lock_version": "2026-01-01T12:00:00+00:00",
            },
        )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_returns_422_for_no_changes(client):
    """COTRTLIC WS-MESG-NO-CHANGES-DETECTED: same description → 422."""
    with patch.object(
        transaction_type_service,
        "update_transaction_type",
        new=AsyncMock(side_effect=TransactionTypeNoChangesError()),
    ):
        resp = await client.put(
            f"{BASE_URL}/01",
            json={
                "description": "Purchase",
                "optimistic_lock_version": "2026-01-01T12:00:00+00:00",
            },
        )

    assert resp.status_code == 422
    assert resp.json()["detail"]["error_code"] == "NO_CHANGES_DETECTED"


@pytest.mark.asyncio
async def test_update_returns_409_for_optimistic_lock_conflict(client):
    """COTRTLIC WS-DATACHANGED-FLAG: stale version → 409 Conflict."""
    with patch.object(
        transaction_type_service,
        "update_transaction_type",
        new=AsyncMock(side_effect=TransactionTypeOptimisticLockError("01")),
    ):
        resp = await client.put(
            f"{BASE_URL}/01",
            json={
                "description": "New Description",
                "optimistic_lock_version": "2025-01-01T12:00:00+00:00",
            },
        )

    assert resp.status_code == 409
    assert resp.json()["detail"]["error_code"] == "OPTIMISTIC_LOCK_CONFLICT"


@pytest.mark.asyncio
async def test_update_returns_403_for_regular_user(regular_client):
    """Admin-only: non-admin update returns 403."""
    resp = await regular_client.put(
        f"{BASE_URL}/01",
        json={
            "description": "New Description",
            "optimistic_lock_version": "2026-01-01T12:00:00+00:00",
        },
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/v1/transaction-types/{type_code} — Delete
# COBOL origin: COTRTLIC 9300-DELETE-RECORD + COTRTUPC 9800-DELETE-PROCESSING
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_returns_204_on_success(client):
    """COTRTLIC 9300-DELETE-RECORD SQLCODE=0: successful delete → 204 No Content."""
    with patch.object(
        transaction_type_service,
        "delete_transaction_type",
        new=AsyncMock(return_value=None),
    ):
        resp = await client.delete(f"{BASE_URL}/01")

    assert resp.status_code == 204
    assert resp.content == b""


@pytest.mark.asyncio
async def test_delete_returns_404_for_missing(client):
    """COTRTUPC 9800-DELETE-PROCESSING: not found → 404."""
    with patch.object(
        transaction_type_service,
        "delete_transaction_type",
        new=AsyncMock(side_effect=TransactionTypeNotFoundError("99")),
    ):
        resp = await client.delete(f"{BASE_URL}/99")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_returns_409_for_fk_violation(client):
    """COTRTLIC 9300-DELETE-RECORD SQLCODE -532: FK violation → 409."""
    with patch.object(
        transaction_type_service,
        "delete_transaction_type",
        new=AsyncMock(side_effect=TransactionTypeHasDependentsError("01")),
    ):
        resp = await client.delete(f"{BASE_URL}/01")

    assert resp.status_code == 409
    assert resp.json()["detail"]["error_code"] == "TRANSACTION_TYPE_HAS_DEPENDENTS"


@pytest.mark.asyncio
async def test_delete_returns_403_for_regular_user(regular_client):
    """Admin-only: non-admin delete returns 403."""
    resp = await regular_client.delete(f"{BASE_URL}/01")
    assert resp.status_code == 403
