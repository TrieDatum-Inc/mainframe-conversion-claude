"""
Tests for ORM model methods and the database session lifecycle.

Focuses on coverage of uncovered lines in app.models.user and app.database.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestUserModel:
    """Tests for the User ORM model."""

    def test_user_repr(self):
        """User.__repr__ returns a readable string with user_id and user_type."""
        user = User(
            user_id="ADMIN001",
            first_name="John",
            last_name="Admin",
            password_hash="$2b$12$fakehashvalue",
            user_type="A",
        )
        repr_str = repr(user)
        assert "ADMIN001" in repr_str
        assert "A" in repr_str

    def test_user_repr_regular_user(self):
        """repr() works for regular (non-admin) users."""
        user = User(
            user_id="USER0001",
            first_name="Alice",
            last_name="Smith",
            password_hash="$2b$12$anotherfakehash",
            user_type="U",
        )
        repr_str = repr(user)
        assert "USER0001" in repr_str
        assert "U" in repr_str

    def test_user_has_expected_columns(self):
        """User model has all fields from USRSEC VSAM record."""
        user = User(
            user_id="TEST001",
            first_name="Test",
            last_name="User",
            password_hash="$2b$12$test",
            user_type="U",
        )
        assert user.user_id == "TEST001"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.password_hash == "$2b$12$test"
        assert user.user_type == "U"


class TestDatabaseSession:
    """Tests for the get_db() dependency lifecycle."""

    @pytest.mark.asyncio
    async def test_get_db_yields_session_and_commits(self):
        """
        get_db() yields a session, commits on successful exit,
        and closes the session.
        """
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.database.AsyncSessionLocal",
            return_value=mock_session_context,
        ):
            from app.database import get_db

            gen = get_db()
            session = await gen.__anext__()
            assert session is mock_session

            # Exhaust the generator (simulates successful request)
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_rolls_back_on_exception(self):
        """
        get_db() calls rollback when an exception propagates from the handler,
        then re-raises.
        """
        from unittest.mock import AsyncMock, patch

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.database.AsyncSessionLocal",
            return_value=mock_session_context,
        ):
            from app.database import get_db

            gen = get_db()
            session = await gen.__anext__()

            # Simulate an exception in the request handler
            with pytest.raises(ValueError):
                await gen.athrow(ValueError("DB error"))

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()
