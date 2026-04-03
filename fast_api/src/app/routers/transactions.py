"""
Transaction Processing API Router.

Maps CICS transactions to REST endpoints:
  CT00 (COTRN00C) → GET  /api/transactions
  CT01 (COTRN01C) → GET  /api/transactions/{tran_id}
  CT02 (COTRN02C) → POST /api/transactions/validate
                    POST /api/transactions
                    GET  /api/transactions/copy-last
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.transaction import (
    TransactionCreate,
    TransactionDetail,
    TransactionListResponse,
    TransactionValidateRequest,
    TransactionValidateResponse,
)
from app.services.transaction_service import TransactionService
from app.utils.exceptions import (
    AccountInactiveError,
    AccountNotFoundError,
    CardNotFoundError,
    DuplicateTransactionError,
    TransactionNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def get_service(session: Annotated[AsyncSession, Depends(get_db)]) -> TransactionService:
    return TransactionService(session)


# ---------------------------------------------------------------------------
# CT00 equivalent: paginated transaction list
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List transactions (paginated)",
    description=(
        "Paginated browse of transaction records. "
        "Mirrors COTRN00C / CT00 (PROCESS-PAGE-FORWARD / PROCESS-PAGE-BACKWARD). "
        "Use start_tran_id to jump to a specific position (like COTRN00C Search Tran ID). "
        "Use direction='backward' with anchor_tran_id for PF7 backward paging."
    ),
)
async def list_transactions(
    service: Annotated[TransactionService, Depends(get_service)],
    page: Annotated[int, Query(ge=1, description="Current page number")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Records per page (COBOL default: 10)")
    ] = 10,
    start_tran_id: Annotated[
        str | None,
        Query(
            description="Starting transaction ID for search/filter (TRNIDINI field). "
            "Must be numeric if provided.",
            max_length=16,
        ),
    ] = None,
    direction: Annotated[
        str,
        Query(
            description="Pagination direction: 'forward' (PF8) or 'backward' (PF7)",
            pattern="^(forward|backward)$",
        ),
    ] = "forward",
    anchor_tran_id: Annotated[
        str | None,
        Query(
            description="Last tran ID of current page; used when direction='backward'",
            max_length=16,
        ),
    ] = None,
) -> TransactionListResponse:
    if start_tran_id and not start_tran_id.strip().isdigit():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tran ID must be Numeric",
        )
    if direction == "backward" and page <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already at the top of the page",
        )
    return await service.list_transactions(
        page=page,
        page_size=page_size,
        start_tran_id=start_tran_id,
        direction=direction,
        anchor_tran_id=anchor_tran_id,
    )


# ---------------------------------------------------------------------------
# CT02 equivalent: copy last transaction (PF5) — must be before /{tran_id}
# ---------------------------------------------------------------------------

@router.get(
    "/copy-last",
    response_model=TransactionDetail,
    summary="Copy last transaction data (PF5 equivalent)",
    description=(
        "Fetches the most recent transaction record for pre-filling the Add Transaction form. "
        "Mirrors COPY-LAST-TRAN-DATA in COTRN02C. "
        "Either card_num or acct_id must be provided."
    ),
)
async def copy_last_transaction(
    service: Annotated[TransactionService, Depends(get_service)],
    card_num: Annotated[str | None, Query(max_length=16)] = None,
    acct_id: Annotated[str | None, Query(max_length=11)] = None,
) -> TransactionDetail:
    try:
        return await service.get_last_transaction_data(card_num, acct_id)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


# ---------------------------------------------------------------------------
# CT01 equivalent: transaction detail view
# ---------------------------------------------------------------------------

@router.get(
    "/{tran_id}",
    response_model=TransactionDetail,
    summary="View transaction detail",
    description=(
        "Read-only detail view of a single transaction. "
        "Mirrors COTRN01C / CT01 (READ-TRANSACT-FILE). "
        "No update locking is applied (the COBOL UPDATE option was an anomaly)."
    ),
)
async def get_transaction(
    tran_id: str,
    service: Annotated[TransactionService, Depends(get_service)],
) -> TransactionDetail:
    try:
        return await service.get_transaction(tran_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


# ---------------------------------------------------------------------------
# CT02 equivalent step 1: validate (enter data phase)
# ---------------------------------------------------------------------------

@router.post(
    "/validate",
    response_model=TransactionValidateResponse,
    summary="Validate transaction input (step 1 of 2)",
    description=(
        "Validates all transaction fields and resolves card/account cross-reference. "
        "Mirrors COTRN02C VALIDATE-INPUT-KEY-FIELDS + VALIDATE-INPUT-DATA-FIELDS. "
        "Returns resolved card number, account ID, account active status, and normalized amount. "
        "The UI uses this response to render the confirmation screen."
    ),
)
async def validate_transaction(
    request: TransactionValidateRequest,
    service: Annotated[TransactionService, Depends(get_service)],
) -> TransactionValidateResponse:
    try:
        return await service.validate_transaction_input(request)
    except CardNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except AccountNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except AccountInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


# ---------------------------------------------------------------------------
# CT02 equivalent step 2: create transaction (confirmed)
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=TransactionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Add new transaction (step 2 of 2 — confirmed)",
    description=(
        "Creates a new transaction record after user confirmation (confirm='Y'). "
        "Mirrors COTRN02C ADD-TRANSACTION + WRITE-TRANSACT-FILE. "
        "Auto-generates transaction ID by reading the last record and incrementing. "
        "Processing timestamp is set at creation time (mirrors EXEC CICS ASKTIME/FORMATTIME). "
        "Returns the created transaction including the auto-generated ID."
    ),
)
async def create_transaction(
    request: TransactionCreate,
    service: Annotated[TransactionService, Depends(get_service)],
) -> TransactionDetail:
    try:
        return await service.add_transaction(request)
    except CardNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except AccountNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except AccountInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except DuplicateTransactionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
