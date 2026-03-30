"""Authentication router porting COBOL program COSGN00C.

COSGN00C handles the CardDemo sign-on screen. It reads SEC-USR-ID and
SEC-USR-PWD from the BMS map, validates against USRSEC (CSUSR01Y.cpy),
and populates the COMMAREA with CDEMO-USER-ID / CDEMO-USER-TYPE on
success. This router replaces that flow with a JWT-based login endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticate a user and return a JWT token.

    Ports COBOL program COSGN00C which validates SEC-USR-ID and SEC-USR-PWD
    against the USRSEC VSAM file and populates the COMMAREA user context.
    No authentication required on this endpoint.
    """
    return auth_service.authenticate_user(db, body.user_id, body.password)
