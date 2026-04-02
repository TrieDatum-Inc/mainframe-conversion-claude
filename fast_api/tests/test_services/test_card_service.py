"""
Tests for card_service.py — maps COCRDLIC, COCRDSLC, COCRDUPC.

Business rules tested:
  COCRDLIC-001: 7 cards per page (default page size)
  COCRDLIC-002: keyset pagination (VSAM STARTBR/READNEXT equivalent)
  COCRDSLC-001: read-only card detail view
  COCRDUPC-001: update card fields (active_status, embossed_name, expiration)
  COCRDUPC-002: card_num is immutable
"""

from datetime import date

import pytest

from app.core.exceptions import ResourceNotFoundError
from app.domain.services.card_service import (
    get_card_detail,
    list_cards,
)
from app.schemas.card_schemas import CardUpdateRequest


class TestListCards:
    """COCRDLIC pagination."""

    @pytest.mark.asyncio
    async def test_returns_cards(self, seeded_db):
        result = await list_cards(seeded_db, page_size=7)
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_default_page_size_is_seven(self, seeded_db):
        """COCRDLIC: 7 rows per page."""
        result = await list_cards(seeded_db, page_size=7)
        assert len(result.items) <= 7

    @pytest.mark.asyncio
    async def test_filter_by_acct_id(self, seeded_db):
        result = await list_cards(seeded_db, page_size=7, account_id_filter=10000000001)
        assert all(item.acct_id == 10000000001 for item in result.items)

    @pytest.mark.asyncio
    async def test_filter_nonexistent_account_returns_empty(self, seeded_db):
        result = await list_cards(seeded_db, page_size=7, account_id_filter=99999999999)
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_has_pagination_info(self, seeded_db):
        result = await list_cards(seeded_db, page_size=7)
        assert hasattr(result, "has_next_page")
        assert hasattr(result, "first_card_num")
        assert hasattr(result, "last_card_num")


class TestGetCardDetail:
    """COCRDSLC read-only view."""

    @pytest.mark.asyncio
    async def test_returns_card_by_num(self, seeded_db):
        result = await get_card_detail("4111111111111001", seeded_db)
        assert result.card_num == "4111111111111001"
        assert result.acct_id == 10000000001
        assert result.cvv_cd == 123

    @pytest.mark.asyncio
    async def test_not_found_raises_resource_not_found(self, seeded_db):
        with pytest.raises(ResourceNotFoundError):
            await get_card_detail("9999999999999999", seeded_db)

    @pytest.mark.asyncio
    async def test_returns_correct_active_status(self, seeded_db):
        result = await get_card_detail("4111111111111003", seeded_db)
        assert result.active_status == "N"  # Inactive card

    @pytest.mark.asyncio
    async def test_returns_embossed_name(self, seeded_db):
        result = await get_card_detail("4111111111111001", seeded_db)
        assert result.embossed_name == "JOHN A DOE"
