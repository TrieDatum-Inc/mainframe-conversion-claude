"""Tests for transaction type endpoints (CRUD on /api/transaction-types).

Ports validation from COBOL programs COTRTLIC (list) and COTRTUPC
(create/update/delete) with FK checks against transaction_categories.
"""


def test_list_transaction_types(client, seed_data, admin_headers):
    """List transaction types; response contains paginated items."""
    response = client.get(
        "/api/transaction-types",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["total_count"] >= 2


def test_get_transaction_type(client, seed_data, admin_headers):
    """Retrieve a specific transaction type by code."""
    response = client.get(
        "/api/transaction-types/01",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tran_type"] == "01"
    assert data["tran_type_desc"] == "Purchase"


def test_create_transaction_type(client, seed_data, admin_headers):
    """Admin can create a new transaction type."""
    response = client.post(
        "/api/transaction-types",
        headers=admin_headers,
        json={"tran_type": "03", "tran_type_desc": "Refund"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "created" in data["message"].lower() or "03" in data["message"]


def test_create_duplicate(client, seed_data, admin_headers):
    """Creating a transaction type with an existing code returns 409."""
    response = client.post(
        "/api/transaction-types",
        headers=admin_headers,
        json={"tran_type": "01", "tran_type_desc": "Duplicate Purchase"},
    )
    assert response.status_code == 409


def test_update_transaction_type(client, seed_data, admin_headers):
    """Admin can update a transaction type description."""
    response = client.put(
        "/api/transaction-types/01",
        headers=admin_headers,
        json={"tran_type_desc": "Purchase Transaction"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "updated" in data["message"].lower()


def test_delete_transaction_type(client, seed_data, admin_headers):
    """Admin can delete a transaction type that has no category references.

    First create a fresh type with no categories, then delete it.
    """
    # Create a type with no FK references
    client.post(
        "/api/transaction-types",
        headers=admin_headers,
        json={"tran_type": "99", "tran_type_desc": "Temp Type"},
    )

    # Now delete it
    response = client.delete(
        "/api/transaction-types/99",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data["message"].lower()
