"""Seed script — creates default CardDemo users.

Run after applying Alembic migrations:
    python seed_data.py

Default accounts (matching COBOL demo data):
  Admin : user_id=ADMIN001  password=ADMIN001  type=A
  User  : user_id=USER0001  password=USER0001  type=U

Passwords are uppercased before hashing to match COSGN00C behaviour.
"""

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.user import User
from app.utils.security import hash_password

SEED_USERS = [
    {
        "user_id": "ADMIN001",
        "first_name": "Admin",
        "last_name": "User",
        "password": "ADMIN001",
        "user_type": "A",
    },
    {
        "user_id": "USER0001",
        "first_name": "Regular",
        "last_name": "User",
        "password": "USER0001",
        "user_type": "U",
    },
    {
        "user_id": "USER0002",
        "first_name": "Jane",
        "last_name": "Smith",
        "password": "USER0002",
        "user_type": "U",
    },
    {
        "user_id": "USER0003",
        "first_name": "Bob",
        "last_name": "Johnson",
        "password": "USER0003",
        "user_type": "U",
    },
    {
        "user_id": "ADMIN002",
        "first_name": "Super",
        "last_name": "Admin",
        "password": "ADMIN002",
        "user_type": "A",
    },
]


async def seed(db: AsyncSession) -> None:
    """Insert seed users if they do not already exist."""
    created = 0
    skipped = 0

    for data in SEED_USERS:
        result = await db.execute(select(User).where(User.user_id == data["user_id"]))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  SKIP  {data['user_id']} (already exists)")
            skipped += 1
            continue

        user = User(
            user_id=data["user_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            # Uppercase password before hashing — mirrors COSGN00C MOVE FUNCTION UPPER-CASE
            password_hash=hash_password(data["password"].upper()),
            user_type=data["user_type"],
        )
        db.add(user)
        print(f"  CREATE {data['user_id']} ({data['user_type']})")
        created += 1

    await db.commit()
    print(f"\nDone: {created} created, {skipped} skipped.")


async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("Seeding CardDemo users...")
    async with session_factory() as session:
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
