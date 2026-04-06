"""
Account API endpoints.

COBOL origin:
  GET /api/v1/accounts/{account_id} → COACTVWC (account + customer view)
  PUT /api/v1/accounts/{account_id} → COACTUPC (account + customer update)

Both endpoints are accessible to ALL authenticated users (user_type A or U).
Authentication is required (get_current_user dependency); no admin-only restriction.

This is a thin controller layer — all business logic is in account_service.py.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.account import AccountUpdateRequest, AccountViewResponse
from app.services import account_service
from app.api.dependencies import CurrentUser, get_current_user

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get(
    "/{account_id}",
    response_model=AccountViewResponse,
    summary="View account with customer details",
    description=(
        "Fetch account + customer details for a given 11-digit account ID. "
        "Replaces COACTVWC (READ ACCTDAT + READ CUSTDAT + READ CARDAIX). "
        "Accessible to all authenticated users."
    ),
)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> AccountViewResponse:
    """
    GET /api/v1/accounts/{account_id}

    COBOL: COACTVWC READ-ACCT-BY-ACCT-ID → READ-CUST-BY-CUST-ID.
    Joins three data sources: accounts + customers (via xref) + card_account_xref.

    Returns 404 if account or customer not found.
    """
    return await account_service.view_account(account_id=account_id, db=db)


@router.put(
    "/{account_id}",
    response_model=AccountViewResponse,
    summary="Update account and customer fields",
    description=(
        "Update all editable account and customer fields. "
        "Replaces COACTUPC (15+ validation rules + UPDATE ACCTDAT + REWRITE CUSTDAT). "
        "Returns 404 if not found, 422 if validation fails or no changes detected."
    ),
)
async def update_account(
    account_id: int,
    request: AccountUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> AccountViewResponse:
    """
    PUT /api/v1/accounts/{account_id}

    COBOL: COACTUPC PROCESS-ENTER-KEY → VALIDATE-INPUT-FIELDS → UPDATE-ACCOUNT-INFO.
    Pydantic schema validates all field-level rules (15+ from COACTUPC).
    Service layer checks no-changes condition and executes the updates.

    Returns updated AccountViewResponse (account + customer + masked SSN).
    """
    return await account_service.update_account(
        account_id=account_id,
        request=request,
        db=db,
    )
