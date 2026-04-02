"""
Tests for auth_service.py — maps COSGN00C business rules.

Business rules tested:
  BR-SGN-001: User ID and password are mandatory (Pydantic validation)
  BR-SGN-002: User ID converted to upper-case
  BR-SGN-003: Password comparison (bcrypt)
  BR-SGN-004: User type 'A' vs 'U' in token
  BR-SGN-005: Wrong password error message
  BR-SGN-006: Not-found error message
"""

import pytest
from jose import jwt

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.domain.services.auth_service import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.schemas.auth_schemas import LoginRequest


class TestHashAndVerifyPassword:
    """Tests for bcrypt password hashing (replaces USRSEC plain-text comparison)."""

    def test_hash_produces_different_string(self):
        plain = "TestPass1"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_hash_is_bcrypt_format(self):
        hashed = hash_password("TestPass1")
        assert hashed.startswith("$2")  # bcrypt prefix

    def test_verify_correct_password(self):
        plain = "TestPass1"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("CorrectPass")
        assert verify_password("WrongPass", hashed) is False

    def test_verify_empty_password_fails(self):
        hashed = hash_password("AnyPass1")
        assert verify_password("", hashed) is False

    def test_hash_is_nondeterministic(self):
        """bcrypt uses salt — same input produces different hashes each call."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2

    def test_max_length_password(self):
        """Original COSGN00C SEC-USR-PWD PIC X(8) — 8 chars max."""
        plain = "12345678"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True


class TestCreateAndDecodeToken:
    """Tests for JWT token creation/decoding."""

    def test_create_and_decode_round_trip(self):
        data = {"sub": "TESTUSER", "user_type": "U"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded["sub"] == "TESTUSER"
        assert decoded["user_type"] == "U"

    def test_token_contains_pgm_context(self):
        """BR-SGN-005: CDEMO-PGM-CONTEXT=0 on login."""
        data = {"sub": "SYSADM00", "user_type": "A", "pgm_context": 0}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        assert decoded["pgm_context"] == 0

    def test_invalid_token_raises_authentication_error(self):
        with pytest.raises(AuthenticationError):
            decode_access_token("not.a.valid.token")

    def test_tampered_token_raises_authentication_error(self):
        data = {"sub": "SYSADM00", "user_type": "A"}
        token = create_access_token(data)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(AuthenticationError):
            decode_access_token(tampered)

    def test_token_encodes_user_type_admin(self):
        data = {"sub": "ADMIN", "user_type": "A"}
        token = create_access_token(data)
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert decoded["user_type"] == "A"

    def test_token_has_exp_field(self):
        data = {"sub": "USER", "user_type": "U"}
        token = create_access_token(data)
        decoded = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert "exp" in decoded


class TestAuthenticateUser:
    """Tests for authenticate_user — maps COSGN00C READ-USER-SEC-FILE."""

    @pytest.mark.asyncio
    async def test_successful_admin_login(self, seeded_db):
        """Happy path: admin user with correct password."""
        req = LoginRequest(user_id="SYSADM00", password="Admin123")
        result = await authenticate_user(req, seeded_db)
        assert result.user_id == "SYSADM00"
        assert result.user_type == "A"
        assert result.access_token is not None
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_successful_regular_user_login(self, seeded_db):
        """Happy path: regular user."""
        req = LoginRequest(user_id="USER0001", password="Pass1234")
        result = await authenticate_user(req, seeded_db)
        assert result.user_id == "USER0001"
        assert result.user_type == "U"

    @pytest.mark.asyncio
    async def test_user_not_found_error(self, seeded_db):
        """BR-SGN-006: RESP=NOTFND -> 'User not found. Try again ...'"""
        req = LoginRequest(user_id="NOBODY00", password="Pass1234")
        with pytest.raises(AuthenticationError) as exc_info:
            await authenticate_user(req, seeded_db)
        assert "not found" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_wrong_password_error(self, seeded_db):
        """BR-SGN-003: Wrong password -> 'Wrong Password. Try again ...'"""
        req = LoginRequest(user_id="USER0001", password="WrongPwd")
        with pytest.raises(AuthenticationError) as exc_info:
            await authenticate_user(req, seeded_db)
        assert "wrong password" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_user_id_case_insensitive(self, seeded_db):
        """BR-SGN-002: User ID uppercased before lookup."""
        req = LoginRequest(user_id="sysadm00", password="Admin123")
        result = await authenticate_user(req, seeded_db)
        assert result.user_id == "SYSADM00"

    @pytest.mark.asyncio
    async def test_token_contains_full_name(self, seeded_db):
        """Token should encode first_name and last_name for COMMAREA."""
        req = LoginRequest(user_id="USER0001", password="Pass1234")
        result = await authenticate_user(req, seeded_db)
        decoded = decode_access_token(result.access_token)
        assert decoded["first_name"] == "Alice"
        assert decoded["last_name"] == "Smith"
