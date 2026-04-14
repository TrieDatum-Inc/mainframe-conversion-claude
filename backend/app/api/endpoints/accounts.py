"""
Accounts API endpoints.

COBOL origin:
  GET /api/v1/accounts/{account_id}  → COACTVWC (Transaction CAVW)
    Replaces: CICS pseudo-conversational READ of ACCTDAT + CUSTDAT via CXACAIX
  PUT /api/v1/accounts/{account_id}  → COACTUPC (Transaction CAUP)
    Replaces: CICS pseudo-conversational READ UPDATE + REWRITE of ACCTDAT + CUSTDAT

Authentication:
  Both endpoints require a valid JWT Bearer token.
  COBOL origin of auth requirement: ALL CICS programs check EIBCALEN=0:
    IF EIBCALEN = 0: XCTL COSGN00C  (redirect to sign-on if no session)
  Modern equivalent: 401 Unauthorized if Authorization header is missing or invalid.

Router is thin — no business logic here. All logic delegates to AccountService.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.account import AccountUpdateRequest, AccountViewResponse
from app.services.account_service import AccountService
from app.utils.security import decode_access_token

from fastapi import HTTPException

router = APIRouter(prefix="/accounts", tags=["Accounts"])
_security_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_security_scheme)],
) -> dict:
    """
    Decode and validate the JWT Bearer token.

    COBOL origin: Every CICS program entry point:
      IF EIBCALEN = 0: XCTL COSGN00C
    In the COBOL system, EIBCALEN=0 meant no COMMAREA — no session.
    In the modern system, absence or invalidity of the JWT Bearer token
    is the equivalent condition → 401 Unauthorized.
    """
    try:
        payload = decode_access_token(credentials.credentials)
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "UNAUTHORIZED",
                "message": "Could not validate credentials",
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.get(
    "/{account_id}",
    status_code=status.HTTP_200_OK,
    summary="View account and linked customer details",
    description=(
        "Returns complete account financial parameters and linked customer details "
        "for the given account ID. "
        "Maps COACTVWC (Transaction CAVW): reads ACCTDAT → CXACAIX → CUSTDAT. "
        "SSN is always returned masked (***-**-XXXX). "
        "Requires valid JWT Bearer token."
    ),
    responses={
        200: {"description": "Account details returned successfully"},
        401: {"description": "Missing or invalid Bearer token"},
        404: {"description": "Account or linked customer not found"},
        422: {"description": "Invalid account_id (zero or negative)"},
    },
)
async def get_account(
    account_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountViewResponse:
    """
    Retrieve account and customer details.

    COBOL origin: COACTVWC MAIN-PARA → 9000-READ-ACCT paragraph.
    """
    return await AccountService.get_account(
        db=db,
        account_id=account_id,
        requesting_user_id=current_user.get("sub", "unknown"),
    )


@router.put(
    "/{account_id}",
    status_code=status.HTTP_200_OK,
    summary="Update account and customer fields",
    description=(
        "Validates and applies changes to account financial parameters and customer "
        "identity fields. Returns the updated account record on success. "
        "Maps COACTUPC (Transaction CAUP): validates 15+ fields, then REWRITEs "
        "ACCTDAT and CUSTDAT. "
        "Returns 422 if no fields were changed (WS-DATACHANGED-FLAG equivalent). "
        "Requires valid JWT Bearer token."
    ),
    responses={
        200: {"description": "Account updated; full updated record returned"},
        401: {"description": "Missing or invalid Bearer token"},
        404: {"description": "Account or linked customer not found"},
        422: {
            "description": (
                "Validation error — invalid field values, SSN part1 rules, "
                "cash limit > credit limit, or no changes detected"
            )
        },
    },
)
async def update_account(
    account_id: int,
    request: AccountUpdateRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountViewResponse:
    """
    Update account and customer fields.

    COBOL origin: COACTUPC MAIN-PARA → 2000-PROCESS-INPUTS → 9000-UPDATE-ACCOUNT.
    """
    return await AccountService.update_account(
        db=db,
        account_id=account_id,
        request=request,
        requesting_user_id=current_user.get("sub", "unknown"),
    )
