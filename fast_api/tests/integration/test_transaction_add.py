"""
Integration tests for POST /api/transactions/validate and POST /api/transactions.
Tests COTRN02C business rules: key lookup, validation, confirmation, auto-increment.
"""

import pytest


VALID_REQUEST = {
    "card_num": "4111111111111111",
    "tran_type_cd": "01",
    "tran_cat_cd": "0001",
    "tran_source": "ONLINE",
    "tran_desc": "Test grocery purchase",
    "tran_amt": "-00000052.47",
    "tran_orig_dt": "2026-03-01",
    "tran_proc_dt": "2026-03-01",
    "tran_merchant_id": "000000001",
    "tran_merchant_name": "Test Merchant",
    "tran_merchant_city": "New York",
    "tran_merchant_zip": "10001",
}


@pytest.mark.asyncio
class TestTransactionValidate:
    """Tests for POST /api/transactions/validate — step 1 (enter data phase)."""

    async def test_valid_card_returns_resolved_info(self, client, seed_data):
        resp = await client.post("/api/transactions/validate", json=VALID_REQUEST)
        assert resp.status_code == 200
        body = resp.json()
        assert body["resolved_card_num"] == "4111111111111111"
        assert body["resolved_acct_id"] == "00000000001"
        assert body["acct_active"] is True

    async def test_validate_via_acct_id_resolves_card(self, client, seed_data):
        """Path 1: Account ID entered → resolves card via CXACAIX alternate index."""
        payload = {**VALID_REQUEST}
        del payload["card_num"]
        payload["acct_id"] = "00000000001"
        resp = await client.post("/api/transactions/validate", json=payload)
        assert resp.status_code == 200
        assert resp.json()["resolved_card_num"] == "4111111111111111"

    async def test_unknown_card_returns_404(self, client, seed_data):
        """Business rule: Card Number NOT found → NOTFND on READ-CCXREF-FILE."""
        payload = {**VALID_REQUEST, "card_num": "0000000000000000"}
        resp = await client.post("/api/transactions/validate", json=payload)
        assert resp.status_code == 404
        assert "NOT found" in resp.json()["detail"]

    async def test_unknown_acct_returns_404(self, client, seed_data):
        """Business rule: Account ID NOT found → NOTFND on READ-CXACAIX-FILE."""
        payload = {**VALID_REQUEST}
        del payload["card_num"]
        payload["acct_id"] = "99999999999"
        resp = await client.post("/api/transactions/validate", json=payload)
        assert resp.status_code == 404

    async def test_inactive_account_flagged(self, client, seed_data):
        """Account linked to 4222222222222222 has acct_active_status='N'."""
        payload = {**VALID_REQUEST, "card_num": "4222222222222222"}
        resp = await client.post("/api/transactions/validate", json=payload)
        assert resp.status_code == 422
        assert "not active" in resp.json()["detail"].lower()

    async def test_normalized_amount_returned(self, client, seed_data):
        resp = await client.post("/api/transactions/validate", json=VALID_REQUEST)
        assert resp.status_code == 200
        assert resp.json()["normalized_amt"] is not None


@pytest.mark.asyncio
class TestTransactionCreate:
    """Tests for POST /api/transactions — step 2 (confirmation phase)."""

    async def test_create_with_confirmation_y_returns_201(self, client, seed_data):
        payload = {**VALID_REQUEST, "confirm": "Y"}
        resp = await client.post("/api/transactions", json=payload)
        assert resp.status_code == 201

    async def test_created_transaction_has_all_fields(self, client, seed_data):
        payload = {**VALID_REQUEST, "confirm": "Y"}
        resp = await client.post("/api/transactions", json=payload)
        body = resp.json()
        assert "tran_id" in body
        assert body["tran_card_num"] == "4111111111111111"
        assert body["tran_desc"] == "Test grocery purchase"

    async def test_auto_generated_id_is_sequential(self, client, seed_data):
        """
        Auto-increment ID: 25 seed transactions exist → new ID = 0000000000000026.
        Mirrors COTRN02C ADD-TRANSACTION: READPREV last record + 1.
        """
        payload = {**VALID_REQUEST, "confirm": "Y"}
        resp = await client.post("/api/transactions", json=payload)
        assert resp.status_code == 201
        tran_id = resp.json()["tran_id"]
        assert tran_id == "0000000000000026"

    async def test_auto_generated_id_increments_on_second_add(self, client, seed_data):
        """Second add gets ID 27 after first add gets 26."""
        payload = {**VALID_REQUEST, "confirm": "Y"}
        resp1 = await client.post("/api/transactions", json=payload)
        resp2 = await client.post("/api/transactions", json=payload)
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        id1 = int(resp1.json()["tran_id"])
        id2 = int(resp2.json()["tran_id"])
        assert id2 == id1 + 1

    async def test_confirmation_n_rejected_at_schema_level(self, client, seed_data):
        """confirm='N' is rejected by schema (mirrors COTRN02C confirm check)."""
        payload = {**VALID_REQUEST, "confirm": "N"}
        resp = await client.post("/api/transactions", json=payload)
        assert resp.status_code == 422

    async def test_inactive_account_prevents_create(self, client, seed_data):
        """Account 00000000002 is inactive → transaction should be rejected."""
        payload = {**VALID_REQUEST, "card_num": "4222222222222222", "confirm": "Y"}
        resp = await client.post("/api/transactions", json=payload)
        assert resp.status_code == 422
        assert "not active" in resp.json()["detail"].lower()

    async def test_card_not_found_returns_404_on_create(self, client, seed_data):
        payload = {**VALID_REQUEST, "card_num": "0000000000000000", "confirm": "Y"}
        resp = await client.post("/api/transactions", json=payload)
        assert resp.status_code == 404

    async def test_proc_ts_set_automatically(self, client, seed_data):
        """Processing timestamp is auto-set at creation (mirrors ASKTIME/FORMATTIME)."""
        payload = {**VALID_REQUEST, "confirm": "Y"}
        resp = await client.post("/api/transactions", json=payload)
        assert resp.status_code == 201
        assert resp.json()["tran_proc_ts"] is not None

    async def test_created_record_retrievable_by_id(self, client, seed_data):
        """After creation, record should be fetchable via GET /api/transactions/{id}."""
        payload = {**VALID_REQUEST, "confirm": "Y"}
        create_resp = await client.post("/api/transactions", json=payload)
        assert create_resp.status_code == 201
        tran_id = create_resp.json()["tran_id"]
        get_resp = await client.get(f"/api/transactions/{tran_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["tran_id"] == tran_id


@pytest.mark.asyncio
class TestCopyLastTransaction:
    """Tests for GET /api/transactions/copy-last — PF5 equivalent."""

    async def test_returns_last_transaction(self, client, seed_data):
        resp = await client.get(
            "/api/transactions/copy-last?card_num=4111111111111111"
        )
        assert resp.status_code == 200
        # Last seeded transaction is 0000000000000025
        assert resp.json()["tran_id"] == "0000000000000025"

    async def test_missing_key_returns_422(self, client, seed_data):
        resp = await client.get("/api/transactions/copy-last")
        assert resp.status_code == 422
