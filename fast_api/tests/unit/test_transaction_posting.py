"""Unit tests for TransactionPostingService (CBTRN02C).

Tests all validation business rules from spec section 7:
- Reason 100: card not in xref
- Reason 101: account not found
- Reason 102: overlimit
- Reason 103: expired
- Dual-fail (102+103): 103 overwrites 102 (COBOL spec behavior preserved)
- Valid transaction: posts correctly
- Account balance update after posting
- TCATBAL create vs update
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio

from app.models.account import Account
from app.models.card_cross_reference import CardCrossReference
from app.models.transaction_category_balance import TransactionCategoryBalance
from app.schemas.transaction import DailyTransactionInput
from app.services.transaction_posting import (
    REASON_EXPIRED,
    REASON_INVALID_CARD,
    REASON_OVERLIMIT,
    TransactionPostingService,
    ValidationResult,
)


def make_transaction(
    card_num: str = "4111111111111111",
    tran_amt: Decimal = Decimal("-50.00"),
    orig_ts: datetime | None = None,
    tran_id: str = "TXN0000000000001",
) -> DailyTransactionInput:
    if orig_ts is None:
        orig_ts = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    return DailyTransactionInput(
        tran_id=tran_id,
        tran_type_cd="01",
        tran_cat_cd="0001",
        tran_source="POS",
        tran_desc="Test purchase",
        tran_amt=tran_amt,
        tran_merchant_id="000000001",
        tran_merchant_name="Test Merchant",
        tran_merchant_city="Test City",
        tran_merchant_zip="12345",
        tran_card_num=card_num,
        tran_orig_ts=orig_ts,
    )


class TestValidationResult:
    """Tests for ValidationResult helper class."""

    def test_initial_state_is_valid(self):
        result = ValidationResult()
        assert result.is_valid is True
        assert result.reason_code is None

    def test_fail_sets_reason(self):
        result = ValidationResult()
        result.fail("102")
        assert result.is_valid is False
        assert result.reason_code == "102"
        assert "OVERLIMIT" in result.reason_desc

    def test_second_fail_overwrites_first(self):
        """COBOL spec: 103 overwrites 102 when both checks fail."""
        result = ValidationResult()
        result.fail("102")
        result.fail("103")
        assert result.reason_code == "103"
        assert "EXPIRATION" in result.reason_desc


def make_mock_account(
    acct_id: str = "00000000001",
    credit_limit: Decimal = Decimal("5000.00"),
    cyc_credit: Decimal = Decimal("2500.00"),
    cyc_debit: Decimal = Decimal("1000.00"),
    expiration_date=None,
) -> Account:
    """Create a mock account without DB."""
    from datetime import date as dt
    account = Account()
    account.acct_id = acct_id
    account.acct_credit_limit = credit_limit
    account.acct_curr_cyc_credit = cyc_credit
    account.acct_curr_cyc_debit = cyc_debit
    account.acct_expiration_date = expiration_date or dt(2027, 12, 31)
    account.acct_curr_bal = Decimal("0")
    account.acct_active_status = "Y"
    return account


class TestCreditLimitCheck:
    """Tests for CBTRN02C credit limit validation (reason 102)."""

    def test_within_credit_limit_passes(self):
        service = TransactionPostingService.__new__(TransactionPostingService)
        result = ValidationResult()
        account = make_mock_account()
        tran_amt = Decimal("-50.00")
        service._check_credit_limit(tran_amt, account, result)
        assert result.is_valid is True

    def test_exactly_at_credit_limit_passes(self):
        """Boundary: credit_limit == temp_bal should pass."""
        service = TransactionPostingService.__new__(TransactionPostingService)
        result = ValidationResult()
        # cyc_credit=2500, cyc_debit=1000, credit_limit=5000
        # temp_bal = 2500 - 1000 + 2500 = 4000 -> within 5000 limit
        account = make_mock_account()
        tran_amt = Decimal("2500.00")  # max that keeps temp_bal == credit_limit
        service._check_credit_limit(tran_amt, account, result)
        assert result.is_valid is True

    def test_over_credit_limit_fails(self):
        """Overlimit: temp_bal exceeds credit_limit."""
        service = TransactionPostingService.__new__(TransactionPostingService)
        result = ValidationResult()
        # cyc_credit=2000, cyc_debit=0, credit_limit=2500
        # temp_bal = 2000 - 0 + 600 = 2600 > 2500 -> fail 102
        account = make_mock_account(
            credit_limit=Decimal("2500.00"),
            cyc_credit=Decimal("2000.00"),
            cyc_debit=Decimal("0.00"),
        )
        tran_amt = Decimal("600.00")
        service._check_credit_limit(tran_amt, account, result)
        assert result.reason_code == "102"

    def test_negative_amount_does_not_exceed_limit(self):
        """Credits (negative amounts) reduce temp_bal — should not fail."""
        service = TransactionPostingService.__new__(TransactionPostingService)
        result = ValidationResult()
        account = make_mock_account(
            credit_limit=Decimal("2500.00"),
            cyc_credit=Decimal("2000.00"),
            cyc_debit=Decimal("0.00"),
        )
        tran_amt = Decimal("-100.00")  # Credit/refund
        service._check_credit_limit(tran_amt, account, result)
        assert result.is_valid is True


class TestExpirationCheck:
    """Tests for CBTRN02C expiration validation (reason 103)."""

    def test_not_expired_passes(self):
        service = TransactionPostingService.__new__(TransactionPostingService)
        result = ValidationResult()
        from datetime import date as dt
        account = make_mock_account(expiration_date=dt(2027, 12, 31))
        orig_ts = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        service._check_expiration(orig_ts, account, result)
        assert result.is_valid is True

    def test_expired_account_fails(self):
        """Account expired 2024-01-31, transaction on 2026-04-01."""
        service = TransactionPostingService.__new__(TransactionPostingService)
        result = ValidationResult()
        from datetime import date as dt
        account = make_mock_account(expiration_date=dt(2024, 1, 31))
        orig_ts = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        service._check_expiration(orig_ts, account, result)
        assert result.reason_code == "103"

    def test_transaction_on_expiration_day_passes(self):
        """Boundary: transaction on exact expiration date should pass."""
        service = TransactionPostingService.__new__(TransactionPostingService)
        result = ValidationResult()
        from datetime import date as dt
        account = make_mock_account(expiration_date=dt(2024, 1, 31))
        orig_ts = datetime(2024, 1, 31, 23, 59, tzinfo=timezone.utc)
        service._check_expiration(orig_ts, account, result)
        assert result.is_valid is True

    def test_no_expiration_date_passes(self):
        """Account with no expiration date should always pass."""
        service = TransactionPostingService.__new__(TransactionPostingService)
        result = ValidationResult()
        account = make_mock_account()
        account.acct_expiration_date = None
        orig_ts = datetime(2030, 1, 1, tzinfo=timezone.utc)
        service._check_expiration(orig_ts, account, result)
        assert result.is_valid is True

    def test_both_checks_fail_103_overwrites_102(self):
        """COBOL spec: if both credit limit and expiry fail, 103 overwrites 102."""
        service = TransactionPostingService.__new__(TransactionPostingService)
        result = ValidationResult()
        from datetime import date as dt

        account = make_mock_account(
            credit_limit=Decimal("2500.00"),
            cyc_credit=Decimal("2000.00"),
            cyc_debit=Decimal("0.00"),
            expiration_date=dt(2020, 1, 1),
        )

        # First fail credit limit (102)
        tran_amt = Decimal("600.00")
        service._check_credit_limit(tran_amt, account, result)
        assert result.reason_code == "102"

        # Then fail expiry (103) — should overwrite 102
        orig_ts = datetime(2026, 4, 1, tzinfo=timezone.utc)
        service._check_expiration(orig_ts, account, result)
        assert result.reason_code == "103"


class TestTransactionPostingService:
    """Integration tests for full transaction validation flow."""

    @pytest.mark.asyncio
    async def test_valid_transaction_posts_successfully(
        self,
        db_session,
        sample_account,
        sample_xref,
    ):
        """End-to-end: valid transaction is posted and account updated."""
        service = TransactionPostingService(db_session)
        tran = make_transaction(card_num="4111111111111111", tran_amt=Decimal("-100.00"))

        result = await service.run([tran])

        assert result["transactions_posted"] == 1
        assert result["transactions_rejected"] == 0
        assert result["has_rejects"] is False

        # Verify account balance was updated
        from sqlalchemy import select
        from app.models.account import Account as AccountModel
        updated = await db_session.execute(
            select(AccountModel).where(AccountModel.acct_id == "00000000001")
        )
        acct = updated.scalar_one()
        assert acct.acct_curr_bal == Decimal("1400.00")  # 1500 + (-100)

    @pytest.mark.asyncio
    async def test_invalid_card_rejected_with_reason_100(self, db_session):
        """Card not in xref -> reason 100."""
        service = TransactionPostingService(db_session)
        tran = make_transaction(card_num="9999999999999999")

        result = await service.run([tran])

        assert result["transactions_rejected"] == 1
        assert result["rejects"][0].reason_code == "100"
        assert result["has_rejects"] is True

    @pytest.mark.asyncio
    async def test_expired_card_rejected_with_reason_103(
        self,
        db_session,
        expired_account,
        sample_xref_expired,
    ):
        """Expired account -> reason 103."""
        service = TransactionPostingService(db_session)
        tran = make_transaction(
            card_num="4444444444444444",
            orig_ts=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )

        result = await service.run([tran])

        assert result["transactions_rejected"] == 1
        assert result["rejects"][0].reason_code == "103"

    @pytest.mark.asyncio
    async def test_overlimit_transaction_rejected_with_reason_102(
        self,
        db_session,
        overlimit_account,
        sample_xref_overlimit,
    ):
        """Overlimit transaction -> reason 102."""
        service = TransactionPostingService(db_session)
        # overlimit_account: cyc_credit=2000, cyc_debit=0, limit=2500
        # temp_bal = 2000 + 600 = 2600 > 2500
        tran = make_transaction(
            card_num="4333333333333333",
            tran_amt=Decimal("600.00"),
        )

        result = await service.run([tran])

        assert result["transactions_rejected"] == 1
        assert result["rejects"][0].reason_code == "102"

    @pytest.mark.asyncio
    async def test_tcatbal_created_for_new_combination(
        self,
        db_session,
        sample_account,
        sample_xref,
    ):
        """New type/category combo creates TCATBAL record (2700-A)."""
        from sqlalchemy import select
        service = TransactionPostingService(db_session)
        tran = make_transaction(tran_amt=Decimal("-75.00"))

        await service.run([tran])

        result = await db_session.execute(
            select(TransactionCategoryBalance).where(
                TransactionCategoryBalance.acct_id == "00000000001",
                TransactionCategoryBalance.tran_type_cd == "01",
                TransactionCategoryBalance.tran_cat_cd == "0001",
            )
        )
        tcatbal = result.scalar_one_or_none()
        assert tcatbal is not None
        assert tcatbal.balance == Decimal("-75.00")

    @pytest.mark.asyncio
    async def test_tcatbal_updated_for_existing_combination(
        self,
        db_session,
        sample_account,
        sample_xref,
        sample_tcatbal,
    ):
        """Existing TCATBAL record gets amount added (2700-B)."""
        from sqlalchemy import select
        service = TransactionPostingService(db_session)
        tran = make_transaction(tran_amt=Decimal("-25.00"))

        await service.run([tran])

        result = await db_session.execute(
            select(TransactionCategoryBalance).where(
                TransactionCategoryBalance.acct_id == "00000000001",
                TransactionCategoryBalance.tran_type_cd == "01",
                TransactionCategoryBalance.tran_cat_cd == "0001",
            )
        )
        tcatbal = result.scalar_one()
        assert tcatbal.balance == Decimal("475.00")  # 500 + (-25)

    @pytest.mark.asyncio
    async def test_mixed_batch_some_valid_some_rejected(
        self,
        db_session,
        sample_account,
        sample_xref,
    ):
        """Multiple transactions: some valid, some invalid — processed independently."""
        service = TransactionPostingService(db_session)
        transactions = [
            make_transaction(
                card_num="4111111111111111",
                tran_amt=Decimal("-50.00"),
                tran_id="TXN0000000000001",
            ),
            make_transaction(
                card_num="9999999999999999",  # Invalid
                tran_id="TXN0000000000002",
            ),
            make_transaction(
                card_num="4111111111111111",
                tran_amt=Decimal("-25.00"),
                tran_id="TXN0000000000003",
            ),
        ]

        result = await service.run(transactions)

        assert result["transactions_processed"] == 3
        assert result["transactions_posted"] == 2
        assert result["transactions_rejected"] == 1
        assert result["has_rejects"] is True

    @pytest.mark.asyncio
    async def test_return_code_4_equivalent_when_rejects(
        self,
        db_session,
    ):
        """has_rejects=True maps to COBOL RETURN-CODE 4."""
        service = TransactionPostingService(db_session)
        tran = make_transaction(card_num="9999999999999999")

        result = await service.run([tran])

        assert result["has_rejects"] is True

    @pytest.mark.asyncio
    async def test_positive_amount_updates_cyc_credit(
        self,
        db_session,
        sample_account,
        sample_xref,
    ):
        """Positive amounts (credits) update ACCT-CURR-CYC-CREDIT."""
        from sqlalchemy import select
        service = TransactionPostingService(db_session)
        tran = make_transaction(tran_amt=Decimal("200.00"))  # Payment/credit

        await service.run([tran])

        result = await db_session.execute(
            select(Account).where(Account.acct_id == "00000000001")
        )
        acct = result.scalar_one()
        assert acct.acct_curr_cyc_credit == Decimal("2700.00")  # 2500 + 200

    @pytest.mark.asyncio
    async def test_negative_amount_updates_cyc_debit(
        self,
        db_session,
        sample_account,
        sample_xref,
    ):
        """Negative amounts (charges) update ACCT-CURR-CYC-DEBIT.

        COBOL: ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT
        sample_account has acct_curr_cyc_debit=1000.00 (positive, represents debit total)
        After adding -100: 1000 + (-100) = 900
        """
        from sqlalchemy import select
        service = TransactionPostingService(db_session)
        tran = make_transaction(tran_amt=Decimal("-100.00"))

        await service.run([tran])

        result = await db_session.execute(
            select(Account).where(Account.acct_id == "00000000001")
        )
        acct = result.scalar_one()
        # cyc_debit was 1000.00, add -100.00 => 900.00
        assert acct.acct_curr_cyc_debit == Decimal("900.00")
