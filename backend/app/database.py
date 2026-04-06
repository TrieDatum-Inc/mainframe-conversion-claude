"""
Database session management using SQLAlchemy async engine.

COBOL origin: Replaces CICS FILE CONTROL section and all EXEC CICS READ/WRITE/
REWRITE/DELETE DATASET commands. The async session provides the same transactional
guarantees that CICS task-level file enqueuing provided in the original system.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """
    Declarative base for all SQLAlchemy ORM models.

    All COBOL VSAM record layouts and DB2 table definitions
    are expressed as subclasses of this base.
    """

    pass


# Async engine — replaces CICS VSAM and DB2 connection management
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set True for SQL debug logging
    pool_pre_ping=True,  # Validates connections before use
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.

    COBOL origin: Replaces CICS HANDLE CONDITION / RESP handling pattern.
    - Session is committed on success (replaces EXEC CICS SYNCPOINT)
    - Session is rolled back on any exception (replaces CICS ABEND handling)
    - Session is always closed after the request completes

    Usage in endpoint:
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """
    Validate database connection on application startup.

    Schema is managed by Alembic migrations, not created here.
    This function only confirms the database is reachable.
    """
    async with engine.begin() as conn:
        # Simple connectivity check; schema managed by Alembic
        _ = conn
