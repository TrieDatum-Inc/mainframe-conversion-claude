"""
Unit tests for app.utils.security — JWT and password hashing utilities.

These tests cover edge cases and error branches not exercised by the higher-level
service and endpoint tests, to push coverage toward the 80% threshold required
by the SonarQube Quality Gate.
"""

import time
from datetime import timedelta

import pytest
from jose import JWTError

from app.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    is_token_revoked,
    revoke_token,
    verify_password,
)


class TestPasswordHashing:
    """Tests for hash_password() and verify_password()."""

    def test_hash_password_returns_bcrypt_string(self):
        """hash_password() returns a bcrypt hash string starting with $2b$."""
        hashed = hash_password("TestPass1!")
        assert hashed.startswith("$2b$")

    def test_hash_password_is_non_deterministic(self):
        """bcrypt generates a unique salt each call — same input, different hash."""
        h1 = hash_password("TestPass1!")
        h2 = hash_password("TestPass1!")
        assert h1 != h2

    def test_verify_password_correct(self):
        """verify_password() returns True for a matching plain/hash pair."""
        plain = "CorrectHorse99"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_wrong(self):
        """verify_password() returns False when plain text does not match hash."""
        hashed = hash_password("RealPassword1")
        assert verify_password("WrongPassword1", hashed) is False

    def test_verify_password_empty_string_against_hash(self):
        """Empty plain text never matches a real bcrypt hash."""
        hashed = hash_password("SomePassword1!")
        assert verify_password("", hashed) is False


class TestCreateAccessToken:
    """Tests for create_access_token()."""

    def test_create_token_returns_string(self):
        token = create_access_token(subject="USER001", user_type="U")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_three_part_jwt(self):
        """JWT must be three base64url segments separated by dots."""
        token = create_access_token(subject="USER001", user_type="U")
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_token_claims_present(self):
        """Issued token carries expected claims."""
        token = create_access_token(subject="ADMIN001", user_type="A")
        payload = decode_access_token(token)
        assert payload["sub"] == "ADMIN001"
        assert payload["user_type"] == "A"
        assert payload["iss"] == "carddemo-api"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_create_token_custom_expiry(self):
        """custom expires_delta is reflected in exp claim."""
        token = create_access_token(
            subject="USER001",
            user_type="U",
            expires_delta=timedelta(seconds=120),
        )
        payload = decode_access_token(token)
        remaining = payload["exp"] - time.time()
        # Should be approximately 120 seconds, with a small tolerance
        assert 100 < remaining < 130

    def test_create_token_unique_jti_each_call(self):
        """Each issued token gets a unique jti (UUID4)."""
        t1 = create_access_token(subject="U1", user_type="U")
        t2 = create_access_token(subject="U1", user_type="U")
        p1 = decode_access_token(t1)
        p2 = decode_access_token(t2)
        assert p1["jti"] != p2["jti"]

    def test_create_admin_token_user_type_claim(self):
        """user_type='A' is encoded correctly."""
        token = create_access_token(subject="ADMIN001", user_type="A")
        payload = decode_access_token(token)
        assert payload["user_type"] == "A"


class TestDecodeAccessToken:
    """Tests for decode_access_token() error handling."""

    def test_decode_valid_token(self):
        """A freshly issued token decodes without error."""
        token = create_access_token(subject="USER001", user_type="U")
        payload = decode_access_token(token)
        assert payload["sub"] == "USER001"

    def test_decode_expired_token_raises(self):
        """An already-expired token raises JWTError."""
        token = create_access_token(
            subject="USER001",
            user_type="U",
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(JWTError):
            decode_access_token(token)

    def test_decode_tampered_signature_raises(self):
        """A token with a tampered signature raises JWTError."""
        token = create_access_token(subject="USER001", user_type="U")
        # Corrupt the signature (third segment)
        header, payload_b64, sig = token.split(".")
        tampered = f"{header}.{payload_b64}.invalidsignature"
        with pytest.raises(JWTError):
            decode_access_token(tampered)

    def test_decode_completely_invalid_string_raises(self):
        """A random string raises JWTError."""
        with pytest.raises(JWTError):
            decode_access_token("not.a.jwt")

    def test_decode_missing_sub_raises(self):
        """A token with empty sub claim raises JWTError with 'Missing sub claim'."""
        from datetime import datetime, timezone
        from jose import jwt
        from app.config import settings

        payload = {
            "sub": "",
            "user_type": "U",
            "exp": datetime.now(timezone.utc) + timedelta(seconds=3600),
            "iat": datetime.now(timezone.utc),
            "iss": "carddemo-api",
            "jti": "test-jti",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(JWTError, match="Missing sub claim"):
            decode_access_token(token)

    def test_decode_invalid_user_type_raises(self):
        """A token with user_type not in ('A', 'U') raises JWTError."""
        from datetime import datetime, timezone
        from jose import jwt
        from app.config import settings

        payload = {
            "sub": "USER001",
            "user_type": "X",  # Invalid
            "exp": datetime.now(timezone.utc) + timedelta(seconds=3600),
            "iat": datetime.now(timezone.utc),
            "iss": "carddemo-api",
            "jti": "test-jti-invalid-type",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(JWTError, match="Invalid user_type claim"):
            decode_access_token(token)

    def test_decode_revoked_token_raises(self):
        """A token whose jti is in the blacklist raises JWTError."""
        token = create_access_token(subject="USER001", user_type="U")
        revoke_token(token)
        with pytest.raises(JWTError, match="Token has been revoked"):
            decode_access_token(token)


class TestRevokeToken:
    """Tests for revoke_token() and is_token_revoked()."""

    def test_revoke_token_adds_jti_to_blacklist(self):
        """Revoking a token adds its jti to the blacklist."""
        token = create_access_token(subject="USER001", user_type="U")
        # Decode to get jti before revoking
        payload = decode_access_token(token)
        jti = payload["jti"]

        assert not is_token_revoked(jti)
        revoke_token(token)
        assert is_token_revoked(jti)

    def test_revoke_already_invalid_token_does_not_raise(self):
        """revoke_token() silently ignores invalid/expired tokens."""
        # Should not raise even for a bad token
        revoke_token("not.a.valid.jwt.at.all")

    def test_is_token_revoked_returns_false_for_fresh_token(self):
        """is_token_revoked() returns False for a newly issued jti."""
        token = create_access_token(subject="USER002", user_type="U")
        payload = decode_access_token(token)
        assert not is_token_revoked(payload["jti"])

    def test_revoke_token_with_already_expired_token(self):
        """revoke_token() on an expired token does not raise."""
        token = create_access_token(
            subject="USER001",
            user_type="U",
            expires_delta=timedelta(seconds=-1),
        )
        # Should be silently ignored (JWTError caught internally)
        revoke_token(token)


class TestBlacklistBackendWarning:
    """Test the module-level RuntimeWarning for in-memory blacklist in non-debug mode."""

    def test_memory_blacklist_warns_when_debug_false(self):
        """security.py emits RuntimeWarning when BLACKLIST_BACKEND=memory and DEBUG!=true."""
        import importlib
        import os
        import sys
        import warnings

        # Remove the already-loaded module so we can reload it with different env
        mod_name = "app.utils.security"
        original_mod = sys.modules.pop(mod_name, None)
        original_debug = os.environ.get("DEBUG")
        original_backend = os.environ.get("BLACKLIST_BACKEND")

        try:
            os.environ["DEBUG"] = "false"
            os.environ["BLACKLIST_BACKEND"] = "memory"

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                importlib.import_module(mod_name)

            runtime_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
            assert len(runtime_warnings) == 1
            assert "in-memory" in str(runtime_warnings[0].message).lower()
        finally:
            # Restore environment and module registry
            if original_debug is None:
                os.environ.pop("DEBUG", None)
            else:
                os.environ["DEBUG"] = original_debug
            if original_backend is None:
                os.environ.pop("BLACKLIST_BACKEND", None)
            else:
                os.environ["BLACKLIST_BACKEND"] = original_backend
            # Restore original module to avoid polluting other tests
            sys.modules.pop(mod_name, None)
            if original_mod is not None:
                sys.modules[mod_name] = original_mod
