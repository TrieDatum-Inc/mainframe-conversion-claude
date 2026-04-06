"""
SQLAlchemy ORM model for the `accounts` table.

COBOL origin: ACCTDAT VSAM KSDS (CVACT01Y copybook).
Record length: 300 bytes.

Field mapping:
  ACCT-ID               9(11)           → account_id BIGINT PRIMARY KEY
  ACCT-ACTIVE-STATUS    X(1)            → active_status CHAR(1) CHECK IN ('Y','N')
  ACCT-CURR-BAL         S9(10)V99 COMP-3 → current_balance NUMERIC(12,2)
  ACCT-CREDIT-LIMIT     S9(10)V99 COMP-3 → credit_limit NUMERIC(12,2)
  ACCT-CASH-CREDIT-LIMIT S9(10)V99 COMP-3 → cash_credit_limit NUMERIC(12,2)
  ACCT-OPEN-DATE        X(10)           → open_date DATE (YYYY-MM-DD)
  ACCT-EXPIRAION-DATE   X(10)           → expiration_date DATE (typo in source preserved as comment)
  ACCT-REISSUE-DATE     X(10)           → reissue_date DATE
  ACCT-CURR-CYC-CREDIT  S9(10)V99 COMP-3 → curr_cycle_credit NUMERIC(12,2)
  ACCT-CURR-CYC-DEBIT   S9(10)V99 COMP-3 → curr_cycle_debit NUMERIC(12,2)
  ACCT-ADDR-ZIP         X(10)           → zip_code VARCHAR(10)
  ACCT-GROUP-ID         X(10)           → group_id VARCHAR(10)
  FILLER X(178)                          → (not stored; padding bytes discarded)

CICS access: READ ACCTDAT by ACCT-ID → SELECT WHERE account_id = ?
COACTVWC: READ UPDATE for view (bug in original — fixed to regular read)
COACTUPC: READ UPDATE → SELECT FOR UPDATE → UPDATE
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CHAR, CheckConstraint, Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Account(Base):
    """
    PostgreSQL `accounts` table.

    Replaces ACCTDAT VSAM KSDS.
    COACTVWC reads this to display account summary (rows 3-10 of CACTVWA map).
    COACTUPC reads and updates this with all financial fields.
    """

    __tablename__ = "accounts"

    __table_args__ = (
        CheckConstraint("active_status IN ('Y', 'N')", name="chk_accounts_active"),
        CheckConstraint("credit_limit >= 0", name="chk_accounts_credit_limit"),
        CheckConstraint("cash_credit_limit >= 0", name="chk_accounts_cash_limit"),
        CheckConstraint(
            "cash_credit_limit <= credit_limit", name="chk_accounts_cash_lte_credit"
        ),
    )

    # ACCT-ID 9(11) — VSAM KSDS primary key; 11-digit numeric
    account_id: Mapped[int] = mapped_column(
        "account_id",
        primary_key=True,
        comment="COBOL: ACCT-ID 9(11) — VSAM KSDS primary key",
    )

    # ACCT-ACTIVE-STATUS X(1) — Y=active, N=inactive
    active_status: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        default="Y",
        comment="COBOL: ACCT-ACTIVE-STATUS X(1) — ACSTTUS field on CACTVWA map",
    )

    # ACCT-CURR-BAL S9(10)V99 COMP-3 — signed packed decimal
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="COBOL: ACCT-CURR-BAL S9(10)V99 COMP-3 — ACURBAL on map; PICOUT='+ZZZ,ZZZ,ZZZ.99'",
    )

    # ACCT-CREDIT-LIMIT S9(10)V99 COMP-3
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="COBOL: ACCT-CREDIT-LIMIT S9(10)V99 COMP-3 — ACRDLIM on map",
    )

    # ACCT-CASH-CREDIT-LIMIT S9(10)V99 COMP-3
    cash_credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="COBOL: ACCT-CASH-CREDIT-LIMIT S9(10)V99 COMP-3 — ACSHLIM on map",
    )

    # ACCT-OPEN-DATE X(10) — stored as YYYY-MM-DD in VSAM
    open_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="COBOL: ACCT-OPEN-DATE X(10) — ADTOPEN on CACTVWA map",
    )

    # ACCT-EXPIRAION-DATE X(10) — note: typo 'EXPIRAION' preserved from source
    expiration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="COBOL: ACCT-EXPIRAION-DATE X(10) — typo in source; AEXPDT on map",
    )

    # ACCT-REISSUE-DATE X(10)
    reissue_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="COBOL: ACCT-REISSUE-DATE X(10) — AREISDT on map",
    )

    # ACCT-CURR-CYC-CREDIT S9(10)V99 COMP-3
    curr_cycle_credit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="COBOL: ACCT-CURR-CYC-CREDIT S9(10)V99 COMP-3 — ACRCYCR on map",
    )

    # ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3
    curr_cycle_debit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="COBOL: ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3 — ACRCYDB on map",
    )

    # ACCT-ADDR-ZIP X(10)
    zip_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="COBOL: ACCT-ADDR-ZIP X(10)",
    )

    # ACCT-GROUP-ID X(10)
    group_id: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="COBOL: ACCT-GROUP-ID X(10) — AADDGRP on map",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Row creation timestamp (not in original VSAM record)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last-modified timestamp; replaces WS-DATACHANGED-FLAG in COACTUPC",
    )

    def __repr__(self) -> str:
        return f"Account(account_id={self.account_id!r}, active_status={self.active_status!r})"
