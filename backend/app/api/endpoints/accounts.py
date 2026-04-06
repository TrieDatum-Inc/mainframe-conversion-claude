"""
Account API endpoints.

GET /api/v1/accounts/{account_id} → COACTVWC (view)
PUT /api/v1/accounts/{account_id} → COACTUPC (update)

Both endpoints require authentication (any user type — no admin restriction).
This is a thin controller layer — all business logic is in account_service.py.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.schemas.account import AccountUpdateRequest, AccountViewResponse
from app.services import account_service

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get(
    "/{account_id}",
    response_model=AccountViewResponse,
    summary="View account — COACTVWC",
    description=(
        "Fetch account + customer details for an account ID. "
        "Joins ACCTDAT + CUSTDAT via account_customer_xref. "
        "SSN is always masked in the response."
    ),
)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> AccountViewResponse:
    """COACTVWC: READ-ACCT-BY-ACCT-ID → READ-CUST-BY-CUST-ID."""
    return await account_service.view_account(account_id, db)


@router.put(
    "/{account_id}",
    response_model=AccountViewResponse,
    summary="Update account — COACTUPC",
    description=(
        "Update account and customer fields. "
        "Validates SSN ranges, FICO score 300-850, cash limit <= credit limit. "
        "Returns 422 if no fields changed (WS-DATACHANGED-FLAG='N')."
    ),
)
async def update_account(
    account_id: int,
    request: AccountUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
) -> AccountViewResponse:
    """COACTUPC: validate → REWRITE ACCTDAT + REWRITE CUSTDAT."""
    return await account_service.update_account(account_id, request, db)
