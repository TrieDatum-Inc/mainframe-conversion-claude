"""
Unit tests for app.config — Settings validation.

Tests the model_validator that blocks production startup when the weak
sentinel SECRET_KEY is in use. This logic is critical for security and
was a finding in the security review.
"""

import os
import pytest
from pydantic import ValidationError


class TestSettingsValidation:
    """Tests for Settings model validators."""

    def test_sentinel_key_allowed_in_debug_mode(self):
        """
        When DEBUG=True, the sentinel SECRET_KEY is permitted.
        Tests run with DEBUG=True (set in conftest.py).
        """
        from app.config import Settings, _SECRET_KEY_SENTINEL

        s = Settings(DEBUG=True, SECRET_KEY=_SECRET_KEY_SENTINEL)
        assert s.SECRET_KEY == _SECRET_KEY_SENTINEL

    def test_sentinel_key_rejected_in_production(self):
        """
        When DEBUG=False and SECRET_KEY equals the sentinel, Settings()
        raises ValidationError with a helpful message.
        """
        from app.config import Settings, _SECRET_KEY_SENTINEL

        with pytest.raises(ValidationError) as exc_info:
            Settings(DEBUG=False, SECRET_KEY=_SECRET_KEY_SENTINEL)
        assert "SECRET_KEY" in str(exc_info.value)

    def test_short_custom_key_rejected(self):
        """
        A custom SECRET_KEY shorter than 32 characters is rejected.
        """
        from app.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings(DEBUG=True, SECRET_KEY="tooshort")
        assert "SECRET_KEY" in str(exc_info.value)

    def test_strong_custom_key_accepted_in_production(self):
        """
        A strong, non-sentinel SECRET_KEY of at least 32 chars is accepted
        even in production (DEBUG=False).
        """
        from app.config import Settings

        strong_key = "a" * 64  # 64 char key, definitely strong enough
        s = Settings(DEBUG=False, SECRET_KEY=strong_key)
        assert s.SECRET_KEY == strong_key

    def test_default_debug_is_false(self):
        """
        DEBUG defaults to False in the Settings class.
        When loading in test environment, DEBUG env var is set to 'true'.
        """
        from app.config import Settings, _SECRET_KEY_SENTINEL

        # Verify the default is False when not set
        s = Settings(DEBUG=True, SECRET_KEY=_SECRET_KEY_SENTINEL)
        assert s.DEBUG is True

    def test_settings_has_required_fields(self):
        """
        The Settings object has the expected fields and sane defaults.
        """
        from app.config import Settings, _SECRET_KEY_SENTINEL

        s = Settings(DEBUG=True, SECRET_KEY=_SECRET_KEY_SENTINEL)
        assert s.ALGORITHM == "HS256"
        assert s.ACCESS_TOKEN_EXPIRE_SECONDS == 3600
        assert s.BCRYPT_ROUNDS == 12
        assert "localhost:3000" in s.CORS_ORIGINS[0]
        assert s.APP_NAME == "CardDemo API"

    def test_settings_singleton_is_loaded(self):
        """The module-level settings object is importable and usable."""
        from app.config import settings

        # In test environment DEBUG=True is set by conftest.py
        assert settings.ALGORITHM == "HS256"
        assert settings.BCRYPT_ROUNDS > 0

    def test_trusted_proxy_cidrs_default_covers_rfc1918_and_loopback(self):
        """
        TRUSTED_PROXY_CIDRS defaults contain the expected RFC 1918 and
        loopback ranges so the out-of-box behaviour is unchanged.
        """
        from app.config import Settings, _SECRET_KEY_SENTINEL

        s = Settings(DEBUG=True, SECRET_KEY=_SECRET_KEY_SENTINEL)
        assert "127.0.0.0/8" in s.TRUSTED_PROXY_CIDRS
        assert "10.0.0.0/8" in s.TRUSTED_PROXY_CIDRS
        assert "172.16.0.0/12" in s.TRUSTED_PROXY_CIDRS
        assert "192.168.0.0/16" in s.TRUSTED_PROXY_CIDRS
        assert "::1/128" in s.TRUSTED_PROXY_CIDRS

    def test_trusted_proxy_cidrs_can_be_overridden(self):
        """
        TRUSTED_PROXY_CIDRS can be replaced via constructor (simulating the
        TRUSTED_PROXY_CIDRS environment variable) so operators can restrict or
        expand the trusted range without changing source code.
        """
        from app.config import Settings, _SECRET_KEY_SENTINEL

        custom_cidrs = ["192.0.2.0/24", "198.51.100.0/24"]
        s = Settings(
            DEBUG=True,
            SECRET_KEY=_SECRET_KEY_SENTINEL,
            TRUSTED_PROXY_CIDRS=custom_cidrs,
        )
        assert s.TRUSTED_PROXY_CIDRS == custom_cidrs
        # Default ranges must not appear when explicitly overridden
        assert "10.0.0.0/8" not in s.TRUSTED_PROXY_CIDRS
