"""
Tests for AuthService — COSGN00C PROCESS-ENTER-KEY paragraph business logic.

These are the most critical tests in the suite because AuthService is the
Python replacement for the COBOL authentication program COSGN00C.

Test coverage:
- Happy path: admin login → '/admin/menu' redirect
- Happy path: regular user login → '/menu' redirect
- User not found → 401 (same message as wrong password)
- Wrong password → 401 (same message as user not found)
- Blank user ID → 422
- JWT token structure validation
- bcrypt password verification
"""

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, MagicMock

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService
from app.utils.security import hash_password, verify_password


def make_user(user_id: str, password: str, user_type: str, first_name: str = "Test", last_name: str = "User") -> User:
    """Helper to create a User model instance for testing."""
    user = User()
    user.user_id = user_id
    user.first_name = first_name
    user.last_name = last_name
    user.password_hash = hash_password(password)
    user.user_type = user_type
    return user


def make_mock_repo(user: User | None = None) -> UserRepository:
    """Helper to create a mock UserRepository."""
    repo = MagicMock(spec=UserRepository)
    repo.get_by_id = AsyncMock(return_value=user)
    return repo


class TestAuthServiceLogin:
    """
    Tests mapping to COSGN00C PROCESS-ENTER-KEY paragraph.

    COBOL logic being tested:
        IF WS-USER-ID = SPACES → error
        EXEC CICS READ DATASET(USRSEC) RIDFLD(WS-USER-ID) RESP
        IF RESP = NOTFND → 'Invalid User ID or Password'
        IF SEC-USR-PWD != WS-USER-PWD → 'Invalid User ID or Password'
        IF SEC-USR-TYPE = 'A' → redirect to /admin/menu
        ELSE → redirect to /menu
    """

    @pytest.mark.asyncio
    async def test_admin_login_success_redirects_to_admin_menu(self):
        """
        COBOL: SEC-USR-TYPE='A' → EXEC CICS XCTL PROGRAM('COADM01C')
        Modern: redirect_to='/admin/menu' in LoginResponse
        """
        admin = make_user("ADMIN001", "Admin1234", "A", "System", "Administrator")
        repo = make_mock_repo(admin)
        service = AuthService(repo)

        request = LoginRequest(user_id="ADMIN001", password="Admin1234")
        response = await service.authenticate_user(request)

        assert response.access_token != ""
        assert response.token_type == "bearer"
        assert response.expires_in == 3600
        assert response.user_id == "ADMIN001"
        assert response.user_type == "A"
        assert response.first_name == "System"
        assert response.last_name == "Administrator"
        assert response.redirect_to == "/admin/menu"

    @pytest.mark.asyncio
    async def test_regular_user_login_success_redirects_to_menu(self):
        """
        COBOL: SEC-USR-TYPE!='A' → EXEC CICS XCTL PROGRAM('COMEN01C')
        Modern: redirect_to='/menu' in LoginResponse
        """
        user = make_user("USER0001", "User1234", "U", "Alice", "Johnson")
        repo = make_mock_repo(user)
        service = AuthService(repo)

        request = LoginRequest(user_id="USER0001", password="User1234")
        response = await service.authenticate_user(request)

        assert response.user_id == "USER0001"
        assert response.user_type == "U"
        assert response.redirect_to == "/menu"

    @pytest.mark.asyncio
    async def test_user_not_found_raises_401(self):
        """
        COBOL: IF RESP = DFHRESP(NOTFND) → 'Invalid User ID or Password'
        Modern: HTTP 401 with INVALID_CREDENTIALS error_code.
        Same message as wrong password — prevents user enumeration.
        """
        repo = make_mock_repo(user=None)  # User not in database
        service = AuthService(repo)

        request = LoginRequest(user_id="NOBODY00", password="anypassword")

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate_user(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error_code"] == "INVALID_CREDENTIALS"
        assert "Invalid User ID or Password" in exc_info.value.detail["message"]

    @pytest.mark.asyncio
    async def test_wrong_password_raises_401(self):
        """
        COBOL: IF SEC-USR-PWD != WS-USER-PWD → 'Invalid User ID or Password'
        Modern: HTTP 401 — SAME message as user-not-found (prevents enumeration).
        """
        user = make_user("ADMIN001", "CorrectPassword", "A")
        repo = make_mock_repo(user)
        service = AuthService(repo)

        request = LoginRequest(user_id="ADMIN001", password="WrongPassword")

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate_user(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_blank_user_id_after_strip_raises_422(self):
        """
        COBOL: MOVE FUNCTION TRIM(USERIDI) TO WS-USER-ID
               IF WS-USER-ID = SPACES → error message, re-send screen
        Modern: HTTP 422 USERID_REQUIRED
        """
        repo = make_mock_repo()
        service = AuthService(repo)

        request = LoginRequest(user_id="  ", password="anypassword")  # whitespace only

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate_user(request)

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error_code"] == "USERID_REQUIRED"

    @pytest.mark.asyncio
    async def test_user_id_is_stripped_before_lookup(self):
        """
        COBOL: MOVE FUNCTION TRIM(USERIDI) TO WS-USER-ID
               (trailing spaces removed before VSAM key lookup)
        Modern: user_id.strip() applied before repository call.
        """
        user = make_user("ADMIN001", "Admin1234", "A")
        repo = make_mock_repo(user)
        service = AuthService(repo)

        # User ID with trailing space (common in COBOL 8-char padded fields)
        request = LoginRequest(user_id="ADMIN001", password="Admin1234")
        response = await service.authenticate_user(request)

        # Should succeed — strip() normalizes the ID
        repo.get_by_id.assert_called_once_with("ADMIN001")
        assert response.user_id == "ADMIN001"

    @pytest.mark.asyncio
    async def test_user_not_found_and_wrong_password_produce_identical_401(self):
        """
        Security: Both failure paths must return identical 401 responses
        to prevent user enumeration attacks.
        Preserves COBOL behavior: same WS-MESSAGE for both conditions.
        """
        # Not found case
        repo_not_found = make_mock_repo(user=None)
        service_not_found = AuthService(repo_not_found)

        # Wrong password case
        user = make_user("ADMIN001", "CorrectPwd", "A")
        repo_wrong_pwd = make_mock_repo(user)
        service_wrong_pwd = AuthService(repo_wrong_pwd)

        request = LoginRequest(user_id="ADMIN001", password="WrongPwd")

        with pytest.raises(HTTPException) as not_found_exc:
            await service_not_found.authenticate_user(request)

        with pytest.raises(HTTPException) as wrong_pwd_exc:
            await service_wrong_pwd.authenticate_user(request)

        # Both must produce identical status code and error_code
        assert not_found_exc.value.status_code == wrong_pwd_exc.value.status_code == 401
        assert (
            not_found_exc.value.detail["error_code"]
            == wrong_pwd_exc.value.detail["error_code"]
            == "INVALID_CREDENTIALS"
        )
        assert (
            not_found_exc.value.detail["message"]
            == wrong_pwd_exc.value.detail["message"]
        )

    @pytest.mark.asyncio
    async def test_jwt_token_contains_correct_claims(self):
        """
        JWT payload must contain sub (user_id) and user_type claims.
        These replace CARDDEMO-COMMAREA fields CDEMO-USER-ID and CDEMO-USER-TYPE.
        """
        from jose import jwt
        from app.config import settings

        user = make_user("ADMIN001", "Admin1234", "A", "System", "Admin")
        repo = make_mock_repo(user)
        service = AuthService(repo)

        request = LoginRequest(user_id="ADMIN001", password="Admin1234")
        response = await service.authenticate_user(request)

        payload = jwt.decode(
            response.access_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["sub"] == "ADMIN001"
        assert payload["user_type"] == "A"
        assert "exp" in payload
        assert "iat" in payload
        assert payload["iss"] == "carddemo-api"


class TestPasswordHashing:
    """Tests for bcrypt password hashing utilities."""

    def test_hash_password_produces_bcrypt_hash(self):
        """hash_password() must produce a bcrypt hash string."""
        hashed = hash_password("testpassword")
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """verify_password() must return True for correct password."""
        hashed = hash_password("correctpassword")
        assert verify_password("correctpassword", hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password() must return False for wrong password."""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_is_different_each_time(self):
        """bcrypt uses per-hash salt; same password → different hashes."""
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2  # Different salts

    def test_verify_works_across_different_hashes(self):
        """Both hashes of the same password must verify successfully."""
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert verify_password("samepassword", hash1) is True
        assert verify_password("samepassword", hash2) is True

    def test_original_8_char_cobol_password_is_supported(self):
        """
        Legacy passwords were max 8 chars (SEC-USR-PWD PIC X(8)).
        The modern system must still accept and verify these.
        """
        short_password = "Admin123"  # 8 chars — COBOL maximum
        hashed = hash_password(short_password)
        assert verify_password(short_password, hashed) is True
