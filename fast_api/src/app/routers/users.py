"""User Administration API router.

HTTP layer only — no business logic here.
All COBOL CICS command equivalents are in the service layer.

Endpoint ↔ COBOL program mapping:
    GET  /api/users               ← COUSR00C (User List, CU00)
    POST /api/users               ← COUSR01C (User Add, CU01)
    GET  /api/users/{user_id}     ← COUSR02C/COUSR03C (lookup phase)
    PUT  /api/users/{user_id}     ← COUSR02C (User Update, CU02)
    DELETE /api/users/{user_id}   ← COUSR03C (User Delete, CU03)

All endpoints require admin role (COUSR00C–03C are admin-only programs
reached only through the admin menu COADM01C).

Admin-only enforcement note:
    Full JWT auth middleware is part of the auth module (COSGN00C conversion).
    Here we use a simple header-based stub that can be replaced with the real
    JWT dependency when the auth module is wired up.  The stub checks for
    X-User-Type: A header, which the auth middleware will set after JWT validation.
"""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import (
    NoChangesDetectedError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


# ---------------------------------------------------------------------------
# Admin auth dependency
# ---------------------------------------------------------------------------


async def require_admin(x_user_type: str = Header(default="")) -> None:
    """Require the caller to be an admin user.

    COBOL context: All COUSR0xC programs are admin-only — they are only
    reachable via COADM01C (admin menu), which itself requires CDEMO-USER-TYPE='A'.

    In production this should be replaced by a JWT-based dependency that
    validates the token and checks the user_type claim.  This stub allows
    integration testing without the auth module dependency.
    """
    if x_user_type.upper() != "A":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


# ---------------------------------------------------------------------------
# GET /api/users — COUSR00C User List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users (COUSR00C — CU00)",
    description=(
        "Paginated browse of all users ordered by user_id. "
        "Maps to COUSR00C STARTBR/READNEXT with page_size=10 per screen. "
        "Optional search_user_id positions the browse at that key "
        "(COUSR00C USRIDINI field — empty=start from beginning)."
    ),
    dependencies=[Depends(require_admin)],
)
async def list_users(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Records per page (COUSR00C shows 10 rows per BMS screen)",
    ),
    search_user_id: str | None = Query(
        default=None,
        max_length=8,
        description="Search/filter by user_id prefix (COUSR00C USRIDINI field)",
    ),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    service = UserService(db)
    return await service.list_users(
        page=page,
        page_size=page_size,
        search_user_id=search_user_id,
    )


# ---------------------------------------------------------------------------
# POST /api/users — COUSR01C User Add
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add user (COUSR01C — CU01)",
    description=(
        "Create a new user record. "
        "All fields are mandatory (mirrors COUSR01C PROCESS-ENTER-KEY validation). "
        "user_type must be 'A' (Admin) or 'U' (Regular) — "
        "COBOL bug fixed: original only validated NOT SPACES. "
        "Returns HTTP 409 on duplicate user_id (DFHRESP(DUPKEY))."
    ),
    dependencies=[Depends(require_admin)],
)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    service = UserService(db)
    try:
        return await service.create_user(body)
    except UserAlreadyExistsError as exc:
        # COUSR01C WRITE-USER-SEC-FILE: DFHRESP(DUPKEY/DUPREC)
        # message: 'User ID already exist...'
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User ID already exist: {exc.user_id}",
        ) from exc


# ---------------------------------------------------------------------------
# GET /api/users/{user_id} — COUSR02C/03C lookup phase
# ---------------------------------------------------------------------------


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user (COUSR02C/03C lookup phase)",
    description=(
        "Fetch a single user by ID. "
        "Maps to the first phase (ENTER key) of COUSR02C (Update) and "
        "COUSR03C (Delete) where the user record is displayed for review. "
        "Returns HTTP 404 when user not found (DFHRESP(NOTFND))."
    ),
    dependencies=[Depends(require_admin)],
)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    service = UserService(db)
    try:
        return await service.get_user(user_id)
    except UserNotFoundError as exc:
        # COUSR02C/03C READ-USER-SEC-FILE: DFHRESP(NOTFND)
        # message: 'User ID NOT found...'
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User ID NOT found: {exc.user_id}",
        ) from exc


# ---------------------------------------------------------------------------
# PUT /api/users/{user_id} — COUSR02C User Update
# ---------------------------------------------------------------------------


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user (COUSR02C — CU02)",
    description=(
        "Update an existing user record. "
        "Maps to COUSR02C UPDATE-USER-INFO + UPDATE-USER-SEC-FILE (REWRITE). "
        "User ID is immutable (VSAM key — not in REWRITE fields). "
        "Returns HTTP 422 if no fields changed "
        "('Please modify to update ...' in COBOL). "
        "PF3 save-and-exit behaviour is handled by the frontend redirect."
    ),
    dependencies=[Depends(require_admin)],
)
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    service = UserService(db)
    try:
        return await service.update_user(user_id, body)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User ID NOT found: {exc.user_id}",
        ) from exc
    except NoChangesDetectedError:
        # COUSR02C UPDATE-USER-INFO: no-change branch
        # message: 'Please modify to update ...'
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please modify to update ...",
        )


# ---------------------------------------------------------------------------
# DELETE /api/users/{user_id} — COUSR03C User Delete
# ---------------------------------------------------------------------------


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user (COUSR03C — CU03)",
    description=(
        "Permanently delete a user record. "
        "Maps to COUSR03C DELETE-USER-INFO + DELETE-USER-SEC-FILE. "
        "Two-phase confirmation is enforced by the frontend (display then confirm). "
        "COBOL bug fixed: error message uses 'Unable to Delete User' "
        "(original incorrectly said 'Unable to Update User'). "
        "Returns HTTP 204 on success."
    ),
    dependencies=[Depends(require_admin)],
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = UserService(db)
    try:
        await service.delete_user(user_id)
    except UserNotFoundError as exc:
        # COUSR03C DELETE-USER-SEC-FILE: DFHRESP(NOTFND)
        # message: 'User ID NOT found...'
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User ID NOT found: {exc.user_id}",
        ) from exc
