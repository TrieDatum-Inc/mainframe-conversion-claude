"""
Authorization API endpoints — thin controller layer.
All business logic is delegated to AuthorizationService.
No direct database calls or business logic in this module.

COBOL transaction mapping:
  GET  /api/v1/authorizations                    → COPAUS0C CPVS transaction (summary list)
  GET  /api/v1/authorizations/{account_id}/details → COPAUS0C + pagination
  GET  /api/v1/authorizations/detail/{auth_id}   → COPAUS1C CPVD transaction (detail view)
  PUT  /api/v1/authorizations/detail/{auth_id}/fraud → COPAUS1C PF5 → COPAUS2C LINK
  GET  /api/v1/authorizations/detail/{auth_id}/fraud-logs → Audit trail (DB2 AUTHFRDS)
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.authorization_repository import AuthorizationRepository
from app.schemas.authorization import (
    AuthDetailResponse,
    AuthFraudLogResponse,
    AuthListResponse,
    FraudToggleRequest,
    FraudToggleResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.authorization_service import AuthorizationService
from app.utils.security import get_current_user

router = APIRouter(
    prefix="/authorizations",
    tags=["authorizations"],
)


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthorizationService:
    """Dependency injection: compose service with its repository."""
    repo = AuthorizationRepository(db)
    return AuthorizationService(repo)


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List authorization summaries (COPAUS0C)",
    description=(
        "Paginated list of all authorization summaries. "
        "Replaces COPAUS0C IMS browse pattern (EXEC DLI GU PAUTSUM0). "
        "Default page_size=5 maps to COPAUS0C's 5 rows per screen."
    ),
)
async def list_authorization_summaries(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Items per page (max 5 for COBOL parity)")
    ] = 5,
    service: Annotated[AuthorizationService, Depends(get_auth_service)] = None,
    _current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> dict:
    """
    GET /api/v1/authorizations
    Accessible to all authenticated users (both admin 'A' and regular 'U').
    Replaces: COPAUS0C GATHER-DETAILS + PROCESS-PAGE-FORWARD (IMS browse loop).
    """
    return await service.list_authorization_summaries(page=page, page_size=page_size)


@router.get(
    "/{account_id}/details",
    response_model=AuthListResponse,
    summary="List authorization details for an account (COPAUS0C detail rows)",
    description=(
        "Paginated authorization detail list for a specific account. "
        "Replaces COPAUS0C IMS GNP PAUTDTL1 browse (5 per page). "
        "ORDER BY processed_at DESC replaces IMS inverted timestamp key."
    ),
)
async def list_details_for_account(
    account_id: int,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 5,
    service: Annotated[AuthorizationService, Depends(get_auth_service)] = None,
    _current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> AuthListResponse:
    """
    GET /api/v1/authorizations/{account_id}/details
    Returns summary header + paginated detail list for COPAU00 screen.
    Replaces: COPAUS0C PROCESS-PAGE-FORWARD loop + POPULATE-AUTH-LIST.
    """
    return await service.list_details_for_account(
        account_id=account_id, page=page, page_size=page_size
    )


@router.get(
    "/detail/{auth_id}",
    response_model=AuthDetailResponse,
    summary="Get single authorization detail (COPAUS1C)",
    description=(
        "Full detail view of a single authorization record. "
        "Replaces COPAUS1C POPULATE-AUTH-DETAILS paragraph. "
        "Resolves decline reason from inline table (WS-DECLINE-REASON-TABLE SEARCH ALL). "
        "AUTHMTC and AUTHFRD fields shown in RED on original COPAU01 screen."
    ),
)
async def get_authorization_detail(
    auth_id: int,
    service: Annotated[AuthorizationService, Depends(get_auth_service)] = None,
    _current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> AuthDetailResponse:
    """
    GET /api/v1/authorizations/detail/{auth_id}
    Replaces: COPAUS1C CPVD transaction, EXEC DLI GNP PAUTDTL1 WHERE(PAUT9CTS=key).
    """
    return await service.get_authorization_detail(auth_id=auth_id)


@router.put(
    "/detail/{auth_id}/fraud",
    response_model=FraudToggleResponse,
    summary="Toggle fraud flag (COPAUS1C PF5 → COPAUS2C)",
    description=(
        "Toggle the fraud status on an authorization detail record. "
        "3-state cycle: N→F (no fraud→fraud confirmed), F→R (remove flag), R→F (re-confirm). "
        "Replaces: COPAUS1C MARK-AUTH-FRAUD paragraph + EXEC CICS LINK COPAUS2C. "
        "Both the authorization_detail update (IMS REPL) and auth_fraud_log insert "
        "(DB2 INSERT AUTHFRDS) are atomic. Handles upsert for duplicate log entries "
        "(replaces COPAUS2C SQLCODE -803 → FRAUD-UPDATE). "
        "current_fraud_status validates client state matches DB to prevent double-toggle."
    ),
)
async def toggle_fraud_flag(
    auth_id: int,
    request: FraudToggleRequest,
    service: Annotated[AuthorizationService, Depends(get_auth_service)] = None,
    _current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> FraudToggleResponse:
    """
    PUT /api/v1/authorizations/detail/{auth_id}/fraud
    Replaces: COPAUS1C MARK-AUTH-FRAUD → COPAUS2C EXEC SQL INSERT/UPDATE + EXEC DLI REPL.
    Accessible to all authenticated users (admin 'A' and regular 'U').
    """
    return await service.toggle_fraud_flag(
        auth_id=auth_id,
        current_fraud_status=request.current_fraud_status,
    )


@router.get(
    "/detail/{auth_id}/fraud-logs",
    response_model=list[AuthFraudLogResponse],
    summary="Get fraud audit log for an authorization",
    description=(
        "Retrieve the immutable audit trail of fraud flag actions for an authorization. "
        "Maps to DB2 CARDDEMO.AUTHFRDS rows for the given auth_id."
    ),
)
async def get_fraud_logs(
    auth_id: int,
    service: Annotated[AuthorizationService, Depends(get_auth_service)] = None,
    _current_user: Annotated[dict, Depends(get_current_user)] = None,
) -> list[AuthFraudLogResponse]:
    """
    GET /api/v1/authorizations/detail/{auth_id}/fraud-logs
    Returns AUTHFRDS audit trail rows for the given authorization.
    """
    return await service.get_fraud_logs(auth_id=auth_id)
