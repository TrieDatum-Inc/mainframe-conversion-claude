"""
Account ORM model — maps to the `accounts` PostgreSQL table.

COBOL origin: ACCTDAT VSAM KSDS (CVACT01Y copybook), record length 300 bytes.
  - ACCT-ID                9(11)            → account_id BIGINT PRIMARY KEY
  - ACCT-ACTIVE-STATUS     X(1)             → active_status CHAR(1) CHECK IN ('Y','N')
  - ACCT-CURR-BAL          S9(10)V99 COMP-3 → current_balance NUMERIC(12,2)
  - ACCT-CREDIT-LIMIT      S9(10)V99 COMP-3 → credit_limit NUMERIC(12,2)
  - ACCT-CASH-CREDIT-LIMIT S9(10)V99 COMP-3 → cash_credit_limit NUMERIC(12,2)
  - ACCT-OPEN-DATE         X(10)            → open_date DATE  (YYYY-MM-DD format)
  - ACCT-EXPIRAION-DATE    X(10)            → expiration_date DATE  (typo in COBOL source preserved as comment)
  - ACCT-REISSUE-DATE      X(10)            → reissue_date DATE
  - ACCT-CURR-CYC-CREDIT   S9(10)V99 COMP-3 → curr_cycle_credit NUMERIC(12,2)
  - ACCT-CURR-CYC-DEBIT    S9(10)V99 COMP-3 → curr_cycle_debit NUMERIC(12,2)
  - ACCT-ADDR-ZIP          X(10)            → zip_code VARCHAR(10)
  - ACCT-GROUP-ID          X(10)            → group_id VARCHAR(10)
  - FILLER X(178)                           → NOT STORED (padding bytes discarded)

Replaces CICS file-control access pattern:
  EXEC CICS READ DATASET('ACCTDAT') INTO(ACCOUNT-RECORD) RIDFLD(ACCT-ID) RESP RESP2
  RESP=NORMAL  → account found
  RESP=NOTFND  → 404 ACCOUNT_NOT_FOUND
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        nullable=False,
        comment="ACCT-ID 9(11) — VSAM KSDS primary key",
    )
    active_status: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
        default="Y",
        comment="ACCT-ACTIVE-STATUS X(1): Y=Active, N=Inactive",
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="ACCT-CURR-BAL S9(10)V99 COMP-3 — signed packed decimal",
    )
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="ACCT-CREDIT-LIMIT S9(10)V99 COMP-3",
    )
    cash_credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="ACCT-CASH-CREDIT-LIMIT S9(10)V99 COMP-3",
    )
    open_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="ACCT-OPEN-DATE X(10) — ISO YYYY-MM-DD",
    )
    expiration_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="ACCT-EXPIRAION-DATE X(10) — note: typo preserved from COBOL source",
    )
    reissue_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="ACCT-REISSUE-DATE X(10)",
    )
    curr_cycle_credit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="ACCT-CURR-CYC-CREDIT S9(10)V99 COMP-3",
    )
    curr_cycle_debit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3",
    )
    zip_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="ACCT-ADDR-ZIP X(10)",
    )
    group_id: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="ACCT-GROUP-ID X(10) — AADDGRP BMS field",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("active_status IN ('Y', 'N')", name="chk_accounts_active"),
        CheckConstraint("credit_limit >= 0", name="chk_accounts_credit_limit"),
        CheckConstraint("cash_credit_limit >= 0", name="chk_accounts_cash_limit"),
        CheckConstraint(
            "cash_credit_limit <= credit_limit",
            name="chk_accounts_cash_lte_credit",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Account account_id={self.account_id!r} "
            f"active_status={self.active_status!r}>"
        )
