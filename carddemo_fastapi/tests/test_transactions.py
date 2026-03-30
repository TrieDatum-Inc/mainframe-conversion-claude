"""Tests for transaction endpoints (GET/POST on /api/transactions).

Ports validation from COBOL programs COTRN00C (list), COTRN01C (detail),
and COTRN02C (add with two-step confirmation flow).
"""

from decimal import Decimal


def test_list_transactions(client, seed_data, admin_headers):
    """List transactions; response contains paginated items."""
    response = client.get("/api/transactions", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["total_count"] >= 3


def test_get_transaction(client, seed_data, admin_headers):
    """Retrieve a specific transaction by ID."""
    response = client.get(
        "/api/transactions/0000000000000001",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tran_id"] == "0000000000000001"


def test_get_transaction_not_found(client, seed_data, admin_headers):
    """Non-existent transaction ID returns 404."""
    response = client.get(
        "/api/transactions/0000000000000099",
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_add_transaction_confirm(client, seed_data, admin_headers):
    """Confirmed transaction (confirm='Y') is committed to the database."""
    response = client.post(
        "/api/transactions",
        headers=admin_headers,
        json={
            "card_num": "4111111111111111",
            "tran_type_cd": "01",
            "tran_cat_cd": 1,
            "tran_source": "ONLINE",
            "tran_desc": "TEST PURCHASE",
            "tran_amt": 75.50,
            "tran_merchant_id": 200001,
            "tran_merchant_name": "TEST MERCHANT",
            "tran_merchant_city": "NEW YORK",
            "tran_merchant_zip": "10001",
            "confirm": "Y",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "committed" in data["message"].lower()


def test_add_transaction_no_confirm(client, seed_data, admin_headers):
    """Unconfirmed transaction (confirm='N') returns confirmation prompt."""
    response = client.post(
        "/api/transactions",
        headers=admin_headers,
        json={
            "card_num": "4111111111111111",
            "tran_type_cd": "01",
            "tran_cat_cd": 1,
            "tran_source": "ONLINE",
            "tran_desc": "TEST PURCHASE",
            "tran_amt": 75.50,
            "tran_merchant_id": 200001,
            "tran_merchant_name": "TEST MERCHANT",
            "tran_merchant_city": "NEW YORK",
            "tran_merchant_zip": "10001",
            "confirm": "N",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "Confirm" in data["message"] or "confirm" in data["message"].lower()


def test_add_transaction_missing_card(client, seed_data, admin_headers):
    """Transaction without card_num or acct_id returns 422."""
    response = client.post(
        "/api/transactions",
        headers=admin_headers,
        json={
            "tran_type_cd": "01",
            "tran_cat_cd": 1,
            "tran_source": "ONLINE",
            "tran_desc": "TEST PURCHASE",
            "tran_amt": 75.50,
            "tran_merchant_id": 200001,
            "tran_merchant_name": "TEST MERCHANT",
            "tran_merchant_city": "NEW YORK",
            "tran_merchant_zip": "10001",
            "confirm": "Y",
        },
    )
    assert response.status_code == 422
