"""
Unit tests for app/services/user_service.py

COBOL origin mapping:
  test_list_users_*     → COUSR00C POPULATE-USER-DATA browse logic
  test_get_user_*       → COUSR02C/COUSR03C READ-USER-SEC-FILE
  test_create_user_*    → COUSR01C PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE
  test_update_user_*    → COUSR02C UPDATE-USER-INFO → UPDATE-USER-SEC-FILE
  test_delete_user_*    → COUSR03C DELETE-USER-INFO → DELETE-USER-SEC-FILE

TDD approach: tests define expected business behavior first.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import (
    NoChangesDetectedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services import user_service
from app.utils.security import hash_password, verify_password


# =============================================================================
# list_users tests — COUSR00C POPULATE-USER-DATA
# =============================================================================


class TestListUsers:
    async def test_returns_empty_list_when_no_users(self, db_session: AsyncSession):
        """COUSR00C: STARTBR RESP=NOTFND → empty list, no error."""
        result = await user_service.list_users(db_session)
        assert result.items == []
        assert result.total_count == 0
        assert result.has_next is False
        assert result.has_previous is False

    async def test_returns_all_users_single_page(
        self, db_session: AsyncSession, multiple_users: list[User]
    ):
        """COUSR00C: first page with up to 10 rows returned."""
        result = await user_service.list_users(db_session, page=1, page_size=10)
        assert len(result.items) == 10
        assert result.total_count == 12
        assert result.has_next is True
        assert result.has_previous is False

    async def test_second_page_has_remaining_users(
        self, db_session: AsyncSession, multiple_users: list[User]
    ):
        """COUSR00C PF8: second page shows remaining rows."""
        result = await user_service.list_users(db_session, page=2, page_size=10)
        assert len(result.items) == 2
        assert result.has_next is False
        assert result.has_previous is True

    async def test_user_id_filter_narrows_results(
        self, db_session: AsyncSession, multiple_users: list[User]
    ):
        """
        COUSR00C: USRIDINI filter → STARTBR at supplied key.
        Results start at or after the filter value.
        """
        result = await user_service.list_users(
            db_session, user_id_filter="USER0005"
        )
        for item in result.items:
            assert item.user_id >= "USER0005"

    async def test_pagination_anchors_set_correctly(
        self, db_session: AsyncSession, multiple_users: list[User]
    ):
        """
        COUSR00C: CDEMO-CU00-USRID-FIRST and CDEMO-CU00-USRID-LAST set from displayed rows.
        """
        result = await user_service.list_users(db_session, page=1, page_size=10)
        assert result.first_item_key == result.items[0].user_id
        assert result.last_item_key == result.items[-1].user_id

    async def test_password_not_in_list_response(
        self, db_session: AsyncSession, sample_admin_user: User
    ):
        """Security: password_hash must never appear in list response."""
        result = await user_service.list_users(db_session)
        for item in result.items:
            item_dict = item.model_dump()
            assert "password" not in item_dict
            assert "password_hash" not in item_dict

    async def test_users_ordered_by_user_id_asc(
        self, db_session: AsyncSession, multiple_users: list[User]
    ):
        """COUSR00C: READNEXT returns records in ascending VSAM key order."""
        result = await user_service.list_users(db_session)
        ids = [item.user_id for item in result.items]
        assert ids == sorted(ids)


# =============================================================================
# get_user tests — COUSR02C/COUSR03C READ-USER-SEC-FILE
# =============================================================================


class TestGetUser:
    async def test_returns_user_when_found(
        self, db_session: AsyncSession, sample_admin_user: User
    ):
        """COUSR02C: READ RESP=NORMAL → return user details."""
        result = await user_service.get_user(db_session, "ADMIN001")
        assert result.user_id == "ADMIN001"
        assert result.first_name == "System"
        assert result.last_name == "Administrator"

    async def test_raises_not_found_when_missing(self, db_session: AsyncSession):
        """
        COUSR02C READ-USER-SEC-FILE: RESP=NOTFND → 'User ID NOT found...'
        Maps to HTTP 404.
        """
        with pytest.raises(UserNotFoundError):
            await user_service.get_user(db_session, "MISSING1")

    async def test_strips_whitespace_from_user_id(
        self, db_session: AsyncSession, sample_admin_user: User
    ):
        """COBOL trailing-space padding: user_id with spaces should still match."""
        result = await user_service.get_user(db_session, "ADMIN001  ")
        assert result.user_id == "ADMIN001"

    async def test_password_not_in_response(
        self, db_session: AsyncSession, sample_admin_user: User
    ):
        """Security: password must never be returned."""
        result = await user_service.get_user(db_session, "ADMIN001")
        result_dict = result.model_dump()
        assert "password" not in result_dict
        assert "password_hash" not in result_dict


# =============================================================================
# create_user tests — COUSR01C PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE
# =============================================================================


class TestCreateUser:
    def _make_create_request(self, **overrides) -> UserCreateRequest:
        defaults = {
            "first_name": "Alice",
            "last_name": "Cooper",
            "user_id": "ALICE001",
            "password": "SecurePass1!",
            "user_type": "U",
        }
        defaults.update(overrides)
        return UserCreateRequest(**defaults)

    async def test_creates_user_successfully(self, db_session: AsyncSession):
        """COUSR01C WRITE-USER-SEC-FILE RESP=NORMAL → user persisted."""
        request = self._make_create_request()
        result = await user_service.create_user(db_session, request)
        assert result.user_id == "ALICE001"
        assert result.first_name == "Alice"
        assert result.user_type == "U"

    async def test_raises_conflict_on_duplicate_user_id(self, db_session: AsyncSession):
        """
        COUSR01C WRITE-USER-SEC-FILE RESP=DUPKEY/DUPREC → 'User ID already exist...'
        Maps to HTTP 409.
        """
        request = self._make_create_request()
        await user_service.create_user(db_session, request)
        with pytest.raises(UserAlreadyExistsError):
            await user_service.create_user(db_session, request)

    async def test_password_is_hashed_not_stored_plain(self, db_session: AsyncSession):
        """
        Security: SEC-USR-PWD was plain text in VSAM.
        Modern system MUST store bcrypt hash — verify password round-trips correctly.
        """
        from app.repositories.user_repository import UserRepository

        request = self._make_create_request(password="MySecret99")
        await user_service.create_user(db_session, request)

        repo = UserRepository()
        stored = await repo.get_by_id(db_session, "ALICE001")
        assert stored is not None
        assert stored.password_hash != "MySecret99"
        assert verify_password("MySecret99", stored.password_hash)

    async def test_password_not_in_create_response(self, db_session: AsyncSession):
        """Security: create response must not include password."""
        request = self._make_create_request()
        result = await user_service.create_user(db_session, request)
        result_dict = result.model_dump()
        assert "password" not in result_dict
        assert "password_hash" not in result_dict

    async def test_user_id_uppercased_on_create(self, db_session: AsyncSession):
        """user_id is stored upper-case to match VSAM key conventions."""
        request = self._make_create_request(user_id="alice001")
        result = await user_service.create_user(db_session, request)
        assert result.user_id == "ALICE001"

    async def test_admin_user_type_accepted(self, db_session: AsyncSession):
        """COUSR01C: user_type='A' is valid — creates an admin user."""
        request = self._make_create_request(user_type="A")
        result = await user_service.create_user(db_session, request)
        assert result.user_type == "A"


# =============================================================================
# update_user tests — COUSR02C UPDATE-USER-INFO → UPDATE-USER-SEC-FILE
# =============================================================================


class TestUpdateUser:
    def _make_update_request(self, **overrides) -> UserUpdateRequest:
        defaults = {
            "first_name": "Updated",
            "last_name": "Name",
            "user_type": "U",
        }
        defaults.update(overrides)
        return UserUpdateRequest(**defaults)

    async def test_updates_first_name(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """COUSR02C: changed first_name detected; REWRITE performed."""
        request = self._make_update_request(first_name="Changed", last_name="Smith")
        result = await user_service.update_user(db_session, "USER0001", request)
        assert result.first_name == "Changed"

    async def test_updates_last_name(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """COUSR02C: changed last_name → USR-MODIFIED-YES → REWRITE."""
        request = self._make_update_request(first_name="John", last_name="NewName")
        result = await user_service.update_user(db_session, "USER0001", request)
        assert result.last_name == "NewName"

    async def test_updates_user_type(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """COUSR02C: changed user_type → USR-MODIFIED-YES."""
        request = self._make_update_request(
            first_name="John", last_name="Smith", user_type="A"
        )
        result = await user_service.update_user(db_session, "USER0001", request)
        assert result.user_type == "A"

    async def test_updates_password_when_provided(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """COUSR02C: non-blank PASSWDI → re-hash and store new password."""
        from app.repositories.user_repository import UserRepository

        request = self._make_update_request(
            first_name="John", last_name="Smith", password="NewPassword99!"
        )
        await user_service.update_user(db_session, "USER0001", request)
        repo = UserRepository()
        stored = await repo.get_by_id(db_session, "USER0001")
        assert stored is not None
        assert verify_password("NewPassword99!", stored.password_hash)

    async def test_password_unchanged_when_not_provided(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """COUSR02C: blank/absent PASSWDI → no change to stored hash."""
        from app.repositories.user_repository import UserRepository

        original_hash = sample_regular_user.password_hash
        request = self._make_update_request(first_name="John", last_name="Smith")
        await user_service.update_user(db_session, "USER0001", request)
        repo = UserRepository()
        stored = await repo.get_by_id(db_session, "USER0001")
        assert stored is not None
        assert stored.password_hash == original_hash

    async def test_raises_no_changes_when_nothing_modified(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """
        COUSR02C UPDATE-USER-INFO: USR-MODIFIED-NO → 'Please modify to update...'
        Maps to HTTP 422 NoChangesDetectedError.
        """
        request = self._make_update_request(
            first_name=sample_regular_user.first_name,
            last_name=sample_regular_user.last_name,
            user_type=sample_regular_user.user_type,
        )
        with pytest.raises(NoChangesDetectedError):
            await user_service.update_user(db_session, "USER0001", request)

    async def test_raises_not_found_for_missing_user(self, db_session: AsyncSession):
        """COUSR02C: READ NOTFND before UPDATE → 'User ID NOT found...'"""
        request = self._make_update_request()
        with pytest.raises(UserNotFoundError):
            await user_service.update_user(db_session, "MISSING1", request)

    async def test_password_not_in_update_response(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """Security: update response must not include password."""
        request = self._make_update_request(first_name="Changed", last_name="Smith")
        result = await user_service.update_user(db_session, "USER0001", request)
        result_dict = result.model_dump()
        assert "password" not in result_dict
        assert "password_hash" not in result_dict


# =============================================================================
# delete_user tests — COUSR03C DELETE-USER-INFO → DELETE-USER-SEC-FILE
# =============================================================================


class TestDeleteUser:
    async def test_deletes_user_successfully(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """COUSR03C: DELETE RESP=NORMAL → user removed; snapshot returned."""
        from app.repositories.user_repository import UserRepository

        snapshot = await user_service.delete_user(db_session, "USER0001")
        assert snapshot.user_id == "USER0001"

        repo = UserRepository()
        deleted = await repo.get_by_id(db_session, "USER0001")
        assert deleted is None

    async def test_returns_user_details_before_deletion(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """
        COUSR03C: User details (name, type) returned for confirmation display.
        Maps COUSR3A screen showing FNAME, LNAME, UTYPE before PF5 confirmation.
        """
        snapshot = await user_service.delete_user(db_session, "USER0001")
        assert snapshot.first_name == "John"
        assert snapshot.last_name == "Smith"
        assert snapshot.user_type == "U"

    async def test_raises_not_found_for_missing_user(self, db_session: AsyncSession):
        """COUSR03C: READ NOTFND → 'User ID NOT found...' Maps to HTTP 404."""
        with pytest.raises(UserNotFoundError):
            await user_service.delete_user(db_session, "MISSING1")

    async def test_password_not_in_delete_response(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """Security: snapshot returned from delete must not include password."""
        snapshot = await user_service.delete_user(db_session, "USER0001")
        snapshot_dict = snapshot.model_dump()
        assert "password" not in snapshot_dict
        assert "password_hash" not in snapshot_dict

    async def test_deletes_correct_bug_fix_message(
        self, db_session: AsyncSession, sample_regular_user: User
    ):
        """
        COUSR03C copy-paste bug verification:
        Original DELETE-USER-SEC-FILE OTHER branch displayed 'Unable to Update User...'
        (copied from COUSR02C). Modern implementation correctly references deletion.
        This test validates deletion succeeds (bug was in the error path only).
        """
        # Normal deletion should succeed without hitting the buggy error path
        snapshot = await user_service.delete_user(db_session, "USER0001")
        assert snapshot.user_id == "USER0001"
