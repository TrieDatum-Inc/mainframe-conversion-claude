"""Pytest configuration and shared fixtures for User Administration tests.

Uses SQLite in-memory database via aiosqlite for fast, isolated tests.
Each test gets a fresh database — no shared state between tests.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.utils.password import hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Create a fresh SQLite in-memory engine for each test."""
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Provide an async session tied to the test engine."""
    TestSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine):
    """HTTP test client with the test database injected."""
    TestSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Admin auth headers — X-User-Type: A (as required by require_admin dependency)
ADMIN_HEADERS = {"X-User-Type": "A"}


@pytest_asyncio.fixture
async def seed_users(db_session: AsyncSession):
    """Insert seed users into the test database.

    Mirrors the 5 users in seed_data.sql:
    - admin001, admin002 (type 'A')
    - user0001, user0002, user0003 (type 'U')
    """
    users = [
        User(
            user_id="admin001",
            first_name="Alice",
            last_name="Administrator",
            password=hash_password("Admin001!"),
            user_type="A",
        ),
        User(
            user_id="admin002",
            first_name="Bob",
            last_name="Supervisor",
            password=hash_password("Admin002!"),
            user_type="A",
        ),
        User(
            user_id="user0001",
            first_name="Carol",
            last_name="Smith",
            password=hash_password("User0001!"),
            user_type="U",
        ),
        User(
            user_id="user0002",
            first_name="David",
            last_name="Johnson",
            password=hash_password("User0002!"),
            user_type="U",
        ),
        User(
            user_id="user0003",
            first_name="Eve",
            last_name="Williams",
            password=hash_password("User0003!"),
            user_type="U",
        ),
    ]
    db_session.add_all(users)
    await db_session.commit()
    return users
