"""User service — all business logic for the User Administration module.

Each method directly corresponds to COBOL paragraph logic:

    list_users()      ← COUSR00C PROCESS-PAGE-FORWARD/BACKWARD
    get_user()        ← COUSR02C/03C READ-USER-SEC-FILE (lookup phase)
    create_user()     ← COUSR01C PROCESS-ENTER-KEY + WRITE-USER-SEC-FILE
    update_user()     ← COUSR02C UPDATE-USER-INFO + UPDATE-USER-SEC-FILE
    delete_user()     ← COUSR03C DELETE-USER-INFO + DELETE-USER-SEC-FILE

Business rules preserved from specs:
    - All fields mandatory on create and update
    - user_type must be 'A' or 'U' (COBOL bug fixed — original only checked NOT SPACES)
    - Duplicate user_id on create raises UserAlreadyExistsError (DFHRESP(DUPKEY))
    - update_user detects no-change and raises NoChangesDetectedError
    - delete is two-phase: caller must first fetch (confirm screen), then delete
    - Passwords are never returned from any method
    - Error messages match COBOL text exactly where possible
    - COBOL bug fixed: delete error says "Unable to Delete User" (not "Update")
"""
import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserCreate,
    UserListItem,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.utils.password import hash_password, verify_password

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions — map to CICS RESP codes in COBOL
# ---------------------------------------------------------------------------


class UserNotFoundError(Exception):
    """User ID not found.  Maps to DFHRESP(NOTFND) in READ/DELETE paragraphs.

    COBOL message: 'User ID NOT found...'
    """

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"User ID NOT found: {user_id!r}")


class UserAlreadyExistsError(Exception):
    """Duplicate user ID.  Maps to DFHRESP(DUPKEY) / DFHRESP(DUPREC) in WRITE.

    COBOL message (COUSR01C): 'User ID already exist...'
    """

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"User ID already exist: {user_id!r}")


class NoChangesDetectedError(Exception):
    """No field values were modified.  Maps to the no-change branch in COUSR02C.

    COBOL message: 'Please modify to update ...'
    """

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"Please modify to update: {user_id!r}")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class UserService:
    """Business logic for User Administration (COUSR00C–03C)."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    # ------------------------------------------------------------------
    # COUSR00C — User List (paginated browse)
    # ------------------------------------------------------------------

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 10,
        search_user_id: str | None = None,
    ) -> UserListResponse:
        """Return one page of users ordered by user_id.

        Maps to COUSR00C PROCESS-PAGE-FORWARD which:
        - Does STARTBR at SEC-USR-ID (or LOW-VALUES if search field blank)
        - Reads up to 10 records via READNEXT
        - Does lookahead READNEXT to set NEXT-PAGE-YES/NO

        Args:
            page: 1-based page number (CDEMO-CU00-PAGE-NUM).
            page_size: Records per page; defaults to 10 (COUSR00C max rows).
            search_user_id: Optional user_id prefix (maps to USRIDINI field).

        Returns:
            UserListResponse with users and pagination metadata.
        """
        clean_search = search_user_id.strip() if search_user_id else None
        if clean_search == "":
            clean_search = None

        users, total_count = await self._repo.list_paginated(
            page=page,
            page_size=page_size,
            search_user_id=clean_search,
        )

        has_next = (page * page_size) < total_count
        has_prev = page > 1

        return UserListResponse(
            users=[
                UserListItem(
                    user_id=u.user_id,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    user_type=u.user_type,
                )
                for u in users
            ],
            page=page,
            page_size=page_size,
            total_count=total_count,
            has_next_page=has_next,
            has_prev_page=has_prev,
        )

    # ------------------------------------------------------------------
    # COUSR02C / COUSR03C — Fetch user for display (lookup phase)
    # ------------------------------------------------------------------

    async def get_user(self, user_id: str) -> UserResponse:
        """Fetch a user record by ID for display.

        Maps to READ-USER-SEC-FILE in COUSR02C (PROCESS-ENTER-KEY) and
        COUSR03C (PROCESS-ENTER-KEY) — the first phase that populates the
        screen fields for review before update or delete.

        Note: password is never included in the response.

        Raises:
            UserNotFoundError: If the user_id does not exist.
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            logger.warning("User lookup failed: user_id=%r not found", user_id)
            raise UserNotFoundError(user_id)

        return self._to_response(user)

    # ------------------------------------------------------------------
    # COUSR01C — Add User
    # ------------------------------------------------------------------

    async def create_user(self, data: UserCreate) -> UserResponse:
        """Create a new user record.

        Maps to COUSR01C PROCESS-ENTER-KEY + WRITE-USER-SEC-FILE.

        Business rules:
        - All fields mandatory (validated by Pydantic schema)
        - user_type must be 'A' or 'U' (COBOL bug fixed)
        - Duplicate user_id raises UserAlreadyExistsError
        - Password hashed with bcrypt before storage

        Args:
            data: Validated create request.

        Returns:
            Created user record (without password).

        Raises:
            UserAlreadyExistsError: If user_id already exists (DFHRESP(DUPKEY)).
        """
        logger.info("Creating user user_id=%r user_type=%r", data.user_id, data.user_type)

        user = User(
            user_id=data.user_id,
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            password=hash_password(data.password),
            user_type=data.user_type,
        )

        try:
            created = await self._repo.create(user)
        except IntegrityError as exc:
            logger.warning("Duplicate user_id=%r: %s", data.user_id, exc)
            raise UserAlreadyExistsError(data.user_id) from exc

        logger.info("User %r has been added", created.user_id)
        return self._to_response(created)

    # ------------------------------------------------------------------
    # COUSR02C — Update User
    # ------------------------------------------------------------------

    async def update_user(self, user_id: str, data: UserUpdate) -> UserResponse:
        """Update an existing user record.

        Maps to COUSR02C UPDATE-USER-INFO + UPDATE-USER-SEC-FILE.

        Business rules from COUSR02C:
        - User must exist (READ-USER-SEC-FILE; raises UserNotFoundError on NOTFND)
        - All editable fields are mandatory (validated by schema)
        - user_type must be 'A' or 'U' (bug fix applied)
        - Change detection: at least one field must differ (NoChangesDetectedError
          maps to "Please modify to update ..." message)
        - User ID is not updateable (it is the VSAM key — not in REWRITE fields)
        - Password is re-hashed only if it changed from the stored value
          (COBOL comparison was plaintext; here we check via verify_password)

        Args:
            user_id: The user to update (path parameter, immutable).
            data: Validated update request.

        Returns:
            Updated user record (without password).

        Raises:
            UserNotFoundError: If user_id does not exist.
            NoChangesDetectedError: If no field values differ from current record.
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        modified = self._apply_changes(user, data)

        if not modified:
            logger.info("No changes detected for user_id=%r", user_id)
            raise NoChangesDetectedError(user_id)

        updated = await self._repo.update(user)
        logger.info("User %r has been updated", updated.user_id)
        return self._to_response(updated)

    def _apply_changes(self, user: User, data: UserUpdate) -> bool:
        """Compare incoming data against the stored record and apply differences.

        Mirrors COUSR02C change-detection block (lines 215–235):
            IF FNAMEI NOT = SEC-USR-FNAME → move, SET USR-MODIFIED-YES
            IF LNAMEI NOT = SEC-USR-LNAME → move, SET USR-MODIFIED-YES
            IF PASSWDI NOT = SEC-USR-PWD  → move, SET USR-MODIFIED-YES
            IF USRTYPEI NOT = SEC-USR-TYPE→ move, SET USR-MODIFIED-YES

        For password: COBOL compared PIC X(08) plaintext directly.
        Here we use verify_password to check the bcrypt hash, because
        the incoming value is plaintext and the stored value is hashed.

        Returns:
            True if at least one field was changed (USR-MODIFIED-YES).
        """
        modified = False
        new_first = data.first_name.strip()
        new_last = data.last_name.strip()

        if new_first != user.first_name:
            user.first_name = new_first
            modified = True

        if new_last != user.last_name:
            user.last_name = new_last
            modified = True

        # Password: if not matching stored hash, it was changed
        if not verify_password(data.password, user.password):
            user.password = hash_password(data.password)
            modified = True

        if data.user_type != user.user_type:
            user.user_type = data.user_type
            modified = True

        return modified

    # ------------------------------------------------------------------
    # COUSR03C — Delete User
    # ------------------------------------------------------------------

    async def confirm_delete_user(self, user_id: str) -> UserResponse:
        """Fetch user for delete confirmation screen (phase 1 of two-phase delete).

        Maps to COUSR03C PROCESS-ENTER-KEY — READ-USER-SEC-FILE to display
        user info for confirmation.  FNAME, LNAME, USRTYPE shown read-only.
        Password is NOT returned (no password field on COUSR03 BMS map).

        Args:
            user_id: The user to preview for deletion.

        Returns:
            User record (read-only display data).

        Raises:
            UserNotFoundError: If user_id does not exist.
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return self._to_response(user)

    async def delete_user(self, user_id: str) -> None:
        """Permanently delete a user record (phase 2 of two-phase delete).

        Maps to COUSR03C DELETE-USER-INFO + DELETE-USER-SEC-FILE.

        Business rules from COUSR03C:
        - User must exist (READ-USER-SEC-FILE before DELETE)
        - COBOL bug fixed: error message says "Unable to Delete User"
          (original said "Unable to Update User" — copy-paste defect)
        - After deletion the screen is cleared for next entry

        Args:
            user_id: The user to delete.

        Raises:
            UserNotFoundError: If user_id does not exist.
        """
        user = await self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        await self._repo.delete(user)
        logger.info("User %r has been deleted", user_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_response(user: User) -> UserResponse:
        """Convert ORM model to response schema (password excluded)."""
        return UserResponse(
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            user_type=user.user_type,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
