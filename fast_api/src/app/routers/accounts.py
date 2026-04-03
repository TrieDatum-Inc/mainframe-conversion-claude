"""Account Management API routes.

Endpoints:
  GET  /api/accounts/{acct_id}  — COACTVWC (Account View, read-only)
  PUT  /api/accounts/{acct_id}  — COACTUPC (Account Update)

Account ID validation mirrors COACTVWC 2210-EDIT-ACCOUNT:
  - Must be 1-11 digits
  - Must be numeric and non-zero
  - Is zero-padded to 11 digits before lookup
"""

import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.account_repository import AccountRepository
from app.schemas.account import (
    AccountDetailResponse,
    AccountUpdateRequest,
    AccountUpdateResponse,
    AccountViewResponse,
)
from app.services.account_service import AccountService
from app.utils.exceptions import (
    AccountNotFoundError,
    ConcurrentModificationError,
    CustomerNotFoundError,
    LockAcquisitionError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def _validate_acct_id(acct_id: str) -> str:
    """Validate account ID per COACTVWC 2210-EDIT-ACCOUNT rules.

    Rules:
    1. Must not be blank (WS-PROMPT-FOR-ACCT).
    2. Must be numeric (FLG-ACCTFILTER-NOT-OK).
    3. Must not be all zeros (SEARCHED-ACCT-ZEROES).
    4. Maximum 11 digits.
    """
    if not acct_id or acct_id.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account number not provided",
        )
    if not re.match(r"^\d{1,11}$", acct_id.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account Filter must be a non-zero 11 digit number",
        )
    if acct_id.strip().lstrip("0") == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account number must be a non zero 11 digit number",
        )
    return acct_id.strip()


def _get_service(db: AsyncSession = Depends(get_db)) -> AccountService:
    """Dependency factory: creates repository + service for the request."""
    repo = AccountRepository(db)
    return AccountService(repo)


@router.get(
    "/{acct_id}",
    response_model=AccountDetailResponse,
    summary="View account details (COACTVWC)",
    description=(
        "Retrieves account master, linked customer, and cards for the given account ID. "
        "Read-only. Equivalent to COBOL transaction CAVW."
    ),
    responses={
        200: {"description": "Account found with full detail"},
        400: {"description": "Invalid account ID format"},
        404: {"description": "Account not found"},
    },
)
async def get_account(
    acct_id: str = Path(description="Account ID (1-11 digits)"),
    service: AccountService = Depends(_get_service),
) -> AccountDetailResponse:
    """COACTVWC: Account View endpoint.

    Replicates COACTVWC 9000-READ-ACCT:
    - 9200-GETCARDXREF-BYACCT: cross-reference lookup
    - 9300-GETACCTDATA-BYACCT: account master read
    - 9400-GETCUSTDATA-BYCUST: customer master read
    """
    _validate_acct_id(acct_id)

    try:
        result = await service.get_account_view(acct_id)
        return AccountDetailResponse(**result.model_dump())
    except AccountNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except CustomerNotFoundError as exc:
        # Per COACTVWC spec: "If customer not found, account data shown without customer"
        # We still return 200 with customer=None; this is handled in the service.
        # This branch handles unexpected errors only.
        logger.warning("Customer lookup failed: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc


@router.put(
    "/{acct_id}",
    response_model=AccountUpdateResponse,
    summary="Update account and customer (COACTUPC)",
    description=(
        "Updates account and linked customer records atomically. "
        "Uses optimistic concurrency control via updated_at timestamp. "
        "Equivalent to COBOL transaction CAUP (F5=Save phase)."
    ),
    responses={
        200: {"description": "Changes committed to database"},
        400: {"description": "Validation error"},
        404: {"description": "Account or customer not found"},
        409: {"description": "Record changed by another user (concurrent modification)"},
        423: {"description": "Record lock could not be acquired"},
    },
)
async def update_account(
    acct_id: str = Path(description="Account ID (1-11 digits)"),
    request: AccountUpdateRequest = ...,
    service: AccountService = Depends(_get_service),
) -> AccountUpdateResponse:
    """COACTUPC: Account Update endpoint.

    Implements the save phase of COACTUPC 9600-WRITE-PROCESSING:
    - Acquires row-level locks (EXEC CICS READ...UPDATE)
    - Checks optimistic concurrency (9700-CHECK-CHANGE-IN-REC)
    - Applies account + customer updates (EXEC CICS REWRITE)
    - Rolls back on failure (EXEC CICS SYNCPOINT ROLLBACK)
    """
    _validate_acct_id(acct_id)

    try:
        return await service.update_account(acct_id, request)
    except AccountNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except ConcurrentModificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from exc
    except LockAcquisitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=exc.message,
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error updating account %s", acct_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update of record failed",
        ) from exc
