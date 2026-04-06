"""Integration tests for the /api/transaction-types HTTP endpoints.

Tests use the HTTPX async client with dependency overrides (test DB).
Every endpoint is tested for:
  - Happy path (200/201/204)
  - Auth guard (403 for non-admin, 401 for missing token)
  - Not found (404)
  - Conflict on duplicate (409)
  - Validation errors (422)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction_type import TransactionType, TransactionTypeCategory


# ---------------------------------------------------------------------------
# Helper: auth headers
# ---------------------------------------------------------------------------

def admin_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def user_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# GET /api/transaction-types — list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_requires_admin(client: AsyncClient, user_token: str):
    resp = await client.get(
        "/api/transaction-types", headers=user_headers(user_token)
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_requires_auth(client: AsyncClient):
    resp = await client.get("/api/transaction-types")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_returns_paginated(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.get(
        "/api/transaction-types", headers=admin_headers(admin_token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert "type_code" in data["items"][0]


@pytest.mark.asyncio
async def test_list_filter_by_type_code(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.get(
        "/api/transaction-types?type_code=01", headers=admin_headers(admin_token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["type_code"] == "01"


@pytest.mark.asyncio
async def test_list_pagination_page_size(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.get(
        "/api/transaction-types?page=1&page_size=2",
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["pages"] == 2


# ---------------------------------------------------------------------------
# GET /api/transaction-types/{type_code}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_type_with_categories(
    client: AsyncClient, admin_token: str, seeded_categories
):
    resp = await client.get(
        "/api/transaction-types/01", headers=admin_headers(admin_token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type_code"] == "01"
    assert len(data["categories"]) == 2


@pytest.mark.asyncio
async def test_get_type_not_found(client: AsyncClient, admin_token: str):
    resp = await client.get(
        "/api/transaction-types/99", headers=admin_headers(admin_token)
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/transaction-types — create
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_type_success(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/transaction-types",
        json={"type_code": "08", "description": "Fee"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["type_code"] == "08"


@pytest.mark.asyncio
async def test_create_type_duplicate_returns_409(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.post(
        "/api/transaction-types",
        json={"type_code": "01", "description": "Dup"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_type_invalid_code_too_long(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/transaction-types",
        json={"type_code": "ABC", "description": "Too long code"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_type_blank_code_rejected(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/transaction-types",
        json={"type_code": "  ", "description": "Blank code"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_type_non_alphanumeric_code_rejected(
    client: AsyncClient, admin_token: str
):
    resp = await client.post(
        "/api/transaction-types",
        json={"type_code": "!@", "description": "Special chars"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_type_blank_description_rejected(
    client: AsyncClient, admin_token: str
):
    resp = await client.post(
        "/api/transaction-types",
        json={"type_code": "09", "description": "   "},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_type_requires_admin(client: AsyncClient, user_token: str):
    resp = await client.post(
        "/api/transaction-types",
        json={"type_code": "08", "description": "Fee"},
        headers=user_headers(user_token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /api/transaction-types/{type_code}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_type_success(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.put(
        "/api/transaction-types/01",
        json={"description": "Purchase Updated"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Purchase Updated"


@pytest.mark.asyncio
async def test_update_type_not_found(client: AsyncClient, admin_token: str):
    resp = await client.put(
        "/api/transaction-types/99",
        json={"description": "Ghost"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_type_blank_description_rejected(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.put(
        "/api/transaction-types/01",
        json={"description": "   "},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/transaction-types/{type_code}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_type_success(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.delete(
        "/api/transaction-types/01", headers=admin_headers(admin_token)
    )
    assert resp.status_code == 204

    # Verify gone
    resp2 = await client.get(
        "/api/transaction-types/01", headers=admin_headers(admin_token)
    )
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_type_not_found(client: AsyncClient, admin_token: str):
    resp = await client.delete(
        "/api/transaction-types/99", headers=admin_headers(admin_token)
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/transaction-types/inline-save
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inline_save_success(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.post(
        "/api/transaction-types/inline-save",
        json={
            "updates": [
                {"type_code": "01", "description": "Purchase v2"},
                {"type_code": "02", "description": "Payment v2"},
            ]
        },
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["saved"] == 2
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_inline_save_empty_updates_rejected(
    client: AsyncClient, admin_token: str
):
    resp = await client.post(
        "/api/transaction-types/inline-save",
        json={"updates": []},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/transaction-types/{type_code}/categories
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_categories_success(
    client: AsyncClient, admin_token: str, seeded_categories
):
    resp = await client.get(
        "/api/transaction-types/01/categories",
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    codes = {c["category_code"] for c in data}
    assert codes == {"RETL", "ONLN"}


@pytest.mark.asyncio
async def test_list_categories_unknown_type(client: AsyncClient, admin_token: str):
    resp = await client.get(
        "/api/transaction-types/99/categories",
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/transaction-types/{type_code}/categories
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_category_success(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.post(
        "/api/transaction-types/01/categories",
        json={"category_code": "RECU", "description": "Recurring"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category_code"] == "RECU"
    assert data["type_code"] == "01"


@pytest.mark.asyncio
async def test_create_category_duplicate_returns_409(
    client: AsyncClient, admin_token: str, seeded_categories
):
    resp = await client.post(
        "/api/transaction-types/01/categories",
        json={"category_code": "RETL", "description": "Dup"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_category_blank_code_rejected(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.post(
        "/api/transaction-types/01/categories",
        json={"category_code": "  ", "description": "Blank"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/transaction-types/{type_code}/categories/{category_code}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_category_success(
    client: AsyncClient, admin_token: str, seeded_categories
):
    resp = await client.put(
        "/api/transaction-types/01/categories/RETL",
        json={"description": "Retail Purchase Updated"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Retail Purchase Updated"


@pytest.mark.asyncio
async def test_update_category_not_found(client: AsyncClient, admin_token: str, seeded_types):
    resp = await client.put(
        "/api/transaction-types/01/categories/ZZZZ",
        json={"description": "Ghost"},
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/transaction-types/{type_code}/categories/{category_code}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_category_success(
    client: AsyncClient, admin_token: str, seeded_categories
):
    resp = await client.delete(
        "/api/transaction-types/01/categories/RETL",
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_category_not_found(
    client: AsyncClient, admin_token: str, seeded_types
):
    resp = await client.delete(
        "/api/transaction-types/01/categories/ZZZZ",
        headers=admin_headers(admin_token),
    )
    assert resp.status_code == 404
