"""Shared pytest fixtures for the CardDemo backend tests.

Uses an in-process SQLite (async) database so tests run without a real
PostgreSQL server while still exercising the full ORM and service layer.
"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import TransactionType, TransactionTypeCategory  # noqa: F401 — ensure tables registered

# ---------------------------------------------------------------------------
# Event loop — module-scoped so fixtures share the same loop
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


# ---------------------------------------------------------------------------
# In-process SQLite engine (async)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh async session per test function."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(scope="function")
async def client(engine) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX async client wired to the FastAPI app with test DB."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Admin JWT token for protected endpoint tests
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_token() -> str:
    """Generate a valid admin JWT (user_type='A') for use in Authorization headers."""
    from app.utils.security import create_access_token
    return create_access_token({"sub": "testadmin", "user_type": "A"})


@pytest.fixture
def user_token() -> str:
    """Generate a non-admin JWT (user_type='U') to test 403 responses."""
    from app.utils.security import create_access_token
    return create_access_token({"sub": "testuser", "user_type": "U"})


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def seeded_types(db_session: AsyncSession) -> list[TransactionType]:
    """Insert a small set of transaction types for test assertions."""
    types = [
        TransactionType(type_code="01", description="Purchase"),
        TransactionType(type_code="02", description="Payment"),
        TransactionType(type_code="03", description="Credit"),
    ]
    db_session.add_all(types)
    await db_session.commit()
    for t in types:
        await db_session.refresh(t)
    return types


@pytest_asyncio.fixture
async def seeded_categories(
    db_session: AsyncSession, seeded_types: list[TransactionType]
) -> list[TransactionTypeCategory]:
    """Insert categories for type '01' to test category endpoints."""
    cats = [
        TransactionTypeCategory(type_code="01", category_code="RETL", description="Retail"),
        TransactionTypeCategory(type_code="01", category_code="ONLN", description="Online"),
    ]
    db_session.add_all(cats)
    await db_session.commit()
    for c in cats:
        await db_session.refresh(c)
    return cats
