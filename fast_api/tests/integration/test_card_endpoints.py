"""Integration tests for all card API endpoints using in-memory SQLite."""
from datetime import date
import pytest
import pytest_asyncio
from tests.conftest import create_account, create_card


@pytest.mark.asyncio
async def test_list_cards_empty(client):
    resp = await client.get("/api/cards")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["has_next_page"] is False
    assert data["total_on_page"] == 0


@pytest.mark.asyncio
async def test_list_cards_returns_up_to_page_size(client, db_session):
    acct = await create_account(db_session)
    for i in range(1, 11):
        await create_card(db_session, card_num=f"411111111111000{i}", acct_id=acct.acct_id)
    await db_session.commit()
    resp = await client.get("/api/cards?page_size=7")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_on_page"] == 7
    assert data["has_next_page"] is True
    assert data["next_cursor"] is not None


@pytest.mark.asyncio
async def test_list_cards_cursor_pagination(client, db_session):
    acct = await create_account(db_session)
    for i in range(1, 11):
        await create_card(db_session, card_num=f"411111111111000{i}", acct_id=acct.acct_id)
    await db_session.commit()
    resp1 = await client.get("/api/cards?page_size=7")
    data1 = resp1.json()
    next_cursor = data1["next_cursor"]
    assert next_cursor is not None
    resp2 = await client.get(f"/api/cards?page_size=7&cursor={next_cursor}")
    data2 = resp2.json()
    assert data2["total_on_page"] == 3
    assert data2["has_next_page"] is False
    page1_nums = {item["card_num"] for item in data1["items"]}
    page2_nums = {item["card_num"] for item in data2["items"]}
    assert page1_nums.isdisjoint(page2_nums)


@pytest.mark.asyncio
async def test_list_cards_account_filter(client, db_session):
    acct1 = await create_account(db_session, acct_id="00000000001")
    acct2 = await create_account(db_session, acct_id="00000000002")
    await create_card(db_session, card_num="4111111111110001", acct_id=acct1.acct_id)
    await create_card(db_session, card_num="4111111111110002", acct_id=acct1.acct_id)
    await create_card(db_session, card_num="4111111111110010", acct_id=acct2.acct_id)
    await db_session.commit()
    resp = await client.get("/api/cards?acct_id=00000000001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_on_page"] == 2
    for item in data["items"]:
        assert item["card_acct_id"] == "00000000001"


@pytest.mark.asyncio
async def test_list_cards_card_num_filter(client, db_session):
    acct = await create_account(db_session)
    await create_card(db_session, card_num="4111111111110001", acct_id=acct.acct_id)
    await create_card(db_session, card_num="4111111111110002", acct_id=acct.acct_id)
    await db_session.commit()
    resp = await client.get("/api/cards?card_num_filter=4111111111110001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_on_page"] == 1
    assert data["items"][0]["card_num"] == "4111111111110001"


@pytest.mark.asyncio
async def test_get_card_detail_success(client, db_session):
    acct = await create_account(db_session)
    await create_card(db_session, card_num="4111111111110001", acct_id=acct.acct_id, cvv="123", name="ALICE JOHNSON", status="Y", exp_date=date(2026, 3, 15))
    await db_session.commit()
    resp = await client.get("/api/cards/4111111111110001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["card_num"] == "4111111111110001"
    assert data["card_cvv_cd"] == "123"
    assert data["card_embossed_name"] == "ALICE JOHNSON"
    assert data["card_active_status"] == "Y"
    assert data["expiry_month"] == 3
    assert data["expiry_year"] == 2026
    assert data["expiry_day"] == 15
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_card_detail_not_found(client):
    resp = await client.get("/api/cards/9999999999999999")
    assert resp.status_code == 404
    assert "Did not find" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_update_card_success(client, db_session):
    acct = await create_account(db_session)
    card = await create_card(db_session, card_num="4111111111110001", acct_id=acct.acct_id, exp_date=date(2026, 3, 15))
    await db_session.commit()
    await db_session.refresh(card)
    payload = {"card_embossed_name": "BOB SMITH", "card_active_status": "N", "expiry_month": 6, "expiry_year": 2027, "updated_at": card.updated_at.isoformat()}
    resp = await client.put("/api/cards/4111111111110001", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["card_embossed_name"] == "BOB SMITH"
    assert data["card_active_status"] == "N"
    assert data["expiry_month"] == 6
    assert data["expiry_year"] == 2027
    assert data["expiry_day"] == 15
    assert data["message"] == "Changes committed to database"


@pytest.mark.asyncio
async def test_update_card_not_found(client):
    payload = {"card_embossed_name": "BOB SMITH", "card_active_status": "Y", "expiry_month": 6, "expiry_year": 2027, "updated_at": "2024-01-01T12:00:00+00:00"}
    resp = await client.put("/api/cards/9999999999999999", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_card_name_with_digits_fails_validation(client, db_session):
    acct = await create_account(db_session)
    card = await create_card(db_session, acct_id=acct.acct_id)
    await db_session.commit()
    await db_session.refresh(card)
    payload = {"card_embossed_name": "ALICE123", "card_active_status": "Y", "expiry_month": 3, "expiry_year": 2026, "updated_at": card.updated_at.isoformat()}
    resp = await client.put("/api/cards/4111111111110001", json=payload)
    assert resp.status_code == 422
    body = resp.json()
    assert any("alphabets" in str(e).lower() for e in body["detail"])


@pytest.mark.asyncio
async def test_update_card_invalid_status_fails_validation(client, db_session):
    acct = await create_account(db_session)
    card = await create_card(db_session, acct_id=acct.acct_id)
    await db_session.commit()
    await db_session.refresh(card)
    payload = {"card_embossed_name": "ALICE JOHNSON", "card_active_status": "X", "expiry_month": 3, "expiry_year": 2026, "updated_at": card.updated_at.isoformat()}
    resp = await client.put("/api/cards/4111111111110001", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_card_invalid_month_fails_validation(client, db_session):
    acct = await create_account(db_session)
    card = await create_card(db_session, acct_id=acct.acct_id)
    await db_session.commit()
    await db_session.refresh(card)
    payload = {"card_embossed_name": "ALICE JOHNSON", "card_active_status": "Y", "expiry_month": 13, "expiry_year": 2026, "updated_at": card.updated_at.isoformat()}
    resp = await client.put("/api/cards/4111111111110001", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_card_invalid_year_fails_validation(client, db_session):
    acct = await create_account(db_session)
    card = await create_card(db_session, acct_id=acct.acct_id)
    await db_session.commit()
    await db_session.refresh(card)
    payload = {"card_embossed_name": "ALICE JOHNSON", "card_active_status": "Y", "expiry_month": 3, "expiry_year": 2100, "updated_at": card.updated_at.isoformat()}
    resp = await client.put("/api/cards/4111111111110001", json=payload)
    assert resp.status_code == 422
