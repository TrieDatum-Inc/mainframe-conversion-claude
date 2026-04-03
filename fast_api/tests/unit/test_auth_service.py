"""Unit tests for AuthService — maps COSGN00C business rules.

Each test corresponds to a specific Business Rule (BR-xxx) from the spec.
"""
import pytest
from unittest.mock import AsyncMock

from app.models.user import User
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthenticationError, AuthService
from app.utils.security import hash_password


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def admin_user() -> User:
    return User(
        user_id="ADMIN001",
        first_name="System",
        last_name="Administrator",
        password=hash_password("ADMIN001"),
        user_type="A",
    )


@pytest.fixture
def regular_user() -> User:
    return User(
        user_id="USER0001",
        first_name="John",
        last_name="Doe",
        password=hash_password("USER0001"),
        user_type="U",
    )


@pytest.fixture
def mock_repo():
    return AsyncMock()


# ============================================================
# BR-003: User ID and Password are uppercased before authentication
# ============================================================

class TestBR003Uppercasing:
    """COSGN00C BR-003: FUNCTION UPPER-CASE applied to both fields."""

    async def test_lowercase_user_id_is_uppercased(self, mock_repo, regular_user):
        """Lowercase user_id should be converted to uppercase before lookup."""
        mock_repo.get_by_id = AsyncMock(return_value=regular_user)
        service = AuthService(mock_repo)
        request = LoginRequest(user_id="user0001", password="USER0001")

        await service.authenticate(request)

        # Verify repository was called with uppercased user_id
        mock_repo.get_by_id.assert_called_once_with("USER0001")

    async def test_mixed_case_password_is_uppercased(self, mock_repo, regular_user):
        """Mixed-case password must be uppercased before verification.

        The hash stored in DB was created from the uppercase version.
        """
        # Store hash of uppercase password
        regular_user.password = hash_password("USER0001")
        mock_repo.get_by_id = AsyncMock(return_value=regular_user)
        service = AuthService(mock_repo)
        # User enters lowercase — should still work due to uppercasing
        request = LoginRequest(user_id="USER0001", password="user0001")

        result = await service.authenticate(request)
        assert result.user.user_id == "USER0001"


# ============================================================
# BR-004: User Must Exist in USRSEC File
# ============================================================

class TestBR004UserNotFound:
    """COSGN00C BR-004: RESP=13 (NOTFND) → "User not found. Try again ..." """

    async def test_nonexistent_user_raises_error(self, mock_repo):
        """Unknown user_id should raise AuthenticationError."""
        mock_repo.get_by_id = AsyncMock(return_value=None)
        service = AuthService(mock_repo)
        request = LoginRequest(user_id="UNKNOWN1", password="WHATEVER")

        with pytest.raises(AuthenticationError) as exc_info:
            await service.authenticate(request)

        assert "not found" in exc_info.value.message.lower()

    async def test_error_message_matches_cobol_text(self, mock_repo):
        """Error message must match COBOL literal exactly."""
        mock_repo.get_by_id = AsyncMock(return_value=None)
        service = AuthService(mock_repo)
        request = LoginRequest(user_id="NOUSER11", password="PASSWORD")

        with pytest.raises(AuthenticationError) as exc_info:
            await service.authenticate(request)

        assert exc_info.value.message == "User not found. Try again ..."


# ============================================================
# BR-005: Password Must Match the Stored Value
# ============================================================

class TestBR005PasswordMismatch:
    """COSGN00C BR-005: Password compare → "Wrong Password. Try again ..." """

    async def test_wrong_password_raises_error(self, mock_repo, regular_user):
        """Incorrect password should raise AuthenticationError."""
        mock_repo.get_by_id = AsyncMock(return_value=regular_user)
        service = AuthService(mock_repo)
        request = LoginRequest(user_id="USER0001", password="WRONGPWD")

        with pytest.raises(AuthenticationError) as exc_info:
            await service.authenticate(request)

        assert "Wrong Password" in exc_info.value.message

    async def test_error_message_matches_cobol_text(self, mock_repo, regular_user):
        """Error message must match COBOL literal exactly."""
        mock_repo.get_by_id = AsyncMock(return_value=regular_user)
        service = AuthService(mock_repo)
        request = LoginRequest(user_id="USER0001", password="BADPASSW")

        with pytest.raises(AuthenticationError) as exc_info:
            await service.authenticate(request)

        assert exc_info.value.message == "Wrong Password. Try again ..."


# ============================================================
# BR-006: User Type Determines Post-Login Destination
# ============================================================

class TestBR006DestinationRouting:
    """COSGN00C BR-006: type='A' → COADM01C (/admin-menu); type='U' → COMEN01C (/main-menu)."""

    async def test_admin_user_redirected_to_admin_menu(self, mock_repo, admin_user):
        """Admin user (type='A') must redirect to /admin-menu."""
        mock_repo.get_by_id = AsyncMock(return_value=admin_user)
        service = AuthService(mock_repo)
        request = LoginRequest(user_id="ADMIN001", password="ADMIN001")

        result = await service.authenticate(request)

        assert result.redirect_to == "/admin-menu"

    async def test_regular_user_redirected_to_main_menu(self, mock_repo, regular_user):
        """Regular user (type='U') must redirect to /main-menu."""
        mock_repo.get_by_id = AsyncMock(return_value=regular_user)
        service = AuthService(mock_repo)
        request = LoginRequest(user_id="USER0001", password="USER0001")

        result = await service.authenticate(request)

        assert result.redirect_to == "/main-menu"

    async def test_successful_login_returns_jwt_token(self, mock_repo, regular_user):
        """Successful login must return a non-empty JWT token."""
        mock_repo.get_by_id = AsyncMock(return_value=regular_user)
        service = AuthService(mock_repo)
        request = LoginRequest(user_id="USER0001", password="USER0001")

        result = await service.authenticate(request)

        assert result.access_token
        assert result.token_type == "bearer"

    async def test_successful_login_includes_user_info(self, mock_repo, admin_user):
        """Login response must include user info from the DB record."""
        mock_repo.get_by_id = AsyncMock(return_value=admin_user)
        service = AuthService(mock_repo)
        request = LoginRequest(user_id="ADMIN001", password="ADMIN001")

        result = await service.authenticate(request)

        assert result.user.user_id == "ADMIN001"
        assert result.user.first_name == "System"
        assert result.user.user_type == "A"


# ============================================================
# Schema validation (BR-001 and BR-002 — enforced at Pydantic level)
# ============================================================

class TestSchemaValidation:
    """BR-001/BR-002 — blank fields rejected by Pydantic before service is called."""

    def test_blank_user_id_rejected(self):
        """BR-001: Blank user_id must fail validation."""
        with pytest.raises(Exception):
            LoginRequest(user_id="   ", password="SOMEPASS")

    def test_empty_user_id_rejected(self):
        """BR-001: Empty user_id must fail validation."""
        with pytest.raises(Exception):
            LoginRequest(user_id="", password="SOMEPASS")

    def test_blank_password_rejected(self):
        """BR-002: Blank password must fail validation."""
        with pytest.raises(Exception):
            LoginRequest(user_id="USER0001", password="   ")

    def test_user_id_max_8_chars(self):
        """COBOL PIC X(08) constraint: user_id max 8 characters."""
        with pytest.raises(Exception):
            LoginRequest(user_id="TOOLONGID", password="SOMEPASS")

    def test_password_max_8_chars(self):
        """COBOL PIC X(08) constraint: password max 8 characters."""
        with pytest.raises(Exception):
            LoginRequest(user_id="USER0001", password="TOOLONGPASSWORD")

    def test_valid_request_accepted(self):
        """Valid 8-char user_id and password should be accepted."""
        req = LoginRequest(user_id="USER0001", password="PASS1234")
        assert req.user_id == "USER0001"
        assert req.password == "PASS1234"
