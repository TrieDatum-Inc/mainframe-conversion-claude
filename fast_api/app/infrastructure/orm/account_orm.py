"""
SQLAlchemy ORM model for the Account entity.

Source: VSAM KSDS ACCTDAT / copybook CVACT01Y (300 bytes)
Primary key: ACCT-ID PIC 9(11)

Field mapping:
  ACCT-ID                PIC 9(11)       -> acct_id         BIGINT PRIMARY KEY
  ACCT-ACTIVE-STATUS     PIC X(01)       -> active_status   CHAR(1)
  ACCT-CURR-BAL          PIC S9(10)V99   -> curr_bal        NUMERIC(12,2)
  ACCT-CREDIT-LIMIT      PIC S9(10)V99   -> credit_limit    NUMERIC(12,2)
  ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99   -> cash_credit_limit NUMERIC(12,2)
  ACCT-OPEN-DATE         PIC X(10)       -> open_date       DATE (YYYY-MM-DD)
  ACCT-EXPIRAION-DATE    PIC X(10)       -> expiration_date DATE (note: original typo kept)
  ACCT-REISSUE-DATE      PIC X(10)       -> reissue_date    DATE
  ACCT-CURR-CYC-CREDIT   PIC S9(10)V99   -> curr_cycle_credit NUMERIC(12,2)
  ACCT-CURR-CYC-DEBIT    PIC S9(10)V99   -> curr_cycle_debit  NUMERIC(12,2)
  ACCT-ADDR-ZIP          PIC X(10)       -> addr_zip        VARCHAR(10)
  ACCT-GROUP-ID          PIC X(10)       -> group_id        VARCHAR(10)
  FILLER                 PIC X(178)      -> (omitted)
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import CHAR, DATE, NUMERIC, VARCHAR, BigInteger, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class AccountORM(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("active_status IN ('Y', 'N')", name="ck_account_active_status"),
        CheckConstraint("acct_id > 0", name="ck_account_id_positive"),
        Index("ix_accounts_group_id", "group_id"),
    )

    # ACCT-ID PIC 9(11) - max 99999999999 = 11 digits
    acct_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # ACCT-ACTIVE-STATUS PIC X(01) - 'Y'=active, 'N'=inactive
    active_status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="Y")

    # ACCT-CURR-BAL PIC S9(10)V99 - signed 10 integer + 2 decimal = 12 total
    curr_bal: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00"))

    # ACCT-CREDIT-LIMIT PIC S9(10)V99
    credit_limit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00"))

    # ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99
    cash_credit_limit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00"))

    # ACCT-OPEN-DATE PIC X(10) - stored as YYYY-MM-DD string in COBOL, DATE in PostgreSQL
    open_date: Mapped[date | None] = mapped_column(DATE, nullable=True)

    # ACCT-EXPIRAION-DATE PIC X(10) - note: original COBOL has typo 'EXPIRAION'
    expiration_date: Mapped[date | None] = mapped_column(DATE, nullable=True)

    # ACCT-REISSUE-DATE PIC X(10)
    reissue_date: Mapped[date | None] = mapped_column(DATE, nullable=True)

    # ACCT-CURR-CYC-CREDIT PIC S9(10)V99 - cycle credit accumulator (reset by CBACT04C)
    curr_cycle_credit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00"))

    # ACCT-CURR-CYC-DEBIT PIC S9(10)V99 - cycle debit accumulator (reset by CBACT04C)
    curr_cycle_debit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False, default=Decimal("0.00"))

    # ACCT-ADDR-ZIP PIC X(10)
    addr_zip: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)

    # ACCT-GROUP-ID PIC X(10) - used for disclosure rate lookup in CBACT04C
    group_id: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)

    def __repr__(self) -> str:
        return f"<Account id={self.acct_id} status={self.active_status} bal={self.curr_bal}>"
