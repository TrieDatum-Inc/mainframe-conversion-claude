"""Account ORM model — maps to the `accounts` table (ACCTDAT VSAM KSDS equivalent).

COBOL source copybook: CVACT01Y.cpy
COBOL 01-level: ACCOUNT-RECORD (300-byte record)
Key field: ACCT-ID PIC 9(11) — stored as NUMERIC(11) PRIMARY KEY

Used by COBIL00C (Bill Payment) to read balance and zero it after payment.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CHAR, DATE, NUMERIC, TIMESTAMP, VARCHAR, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Account(Base):
    """Maps to accounts table.

    Business rules from COBIL00C:
      BR-001: ACCT-ID must not be empty (ACTIDINI check).
      BR-003: ACCT-CURR-BAL <= 0 → 'You have nothing to pay...' error.
      BR-004: Payment always zeroes ACCT-CURR-BAL (ACCT-CURR-BAL - TRAN-AMT where TRAN-AMT = ACCT-CURR-BAL).
    """

    __tablename__ = "accounts"

    acct_id: Mapped[int] = mapped_column(
        NUMERIC(11, 0),
        primary_key=True,
        comment="ACCT-ID PIC 9(11) — account number",
    )
    active_status: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        server_default=text("'Y'"),
        comment="ACCT-ACTIVE-STATUS PIC X(01): Y=Active N=Inactive",
    )
    curr_bal: Mapped[Decimal] = mapped_column(
        NUMERIC(12, 2),
        nullable=False,
        server_default=text("0"),
        comment="ACCT-CURR-BAL S9(10)V99 — current outstanding balance",
    )
    credit_limit: Mapped[Decimal] = mapped_column(
        NUMERIC(12, 2),
        nullable=False,
        server_default=text("0"),
        comment="ACCT-CREDIT-LIMIT S9(10)V99",
    )
    cash_credit_limit: Mapped[Decimal] = mapped_column(
        NUMERIC(12, 2),
        nullable=False,
        server_default=text("0"),
        comment="ACCT-CASH-CREDIT-LIMIT S9(10)V99",
    )
    open_date: Mapped[date | None] = mapped_column(
        DATE,
        nullable=True,
        comment="ACCT-OPEN-DATE X(10) YYYY-MM-DD",
    )
    expiration_date: Mapped[date | None] = mapped_column(
        DATE,
        nullable=True,
        comment="ACCT-EXPIRAION-DATE X(10) [typo preserved from COBOL source]",
    )
    reissue_date: Mapped[date | None] = mapped_column(
        DATE,
        nullable=True,
        comment="ACCT-REISSUE-DATE X(10)",
    )
    curr_cycle_credit: Mapped[Decimal] = mapped_column(
        NUMERIC(12, 2),
        nullable=False,
        server_default=text("0"),
        comment="ACCT-CURR-CYC-CREDIT — total credits this cycle",
    )
    curr_cycle_debit: Mapped[Decimal] = mapped_column(
        NUMERIC(12, 2),
        nullable=False,
        server_default=text("0"),
        comment="ACCT-CURR-CYC-DEBIT — total debits this cycle",
    )
    addr_zip: Mapped[str | None] = mapped_column(
        VARCHAR(10),
        nullable=True,
        comment="ACCT-ADDR-ZIP PIC X(10)",
    )
    group_id: Mapped[str | None] = mapped_column(
        VARCHAR(10),
        nullable=True,
        comment="ACCT-GROUP-ID PIC X(10) — links to disclosure_groups",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def has_balance(self) -> bool:
        """True when curr_bal > 0 (COBIL00C balance check guard)."""
        return self.curr_bal > Decimal("0")
