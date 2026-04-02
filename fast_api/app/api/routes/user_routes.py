"""
User management routes (Admin only).
Maps COUSR00C (CU00), COUSR01C (CU01), COUSR02C (CU02), COUSR03C (CU03).

All endpoints require admin user type ('A').
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.core.exceptions import (
    BusinessValidationError,
    DuplicateKeyError,
    ResourceNotFoundError,
)
from app.domain.services.user_service import (
    create_user,
    delete_user,
    get_user,
    list_users,
    update_user,
)
from app.infrastructure.database import get_db
from app.schemas.auth_schemas import UserContext
from app.schemas.user_schemas import (
    UserCreateRequest,
    UserDeleteRequest,
    UserListResponse,
    UserUpdateRequest,
    UserView,
)

router = APIRouter(prefix="/users", tags=["User Management (COUSR00C-03C, Admin Only)"])


@router.get(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List users (COUSR00C - CU00, Admin Only)",
    description="""
    Paginated user list. Admin only.
    10 rows per page (COUSR00C WS-USER-DATA OCCURS 10).

    COUSR00C COMMAREA:
    - CDEMO-CU00-USRID-FIRST / LAST (page boundaries)
    - CDEMO-CU00-PAGE-NUM
    - CDEMO-CU00-NEXT-PAGE-FLG

    Actions from list (original screen):
    - 'U' = update user -> PUT /users/{usr_id}
    - 'D' = delete user -> DELETE /users/{usr_id}
    """,
)
async def list_users_endpoint(
    start_usr_id: Optional[str] = Query(None, max_length=8),
    end_usr_id: Optional[str] = Query(None, max_length=8),
    direction: str = Query("forward", description="'forward' or 'backward'"),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> UserListResponse:
    return await list_users(
        db=db,
        page_size=page_size,
        start_usr_id=start_usr_id,
        direction=direction,
        end_usr_id=end_usr_id,
    )


@router.get(
    "/{usr_id}",
    response_model=UserView,
    status_code=status.HTTP_200_OK,
    summary="Get user (Admin Only)",
    description="Read user record for display before update (COUSR02C pre-read).",
)
async def get_user_endpoint(
    usr_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> UserView:
    try:
        return await get_user(usr_id, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )


@router.post(
    "",
    response_model=UserView,
    status_code=status.HTTP_201_CREATED,
    summary="Add user (COUSR01C - CU01, Admin Only)",
    description="""
    Create a new user record in USRSEC.

    COUSR01C validation (all 5 fields mandatory):
    - first_name: max 20 chars
    - last_name: max 20 chars
    - usr_id: 1-8 chars, upper-cased, must be unique
    - password: 1-8 chars (bcrypt hashed at rest)
    - usr_type: 'A' or 'U'
    """,
)
async def create_user_endpoint(
    request: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> UserView:
    try:
        return await create_user(request, db)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "CDERR070", "message": exc.message},
        )


@router.put(
    "/{usr_id}",
    response_model=UserView,
    status_code=status.HTTP_200_OK,
    summary="Update user (COUSR02C - CU02, Admin Only)",
    description="""
    Update user record. User ID (key) cannot be changed.

    COUSR02C: REWRITE USRSEC after validation.
    Updatable fields: first_name, last_name, usr_type, password (optional).
    """,
)
async def update_user_endpoint(
    usr_id: str,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> UserView:
    try:
        return await update_user(usr_id, request, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )


@router.delete(
    "/{usr_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete user (COUSR03C - CU03, Admin Only)",
    description="""
    Delete user record from USRSEC.

    COUSR03C: Two-step confirm pattern.
    Pass confirm=true in body to confirm deletion.
    """,
)
async def delete_user_endpoint(
    usr_id: str,
    request: UserDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_admin),
) -> dict:
    try:
        return await delete_user(usr_id, request.confirm, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )
    except BusinessValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "CDERR422", "message": exc.message},
        )
