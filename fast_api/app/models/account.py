"""
SQLAlchemy ORM model for the `accounts` table.

Source copybook: app/cpy/CVACT01Y.cpy — ACCOUNT-RECORD (300 bytes)
Source VSAM file: AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS (ACCTDAT)
Primary key: ACCT-ID PIC 9(11) → BigInt

Access patterns mapped from CICS:
  EXEC CICS READ FILE(ACCTDAT)     → AccountRepository.get_by_id()
  EXEC CICS REWRITE FILE(ACCTDAT) → AccountRepository.update()
"""
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, Date, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Account(Base):
    """
    Credit card account record.

    Maps to COBOL ACCOUNT-RECORD (CVACT01Y.cpy).
    All monetary fields use NUMERIC(12,2) to preserve COMP-3 precision.
    """

    __tablename__ = "accounts"
    __table_args__ = (
        # ACCT-ACTIVE-STATUS PIC X(01): valid values 'Y' or 'N'
        CheckConstraint("active_status IN ('Y', 'N')", name="ck_accounts_active_status"),
        # ACCT-CREDIT-LIMIT must be positive
        CheckConstraint("credit_limit >= 0", name="ck_accounts_credit_limit_positive"),
        Index("ix_accounts_group_id", "group_id"),
    )

    # ACCT-ID PIC 9(11) — primary key
    acct_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="ACCT-ID PIC 9(11)")

    # ACCT-ACTIVE-STATUS PIC X(01) — 'Y'=active, 'N'=inactive
    active_status: Mapped[str] = mapped_column(
        String(1), nullable=False, default="Y", comment="ACCT-ACTIVE-STATUS PIC X(01)"
    )

    # ACCT-CURR-BAL PIC S9(10)V99 COMP-3
    curr_bal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), comment="ACCT-CURR-BAL PIC S9(10)V99"
    )

    # ACCT-CREDIT-LIMIT PIC S9(10)V99 COMP-3
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), comment="ACCT-CREDIT-LIMIT PIC S9(10)V99"
    )

    # ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99 COMP-3
    cash_credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), comment="ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99"
    )

    # ACCT-OPEN-DATE PIC X(10) format YYYY-MM-DD
    open_date: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="ACCT-OPEN-DATE PIC X(10)")

    # ACCT-EXPIRAION-DATE PIC X(10) — note: typo in original COBOL retained as comment
    expiration_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="ACCT-EXPIRAION-DATE PIC X(10) [typo in original copybook]"
    )

    # ACCT-REISSUE-DATE PIC X(10)
    reissue_date: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="ACCT-REISSUE-DATE PIC X(10)")

    # ACCT-CURR-CYC-CREDIT PIC S9(10)V99 COMP-3
    curr_cycle_credit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), comment="ACCT-CURR-CYC-CREDIT PIC S9(10)V99"
    )

    # ACCT-CURR-CYC-DEBIT PIC S9(10)V99 COMP-3
    curr_cycle_debit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), comment="ACCT-CURR-CYC-DEBIT PIC S9(10)V99"
    )

    # ACCT-ADDR-ZIP PIC X(10)
    addr_zip: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="ACCT-ADDR-ZIP PIC X(10)")

    # ACCT-GROUP-ID PIC X(10) — links to disclosure_groups for interest calculation
    group_id: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="ACCT-GROUP-ID PIC X(10)")

    # Relationships (lazy loaded to avoid circular import issues)
    cards: Mapped[list["Card"]] = relationship("Card", back_populates="account", lazy="select")
    card_xrefs: Mapped[list["CardXref"]] = relationship("CardXref", back_populates="account", lazy="select")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="account", lazy="select",
        foreign_keys="Transaction.acct_id",
    )
    tran_cat_balances: Mapped[list["TranCatBalance"]] = relationship(
        "TranCatBalance", back_populates="account", lazy="select"
    )
    auth_summary: Mapped["AuthSummary | None"] = relationship(  # noqa: F821
        "AuthSummary", back_populates="account", lazy="select", uselist=False
    )
