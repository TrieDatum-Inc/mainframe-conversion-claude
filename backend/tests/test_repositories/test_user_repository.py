"""
Tests for UserRepository — USRSEC VSAM KSDS operations.

Maps CICS FILE CONTROL commands to SQL operations:
    READ DATASET(USRSEC)   → get_by_id()
    WRITE DATASET(USRSEC)  → create()
    REWRITE DATASET(USRSEC) → update()
    DELETE DATASET(USRSEC) → delete()
    STARTBR/READNEXT       → list_users()
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import hash_password


def build_user(user_id: str, user_type: str = "U") -> User:
    """Build a User instance for testing."""
    return User(
        user_id=user_id,
        first_name="Test",
        last_name="User",
        password_hash=hash_password("TestPass1"),
        user_type=user_type,
    )


class TestGetById:
    """Maps EXEC CICS READ DATASET(USRSEC) RIDFLD(key) RESP."""

    @pytest.mark.asyncio
    async def test_get_existing_user_returns_user(self, db_session: AsyncSession):
        """RESP=NORMAL → user returned."""
        db_session.add(build_user("USER0001"))
        await db_session.flush()

        repo = UserRepository(db_session)
        user = await repo.get_by_id("USER0001")

        assert user is not None
        assert user.user_id == "USER0001"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_returns_none(self, db_session: AsyncSession):
        """RESP=NOTFND → returns None (caller decides 404 vs 401)."""
        repo = UserRepository(db_session)
        user = await repo.get_by_id("NOBODY00")

        assert user is None

    @pytest.mark.asyncio
    async def test_get_is_case_sensitive(self, db_session: AsyncSession):
        """VSAM KSDS key lookup is case-sensitive."""
        db_session.add(build_user("ADMIN001"))
        await db_session.flush()

        repo = UserRepository(db_session)
        upper = await repo.get_by_id("ADMIN001")
        lower = await repo.get_by_id("admin001")

        assert upper is not None
        assert lower is None


class TestCreate:
    """Maps EXEC CICS WRITE DATASET(USRSEC) FROM(record) RIDFLD(key)."""

    @pytest.mark.asyncio
    async def test_create_user_persists_record(self, db_session: AsyncSession):
        """Successful write: record retrievable after create."""
        repo = UserRepository(db_session)
        user = build_user("NEWUSER1", "A")

        created = await repo.create(user)

        assert created.user_id == "NEWUSER1"
        assert created.user_type == "A"

        # Verify persisted
        fetched = await repo.get_by_id("NEWUSER1")
        assert fetched is not None

    @pytest.mark.asyncio
    async def test_create_sets_timestamps(self, db_session: AsyncSession):
        """created_at and updated_at should be set on creation."""
        repo = UserRepository(db_session)
        user = build_user("NEWUSER2")
        created = await repo.create(user)

        assert created.created_at is not None
        assert created.updated_at is not None


class TestListUsers:
    """Maps EXEC CICS STARTBR/READNEXT DATASET(USRSEC) browse pattern."""

    @pytest.mark.asyncio
    async def test_list_returns_all_users_ordered(self, db_session: AsyncSession):
        """
        STARTBR with LOW-VALUES → ORDER BY user_id ASC (full browse).
        """
        for i in range(3):
            db_session.add(build_user(f"USER000{i+1}"))
        await db_session.flush()

        repo = UserRepository(db_session)
        users, total = await repo.list_users(page=1, page_size=10)

        assert total == 3
        user_ids = [u.user_id for u in users]
        assert user_ids == sorted(user_ids)  # Ordered by user_id

    @pytest.mark.asyncio
    async def test_list_with_filter_applies_prefix_filter(self, db_session: AsyncSession):
        """
        STARTBR with USRIDINI filter → WHERE user_id >= filter ORDER BY ASC.
        """
        db_session.add(build_user("AUSER001"))
        db_session.add(build_user("BUSER001"))
        db_session.add(build_user("CUSER001"))
        await db_session.flush()

        repo = UserRepository(db_session)
        users, total = await repo.list_users(user_id_filter="B", page=1, page_size=10)

        # Only BUSER001 and CUSER001 (>= 'B')
        assert total == 2
        assert all(u.user_id >= "B" for u in users)

    @pytest.mark.asyncio
    async def test_list_pagination_returns_correct_page(self, db_session: AsyncSession):
        """Pagination: page 2 of page_size=2 from 5 records."""
        for i in range(5):
            db_session.add(build_user(f"USER{i:04d}"))
        await db_session.flush()

        repo = UserRepository(db_session)
        page1_users, total = await repo.list_users(page=1, page_size=2)
        page2_users, _ = await repo.list_users(page=2, page_size=2)

        assert total == 5
        assert len(page1_users) == 2
        assert len(page2_users) == 2
        # Page 2 should have different users than page 1
        page1_ids = {u.user_id for u in page1_users}
        page2_ids = {u.user_id for u in page2_users}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_list_empty_returns_zero_total(self, db_session: AsyncSession):
        """Empty table → empty list, total=0."""
        repo = UserRepository(db_session)
        users, total = await repo.list_users()

        assert users == []
        assert total == 0


class TestExists:
    """Tests for duplicate-key detection."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing_user(self, db_session: AsyncSession):
        """RESP=DUPKEY detection before WRITE."""
        db_session.add(build_user("EXISTUSR"))
        await db_session.flush()

        repo = UserRepository(db_session)
        assert await repo.exists("EXISTUSR") is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_new_user(self, db_session: AsyncSession):
        """No duplicate — safe to WRITE."""
        repo = UserRepository(db_session)
        assert await repo.exists("NEWUSR00") is False
