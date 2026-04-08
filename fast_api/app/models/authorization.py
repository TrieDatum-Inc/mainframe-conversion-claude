"""
SQLAlchemy ORM models for the Authorization module.

Source programs:
  app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl — Authorization decision engine
  app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl — Authorization summary view
  app-authorization-ims-db2-mq/cbl/COPAUS1C.cbl — Authorization detail view
  app-authorization-ims-db2-mq/cbl/COPAUS2C.cbl — Fraud marking (DB2 INSERT/UPDATE)

IMS segments replaced by PostgreSQL tables:
  PAUTSUM0 (CIPAUSMY.cpy) — PENDING-AUTH-SUMMARY root segment → auth_summaries
  PAUTDTL1 (CIPAUDTY.cpy) — PENDING-AUTH-DETAILS child segment → auth_details

DB2 table (COPAUS2C EXEC SQL INSERT/UPDATE):
  CARDDEMO.AUTHFRDS → auth_fraud_records

VSAM files accessed:
  CCXREF  (CVACT03Y.cpy) → card_xref (existing model in card.py)
  ACCTDAT (CVACT01Y.cpy) → accounts  (existing model in account.py)
  CUSTDAT (CVCUS01Y.cpy) → customers (existing model in customer.py)

MQ request/reply pattern replaced by synchronous REST POST.
"""
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Decline reason codes (from WS-DECLINE-REASON-TABLE in COPAUS1C)
# ---------------------------------------------------------------------------
#   '0000' = APPROVED
#   '3100' = INVALID CARD  (CARD-NFOUND-XREF / NFOUND-ACCT-IN-MSTR)
#   '4100' = INSUFFICIENT FUND
#   '4200' = CARD NOT ACTIVE
#   '4300' = ACCOUNT CLOSED
#   '4400' = EXCEEDED DAILY LIMIT
#   '5100' = CARD FRAUD
#   '5200' = MERCHANT FRAUD
#   '5300' = LOST CARD
#   '9000' = UNKNOWN


class AuthSummary(Base):
    """
    Pending Authorization Summary record.

    Replaces IMS PAUTSUM0 root segment (CIPAUSMY.cpy).
    One row per account — tracks aggregate credit/balance counters
    that were maintained by the IMS hierarchical DB.

    Fields mirror the IMS segment layout exactly, using PostgreSQL
    Numeric for COMP-3 packed-decimal fields.
    """

    __tablename__ = "auth_summaries"

    # PA-ACCT-ID PIC S9(11) COMP-3 — primary key (IMS root key)
    acct_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("accounts.acct_id", ondelete="CASCADE"),
        primary_key=True,
        comment="PA-ACCT-ID PIC S9(11) COMP-3 — IMS PAUTSUM0 root key",
    )

    # PA-CUST-ID PIC 9(09)
    cust_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="PA-CUST-ID PIC 9(09)"
    )

    # PA-AUTH-STATUS PIC X(01)
    auth_status: Mapped[str | None] = mapped_column(
        String(1), nullable=True, comment="PA-AUTH-STATUS PIC X(01)"
    )

    # PA-CREDIT-LIMIT PIC S9(09)V99 COMP-3
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(11, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="PA-CREDIT-LIMIT PIC S9(09)V99 COMP-3",
    )

    # PA-CASH-LIMIT PIC S9(09)V99 COMP-3
    cash_limit: Mapped[Decimal] = mapped_column(
        Numeric(11, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="PA-CASH-LIMIT PIC S9(09)V99 COMP-3",
    )

    # PA-CREDIT-BALANCE PIC S9(09)V99 COMP-3
    credit_balance: Mapped[Decimal] = mapped_column(
        Numeric(11, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="PA-CREDIT-BALANCE PIC S9(09)V99 COMP-3",
    )

    # PA-CASH-BALANCE PIC S9(09)V99 COMP-3
    cash_balance: Mapped[Decimal] = mapped_column(
        Numeric(11, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="PA-CASH-BALANCE PIC S9(09)V99 COMP-3",
    )

    # PA-APPROVED-AUTH-CNT PIC S9(04) COMP
    approved_auth_cnt: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        comment="PA-APPROVED-AUTH-CNT PIC S9(04) COMP",
    )

    # PA-DECLINED-AUTH-CNT PIC S9(04) COMP
    declined_auth_cnt: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        comment="PA-DECLINED-AUTH-CNT PIC S9(04) COMP",
    )

    # PA-APPROVED-AUTH-AMT PIC S9(09)V99 COMP-3
    approved_auth_amt: Mapped[Decimal] = mapped_column(
        Numeric(11, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="PA-APPROVED-AUTH-AMT PIC S9(09)V99 COMP-3",
    )

    # PA-DECLINED-AUTH-AMT PIC S9(09)V99 COMP-3
    declined_auth_amt: Mapped[Decimal] = mapped_column(
        Numeric(11, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="PA-DECLINED-AUTH-AMT PIC S9(09)V99 COMP-3",
    )

    # Relationships
    account: Mapped["Account"] = relationship(  # noqa: F821
        "Account", back_populates="auth_summary", lazy="select"
    )
    auth_details: Mapped[list["AuthDetail"]] = relationship(
        "AuthDetail",
        back_populates="summary",
        lazy="select",
        cascade="all, delete-orphan",
    )


class AuthDetail(Base):
    """
    Pending Authorization Detail record.

    Replaces IMS PAUTDTL1 child segment (CIPAUDTY.cpy).
    One row per individual authorization request, child of AuthSummary.

    The composite primary key (acct_id, auth_date_9c, auth_time_9c) mirrors
    PA-AUTHORIZATION-KEY from the IMS segment, which used inverted date/time
    values so that most-recent sorts first (COBOL: 99999 - YYDDD, 999999999 - HHMMSS).

    Match status 88-levels:
      PA-MATCH-PENDING         = 'P'
      PA-MATCH-AUTH-DECLINED   = 'D'
      PA-MATCH-PENDING-EXPIRED = 'E'
      PA-MATCHED-WITH-TRAN     = 'M'

    Fraud status 88-levels:
      PA-FRAUD-CONFIRMED = 'F'
      PA-FRAUD-REMOVED   = 'R'
    """

    __tablename__ = "auth_details"
    __table_args__ = (
        Index("ix_auth_details_card_num", "card_num"),
        Index("ix_auth_details_acct_id_match_status", "acct_id", "match_status"),
        CheckConstraint(
            "match_status IN ('P','D','E','M')",
            name="ck_auth_details_match_status",
        ),
        CheckConstraint(
            "auth_fraud IN ('F','R',' ') OR auth_fraud IS NULL",
            name="ck_auth_details_fraud",
        ),
    )

    # Surrogate PK — IMS used PA-AUTHORIZATION-KEY (auth_date_9c + auth_time_9c)
    # as the physical IMS key; we use a surrogate for PostgreSQL and carry
    # the original COBOL key values as data columns.
    # Using Integer (not BigInteger) for SQLite test compatibility (autoincrement PK).
    auth_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Surrogate PK (IMS used PA-AUTHORIZATION-KEY composite key)",
    )

    # FK to auth_summaries
    acct_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("auth_summaries.acct_id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to auth_summaries (IMS parent segment)",
    )

    # PA-AUTHORIZATION-KEY.PA-AUTH-DATE-9C PIC S9(05) COMP-3
    # Inverted YYDDD: 99999 - YYDDD  (most-recent-first sort order)
    auth_date_9c: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="PA-AUTH-DATE-9C PIC S9(05) COMP-3 (inverted YYDDD)",
    )

    # PA-AUTHORIZATION-KEY.PA-AUTH-TIME-9C PIC S9(09) COMP-3
    # Inverted HHMMSSMMM: 999999999 - time (most-recent-first sort order)
    auth_time_9c: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="PA-AUTH-TIME-9C PIC S9(09) COMP-3 (inverted time)",
    )

    # PA-AUTH-ORIG-DATE PIC X(06)  — YYMMDD format
    auth_orig_date: Mapped[str | None] = mapped_column(
        String(6), nullable=True, comment="PA-AUTH-ORIG-DATE PIC X(06) YYMMDD"
    )

    # PA-AUTH-ORIG-TIME PIC X(06)  — HHMMSS format
    auth_orig_time: Mapped[str | None] = mapped_column(
        String(6), nullable=True, comment="PA-AUTH-ORIG-TIME PIC X(06) HHMMSS"
    )

    # PA-CARD-NUM PIC X(16)
    card_num: Mapped[str | None] = mapped_column(
        String(16), nullable=True, comment="PA-CARD-NUM PIC X(16)"
    )

    # PA-AUTH-TYPE PIC X(04)
    auth_type: Mapped[str | None] = mapped_column(
        String(4), nullable=True, comment="PA-AUTH-TYPE PIC X(04)"
    )

    # PA-CARD-EXPIRY-DATE PIC X(04)  — MMYY
    card_expiry_date: Mapped[str | None] = mapped_column(
        String(4), nullable=True, comment="PA-CARD-EXPIRY-DATE PIC X(04) MMYY"
    )

    # PA-MESSAGE-TYPE PIC X(06)
    message_type: Mapped[str | None] = mapped_column(
        String(6), nullable=True, comment="PA-MESSAGE-TYPE PIC X(06)"
    )

    # PA-MESSAGE-SOURCE PIC X(06)
    message_source: Mapped[str | None] = mapped_column(
        String(6), nullable=True, comment="PA-MESSAGE-SOURCE PIC X(06)"
    )

    # PA-AUTH-ID-CODE PIC X(06)  — set from PA-RQ-AUTH-TIME in COPAUA0C
    auth_id_code: Mapped[str | None] = mapped_column(
        String(6), nullable=True, comment="PA-AUTH-ID-CODE PIC X(06)"
    )

    # PA-AUTH-RESP-CODE PIC X(02)  — '00'=approved, '05'=declined
    auth_resp_code: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        comment="PA-AUTH-RESP-CODE PIC X(02) 88-PA-AUTH-APPROVED='00'",
    )

    # PA-AUTH-RESP-REASON PIC X(04)
    #   '0000'=APPROVED, '3100'=INVALID CARD, '4100'=INSUFFICIENT FUND,
    #   '4200'=CARD NOT ACTIVE, '4300'=ACCOUNT CLOSED, '5100'=CARD FRAUD,
    #   '5200'=MERCHANT FRAUD, '9000'=UNKNOWN
    auth_resp_reason: Mapped[str | None] = mapped_column(
        String(4), nullable=True, comment="PA-AUTH-RESP-REASON PIC X(04)"
    )

    # PA-PROCESSING-CODE PIC 9(06)
    processing_code: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="PA-PROCESSING-CODE PIC 9(06)"
    )

    # PA-TRANSACTION-AMT PIC S9(10)V99 COMP-3
    transaction_amt: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="PA-TRANSACTION-AMT PIC S9(10)V99 COMP-3",
    )

    # PA-APPROVED-AMT PIC S9(10)V99 COMP-3
    approved_amt: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="PA-APPROVED-AMT PIC S9(10)V99 COMP-3",
    )

    # PA-MERCHANT-CATAGORY-CODE PIC X(04)  [sic — COBOL spelling preserved]
    merchant_category_code: Mapped[str | None] = mapped_column(
        String(4), nullable=True, comment="PA-MERCHANT-CATAGORY-CODE PIC X(04)"
    )

    # PA-ACQR-COUNTRY-CODE PIC X(03)
    acqr_country_code: Mapped[str | None] = mapped_column(
        String(3), nullable=True, comment="PA-ACQR-COUNTRY-CODE PIC X(03)"
    )

    # PA-POS-ENTRY-MODE PIC 9(02)
    pos_entry_mode: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="PA-POS-ENTRY-MODE PIC 9(02)"
    )

    # PA-MERCHANT-ID PIC X(15)
    merchant_id: Mapped[str | None] = mapped_column(
        String(15), nullable=True, comment="PA-MERCHANT-ID PIC X(15)"
    )

    # PA-MERCHANT-NAME PIC X(22)
    merchant_name: Mapped[str | None] = mapped_column(
        String(22), nullable=True, comment="PA-MERCHANT-NAME PIC X(22)"
    )

    # PA-MERCHANT-CITY PIC X(13)
    merchant_city: Mapped[str | None] = mapped_column(
        String(13), nullable=True, comment="PA-MERCHANT-CITY PIC X(13)"
    )

    # PA-MERCHANT-STATE PIC X(02)
    merchant_state: Mapped[str | None] = mapped_column(
        String(2), nullable=True, comment="PA-MERCHANT-STATE PIC X(02)"
    )

    # PA-MERCHANT-ZIP PIC X(09)
    merchant_zip: Mapped[str | None] = mapped_column(
        String(9), nullable=True, comment="PA-MERCHANT-ZIP PIC X(09)"
    )

    # PA-TRANSACTION-ID PIC X(15)
    transaction_id: Mapped[str | None] = mapped_column(
        String(15), nullable=True, comment="PA-TRANSACTION-ID PIC X(15)"
    )

    # PA-MATCH-STATUS PIC X(01)
    #   88 PA-MATCH-PENDING          VALUE 'P'
    #   88 PA-MATCH-AUTH-DECLINED    VALUE 'D'
    #   88 PA-MATCH-PENDING-EXPIRED  VALUE 'E'
    #   88 PA-MATCHED-WITH-TRAN      VALUE 'M'
    match_status: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
        default="P",
        comment="PA-MATCH-STATUS: P=Pending D=Declined E=Expired M=Matched",
    )

    # PA-AUTH-FRAUD PIC X(01)
    #   88 PA-FRAUD-CONFIRMED VALUE 'F'
    #   88 PA-FRAUD-REMOVED   VALUE 'R'
    auth_fraud: Mapped[str | None] = mapped_column(
        String(1), nullable=True, comment="PA-AUTH-FRAUD: F=Confirmed R=Removed"
    )

    # PA-FRAUD-RPT-DATE PIC X(08)  — MM/DD/YY format (COPAUS2C FORMATTIME MMDDYY)
    fraud_rpt_date: Mapped[str | None] = mapped_column(
        String(8), nullable=True, comment="PA-FRAUD-RPT-DATE PIC X(08) MM/DD/YY"
    )

    # Relationships
    summary: Mapped["AuthSummary"] = relationship(
        "AuthSummary", back_populates="auth_details", lazy="select"
    )


class AuthFraudRecord(Base):
    """
    Authorization Fraud Record.

    Maps to DB2 table CARDDEMO.AUTHFRDS (COPAUS2C EXEC SQL INSERT/UPDATE).
    Created/updated when a user marks an authorization as fraudulent (PF5 key
    in COPAUS1C → EXEC CICS LINK COPAUS2C).

    SQLCODE = -803 on INSERT triggers an UPDATE (upsert logic in COPAUS2C
    FRAUD-UPDATE paragraph) — modeled here as an explicit upsert.

    Primary key mirrors DB2: (card_num, auth_ts).
    """

    __tablename__ = "auth_fraud_records"
    __table_args__ = (
        Index("ix_auth_fraud_acct_id", "acct_id"),
        Index("ix_auth_fraud_card_num", "card_num"),
    )

    # CARD_NUM CHAR(16) — part of composite PK
    card_num: Mapped[str] = mapped_column(
        String(16),
        primary_key=True,
        comment="CARD_NUM CHAR(16) — PK part 1",
    )

    # AUTH_TS TIMESTAMP — derived from PA-AUTH-ORIG-DATE + inverted PA-AUTH-TIME-9C
    # Stored as string to match DB2 TIMESTAMP_FORMAT pattern in COPAUS2C
    auth_ts: Mapped[str] = mapped_column(
        String(26),
        primary_key=True,
        comment="AUTH_TS TIMESTAMP 'YY-MM-DD HH24.MI.SSNNNNNN' — PK part 2",
    )

    # AUTH_TYPE CHAR(4) — PA-AUTH-TYPE PIC X(04)
    auth_type: Mapped[str | None] = mapped_column(
        String(4), nullable=True, comment="AUTH_TYPE"
    )

    # CARD_EXPIRY_DATE CHAR(4)
    card_expiry_date: Mapped[str | None] = mapped_column(
        String(4), nullable=True, comment="CARD_EXPIRY_DATE"
    )

    # MESSAGE_TYPE CHAR(6)
    message_type: Mapped[str | None] = mapped_column(
        String(6), nullable=True, comment="MESSAGE_TYPE"
    )

    # MESSAGE_SOURCE CHAR(6)
    message_source: Mapped[str | None] = mapped_column(
        String(6), nullable=True, comment="MESSAGE_SOURCE"
    )

    # AUTH_ID_CODE CHAR(6)
    auth_id_code: Mapped[str | None] = mapped_column(
        String(6), nullable=True, comment="AUTH_ID_CODE"
    )

    # AUTH_RESP_CODE CHAR(2)
    auth_resp_code: Mapped[str | None] = mapped_column(
        String(2), nullable=True, comment="AUTH_RESP_CODE"
    )

    # AUTH_RESP_REASON CHAR(4)
    auth_resp_reason: Mapped[str | None] = mapped_column(
        String(4), nullable=True, comment="AUTH_RESP_REASON"
    )

    # PROCESSING_CODE INTEGER
    processing_code: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="PROCESSING_CODE"
    )

    # TRANSACTION_AMT DECIMAL(12,2)
    transaction_amt: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="TRANSACTION_AMT DECIMAL(12,2)",
    )

    # APPROVED_AMT DECIMAL(12,2)
    approved_amt: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="APPROVED_AMT DECIMAL(12,2)",
    )

    # MERCHANT_CATAGORY_CODE CHAR(4) [sic]
    merchant_category_code: Mapped[str | None] = mapped_column(
        String(4), nullable=True, comment="MERCHANT_CATAGORY_CODE CHAR(4)"
    )

    # ACQR_COUNTRY_CODE CHAR(3)
    acqr_country_code: Mapped[str | None] = mapped_column(
        String(3), nullable=True, comment="ACQR_COUNTRY_CODE CHAR(3)"
    )

    # POS_ENTRY_MODE SMALLINT
    pos_entry_mode: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="POS_ENTRY_MODE SMALLINT"
    )

    # MERCHANT_ID CHAR(15)
    merchant_id: Mapped[str | None] = mapped_column(
        String(15), nullable=True, comment="MERCHANT_ID CHAR(15)"
    )

    # MERCHANT_NAME VARCHAR(22)
    merchant_name: Mapped[str | None] = mapped_column(
        String(22), nullable=True, comment="MERCHANT_NAME VARCHAR(22)"
    )

    # MERCHANT_CITY CHAR(13)
    merchant_city: Mapped[str | None] = mapped_column(
        String(13), nullable=True, comment="MERCHANT_CITY CHAR(13)"
    )

    # MERCHANT_STATE CHAR(2)
    merchant_state: Mapped[str | None] = mapped_column(
        String(2), nullable=True, comment="MERCHANT_STATE CHAR(2)"
    )

    # MERCHANT_ZIP CHAR(9)
    merchant_zip: Mapped[str | None] = mapped_column(
        String(9), nullable=True, comment="MERCHANT_ZIP CHAR(9)"
    )

    # TRANSACTION_ID CHAR(15)
    transaction_id: Mapped[str | None] = mapped_column(
        String(15), nullable=True, comment="TRANSACTION_ID CHAR(15)"
    )

    # MATCH_STATUS CHAR(1)
    match_status: Mapped[str | None] = mapped_column(
        String(1), nullable=True, comment="MATCH_STATUS CHAR(1)"
    )

    # AUTH_FRAUD CHAR(1) — 'F'=Confirmed / 'R'=Removed
    auth_fraud: Mapped[str | None] = mapped_column(
        String(1), nullable=True, comment="AUTH_FRAUD CHAR(1) F=Confirmed R=Removed"
    )

    # FRAUD_RPT_DATE DATE — CURRENT DATE in COPAUS2C
    fraud_rpt_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="FRAUD_RPT_DATE DATE (CURRENT DATE)"
    )

    # ACCT_ID BIGINT
    acct_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="ACCT_ID BIGINT"
    )

    # CUST_ID INTEGER
    cust_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="CUST_ID INTEGER"
    )
