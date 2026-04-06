"""Bill payment API routes — thin controller layer.

Maps CICS CB00 (COBIL00C) to REST endpoints:
  GET  /api/bill-payment/preview/{account_id} — preview balance (CURBAL display)
  POST /api/bill-payment                       — process payment (CONFIRM='Y')
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import User, get_current_user
from app.schemas.bill_payment import BillPaymentPreview, BillPaymentRequest, BillPaymentResult
from app.services.bill_payment_service import BillPaymentService

router = APIRouter(prefix="/api/bill-payment", tags=["bill-payment"])


@router.get(
    "/preview/{account_id}",
    response_model=BillPaymentPreview,
    summary="Preview bill payment — show current balance (CB00 / COBIL00C)",
)
async def preview_payment(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillPaymentPreview:
    """Fetch current account balance for display before confirmation.

    Mirrors COBIL00C first screen interaction:
      READ ACCTDAT → display CURBAL
      If balance <= 0 → can_pay=false, message='You have nothing to pay'
    """
    service = BillPaymentService(db)
    return await service.preview_payment(account_id)


@router.post(
    "",
    response_model=BillPaymentResult,
    summary="Process bill payment (CB00 / COBIL00C)",
)
async def process_payment(
    request: BillPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillPaymentResult:
    """Process a full bill payment for the account.

    Mirrors COBIL00C CONFIRM='Y' flow:
    - Reads full account balance (always full, no partial payments)
    - Creates transaction: type='02', category=2, merchant_id='999999999'
    - Sets account balance to 0
    - Returns transaction ID and payment details

    If confirmed=false, returns a preview without processing.
    If balance <= 0, returns HTTP 422 'You have nothing to pay'.
    """
    service = BillPaymentService(db)
    return await service.process_payment(request)
