"""Tests for account endpoints (GET/PUT on /api/accounts).

Ports validation from COBOL programs COACTVWC (view) and COACTUPC
(update), including joined customer data and field-level validation.
"""

from decimal import Decimal


def test_get_account(client, seed_data, admin_headers):
    """Retrieve an account; response contains the acct_id field."""
    response = client.get(
        "/api/accounts/10000000001",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["acct_id"] == 10000000001


def test_get_account_not_found(client, seed_data, admin_headers):
    """Non-existent account returns 404."""
    response = client.get(
        "/api/accounts/99999999999",
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_update_account(client, seed_data, admin_headers):
    """Update credit limit; response confirms change."""
    response = client.put(
        "/api/accounts/10000000001",
        headers=admin_headers,
        json={"acct_credit_limit": 7500.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert "committed" in data["message"].lower() or "Changes" in data["message"]


def test_update_account_invalid_status(client, seed_data, admin_headers):
    """Setting acct_active_status to an invalid value returns 422."""
    response = client.put(
        "/api/accounts/10000000001",
        headers=admin_headers,
        json={"acct_active_status": "X"},
    )
    assert response.status_code == 422
