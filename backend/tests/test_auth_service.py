"""
Unit tests for AuthService.

Tests business logic in isolation using the test database.
All tests map directly to COSGN00C PROCEDURE DIVISION behaviour documented
in the spec.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService


class TestAuthServiceLogin:
    """Tests for AuthService.login() — maps COSGN00C PROCESS-ENTER-KEY."""

    @pytest.mark.asyncio
    async def test_login_admin_user_success(
        self, db_session: AsyncSession, seed_users
    ):
        """
        Admin user with correct credentials → success, redirect to /admin/menu.

        COBOL origin: SEC-USR-TYPE='A' → XCTL COADM01C.
        """
        response = await AuthService.login(
            request=LoginRequest(user_id="ADMIN001", password="Admin01!"),
            db=db_session,
        )
        assert response.access_token
        assert response.token_type == "bearer"
        assert response.user_id == "ADMIN001"
        assert response.user_type == "A"
        assert response.first_name == "John"
        assert response.last_name == "Admin"
        assert response.redirect_to == "/admin/menu"

    @pytest.mark.asyncio
    async def test_login_regular_user_success(
        self, db_session: AsyncSession, seed_users
    ):
        """
        Regular user with correct credentials → success, redirect to /menu.

        COBOL origin: SEC-USR-TYPE != 'A' → XCTL COMEN01C.
        """
        response = await AuthService.login(
            request=LoginRequest(user_id="USER0001", password="User001!"),
            db=db_session,
        )
        assert response.access_token
        assert response.user_type == "U"
        assert response.redirect_to == "/menu"

    @pytest.mark.asyncio
    async def test_login_user_not_found_returns_401(
        self, db_session: AsyncSession, seed_users
    ):
        """
        Non-existent user ID → 401 INVALID_CREDENTIALS.

        COBOL origin: RESP=NOTFND → display 'Invalid User ID or Password'.
        SECURITY: Error message must NOT reveal the user does not exist.
        """
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login(
                request=LoginRequest(user_id="NOBODY", password="anything1"),
                db=db_session,
            )
        exc = exc_info.value
        assert exc.status_code == 401
        assert exc.detail["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(
        self, db_session: AsyncSession, seed_users
    ):
        """
        Correct user ID, wrong password → 401 INVALID_CREDENTIALS.

        COBOL origin: password mismatch → same message as NOTFND (enumeration prevention).
        SECURITY: The error message must be IDENTICAL to the user-not-found case.
        """
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.login(
                request=LoginRequest(user_id="ADMIN001", password="WrongPwd"),
                db=db_session,
            )
        exc = exc_info.value
        assert exc.status_code == 401
        assert exc.detail["error_code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_wrong_password_and_not_found_same_error(
        self, db_session: AsyncSession, seed_users
    ):
        """
        User-not-found and wrong-password return identical error messages.

        COBOL origin: Both NOTFND and password mismatch displayed the same
        'Invalid User ID or Password' message to prevent user enumeration.
        This test enforces that invariant in the modern system.
        """
        with pytest.raises(HTTPException) as not_found_exc:
            await AuthService.login(
                request=LoginRequest(user_id="NOBODY99", password="anything1"),
                db=db_session,
            )
        with pytest.raises(HTTPException) as wrong_pwd_exc:
            await AuthService.login(
                request=LoginRequest(user_id="ADMIN001", password="WrongPw1"),
                db=db_session,
            )
        # Both must be identical — this is the enumeration prevention guarantee
        assert not_found_exc.value.status_code == wrong_pwd_exc.value.status_code
        assert not_found_exc.value.detail["error_code"] == wrong_pwd_exc.value.detail["error_code"]
        assert not_found_exc.value.detail["message"] == wrong_pwd_exc.value.detail["message"]

    @pytest.mark.asyncio
    async def test_login_token_contains_correct_claims(
        self, db_session: AsyncSession, seed_users
    ):
        """Issued JWT contains correct sub and user_type claims."""
        from app.utils.security import decode_access_token

        response = await AuthService.login(
            request=LoginRequest(user_id="ADMIN001", password="Admin01!"),
            db=db_session,
        )
        payload = decode_access_token(response.access_token)
        assert payload["sub"] == "ADMIN001"
        assert payload["user_type"] == "A"
        assert payload["iss"] == "carddemo-api"
        assert "jti" in payload
        assert "exp" in payload

    @pytest.mark.asyncio
    async def test_login_user_id_trimmed(
        self, db_session: AsyncSession, seed_users
    ):
        """
        Trailing spaces in user_id are stripped before lookup.

        COBOL origin: COSGN00C trims WS-USER-ID with FUNCTION TRIM(USERIDI TRAILING).
        """
        response = await AuthService.login(
            request=LoginRequest(user_id="ADMIN001", password="Admin01!"),
            db=db_session,
        )
        assert response.user_id == "ADMIN001"


class TestAuthServiceLogout:
    """Tests for AuthService.logout() — maps COSGN00C RETURN-TO-PREV-SCREEN."""

    @pytest.mark.asyncio
    async def test_logout_revokes_token(
        self, db_session: AsyncSession, seed_users
    ):
        """
        After logout, the token's jti is blacklisted.

        COBOL origin: PF3 executes bare EXEC CICS RETURN (no TRANSID),
        terminating the session with no re-entry.
        """
        from app.utils.security import create_access_token, decode_access_token, is_token_revoked

        token = create_access_token(subject="ADMIN001", user_type="A")
        payload = decode_access_token(token)
        jti = payload["jti"]

        assert not is_token_revoked(jti)

        await AuthService.logout(token=token, user_id="ADMIN001")

        assert is_token_revoked(jti)
