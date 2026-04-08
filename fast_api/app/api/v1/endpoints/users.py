"""
User management endpoints — derived from COUSR00C, COUSR01C, COUSR02C, COUSR03C.

Source programs:
  app/cbl/COUSR00C.cbl — User List   (CICS transaction CU00)
  app/cbl/COUSR01C.cbl — User Add    (CICS transaction CU01)
  app/cbl/COUSR02C.cbl — User Update (CICS transaction CU02)
  app/cbl/COUSR03C.cbl — User Delete (CICS transaction CU03)

BMS maps: COUSR00, COUSR01, COUSR02, COUSR03

All user management endpoints require admin access (user_type='A').
In COBOL, these screens are only reachable via the admin menu (COADM01C).

Endpoint mapping:
  GET    /api/v1/admin/users         → COUSR00C (browse USRSEC)
  POST   /api/v1/admin/users         → COUSR01C (write USRSEC)
  GET    /api/v1/admin/users/{id}    → EXEC CICS READ FILE(USRSEC)
  PUT    /api/v1/admin/users/{id}    → COUSR02C (rewrite USRSEC)
  DELETE /api/v1/admin/users/{id}    → COUSR03C (delete USRSEC)
"""
from fastapi import APIRouter

from app.dependencies import AdminUser, DBSession
from app.schemas.user import UserCreateRequest, UserListResponse, UserResponse, UserUpdateRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["User Management (COUSR00C-03C)"])


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users (COUSR00C / CU00)",
    responses={
        200: {"description": "Paginated user list"},
        403: {"description": "Admin access required"},
    },
)
async def list_users(
    db: DBSession,
    current_user: AdminUser,
    cursor: str | None = None,
    limit: int = 10,
    direction: str = "forward",
) -> UserListResponse:
    """
    Browse all users with keyset pagination.

    Derived from COUSR00C BROWSE-USERS paragraph:
      EXEC CICS STARTBR FILE('USRSEC') RIDFLD(WS-USER-ID)
      EXEC CICS READNEXT FILE('USRSEC') INTO(SEC-USER-DATA)

    CDEMO-CU00-USRID-FIRST / CDEMO-CU00-USRID-LAST track page boundaries.
    COUSR00C shows 10 users per screen page.

    Requires admin role (COADM01C admin menu access only in COBOL).
    """
    service = UserService(db)
    return await service.list_users(cursor=cursor, limit=limit, direction=direction)


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="Create user (COUSR01C / CU01)",
    responses={
        201: {"description": "User created"},
        403: {"description": "Admin access required"},
        409: {"description": "User ID already exists (CICS RESP=14 DUPREC)"},
    },
)
async def create_user(
    request: UserCreateRequest,
    db: DBSession,
    current_user: AdminUser,
) -> UserResponse:
    """
    Create a new user.

    Derived from COUSR01C PROCESS-ENTER-KEY:
      1. Validate user_id and password (non-blank)
      2. EXEC CICS WRITE FILE('USRSEC') FROM(SEC-USER-DATA)
      3. RESP=14 (DUPREC) → duplicate user ID → HTTP 409

    Password is bcrypt-hashed before storage (COBOL stores plaintext).
    user_id is normalized to 8-char uppercase (COBOL PIC X(08) behavior).
    """
    service = UserService(db)
    return await service.create_user(request)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user (EXEC CICS READ USRSEC)",
    responses={
        200: {"description": "User details"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found (CICS RESP=13 NOTFND)"},
    },
)
async def get_user(
    user_id: str,
    db: DBSession,
    current_user: AdminUser,
) -> UserResponse:
    """
    Retrieve user details by user ID.

    EXEC CICS READ FILE('USRSEC') INTO(SEC-USER-DATA) RIDFLD(user_id).
    Password hash is never returned.
    """
    service = UserService(db)
    return await service.get_user(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user (COUSR02C / CU02)",
    responses={
        200: {"description": "User updated"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found (CICS RESP=13 NOTFND)"},
    },
)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: DBSession,
    current_user: AdminUser,
) -> UserResponse:
    """
    Update user fields.

    Derived from COUSR02C PROCESS-ENTER-KEY:
      1. EXEC CICS READ FILE('USRSEC') (read-then-rewrite pattern)
      2. Update provided fields
      3. EXEC CICS REWRITE FILE('USRSEC') FROM(SEC-USER-DATA)

    user_id cannot be changed (it is the VSAM primary key).
    If password is provided, it is bcrypt-hashed before storage.
    """
    service = UserService(db)
    return await service.update_user(user_id, request)


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Delete user (COUSR03C / CU03)",
    responses={
        204: {"description": "User deleted"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found (CICS RESP=13 NOTFND)"},
    },
)
async def delete_user(
    user_id: str,
    db: DBSession,
    current_user: AdminUser,
) -> None:
    """
    Delete a user.

    Derived from COUSR03C PROCESS-ENTER-KEY:
      1. EXEC CICS READ FILE('USRSEC') — confirm record exists
      2. EXEC CICS DELETE FILE('USRSEC') RIDFLD(WS-USER-ID)
      3. Returns HTTP 204 (No Content) — equivalent to CICS RETURN

    RESP=13 (NOTFND) → HTTP 404.
    """
    service = UserService(db)
    await service.delete_user(user_id)
