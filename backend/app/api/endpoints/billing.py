"""
FastAPI endpoints for Billing (bill payment) operations.

COBOL origin: COBIL00C — Online Bill Payment (Transaction: CB00).

Two-phase pattern:
  GET  /api/v1/billing/{account_id}/balance  → Phase 1 (display balance)
  POST /api/v1/billing/{account_id}/payment  → Phase 2 (confirm and execute payment)

Both phases require authentication. No admin restriction (COBIL00C accessible from COMEN01C).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.billing import (
    BillingBalanceResponse,
    BillPaymentRequest,
    BillPaymentResponse,
)
from app.services.billing_service import BillingService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get(
    "/{account_id}/balance",
    response_model=BillingBalanceResponse,
    summary="Get account balance (COBIL00C Phase 1)",
    description=(
        "Display current account balance before payment confirmation. "
        "COBIL00C: READ-ACCTDAT-FILE when CONFIRMI=SPACES → display ACCT-CURR-BAL as CURBAL. "
        "No side effects — read-only (unlike COBIL00C which used READ UPDATE even here)."
    ),
)
async def get_balance(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> BillingBalanceResponse:
    """
    Phase 1: Retrieve account balance for display.

    COBOL origin: COBIL00C READ-ACCTDAT-FILE path when CONFIRMI=SPACES/LOW-VALUES.
    Displays ACCT-CURR-BAL on COBIL0A screen as CURBAL.

    ACTIDINI blank → ValidationError (COBIL00C: 'Acct ID can NOT be empty...').
    ACCTDAT NOTFND → 404 AccountNotFoundError (COBIL00C: 'Account ID NOT found...').
    """
    service = BillingService(db)
    return await service.get_balance(account_id)


@router.post(
    "/{account_id}/payment",
    response_model=BillPaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Process bill payment (COBIL00C Phase 2)",
    description=(
        "Execute bill payment after user confirmation. "
        "COBIL00C CONF-PAY-YES path: READ CXACAIX → generate transaction ID → "
        "WRITE TRANSACT → REWRITE ACCTDAT (balance = 0). "
        "confirm='Y' required. "
        "Transaction ID generated via sequence (fixes COBIL00C STARTBR/READPREV race condition)."
    ),
)
async def process_payment(
    account_id: int,
    request: BillPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> BillPaymentResponse:
    """
    Phase 2: Execute bill payment.

    COBOL origin: COBIL00C PROCESS-ENTER-KEY when CONFIRMI='Y':
      1. READ ACCTDAT with UPDATE lock (SELECT FOR UPDATE in modern)
      2. IF ACCT-CURR-BAL <= 0: NothingToPayError
      3. READ CXACAIX → card number
      4. Generate transaction ID (sequence, not STARTBR/READPREV)
      5. WRITE TRANSACT (payment transaction with hardcoded attributes)
      6. COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT (= 0)
      7. REWRITE ACCTDAT

    Success message: 'Payment successful. Your Transaction ID is [N].'
    (COBIL00C: ERRMSGO with DFHGREEN color on success).

    ACCT-CURR-BAL <= 0 → 422 NothingToPayError.
    CXACAIX NOTFND → 404 CardNotFoundError.
    """
    service = BillingService(db)
    return await service.process_payment(account_id, request)
