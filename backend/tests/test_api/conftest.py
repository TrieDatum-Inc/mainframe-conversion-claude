"""
Test-specific conftest for API endpoint tests.

Overrides the session-scoped db_engine fixture to only create tables
that are needed for the endpoint tests and are compatible with SQLite.

Background: Several models contain PostgreSQL-specific CHECK constraints
(EXTRACT(), ~ regex operator, ::INTEGER cast) that are not supported by
SQLite, which is used for in-memory testing. This conftest patches the
metadata to only create SQLite-compatible tables for API tests.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Tables compatible with SQLite for test schema creation
SQLITE_SAFE_TABLES = {"users", "transaction_types"}

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine():
    """Create a test engine with only SQLite-compatible tables."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create a partial metadata with only the tables we need
    test_metadata = MetaData()
    for table in Base.metadata.sorted_tables:
        if table.name in SQLITE_SAFE_TABLES:
            table.to_metadata(test_metadata)

    async with engine.begin() as conn:
        await conn.run_sync(test_metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(test_metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    """Provide a fresh async session for each test, rolling back after."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
