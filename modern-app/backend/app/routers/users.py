"""HTTP endpoints for User Administration.

All endpoints require admin authentication (require_admin dependency).
Maps COBOL COUSR00C-03C programs to REST resources:

  GET    /api/users              → COUSR00C list/browse (paginated)
  GET    /api/users/{user_id}    → COUSR02C Phase 1 fetch
  POST   /api/users              → COUSR01C add user
  PUT    /api/users/{user_id}    → COUSR02C Phase 2 update
  DELETE /api/users/{user_id}    → COUSR03C Phase 2 delete

HTTP status mapping:
  200 — OK (GET, PUT)
  201 — Created (POST — mirrors VSAM WRITE success)
  204 — No Content was not used; we return 200 with a body for DELETE
        to provide the confirmation message COUSR03C shows ("User X deleted")
  400 — Bad Request (no changes detected — COUSR02C "Please modify" guard)
  404 — Not Found (VSAM NOTFND)
  409 — Conflict (VSAM DUPKEY/DUPREC on WRITE)
  403 — Forbidden (non-admin — admin menu guard from COADM01C)
  401 — Unauthorized (invalid/missing JWT)
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserDeleteResponse,
    UserListResponse,
    UserPublic,
    UserUpdate,
)
from app.services.user_service import DEFAULT_PAGE_SIZE, UserService

router = APIRouter(prefix="/api/users", tags=["users"])


def _get_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Inject a UserService with the current DB session."""
    return UserService(db)


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1, description="1-based page number"),
    page_size: int = Query(
        default=DEFAULT_PAGE_SIZE, ge=1, le=100, description="Records per page"
    ),
    user_id: str | None = Query(
        default=None,
        max_length=8,
        description="Filter by user_id prefix (mirrors COUSR00C USRIDIN search)",
    ),
    _admin: User = Depends(require_admin),
    service: UserService = Depends(_get_service),
) -> UserListResponse:
    """List all users with pagination and optional user_id filter.

    Mirrors COUSR00C paginated browse with STARTBR/READNEXT 10 logic.
    """
    return await service.list_users(
        page=page,
        page_size=page_size,
        user_id_filter=user_id,
    )


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: str,
    _admin: User = Depends(require_admin),
    service: UserService = Depends(_get_service),
) -> UserPublic:
    """Fetch a single user by user_id.

    Mirrors COUSR02C Phase 1 (ENTER — fetch for display).
    Returns 404 if user does not exist (VSAM NOTFND).
    """
    return await service.get_user(user_id)


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    _admin: User = Depends(require_admin),
    service: UserService = Depends(_get_service),
) -> UserPublic:
    """Create a new user record.

    Mirrors COUSR01C EXEC CICS WRITE flow.
    Returns 409 if user_id already exists (VSAM DUPKEY).
    Returns 201 on success.
    """
    return await service.create_user(body)


@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: str,
    body: UserUpdate,
    _admin: User = Depends(require_admin),
    service: UserService = Depends(_get_service),
) -> UserPublic:
    """Update an existing user record.

    Mirrors COUSR02C Phase 2 (PF5 save) with change-detection guard.
    Returns 400 if no fields changed ("Please modify to update").
    Returns 404 if user does not exist.
    """
    return await service.update_user(user_id, body)


@router.delete("/{user_id}", response_model=UserDeleteResponse)
async def delete_user(
    user_id: str,
    _admin: User = Depends(require_admin),
    service: UserService = Depends(_get_service),
) -> UserDeleteResponse:
    """Delete a user record.

    Mirrors COUSR03C Phase 2 (PF5 confirm delete).
    Returns 404 if user does not exist.
    Returns 200 with confirmation message on success.
    """
    return await service.delete_user(user_id)
