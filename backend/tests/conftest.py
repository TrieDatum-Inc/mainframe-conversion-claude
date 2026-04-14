"""
pytest fixtures for the CardDemo backend test suite.

Uses an in-memory SQLite database (via aiosqlite) so tests run without
a real PostgreSQL instance. SQLite is structurally compatible for these
unit/integration tests; the Alembic migration is applied programmatically.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import create_app
from app.models.user import User
from app.utils.rate_limit import limiter
from app.utils.security import hash_password

# Use SQLite in-memory database for tests (no PostgreSQL required)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create all tables in the test database once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a test database session, rolling back after each test.

    Uses a nested transaction (savepoint) so that even if test code calls
    session.commit(), the outer transaction is rolled back and the database
    stays clean between tests.
    """
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        # Start a savepoint; session.commit() will release & re-create it
        nested = await conn.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def reopen_nested(session_sync, transaction):
            nonlocal nested
            if not conn.closed and not conn.invalidated and nested.is_active is False:
                nested = conn.sync_connection.begin_nested()

        yield session

        await session.close()
        await trans.rollback()


@pytest_asyncio.fixture
async def seed_users(db_session: AsyncSession) -> list[User]:
    """
    Insert test users into the database.

    Mirrors the USRSEC VSAM test records:
      - ADMIN001: Admin user (SEC-USR-TYPE='A')
      - USER0001: Regular user (SEC-USR-TYPE='U')
    """
    users = [
        User(
            user_id="ADMIN001",
            first_name="John",
            last_name="Admin",
            password_hash=hash_password("Admin01!"),
            user_type="A",
        ),
        User(
            user_id="USER0001",
            first_name="Alice",
            last_name="Smith",
            password_hash=hash_password("User001!"),
            user_type="U",
        ),
    ]
    for user in users:
        db_session.add(user)
    await db_session.commit()
    return users


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Yield an HTTPX AsyncClient wired to the FastAPI app
    with the test database session injected.
    """
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Reset rate limiter state so tests don't interfere with each other
    limiter.reset()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
