"""
Unit tests for UserService — business logic from COUSR00C-03C.

Tests verify all business rules:
  1. list_users — keyset pagination on user_id
  2. create_user — normalize user_id, hash password, detect duplicates
  3. update_user — read-then-rewrite, partial update
  4. delete_user — read-then-delete, not-found error
"""
import pytest

from app.models.user import User
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services.user_service import UserService
from app.utils.error_handlers import DuplicateRecordError, RecordNotFoundError


class TestUserService:
    """Tests for COUSR00C-03C business logic."""

    @pytest.mark.asyncio
    async def test_list_users_pagination(self, db, admin_user: User, regular_user: User) -> None:
        """
        COUSR00C: STARTBR/READNEXT USRSEC — returns users ordered by user_id.
        """
        service = UserService(db)
        result = await service.list_users(limit=10)

        assert result.total >= 2
        assert len(result.items) >= 2
        # Ordered by user_id ascending (VSAM KSDS key order)
        user_ids = [u.user_id for u in result.items]
        assert user_ids == sorted(user_ids)

    @pytest.mark.asyncio
    async def test_create_user_normalizes_id(self, db) -> None:
        """
        COUSR01C: user_id uppercased and padded to 8 chars (PIC X(08)).
        COSGN00C: FUNCTION UPPER-CASE applied.
        """
        service = UserService(db)
        request = UserCreateRequest(user_id="new_usr", password="Pass1234", user_type="U")
        result = await service.create_user(request)

        # Stored with uppercase and trim
        assert result.user_id == "NEW_USR"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_rejected(self, db, admin_user: User) -> None:
        """
        COUSR01C: EXEC CICS WRITE FILE(USRSEC) → RESP=14 (DUPREC) → HTTP 409.
        """
        service = UserService(db)
        request = UserCreateRequest(user_id="ADMIN", password="Admin123", user_type="A")

        with pytest.raises(DuplicateRecordError):
            await service.create_user(request)

    @pytest.mark.asyncio
    async def test_create_user_password_hashed(self, db) -> None:
        """Password stored as bcrypt hash, not plaintext."""
        service = UserService(db)
        request = UserCreateRequest(user_id="TESTUS", password="Admin123", user_type="U")
        await service.create_user(request)

        from app.repositories.user_repo import UserRepository
        repo = UserRepository(db)
        user = await repo.get_by_id("TESTUS")
        assert user.password_hash.startswith("$2b$")
        assert user.password_hash != "Admin123"

    @pytest.mark.asyncio
    async def test_update_user_partial(self, db, regular_user: User) -> None:
        """
        COUSR02C: read-then-rewrite, only provided fields updated.
        """
        service = UserService(db)
        request = UserUpdateRequest(first_name="Jane Updated")
        result = await service.update_user("USER0001", request)

        assert result.first_name == "Jane Updated"
        # last_name unchanged
        assert result.last_name == regular_user.last_name

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, db) -> None:
        """CICS RESP=13 (NOTFND) → RecordNotFoundError."""
        service = UserService(db)
        request = UserUpdateRequest(first_name="Ghost")

        with pytest.raises(RecordNotFoundError):
            await service.update_user("NOUSER", request)

    @pytest.mark.asyncio
    async def test_delete_user_success(self, db, regular_user: User) -> None:
        """
        COUSR03C: read-then-delete, returns without error.
        """
        service = UserService(db)
        await service.delete_user("USER0001")

        with pytest.raises(RecordNotFoundError):
            await service.get_user("USER0001")

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, db) -> None:
        """COUSR03C: RESP=13 (NOTFND) → RecordNotFoundError → HTTP 404."""
        service = UserService(db)
        with pytest.raises(RecordNotFoundError):
            await service.delete_user("NOUSER")

    @pytest.mark.asyncio
    async def test_user_type_admin_property(self, db, admin_user: User) -> None:
        """
        CDEMO-USRTYP-ADMIN: 88-level condition VALUE 'A' from COCOM01Y.
        User.is_admin must be True for user_type='A'.
        """
        service = UserService(db)
        result = await service.get_user("ADMIN")

        assert result.is_admin is True
        assert result.user_type == "A"

    @pytest.mark.asyncio
    async def test_regular_user_not_admin(self, db, regular_user: User) -> None:
        """Regular user (user_type='U') is_admin must be False."""
        service = UserService(db)
        result = await service.get_user("USER0001")

        assert result.is_admin is False
