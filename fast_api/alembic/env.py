"""
Alembic environment configuration for CardDemo FastAPI.

Uses async SQLAlchemy engine (asyncpg) with all ORM models
imported so autogenerate can detect schema changes.

Usage:
  alembic upgrade head        -- apply all migrations
  alembic downgrade -1        -- roll back one migration
  alembic revision --autogenerate -m "add column X"  -- generate new migration
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import Base and all ORM models so autogenerate picks them up
from app.infrastructure.database import Base
from app.infrastructure.orm import (  # noqa: F401 — side-effect import registers all models
    account_orm,
    authorization_orm,
    card_orm,
    customer_orm,
    transaction_orm,
    user_orm,
)

config = context.config

# Override sqlalchemy.url from DATABASE_URL environment variable if set
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # asyncpg driver required; replace psycopg2 URL if provided as plain postgres://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Generates SQL script without connecting to the database.
    Useful for generating migration SQL for DBA review.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations within a synchronous connection context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using the async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to DB)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
