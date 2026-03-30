"""Tests for authorization endpoints on /api/authorizations.

Ports validation from COBOL programs COPAUS0C (summary list),
COPAUS1C / COPAUA0C (detail view), COPAUS2C (fraud marking),
and COPAUA0C (authorization decision).
"""


def test_list_auth_summary(client, seed_data, admin_headers):
    """List pending authorization summaries; response is paginated."""
    response = client.get(
        "/api/authorizations/summary",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["total_count"] >= 1


def test_get_auth_detail(client, seed_data, admin_headers):
    """Retrieve authorization detail for an account with summary and details."""
    response = client.get(
        "/api/authorizations/10000000001/detail",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "details" in data
    assert isinstance(data["details"], list)


def test_get_auth_detail_not_found(client, seed_data, admin_headers):
    """Non-existent account authorization detail returns 404."""
    response = client.get(
        "/api/authorizations/99999999999/detail",
        headers=admin_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Authorization Decision Tests (POST /api/authorizations/decide)
# Ports COBOL program COPAUA0C authorization decision engine
# ---------------------------------------------------------------------------


def test_auth_decide_approve_with_summary(client, seed_data, admin_headers):
    """Approve when summary exists and available credit is sufficient.

    Seed: acct 10000000001 pa_credit_limit=5000, pa_credit_balance=3500.
    Available = 1500.  amt=500 < 1500 -> APPROVED.
    """
    response = client.post(
        "/api/authorizations/decide",
        headers=admin_headers,
        json={
            "card_num": "4111111111111111",
            "auth_type": "0100",
            "card_expiry_date": "1225",
            "transaction_amt": 500.00,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["card_num"] == "4111111111111111"
    assert data["auth_resp_code"] == "00"
    assert data["auth_resp_reason"] == "0000"
    assert float(data["approved_amt"]) == 500.00
    assert data["transaction_id"] is not None


def test_auth_decide_decline_insufficient_funds_with_summary(
    client, seed_data, admin_headers
):
    """Decline when summary exists but available credit is insufficient.

    Available = 5000 - 3500 = 1500.  amt=2000 > 1500 -> DECLINED 4100.
    """
    response = client.post(
        "/api/authorizations/decide",
        headers=admin_headers,
        json={
            "card_num": "4111111111111111",
            "auth_type": "0100",
            "card_expiry_date": "1225",
            "transaction_amt": 2000.00,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auth_resp_code"] == "05"
    assert data["auth_resp_reason"] == "4100"
    assert float(data["approved_amt"]) == 0.0


def test_auth_decide_approve_without_summary(client, seed_data, admin_headers):
    """Approve when no summary exists, using account master data.

    Card 5333333333333333 -> acct 20000000002: credit_limit=10000, curr_bal=3000.
    No pending_auth_summary.  Available = 7000.  amt=1000 -> APPROVED.
    """
    response = client.post(
        "/api/authorizations/decide",
        headers=admin_headers,
        json={
            "card_num": "5333333333333333",
            "auth_type": "0100",
            "card_expiry_date": "0626",
            "transaction_amt": 1000.00,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auth_resp_code"] == "00"
    assert data["auth_resp_reason"] == "0000"
    assert float(data["approved_amt"]) == 1000.00


def test_auth_decide_decline_insufficient_funds_no_summary(
    client, seed_data, admin_headers
):
    """Decline when no summary exists and transaction exceeds available credit.

    Card 5333333333333333 -> acct 20000000002: credit_limit=10000, curr_bal=3000.
    Available = 7000.  amt=8000 > 7000 -> DECLINED 4100.
    """
    response = client.post(
        "/api/authorizations/decide",
        headers=admin_headers,
        json={
            "card_num": "5333333333333333",
            "auth_type": "0100",
            "card_expiry_date": "0626",
            "transaction_amt": 8000.00,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auth_resp_code"] == "05"
    assert data["auth_resp_reason"] == "4100"
    assert float(data["approved_amt"]) == 0.0


def test_auth_decide_card_not_found(client, seed_data, admin_headers):
    """Decline when card number is not in the cross-reference.

    Returns 200 with resp_code='05' and reason='3100' (matches COBOL behavior
    where COPAUA0C sends a structured decline, not an abort).
    """
    response = client.post(
        "/api/authorizations/decide",
        headers=admin_headers,
        json={
            "card_num": "9999999999999999",
            "auth_type": "0100",
            "card_expiry_date": "1225",
            "transaction_amt": 100.00,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auth_resp_code"] == "05"
    assert data["auth_resp_reason"] == "3100"
    assert float(data["approved_amt"]) == 0.0


def test_auth_decide_exact_available_amount(client, seed_data, admin_headers):
    """Approve when transaction amount equals exactly the available credit.

    Available = 5000 - 3500 = 1500.  amt=1500 is NOT > 1500 -> APPROVED.
    COBOL line 668 uses '>' not '>=', so equal amounts approve.
    """
    response = client.post(
        "/api/authorizations/decide",
        headers=admin_headers,
        json={
            "card_num": "4111111111111111",
            "auth_type": "0100",
            "card_expiry_date": "1225",
            "transaction_amt": 1500.00,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auth_resp_code"] == "00"
    assert data["auth_resp_reason"] == "0000"


def test_auth_decide_with_merchant_fields(client, seed_data, admin_headers):
    """Approve with full merchant information included in request."""
    response = client.post(
        "/api/authorizations/decide",
        headers=admin_headers,
        json={
            "card_num": "5333333333333333",
            "auth_type": "0100",
            "card_expiry_date": "0626",
            "transaction_amt": 100.00,
            "merchant_category_code": "5411",
            "acqr_country_code": "840",
            "pos_entry_mode": 51,
            "merchant_id": "MID000000000002",
            "merchant_name": "TEST GROCERY",
            "merchant_city": "LOS ANGELES",
            "merchant_state": "CA",
            "merchant_zip": "90210",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["auth_resp_code"] == "00"


def test_auth_decide_creates_summary_record(client, seed_data, admin_headers):
    """When no summary exists, the endpoint creates one after approval.

    Card 5333333333333333 -> acct 20000000002 has no pending_auth_summary.
    After approval, GET detail should return the created summary and detail.
    """
    client.post(
        "/api/authorizations/decide",
        headers=admin_headers,
        json={
            "card_num": "5333333333333333",
            "auth_type": "0100",
            "card_expiry_date": "0626",
            "transaction_amt": 100.00,
        },
    )
    detail_resp = client.get(
        "/api/authorizations/20000000002/detail",
        headers=admin_headers,
    )
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["summary"]["pa_acct_id"] == 20000000002
    assert detail_data["summary"]["pa_approved_auth_cnt"] >= 1
    assert len(detail_data["details"]) >= 1


def test_auth_decide_unauthenticated(client, seed_data):
    """Unauthenticated request returns 401 or 403."""
    response = client.post(
        "/api/authorizations/decide",
        json={
            "card_num": "4111111111111111",
            "auth_type": "0100",
            "card_expiry_date": "1225",
            "transaction_amt": 100.00,
        },
    )
    assert response.status_code in (401, 403)
