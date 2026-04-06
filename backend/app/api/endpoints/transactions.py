"""
FastAPI endpoints for Transaction operations.

COBOL origin:
  COTRN00C → GET /api/v1/transactions (list/browse)
  COTRN01C → GET /api/v1/transactions/{transaction_id} (detail view)
  COTRN02C → POST /api/v1/transactions (add new transaction)

All endpoints require authentication (replaces CICS EIBCALEN=0 check).
Both admin (type='A') and regular (type='U') users may access these endpoints.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.transaction import (
    TransactionCreateRequest,
    TransactionDetailResponse,
    TransactionListResponse,
)
from app.services.transaction_service import TransactionService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List transactions (COTRN00C)",
    description=(
        "Paginated transaction list with optional filters. "
        "COTRN00C POPULATE-TRAN-DATA: 10 rows per page, "
        "STARTBR/READNEXT/READPREV replaced by SQL pagination."
    ),
)
async def list_transactions(
    page: int = Query(default=1, ge=1, description="Page number (CDEMO-CT00-PAGE-NUM)"),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Rows per page (COTRN00C: fixed 10; modern: configurable)",
    ),
    tran_id_filter: Optional[str] = Query(
        default=None,
        max_length=16,
        description="TRNIDINI — filter to transactions with ID >= this value (STARTBR key)",
    ),
    card_number: Optional[str] = Query(
        default=None,
        description="Filter by card number",
    ),
    account_id: Optional[int] = Query(
        default=None,
        description="Filter by account ID (via card_account_xref join)",
    ),
    start_date: Optional[date] = Query(
        default=None,
        description="Filter original_date >= start_date",
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Filter original_date <= end_date",
    ),
    type_code: Optional[str] = Query(
        default=None,
        max_length=2,
        description="Filter by transaction type code",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TransactionListResponse:
    """
    List transactions with pagination.

    COBOL origin: COTRN00C POPULATE-TRAN-DATA paragraph.
      - 10 rows per page (COTRN0A BMS map)
      - Optional TRNIDINI filter (STARTBR key = WHERE id >= filter)
      - CDEMO-CT00-NEXT-PAGE-FLG → has_next
      - CDEMO-CT00-TRNID-FIRST/LAST → first_item_key/last_item_key

    Access: all authenticated users (no admin restriction in COTRN00C).
    """
    service = TransactionService(db)
    return await service.list_transactions(
        page=page,
        page_size=page_size,
        tran_id_filter=tran_id_filter,
        card_number=card_number,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        type_code=type_code,
    )


@router.get(
    "/last",
    response_model=Optional[TransactionDetailResponse],
    summary="Get last created transaction (COTRN02C PF5)",
    description=(
        "Returns the most recently created transaction for PF5 copy-last-transaction feature. "
        "COTRN02C PF5 COPY-LAST-TRAN-DATA: copies WS-LAST-TRAN-* fields to screen."
    ),
)
async def get_last_transaction(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Optional[TransactionDetailResponse]:
    """
    Get the most recently created transaction.

    COBOL origin: COTRN02C PF5 COPY-LAST-TRAN-DATA paragraph.
    Pre-populates all form fields from the last submitted transaction.
    """
    service = TransactionService(db)
    return await service.get_last_transaction()


@router.get(
    "/{transaction_id}",
    response_model=TransactionDetailResponse,
    summary="Get transaction detail (COTRN01C)",
    description=(
        "Retrieve full transaction detail by ID. "
        "COTRN01C BUG FIX: original issued READ UPDATE (exclusive lock) for display-only; "
        "this endpoint uses plain SELECT."
    ),
)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TransactionDetailResponse:
    """
    Get transaction detail by ID.

    COBOL origin: COTRN01C PROCESS-ENTER-KEY → READ-TRANS-FILE.

    BUG FIX documented: COTRN01C used READ UPDATE for display-only operation.
    This endpoint uses GET (SELECT without lock) as the spec recommends.

    RESP=NOTFND → 404 TransactionNotFoundError.
    """
    service = TransactionService(db)
    return await service.get_transaction(transaction_id)


@router.post(
    "",
    response_model=TransactionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add new transaction (COTRN02C)",
    description=(
        "Create a new transaction record. "
        "COTRN02C: account_id XOR card_number required; "
        "transaction_id generated via PostgreSQL sequence (fixes STARTBR/READPREV race condition). "
        "confirm='Y' required."
    ),
)
async def create_transaction(
    request: TransactionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TransactionDetailResponse:
    """
    Create a new transaction.

    COBOL origin: COTRN02C ADD-TRANSACTION paragraph.

    Key differences from COTRN02C:
      - transaction_id generated via NEXTVAL('transaction_id_seq') — no race condition
      - account_id XOR card_number: mutually exclusive validation in schema
      - confirm='Y' enforced at schema level (Literal['Y'])
      - amount != 0 enforced at schema level
      - processed_date >= original_date enforced at schema level

    WRITE RESP=DUPKEY is impossible with sequence-generated IDs.
    WRITE RESP=OTHER → 500 Internal Server Error.
    """
    service = TransactionService(db)
    return await service.create_transaction(request)
