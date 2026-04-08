"""
Authentication endpoint — derived from COSGN00C (CICS transaction CC00).

Source: app/cbl/COSGN00C.cbl
BMS map: COSGN00 (COSGN0A map)
CICS transaction: CC00

Conversion:
  COSGN0A RECEIVE MAP → POST /api/v1/auth/login request body
  EXEC CICS XCTL (success) → 200 response with JWT token
  WS-MESSAGE error → 401 response with detail message
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import DBSession
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication (COSGN00C)"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User sign-on (COSGN00C / CC00 transaction)",
    responses={
        200: {"description": "Successful login — JWT token returned"},
        401: {"description": "CICS RESP=13 (NOTFND) or wrong password"},
    },
)
async def login(request: LoginRequest, db: DBSession) -> TokenResponse:
    """
    Authenticate a CardDemo user.

    Derived from COSGN00C PROCESS-ENTER-KEY and READ-USER-SEC-FILE paragraphs.

    Business rules (preserved from COSGN00C):
      1. user_id is uppercased before lookup (FUNCTION UPPER-CASE)
      2. RESP=13 (NOTFND) → "User not found. Try again ..."
      3. Wrong password → "Wrong Password. Try again ..."
      4. User type 'A' → admin JWT role; 'U' → regular user role

    Replaces:
      EXEC CICS RETURN TRANSID(WS-TRANID) COMMAREA(CARDDEMO-COMMAREA)
    """
    service = AuthService(db)
    return await service.authenticate_user(request)


@router.post(
    "/token",
    response_model=TokenResponse,
    include_in_schema=True,  # OAuth2 form-based login (for Swagger UI Authorize button)
)
async def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSession,
) -> TokenResponse:
    """OAuth2 form-based login for Swagger UI compatibility."""
    service = AuthService(db)
    login_req = LoginRequest(user_id=form_data.username, password=form_data.password)
    return await service.authenticate_user(login_req)
