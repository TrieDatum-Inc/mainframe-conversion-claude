"""
Unit tests for app/repositories/user_repository.py

Tests the data access layer in isolation using a SQLite in-memory DB.
Each method maps directly to a CICS file command from the COUSR programs.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import hash_password


@pytest.fixture
def repo() -> UserRepository:
    return UserRepository()


@pytest.fixture
async def persisted_user(db_session: AsyncSession) -> User:
    user = User(
        user_id="TESTUS01",
        first_name="Test",
        last_name="User",
        password_hash=hash_password("pass"),
        user_type="U",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestGetById:
    async def test_returns_user_when_exists(
        self, db_session: AsyncSession, repo: UserRepository, persisted_user: User
    ):
        """EXEC CICS READ DATASET(USRSEC) RESP=NORMAL → return record."""
        result = await repo.get_by_id(db_session, "TESTUS01")
        assert result is not None
        assert result.user_id == "TESTUS01"

    async def test_returns_none_when_not_found(
        self, db_session: AsyncSession, repo: UserRepository
    ):
        """EXEC CICS READ DATASET(USRSEC) RESP=NOTFND → return None."""
        result = await repo.get_by_id(db_session, "NOBODY99")
        assert result is None


class TestExists:
    async def test_returns_true_when_user_exists(
        self, db_session: AsyncSession, repo: UserRepository, persisted_user: User
    ):
        """Pre-flight duplicate check for COUSR01C WRITE-USER-SEC-FILE."""
        result = await repo.exists(db_session, "TESTUS01")
        assert result is True

    async def test_returns_false_when_user_missing(
        self, db_session: AsyncSession, repo: UserRepository
    ):
        result = await repo.exists(db_session, "ABSENT99")
        assert result is False


class TestListAll:
    async def test_returns_empty_for_empty_table(
        self, db_session: AsyncSession, repo: UserRepository
    ):
        """STARTBR RESP=NOTFND → empty rows list."""
        rows, count = await repo.list_all(db_session)
        assert rows == []
        assert count == 0

    async def test_returns_all_users_ordered_by_id(
        self, db_session: AsyncSession, repo: UserRepository
    ):
        """READNEXT returns records in ascending VSAM key order."""
        for uid in ["ZZZZZ001", "AAAAA001", "MMMMM001"]:
            db_session.add(
                User(
                    user_id=uid,
                    first_name="F",
                    last_name="L",
                    password_hash="h",
                    user_type="U",
                )
            )
        await db_session.commit()

        rows, count = await repo.list_all(db_session)
        ids = [r.user_id for r in rows]
        assert ids == sorted(ids)
        assert count == 3

    async def test_pagination_limit_applied(
        self, db_session: AsyncSession, repo: UserRepository, multiple_users: list[User]
    ):
        """POPULATE-USER-DATA reads at most page_size rows."""
        rows, total = await repo.list_all(db_session, page=1, page_size=5)
        assert len(rows) == 5
        assert total == 12

    async def test_filter_applies_gte_condition(
        self, db_session: AsyncSession, repo: UserRepository, multiple_users: list[User]
    ):
        """STARTBR with RIDFLD = filter → WHERE user_id >= filter."""
        rows, _ = await repo.list_all(db_session, user_id_filter="USER0010")
        for row in rows:
            assert row.user_id >= "USER0010"


class TestCreate:
    async def test_inserts_new_user(
        self, db_session: AsyncSession, repo: UserRepository
    ):
        """EXEC CICS WRITE DATASET(USRSEC) RESP=NORMAL → record persisted."""
        user = User(
            user_id="NEWUSR01",
            first_name="New",
            last_name="Person",
            password_hash=hash_password("pass"),
            user_type="A",
        )
        created = await repo.create(db_session, user)
        assert created.user_id == "NEWUSR01"

        fetched = await repo.get_by_id(db_session, "NEWUSR01")
        assert fetched is not None


class TestUpdate:
    async def test_updates_persisted_user(
        self, db_session: AsyncSession, repo: UserRepository, persisted_user: User
    ):
        """EXEC CICS REWRITE DATASET(USRSEC) → row updated."""
        persisted_user.first_name = "Modified"
        updated = await repo.update(db_session, persisted_user)
        assert updated.first_name == "Modified"

        refetched = await repo.get_by_id(db_session, "TESTUS01")
        assert refetched is not None
        assert refetched.first_name == "Modified"


class TestDelete:
    async def test_deletes_persisted_user(
        self, db_session: AsyncSession, repo: UserRepository, persisted_user: User
    ):
        """EXEC CICS DELETE DATASET(USRSEC) → record removed."""
        await repo.delete(db_session, persisted_user)
        await db_session.commit()

        refetched = await repo.get_by_id(db_session, "TESTUS01")
        assert refetched is None
