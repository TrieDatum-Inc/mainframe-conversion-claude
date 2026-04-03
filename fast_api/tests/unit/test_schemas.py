"""Unit tests for Pydantic schema validation — mirrors COBOL field edit paragraphs."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.schemas.card import CardUpdateRequest


def valid_request(**overrides) -> dict:
    base = {"card_embossed_name": "ALICE JOHNSON", "card_active_status": "Y", "expiry_month": 3, "expiry_year": 2026, "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc)}
    base.update(overrides)
    return base


def test_name_valid_alphabetic():
    req = CardUpdateRequest(**valid_request(card_embossed_name="ALICE JOHNSON"))
    assert req.card_embossed_name == "ALICE JOHNSON"

def test_name_lowercase_is_uppercased():
    req = CardUpdateRequest(**valid_request(card_embossed_name="alice johnson"))
    assert req.card_embossed_name == "ALICE JOHNSON"

def test_name_with_digits_fails():
    with pytest.raises(ValidationError) as exc_info:
        CardUpdateRequest(**valid_request(card_embossed_name="ALICE123"))
    assert "alphabets and spaces" in str(exc_info.value)

def test_name_with_special_chars_fails():
    with pytest.raises(ValidationError) as exc_info:
        CardUpdateRequest(**valid_request(card_embossed_name="ALICE-JOHNSON"))
    assert "alphabets and spaces" in str(exc_info.value)

def test_name_blank_fails():
    with pytest.raises(ValidationError) as exc_info:
        CardUpdateRequest(**valid_request(card_embossed_name="   "))
    assert "not provided" in str(exc_info.value).lower() or "alphabets" in str(exc_info.value).lower()

def test_status_y_valid():
    assert CardUpdateRequest(**valid_request(card_active_status="Y")).card_active_status == "Y"

def test_status_n_valid():
    assert CardUpdateRequest(**valid_request(card_active_status="N")).card_active_status == "N"

def test_status_lowercase_y_normalised():
    assert CardUpdateRequest(**valid_request(card_active_status="y")).card_active_status == "Y"

def test_status_invalid_value_fails():
    with pytest.raises(ValidationError) as exc_info:
        CardUpdateRequest(**valid_request(card_active_status="X"))
    assert "Y or N" in str(exc_info.value)

def test_status_digit_fails():
    with pytest.raises(ValidationError) as exc_info:
        CardUpdateRequest(**valid_request(card_active_status="1"))
    assert "Y or N" in str(exc_info.value)

def test_expiry_month_valid_boundaries():
    assert CardUpdateRequest(**valid_request(expiry_month=1)).expiry_month == 1
    assert CardUpdateRequest(**valid_request(expiry_month=12)).expiry_month == 12

def test_expiry_month_zero_fails():
    with pytest.raises(ValidationError):
        CardUpdateRequest(**valid_request(expiry_month=0))

def test_expiry_month_thirteen_fails():
    with pytest.raises(ValidationError):
        CardUpdateRequest(**valid_request(expiry_month=13))

def test_expiry_year_valid_boundaries():
    assert CardUpdateRequest(**valid_request(expiry_year=1950)).expiry_year == 1950
    assert CardUpdateRequest(**valid_request(expiry_year=2099)).expiry_year == 2099

def test_expiry_year_below_1950_fails():
    with pytest.raises(ValidationError):
        CardUpdateRequest(**valid_request(expiry_year=1949))

def test_expiry_year_above_2099_fails():
    with pytest.raises(ValidationError):
        CardUpdateRequest(**valid_request(expiry_year=2100))
