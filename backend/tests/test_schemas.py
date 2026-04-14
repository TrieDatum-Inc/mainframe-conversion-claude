"""
Unit tests for Pydantic auth schemas — LoginRequest and LoginResponse.

Tests validation rules that map to COBOL BMS field constraints.
"""

import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, LoginResponse


class TestLoginRequestSchema:
    """Tests for LoginRequest field validation."""

    def test_valid_request(self):
        req = LoginRequest(user_id="ADMIN001", password="Admin01!")
        assert req.user_id == "ADMIN001"
        assert req.password == "Admin01!"

    def test_user_id_stripped_of_whitespace(self):
        """user_id_strip validator removes leading/trailing whitespace.
        Note: the input must be within max_length=8 including spaces, so
        we test with a short string that has whitespace."""
        req = LoginRequest(user_id=" U1 ", password="Password1")
        assert req.user_id == "U1"

    def test_user_id_only_whitespace_raises(self):
        """Whitespace-only user_id is rejected after stripping."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(user_id="   ", password="Password1")
        assert "empty" in str(exc_info.value).lower()

    def test_user_id_empty_raises(self):
        """Empty string user_id fails min_length=1."""
        with pytest.raises(ValidationError):
            LoginRequest(user_id="", password="Password1")

    def test_user_id_too_long_raises(self):
        """user_id longer than 8 chars fails max_length=8."""
        with pytest.raises(ValidationError):
            LoginRequest(user_id="TOOLONGID", password="Password1")

    def test_user_id_exactly_8_chars_accepted(self):
        req = LoginRequest(user_id="ADMIN001", password="Password1")
        assert len(req.user_id) == 8

    def test_password_too_short_raises(self):
        """Password shorter than 8 chars fails min_length=8."""
        with pytest.raises(ValidationError):
            LoginRequest(user_id="USER001", password="short")

    def test_password_too_long_raises(self):
        """Password longer than 72 chars fails max_length=72 (bcrypt limit)."""
        with pytest.raises(ValidationError):
            LoginRequest(user_id="USER001", password="x" * 73)

    def test_password_exactly_72_chars_accepted(self):
        req = LoginRequest(user_id="USER001", password="x" * 72)
        assert len(req.password) == 72

    def test_password_exactly_8_chars_accepted(self):
        req = LoginRequest(user_id="USER001", password="y" * 8)
        assert len(req.password) == 8


class TestLoginResponseSchema:
    """Tests for LoginResponse serialization."""

    def test_default_token_type_is_bearer(self):
        resp = LoginResponse(
            access_token="tok",
            user_id="USER001",
            user_type="U",
            first_name="Alice",
            last_name="Smith",
            redirect_to="/menu",
        )
        assert resp.token_type == "bearer"

    def test_default_expires_in(self):
        resp = LoginResponse(
            access_token="tok",
            user_id="USER001",
            user_type="U",
            first_name="Alice",
            last_name="Smith",
            redirect_to="/menu",
        )
        assert resp.expires_in == 3600

    def test_admin_user_type_accepted(self):
        resp = LoginResponse(
            access_token="tok",
            user_id="ADMIN001",
            user_type="A",
            first_name="John",
            last_name="Admin",
            redirect_to="/admin/menu",
        )
        assert resp.user_type == "A"

    def test_invalid_user_type_raises(self):
        """user_type must be Literal['A', 'U']."""
        with pytest.raises(ValidationError):
            LoginResponse(
                access_token="tok",
                user_id="USER001",
                user_type="X",  # invalid
                first_name="Alice",
                last_name="Smith",
                redirect_to="/menu",
            )

    def test_response_does_not_include_password_hash_field(self):
        """LoginResponse schema has no password_hash field — enforces security invariant."""
        resp = LoginResponse(
            access_token="tok",
            user_id="USER001",
            user_type="U",
            first_name="Alice",
            last_name="Smith",
            redirect_to="/menu",
        )
        dumped = resp.model_dump()
        assert "password_hash" not in dumped
        assert "password" not in dumped
