"""Unit tests for security utilities (password hashing and JWT)."""
import pytest
from jose import JWTError

from app.schemas.auth import TokenPayload
from app.utils.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Password hashing replaces COBOL plaintext SEC-USR-PWD comparison."""

    def test_hash_is_not_plaintext(self):
        """Stored hash must not equal the plaintext password."""
        hashed = hash_password("TESTPASS")
        assert hashed != "TESTPASS"
        assert len(hashed) > 20

    def test_correct_password_verifies(self):
        """Correct password should verify successfully."""
        hashed = hash_password("MYPASSWD")
        assert verify_password("MYPASSWD", hashed) is True

    def test_wrong_password_fails(self):
        """Wrong password should fail verification — maps BR-005."""
        hashed = hash_password("CORRECT1")
        assert verify_password("WRONGPWD", hashed) is False

    def test_uppercase_password_verifies(self):
        """Uppercased password should match hash of uppercase — BR-003."""
        hashed = hash_password("USER0001")
        # Simulate BR-003: input uppercased before verify
        assert verify_password("USER0001", hashed) is True

    def test_case_sensitivity(self):
        """Password hash is case-sensitive after uppercasing is applied."""
        hashed = hash_password("USER0001")
        assert verify_password("user0001", hashed) is False


class TestJWT:
    """JWT token replaces CARDDEMO-COMMAREA session state."""

    def test_create_and_decode_token(self):
        """Token created and decoded must have same payload."""
        payload = TokenPayload(
            sub="USER0001",
            user_type="U",
            first_name="John",
            last_name="Doe",
        )
        token = create_access_token(payload)
        decoded = decode_token(token)

        assert decoded.sub == "USER0001"
        assert decoded.user_type == "U"
        assert decoded.first_name == "John"

    def test_admin_user_type_preserved(self):
        """Admin user_type='A' must be preserved in token — maps CDEMO-USER-TYPE."""
        payload = TokenPayload(
            sub="ADMIN001",
            user_type="A",
            first_name="System",
            last_name="Admin",
        )
        token = create_access_token(payload)
        decoded = decode_token(token)

        assert decoded.user_type == "A"

    def test_invalid_token_raises_jwt_error(self):
        """Tampered token must raise JWTError."""
        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_token_contains_expiry(self):
        """Token must have an expiry (exp claim) — replaces CICS transaction timeout."""
        payload = TokenPayload(
            sub="USER0001",
            user_type="U",
            first_name="John",
            last_name="Doe",
        )
        token = create_access_token(payload)
        decoded = decode_token(token)
        assert decoded.exp is not None
        assert decoded.exp > 0
