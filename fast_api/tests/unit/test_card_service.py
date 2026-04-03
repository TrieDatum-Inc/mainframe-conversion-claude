"""Unit tests for CardService business logic."""
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.card import CardUpdateRequest
from app.services.card_service import CardService, _card_to_detail
from app.utils.exceptions import CardNotFoundError, CardUpdateLockError, ConcurrentModificationError


def _make_card(card_num="4111111111110001", acct_id="00000000001", cvv="123", name="ALICE JOHNSON", status="Y", exp_date=None, updated_at=None):
    card = MagicMock()
    card.card_num = card_num
    card.card_acct_id = acct_id
    card.card_cvv_cd = cvv
    card.card_embossed_name = name
    card.card_active_status = status
    card.card_expiration_date = exp_date or date(2026, 3, 15)
    card.updated_at = updated_at or datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    return card


def _make_service(repo=None):
    if repo is None:
        repo = MagicMock()
    return CardService(repo)


def test_card_to_detail_splits_expiry_components():
    card = _make_card(exp_date=date(2026, 3, 15))
    detail = _card_to_detail(card)
    assert detail.expiry_month == 3
    assert detail.expiry_year == 2026
    assert detail.expiry_day == 15


def test_card_to_detail_handles_null_expiry():
    card = _make_card(exp_date=None)
    card.card_expiration_date = None
    detail = _card_to_detail(card)
    assert detail.expiry_month is None
    assert detail.expiry_year is None
    assert detail.expiry_day is None


@pytest.mark.asyncio
async def test_list_cards_returns_page():
    cards = [_make_card(card_num=f"411111111111000{i}") for i in range(3)]
    repo = MagicMock()
    repo.list_cards_forward = AsyncMock(return_value=(cards, False, None))
    result = await _make_service(repo).list_cards(cursor=None, page_size=7, acct_id=None, card_num_filter=None)
    assert len(result.items) == 3
    assert result.has_next_page is False
    assert result.total_on_page == 3


@pytest.mark.asyncio
async def test_list_cards_has_next_page_sets_cursor():
    cards = [_make_card(card_num=f"411111111111000{i}") for i in range(7)]
    repo = MagicMock()
    repo.list_cards_forward = AsyncMock(return_value=(cards, True, "4111111111110080"))
    result = await _make_service(repo).list_cards(cursor="4111111111110001", page_size=7, acct_id=None, card_num_filter=None)
    assert result.has_next_page is True
    assert result.next_cursor == "4111111111110080"
    assert result.prev_cursor == "4111111111110001"


@pytest.mark.asyncio
async def test_list_cards_passes_filters_to_repo():
    repo = MagicMock()
    repo.list_cards_forward = AsyncMock(return_value=([], False, None))
    await _make_service(repo).list_cards(cursor=None, page_size=7, acct_id="00000000001", card_num_filter="4111111111110001")
    repo.list_cards_forward.assert_called_once_with(cursor=None, page_size=7, acct_id="00000000001", card_num_filter="4111111111110001")


@pytest.mark.asyncio
async def test_get_card_detail_returns_card():
    card = _make_card()
    repo = MagicMock()
    repo.get_card_by_num = AsyncMock(return_value=card)
    detail = await _make_service(repo).get_card_detail("4111111111110001")
    assert detail.card_num == "4111111111110001"
    assert detail.card_active_status == "Y"


@pytest.mark.asyncio
async def test_get_card_detail_raises_not_found():
    repo = MagicMock()
    repo.get_card_by_num = AsyncMock(side_effect=CardNotFoundError("9999999999999999"))
    with pytest.raises(CardNotFoundError):
        await _make_service(repo).get_card_detail("9999999999999999")


@pytest.mark.asyncio
async def test_update_card_succeeds_when_timestamps_match():
    ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    locked = _make_card(updated_at=ts)
    updated = _make_card(name="BOB SMITH", status="N", exp_date=date(2027, 6, 15), updated_at=datetime(2024, 1, 1, 12, 0, 1, tzinfo=timezone.utc))
    repo = MagicMock()
    repo.get_card_for_update = AsyncMock(return_value=locked)
    repo.update_card = AsyncMock(return_value=updated)
    req = CardUpdateRequest(card_embossed_name="BOB SMITH", card_active_status="N", expiry_month=6, expiry_year=2027, updated_at=ts)
    result = await _make_service(repo).update_card("4111111111110001", req)
    assert result.card_embossed_name == "BOB SMITH"
    assert result.message == "Changes committed to database"


@pytest.mark.asyncio
async def test_update_card_raises_concurrent_modification_when_ts_differs():
    ts_db = datetime(2024, 1, 1, 12, 0, 5, tzinfo=timezone.utc)
    ts_client = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    locked = _make_card(updated_at=ts_db)
    repo = MagicMock()
    repo.get_card_for_update = AsyncMock(return_value=locked)
    req = CardUpdateRequest(card_embossed_name="ALICE JOHNSON", card_active_status="Y", expiry_month=3, expiry_year=2026, updated_at=ts_client)
    with pytest.raises(ConcurrentModificationError):
        await _make_service(repo).update_card("4111111111110001", req)


@pytest.mark.asyncio
async def test_update_card_raises_lock_error():
    repo = MagicMock()
    repo.get_card_for_update = AsyncMock(side_effect=CardUpdateLockError("4111111111110001"))
    req = CardUpdateRequest(card_embossed_name="ALICE JOHNSON", card_active_status="Y", expiry_month=3, expiry_year=2026, updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
    with pytest.raises(CardUpdateLockError):
        await _make_service(repo).update_card("4111111111110001", req)


@pytest.mark.asyncio
async def test_update_preserves_expiry_day():
    ts = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    original_day = 28
    locked = _make_card(updated_at=ts, exp_date=date(2026, 3, original_day))
    updated = _make_card(exp_date=date(2027, 6, original_day), updated_at=datetime(2024, 1, 1, 12, 0, 1, tzinfo=timezone.utc))
    repo = MagicMock()
    repo.get_card_for_update = AsyncMock(return_value=locked)
    repo.update_card = AsyncMock(return_value=updated)
    req = CardUpdateRequest(card_embossed_name="ALICE JOHNSON", card_active_status="Y", expiry_month=6, expiry_year=2027, updated_at=ts)
    await _make_service(repo).update_card("4111111111110001", req)
    repo.update_card.assert_called_once_with(card_num="4111111111110001", embossed_name="ALICE JOHNSON", active_status="Y", expiry_month=6, expiry_year=2027, expiry_day=original_day)
