"""Unit tests for UserService — business logic layer.

Tests every business rule from COUSR01C-03C and COUSR00C specs:
  - Pagination (COUSR00C browse/page logic)
  - Create with duplicate key (COUSR01C DUPKEY guard)
  - Update with change-detection (COUSR02C "Please modify" guard)
  - Delete confirmation flow (COUSR03C two-phase delete)
  - 404 handling for missing users (VSAM NOTFND)
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


async def _seed_user(
    db: AsyncSession,
    user_id: str = "TEST0001",
    first_name: str = "John",
    last_name: str = "Smith",
    user_type: str = "U",
) -> User:
    import bcrypt

    u = User(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        password_hash=bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode(),
        user_type=user_type,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


class TestListUsers:
    """COUSR00C: paginated browse."""

    async def test_empty_list_returns_zero_total(self, db_session: AsyncSession):
        svc = UserService(db_session)
        result = await svc.list_users()
        assert result.total == 0
        assert result.users == []
        assert result.page == 1
        assert result.total_pages == 1  # min 1 page even when empty

    async def test_returns_seeded_user(self, db_session: AsyncSession):
        await _seed_user(db_session, "BROWSEU1")
        svc = UserService(db_session)
        result = await svc.list_users()
        assert result.total == 1
        assert result.users[0].user_id == "BROWSEU1"

    async def test_pagination_page_size(self, db_session: AsyncSession):
        for i in range(5):
            await _seed_user(db_session, f"PG{i:06d}")
        svc = UserService(db_session)
        page1 = await svc.list_users(page=1, page_size=3)
        assert len(page1.users) == 3
        assert page1.total == 5
        assert page1.total_pages == 2

        page2 = await svc.list_users(page=2, page_size=3)
        assert len(page2.users) == 2

    async def test_filter_by_user_id_prefix(self, db_session: AsyncSession):
        await _seed_user(db_session, "ALPHA001")
        await _seed_user(db_session, "ALPHA002")
        await _seed_user(db_session, "BETA0001")
        svc = UserService(db_session)
        result = await svc.list_users(user_id_filter="ALPHA")
        assert result.total == 2
        ids = {u.user_id for u in result.users}
        assert ids == {"ALPHA001", "ALPHA002"}

    async def test_no_password_in_response(self, db_session: AsyncSession):
        await _seed_user(db_session, "NOPWDU1")
        svc = UserService(db_session)
        result = await svc.list_users()
        user_dicts = [u.model_dump() for u in result.users]
        for d in user_dicts:
            assert "password" not in d
            assert "password_hash" not in d


class TestGetUser:
    """COUSR02C Phase 1 — fetch single user."""

    async def test_returns_user(self, db_session: AsyncSession):
        await _seed_user(db_session, "GETU0001")
        svc = UserService(db_session)
        user = await svc.get_user("GETU0001")
        assert user.user_id == "GETU0001"
        assert user.first_name == "John"

    async def test_not_found_raises_404(self, db_session: AsyncSession):
        svc = UserService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.get_user("NOBODY01")
        assert exc_info.value.status_code == 404

    async def test_user_id_uppercased(self, db_session: AsyncSession):
        await _seed_user(db_session, "UCASE001")
        svc = UserService(db_session)
        # lowercase lookup should still find the record
        user = await svc.get_user("ucase001")
        assert user.user_id == "UCASE001"


class TestCreateUser:
    """COUSR01C — add user."""

    async def test_creates_user_successfully(self, db_session: AsyncSession):
        svc = UserService(db_session)
        payload = UserCreate(
            user_id="NEWUSER1",
            first_name="Alice",
            last_name="Wonder",
            password="pass1234",
            user_type="U",
        )
        created = await svc.create_user(payload)
        assert created.user_id == "NEWUSER1"
        assert created.first_name == "Alice"
        assert created.user_type == "U"

    async def test_password_not_in_response(self, db_session: AsyncSession):
        svc = UserService(db_session)
        payload = UserCreate(
            user_id="NOPW0001",
            first_name="Bob",
            last_name="Builder",
            password="secret01",
            user_type="A",
        )
        created = await svc.create_user(payload)
        created_dict = created.model_dump()
        assert "password" not in created_dict
        assert "password_hash" not in created_dict

    async def test_duplicate_user_id_raises_409(self, db_session: AsyncSession):
        await _seed_user(db_session, "DUP00001")
        svc = UserService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.create_user(
                UserCreate(
                    user_id="DUP00001",
                    first_name="Dup",
                    last_name="User",
                    password="anypass1",
                    user_type="U",
                )
            )
        assert exc_info.value.status_code == 409

    async def test_user_id_uppercased_on_create(self, db_session: AsyncSession):
        svc = UserService(db_session)
        payload = UserCreate(
            user_id="lower001",  # lowercase input
            first_name="Case",
            last_name="Test",
            password="pass0001",
            user_type="U",
        )
        created = await svc.create_user(payload)
        assert created.user_id == "LOWER001"


class TestUpdateUser:
    """COUSR02C Phase 2 — update user with change-detection."""

    async def test_updates_first_name(self, db_session: AsyncSession):
        await _seed_user(db_session, "UPDT0001", first_name="OldName")
        svc = UserService(db_session)
        updated = await svc.update_user(
            "UPDT0001",
            UserUpdate(first_name="NewName", last_name="Smith", user_type="U"),
        )
        assert updated.first_name == "NewName"

    async def test_no_changes_raises_400(self, db_session: AsyncSession):
        """Mirrors COUSR02C 'Please modify to update' guard."""
        await _seed_user(db_session, "NOCH0001", first_name="John", last_name="Smith")
        svc = UserService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.update_user(
                "NOCH0001",
                UserUpdate(first_name="John", last_name="Smith", user_type="U"),
            )
        assert exc_info.value.status_code == 400
        assert "No changes" in exc_info.value.detail

    async def test_update_nonexistent_user_raises_404(self, db_session: AsyncSession):
        svc = UserService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.update_user(
                "GHOST001",
                UserUpdate(first_name="Ghost", last_name="User", user_type="U"),
            )
        assert exc_info.value.status_code == 404

    async def test_password_update_triggers_change(self, db_session: AsyncSession):
        await _seed_user(db_session, "PWUP0001", first_name="John", last_name="Smith")
        svc = UserService(db_session)
        # same name fields but new password — should succeed
        updated = await svc.update_user(
            "PWUP0001",
            UserUpdate(
                first_name="John",
                last_name="Smith",
                user_type="U",
                password="newpass1",
            ),
        )
        assert updated.user_id == "PWUP0001"

    async def test_omitting_password_keeps_existing(self, db_session: AsyncSession):
        """Password=None on update should NOT change the stored hash."""
        import bcrypt
        from sqlalchemy import select

        await _seed_user(db_session, "KEEPW001", first_name="Alice")
        # Grab original hash
        result = await db_session.execute(
            __import__("sqlalchemy", fromlist=["select"]).select(User).where(
                User.user_id == "KEEPW001"
            )
        )
        original_hash = result.scalar_one().password_hash

        svc = UserService(db_session)
        await svc.update_user(
            "KEEPW001",
            UserUpdate(first_name="Alicia", last_name="Smith", user_type="U"),
        )
        result2 = await db_session.execute(
            __import__("sqlalchemy", fromlist=["select"]).select(User).where(
                User.user_id == "KEEPW001"
            )
        )
        assert result2.scalar_one().password_hash == original_hash


class TestDeleteUser:
    """COUSR03C Phase 2 — delete user."""

    async def test_deletes_user_and_returns_message(self, db_session: AsyncSession):
        await _seed_user(db_session, "DELU0001")
        svc = UserService(db_session)
        response = await svc.delete_user("DELU0001")
        assert response.user_id == "DELU0001"
        assert "deleted" in response.message.lower()

    async def test_delete_nonexistent_raises_404(self, db_session: AsyncSession):
        svc = UserService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            await svc.delete_user("PHANTOM1")
        assert exc_info.value.status_code == 404

    async def test_user_gone_after_delete(self, db_session: AsyncSession):
        await _seed_user(db_session, "GONE0001")
        svc = UserService(db_session)
        await svc.delete_user("GONE0001")
        with pytest.raises(HTTPException) as exc_info:
            await svc.get_user("GONE0001")
        assert exc_info.value.status_code == 404
