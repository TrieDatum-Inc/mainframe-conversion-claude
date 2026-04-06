"""
REST API endpoints for User Management (admin-only).

COBOL origin: Replaces CICS transactions CU00, CU01, CU02, CU03 —
the SEND/RECEIVE MAP + AID key dispatch replaced by HTTP verbs and JSON.

All endpoints require admin privileges (user_type='A' JWT claim).
This mirrors the COUSR programs being reachable only from COADM01C.

Endpoint → COBOL mapping:
  GET  /users              → COUSR00C POPULATE-USER-DATA (browse/list)
  GET  /users/{user_id}    → COUSR02C PROCESS-ENTER-KEY (single read)
  POST /users              → COUSR01C PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE
  PUT  /users/{user_id}    → COUSR02C UPDATE-USER-INFO → UPDATE-USER-SEC-FILE
  DELETE /users/{user_id}  → COUSR03C DELETE-USER-INFO → DELETE-USER-SEC-FILE
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, require_admin
from app.database import get_db
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users (paginated)",
    description=(
        "Returns a paginated list of users ordered by user_id. "
        "COBOL origin: COUSR00C POPULATE-USER-DATA (STARTBR/READNEXT up to 10 rows). "
        "Admin only."
    ),
)
async def list_users(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=10, ge=1, le=10, description="Rows per page (max 10; COUSR00C shows 10)"
    ),
    user_id_filter: Optional[str] = Query(
        default=None,
        max_length=8,
        description="Filter: start browse at or after this user_id. Maps to USRIDINI field.",
    ),
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
) -> UserListResponse:
    """
    COUSR00C replacement — browse user list with optional filter and pagination.

    STARTBR behavior:
      - user_id_filter set → STARTBR at that key (WHERE user_id >= filter)
      - user_id_filter absent → STARTBR at LOW-VALUES (full table scan from start)
    """
    return await user_service.list_users(
        db, page=page, page_size=page_size, user_id_filter=user_id_filter
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get single user",
    description=(
        "Fetch one user by user_id. "
        "COBOL origin: COUSR02C PROCESS-ENTER-KEY → READ-USER-SEC-FILE (RESP=NORMAL path). "
        "Admin only."
    ),
)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
) -> UserResponse:
    """
    COUSR02C/COUSR03C READ-USER-SEC-FILE replacement.
    Returns 404 if user_id not found (maps RESP=NOTFND → 'User ID NOT found...').
    """
    return await user_service.get_user(db, user_id)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description=(
        "Add a new user. All five fields required. "
        "COBOL origin: COUSR01C PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE. "
        "Returns 409 if user_id already exists (RESP=DUPKEY/DUPREC). "
        "Admin only."
    ),
)
async def create_user(
    request: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
) -> UserResponse:
    """
    COUSR01C WRITE-USER-SEC-FILE replacement.

    Validation order preserved from COUSR01C EVALUATE TRUE:
      first_name → last_name → user_id → password → user_type
    Password is bcrypt-hashed; plain text is never stored.
    """
    return await user_service.create_user(db, request)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description=(
        "Update an existing user's fields. "
        "COBOL origin: COUSR02C UPDATE-USER-INFO → UPDATE-USER-SEC-FILE. "
        "Returns 422 if no fields were changed (USR-MODIFIED-NO path). "
        "Password is optional — omit to leave unchanged. "
        "Admin only."
    ),
)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
) -> UserResponse:
    """
    COUSR02C UPDATE-USER-INFO replacement.

    Field-level change detection preserved from COUSR02C (WS-USR-MODIFIED flag).
    If no fields differ from current values: 422 'Please modify to update...'
    """
    return await user_service.update_user(db, user_id, request)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete user",
    description=(
        "Delete an existing user after confirming existence. "
        "COBOL origin: COUSR03C DELETE-USER-INFO → DELETE-USER-SEC-FILE. "
        "Returns 404 if user_id not found. "
        "Bug fix: COUSR03C error message said 'Unable to Update User' on delete failure — "
        "corrected to 'Unable to delete user' in this implementation. "
        "Admin only."
    ),
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
) -> MessageResponse:
    """
    COUSR03C DELETE-USER-SEC-FILE replacement.

    Two-step pattern preserved:
      1. Read user record (verify existence — maps READ-USER-SEC-FILE)
      2. Delete record (maps DELETE-USER-SEC-FILE)

    COUSR03C bug fixed: original said 'Unable to Update User...' on DELETE failure.
    This endpoint returns 'Unable to delete user' on unexpected errors.
    """
    await user_service.delete_user(db, user_id)
    return MessageResponse(message=f"User {user_id} has been deleted successfully")
