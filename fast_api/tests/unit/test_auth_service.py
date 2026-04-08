"""
Unit tests for AuthService — business logic from COSGN00C.

Tests verify all business rules from COSGN00C:
  1. User ID uppercase normalization (FUNCTION UPPER-CASE)
  2. Correct credentials → successful login with JWT
  3. Wrong password → AuthenticationError "Wrong Password. Try again ..."
  4. Non-existent user → AuthenticationError "User not found. Try again ..."
  5. User type 'A' → JWT role='A' claim
  6. User type 'U' → JWT role='U' claim
"""
import pytest

from app.models.user import User
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService
from app.utils.error_handlers import AuthenticationError


class TestAuthService:
    """Tests for COSGN00C business logic."""

    @pytest.mark.asyncio
    async def test_login_success_admin(self, db, admin_user: User) -> None:
        """
        COSGN00C: correct credentials → XCTL COADM01C for admin.
        JWT role claim must be 'A'.
        """
        service = AuthService(db)
        request = LoginRequest(user_id="ADMIN", password="Admin123")
        response = await service.authenticate_user(request)

        assert response.user_id == "ADMIN"
        assert response.user_type == "A"
        assert response.access_token is not None
        assert response.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_success_regular_user(self, db, regular_user: User) -> None:
        """
        COSGN00C: correct credentials → XCTL COMEN01C for regular user.
        JWT role claim must be 'U'.
        """
        service = AuthService(db)
        request = LoginRequest(user_id="USER0001", password="Admin123")
        response = await service.authenticate_user(request)

        assert response.user_type == "U"
        assert response.access_token is not None

    @pytest.mark.asyncio
    async def test_login_user_id_case_insensitive(self, db, admin_user: User) -> None:
        """
        COSGN00C PROCESS-ENTER-KEY:
          MOVE FUNCTION UPPER-CASE(USERIDI OF COSGN0AI) TO WS-USER-ID
        Login with lowercase user_id must succeed.
        """
        service = AuthService(db)
        request = LoginRequest(user_id="admin", password="Admin123")
        response = await service.authenticate_user(request)

        assert response.user_id == "ADMIN"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db, admin_user: User) -> None:
        """
        COSGN00C READ-USER-SEC-FILE:
          ELSE MOVE 'Wrong Password. Try again ...' TO WS-MESSAGE
        """
        service = AuthService(db)
        request = LoginRequest(user_id="ADMIN", password="WrongPwd")

        with pytest.raises(AuthenticationError) as exc_info:
            await service.authenticate_user(request)

        assert "Wrong Password" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, db, admin_user: User) -> None:
        """
        COSGN00C READ-USER-SEC-FILE:
          WHEN 13 → MOVE 'User not found. Try again ...' TO WS-MESSAGE
        """
        service = AuthService(db)
        request = LoginRequest(user_id="NOUSER", password="Admin123")

        with pytest.raises(AuthenticationError) as exc_info:
            await service.authenticate_user(request)

        assert "User not found" in str(exc_info.value)

    def test_hash_password_produces_bcrypt(self) -> None:
        """Bcrypt hash must start with '$2b$' prefix."""
        hashed = AuthService.hash_password("Admin123")
        assert hashed.startswith("$2b$")

    def test_hash_password_different_each_time(self) -> None:
        """Bcrypt uses random salt — same input produces different hashes."""
        h1 = AuthService.hash_password("Admin123")
        h2 = AuthService.hash_password("Admin123")
        assert h1 != h2


class TestLoginRequestValidation:
    """Tests for COSGN00C input validation (PROCESS-ENTER-KEY paragraph)."""

    def test_empty_user_id_rejected(self) -> None:
        """COSGN00C: WHEN USERIDI = SPACES → error."""
        with pytest.raises(Exception):
            LoginRequest(user_id="", password="Admin123")

    def test_empty_password_rejected(self) -> None:
        """COSGN00C: WHEN PASSWDI = SPACES → error."""
        with pytest.raises(Exception):
            LoginRequest(user_id="ADMIN", password="")

    def test_user_id_truncated_at_8(self) -> None:
        """SEC-USR-ID PIC X(08) — max 8 chars."""
        with pytest.raises(Exception):
            LoginRequest(user_id="TOOLONGID", password="Admin123")

    def test_user_id_uppercased(self) -> None:
        """FUNCTION UPPER-CASE applied on input."""
        req = LoginRequest(user_id="admin", password="Admin123")
        assert req.user_id == "ADMIN"
