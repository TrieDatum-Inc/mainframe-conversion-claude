"""
User management service — business logic from COUSR00C-03C.

Paragraph mapping:
  COUSR00C BROWSE-USERS             → list_users()
  COUSR01C PROCESS-ENTER-KEY        → create_user()
  COUSR02C PROCESS-ENTER-KEY        → update_user()
  COUSR03C PROCESS-ENTER-KEY        → delete_user()

Business rules preserved:
  1. User ID: 8-char max, uppercase, space-padded (SEC-USR-ID PIC X(08))
  2. Password: 8-char max in COBOL → stored as bcrypt hash
  3. User type: 'A' or 'U' only (88-level conditions)
  4. Delete: read record first, then delete (COUSR03C read-then-delete pattern)
  5. Duplicate user_id on create → DuplicateRecordError (CICS DUPREC → HTTP 409)
  6. User not found → RecordNotFoundError (CICS NOTFND → HTTP 404)
  7. Browse is paginated by user_id key (STARTBR/READNEXT USRSEC)
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest
from app.services.auth_service import AuthService
from app.utils.cobol_compat import cobol_trim, pad_user_id


class UserService:
    """User management business logic from COUSR00C-03C."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserRepository(db)

    async def list_users(
        self, cursor: str | None = None, limit: int = 10, direction: str = "forward"
    ) -> UserListResponse:
        """
        COUSR00C BROWSE-USERS paragraph.

        STARTBR FILE('USRSEC') → READNEXT — sequential browse by user_id.
        CDEMO-CU00-USRID-FIRST / CDEMO-CU00-USRID-LAST track page boundaries.

        Args:
            cursor: Last user_id from previous page.
            limit: Page size (COUSR00C: 10 rows per screen).

        Returns:
            UserListResponse with pagination cursor.
        """
        users, total, has_more = await self._repo.list_paginated(
            cursor=cursor, limit=limit, direction=direction
        )
        items = [self._build_response(u) for u in users]
        first = users[0].user_id.strip() if users else None
        last = users[-1].user_id.strip() if users else None

        # has_more reflects whether more rows exist in the *direction of fetch*.
        # forward: more rows after `last`  → has_next
        # backward: more rows before `first` → has_prev
        if direction == "backward":
            has_prev = has_more
            has_next = True  # came from a forward page, so next exists
        else:
            has_next = has_more
            has_prev = cursor is not None  # came from a previous page

        return UserListResponse(
            items=items,
            total=total,
            next_cursor=last if has_next and users else None,
            prev_cursor=first if has_prev and users else None,
        )

    async def get_user(self, user_id: str) -> UserResponse:
        """
        EXEC CICS READ FILE('USRSEC') RIDFLD(user_id).
        Raises RecordNotFoundError if not found.
        """
        user = await self._repo.get_by_id(user_id)
        return self._build_response(user)

    async def create_user(self, request: UserCreateRequest) -> UserResponse:
        """
        COUSR01C PROCESS-ENTER-KEY → EXEC CICS WRITE FILE('USRSEC').

        Business rules:
          1. user_id normalized to 8-char uppercase (pad_user_id)
          2. password hashed with bcrypt (replaces plaintext SEC-USR-PWD)
          3. Duplicate → DuplicateRecordError (CICS RESP=14 DUPREC → HTTP 409)
        """
        user = User(
            user_id=pad_user_id(request.user_id),  # SEC-USR-ID PIC X(08)
            first_name=request.first_name,
            last_name=request.last_name,
            password_hash=AuthService.hash_password(request.password),
            user_type=request.user_type or "U",
        )
        created = await self._repo.create(user)
        return self._build_response(created)

    async def update_user(self, user_id: str, request: UserUpdateRequest) -> UserResponse:
        """
        COUSR02C PROCESS-ENTER-KEY → EXEC CICS REWRITE FILE('USRSEC').

        Read-then-rewrite pattern (COBOL requires READ before REWRITE).
        Only updates provided fields; user_id cannot be changed (it is the key).
        """
        # COUSR02C: READ FILE('USRSEC') before REWRITE
        user = await self._repo.get_by_id(user_id)

        self._apply_user_changes(user, request)

        updated = await self._repo.update(user)
        return self._build_response(updated)

    async def delete_user(self, user_id: str) -> None:
        """
        COUSR03C PROCESS-ENTER-KEY → EXEC CICS DELETE FILE('USRSEC').

        COUSR03C reads the record first to confirm existence, then deletes.
        Raises RecordNotFoundError if user not found.
        """
        # COUSR03C: READ FILE('USRSEC') first (read-then-delete pattern)
        await self._repo.delete(user_id)  # repo handles the read-then-delete

    def _apply_user_changes(self, user: User, request: UserUpdateRequest) -> None:
        """
        COUSR02C: apply only provided field changes.
        Mirrors COBOL MOVE — only explicitly provided fields are rewritten.
        """
        if request.first_name is not None:
            user.first_name = request.first_name
        if request.last_name is not None:
            user.last_name = request.last_name
        if request.user_type is not None:
            user.user_type = request.user_type
        if request.password is not None:
            user.password_hash = AuthService.hash_password(request.password)

    @staticmethod
    def _build_response(user: User) -> UserResponse:
        """Build UserResponse from ORM model (never include password hash)."""
        return UserResponse(
            user_id=user.user_id.strip(),
            first_name=cobol_trim(user.first_name),
            last_name=cobol_trim(user.last_name),
            user_type=user.user_type,
            is_admin=user.is_admin,
        )
