"""
Transaction endpoints — derived from COTRN00C, COTRN01C, COTRN02C, COBIL00C.

Source programs:
  app/cbl/COTRN00C.cbl — Transaction List (CICS transaction CT00)
  app/cbl/COTRN01C.cbl — Transaction View (CICS transaction CT01)
  app/cbl/COTRN02C.cbl — Transaction Add  (CICS transaction CT02)
  app/cbl/COBIL00C.cbl — Bill Payment     (CICS transaction CB00)

BMS maps: COTRN00, COTRN01, COTRN02, COBIL00

Endpoint mapping:
  GET  /api/v1/transactions          → COTRN00C (browse TRANSACT by TRAN-ID)
  GET  /api/v1/transactions/{id}     → COTRN01C (read single transaction)
  POST /api/v1/transactions          → COTRN02C (write new TRANSACT record)
  POST /api/v1/transactions/payment  → COBIL00C (payment + account balance update)
"""
from fastapi import APIRouter, Query

from app.dependencies import CurrentUser, DBSession
from app.schemas.transaction import (
    BillPaymentRequest,
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions (COTRN00C/01C/02C/COBIL00C)"])


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="Browse transactions (COTRN00C / CT00)",
    responses={
        200: {"description": "Paginated transaction list"},
    },
)
async def list_transactions(
    db: DBSession,
    current_user: CurrentUser,
    cursor: str | None = Query(None, description="Keyset cursor — last tran_id from previous page"),
    limit: int = Query(10, ge=1, le=100, description="Page size (COTRN00C: 10 rows per screen)"),
    card_num: str | None = Query(None, description="Filter by TRAN-CARD-NUM"),
    acct_id: int | None = Query(None, description="Filter by account ID"),
    direction: str = Query("forward", pattern="^(forward|backward)$", description="READNEXT or READPREV"),
) -> TransactionListResponse:
    """
    Browse transactions with keyset pagination.

    Derived from COTRN00C BROWSE-TRANSACTIONS paragraph:
      EXEC CICS STARTBR FILE('TRANSACT') RIDFLD(WS-TRAN-ID) GTEQ
      EXEC CICS READNEXT FILE('TRANSACT') INTO(TRAN-RECORD)

    CDEMO-CT00-TRNID-FIRST and CDEMO-CT00-TRNID-LAST track page position.
    CDEMO-CT00-PAGE-NUM tracks the page number.
    """
    service = TransactionService(db)
    return await service.list_transactions(
        cursor=cursor, limit=limit, card_num=card_num, acct_id=acct_id, direction=direction
    )


@router.get(
    "/{tran_id}",
    response_model=TransactionResponse,
    summary="View transaction details (COTRN01C / CT01)",
    responses={
        200: {"description": "Transaction details"},
        404: {"description": "Transaction not found (CICS RESP=13 NOTFND)"},
    },
)
async def get_transaction(
    tran_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> TransactionResponse:
    """
    Retrieve transaction details by transaction ID.

    Derived from COTRN01C READ-TRANSACTION paragraph:
      EXEC CICS READ FILE('TRANSACT') INTO(TRAN-RECORD) RIDFLD(WS-TRAN-ID)

    tran_id is TRAN-ID PIC X(16) — padded to exactly 16 characters.
    """
    service = TransactionService(db)
    return await service.get_transaction(tran_id)


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=201,
    summary="Create transaction (COTRN02C / CT02)",
    responses={
        201: {"description": "Transaction created"},
        404: {"description": "Card not found"},
        422: {"description": "Validation error (e.g., card inactive, zero amount)"},
    },
)
async def create_transaction(
    request: TransactionCreateRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> TransactionResponse:
    """
    Create a new transaction record.

    Derived from COTRN02C PROCESS-ENTER-KEY:
      1. Validate card exists and is ACTIVE (CARD-ACTIVE-STATUS = 'Y')
      2. Look up account via CCXREF (CBTRN01C: READ FILE('XREFFILE'))
      3. Generate TRAN-ID (COBIL00C: WS-TRAN-ID-NUM from ASKTIME)
      4. EXEC CICS WRITE FILE('TRANSACT') FROM(TRAN-RECORD)
    """
    service = TransactionService(db)
    return await service.create_transaction(request, current_user.sub)


@router.post(
    "/payment",
    response_model=TransactionResponse,
    status_code=201,
    summary="Process bill payment (COBIL00C / CB00)",
    responses={
        201: {"description": "Payment processed, balance updated"},
        404: {"description": "Account not found"},
        422: {"description": "Payment > balance or no card on file"},
    },
)
async def process_payment(
    request: BillPaymentRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> TransactionResponse:
    """
    Process a bill payment.

    Derived from COBIL00C PROCESS-PAYMENT paragraph:
      1. READ FILE('ACCTDAT') to get current balance
      2. Validate payment_amount <= ACCT-CURR-BAL
      3. STARTBR FILE('CXACAIX') RIDFLD(ACCT-ID) — find card for account
      4. EXEC CICS WRITE FILE('TRANSACT') — create payment transaction
      5. EXEC CICS REWRITE FILE('ACCTDAT') — reduce ACCT-CURR-BAL
         ACCT-CURR-BAL = ACCT-CURR-BAL - payment_amount
         ACCT-CURR-CYC-CREDIT = ACCT-CURR-CYC-CREDIT + payment_amount

    All arithmetic uses Python Decimal (COBOL COMP-3 equivalent).
    """
    service = TransactionService(db)
    return await service.process_bill_payment(request, current_user.sub)
