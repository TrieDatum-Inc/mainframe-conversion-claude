"""Tests for bill payment endpoint (POST /api/bill-payment).

Ports validation from COBOL program COBIL00C which handles the
two-step bill payment confirmation flow: preview (confirm='N')
then process (confirm='Y').
"""


def test_bill_payment_preview(client, seed_data, admin_headers):
    """Preview mode (confirm='N') returns current balance information."""
    response = client.post(
        "/api/bill-payment",
        headers=admin_headers,
        json={"acct_id": 10000000001, "confirm": "N"},
    )
    assert response.status_code == 200
    data = response.json()
    # Preview should show balance and/or a confirmation prompt message
    assert "previous_balance" in data or "balance" in data["message"].lower()


def test_bill_payment_confirm(client, seed_data, admin_headers):
    """Confirmed payment (confirm='Y') succeeds with 'Payment successful'."""
    response = client.post(
        "/api/bill-payment",
        headers=admin_headers,
        json={"acct_id": 10000000001, "confirm": "Y"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Payment successful" in data["message"]


def test_bill_payment_not_found(client, seed_data, admin_headers):
    """Bill payment with non-existent account returns 404."""
    response = client.post(
        "/api/bill-payment",
        headers=admin_headers,
        json={"acct_id": 99999999999, "confirm": "Y"},
    )
    assert response.status_code == 404
