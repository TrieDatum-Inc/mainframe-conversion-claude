"""Payments router — REST API endpoints for COBIL00C (Transaction CB00).

Endpoints:
  GET  /payments/balance/{acct_id}  — Look up account balance (Phase 1)
  POST /payments/{acct_id}          — Process bill payment (Phase 2, CONFIRM=Y)

COBIL00C two-phase interaction mapping:
  Phase 1 (SPACES in CONFIRM field):
    User enters account ID → GET /payments/balance/{acct_id} → display balance
  Phase 2 (CONFIRM = 'Y'):
    User confirms → POST /payments/{acct_id} → atomic payment + balance zero
    'N' → frontend cancels without calling API (CLEAR-CURRENT-SCREEN equivalent)
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.account_repository import AccountRepository
from app.repositories.card_cross_reference_repository import CardCrossReferenceRepository
from app.repositories.transaction_repository import TransactionRepository
from app.middleware.auth_middleware import get_current_user_info
from app.schemas.auth import UserInfo
from app.schemas.payments import AccountBalanceResponse, PaymentResponse
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Bill Payment (COBIL00C / CB00)"])


def _get_payment_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentService:
    """Dependency injection for PaymentService."""
    return PaymentService(
        account_repo=AccountRepository(db),
        xref_repo=CardCrossReferenceRepository(db),
        transaction_repo=TransactionRepository(db),
    )


@router.get(
    "/balance/{acct_id}",
    response_model=AccountBalanceResponse,
    summary="Look up account balance (COBIL00C Phase 1 / READ-ACCTDAT-FILE)",
    description=(
        "Fetches the current account balance for display. "
        "Maps COBIL00C READ-ACCTDAT-FILE + balance display (lines 184-196). "
        "No payment occurs. User sees balance and then decides whether to confirm payment."
    ),
)
async def get_account_balance(
    acct_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user_info)],
    service: Annotated[PaymentService, Depends(_get_payment_service)],
) -> AccountBalanceResponse:
    """Phase 1: Look up account and return current balance.

    COBIL00C EVALUATE CONFIRMI WHEN SPACES → READ-ACCTDAT-FILE, display balance.
    """
    return await service.get_account_balance(acct_id)


@router.post(
    "/{acct_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process bill payment (COBIL00C Phase 2 / CONFIRM=Y)",
    description=(
        "Processes a full balance payment for the specified account. "
        "Maps COBIL00C CONF-PAY-YES path (lines 208-240). "
        "\n\n**Atomic operations (single DB transaction):**\n"
        "1. Read account + validate positive balance\n"
        "2. Read card cross-reference → get card number\n"
        "3. Generate next transaction ID (MAX tran_id + 1)\n"
        "4. Write new payment transaction (type '02', full balance)\n"
        "5. Zero account balance (REWRITE ACCTDAT)\n"
        "\n**CONFIRM=Y** is implied by the user submitting this request."
    ),
)
async def process_payment(
    acct_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user_info)],
    service: Annotated[PaymentService, Depends(_get_payment_service)],
) -> PaymentResponse:
    """Phase 2: Process the full balance payment.

    COBIL00C EVALUATE CONFIRMI WHEN 'Y' → CONF-PAY-YES = TRUE → payment processing.
    The get_db() dependency auto-commits on success and rolls back on exception,
    ensuring atomicity of the transaction write + balance zero operations.
    """
    return await service.process_payment(acct_id)
