"""
Unit tests for auth_service.py and security utilities.

Tests COSGN00C login flow: credential verification, JWT creation, redirect logic.
Also covers security.py helpers: hash_password, verify_password, decode_token.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.exceptions.errors import InvalidCredentialsError
from app.services.auth_service import login
from app.utils.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# =============================================================================
# security.py — hash_password / verify_password
# =============================================================================

class TestHashAndVerifyPassword:
    def test_hash_returns_different_string(self):
        hashed = hash_password("secret")
        assert hashed != "secret"

    def test_verify_correct_password_returns_true(self):
        hashed = hash_password("MyPassword1")
        assert verify_password("MyPassword1", hashed) is True

    def test_verify_wrong_password_returns_false(self):
        hashed = hash_password("MyPassword1")
        assert verify_password("WrongPass", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses a random salt — two hashes must differ."""
        h1 = hash_password("abc")
        h2 = hash_password("abc")
        assert h1 != h2


# =============================================================================
# security.py — create_access_token / decode_token
# =============================================================================

class TestCreateAndDecodeToken:
    def test_token_is_a_non_empty_string(self):
        token = create_access_token("USER001", "U")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decoded_payload_has_correct_subject(self):
        token = create_access_token("USER001", "U")
        payload = decode_token(token)
        assert payload["sub"] == "USER001"

    def test_decoded_payload_has_correct_user_type(self):
        token = create_access_token("ADMIN01", "A")
        payload = decode_token(token)
        assert payload["user_type"] == "A"

    def test_decoded_payload_has_issuer(self):
        token = create_access_token("USER001", "U")
        payload = decode_token(token)
        assert payload["iss"] == "carddemo-api"

    def test_decoded_payload_has_jti(self):
        """Each token must carry a unique JTI claim."""
        token = create_access_token("USER001", "U")
        payload = decode_token(token)
        assert "jti" in payload

    def test_two_tokens_have_different_jti(self):
        t1 = create_access_token("USER001", "U")
        t2 = create_access_token("USER001", "U")
        p1 = decode_token(t1)
        p2 = decode_token(t2)
        assert p1["jti"] != p2["jti"]

    def test_invalid_token_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid or expired token"):
            decode_token("not.a.jwt")

    def test_tampered_token_raises_value_error(self):
        token = create_access_token("USER001", "U")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValueError):
            decode_token(tampered)


# =============================================================================
# auth_service.login — COSGN00C PROCESS-ENTER-KEY
# =============================================================================

class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success_regular_user_redirects_to_menu(self):
        db = AsyncMock()
        mock_user = MagicMock()
        mock_user.user_id = "USER0001"
        mock_user.user_type = "U"
        mock_user.first_name = "Alice"
        mock_user.last_name = "Johnson"
        mock_user.password_hash = hash_password("User1234")

        with patch("app.services.auth_service.UserRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)

            response = await login("USER0001", "User1234", db)

        assert response.access_token is not None
        assert response.user_id == "USER0001"
        assert response.user_type == "U"
        assert response.redirect_to == "/menu"

    @pytest.mark.asyncio
    async def test_login_success_admin_redirects_to_admin_menu(self):
        db = AsyncMock()
        mock_user = MagicMock()
        mock_user.user_id = "ADMIN001"
        mock_user.user_type = "A"
        mock_user.first_name = "System"
        mock_user.last_name = "Admin"
        mock_user.password_hash = hash_password("Admin1234")

        with patch("app.services.auth_service.UserRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)

            response = await login("ADMIN001", "Admin1234", db)

        assert response.redirect_to == "/admin/menu"
        assert response.user_type == "A"

    @pytest.mark.asyncio
    async def test_login_returns_bearer_token_type(self):
        db = AsyncMock()
        mock_user = MagicMock()
        mock_user.user_id = "USER0001"
        mock_user.user_type = "U"
        mock_user.first_name = "Alice"
        mock_user.last_name = "Test"
        mock_user.password_hash = hash_password("Pass1234")

        with patch("app.services.auth_service.UserRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)
            response = await login("USER0001", "Pass1234", db)

        assert response.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_strips_whitespace_from_user_id(self):
        """COSGN00C trims user_id before CICS READ."""
        db = AsyncMock()
        mock_user = MagicMock()
        mock_user.user_id = "USER0001"
        mock_user.user_type = "U"
        mock_user.first_name = "Alice"
        mock_user.last_name = "Johnson"
        mock_user.password_hash = hash_password("Pass1234")

        with patch("app.services.auth_service.UserRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)
            # Call with leading/trailing spaces
            await login("  USER0001  ", "Pass1234", db)
            # Verify .strip() was applied
            mock_repo.get_by_id.assert_called_once_with("USER0001")

    @pytest.mark.asyncio
    async def test_login_user_not_found_raises_invalid_credentials(self):
        """COSGN00C: unknown user_id → same error as wrong password (no enumeration)."""
        db = AsyncMock()

        with patch("app.services.auth_service.UserRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(InvalidCredentialsError):
                await login("NOBODY", "Pass1234", db)

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises_invalid_credentials(self):
        """COSGN00C: correct user_id but wrong password → same error."""
        db = AsyncMock()
        mock_user = MagicMock()
        mock_user.user_id = "USER0001"
        mock_user.user_type = "U"
        mock_user.password_hash = hash_password("CorrectPass")

        with patch("app.services.auth_service.UserRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)

            with pytest.raises(InvalidCredentialsError):
                await login("USER0001", "WrongPass", db)

    @pytest.mark.asyncio
    async def test_login_response_includes_expires_in(self):
        db = AsyncMock()
        mock_user = MagicMock()
        mock_user.user_id = "USER0001"
        mock_user.user_type = "U"
        mock_user.first_name = "Alice"
        mock_user.last_name = "Johnson"
        mock_user.password_hash = hash_password("Pass1234")

        with patch("app.services.auth_service.UserRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)
            response = await login("USER0001", "Pass1234", db)

        assert response.expires_in > 0
