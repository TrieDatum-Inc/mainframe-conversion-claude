"""Tests for card endpoints (GET/PUT on /api/cards).

Ports validation from COBOL programs COCRDLIC (list), COCRDSLC (detail),
and COCRDUPC (update) including card name alpha validation.
"""


def test_list_cards(client, seed_data, admin_headers):
    """List all cards; response contains a paginated items list."""
    response = client.get("/api/cards", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["total_count"] >= 3


def test_list_cards_by_account(client, seed_data, admin_headers):
    """Filter cards by account ID; only matching cards returned."""
    response = client.get(
        "/api/cards",
        headers=admin_headers,
        params={"acct_id": 10000000001},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    # Account 10000000001 has 2 cards in seed data
    for card in data["items"]:
        assert card["card_acct_id"] == 10000000001


def test_get_card_detail(client, seed_data, admin_headers):
    """Retrieve full detail for a specific card."""
    response = client.get(
        "/api/cards/4111111111111111",
        headers=admin_headers,
        params={"acct_id": 10000000001},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["card_num"] == "4111111111111111"
    assert data["card_acct_id"] == 10000000001


def test_get_card_not_found(client, seed_data, admin_headers):
    """Non-existent card returns 404."""
    response = client.get(
        "/api/cards/9999999999999999",
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_update_card(client, seed_data, admin_headers):
    """Update card embossed name; response confirms change."""
    response = client.put(
        "/api/cards/4111111111111111",
        headers=admin_headers,
        params={"acct_id": 10000000001},
        json={"card_embossed_name": "JOHN DOE UPDATED"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "committed" in data["message"].lower() or "Changes" in data["message"]


def test_update_card_invalid_name(client, seed_data, admin_headers):
    """Non-alpha embossed name returns 422."""
    response = client.put(
        "/api/cards/4111111111111111",
        headers=admin_headers,
        params={"acct_id": 10000000001},
        json={"card_embossed_name": "John123"},
    )
    assert response.status_code == 422
