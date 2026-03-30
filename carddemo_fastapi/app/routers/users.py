"""User management router porting COBOL programs COUSR00C, COUSR01C, COUSR02C, and COUSR03C.

COUSR00C lists users with STARTBR/READNEXT pagination over the USRSEC
VSAM file (CSUSR01Y.cpy). Admin-only screen.

COUSR01C handles new user creation, writing to the USRSEC file.

COUSR02C displays/updates a selected user record.

COUSR03C handles user deletion with a confirmation step.

This router replaces all four screens with REST endpoints.
All endpoints require admin access (user_type='A').
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import UserCreate, UserListItem, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(tags=["users"])


@router.get("/", response_model=PaginatedResponse[UserListItem])
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> PaginatedResponse[UserListItem]:
    """List all users with pagination.

    Ports COBOL program COUSR00C which uses STARTBR/READNEXT to browse
    the USRSEC VSAM KSDS file. Admin-only access.
    """
    return user_service.list_users(db, page=page, page_size=page_size)


@router.post("/", response_model=MessageResponse)
def add_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> MessageResponse:
    """Create a new user.

    Ports COBOL program COUSR01C which validates input fields and writes
    a new record to the USRSEC VSAM file. Admin-only access.
    """
    return user_service.add_user(db, body.model_dump())


@router.get("/{usr_id}", response_model=UserRead)
def get_user(
    usr_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserRead:
    """Retrieve a specific user by ID.

    Ports COBOL program COUSR02C display mode which reads a user record
    from the USRSEC VSAM file. Admin-only access.
    """
    return user_service.get_user(db, usr_id)


@router.put("/{usr_id}", response_model=MessageResponse)
def update_user(
    usr_id: str,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> MessageResponse:
    """Update an existing user.

    Ports COBOL program COUSR02C update mode which validates and rewrites
    the user record in the USRSEC VSAM file. Admin-only access.
    """
    return user_service.update_user(db, usr_id, body.model_dump(exclude_unset=True))


@router.delete("/{usr_id}", response_model=MessageResponse)
def delete_user(
    usr_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> MessageResponse:
    """Delete a user.

    Ports COBOL program COUSR03C which deletes the user record from
    the USRSEC VSAM file after confirmation. Admin-only access.
    """
    return user_service.delete_user(db, usr_id)
