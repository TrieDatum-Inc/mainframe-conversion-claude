"""
SQLAlchemy ORM models for Transaction entities.

Sources:
  TRANSACT  VSAM KSDS / copybook CVTRA05Y (350 bytes) - Transaction record
  CVTRA01Y  VSAM KSDS (50 bytes)                       - Tran category balance
  CVTRA02Y  VSAM KSDS (50 bytes)                       - Disclosure group rates
  CVTRA03Y  VSAM KSDS (60 bytes)                       - Transaction type codes
  CVTRA04Y  VSAM KSDS (60 bytes)                       - Transaction category codes

Transaction field mapping (CVTRA05Y):
  TRAN-ID              PIC X(16)         -> tran_id         VARCHAR(16) PK
  TRAN-TYPE-CD         PIC X(02)         -> tran_type_cd    CHAR(2)
  TRAN-CAT-CD          PIC 9(04)         -> tran_cat_cd     INTEGER
  TRAN-SOURCE          PIC X(10)         -> tran_source     VARCHAR(10)
  TRAN-DESC            PIC X(100)        -> tran_desc       VARCHAR(100)
  TRAN-AMT             PIC S9(09)V99     -> tran_amt        NUMERIC(11,2)
  TRAN-MERCHANT-ID     PIC 9(09)         -> merchant_id     INTEGER
  TRAN-MERCHANT-NAME   PIC X(50)         -> merchant_name   VARCHAR(50)
  TRAN-MERCHANT-CITY   PIC X(50)         -> merchant_city   VARCHAR(50)
  TRAN-MERCHANT-ZIP    PIC X(10)         -> merchant_zip    VARCHAR(10)
  TRAN-CARD-NUM        PIC X(16)         -> card_num        VARCHAR(16) FK->cards
  TRAN-ORIG-TS         PIC X(26)         -> orig_ts         TIMESTAMP
  TRAN-PROC-TS         PIC X(26)         -> proc_ts         TIMESTAMP
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    NUMERIC,
    VARCHAR,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    TIMESTAMP,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class TransactionORM(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_card_num", "card_num"),
        Index("ix_transactions_tran_type_cd", "tran_type_cd"),
        Index("ix_transactions_orig_ts", "orig_ts"),
        CheckConstraint(
            "tran_type_cd IS NOT NULL AND tran_type_cd != ''",
            name="ck_transaction_type_not_empty",
        ),
    )

    # TRAN-ID PIC X(16) - 16-character transaction ID (primary key)
    tran_id: Mapped[str] = mapped_column(VARCHAR(16), primary_key=True)

    # TRAN-TYPE-CD PIC X(02)
    tran_type_cd: Mapped[str] = mapped_column(CHAR(2), nullable=False)

    # TRAN-CAT-CD PIC 9(04)
    tran_cat_cd: Mapped[int] = mapped_column(Integer, nullable=False)

    # TRAN-SOURCE PIC X(10)
    tran_source: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)

    # TRAN-DESC PIC X(100)
    tran_desc: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)

    # TRAN-AMT PIC S9(09)V99 - signed 9+2 = 11 total digits
    tran_amt: Mapped[Decimal] = mapped_column(NUMERIC(11, 2), nullable=False)

    # TRAN-MERCHANT-ID PIC 9(09)
    merchant_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # TRAN-MERCHANT-NAME PIC X(50)
    merchant_name: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)

    # TRAN-MERCHANT-CITY PIC X(50)
    merchant_city: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)

    # TRAN-MERCHANT-ZIP PIC X(10)
    merchant_zip: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)

    # TRAN-CARD-NUM PIC X(16)
    card_num: Mapped[str] = mapped_column(
        VARCHAR(16),
        ForeignKey("cards.card_num", ondelete="RESTRICT"),
        nullable=False,
    )

    # TRAN-ORIG-TS PIC X(26) - ISO timestamp of origination
    orig_ts: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    # TRAN-PROC-TS PIC X(26) - ISO timestamp of processing
    proc_ts: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    def __repr__(self) -> str:
        return f"<Transaction id={self.tran_id} amt={self.tran_amt} card={self.card_num}>"


class TranCatBalORM(Base):
    """
    Transaction Category Balance record.
    Source: VSAM KSDS TRAN-CAT-BAL-FILE / copybook CVTRA01Y (50 bytes)

    Composite key: acct_id + tran_type_cd + tran_cat_cd
    Used by CBACT04C for interest calculation and CBTRN02C for cycle balance updates.
    """
    __tablename__ = "tran_cat_bal"
    __table_args__ = (
        Index("ix_tran_cat_bal_acct_id", "acct_id"),
    )

    # TRANCAT-ACCT-ID PIC 9(11)
    acct_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("accounts.acct_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # TRANCAT-TYPE-CD PIC X(02)
    tran_type_cd: Mapped[str] = mapped_column(CHAR(2), primary_key=True)

    # TRANCAT-CD PIC 9(04)
    tran_cat_cd: Mapped[int] = mapped_column(Integer, primary_key=True)

    # TRAN-CAT-BAL PIC S9(09)V99
    tran_cat_bal: Mapped[Decimal] = mapped_column(NUMERIC(11, 2), nullable=False, default=Decimal("0.00"))


class DisclosureGroupORM(Base):
    """
    Disclosure Group interest rate record.
    Source: VSAM KSDS DIS-GROUP-FILE / copybook CVTRA02Y (50 bytes)

    Key: acct_group_id + tran_type_cd + tran_cat_cd
    Used by CBACT04C to look up interest rates per account group/transaction category.
    """
    __tablename__ = "disclosure_groups"

    # DIS-ACCT-GROUP-ID PIC X(10)
    acct_group_id: Mapped[str] = mapped_column(VARCHAR(10), primary_key=True)

    # DIS-TRAN-TYPE-CD PIC X(02)
    tran_type_cd: Mapped[str] = mapped_column(CHAR(2), primary_key=True)

    # DIS-TRAN-CAT-CD PIC 9(04)
    tran_cat_cd: Mapped[int] = mapped_column(Integer, primary_key=True)

    # DIS-INT-RATE PIC S9(04)V99 - interest rate (e.g., 21.99 = 21.99%)
    int_rate: Mapped[Decimal] = mapped_column(NUMERIC(6, 2), nullable=False)


class TransactionTypeORM(Base):
    """
    Transaction Type code table.
    Source: DB2 CARDDEMO.TRANSACTION_TYPE / copybook CVTRA03Y (60 bytes)
    Also used by COTRTLIC and COTRTUPC programs.

    TRAN-TYPE       PIC X(02)  -> tran_type_cd  CHAR(2) PK
    TRAN-TYPE-DESC  PIC X(50)  -> tran_type_desc VARCHAR(50)
    """
    __tablename__ = "transaction_types"

    # TRAN-TYPE PIC X(02)
    tran_type_cd: Mapped[str] = mapped_column(CHAR(2), primary_key=True)

    # TRAN-TYPE-DESC PIC X(50)
    tran_type_desc: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)

    def __repr__(self) -> str:
        return f"<TransactionType cd={self.tran_type_cd} desc={self.tran_type_desc}>"


class TransactionCategoryORM(Base):
    """
    Transaction Category code table.
    Source: DB2 CARDDEMO.TRANSACTION_CATEGORY / copybook CVTRA04Y (60 bytes)

    TRAN-TYPE-CD    PIC X(02)  -> tran_type_cd   CHAR(2) PK
    TRAN-CAT-CD     PIC 9(04)  -> tran_cat_cd    INTEGER PK
    TRAN-CAT-TYPE-DESC PIC X(50) -> tran_cat_desc VARCHAR(50)
    """
    __tablename__ = "transaction_categories"

    tran_type_cd: Mapped[str] = mapped_column(CHAR(2), primary_key=True)
    tran_cat_cd: Mapped[int] = mapped_column(Integer, primary_key=True)
    tran_cat_desc: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
