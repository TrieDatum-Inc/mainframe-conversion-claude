"""Bill payment router porting COBOL program COBIL00C.

COBIL00C handles the bill payment screen which accepts an account ID,
displays the current balance, and processes payment with a two-step
confirm flow (preview then confirm with flag 'Y'). The program reads
from ACCTDAT, computes the payment, and writes a transaction to TRANSACT.

This router replaces that screen with a REST endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.bill_payment import BillPaymentRequest, BillPaymentResponse
from app.services import bill_payment_service

router = APIRouter(tags=["bill-payment"])


@router.post("/", response_model=BillPaymentResponse)
def process_bill_payment(
    body: BillPaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> BillPaymentResponse:
    """Process a bill payment for an account.

    Ports COBOL program COBIL00C which handles the bill pay screen with
    a two-step confirm flow. When confirm='N', returns a preview with
    current balance. When confirm='Y', processes the payment, generates
    a transaction record, and updates the account balance.
    """
    return bill_payment_service.process_bill_payment(db, body.acct_id, body.confirm)
