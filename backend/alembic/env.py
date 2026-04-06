"""
Alembic migration environment configuration.

Uses the application's Settings to get the database URL, ensuring
migrations always target the same database as the running application.

The sync psycopg2 driver is used for migrations (Alembic does not support async).
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Alembic Config object — provides access to values within alembic.ini
config = context.config

# Setup Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Base and all models so Alembic can detect schema changes
# All models must be imported here for autogenerate to work correctly
from app.database import Base  # noqa: E402
from app.models.user import User  # noqa: E402, F401 (import registers model with Base)

target_metadata = Base.metadata

# Override sqlalchemy.url with value from application settings
# This ensures migrations use the same DB as the running application
from app.config import settings  # noqa: E402

config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (generate SQL without DB connection).
    Useful for generating SQL scripts for DBA review.
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
    """Execute pending migrations against the provided connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (matches the app's engine type)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connected to live database)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
