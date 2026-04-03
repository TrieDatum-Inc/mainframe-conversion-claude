"""
Integration tests for GET /api/transactions — COTRN00C equivalent.
Tests pagination, search, and navigation business rules.
"""

import pytest


@pytest.mark.asyncio
class TestTransactionList:
    """Tests for CT00 (COTRN00C) paginated list endpoint."""

    async def test_list_returns_default_page(self, client, seed_data):
        resp = await client.get("/api/transactions")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "pagination" in body
        assert len(body["items"]) == 10  # COBOL default page size

    async def test_list_items_have_required_fields(self, client, seed_data):
        resp = await client.get("/api/transactions")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert "tran_id" in item
        assert "tran_orig_ts" in item
        assert "tran_desc" in item
        assert "tran_amt" in item

    async def test_pagination_has_next_page(self, client, seed_data):
        """25 records with page_size=10 → has_next_page=True on page 1."""
        resp = await client.get("/api/transactions?page=1&page_size=10")
        assert resp.status_code == 200
        pagination = resp.json()["pagination"]
        assert pagination["has_next_page"] is True
        assert pagination["has_prev_page"] is False

    async def test_pagination_no_prev_on_first_page(self, client, seed_data):
        resp = await client.get("/api/transactions?page=1")
        assert resp.json()["pagination"]["has_prev_page"] is False

    async def test_last_page_no_next(self, client, seed_data):
        """Page 3 with 25 records and page_size=10 → has_next_page=False."""
        last_id = "0000000000000021"  # start of last page
        resp = await client.get(
            f"/api/transactions?page=3&page_size=10&start_tran_id={last_id}"
        )
        assert resp.status_code == 200
        pagination = resp.json()["pagination"]
        assert pagination["has_next_page"] is False

    async def test_start_tran_id_filters_forward(self, client, seed_data):
        """TRNIDINI search field — browse starts at given ID."""
        resp = await client.get(
            "/api/transactions?start_tran_id=0000000000000011"
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert items[0]["tran_id"] == "0000000000000011"

    async def test_non_numeric_tran_id_returns_422(self, client, seed_data):
        """Business rule: Tran ID must be Numeric."""
        resp = await client.get("/api/transactions?start_tran_id=NOTANUMBER")
        assert resp.status_code == 422
        assert "Tran ID must be Numeric" in resp.json()["detail"]

    async def test_backward_direction_from_page_one_returns_400(self, client, seed_data):
        """Business rule: cannot go backward from page 1."""
        resp = await client.get(
            "/api/transactions?direction=backward&page=1&anchor_tran_id=0000000000000010"
        )
        assert resp.status_code == 400
        assert "top of the page" in resp.json()["detail"]

    async def test_backward_navigation(self, client, seed_data):
        """PF7 backward navigation — returns previous page records."""
        resp = await client.get(
            "/api/transactions?direction=backward&page=2&anchor_tran_id=0000000000000010"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) > 0

    async def test_page_size_respected(self, client, seed_data):
        resp = await client.get("/api/transactions?page_size=5")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 5

    async def test_pagination_metadata_contains_first_last_ids(self, client, seed_data):
        resp = await client.get("/api/transactions?page_size=10")
        pagination = resp.json()["pagination"]
        assert pagination["first_tran_id"] is not None
        assert pagination["last_tran_id"] is not None
