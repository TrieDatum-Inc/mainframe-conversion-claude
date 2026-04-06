"""Account API routes.

Maps COBOL programs to REST endpoints:
  COACTVWC (GET /api/accounts/{id})          — view account details
  COACTUPC (PUT /api/accounts/{id})          — update account + customer
  COCRDLIC  (GET /api/accounts, with filters) — list/search accounts

All endpoints require JWT Bearer authentication (Depends(get_current_user)).
HTTP status code mapping:
  COBOL NOT-FOUND condition -> 404
  COBOL validation error    -> 422
  COBOL REWRITE ok          -> 200
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.account import (
    AccountDetailResponse,
    AccountListResponse,
    AccountUpdateRequest,
)
from app.services import account_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100),
    account_id: str | None = Query(default=None, description="Filter by account ID prefix"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> AccountListResponse:
    """List accounts with optional search by account_id.

    COBOL equivalent: COACTVWC BROWSE ACCTDAT with optional key filter.
    Returns paginated results for account list table.
    """
    return await account_service.list_accounts(
        db,
        page=page,
        page_size=page_size,
        account_id_filter=account_id,
    )


@router.get("/{account_id}", response_model=AccountDetailResponse)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> AccountDetailResponse:
    """Get full account detail including customer info and associated cards.

    COBOL COACTVWC flow:
      1. READ ACCTDAT by ACCT-ID
      2. READ CXACAIX to get CUST-ID
      3. READ CUSTDAT by CUST-ID
      4. BROWSE CARDAIX for cards

    Returns 404 if account not found (COBOL NOTFND condition).
    """
    detail = await account_service.get_account_detail(db, account_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id!r} not found",
        )
    return detail


@router.put("/{account_id}", response_model=AccountDetailResponse)
async def update_account(
    account_id: str,
    payload: AccountUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> AccountDetailResponse:
    """Update account and customer fields.

    COBOL COACTUPC PF5 save flow:
      1. READ ACCTDAT WITH UPDATE
      2. Validate all fields (phone, SSN, state, zip, dates, financials)
      3. REWRITE ACCTDAT
      4. READ CUSTDAT WITH UPDATE
      5. REWRITE CUSTDAT

    Validation errors (COBOL field-level highlights) -> HTTP 422.
    Account not found -> HTTP 404.
    """
    updated = await account_service.update_account(db, account_id, payload)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id!r} not found",
        )
    return updated
