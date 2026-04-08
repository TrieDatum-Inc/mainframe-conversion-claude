"""
Async PostgreSQL database session management.
Replaces CICS file service (EXEC CICS READ/WRITE/REWRITE/DELETE) connection layer.

All VSAM file operations map to SQLAlchemy async sessions:
  EXEC CICS READ   FILE(x) → session.get() / session.execute(select(...))
  EXEC CICS WRITE  FILE(x) → session.add() + session.commit()
  EXEC CICS REWRITE FILE(x)→ session.merge() + session.commit()
  EXEC CICS DELETE FILE(x) → session.delete() + session.commit()
  EXEC CICS STARTBR/READNEXT → session.execute(select(...).order_by(...).where(...).limit(...))
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an async database session.
    Analogous to CICS implicit task storage — each request gets its own session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
