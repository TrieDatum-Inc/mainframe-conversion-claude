"""Unit tests for UserService business logic.

Tests mirror the COBOL paragraph logic from all four programs:
    COUSR00C — list_users (pagination, search, guards)
    COUSR01C — create_user (validations, duplicate detection)
    COUSR02C — update_user (change detection, no-change guard)
    COUSR03C — delete_user (two-phase, not-found handling)
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import (
    NoChangesDetectedError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
)
from app.utils.password import hash_password, verify_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_service(session: AsyncSession) -> UserService:
    return UserService(session)


async def insert_user(
    session: AsyncSession,
    user_id: str = "testuser",
    first_name: str = "Test",
    last_name: str = "User",
    password: str = "password1",
    user_type: str = "U",
) -> User:
    user = User(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        password=hash_password(password),
        user_type=user_type,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# COUSR00C — list_users
# ---------------------------------------------------------------------------


class TestListUsers:
    """Tests for COUSR00C PROCESS-PAGE-FORWARD / PROCESS-PAGE-BACKWARD logic."""

    @pytest.mark.asyncio
    async def test_empty_database_returns_empty_list(self, db_session):
        """COUSR00C: empty USRSEC produces empty list, no error."""
        service = make_service(db_session)
        result = await service.list_users(page=1, page_size=10)
        assert result.users == []
        assert result.total_count == 0
        assert result.has_next_page is False
        assert result.has_prev_page is False

    @pytest.mark.asyncio
    async def test_returns_page_size_records(self, db_session):
        """COUSR00C: exactly page_size records returned per page."""
        for i in range(15):
            await insert_user(db_session, user_id=f"user{i:04d}")

        service = make_service(db_session)
        result = await service.list_users(page=1, page_size=10)
        assert len(result.users) == 10
        assert result.total_count == 15

    @pytest.mark.asyncio
    async def test_next_page_flag_set_when_more_records(self, db_session):
        """COUSR00C: NEXT-PAGE-YES when lookahead READNEXT finds a record."""
        for i in range(11):
            await insert_user(db_session, user_id=f"user{i:04d}")

        service = make_service(db_session)
        result = await service.list_users(page=1, page_size=10)
        assert result.has_next_page is True

    @pytest.mark.asyncio
    async def test_next_page_flag_false_at_end(self, db_session):
        """COUSR00C: NEXT-PAGE-NO when at last page."""
        for i in range(5):
            await insert_user(db_session, user_id=f"user{i:04d}")

        service = make_service(db_session)
        result = await service.list_users(page=1, page_size=10)
        assert result.has_next_page is False

    @pytest.mark.asyncio
    async def test_prev_page_false_on_first_page(self, db_session):
        """COUSR00C: top-of-list guard — page 1 has no previous page."""
        await insert_user(db_session, user_id="user0001")
        service = make_service(db_session)
        result = await service.list_users(page=1, page_size=10)
        assert result.has_prev_page is False

    @pytest.mark.asyncio
    async def test_prev_page_true_on_subsequent_pages(self, db_session):
        """COUSR00C: page 2+ has previous page."""
        for i in range(15):
            await insert_user(db_session, user_id=f"user{i:04d}")

        service = make_service(db_session)
        result = await service.list_users(page=2, page_size=10)
        assert result.has_prev_page is True

    @pytest.mark.asyncio
    async def test_users_ordered_by_user_id(self, db_session):
        """COUSR00C: VSAM KSDS browse returns records in key (user_id) order."""
        await insert_user(db_session, user_id="zzz99999")
        await insert_user(db_session, user_id="aaa00001")
        await insert_user(db_session, user_id="mmm55555")

        service = make_service(db_session)
        result = await service.list_users(page=1, page_size=10)
        ids = [u.user_id for u in result.users]
        assert ids == sorted(ids)

    @pytest.mark.asyncio
    async def test_search_by_user_id_prefix(self, db_session):
        """COUSR00C: non-blank USRIDINI positions browse at that key."""
        await insert_user(db_session, user_id="admin001")
        await insert_user(db_session, user_id="admin002")
        await insert_user(db_session, user_id="user0001")

        service = make_service(db_session)
        result = await service.list_users(page=1, page_size=10, search_user_id="user")
        assert all(u.user_id >= "user" for u in result.users)

    @pytest.mark.asyncio
    async def test_blank_search_returns_all(self, db_session):
        """COUSR00C: blank USRIDINI → browse from LOW-VALUES (all records)."""
        await insert_user(db_session, user_id="admin001")
        await insert_user(db_session, user_id="user0001")

        service = make_service(db_session)
        result = await service.list_users(page=1, page_size=10, search_user_id="")
        assert result.total_count == 2

    @pytest.mark.asyncio
    async def test_password_not_in_list_items(self, db_session, seed_users):
        """Password must never appear in list response."""
        service = make_service(db_session)
        result = await service.list_users(page=1, page_size=10)
        for item in result.users:
            assert not hasattr(item, "password")


# ---------------------------------------------------------------------------
# COUSR01C — create_user
# ---------------------------------------------------------------------------


class TestCreateUser:
    """Tests for COUSR01C PROCESS-ENTER-KEY + WRITE-USER-SEC-FILE logic."""

    @pytest.mark.asyncio
    async def test_create_valid_admin_user(self, db_session):
        """COUSR01C: valid admin user is written to USRSEC."""
        service = make_service(db_session)
        data = UserCreate(
            first_name="Alice",
            last_name="Admin",
            user_id="newadmin",
            password="SecretPwd",
            user_type="A",
        )
        result = await service.create_user(data)
        assert result.user_id == "newadmin"
        assert result.first_name == "Alice"
        assert result.user_type == "A"

    @pytest.mark.asyncio
    async def test_create_valid_regular_user(self, db_session):
        """COUSR01C: valid regular user is written to USRSEC."""
        service = make_service(db_session)
        data = UserCreate(
            first_name="Carol",
            last_name="Smith",
            user_id="user0001",
            password="PassWord1",
            user_type="U",
        )
        result = await service.create_user(data)
        assert result.user_type == "U"

    @pytest.mark.asyncio
    async def test_password_not_in_response(self, db_session):
        """COUSR01C: password must never appear in create response."""
        service = make_service(db_session)
        data = UserCreate(
            first_name="Test",
            last_name="User",
            user_id="testuser",
            password="mypassword",
            user_type="U",
        )
        result = await service.create_user(data)
        assert not hasattr(result, "password")

    @pytest.mark.asyncio
    async def test_password_stored_as_hash(self, db_session):
        """COUSR01C: password is stored as bcrypt hash, not plaintext."""
        from app.repositories.user_repository import UserRepository

        service = make_service(db_session)
        data = UserCreate(
            first_name="Test",
            last_name="User",
            user_id="testuser",
            password="plaintext",
            user_type="U",
        )
        await service.create_user(data)

        repo = UserRepository(db_session)
        user = await repo.get_by_id("testuser")
        assert user is not None
        assert user.password != "plaintext"
        assert verify_password("plaintext", user.password)

    @pytest.mark.asyncio
    async def test_duplicate_user_id_raises_error(self, db_session):
        """COUSR01C WRITE-USER-SEC-FILE: DFHRESP(DUPKEY) → UserAlreadyExistsError."""
        await insert_user(db_session, user_id="dupusr01")
        service = make_service(db_session)
        data = UserCreate(
            first_name="Dup",
            last_name="User",
            user_id="dupusr01",
            password="password",
            user_type="U",
        )
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await service.create_user(data)
        assert exc_info.value.user_id == "dupusr01"

    @pytest.mark.asyncio
    async def test_user_type_must_be_a_or_u(self):
        """COBOL bug fix: user_type must be strictly 'A' or 'U', not any non-blank char."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserCreate(
                first_name="Test",
                last_name="User",
                user_id="testuser",
                password="password",
                user_type="X",  # Invalid — COBOL would accept this (bug)
            )

    @pytest.mark.asyncio
    async def test_first_name_cannot_be_empty(self):
        """COUSR01C validation step 1: First Name can NOT be empty."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserCreate(
                first_name="",
                last_name="User",
                user_id="testuser",
                password="password",
                user_type="U",
            )

    @pytest.mark.asyncio
    async def test_last_name_cannot_be_empty(self):
        """COUSR01C validation step 2: Last Name can NOT be empty."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserCreate(
                first_name="Test",
                last_name="",
                user_id="testuser",
                password="password",
                user_type="U",
            )

    @pytest.mark.asyncio
    async def test_user_id_cannot_be_empty(self):
        """COUSR01C validation step 3: User ID can NOT be empty."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserCreate(
                first_name="Test",
                last_name="User",
                user_id="",
                password="password",
                user_type="U",
            )

    @pytest.mark.asyncio
    async def test_user_id_max_8_chars(self):
        """COUSR01C: User ID is PIC X(08) — max 8 characters."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserCreate(
                first_name="Test",
                last_name="User",
                user_id="toolongid",  # 9 chars
                password="password",
                user_type="U",
            )


# ---------------------------------------------------------------------------
# COUSR02C — update_user
# ---------------------------------------------------------------------------


class TestUpdateUser:
    """Tests for COUSR02C UPDATE-USER-INFO + UPDATE-USER-SEC-FILE logic."""

    @pytest.mark.asyncio
    async def test_update_first_name(self, db_session):
        """COUSR02C: changing first name triggers REWRITE."""
        user = await insert_user(db_session, user_id="updusr01", first_name="Old")
        service = make_service(db_session)
        data = UserUpdate(
            first_name="New",
            last_name=user.last_name,
            password="password1",
            user_type=user.user_type,
        )
        result = await service.update_user("updusr01", data)
        assert result.first_name == "New"

    @pytest.mark.asyncio
    async def test_update_user_type(self, db_session):
        """COUSR02C: changing user_type from U to A triggers REWRITE."""
        await insert_user(db_session, user_id="updusr02", user_type="U")
        service = make_service(db_session)
        data = UserUpdate(
            first_name="Test",
            last_name="User",
            password="password1",
            user_type="A",
        )
        result = await service.update_user("updusr02", data)
        assert result.user_type == "A"

    @pytest.mark.asyncio
    async def test_no_changes_raises_error(self, db_session):
        """COUSR02C: no-change detected → NoChangesDetectedError ('Please modify to update')."""
        await insert_user(
            db_session,
            user_id="nochg001",
            first_name="Alice",
            last_name="User",
            password="password1",
            user_type="U",
        )
        service = make_service(db_session)
        # Submit identical values — should trigger no-change guard
        data = UserUpdate(
            first_name="Alice",
            last_name="User",
            password="password1",  # same plaintext → same hash check
            user_type="U",
        )
        with pytest.raises(NoChangesDetectedError):
            await service.update_user("nochg001", data)

    @pytest.mark.asyncio
    async def test_user_not_found_raises_error(self, db_session):
        """COUSR02C READ-USER-SEC-FILE: DFHRESP(NOTFND) → UserNotFoundError."""
        service = make_service(db_session)
        data = UserUpdate(
            first_name="Test",
            last_name="User",
            password="password",
            user_type="U",
        )
        with pytest.raises(UserNotFoundError):
            await service.update_user("notexist", data)

    @pytest.mark.asyncio
    async def test_user_id_is_not_updatable(self, db_session):
        """COUSR02C: user_id is VSAM key and not in REWRITE fields."""
        await insert_user(db_session, user_id="updusr03")
        service = make_service(db_session)
        data = UserUpdate(
            first_name="New Name",
            last_name="User",
            password="password1",
            user_type="U",
        )
        result = await service.update_user("updusr03", data)
        # user_id must remain unchanged
        assert result.user_id == "updusr03"

    @pytest.mark.asyncio
    async def test_password_changed_when_different(self, db_session):
        """COUSR02C: password change detected and new hash stored."""
        from app.repositories.user_repository import UserRepository

        await insert_user(db_session, user_id="pwdchg01", password="oldpasswd")
        service = make_service(db_session)
        data = UserUpdate(
            first_name="Test",
            last_name="User",
            password="newpasswd",
            user_type="U",
        )
        await service.update_user("pwdchg01", data)

        repo = UserRepository(db_session)
        user = await repo.get_by_id("pwdchg01")
        assert verify_password("newpasswd", user.password)

    @pytest.mark.asyncio
    async def test_invalid_user_type_rejected(self):
        """COBOL bug fix: user_type validation enforced on update too."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserUpdate(
                first_name="Test",
                last_name="User",
                password="password",
                user_type="B",
            )


# ---------------------------------------------------------------------------
# COUSR03C — delete_user
# ---------------------------------------------------------------------------


class TestDeleteUser:
    """Tests for COUSR03C DELETE-USER-INFO + DELETE-USER-SEC-FILE logic."""

    @pytest.mark.asyncio
    async def test_delete_existing_user(self, db_session):
        """COUSR03C: user is permanently removed after PF5 confirmation."""
        from app.repositories.user_repository import UserRepository

        await insert_user(db_session, user_id="delusr01")
        service = make_service(db_session)
        await service.delete_user("delusr01")

        repo = UserRepository(db_session)
        assert not await repo.exists("delusr01")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_raises_error(self, db_session):
        """COUSR03C DELETE-USER-SEC-FILE: DFHRESP(NOTFND) → UserNotFoundError."""
        service = make_service(db_session)
        with pytest.raises(UserNotFoundError) as exc_info:
            await service.delete_user("notexist")
        assert exc_info.value.user_id == "notexist"

    @pytest.mark.asyncio
    async def test_confirm_delete_returns_user_data(self, db_session):
        """COUSR03C PROCESS-ENTER-KEY: fetch user for read-only confirmation display."""
        await insert_user(
            db_session,
            user_id="delprev1",
            first_name="Preview",
            last_name="User",
        )
        service = make_service(db_session)
        result = await service.confirm_delete_user("delprev1")
        assert result.user_id == "delprev1"
        assert result.first_name == "Preview"
        assert not hasattr(result, "password")

    @pytest.mark.asyncio
    async def test_confirm_delete_not_found(self, db_session):
        """COUSR03C PROCESS-ENTER-KEY: NOTFND on confirm fetch too."""
        service = make_service(db_session)
        with pytest.raises(UserNotFoundError):
            await service.confirm_delete_user("doesnotexist")

    @pytest.mark.asyncio
    async def test_delete_does_not_delete_other_users(self, db_session):
        """COUSR03C: only the targeted user is deleted."""
        from app.repositories.user_repository import UserRepository

        await insert_user(db_session, user_id="delusr02")
        await insert_user(db_session, user_id="keepusr1")

        service = make_service(db_session)
        await service.delete_user("delusr02")

        repo = UserRepository(db_session)
        assert not await repo.exists("delusr02")
        assert await repo.exists("keepusr1")


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------


class TestPasswordUtils:
    """Tests for bcrypt hashing (replacing COBOL plaintext PIC X(08))."""

    def test_hash_and_verify_round_trip(self):
        """Password can be verified against its own hash."""
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed)

    def test_wrong_password_fails_verification(self):
        """Wrong plaintext does not match hash."""
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_is_not_plaintext(self):
        """Hash must not equal the plaintext (COBOL bug — stored plaintext)."""
        plaintext = "secret01"
        hashed = hash_password(plaintext)
        assert hashed != plaintext

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt salt produces different hashes each time."""
        h1 = hash_password("samepass")
        h2 = hash_password("samepass")
        assert h1 != h2
