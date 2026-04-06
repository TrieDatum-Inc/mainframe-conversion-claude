"""
Business logic service for billing (bill payment).

COBOL origin: COBIL00C — Online Bill Payment program (Transaction: CB00).

Two-phase pattern replicated:
  Phase 1: get_balance() → COBIL00C READ-ACCTDAT-FILE (display balance, no payment)
  Phase 2: process_payment() → COBIL00C CONF-PAY-YES path:
    READ-CXACAIX-FILE → get card
    STARTBR/READPREV → transaction ID (replaced by sequence)
    WRITE-TRANSACT-FILE → create payment transaction
    UPDATE-ACCTDAT-FILE → set balance = 0

All hardcoded COBIL00C values preserved:
  TRAN-TYPE-CD   = '02'
  TRAN-CAT-CD    = '0002'
  TRAN-SOURCE    = 'POS TERM'
  TRAN-DESC      = 'BILL PAYMENT - ONLINE'
  TRAN-MERCHANT-ID   = '999999999'
  TRAN-MERCHANT-NAME = 'BILL PAYMENT'
  TRAN-MERCHANT-CITY = 'N/A'
  TRAN-MERCHANT-ZIP  = 'N/A'
"""

from datetime import date, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.errors import (
    AccountNotFoundError,
    CardNotFoundError,
    NothingToPayError,
    ValidationError as ServiceValidationError,
)
from app.models.transaction import Transaction
from app.repositories.billing_repository import BillingRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.billing import BillingBalanceResponse, BillPaymentRequest, BillPaymentResponse


# Hardcoded values from COBIL00C PROCESS-ENTER-KEY / ADD-TRANSACTION paragraphs
_PAYMENT_TYPE_CODE = "02"           # TRAN-TYPE-CD = '02'
_PAYMENT_CATEGORY_CODE = "0002"     # TRAN-CAT-CD = 2 → '0002'
_PAYMENT_SOURCE = "POS TERM"        # TRAN-SOURCE = 'POS TERM' (hardcoded in COBIL00C)
_PAYMENT_DESCRIPTION = "BILL PAYMENT - ONLINE"  # TRAN-DESC (hardcoded in COBIL00C)
_PAYMENT_MERCHANT_ID = "999999999"  # TRAN-MERCHANT-ID = 999999999 (synthetic, hardcoded)
_PAYMENT_MERCHANT_NAME = "BILL PAYMENT"  # TRAN-MERCHANT-NAME (hardcoded in COBIL00C)
_PAYMENT_MERCHANT_CITY = "N/A"      # TRAN-MERCHANT-CITY = 'N/A' (hardcoded in COBIL00C)
_PAYMENT_MERCHANT_ZIP = "N/A"       # TRAN-MERCHANT-ZIP = 'N/A' (hardcoded in COBIL00C)


class BillingService:
    """
    Service handling COBIL00C bill payment business logic.

    Implements the two-phase confirmation pattern from COBIL00C:
      Phase 1: Display balance (no side effects)
      Phase 2: Confirm payment (creates transaction, zeroes balance)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.billing_repo = BillingRepository(db)
        self.transaction_repo = TransactionRepository(db)
        self.db = db

    async def get_balance(self, account_id: int) -> BillingBalanceResponse:
        """
        Phase 1: Retrieve account balance for display.

        COBOL origin: COBIL00C PROCESS-ENTER-KEY when CONFIRMI=SPACES/LOW-VALUES:
          READ-ACCTDAT-FILE → display ACCT-CURR-BAL as CURBAL
          "Confirm to make a bill payment..." → cursor to CONFIRMI

        No side effects — read-only, no lock acquired (unlike COBIL00C which
        used READ UPDATE even for display-only Phase 1).
        """
        self._validate_account_id(account_id)

        account = await self.billing_repo.get_account_balance(account_id)
        if not account:
            raise AccountNotFoundError(account_id)

        available_credit = Decimal(str(account.credit_limit)) - Decimal(str(account.current_balance))

        return BillingBalanceResponse(
            account_id=account.account_id,
            current_balance=Decimal(str(account.current_balance)),
            credit_limit=Decimal(str(account.credit_limit)),
            available_credit=available_credit,
        )

    async def process_payment(
        self, account_id: int, request: BillPaymentRequest
    ) -> BillPaymentResponse:
        """
        Phase 2: Execute bill payment with account lock.

        COBOL origin: COBIL00C PROCESS-ENTER-KEY when CONFIRMI='Y':
          SET CONF-PAY-YES
          READ-ACCTDAT-FILE (UPDATE lock)
          IF ACCT-CURR-BAL <= 0: "You have nothing to pay..."
          READ-CXACAIX-FILE → XREF-CARD-NUM
          STARTBR-TRANSACT-FILE + READPREV-TRANSACT-FILE + ENDBR (get max ID)
          ADD 1 to TRAN-ID → new WS-NEW-TRAN-ID  [REPLACED BY SEQUENCE]
          WRITE-TRANSACT-FILE (new payment transaction)
          COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT (= 0)
          UPDATE-ACCTDAT-FILE (REWRITE)

        Uses SELECT FOR UPDATE for the account record to prevent double-payment
        race condition. COBIL00C used CICS READ UPDATE for the same purpose.
        """
        self._validate_account_id(account_id)

        # Acquire pessimistic lock on account (COBIL00C: READ UPDATE)
        account = await self.billing_repo.get_account_for_update(account_id)
        if not account:
            raise AccountNotFoundError(account_id)

        # COBIL00C: IF ACCT-CURR-BAL <= 0: "You have nothing to pay..."
        previous_balance = Decimal(str(account.current_balance))
        if previous_balance <= Decimal("0"):
            raise NothingToPayError(account_id)

        # COBIL00C: READ-CXACAIX-FILE → get XREF-CARD-NUM for TRAN-CARD-NUM
        card_number = await self.billing_repo.get_card_for_account(account_id)
        if not card_number:
            raise CardNotFoundError(f"account={account_id}")

        # Generate transaction ID via sequence (replaces COBIL00C STARTBR/READPREV/ADD-1)
        transaction_id = await self.transaction_repo.generate_transaction_id()

        # Build payment transaction record with COBIL00C hardcoded values
        today = date.today()
        payment_transaction = self._build_payment_transaction(
            transaction_id=transaction_id,
            card_number=card_number,
            amount=previous_balance,
            transaction_date=today,
        )

        await self.transaction_repo.create(payment_transaction)

        # COBIL00C: COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT (= 0)
        new_balance = Decimal("0.00")
        await self.billing_repo.update_account_balance(account_id, new_balance)

        return BillPaymentResponse(
            account_id=account_id,
            previous_balance=previous_balance,
            new_balance=new_balance,
            transaction_id=transaction_id,
            message=(
                f"Payment successful. Your Transaction ID is {int(transaction_id)}."
            ),
        )

    def _build_payment_transaction(
        self,
        transaction_id: str,
        card_number: str,
        amount: Decimal,
        transaction_date: date,
    ) -> Transaction:
        """
        Construct payment Transaction with COBIL00C hardcoded attributes.

        COBOL origin: COBIL00C ADD-TRANSACTION / INITIALIZE TRAN-RECORD then:
          TRAN-TYPE-CD     = '02'              → _PAYMENT_TYPE_CODE
          TRAN-CAT-CD      = 2                 → _PAYMENT_CATEGORY_CODE
          TRAN-SOURCE      = 'POS TERM'        → _PAYMENT_SOURCE
          TRAN-DESC        = 'BILL PAYMENT - ONLINE' → _PAYMENT_DESCRIPTION
          TRAN-AMT         = ACCT-CURR-BAL     → amount (full balance)
          TRAN-CARD-NUM    = XREF-CARD-NUM     → card_number (from CXACAIX lookup)
          TRAN-MERCHANT-ID = 999999999         → _PAYMENT_MERCHANT_ID
          TRAN-ORIG-TS     = WS-TIMESTAMP      → transaction_date
          TRAN-PROC-TS     = WS-TIMESTAMP      → transaction_date (same as orig in COBIL00C)
        """
        return Transaction(
            transaction_id=transaction_id,
            card_number=card_number,
            transaction_type_code=_PAYMENT_TYPE_CODE,
            transaction_category_code=_PAYMENT_CATEGORY_CODE,
            transaction_source=_PAYMENT_SOURCE,
            description=_PAYMENT_DESCRIPTION,
            amount=float(amount),
            original_date=transaction_date,
            processed_date=transaction_date,
            merchant_id=_PAYMENT_MERCHANT_ID,
            merchant_name=_PAYMENT_MERCHANT_NAME,
            merchant_city=_PAYMENT_MERCHANT_CITY,
            merchant_zip=_PAYMENT_MERCHANT_ZIP,
        )

    def _validate_account_id(self, account_id: int) -> None:
        """
        Validate account ID.

        COBOL origin: COBIL00C PROCESS-ENTER-KEY:
          IF ACTIDINI = SPACES: "Acct ID can NOT be empty..." → cursor to ACTIDINI
        """
        if not account_id or account_id <= 0:
            raise ServiceValidationError("account_id", "Account ID cannot be empty or zero")
