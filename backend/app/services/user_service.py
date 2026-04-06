"""
Business logic for the User Management module.

COBOL origin: Encapsulates the PROCEDURE DIVISION logic from:
  COUSR00C — list/browse users (POPULATE-USER-DATA paragraph)
  COUSR01C — add user (PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE)
  COUSR02C — update user (UPDATE-USER-INFO → UPDATE-USER-SEC-FILE)
  COUSR03C — delete user (DELETE-USER-INFO → DELETE-USER-SEC-FILE)

Architecture rule: NO database calls in this layer.
All DB access is delegated to UserRepository.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import (
    NoChangesDetectedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

_repo = UserRepository()


async def list_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    user_id_filter: Optional[str] = None,
) -> UserListResponse:
    """
    Return a paginated list of users, ordered by user_id ascending.

    COBOL origin: COUSR00C POPULATE-USER-DATA paragraph (lines 360-520).
      - STARTBR USRSEC with RIDFLD = filter or LOW-VALUES
      - READNEXT up to 10 rows
      - One look-ahead READNEXT to determine CDEMO-CU00-NEXT-PAGE-FLG
      - ENDBR after each browse

    Modern equivalent:
      SELECT ... WHERE user_id >= filter ORDER BY user_id ASC
      LIMIT page_size OFFSET (page-1)*page_size
      COUNT(*) replaces look-ahead READNEXT for has_next calculation.

    Args:
        db: Active database session.
        page: Current page number (1-based). Maps to CDEMO-CU00-PAGE-NUM.
        page_size: Rows per page (max 10). Maps to COUSR00C's fixed 10-row display.
        user_id_filter: Optional user_id prefix/exact to start browse from.
                        Maps to USRIDINI → STARTBR RIDFLD.
    """
    rows, total_count = await _repo.list_all(
        db, page=page, page_size=page_size, user_id_filter=user_id_filter
    )

    items = [_to_response(u) for u in rows]
    has_next = (page * page_size) < total_count
    has_previous = page > 1
    first_key = items[0].user_id if items else None
    last_key = items[-1].user_id if items else None

    return UserListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_count=total_count,
        has_next=has_next,
        has_previous=has_previous,
        first_item_key=first_key,
        last_item_key=last_key,
    )


async def get_user(db: AsyncSession, user_id: str) -> UserResponse:
    """
    Fetch a single user by user_id. Raises 404 if not found.

    COBOL origin: COUSR02C PROCESS-ENTER-KEY → READ-USER-SEC-FILE:
      EXEC CICS READ DATASET(USRSEC) INTO(SEC-USER-DATA) RIDFLD(SEC-USR-ID)
      IF RESP = NOTFND → 'User ID NOT found...'
    Also used by COUSR03C PROCESS-ENTER-KEY before displaying delete confirmation.
    """
    user = await _repo.get_by_id(db, user_id.strip())
    if user is None:
        raise UserNotFoundError(user_id)
    return _to_response(user)


async def create_user(db: AsyncSession, request: UserCreateRequest) -> UserResponse:
    """
    Validate and insert a new user record. Raises 409 if user_id already exists.

    COBOL origin: COUSR01C PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE (lines 115-274).

    Validation order (mirrors COUSR01C EVALUATE TRUE short-circuit):
      1. first_name not blank  (Pydantic enforces at schema layer)
      2. last_name not blank   (Pydantic enforces at schema layer)
      3. user_id not blank     (Pydantic enforces at schema layer)
      4. password not blank    (Pydantic enforces at schema layer)
      5. user_type in ('A','U') (Pydantic Literal enforces at schema layer)
      6. user_id uniqueness check → 409 if duplicate (replaces RESP=DUPKEY/DUPREC)

    Security: password is bcrypt-hashed before storage; plain text is discarded.
    On success: returns the created UserResponse (password_hash never in response).
    """
    user_id = request.user_id.strip().upper()

    if await _repo.exists(db, user_id):
        raise UserAlreadyExistsError(user_id)

    new_user = User(
        user_id=user_id,
        first_name=request.first_name.strip(),
        last_name=request.last_name.strip(),
        password_hash=hash_password(request.password),
        user_type=request.user_type,
    )

    created = await _repo.create(db, new_user)
    logger.info("User created: %s (type=%s)", created.user_id, created.user_type)
    return _to_response(created)


async def update_user(
    db: AsyncSession, user_id: str, request: UserUpdateRequest
) -> UserResponse:
    """
    Apply field-level changes to an existing user. Raises 404 or 422 as appropriate.

    COBOL origin: COUSR02C UPDATE-USER-INFO paragraph (lines 177-245).

    Step 1: READ current record (COUSR02C READ-USER-SEC-FILE before REWRITE).
    Step 2: Validate non-blank fields (Pydantic schema layer handles this).
    Step 3: Field-level change detection — WS-USR-MODIFIED flag.
            Compare each editable field to current DB value.
            Mark modified if any differ.
    Step 4: If no fields modified → 422 'Please modify to update...' (USR-MODIFIED-NO path).
    Step 5: Apply changes and REWRITE (UPDATE-USER-SEC-FILE).

    Password handling: If request.password is None/blank → no password change.
    If provided → bcrypt-hash and store (replaces plain-text PASSWDI in COUSR02C).
    """
    user = await _repo.get_by_id(db, user_id.strip())
    if user is None:
        raise UserNotFoundError(user_id)

    modified = _apply_field_changes(user, request)

    if not modified:
        raise NoChangesDetectedError()

    updated = await _repo.update(db, user)
    logger.info("User updated: %s", updated.user_id)
    return _to_response(updated)


async def delete_user(db: AsyncSession, user_id: str) -> UserResponse:
    """
    Read-then-delete a user record. Raises 404 if not found.

    COBOL origin: COUSR03C DELETE-USER-INFO paragraph (lines 174-192).
      1. PERFORM READ-USER-SEC-FILE (re-read to reacquire UPDATE lock)
      2. PERFORM DELETE-USER-SEC-FILE

    The response includes the user details displayed before deletion
    (maps COUSR3A screen showing FNAME, LNAME, UTYPE for confirmation).

    Bug fix: COUSR03C DELETE-USER-SEC-FILE OTHER branch displays
    'Unable to Update User...' (copy-paste from COUSR02C template).
    This implementation corrects the message to reference deletion.
    """
    user = await _repo.get_by_id(db, user_id.strip())
    if user is None:
        raise UserNotFoundError(user_id)

    snapshot = _to_response(user)  # Capture details before deletion
    await _repo.delete(db, user)
    logger.info("User deleted: %s", user_id)
    return snapshot


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _to_response(user: User) -> UserResponse:
    """
    Convert a User ORM model to a UserResponse DTO.

    Ensures password_hash is NEVER included in any response.
    COBOL origin: BMS output map fields USRID, FNAME, LNAME, UTYPE
    from COUSR0AO / COUSR2AO — password field omitted from display.
    """
    return UserResponse(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        user_type=user.user_type,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _apply_field_changes(user: User, request: UserUpdateRequest) -> bool:
    """
    Apply field-level changes from request to the user ORM object.
    Returns True if at least one field was modified.

    COBOL origin: COUSR02C UPDATE-USER-INFO field comparison block (lines 219-234):
      IF FNAMEI NOT = SEC-USR-FNAME → MOVE FNAMEI TO SEC-USR-FNAME; SET USR-MODIFIED-YES
      IF LNAMEI NOT = SEC-USR-LNAME → MOVE LNAMEI TO SEC-USR-LNAME; SET USR-MODIFIED-YES
      IF PASSWDI NOT = SEC-USR-PWD  → MOVE PASSWDI TO SEC-USR-PWD; SET USR-MODIFIED-YES
      IF USRTYPEI NOT = SEC-USR-TYPE → MOVE USRTYPEI TO SEC-USR-TYPE; SET USR-MODIFIED-YES

    Modern equivalent: compare stripped values; if password provided and non-blank,
    always re-hash (cannot compare bcrypt hash to old hash for equality).
    """
    modified = False

    new_first = request.first_name.strip()
    if new_first != user.first_name:
        user.first_name = new_first
        modified = True

    new_last = request.last_name.strip()
    if new_last != user.last_name:
        user.last_name = new_last
        modified = True

    if request.password and request.password.strip():
        user.password_hash = hash_password(request.password)
        modified = True

    if request.user_type != user.user_type:
        user.user_type = request.user_type
        modified = True

    return modified
