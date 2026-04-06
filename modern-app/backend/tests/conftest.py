"""Pytest configuration and shared fixtures for the transaction module tests."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.transaction import Transaction
from app.routers.auth import create_access_token

# In-memory SQLite for fast unit tests (structure testing only)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with overridden DB dependency."""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Valid JWT auth headers for test requests."""
    token = create_access_token(user_id="testuser", user_type="regular")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_transaction(db_session: AsyncSession) -> Transaction:
    """A single persisted transaction for read tests."""
    txn = Transaction(
        transaction_id="0000000000000001",
        type_code="01",
        category_code="0001",
        source="POS TERM",
        description="TEST GROCERY PURCHASE",
        amount=Decimal("-45.67"),
        merchant_id="123456789",
        merchant_name="TEST MARKET",
        merchant_city="NEW YORK",
        merchant_zip="10001",
        card_number="4000002000000000",
        original_timestamp=datetime(2024, 1, 5, 10, 23, 45),
        processing_timestamp=datetime(2024, 1, 5, 10, 25, 0),
    )
    db_session.add(txn)
    await db_session.commit()
    await db_session.refresh(txn)
    return txn


@pytest_asyncio.fixture
async def multiple_transactions(db_session: AsyncSession) -> list[Transaction]:
    """15 transactions for pagination tests."""
    txns = []
    for i in range(1, 16):
        txn = Transaction(
            transaction_id=str(i).zfill(16),
            type_code="01",
            category_code="0001",
            source="POS TERM",
            description=f"TRANSACTION {i}",
            amount=Decimal(f"-{i * 10}.00"),
            merchant_id="123456789",
            merchant_name="TEST MERCHANT",
            merchant_city="TESTCITY",
            merchant_zip="10001",
            card_number="4000002000000000",
            original_timestamp=datetime(2024, 1, i, 10, 0, 0),
            processing_timestamp=datetime(2024, 1, i, 10, 5, 0),
        )
        db_session.add(txn)
        txns.append(txn)
    await db_session.commit()
    return txns
