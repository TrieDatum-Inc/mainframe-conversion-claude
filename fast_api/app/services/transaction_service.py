"""
Transaction service — business logic from COTRN00C, COTRN01C, COTRN02C, COBIL00C.

Paragraph mapping:
  COTRN00C BROWSE-TRANSACTIONS      → list_transactions()
  COTRN01C READ-TRANSACTION         → get_transaction()
  COTRN02C PROCESS-ENTER-KEY        → create_transaction()
  COBIL00C PROCESS-PAYMENT          → process_bill_payment()

Business rules preserved:
  1. TRAN-ID generated from account number + timestamp (COBIL00C WS-TRAN-ID-NUM)
  2. Bill payment: amount must be positive and <= current balance
  3. Bill payment creates new TRANSACT record (EXEC CICS WRITE FILE(TRANSACT))
  4. Bill payment reduces ACCT-CURR-BAL (EXEC CICS REWRITE FILE(ACCTDAT))
  5. Transaction browsing uses TRAN-ID keyset pagination (STARTBR GTEQ)
  6. Card must be ACTIVE (CBTRN01C: CARD-ACTIVE-STATUS = 'Y')
  7. All monetary calculations use Python Decimal (COMP-3 equivalent)
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.repositories.account_repo import AccountRepository
from app.repositories.card_repo import CardRepository
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.transaction import (
    BillPaymentRequest,
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
)
from app.utils.cobol_compat import cobol_move_x, generate_transaction_id, to_decimal
from app.utils.error_handlers import ValidationError


class TransactionService:
    """Transaction business logic from COTRN00C-02C and COBIL00C."""

    def __init__(self, db: AsyncSession) -> None:
        self._txn_repo = TransactionRepository(db)
        self._acct_repo = AccountRepository(db)
        self._card_repo = CardRepository(db)

    async def list_transactions(
        self,
        cursor: str | None = None,
        limit: int = 10,
        card_num: str | None = None,
        acct_id: int | None = None,
        direction: str = "forward",
    ) -> TransactionListResponse:
        """
        COTRN00C BROWSE-TRANSACTIONS paragraph.

        STARTBR FILE('TRANSACT') RIDFLD(WS-TRAN-ID) GTEQ
        READNEXT FILE('TRANSACT') INTO(TRAN-RECORD)

        Keyset pagination on TRAN-ID ascending.
        CDEMO-CT00-TRNID-FIRST / CDEMO-CT00-TRNID-LAST track page boundaries.
        """
        txns, total, has_more = await self._txn_repo.list_paginated(
            cursor=cursor, limit=limit, card_num=card_num, acct_id=acct_id, direction=direction
        )
        items = [self._build_response(t) for t in txns]
        first = txns[0].tran_id.strip() if txns else None
        last = txns[-1].tran_id.strip() if txns else None

        if direction == "backward":
            has_prev = has_more
            has_next = cursor is not None
        else:
            has_next = has_more
            has_prev = cursor is not None

        return TransactionListResponse(
            items=items,
            total=total,
            next_cursor=last if has_next and txns else None,
            prev_cursor=first if has_prev and txns else None,
        )

    async def get_transaction(self, tran_id: str) -> TransactionResponse:
        """
        COTRN01C READ-TRANSACTION: EXEC CICS READ FILE('TRANSACT') RIDFLD(TRAN-ID).

        Raises RecordNotFoundError if not found (CICS RESP=13).
        """
        txn = await self._txn_repo.get_by_id(tran_id)
        return self._build_response(txn)

    async def create_transaction(
        self, request: TransactionCreateRequest, user_id: str
    ) -> TransactionResponse:
        """
        COTRN02C PROCESS-ENTER-KEY → validate → EXEC CICS WRITE FILE('TRANSACT').

        Business rules:
          1. card_num must exist and be ACTIVE (CARD-ACTIVE-STATUS = 'Y')
          2. Look up account via CCXREF (CBTRN01C pattern)
          3. Generate TRAN-ID from account + timestamp
          4. Write new TRANSACT record
        """
        # Validate card exists and is active (CBTRN01C: IF CARD-ACTIVE-STATUS NOT = 'Y')
        card = await self._card_repo.get_by_card_num(request.card_num)
        if card.active_status != "Y":
            raise ValidationError(f"Card {request.card_num.strip()!r} is not active")

        # Look up account via CCXREF (CBTRN01C: READ FILE('XREFFILE') RIDFLD(CARD-NUM))
        xref = await self._card_repo.get_xref_by_card_num(request.card_num)
        acct_id = xref.acct_id

        now = datetime.now(timezone.utc)
        tran_id = generate_transaction_id(acct_id, now)
        ts_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")

        txn = Transaction(
            tran_id=cobol_move_x(tran_id, 16),
            type_cd=cobol_move_x(request.type_cd, 2) if request.type_cd else None,
            cat_cd=request.cat_cd,
            source=cobol_move_x(request.source or "ONLINE", 10),
            description=request.description,
            amount=to_decimal(request.amount),
            merchant_id=request.merchant_id,
            merchant_name=request.merchant_name,
            merchant_city=request.merchant_city,
            merchant_zip=request.merchant_zip,
            card_num=cobol_move_x(request.card_num, 16),
            acct_id=acct_id,
            orig_ts=ts_str,
            proc_ts=ts_str,
        )

        created = await self._txn_repo.create(txn)
        return self._build_response(created)

    async def process_bill_payment(
        self, request: BillPaymentRequest, user_id: str
    ) -> TransactionResponse:
        """
        COBIL00C PROCESS-PAYMENT paragraph.

        Business rules:
          1. payment_amount must be positive (validated in schema)
          2. payment_amount <= current balance (COBIL00C validation)
          3. Browse CXACAIX to find card for account (STARTBR CXACAIX)
          4. Create new TRANSACT record (EXEC CICS WRITE FILE(TRANSACT))
          5. Reduce ACCT-CURR-BAL (EXEC CICS REWRITE FILE(ACCTDAT))
          6. TRAN-ID from account ID + timestamp (WS-ABS-TIME pattern)
        """
        # COBIL00C: READ FILE(ACCTDAT) to get current balance
        account = await self._acct_repo.get_by_id(request.account_id)

        payment = to_decimal(request.payment_amount)

        # COBIL00C validation: payment amount <= current balance
        if payment > account.curr_bal:
            raise ValidationError(
                f"Payment amount {payment} exceeds current balance {account.curr_bal}"
            )

        # COBIL00C: STARTBR FILE(CXACAIX) RIDFLD(WS-ACCT-ID) — find card for account
        xrefs = await self._card_repo.list_xref_by_account(request.account_id)
        if not xrefs:
            raise ValidationError(f"No card found for account {request.account_id}")
        card_num = xrefs[0].card_num  # Use first card (COBIL00C uses first READNEXT result)

        now = datetime.now(timezone.utc)
        tran_id = generate_transaction_id(request.account_id, now)
        ts_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")

        # COBIL00C: EXEC CICS WRITE FILE(TRANSACT) — create payment transaction
        txn = Transaction(
            tran_id=cobol_move_x(tran_id, 16),
            type_cd="02",  # TRAN-TYPE-CD '02' = Payment (from trantype.txt)
            cat_cd=1,
            source=cobol_move_x("PAYMENT", 10),
            description=cobol_move_x(request.description or "Bill Payment", 100),
            amount=payment,
            card_num=cobol_move_x(card_num, 16),
            acct_id=request.account_id,
            orig_ts=ts_str,
            proc_ts=ts_str,
        )
        created = await self._txn_repo.create(txn)

        # COBIL00C: EXEC CICS REWRITE FILE(ACCTDAT) — update balance
        # ACCT-CURR-BAL = ACCT-CURR-BAL - payment_amount
        account.curr_bal = to_decimal(account.curr_bal) - payment
        account.curr_cycle_credit = to_decimal(account.curr_cycle_credit) + payment
        await self._acct_repo.update(account)

        return self._build_response(created)

    @staticmethod
    def _build_response(txn: Transaction) -> TransactionResponse:
        """Build TransactionResponse from ORM model."""
        return TransactionResponse(
            tran_id=txn.tran_id.strip() if txn.tran_id else txn.tran_id,
            type_cd=txn.type_cd,
            cat_cd=txn.cat_cd,
            source=txn.source,
            description=txn.description,
            amount=txn.amount,
            merchant_id=txn.merchant_id,
            merchant_name=txn.merchant_name,
            merchant_city=txn.merchant_city,
            merchant_zip=txn.merchant_zip,
            card_num=txn.card_num,
            acct_id=txn.acct_id,
            orig_ts=txn.orig_ts,
            proc_ts=txn.proc_ts,
        )
