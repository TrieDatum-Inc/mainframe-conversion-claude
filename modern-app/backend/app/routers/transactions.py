"""Transaction API routes — thin controller layer.

Maps CICS transaction IDs to REST endpoints:
  CT00 (COTRN00C) → GET  /api/transactions
  CT01 (COTRN01C) → GET  /api/transactions/{transaction_id}
  CT02 (COTRN02C) → POST /api/transactions
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import User, get_current_user
from app.schemas.transaction import TransactionCreate, TransactionDetail, TransactionPage
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=TransactionPage, summary="List transactions (CT00 / COTRN00C)")
async def list_transactions(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Rows per page (default 10)"),
    transaction_id: str | None = Query(default=None, description="Prefix search on transaction ID (TRNIDIN field)"),
    card_number: str | None = Query(default=None, description="Filter by card number"),
    account_id: str | None = Query(default=None, description="Filter by account ID"),
    start_date: date | None = Query(default=None, description="Filter: original date >= start_date (YYYY-MM-DD)"),
    end_date: date | None = Query(default=None, description="Filter: original date <= end_date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionPage:
    """Paginated transaction list with optional filters.

    Mirrors COTRN00C: 10 transactions per page, sorted by transaction ID descending.
    The transaction_id parameter performs a prefix match (STARTBR behavior).
    """
    service = TransactionService(db)
    return await service.list_transactions(
        page=page,
        page_size=page_size,
        transaction_id_prefix=transaction_id,
        card_number=card_number,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionDetail,
    summary="View transaction detail (CT01 / COTRN01C)",
)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionDetail:
    """Fetch full detail for a single transaction by ID.

    Mirrors COTRN01C: READ TRANSACT by TRAN-ID, display all 13 output fields.
    Returns HTTP 404 if not found (COBOL NOTFND condition).
    """
    service = TransactionService(db)
    return await service.get_transaction(transaction_id)


@router.post(
    "",
    response_model=TransactionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Add transaction (CT02 / COTRN02C)",
)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionDetail:
    """Create a new transaction record.

    Mirrors COTRN02C:
    - Either account_id OR card_number required (other resolved via xref)
    - Amount in range -99999999.99 to +99999999.99
    - Merchant ID must be all numeric
    - confirmed=true required to actually write (COBOL CONFIRM='Y')
    - transaction_id is auto-generated (max existing + 1)

    Returns HTTP 422 if confirmed=false (validation only, no write performed).
    """
    service = TransactionService(db)

    card_number, account_id = await _resolve_card_and_account(service, payload)

    if not payload.confirmed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Transaction validated but not committed. Set confirmed=true to commit.",
                "account_id": account_id,
                "card_number": card_number,
            },
        )

    return await service.create_transaction(payload, card_number, account_id)


async def _resolve_card_and_account(
    service: TransactionService, payload: TransactionCreate
) -> tuple[str, str]:
    """Resolve both card_number and account_id from whichever was provided.

    COBOL: if ACTIDIN provided → READ CXACAIX to get card.
           if CARDNIN provided → READ CCXREF to get account.
    """
    if payload.card_number and not payload.account_id:
        account_id = await service.resolve_account_from_card(payload.card_number)
        card_number = payload.card_number
    elif payload.account_id and not payload.card_number:
        card_number = await service.resolve_card_from_account(payload.account_id)
        account_id = payload.account_id
    else:
        card_number = payload.card_number  # type: ignore[assignment]
        account_id = payload.account_id  # type: ignore[assignment]
    return card_number, account_id
