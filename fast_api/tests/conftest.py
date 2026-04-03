"""Shared test fixtures for unit and integration tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserInfo
from app.utils.security import hash_password

# ============================================================
# Test user fixtures (mirrors seed data users)
# ============================================================

@pytest.fixture
def admin_user() -> User:
    """Admin user fixture — user_type='A'."""
    return User(
        user_id="ADMIN001",
        first_name="System",
        last_name="Administrator",
        password=hash_password("ADMIN001"),
        user_type="A",
    )


@pytest.fixture
def regular_user() -> User:
    """Regular user fixture — user_type='U'."""
    return User(
        user_id="USER0001",
        first_name="John",
        last_name="Doe",
        password=hash_password("USER0001"),
        user_type="U",
    )


@pytest.fixture
def admin_user_info() -> UserInfo:
    """Admin UserInfo fixture."""
    return UserInfo(
        user_id="ADMIN001",
        first_name="System",
        last_name="Administrator",
        user_type="A",
    )


@pytest.fixture
def regular_user_info() -> UserInfo:
    """Regular UserInfo fixture."""
    return UserInfo(
        user_id="USER0001",
        first_name="John",
        last_name="Doe",
        user_type="U",
    )


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    """Mock UserRepository for unit tests (no DB required)."""
    repo = AsyncMock(spec=UserRepository)
    return repo
