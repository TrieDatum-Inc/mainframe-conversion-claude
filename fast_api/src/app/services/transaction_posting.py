"""Transaction Posting Service — CBTRN02C equivalent.

Validates and posts daily transactions. Full business logic from spec sections 2-7.

Key business rules preserved:
- Reason 100: card not in cross-reference
- Reason 101: account not found
- Reason 102: overlimit (ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT > ACCT-CREDIT-LIMIT)
- Reason 103: expired account
- Both credit/expiry checks run; 103 overwrites 102 if both fail (COBOL spec behavior)
- Atomic per-transaction: each succeeds or fails independently
- Return code 4 equivalent: has_rejects=True when any rejects occur
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.repositories.account import AccountRepository
from app.repositories.batch_job import BatchJobRepository
from app.repositories.card_cross_reference import CardCrossReferenceRepository
from app.repositories.transaction import TransactionRepository
from app.repositories.transaction_category_balance import TransactionCategoryBalanceRepository
from app.schemas.transaction import DailyTransactionInput, RejectRecord

logger = logging.getLogger(__name__)

# Reason codes from CBTRN02C WS-VALIDATION-FAIL-REASON
REASON_INVALID_CARD = "100"
REASON_ACCOUNT_NOT_FOUND = "101"
REASON_OVERLIMIT = "102"
REASON_EXPIRED = "103"
REASON_ACCOUNT_UPDATE_FAILED = "109"

REASON_DESCRIPTIONS = {
    REASON_INVALID_CARD: "INVALID CARD NUMBER FOUND",
    REASON_ACCOUNT_NOT_FOUND: "ACCOUNT RECORD NOT FOUND",
    REASON_OVERLIMIT: "OVERLIMIT TRANSACTION",
    REASON_EXPIRED: "TRANSACTION RECEIVED AFTER ACCT EXPIRATION",
    REASON_ACCOUNT_UPDATE_FAILED: "ACCOUNT RECORD NOT FOUND",
}


class ValidationResult:
    """Result of transaction validation. Maps WS-VALIDATION-FAIL-REASON."""

    def __init__(self) -> None:
        self.reason_code: str | None = None
        self.reason_desc: str = ""
        self.acct_id: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.reason_code is None

    def fail(self, code: str) -> None:
        self.reason_code = code
        self.reason_desc = REASON_DESCRIPTIONS.get(code, "UNKNOWN ERROR")


class TransactionPostingService:
    """CBTRN02C equivalent: validates and posts daily transactions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.account_repo = AccountRepository(db)
        self.xref_repo = CardCrossReferenceRepository(db)
        self.tran_repo = TransactionRepository(db)
        self.tcatbal_repo = TransactionCategoryBalanceRepository(db)
        self.job_repo = BatchJobRepository(db)

    async def run(
        self, transactions: list[DailyTransactionInput]
    ) -> dict:
        """Main entry point. Maps CBTRN02C PROCEDURE DIVISION main loop.

        Returns dict with job result matching TransactionPostingResponse schema.
        Each transaction is processed atomically (independent success/fail).
        """
        job = await self.job_repo.create_job("transaction_posting")
        await self.db.commit()

        posted: list[str] = []
        rejects: list[RejectRecord] = []

        for tran in transactions:
            result = await self._process_one_transaction(job.job_id, tran, rejects)
            if result:
                posted.append(tran.tran_id)

        await self.job_repo.complete_job(
            job_id=job.job_id,
            records_processed=len(transactions),
            records_rejected=len(rejects),
            result_summary={
                "transactions_posted": len(posted),
                "rejects": len(rejects),
            },
        )
        await self.db.commit()

        return {
            "job_id": job.job_id,
            "status": "completed",
            "transactions_processed": len(transactions),
            "transactions_posted": len(posted),
            "transactions_rejected": len(rejects),
            "has_rejects": len(rejects) > 0,  # Maps COBOL RETURN-CODE 4
            "rejects": rejects,
            "message": (
                f"Processed {len(transactions)} transactions: "
                f"{len(posted)} posted, {len(rejects)} rejected"
            ),
        }

    async def _process_one_transaction(
        self,
        job_id: int,
        tran: DailyTransactionInput,
        rejects: list[RejectRecord],
    ) -> bool:
        """Process a single transaction atomically.

        Maps CBTRN02C inner loop body:
          PERFORM 1500-VALIDATE-TRAN
          IF WS-VALIDATION-FAIL-REASON = 0 -> PERFORM 2000-POST-TRANSACTION
          ELSE -> PERFORM 2500-WRITE-REJECT-REC
        Returns True if posted, False if rejected.
        """
        validation = ValidationResult()

        await self._validate_transaction(tran, validation)

        if validation.is_valid:
            posted_ok = await self._post_transaction(tran, validation.acct_id or "")
            if not posted_ok:
                validation.fail(REASON_ACCOUNT_UPDATE_FAILED)

        if not validation.is_valid:
            reject = RejectRecord(
                tran_id=tran.tran_id,
                card_num=tran.tran_card_num,
                reason_code=validation.reason_code or "999",
                reason_desc=validation.reason_desc,
                original_data=tran.model_dump(mode="json"),
            )
            rejects.append(reject)
            await self.job_repo.insert_reject(
                job_id=job_id,
                tran_id=tran.tran_id,
                card_num=tran.tran_card_num,
                reason_code=validation.reason_code or "999",
                reason_desc=validation.reason_desc,
                original_data=tran.model_dump(mode="json"),
            )
            logger.info(
                "Transaction rejected: tran_id=%s reason=%s",
                tran.tran_id,
                validation.reason_code,
            )
            return False

        return True

    async def _validate_transaction(
        self, tran: DailyTransactionInput, result: ValidationResult
    ) -> None:
        """Validate transaction. Maps CBTRN02C 1500-VALIDATE-TRAN.

        Calls 1500-A-LOOKUP-XREF, then 1500-B-LOOKUP-ACCT only if xref found.
        """
        await self._lookup_xref(tran.tran_card_num, result)
        if result.is_valid:
            await self._lookup_account(tran, result)

    async def _lookup_xref(self, card_num: str, result: ValidationResult) -> None:
        """Maps CBTRN02C 1500-A-LOOKUP-XREF.

        INVALID KEY -> reason 100 (INVALID CARD NUMBER FOUND).
        """
        xref = await self.xref_repo.get_by_card_num(card_num)
        if xref is None:
            result.fail(REASON_INVALID_CARD)
            logger.warning("Card not found in xref: %s", card_num)
        else:
            result.acct_id = xref.xref_acct_id

    async def _lookup_account(
        self, tran: DailyTransactionInput, result: ValidationResult
    ) -> None:
        """Maps CBTRN02C 1500-B-LOOKUP-ACCT.

        Performs both credit limit check (102) and expiry check (103).
        Both checks execute regardless of first result — 103 overwrites 102.
        This is preserved from the COBOL spec (noted as potential defect).
        """
        account = await self.account_repo.get_by_id(result.acct_id or "")
        if account is None:
            result.fail(REASON_ACCOUNT_NOT_FOUND)
            return

        self._check_credit_limit(tran.tran_amt, account, result)
        self._check_expiration(tran.tran_orig_ts, account, result)

    def _check_credit_limit(
        self, tran_amt: Decimal, account, result: ValidationResult
    ) -> None:
        """Credit limit check. Maps CBTRN02C lines 403-412.

        COMPUTE WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
        IF ACCT-CREDIT-LIMIT < WS-TEMP-BAL -> reason 102
        """
        cyc_credit = account.acct_curr_cyc_credit or Decimal("0")
        cyc_debit = account.acct_curr_cyc_debit or Decimal("0")
        temp_bal = cyc_credit - cyc_debit + tran_amt

        if (account.acct_credit_limit or Decimal("0")) < temp_bal:
            result.fail(REASON_OVERLIMIT)

    def _check_expiration(
        self, orig_ts: datetime, account, result: ValidationResult
    ) -> None:
        """Expiration check. Maps CBTRN02C lines 414-419.

        IF ACCT-EXPIRAION-DATE < DALYTRAN-ORIG-TS(1:10) -> reason 103
        Both checks always run; 103 overwrites 102 if both fail.
        """
        if account.acct_expiration_date is None:
            return

        tran_date = orig_ts.date()
        if account.acct_expiration_date < tran_date:
            result.fail(REASON_EXPIRED)  # Overwrites 102 if both failed

    async def _post_transaction(self, tran: DailyTransactionInput, acct_id: str) -> bool:
        """Post a valid transaction. Maps CBTRN02C 2000-POST-TRANSACTION.

        Calls: 2700-UPDATE-TCATBAL, 2800-UPDATE-ACCOUNT-REC, 2900-WRITE-TRANSACTION-FILE.
        """
        await self._update_tcatbal(tran, acct_id)

        updated = await self.account_repo.update_balance_after_posting(
            acct_id, tran.tran_amt
        )
        if not updated:
            return False

        transaction = Transaction(
            tran_id=tran.tran_id,
            tran_type_cd=tran.tran_type_cd,
            tran_cat_cd=tran.tran_cat_cd,
            tran_source=tran.tran_source,
            tran_desc=tran.tran_desc,
            tran_amt=tran.tran_amt,
            tran_merchant_id=tran.tran_merchant_id,
            tran_merchant_name=tran.tran_merchant_name,
            tran_merchant_city=tran.tran_merchant_city,
            tran_merchant_zip=tran.tran_merchant_zip,
            tran_card_num=tran.tran_card_num,
            tran_orig_ts=tran.tran_orig_ts,
            tran_proc_ts=datetime.now(tz=timezone.utc),  # Z-GET-DB2-FORMAT-TIMESTAMP
        )
        await self.tran_repo.insert(transaction)
        logger.info("Transaction posted: tran_id=%s acct_id=%s", tran.tran_id, acct_id)
        return True

    async def _update_tcatbal(
        self, tran: DailyTransactionInput, acct_id: str
    ) -> None:
        """Update transaction category balance. Maps CBTRN02C 2700-UPDATE-TCATBAL.

        Creates record if not exists (2700-A-CREATE-TCATBAL-REC),
        updates if exists (2700-B-UPDATE-TCATBAL-REC).
        """
        await self.tcatbal_repo.upsert(
            acct_id=acct_id,
            tran_type_cd=tran.tran_type_cd,
            tran_cat_cd=tran.tran_cat_cd,
            amount_delta=tran.tran_amt,
        )
