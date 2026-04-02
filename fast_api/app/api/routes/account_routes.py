"""
Account routes.
Maps COACTVWC (CAVW) and COACTUPC (CAUP) programs.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_user
from app.core.exceptions import BusinessValidationError, ResourceNotFoundError
from app.domain.services.account_service import (
    get_account_with_customer,
    update_account_with_customer,
)
from app.infrastructure.database import get_db
from app.schemas.account_schemas import (
    AccountWithCustomerUpdateRequest,
    AccountWithCustomerView,
)
from app.schemas.auth_schemas import UserContext

router = APIRouter(prefix="/accounts", tags=["Accounts (COACTVWC/COACTUPC)"])


@router.get(
    "/{acct_id}",
    response_model=AccountWithCustomerView,
    status_code=status.HTTP_200_OK,
    summary="View account (COACTVWC - CAVW)",
    description="""
    Read-only account + customer data display.

    Maps COACTVWC 9000-READ-ACCT:
    1. READ CXACAIX (alternate index by account ID) -> get cust_id + card_num
    2. READ ACCTDAT -> account data
    3. READ CUSTDAT -> customer data

    Validation:
    - Account ID must be a non-zero 11-digit number
    - Returns 'Did not find this account' if not found

    No updates are performed by this endpoint (COACTVWC is read-only).
    """,
)
async def get_account(
    acct_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> AccountWithCustomerView:
    try:
        return await get_account_with_customer(acct_id, db)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )


@router.put(
    "/{acct_id}",
    response_model=AccountWithCustomerView,
    status_code=status.HTTP_200_OK,
    summary="Update account (COACTUPC - CAUP)",
    description="""
    Update account and customer data atomically.

    Maps COACTUPC 6-state machine:
    - Read account+customer data
    - Validate 35+ fields
    - Confirm changes (F5 equivalent: confirm=true in body)
    - REWRITE ACCTDAT + REWRITE CUSTDAT atomically

    Business rules validated:
    - Active status: 'Y' or 'N'
    - Credit limits: non-negative; cash limit <= credit limit
    - Dates: valid YYYY-MM-DD; expiration >= open date
    - State codes: valid US 2-letter codes (CSLKPCDY table)
    - Phone: (999)999-9999 format
    - FICO: 300-850
    - DOB: must be in the past
    """,
)
async def update_account(
    acct_id: int,
    request: AccountWithCustomerUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserContext = Depends(require_user),
) -> AccountWithCustomerView:
    try:
        return await update_account_with_customer(
            acct_id, request.account, request.customer, db
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "CDERR013", "message": exc.message},
        )
    except BusinessValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "CDERR422", "message": exc.message, "field": exc.field},
        )
