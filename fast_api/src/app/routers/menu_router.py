"""Menu router — REST API equivalents of COMEN01C (CM00) and COADM01C (CA00).

Endpoints:
  GET  /menu/main              → COMEN01C SEND-MENU-SCREEN (initial display)
  POST /menu/main/navigate     → COMEN01C PROCESS-ENTER-KEY (option selection)
  GET  /menu/admin             → COADM01C SEND-MENU-SCREEN (initial display)
  POST /menu/admin/navigate    → COADM01C PROCESS-ENTER-KEY (option selection)
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.auth_middleware import require_admin, require_regular_user
from app.schemas.auth import (
    MenuResponse,
    NavigateRequest,
    NavigateResponse,
    UserInfo,
)
from app.services.menu_service import MenuNavigationError, MenuService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/menu", tags=["Menu Navigation (COMEN01C / COADM01C)"])

_menu_service = MenuService()


@router.get(
    "/main",
    response_model=MenuResponse,
    summary="Get main menu (COMEN01C / Transaction CM00)",
    description=(
        "Returns the main menu options for authenticated regular users. "
        "Maps COMEN01C SEND-MENU-SCREEN + BUILD-MENU-OPTIONS + POPULATE-HEADER-INFO. "
        "COMEN01C BR-001: requires valid authentication (missing token → 401). "
        "Admin users may also access this menu (no restriction in COMEN01C itself)."
    ),
)
async def get_main_menu(
    current_user: Annotated[UserInfo, Depends(require_regular_user)],
) -> MenuResponse:
    """Return main menu for authenticated user.

    COMEN01C: First-entry logic (CDEMO-PGM-CONTEXT=0) → send menu screen.
    In REST: every GET is effectively a first-entry display.
    """
    return _menu_service.get_main_menu(current_user)


@router.post(
    "/main/navigate",
    response_model=NavigateResponse,
    summary="Select main menu option (COMEN01C PROCESS-ENTER-KEY)",
    description=(
        "Processes a menu option selection. Validates the option number (BR-003), "
        "checks access control (BR-004), handles COPAUS0C extension check (BR-005), "
        "and handles DUMMY options (BR-006). "
        "Returns the target route for the frontend to navigate to."
    ),
    responses={
        200: {"description": "Navigation target returned"},
        400: {"description": "Invalid option or access denied"},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin-only option selected by regular user (BR-004)"},
    },
)
async def navigate_main_menu(
    request: NavigateRequest,
    current_user: Annotated[UserInfo, Depends(require_regular_user)],
) -> NavigateResponse:
    """Process main menu option selection — maps COMEN01C PROCESS-ENTER-KEY."""
    try:
        return _menu_service.navigate_main_menu(request, current_user)
    except MenuNavigationError as exc:
        status_code = (
            status.HTTP_403_FORBIDDEN
            if "Admin Only" in exc.message
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail={"message": exc.message, "message_type": exc.message_type},
        ) from exc


@router.get(
    "/admin",
    response_model=MenuResponse,
    summary="Get admin menu (COADM01C / Transaction CA00)",
    description=(
        "Returns the admin menu options. Admin-only route (user_type='A' required). "
        "Maps COADM01C SEND-MENU-SCREEN + BUILD-MENU-OPTIONS + POPULATE-HEADER-INFO. "
        "COADM01C BR-001: requires valid authentication. "
        "COADM01C BR-009: no per-option access control within admin menu."
    ),
    responses={
        200: {"description": "Admin menu returned"},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin role required"},
    },
)
async def get_admin_menu(
    current_user: Annotated[UserInfo, Depends(require_admin)],
) -> MenuResponse:
    """Return admin menu for authenticated admin user.

    COADM01C: user_type must be 'A' — enforced by require_admin dependency.
    """
    return _menu_service.get_admin_menu(current_user)


@router.post(
    "/admin/navigate",
    response_model=NavigateResponse,
    summary="Select admin menu option (COADM01C PROCESS-ENTER-KEY)",
    description=(
        "Processes an admin menu option selection. Validates option range 1-6 (BR-003 COADM01C). "
        "Handles DUMMY programs (BR-004 COADM01C) and missing programs (BR-005 COADM01C). "
        "No per-option user type check (BR-009 COADM01C)."
    ),
    responses={
        200: {"description": "Navigation target returned"},
        400: {"description": "Invalid option or program not installed"},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin role required"},
    },
)
async def navigate_admin_menu(
    request: NavigateRequest,
    current_user: Annotated[UserInfo, Depends(require_admin)],
) -> NavigateResponse:
    """Process admin menu option selection — maps COADM01C PROCESS-ENTER-KEY."""
    try:
        return _menu_service.navigate_admin_menu(request, current_user)
    except MenuNavigationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": exc.message, "message_type": exc.message_type},
        ) from exc
