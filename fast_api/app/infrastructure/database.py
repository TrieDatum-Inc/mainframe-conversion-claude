"""
Database connection and session management.
Replaces all VSAM KSDS file open/close and DB2 connect/disconnect operations.

PostgreSQL tables map to:
  accounts    <- ACCTDAT  VSAM KSDS (CVACT01Y, 300 bytes)
  customers   <- CUSTDAT  VSAM KSDS (CVCUS01Y, 500 bytes)
  cards       <- CARDDAT  VSAM KSDS (CVACT02Y, 150 bytes)
  card_xref   <- CXACAIX  VSAM AIX  (CVACT03Y, 50 bytes)
  transactions <- TRANSACT VSAM KSDS (CVTRA05Y, 350 bytes)
  users       <- USRSEC   VSAM KSDS (CSUSR01Y, 80 bytes)
  tran_cat_bal <- TRAN-CAT-BAL-FILE  (CVTRA01Y, 50 bytes)
  dis_group   <- DIS-GROUP-FILE      (CVTRA02Y, 50 bytes)
  tran_types  <- CARDDEMO.TRANSACTION_TYPE DB2
  tran_categories <- CARDDEMO.TRANSACTION_CATEGORY DB2
  auth_summary <- IMS CIPAUSMY segment
  auth_detail  <- IMS CIPAUDTY segment
  auth_fraud   <- CARDDEMO.AUTHFRDS DB2
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session.
    Replaces CICS file open/close — session is scoped to the request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables from ORM metadata (used for testing)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables (used for testing teardown)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
