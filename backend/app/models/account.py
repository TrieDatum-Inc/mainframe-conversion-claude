"""
Account ORM model — maps ACCTDAT VSAM KSDS to PostgreSQL `accounts` table.

COBOL source: CVACT01Y copybook, ACCTDAT VSAM KSDS (300-byte record)
CICS access: EXEC CICS READ/REWRITE DATASET('ACCTDAT')

Record layout (CVACT01Y):
  ACCT-ID                  PIC 9(11)       → account_id    BIGINT PK
  ACCT-ACTIVE-STATUS       PIC X(01)       → active_status CHAR(1) CHECK IN ('Y','N')
  ACCT-CURR-BAL            PIC S9(10)V99   → current_balance NUMERIC(12,2)
  ACCT-CREDIT-LIMIT        PIC S9(10)V99   → credit_limit    NUMERIC(12,2)
  ACCT-CASH-CREDIT-LIMIT   PIC S9(10)V99   → cash_credit_limit NUMERIC(12,2)
  ACCT-OPEN-DATE           PIC X(10)       → open_date     DATE
  ACCT-EXPIRAION-DATE      PIC X(10)       → expiration_date DATE
  ACCT-REISSUE-DATE        PIC X(10)       → reissue_date   DATE
  ACCT-CURR-CYC-CREDIT     PIC S9(10)V99   → curr_cycle_credit NUMERIC(12,2)
  ACCT-CURR-CYC-DEBIT      PIC S9(10)V99   → curr_cycle_debit  NUMERIC(12,2)
  ACCT-ADDR-ZIP            PIC X(10)       → (not used separately; customer has zip)
  ACCT-GROUP-ID            PIC X(10)       → group_id       VARCHAR(10)
"""

from datetime import date, datetime

from sqlalchemy import BigInteger, CHAR, CheckConstraint, Date, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Account(Base):
    """
    PostgreSQL `accounts` table.

    Replaces ACCTDAT VSAM KSDS (CVACT01Y copybook, 300-byte record).
    Primary key: ACCT-ID PIC 9(11) → BIGINT.
    Financial fields use NUMERIC(12,2) to preserve COBOL S9(10)V99 precision.
    """

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("active_status IN ('Y', 'N')", name="chk_accounts_active_status"),
        CheckConstraint("credit_limit >= 0", name="chk_accounts_credit_limit_positive"),
        CheckConstraint(
            "cash_credit_limit >= 0 AND cash_credit_limit <= credit_limit",
            name="chk_accounts_cash_limit_range",
        ),
    )

    # ACCT-ID PIC 9(11) — VSAM KSDS primary key
    account_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True,
        comment="COBOL: ACCT-ID PIC 9(11) — VSAM KSDS primary key",
    )

    # ACCT-ACTIVE-STATUS PIC X(01) — Y/N
    active_status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="Y",
        comment="COBOL: ACCT-ACTIVE-STATUS PIC X(01) — Y/N",
    )

    # Financial fields — COBOL S9(10)V99 → NUMERIC(12,2)
    current_balance: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0,
        comment="COBOL: ACCT-CURR-BAL PIC S9(10)V99",
    )
    credit_limit: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0,
        comment="COBOL: ACCT-CREDIT-LIMIT PIC S9(10)V99",
    )
    cash_credit_limit: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0,
        comment="COBOL: ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99",
    )
    curr_cycle_credit: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0,
        comment="COBOL: ACCT-CURR-CYC-CREDIT PIC S9(10)V99",
    )
    curr_cycle_debit: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0,
        comment="COBOL: ACCT-CURR-CYC-DEBIT PIC S9(10)V99",
    )

    # Date fields — COBOL PIC X(10) storing YYYY-MM-DD → DATE
    open_date: Mapped[date | None] = mapped_column(
        Date, nullable=True,
        comment="COBOL: ACCT-OPEN-DATE PIC X(10)",
    )
    expiration_date: Mapped[date | None] = mapped_column(
        Date, nullable=True,
        comment="COBOL: ACCT-EXPIRAION-DATE PIC X(10) (note: COBOL typo preserved)",
    )
    reissue_date: Mapped[date | None] = mapped_column(
        Date, nullable=True,
        comment="COBOL: ACCT-REISSUE-DATE PIC X(10)",
    )

    # ACCT-GROUP-ID PIC X(10)
    group_id: Mapped[str | None] = mapped_column(
        String(10), nullable=True,
        comment="COBOL: ACCT-GROUP-ID PIC X(10)",
    )

    # Audit timestamps — not in COBOL source
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
        comment="Optimistic lock version — replaces COACTUPC WS-DATACHANGED-FLAG",
    )

    def __repr__(self) -> str:
        return f"<Account account_id={self.account_id} status={self.active_status!r}>"
