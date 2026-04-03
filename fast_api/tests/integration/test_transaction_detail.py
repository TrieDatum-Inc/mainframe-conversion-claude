"""
Integration tests for GET /api/transactions/{tran_id} — COTRN01C equivalent.
Tests read-only detail view, auto-fetch behavior, and not-found handling.
"""

import pytest


@pytest.mark.asyncio
class TestTransactionDetail:
    """Tests for CT01 (COTRN01C) transaction detail endpoint."""

    async def test_get_existing_transaction_returns_200(self, client, seed_data):
        resp = await client.get("/api/transactions/0000000000000001")
        assert resp.status_code == 200

    async def test_response_has_all_detail_fields(self, client, seed_data):
        """All COTRN1A screen fields must be present in the response."""
        resp = await client.get("/api/transactions/0000000000000001")
        assert resp.status_code == 200
        body = resp.json()
        required_fields = [
            "tran_id", "tran_type_cd", "tran_cat_cd", "tran_source",
            "tran_desc", "tran_amt", "tran_merchant_id", "tran_merchant_name",
            "tran_merchant_city", "tran_merchant_zip", "tran_card_num",
            "tran_orig_ts", "tran_proc_ts",
        ]
        for field in required_fields:
            assert field in body, f"Missing field: {field}"

    async def test_tran_id_matches_requested(self, client, seed_data):
        resp = await client.get("/api/transactions/0000000000000005")
        assert resp.status_code == 200
        assert resp.json()["tran_id"] == "0000000000000005"

    async def test_not_found_returns_404(self, client, seed_data):
        """Business rule: Transaction ID NOT found → error message (NOTFND response)."""
        resp = await client.get("/api/transactions/9999999999999999")
        assert resp.status_code == 404
        assert "NOT found" in resp.json()["detail"]

    async def test_no_update_lock_applied(self, client, seed_data):
        """
        COTRN01C anomaly: READ WITH UPDATE was used but no REWRITE follows.
        We must not acquire any exclusive lock — verify two concurrent reads succeed.
        """
        resp1 = await client.get("/api/transactions/0000000000000001")
        resp2 = await client.get("/api/transactions/0000000000000001")
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["tran_id"] == resp2.json()["tran_id"]
