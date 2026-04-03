"""Bill Payment service — business logic for COBIL00C (Transaction CB00).

All COBOL paragraph logic from PROCESS-ENTER-KEY is preserved here.
The entire payment operation (transaction write + balance zero) is
executed in a single database transaction for atomicity.

COBOL source: app/cbl/COBIL00C.cbl
BMS Mapset: COBIL00 / Map COBIL0A
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status

from app.models.transaction import (
    TRAN_CAT_BILL_PAYMENT,
    TRAN_DESC_BILL_PAYMENT,
    TRAN_MERCHANT_CITY_BILL_PAYMENT,
    TRAN_MERCHANT_ID_BILL_PAYMENT,
    TRAN_MERCHANT_NAME_BILL_PAYMENT,
    TRAN_MERCHANT_ZIP_BILL_PAYMENT,
    TRAN_SOURCE_BILL_PAYMENT,
    TRAN_TYPE_BILL_PAYMENT,
    Transaction,
)
from app.repositories.account_repository import AccountRepository
from app.repositories.card_cross_reference_repository import CardCrossReferenceRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.payments import AccountBalanceResponse, PaymentResponse

logger = logging.getLogger(__name__)


def _build_payment_transaction(
    tran_id: str,
    card_num: str,
    payment_amount: Decimal,
    now: datetime,
) -> Transaction:
    """Build the bill payment transaction record.

    COBIL00C lines 220-232 — populate TRAN-RECORD fields:
      TRAN-ID          → tran_id (last+1)
      TRAN-TYPE-CD     → '02' (bill payment)
      TRAN-CAT-CD      → 2
      TRAN-SOURCE      → 'POS TERM'
      TRAN-DESC        → 'BILL PAYMENT - ONLINE'
      TRAN-AMT         → full current balance
      TRAN-MERCHANT-ID → 999999999
      TRAN-MERCHANT-NAME → 'BILL PAYMENT'
      TRAN-MERCHANT-CITY → 'N/A'
      TRAN-MERCHANT-ZIP  → 'N/A'
      TRAN-CARD-NUM    → from CXACAIX cross-reference
      TRAN-ORIG-TS     → current timestamp
      TRAN-PROC-TS     → current timestamp
    """
    return Transaction(
        tran_id=tran_id,
        tran_type_cd=TRAN_TYPE_BILL_PAYMENT,
        tran_cat_cd=TRAN_CAT_BILL_PAYMENT,
        source=TRAN_SOURCE_BILL_PAYMENT,
        description=TRAN_DESC_BILL_PAYMENT,
        amount=payment_amount,
        merchant_id=TRAN_MERCHANT_ID_BILL_PAYMENT,
        merchant_name=TRAN_MERCHANT_NAME_BILL_PAYMENT,
        merchant_city=TRAN_MERCHANT_CITY_BILL_PAYMENT,
        merchant_zip=TRAN_MERCHANT_ZIP_BILL_PAYMENT,
        card_num=card_num,
        orig_timestamp=now,
        proc_timestamp=now,
    )


class PaymentService:
    """Business logic for bill payment (COBIL00C).

    COBIL00C two-phase transaction flow:
      Phase 1: READ-ACCTDAT-FILE → display ACCT-CURR-BAL
      Phase 2 (CONFIRM=Y):
        1. READ-CXACAIX-FILE → get XREF-CARD-NUM
        2. STARTBR/READPREV/ENDBR TRANSACT → get last TRAN-ID
        3. Increment TRAN-ID
        4. Build + WRITE TRAN-RECORD (type '02', full balance, card number, timestamps)
        5. REWRITE ACCTDAT with zeroed balance
    """

    def __init__(
        self,
        account_repo: AccountRepository,
        xref_repo: CardCrossReferenceRepository,
        transaction_repo: TransactionRepository,
    ) -> None:
        self._account_repo = account_repo
        self._xref_repo = xref_repo
        self._transaction_repo = transaction_repo

    async def get_account_balance(self, acct_id: str) -> AccountBalanceResponse:
        """Phase 1 — look up account and return current balance.

        COBIL00C READ-ACCTDAT-FILE + balance display (lines 184-196).
        No payment occurs; user sees balance and decides whether to pay.

        BR-001: Account ID must not be empty (validated by schema).
        BR-003: Returns balance even if 0 — zero-balance error shown to user.
        """
        account = await self._account_repo.get_by_id(acct_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account ID NOT found",
            )

        message = None
        message_type = None
        if account.curr_bal <= Decimal("0"):
            message = "You have nothing to pay"
            message_type = "info"

        return AccountBalanceResponse(
            acct_id=str(account.acct_id),
            curr_bal=account.curr_bal,
            message=message,
            message_type=message_type,
        )

    async def process_payment(self, acct_id: str) -> PaymentResponse:
        """Phase 2 — process the full balance payment.

        COBIL00C CONF-PAY-YES path (lines 208-240).
        This entire operation must be atomic — wrapped in a single DB transaction
        by the caller (via get_db() dependency which auto-commits on success).

        Steps:
          1. Read account (verify exists + get current balance)
          2. BR-003: Reject if balance <= 0
          3. Read card cross-reference → get card number
          4. Generate next transaction ID (MAX tran_id + 1)
          5. Build payment transaction record
          6. Write transaction
          7. Zero account balance (REWRITE ACCTDAT)
          8. Return success with transaction ID
        """
        account = await self._account_repo.get_by_id(acct_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account ID NOT found",
            )

        # BR-003: Cannot pay zero or negative balance
        if account.curr_bal <= Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="You have nothing to pay",
            )

        payment_amount = account.curr_bal

        # Step 3: Get card number from cross-reference (READ-CXACAIX-FILE)
        card_xref = await self._xref_repo.get_by_acct_id(acct_id)
        if card_xref is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account ID NOT found in card cross-reference",
            )
        card_num = card_xref.card_num

        # Steps 4-5: Generate next transaction ID and build record
        # (STARTBR/READPREV/ENDBR + WS-TRAN-ID-NUM + 1)
        next_tran_id = await self._transaction_repo.generate_next_tran_id()

        # GET-CURRENT-TIMESTAMP equivalent (CICS ASKTIME + FORMATTIME)
        now = datetime.now(tz=timezone.utc)

        transaction = _build_payment_transaction(
            tran_id=next_tran_id,
            card_num=card_num,
            payment_amount=payment_amount,
            now=now,
        )

        # Step 6: Write transaction (WRITE-TRANSACT-FILE)
        created_transaction = await self._transaction_repo.create(transaction)

        # Step 7: Zero account balance (UPDATE-ACCTDAT-FILE / REWRITE)
        # COBIL00C line 234: ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT (always 0)
        await self._account_repo.zero_balance(acct_id, payment_amount)

        # Step 8: Build success response
        # COBIL00C WRITE-TRANSACT-FILE success (line 165):
        # 'Payment successful. Your Transaction ID is <TRAN-ID>.'
        success_message = (
            f"Payment successful. Your Transaction ID is {created_transaction.tran_id}."
        )

        return PaymentResponse(
            tran_id=created_transaction.tran_id,
            acct_id=acct_id,
            payment_amount=payment_amount,
            new_balance=Decimal("0.00"),
            orig_timestamp=now,
            message=success_message,
            message_type="success",
        )
