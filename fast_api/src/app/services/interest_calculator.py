"""Interest Calculator Service — CBACT04C equivalent.

Calculates monthly interest charges for all accounts.

Business rules preserved:
- Formula: monthly_interest = (category_balance * annual_rate) / 1200
- Only compute if DIS-INT-RATE != 0 (zero rate categories skipped)
- DEFAULT group fallback when specific group rate not found
- Interest accumulated per account before single account update
- Account CURR-BAL updated, cycle credit/debit zeroed (end of cycle)
- Last account processed after EOF (handled by iterating all records)
- Fee calculation (1400-COMPUTE-FEES) is a stub — TODO note preserved

Transaction ID format: PARM-DATE (10 chars) + 6-digit suffix (WS-TRANID-SUFFIX)
Hardcoded: TRAN-TYPE-CD='01', TRAN-CAT-CD='05'
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.transaction import Transaction
from app.repositories.account import AccountRepository
from app.repositories.batch_job import BatchJobRepository
from app.repositories.card_cross_reference import CardCrossReferenceRepository
from app.repositories.disclosure_group import DisclosureGroupRepository
from app.repositories.transaction import TransactionRepository
from app.repositories.transaction_category_balance import TransactionCategoryBalanceRepository
from app.schemas.batch import AccountInterestSummary, InterestTransactionResult

logger = logging.getLogger(__name__)

# Hardcoded from CBACT04C 1300-B-WRITE-TX lines 482-483
INTEREST_TRAN_TYPE_CD = "01"
INTEREST_TRAN_CAT_CD = "05"
INTEREST_DIVISOR = Decimal("1200")  # Annual rate / 1200 = monthly fraction


class InterestCalculatorService:
    """CBACT04C equivalent: calculates and posts monthly interest charges."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.account_repo = AccountRepository(db)
        self.xref_repo = CardCrossReferenceRepository(db)
        self.discgrp_repo = DisclosureGroupRepository(db)
        self.tcatbal_repo = TransactionCategoryBalanceRepository(db)
        self.tran_repo = TransactionRepository(db)
        self.job_repo = BatchJobRepository(db)

    async def run(self, run_date: date) -> dict:
        """Calculate interest for all accounts.

        Maps CBACT04C PROCEDURE DIVISION main loop.
        run_date maps to JCL PARM date used to prefix TRAN-IDs.
        """
        job = await self.job_repo.create_job("interest_calculation")
        await self.db.commit()

        balances = await self.tcatbal_repo.get_all_ordered_by_account()

        summaries, tran_count = await self._process_all_balances(
            run_date, balances
        )

        total_accounts = len(summaries)
        await self.job_repo.complete_job(
            job_id=job.job_id,
            records_processed=len(balances),
            records_rejected=0,
            result_summary={
                "run_date": str(run_date),
                "accounts_processed": total_accounts,
                "interest_transactions_created": tran_count,
            },
        )
        await self.db.commit()

        return {
            "job_id": job.job_id,
            "status": "completed",
            "run_date": run_date,
            "accounts_processed": total_accounts,
            "interest_transactions_created": tran_count,
            "account_summaries": summaries,
            "message": (
                f"Interest calculation complete: {total_accounts} accounts processed, "
                f"{tran_count} interest transactions created"
            ),
        }

    async def _process_all_balances(
        self, run_date: date, balances: list
    ) -> tuple[list[AccountInterestSummary], int]:
        """Process all category balances grouped by account.

        Maps CBACT04C main loop with account break detection:
          IF TRANCAT-ACCT-ID NOT= WS-LAST-ACCT-NUM -> account change
        Balances are ordered by acct_id so we can detect breaks.
        """
        summaries: list[AccountInterestSummary] = []
        tran_count = 0
        tran_suffix = 0

        # Group balances by account (they are sorted by acct_id from repo)
        current_acct_id = ""
        current_acct = None
        current_card_num = ""
        total_int = Decimal("0")
        category_transactions: list[InterestTransactionResult] = []

        for balance in balances:
            if balance.acct_id != current_acct_id:
                # Account break: flush accumulated interest for previous account
                if current_acct_id and current_acct is not None:
                    await self.account_repo.update_balance_after_interest(
                        current_acct_id, total_int
                    )
                    summaries.append(
                        AccountInterestSummary(
                            acct_id=current_acct_id,
                            total_interest=total_int,
                            category_count=len(category_transactions),
                            transactions_created=category_transactions,
                        )
                    )

                # Start new account
                current_acct_id = balance.acct_id
                current_acct = await self.account_repo.get_by_id(current_acct_id)
                xref = await self.xref_repo.get_by_acct_id(current_acct_id)
                current_card_num = xref.xref_card_num if xref else ""
                total_int = Decimal("0")
                category_transactions = []

            if current_acct is None:
                logger.warning("Account not found for interest calc: %s", balance.acct_id)
                continue

            interest_result = await self._compute_interest_for_category(
                run_date=run_date,
                account=current_acct,
                balance=balance,
                card_num=current_card_num,
                tran_suffix=tran_suffix,
            )

            if interest_result is not None:
                total_int += interest_result.monthly_interest
                category_transactions.append(interest_result)
                tran_suffix += 1
                tran_count += 1
                # TODO: CBACT04C 1400-COMPUTE-FEES is a stub in COBOL — not implemented

        # Flush last account after EOF
        if current_acct_id and current_acct is not None:
            await self.account_repo.update_balance_after_interest(current_acct_id, total_int)
            summaries.append(
                AccountInterestSummary(
                    acct_id=current_acct_id,
                    total_interest=total_int,
                    category_count=len(category_transactions),
                    transactions_created=category_transactions,
                )
            )

        return summaries, tran_count

    async def _compute_interest_for_category(
        self,
        run_date: date,
        account,
        balance,
        card_num: str,
        tran_suffix: int,
    ) -> InterestTransactionResult | None:
        """Compute interest for one category balance.

        Maps CBACT04C 1200-GET-INTEREST-RATE + 1300-COMPUTE-INTEREST + 1300-B-WRITE-TX.
        Returns None if rate is zero (no interest charged).
        """
        group_id = account.acct_group_id or "DEFAULT"
        rate_record = await self.discgrp_repo.get_rate_with_default_fallback(
            group_id=group_id,
            tran_type_cd=balance.tran_type_cd,
            tran_cat_cd=balance.tran_cat_cd,
        )

        if rate_record is None:
            logger.warning(
                "No disclosure group rate found: group=%s type=%s cat=%s",
                group_id,
                balance.tran_type_cd,
                balance.tran_cat_cd,
            )
            return None

        interest_rate = rate_record.interest_rate or Decimal("0")

        # IF DIS-INT-RATE NOT = 0 -> compute, else skip
        if interest_rate == Decimal("0"):
            return None

        monthly_interest = self._compute_monthly_interest(
            balance.balance, interest_rate
        )

        tran_id = self._build_tran_id(run_date, tran_suffix)
        await self._write_interest_transaction(
            tran_id=tran_id,
            acct_id=balance.acct_id,
            monthly_interest=monthly_interest,
            card_num=card_num,
        )

        return InterestTransactionResult(
            tran_id=tran_id,
            acct_id=balance.acct_id,
            tran_type_cd=INTEREST_TRAN_TYPE_CD,
            tran_cat_cd=INTEREST_TRAN_CAT_CD,
            balance=balance.balance,
            interest_rate=interest_rate,
            monthly_interest=monthly_interest,
            card_num=card_num,
        )

    def _compute_monthly_interest(
        self, balance: Decimal, annual_rate: Decimal
    ) -> Decimal:
        """Calculate monthly interest.

        Maps CBACT04C 1300-COMPUTE-INTEREST:
          COMPUTE WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200
        Rate is annual percentage (e.g., 18.00 = 18% APR).
        Divisor 1200 = 12 months * 100 (percent to decimal).
        """
        return (balance * annual_rate / INTEREST_DIVISOR).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def _build_tran_id(self, run_date: date, suffix: int) -> str:
        """Build transaction ID for interest charge.

        Maps CBACT04C 1300-B-WRITE-TX lines 476-481:
          STRING PARM-DATE + WS-TRANID-SUFFIX (6-digit sequence)
        Format: YYYY-MM-DD (10 chars) + 000001 (6 digits) = 16 chars total
        """
        date_str = run_date.strftime("%Y%m%d")  # 8 chars
        suffix_str = f"{suffix:06d}"  # 6 chars WS-TRANID-SUFFIX
        tran_id = f"{date_str}{suffix_str}"
        return tran_id[:16]  # TRAN-ID PIC X(16)

    async def _write_interest_transaction(
        self,
        tran_id: str,
        acct_id: str,
        monthly_interest: Decimal,
        card_num: str,
    ) -> None:
        """Write interest transaction record.

        Maps CBACT04C 1300-B-WRITE-TX:
          TRAN-TYPE-CD = '01'
          TRAN-CAT-CD = '05'
          TRAN-SOURCE = 'System'
          TRAN-DESC = 'Int. for a/c ' + ACCT-ID
        """
        now = datetime.now(tz=timezone.utc)
        transaction = Transaction(
            tran_id=tran_id,
            tran_type_cd=INTEREST_TRAN_TYPE_CD,
            tran_cat_cd=INTEREST_TRAN_CAT_CD,
            tran_source="System",
            tran_desc=f"Int. for a/c {acct_id}",
            tran_amt=monthly_interest,
            tran_merchant_id=None,
            tran_merchant_name=None,
            tran_merchant_city=None,
            tran_merchant_zip=None,
            tran_card_num=card_num,
            tran_orig_ts=now,
            tran_proc_ts=now,
        )
        await self.tran_repo.insert(transaction)
