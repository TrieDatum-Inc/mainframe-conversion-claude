"""ORM models for the Account and Customer module.

Migrated from VSAM KSDS files:
  ACCTDATA (ACCTDAT) -> Account
  CUSTDATA (CUSTDAT) -> Customer

COBOL copybook mappings:
  CVACT01Y -> Account  (ACCOUNT-RECORD, 300 bytes, key ACCT-ID 9(11))
  CVCUS01Y -> Customer (CUSTOMER-RECORD, 500 bytes, key CUST-ID 9(9))
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Account(Base):
    """Maps to ACCTDATA VSAM KSDS — ACCOUNT-RECORD (CVACT01Y).

    Key field: ACCT-ID PIC 9(11) -> account_id VARCHAR(11)
    Financial fields use NUMERIC(12,2) for exact decimal arithmetic.
    """

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint(
            "active_status IN ('Y', 'N')",
            name="ck_accounts_active_status",
        ),
        CheckConstraint(
            "credit_limit >= 0",
            name="ck_accounts_credit_limit_nonneg",
        ),
        CheckConstraint(
            "cash_credit_limit >= 0",
            name="ck_accounts_cash_credit_limit_nonneg",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ACCT-ID PIC 9(11) — primary VSAM key, stored as string to preserve leading zeros
    account_id: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False, index=True
    )

    # ACCT-ACTIVE-STATUS PIC X(1) — 'Y' active, 'N' inactive
    active_status: Mapped[str] = mapped_column(
        String(1), nullable=False, default="Y"
    )

    # ACCT-CURR-BAL PIC S9(10)V99 COMP-3 — signed decimal
    current_balance: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    # ACCT-CREDIT-LIMIT PIC 9(10)V99 COMP-3
    credit_limit: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    # ACCT-CASH-CREDIT-LIMIT PIC 9(10)V99 COMP-3
    cash_credit_limit: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    # ACCT-OPEN-DATE PIC X(10) — stored as DATE
    open_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ACCT-EXPIRAION-DATE PIC X(10)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ACCT-REISSUE-DATE PIC X(10)
    reissue_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ACCT-CURR-CYC-CREDIT PIC S9(10)V99 COMP-3
    current_cycle_credit: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    # ACCT-CURR-CYC-DEBIT PIC S9(10)V99 COMP-3
    current_cycle_debit: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )

    # ACCT-ADDR-ZIP — zip portion from address (cross-validation with state)
    address_zip: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # ACCT-GROUP-ID PIC X(10) — FK to DISCGRP
    group_id: Mapped[str | None] = mapped_column(String(10), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # One-to-many: an account has many cards
    cards: Mapped[list["Card"]] = relationship(  # noqa: F821
        "Card", back_populates="account", lazy="selectin"
    )

    # One-to-many: an account has many xref records
    card_xrefs: Mapped[list["CardXref"]] = relationship(  # noqa: F821
        "CardXref", back_populates="account", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Account account_id={self.account_id!r} status={self.active_status!r}>"


class Customer(Base):
    """Maps to CUSTDATA VSAM KSDS — CUSTOMER-RECORD (CVCUS01Y).

    Key field: CUST-ID PIC 9(9) -> customer_id VARCHAR(9)
    """

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint(
            "primary_card_holder IN ('Y', 'N')",
            name="ck_customers_primary_card_holder",
        ),
        CheckConstraint(
            "fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)",
            name="ck_customers_fico_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # CUST-ID PIC 9(9) — primary VSAM key
    customer_id: Mapped[str] = mapped_column(
        String(9), unique=True, nullable=False, index=True
    )

    # CUST-FIRST-NAME PIC X(25)
    first_name: Mapped[str] = mapped_column(String(25), nullable=False, default="")

    # CUST-MIDDLE-NAME PIC X(25)
    middle_name: Mapped[str] = mapped_column(String(25), nullable=False, default="")

    # CUST-LAST-NAME PIC X(25)
    last_name: Mapped[str] = mapped_column(String(25), nullable=False, default="")

    # CUST-ADDR-LINE-1/2/3 PIC X(50)
    address_line_1: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    address_line_2: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    address_line_3: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # CUST-ADDR-STATE-CD PIC X(2)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False, default="")

    # CUST-ADDR-COUNTRY-CD PIC X(3)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, default="")

    # CUST-ADDR-ZIP PIC X(10)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False, default="")

    # CUST-PHONE-NUM-1 PIC X(15) — format (xxx)xxx-xxxx
    phone_1: Mapped[str] = mapped_column(String(15), nullable=False, default="")

    # CUST-PHONE-NUM-2 PIC X(15)
    phone_2: Mapped[str] = mapped_column(String(15), nullable=False, default="")

    # CUST-SSN PIC 9(9) — stored as string to preserve leading zeros
    ssn: Mapped[str] = mapped_column(String(9), nullable=False, default="")

    # CUST-GOVT-ISSUED-ID PIC X(20)
    govt_issued_id: Mapped[str] = mapped_column(String(20), nullable=False, default="")

    # CUST-DOB-YYYY-MM-DD
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    # CUST-EFT-ACCOUNT-ID PIC X(10)
    eft_account_id: Mapped[str] = mapped_column(String(10), nullable=False, default="")

    # CUST-PRI-CARD-HOLDER-IND PIC X(1) — 'Y' or 'N'
    primary_card_holder: Mapped[str] = mapped_column(
        String(1), nullable=False, default="Y"
    )

    # CUST-FICO-CREDIT-SCORE PIC 9(3)
    fico_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to xref
    card_xrefs: Mapped[list["CardXref"]] = relationship(  # noqa: F821
        "CardXref", back_populates="customer", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<Customer customer_id={self.customer_id!r} "
            f"name={self.first_name!r} {self.last_name!r}>"
        )
