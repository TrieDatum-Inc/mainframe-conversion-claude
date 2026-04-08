"""
Account endpoints — derived from COACTVWC, COACTUPC, and COBIL00C.

Source programs:
  app/cbl/COACTVWC.cbl — Account View (CICS transaction CA0V)
  app/cbl/COACTUPC.cbl — Account Update (CICS transaction CA0U)
  app/cbl/COBIL00C.cbl — Bill Payment (CICS transaction CB00)

BMS maps: COACTUP, COBIL00

Endpoint mapping:
  GET  /api/v1/accounts/{id}          → COACTVWC (read + join CUSTDAT/CCXREF)
  PUT  /api/v1/accounts/{id}          → COACTUPC (validate + rewrite)
  POST /api/v1/accounts/{id}/payments → COBIL00C (bill payment — account-centric path)
"""
from fastapi import APIRouter

from app.dependencies import AdminUser, CurrentUser, DBSession
from app.schemas.account import AccountDetailResponse, AccountResponse, AccountUpdateRequest
from app.schemas.transaction import AccountPaymentRequest, BillPaymentRequest, TransactionResponse
from app.services.account_service import AccountService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/accounts", tags=["Accounts (COACTVWC/COACTUPC)"])


@router.get(
    "/{acct_id}",
    response_model=AccountDetailResponse,
    summary="View account details (COACTVWC)",
    responses={
        200: {"description": "Account details with customer info"},
        404: {"description": "Account not found (CICS RESP=13 NOTFND)"},
    },
)
async def get_account(
    acct_id: int,
    db: DBSession,
    current_user: CurrentUser,
) -> AccountDetailResponse:
    """
    Retrieve account details.

    Derived from COACTVWC READ-PROCESSING paragraph:
      1. EXEC CICS READ FILE('ACCTDAT') INTO(ACCOUNT-RECORD) RIDFLD(WS-ACCT-ID)
      2. STARTBR FILE('CXACAIX') RIDFLD(WS-ACCT-ID) → get customer ID
      3. EXEC CICS READ FILE('CUSTDAT') INTO(CUSTOMER-RECORD) RIDFLD(CUST-ID)

    Returns account fields plus customer name/ID from the CCXREF join.
    Any authenticated user can view account details.
    """
    service = AccountService(db)
    return await service.get_account(acct_id)


@router.put(
    "/{acct_id}",
    response_model=AccountResponse,
    summary="Update account (COACTUPC)",
    responses={
        200: {"description": "Account updated successfully"},
        403: {"description": "Non-admin attempting to change group_id"},
        404: {"description": "Account not found (CICS RESP=13 NOTFND)"},
        422: {"description": "Validation error"},
    },
)
async def update_account(
    acct_id: int,
    request: AccountUpdateRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> AccountResponse:
    """
    Update account fields.

    Derived from COACTUPC PROCESS-ENTER-KEY → VALIDATE-INPUT-FIELDS →
    CHECK-CHANGE-IN-REC → EXEC CICS REWRITE FILE('ACCTDAT').

    Business rules (COACTUPC):
      - Only admin users (user_type='A') can change group_id
      - All monetary fields maintain Decimal precision (COMP-3)
      - ZIP code format validated
      - Read-then-rewrite pattern (CICS requirement)

    Any authenticated user can update non-restricted fields.
    Admin-only field: group_id (ACCT-GROUP-ID).
    """
    service = AccountService(db)
    is_admin = current_user.role == "A"
    return await service.update_account(acct_id, request, is_admin)


@router.post(
    "/{acct_id}/payments",
    response_model=TransactionResponse,
    status_code=201,
    summary="Process bill payment (COBIL00C / CB00)",
    responses={
        201: {"description": "Payment processed, account balance updated"},
        404: {"description": "Account not found (CICS RESP=13 NOTFND on ACCTDAT)"},
        422: {
            "description": (
                "Payment validation failed — amount exceeds balance, "
                "or no card on file (COBIL00C: 'You have nothing to pay...')"
            )
        },
    },
)
async def process_account_payment(
    acct_id: int,
    request: AccountPaymentRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> TransactionResponse:
    """
    Process a bill payment for a specific account.

    Account-centric path for COBIL00C PROCESS-PAYMENT paragraph:

    COBOL:
      1. EXEC CICS READ FILE('ACCTDAT') INTO(ACCOUNT-RECORD) RIDFLD(ACCT-ID) UPDATE
         → Verify account exists and lock for update
      2. IF ACCT-CURR-BAL <= ZEROS → 'You have nothing to pay...'
      3. IF CONFIRMI = 'Y' → proceed with payment
      4. READ FILE('CXACAIX') RIDFLD(ACCT-ID) → get card number (XREF-CARD-NUM)
      5. STARTBR FILE('TRANSACT') / READPREV / ENDBR → get last TRAN-ID
      6. ADD 1 TO WS-TRAN-ID-NUM → generate next TRAN-ID
      7. WRITE FILE('TRANSACT') — create payment transaction:
           TRAN-TYPE-CD = '02' (bill payment)
           TRAN-CAT-CD  = 2
           TRAN-SOURCE  = 'POS TERM'
           TRAN-DESC    = 'BILL PAYMENT - ONLINE'
           TRAN-AMT     = ACCT-CURR-BAL (full balance)
           TRAN-MERCHANT-ID   = 999999999
           TRAN-MERCHANT-NAME = 'BILL PAYMENT'
      8. COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT
      9. REWRITE FILE('ACCTDAT') — update account balance

    The acct_id in the URL path is used as the target account.
    The request body carries only payment_amount (and optional description);
    account_id is taken from the path parameter — no account_id in the body.
    All arithmetic uses Python Decimal (COBOL COMP-3 equivalent).
    """
    # Combine path acct_id with the body-only AccountPaymentRequest
    # to form the full BillPaymentRequest that the service expects.
    payment_request = BillPaymentRequest(
        account_id=acct_id,
        payment_amount=request.payment_amount,
        description=request.description,
    )
    service = TransactionService(db)
    return await service.process_bill_payment(payment_request, current_user.sub)
