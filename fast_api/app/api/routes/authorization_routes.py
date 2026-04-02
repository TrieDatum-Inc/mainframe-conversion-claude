"""
Authorization subsystem routes.
Maps COPAUS0C, COPAUS1C, COPAUS2C, COPAUA0C programs.
"""

from datetime import date, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_user
from app.core.exceptions import ResourceNotFoundError
from app.domain.services.authorization_service import (
    flag_fraud,
    get_auth_detail,
    get_auth_details_for_account,
    get_auth_summary_list,
    process_authorization,
)
from app.infrastructure.database import get_db
from app.schemas.auth_schemas import UserContext
from app.schemas.authorization_schemas import (
    AuthDetailView,
    AuthSummaryListResponse,
    AuthorizationRequest,
    AuthorizationResponse,
    FraudFlagRequest,
)

router = APIRouter(
    prefix="/authorizations",
    tags=["Authorization (COPAUS0C/1C/2C/COPAUA0C)"],
)


@router.get(
    "",
    response_model=AuthSummaryListResponse,
    status_code=status.HTTP_200_OK,
    summary="Pending authorization summary list (COPAUS0C)",
    description="""
    List pending authorization summaries.

    Maps COPAUS0C / COPAU00 BMS map:
    - Account ID input (optional filter)
    - Displays list of IMS PAUTSUM0 (CIPAUSMY) segments
    """,
)
async def get_auth_summaries(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> AuthSummaryListResponse:
    return await get_auth_summary_list(db, account_id_filter=account_id)


@router.get(
    "/{acct_id}/details",
    response_model=list[AuthDetailView],
    status_code=status.HTTP_200_OK,
    summary="Authorization details for account (COPAUS1C)",
    description="List all authorization detail records for an account (IMS CIPAUDTY segments).",
)
async def get_auth_details(
    acct_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> list[AuthDetailView]:
    return await get_auth_details_for_account(acct_id, db)


@router.get(
    "/{acct_id}/details/{auth_date}/{auth_time}",
    response_model=AuthDetailView,
    status_code=status.HTTP_200_OK,
    summary="Authorization detail view (COPAUS1C)",
    description="""
    Read single authorization detail record.

    Maps COPAUS1C / COPAU01 BMS map:
    - Key: account ID + auth_date (YYYYMMDD) + auth_time (HHMMSS)
    - Displays IMS CIPAUDTY segment including fraud_flag
    """,
)
async def get_auth_detail_endpoint(
    acct_id: int,
    auth_date: date,
    auth_time: time,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> AuthDetailView:
    try:
        return await get_auth_detail(acct_id, auth_date, auth_time, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )


@router.post(
    "/fraud-flag",
    status_code=status.HTTP_200_OK,
    summary="Flag authorization as fraudulent (COPAUS2C)",
    description="""
    Flag an authorization record as fraudulent.

    Maps COPAUS2C:
    - COPAUS1C LINK -> COPAUS2C (CICS LINK, not XCTL)
    - If AUTHFRDS record exists: EXEC SQL UPDATE CARDDEMO.AUTHFRDS
    - If not exists: EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS
    - Sets IMS CIPAUDTY fraud_flag = 'Y' (IMS REPL)
    """,
)
async def flag_fraud_endpoint(
    request: FraudFlagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> dict:
    try:
        return await flag_fraud(request, current_user.user_id, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )


@router.post(
    "/process",
    response_model=AuthorizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Process authorization decision (COPAUA0C)",
    description="""
    Make an authorization approve/decline decision.

    Maps COPAUA0C MQ-triggered engine (now REST-triggered):
    1. Resolve card -> XREF -> account
    2. Compute available = credit_limit - |curr_bal| - running_approved
    3. available >= requested -> APPROVE ('00')
       else -> DECLINE ('51' insufficient funds)
    4. Write IMS PAUTDTL1 record
    5. Update IMS PAUTSUM0 running totals

    Original: processes up to 500 MQ messages per invocation.
    """,
)
async def process_auth(
    request: AuthorizationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> AuthorizationResponse:
    try:
        return await process_authorization(request, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )
