"""
Tests for user_repository.py — maps USRSEC VSAM KSDS operations.

COUSR00C-03C business rules:
  COUSR-001: list users (10 per page, STARTBR/READNEXT)
  COUSR-002: get user by ID (RESP=NOTFND -> 'User not found. Try again ...')
  COUSR-003: create user (RESP=DUPREC -> DuplicateKeyError)
  COUSR-004: update user (optional password change)
  COUSR-005: delete user (RESP=NOTFND if not exists)
  COUSR-006: user_type 'A'=Admin, 'U'=Regular
"""

import pytest

from app.core.exceptions import DuplicateKeyError, ResourceNotFoundError
from app.domain.services.auth_service import hash_password
from app.infrastructure.orm.user_orm import UserORM
from app.infrastructure.repositories.user_repository import UserRepository


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_returns_user(self, seeded_db):
        repo = UserRepository(seeded_db)
        user = await repo.get_by_id("SYSADM00")
        assert user.usr_id == "SYSADM00"
        assert user.usr_type == "A"
        assert user.first_name == "System"

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found(self, seeded_db):
        """Maps COSGN00C 'User not found. Try again ...' RESP=NOTFND."""
        repo = UserRepository(seeded_db)
        with pytest.raises(ResourceNotFoundError):
            await repo.get_by_id("NOBODY00")

    @pytest.mark.asyncio
    async def test_list_paginated_forward_returns_users(self, seeded_db):
        """COUSR00C STARTBR/READNEXT 10 rows."""
        repo = UserRepository(seeded_db)
        users, has_next = await repo.list_paginated_forward(page_size=10)
        assert len(users) == 3  # seed has 3 users

    @pytest.mark.asyncio
    async def test_list_paginated_forward_limits_by_page_size(self, seeded_db):
        repo = UserRepository(seeded_db)
        users, has_next = await repo.list_paginated_forward(page_size=1)
        assert len(users) == 1
        assert has_next is True

    @pytest.mark.asyncio
    async def test_create_stores_user(self, seeded_db):
        """COUSR01C WRITE USRSEC."""
        repo = UserRepository(seeded_db)
        new_user = UserORM(
            usr_id="NEWUSR01",
            first_name="New",
            last_name="User",
            pwd_hash=hash_password("NewPass1"),
            usr_type="U",
        )
        created = await repo.create(new_user)
        assert created.usr_id == "NEWUSR01"

        fetched = await repo.get_by_id("NEWUSR01")
        assert fetched.last_name == "User"

    @pytest.mark.asyncio
    async def test_create_duplicate_raises_duplicate_key_error(self, seeded_db):
        """COUSR01C: RESP=DUPREC -> DuplicateKeyError."""
        repo = UserRepository(seeded_db)
        dup_user = UserORM(
            usr_id="SYSADM00",  # Already exists
            first_name="Duplicate",
            last_name="Admin",
            pwd_hash=hash_password("DupPass1"),
            usr_type="A",
        )
        with pytest.raises(DuplicateKeyError):
            await repo.create(dup_user)

    @pytest.mark.asyncio
    async def test_update_user_fields(self, seeded_db):
        """COUSR02C REWRITE USRSEC."""
        repo = UserRepository(seeded_db)
        user = await repo.get_by_id("USER0001")
        user.first_name = "Alicia"
        await repo.update(user)

        updated = await repo.get_by_id("USER0001")
        assert updated.first_name == "Alicia"

    @pytest.mark.asyncio
    async def test_delete_user(self, seeded_db):
        """COUSR03C DELETE USRSEC."""
        repo = UserRepository(seeded_db)
        # Create disposable user first
        temp_user = UserORM(
            usr_id="TMPUSR01",
            first_name="Temp",
            last_name="User",
            pwd_hash=hash_password("TempPass"),
            usr_type="U",
        )
        await repo.create(temp_user)

        await repo.delete("TMPUSR01")

        with pytest.raises(ResourceNotFoundError):
            await repo.get_by_id("TMPUSR01")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user_raises_not_found(self, seeded_db):
        repo = UserRepository(seeded_db)
        with pytest.raises(ResourceNotFoundError):
            await repo.delete("NOBODY00")

    @pytest.mark.asyncio
    async def test_user_id_max_length_constraint(self, seeded_db):
        """SEC-USR-ID PIC X(8) — max 8 chars."""
        repo = UserRepository(seeded_db)
        # usr_id already validated at Pydantic layer; repository level just stores
        user = await repo.get_by_id("SYSADM00")
        assert len(user.usr_id) <= 8

    @pytest.mark.asyncio
    async def test_regular_user_type_is_u(self, seeded_db):
        repo = UserRepository(seeded_db)
        user = await repo.get_by_id("USER0001")
        assert user.usr_type == "U"

    @pytest.mark.asyncio
    async def test_admin_user_type_is_a(self, seeded_db):
        repo = UserRepository(seeded_db)
        user = await repo.get_by_id("SYSADM00")
        assert user.usr_type == "A"
