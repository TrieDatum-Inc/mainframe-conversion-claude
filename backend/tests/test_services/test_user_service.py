"""
Unit tests for user_service.py.

Tests COUSR00C (list), COUSR01C (create), COUSR02C (get/update), COUSR03C (delete).
Uses mock repositories so no database is needed.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.exceptions.errors import DuplicateResourceError, NotFoundError
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services.user_service import (
    create_user,
    delete_user,
    get_user,
    list_users,
    update_user,
)


def _make_user(
    user_id: str = "USER0001",
    first_name: str = "Alice",
    last_name: str = "Johnson",
    user_type: str = "U",
) -> MagicMock:
    """Build a mock User ORM object."""
    user = MagicMock()
    user.user_id = user_id
    user.first_name = first_name
    user.last_name = last_name
    user.user_type = user_type
    user.password_hash = "hashed"
    now = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    user.created_at = now
    user.updated_at = now
    return user


# =============================================================================
# list_users — COUSR00C POPULATE-USER-DATA
# =============================================================================

class TestListUsers:
    @pytest.mark.asyncio
    async def test_returns_paginated_response(self):
        db = AsyncMock()
        users = [_make_user("USER0001"), _make_user("USER0002")]
        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.list_paginated = AsyncMock(return_value=(users, 2))
            resp = await list_users(db, page=1, page_size=10, user_id_filter=None)

        assert resp.total_count == 2
        assert resp.page == 1
        assert resp.page_size == 10
        assert len(resp.items) == 2

    @pytest.mark.asyncio
    async def test_has_next_when_more_pages_exist(self):
        db = AsyncMock()
        users = [_make_user()]
        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.list_paginated = AsyncMock(return_value=(users, 25))
            resp = await list_users(db, page=1, page_size=10, user_id_filter=None)

        assert resp.has_next is True

    @pytest.mark.asyncio
    async def test_has_previous_when_not_first_page(self):
        db = AsyncMock()
        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.list_paginated = AsyncMock(return_value=([], 25))
            resp = await list_users(db, page=2, page_size=10, user_id_filter=None)

        assert resp.has_previous is True

    @pytest.mark.asyncio
    async def test_no_previous_on_first_page(self):
        db = AsyncMock()
        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.list_paginated = AsyncMock(return_value=([], 0))
            resp = await list_users(db, page=1, page_size=10, user_id_filter=None)

        assert resp.has_previous is False

    @pytest.mark.asyncio
    async def test_passes_filter_to_repo(self):
        db = AsyncMock()
        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.list_paginated = AsyncMock(return_value=([], 0))
            await list_users(db, page=1, page_size=10, user_id_filter="USER")
            mock_repo.list_paginated.assert_called_once_with(1, 10, "USER")


# =============================================================================
# get_user — COUSR02C READ-USER-SEC-FILE
# =============================================================================

class TestGetUser:
    @pytest.mark.asyncio
    async def test_returns_user_response_when_found(self):
        db = AsyncMock()
        mock_user = _make_user("USER0001")
        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)
            resp = await get_user("USER0001", db)

        assert resp.user_id == "USER0001"

    @pytest.mark.asyncio
    async def test_raises_not_found_when_user_missing(self):
        db = AsyncMock()
        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(NotFoundError) as exc_info:
                await get_user("NOBODY", db)

        assert "NOBODY" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_not_found_error_code_is_user_not_found(self):
        db = AsyncMock()
        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(NotFoundError) as exc_info:
                await get_user("NOBODY", db)

        assert exc_info.value.error_code == "USER_NOT_FOUND"


# =============================================================================
# create_user — COUSR01C WRITE-USER-SEC-FILE
# =============================================================================

class TestCreateUser:
    @pytest.mark.asyncio
    async def test_creates_user_and_returns_response(self):
        db = AsyncMock()
        mock_user = _make_user("NEWUSER1")

        request = UserCreateRequest(
            user_id="newuser1",
            first_name="Bob",
            last_name="Smith",
            password="Pass1234",
            user_type="U",
        )

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.create = AsyncMock(return_value=mock_user)
            resp = await create_user(request, db)

        assert resp.user_id == "NEWUSER1"

    @pytest.mark.asyncio
    async def test_user_id_uppercased_before_create(self):
        """COUSR01C stores user_id in uppercase (COBOL PIC X field convention)."""
        db = AsyncMock()
        captured_user = None

        async def _capture_create(user):
            nonlocal captured_user
            captured_user = user
            mock_created = _make_user(user.user_id)
            return mock_created

        # user_id max_length=8 per COBOL PIC X(8) constraint
        request = UserCreateRequest(
            user_id="lower123",   # 8 chars lowercase
            first_name="Bob",
            last_name="Smith",
            password="Pass1234",
            user_type="U",
        )

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.create = AsyncMock(side_effect=_capture_create)
            await create_user(request, db)

        assert captured_user.user_id == "LOWER123"

    @pytest.mark.asyncio
    async def test_password_hashed_before_create(self):
        """Password must be stored as a bcrypt hash, not plain text."""
        db = AsyncMock()
        captured_user = None

        async def _capture(user):
            nonlocal captured_user
            captured_user = user
            return _make_user()

        # password max_length=8 per COBOL PASSWDI PIC X(8) constraint
        request = UserCreateRequest(
            user_id="USER0001",
            first_name="Bob",
            last_name="Smith",
            password="PlainPas",   # 8 chars
            user_type="U",
        )

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.create = AsyncMock(side_effect=_capture)
            await create_user(request, db)

        assert captured_user.password_hash != "PlainPas"
        assert captured_user.password_hash.startswith("$2")  # bcrypt prefix

    @pytest.mark.asyncio
    async def test_duplicate_user_raises_duplicate_resource_error(self):
        from sqlalchemy.exc import IntegrityError

        db = AsyncMock()
        request = UserCreateRequest(
            user_id="EXISTING",
            first_name="Bob",
            last_name="Smith",
            password="Pass1234",
            user_type="U",
        )

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.create = AsyncMock(
                side_effect=IntegrityError("", {}, Exception("dup"))
            )

            with pytest.raises(DuplicateResourceError) as exc_info:
                await create_user(request, db)

        assert exc_info.value.error_code == "USER_ALREADY_EXISTS"


# =============================================================================
# update_user — COUSR02C UPDATE-USER-SEC-FILE
# =============================================================================

class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_updates_and_returns_user(self):
        db = AsyncMock()
        mock_user = _make_user("USER0001", first_name="Alice", last_name="Old")

        request = UserUpdateRequest(
            first_name="Alice",
            last_name="Updated",
            user_type="U",
        )

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)
            mock_repo.update = AsyncMock(return_value=mock_user)
            resp = await update_user("USER0001", request, db)

        assert resp.user_id == "USER0001"
        assert mock_user.last_name == "Updated"

    @pytest.mark.asyncio
    async def test_update_rehashes_password_when_provided(self):
        db = AsyncMock()
        mock_user = _make_user("USER0001")
        mock_user.password_hash = "old_hash"

        request = UserUpdateRequest(
            first_name="Alice",
            last_name="Johnson",
            user_type="U",
            password="NewPass1",
        )

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)
            mock_repo.update = AsyncMock(return_value=mock_user)
            await update_user("USER0001", request, db)

        assert mock_user.password_hash != "old_hash"
        assert mock_user.password_hash.startswith("$2")

    @pytest.mark.asyncio
    async def test_update_preserves_password_when_not_provided(self):
        db = AsyncMock()
        mock_user = _make_user("USER0001")
        mock_user.password_hash = "existing_hash"

        request = UserUpdateRequest(
            first_name="Alice",
            last_name="Johnson",
            user_type="U",
            password=None,
        )

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)
            mock_repo.update = AsyncMock(return_value=mock_user)
            await update_user("USER0001", request, db)

        assert mock_user.password_hash == "existing_hash"

    @pytest.mark.asyncio
    async def test_update_user_not_found_raises(self):
        db = AsyncMock()
        request = UserUpdateRequest(
            first_name="Alice", last_name="Johnson", user_type="U"
        )

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(NotFoundError):
                await update_user("NOBODY", request, db)


# =============================================================================
# delete_user — COUSR03C DELETE-USER-SEC-FILE
# =============================================================================

class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_deletes_user_successfully(self):
        db = AsyncMock()
        mock_user = _make_user("USER0001")

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=mock_user)
            mock_repo.delete = AsyncMock(return_value=None)
            # Should complete without error
            await delete_user("USER0001", db)

        mock_repo.delete.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_delete_user_not_found_raises(self):
        db = AsyncMock()

        with patch("app.services.user_service.UserRepository") as mock_cls:
            mock_repo = mock_cls.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(NotFoundError) as exc_info:
                await delete_user("NOBODY", db)

        assert "NOBODY" in str(exc_info.value)
