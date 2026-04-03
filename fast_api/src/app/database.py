"""Database engine and session management.

Uses SQLAlchemy async engine with asyncpg for PostgreSQL.
Provides a dependency-injectable session factory for FastAPI routes.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def _make_engine(database_url: str):
    """Create async engine with connection pool settings."""
    return create_async_engine(
        database_url,
        echo=get_settings().debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


_settings = get_settings()
engine = _make_engine(_settings.database_url)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
