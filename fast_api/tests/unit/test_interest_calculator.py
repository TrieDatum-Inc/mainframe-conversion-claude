"""Unit tests for InterestCalculatorService (CBACT04C).

Tests:
- Monthly interest formula: (balance * rate) / 1200
- Zero rate categories skipped
- DEFAULT group fallback
- Account balance update with cycle credit/debit zeroed
- Transaction ID format: YYYYMMDD + 6-digit suffix
- Last account processed after loop ends
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models.account import Account
from app.models.card_cross_reference import CardCrossReference
from app.models.disclosure_group import DisclosureGroup
from app.models.transaction_category_balance import TransactionCategoryBalance
from app.services.interest_calculator import InterestCalculatorService, INTEREST_DIVISOR


class TestInterestFormula:
    """Tests for CBACT04C interest calculation formula."""

    def test_basic_interest_calculation(self):
        """Monthly interest = (balance * annual_rate) / 1200."""
        service = InterestCalculatorService.__new__(InterestCalculatorService)
        balance = Decimal("500.00")
        rate = Decimal("18.00")  # 18% APR
        result = service._compute_monthly_interest(balance, rate)
        # 500 * 18 / 1200 = 9000 / 1200 = 7.50
        assert result == Decimal("7.50")

    def test_interest_with_non_round_result(self):
        """Verify rounding on fractional interest."""
        service = InterestCalculatorService.__new__(InterestCalculatorService)
        balance = Decimal("1000.00")
        rate = Decimal("21.99")  # 21.99% APR
        result = service._compute_monthly_interest(balance, rate)
        # 1000 * 21.99 / 1200 = 21990 / 1200 = 18.325 -> rounds to 18.33
        assert result == Decimal("18.33")

    def test_zero_rate_produces_zero_interest(self):
        """Zero rate should produce zero (category skipped in COBOL)."""
        service = InterestCalculatorService.__new__(InterestCalculatorService)
        balance = Decimal("1000.00")
        rate = Decimal("0.00")
        result = service._compute_monthly_interest(balance, rate)
        assert result == Decimal("0.00")

    def test_zero_balance_produces_zero_interest(self):
        """Zero balance should produce zero interest."""
        service = InterestCalculatorService.__new__(InterestCalculatorService)
        balance = Decimal("0.00")
        rate = Decimal("18.00")
        result = service._compute_monthly_interest(balance, rate)
        assert result == Decimal("0.00")

    def test_divisor_is_1200(self):
        """Verify divisor is 1200 (annual to monthly conversion)."""
        assert INTEREST_DIVISOR == Decimal("1200")


class TestTransactionIdGeneration:
    """Tests for CBACT04C transaction ID format."""

    def test_tran_id_format(self):
        """ID format: YYYYMMDD (8 chars) + 6-digit suffix = 16 chars max."""
        service = InterestCalculatorService.__new__(InterestCalculatorService)
        run_date = date(2026, 4, 3)
        tran_id = service._build_tran_id(run_date, 0)
        assert tran_id == "20260403000000"
        assert len(tran_id) <= 16

    def test_tran_id_suffix_increments(self):
        """Suffix increments for each transaction."""
        service = InterestCalculatorService.__new__(InterestCalculatorService)
        run_date = date(2026, 4, 3)
        id_0 = service._build_tran_id(run_date, 0)
        id_1 = service._build_tran_id(run_date, 1)
        id_999 = service._build_tran_id(run_date, 999)
        assert id_0 == "20260403000000"
        assert id_1 == "20260403000001"
        assert id_999 == "20260403000999"

    def test_tran_id_max_length_16(self):
        """Transaction ID must not exceed 16 characters."""
        service = InterestCalculatorService.__new__(InterestCalculatorService)
        run_date = date(2026, 12, 31)
        tran_id = service._build_tran_id(run_date, 999999)
        assert len(tran_id) <= 16


class TestInterestCalculatorService:
    """Integration tests for full interest calculation flow."""

    @pytest.mark.asyncio
    async def test_interest_calculated_and_posted(
        self,
        db_session,
        sample_account,
        sample_xref,
        sample_tcatbal,
        sample_disclosure_groups,
    ):
        """End-to-end: interest calculated, transaction created, account updated."""
        from sqlalchemy import select
        from app.models.transaction import Transaction
        service = InterestCalculatorService(db_session)
        run_date = date(2026, 4, 3)

        result = await service.run(run_date)

        assert result["accounts_processed"] == 1
        assert result["interest_transactions_created"] >= 1

        # Verify interest transaction was created
        tran_result = await db_session.execute(
            select(Transaction).where(Transaction.tran_type_cd == "01")
        )
        transactions = tran_result.scalars().all()
        interest_trans = [t for t in transactions if t.tran_desc and "Int. for a/c" in t.tran_desc]
        assert len(interest_trans) >= 1
        assert interest_trans[0].tran_source == "System"

    @pytest.mark.asyncio
    async def test_account_balance_updated_after_interest(
        self,
        db_session,
        sample_account,
        sample_xref,
        sample_tcatbal,
        sample_disclosure_groups,
    ):
        """Account curr_bal increased by total interest."""
        from sqlalchemy import select
        initial_bal = sample_account.acct_curr_bal

        service = InterestCalculatorService(db_session)
        await service.run(date(2026, 4, 3))

        result = await db_session.execute(
            select(Account).where(Account.acct_id == sample_account.acct_id)
        )
        updated_acct = result.scalar_one()
        # Balance should be higher after interest
        assert updated_acct.acct_curr_bal > initial_bal

    @pytest.mark.asyncio
    async def test_cycle_credit_debit_zeroed_after_interest(
        self,
        db_session,
        sample_account,
        sample_xref,
        sample_tcatbal,
        sample_disclosure_groups,
    ):
        """ACCT-CURR-CYC-CREDIT and DEBIT zeroed after interest posting."""
        from sqlalchemy import select
        # sample_account has non-zero cycle credit/debit
        assert sample_account.acct_curr_cyc_credit > Decimal("0")

        service = InterestCalculatorService(db_session)
        await service.run(date(2026, 4, 3))

        result = await db_session.execute(
            select(Account).where(Account.acct_id == sample_account.acct_id)
        )
        updated_acct = result.scalar_one()
        assert updated_acct.acct_curr_cyc_credit == Decimal("0")
        assert updated_acct.acct_curr_cyc_debit == Decimal("0")

    @pytest.mark.asyncio
    async def test_zero_balance_skipped(
        self,
        db_session,
        sample_account,
        sample_xref,
        sample_disclosure_groups,
    ):
        """Zero balance category produces no interest transaction."""
        from sqlalchemy import select
        from app.models.transaction import Transaction
        # Add zero-balance category
        zero_bal = TransactionCategoryBalance(
            acct_id=sample_account.acct_id,
            tran_type_cd="01",
            tran_cat_cd="0005",
            balance=Decimal("0.00"),
        )
        db_session.add(zero_bal)
        await db_session.flush()

        service = InterestCalculatorService(db_session)
        result = await service.run(date(2026, 4, 3))

        # No interest transaction for zero balance (rate is also 0 for cat 0005)
        tran_result = await db_session.execute(
            select(Transaction).where(
                Transaction.tran_cat_cd == "0005",
            )
        )
        transactions = tran_result.scalars().all()
        assert len(transactions) == 0

    @pytest.mark.asyncio
    async def test_default_fallback_rate_used(
        self,
        db_session,
        sample_xref,
        sample_disclosure_groups,
    ):
        """Account group not in disclosure_groups -> DEFAULT rate used."""
        from sqlalchemy import select
        from app.models.transaction import Transaction
        # Account with group UNKNOWN (no specific rate)
        unknown_account = Account(
            acct_id="00000000099",
            acct_active_status="Y",
            acct_curr_bal=Decimal("0"),
            acct_credit_limit=Decimal("5000"),
            acct_curr_cyc_credit=Decimal("0"),
            acct_curr_cyc_debit=Decimal("0"),
            acct_group_id="UNKNOWN",  # No disclosure group entry
        )
        import datetime
        unknown_account.acct_expiration_date = datetime.date(2030, 1, 1)
        db_session.add(unknown_account)

        unknown_xref = CardCrossReference(
            xref_card_num="9000000000000001",
            xref_cust_id="000000099",
            xref_acct_id="00000000099",
        )
        db_session.add(unknown_xref)

        tcatbal = TransactionCategoryBalance(
            acct_id="00000000099",
            tran_type_cd="01",
            tran_cat_cd="0001",
            balance=Decimal("1000.00"),
        )
        db_session.add(tcatbal)
        await db_session.flush()

        service = InterestCalculatorService(db_session)
        result = await service.run(date(2026, 4, 3))

        # Should have used DEFAULT rate (24.00%)
        # 1000 * 24 / 1200 = 20.00
        summaries = [s for s in result["account_summaries"] if s.acct_id == "00000000099"]
        assert len(summaries) == 1
        assert summaries[0].total_interest == Decimal("20.00")
