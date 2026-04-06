"""
Authorization API routes.

All endpoints require JWT Bearer authentication.
The purge endpoint additionally requires admin role.

Route mapping to COBOL programs:
  POST /authorizations/process                        → COPAUA0C (MQ engine)
  GET  /authorizations                                → COPAUS0C (summary browse)
  GET  /authorizations/{account_id}                   → COPAUS0C (account detail)
  GET  /authorizations/{account_id}/details/{id}      → COPAUS1C (detail view)
  POST /authorizations/details/{id}/fraud             → COPAUS2C (fraud mark/remove)
  POST /authorizations/purge                          → CBPAUP0C (batch purge)

HTTP status code mapping:
  200 OK          → COBOL RETURN-CODE 0 / WS-FRD-UPDT-SUCCESS
  201 Created     → COBOL ISRT success
  400 Bad Request → COBOL validation failures
  401 Unauthorized → Not authenticated
  403 Forbidden   → Not admin (purge endpoint)
  404 Not Found   → COBOL NOTFND / GE condition
  500 Internal    → COBOL ABEND / IMS/DB2 error
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.schemas.authorization import (
    AuthorizationDetailResponse,
    AuthorizationListResponse,
    AuthorizationProcessRequest,
    AuthorizationProcessResponse,
    PaginatedDetailResponse,
    PurgeRequest,
    PurgeResponse,
)
from app.schemas.fraud import FraudActionRequest, FraudActionResponse
from app.services.authorization_service import AuthorizationService
from app.services.fraud_service import FraudService

router = APIRouter(prefix="/authorizations", tags=["Authorizations"])


@router.post(
    "/process",
    response_model=AuthorizationProcessResponse,
    status_code=201,
    summary="Process authorization request",
    description=(
        "Process an authorization request. Replaces the IMS+MQ-based COPAUA0C engine. "
        "Validates card/account, checks fraud flags, calculates available credit, "
        "and returns APPROVED or DECLINED with reason code."
    ),
)
async def process_authorization(
    request: AuthorizationProcessRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> AuthorizationProcessResponse:
    """Process a new authorization request."""
    service = AuthorizationService(db)
    return await service.process_authorization(request)


@router.get(
    "",
    response_model=AuthorizationListResponse,
    summary="List authorization summaries",
    description=(
        "List all authorization summaries with pagination. "
        "Optionally filter by account_id."
    ),
)
async def list_authorizations(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> AuthorizationListResponse:
    """List authorization summaries with optional account filter."""
    service = AuthorizationService(db)
    return await service.get_authorization_list(
        page=page, page_size=page_size, account_id=account_id
    )


@router.get(
    "/{account_id}",
    response_model=PaginatedDetailResponse,
    summary="Get authorization summary with detail list",
    description=(
        "Get account-level authorization summary (name, limits, balances, counts) "
        "with paginated list of authorization records (5 per page). "
        "Maps to COPAUS0C screen layout."
    ),
)
async def get_account_authorizations(
    account_id: str,
    page: int = Query(default=1, ge=1, description="Page number (5 records per page)"),
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> PaginatedDetailResponse:
    """Get authorization summary and paginated detail list for an account."""
    service = AuthorizationService(db)
    return await service.get_account_summary_with_details(
        account_id=account_id, page=page
    )


@router.get(
    "/{account_id}/details/{detail_id}",
    response_model=AuthorizationDetailResponse,
    summary="Get single authorization detail",
    description=(
        "Get full detail of a single authorization record including all merchant info, "
        "fraud status, and decline reason. Maps to COPAUS1C screen layout."
    ),
)
async def get_authorization_detail(
    account_id: str,
    detail_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> AuthorizationDetailResponse:
    """Get a single authorization detail record."""
    service = AuthorizationService(db)
    return await service.get_single_detail(
        account_id=account_id, detail_id=detail_id
    )


@router.post(
    "/details/{detail_id}/fraud",
    response_model=FraudActionResponse,
    summary="Mark or remove fraud flag",
    description=(
        "Mark an authorization as fraud ('mark') or remove the fraud flag ('remove'). "
        "Maps to COPAUS2C fraud action via EXEC CICS LINK from COPAUS1C (F5 key). "
        "Inserts or updates the fraud_records table (DB2 AUTHFRDS equivalent)."
    ),
)
async def toggle_fraud(
    detail_id: int,
    request: FraudActionRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> FraudActionResponse:
    """Mark or remove fraud flag on an authorization detail."""
    service = FraudService(db)
    return await service.toggle_fraud(detail_id=detail_id, request=request)


@router.post(
    "/purge",
    response_model=PurgeResponse,
    summary="Purge expired authorizations (admin only)",
    description=(
        "Purge expired authorization detail records older than expiry_days. "
        "Deletes empty summaries after detail purge. "
        "Maps to CBPAUP0C batch BMP program. Admin role required."
    ),
)
async def purge_authorizations(
    request: PurgeRequest,
    db: AsyncSession = Depends(get_db),
    _admin_user: dict = Depends(require_admin),
) -> PurgeResponse:
    """Admin-only: purge expired authorization records."""
    service = AuthorizationService(db)
    return await service.purge_expired_authorizations(request)
