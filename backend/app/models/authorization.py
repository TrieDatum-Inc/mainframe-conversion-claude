"""
SQLAlchemy ORM models for the Authorization module.

Sources:
  - AuthorizationSummary: IMS PAUTSUM0 root segment (CIPAUSMY copybook)
    Replaces: HISAM database DBPAUTP0, accessed via EXEC DLI GU in COPAUS0C
  - AuthorizationDetail: IMS PAUTDTL1 child segment (CIPAUDTY copybook, 200 bytes)
    Replaces: HISAM child segment, accessed via EXEC DLI GNP in COPAUS0C/COPAUS1C
    IMS key note: inverted timestamp (999999999 - AUTH-TIME-9C) replaced by processed_at DESC
  - AuthFraudLog: DB2 CARDDEMO.AUTHFRDS (26 columns)
    Replaces: EXEC SQL INSERT/UPDATE in COPAUS2C
    Unique index on (auth_id, fraud_flag='F') replaces SQLCODE -803 handling
"""
from datetime import date, time
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP

from app.database import Base


class AuthorizationSummary(Base):
    """
    Authorization summary record — one per account.
    Maps IMS PAUTSUM0 root segment (CIPAUSMY copybook).
    COPAUS0C: EXEC DLI GU PAUTSUM0 WHERE(ACCNTID = WS-CARD-RID-ACCT-ID)
    Fields: PA-CREDIT-LIMIT, PA-CASH-LIMIT, PA-CREDIT-BALANCE, PA-CASH-BALANCE,
            PA-APPROVED-AUTH-CNT, PA-DECLINED-AUTH-CNT,
            PA-APPROVED-AUTH-AMT, PA-DECLINED-AUTH-AMT
    """

    __tablename__ = "authorization_summary"

    # PA-ACCT-ID PIC 9(11) — IMS segment key ACCNTID
    account_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # PA-CREDIT-LIMIT S9(10)V99 COMP-3
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # PA-CASH-LIMIT S9(10)V99 COMP-3
    cash_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # PA-CREDIT-BALANCE S9(10)V99 COMP-3
    credit_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # PA-CASH-BALANCE S9(10)V99 COMP-3
    cash_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # PA-APPROVED-AUTH-CNT S9(4) COMP
    approved_auth_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # PA-DECLINED-AUTH-CNT S9(4) COMP
    declined_auth_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # PA-APPROVED-AUTH-AMT S9(10)V99 COMP-3
    approved_auth_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    # PA-DECLINED-AUTH-AMT S9(10)V99 COMP-3
    declined_auth_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    created_at: Mapped[any] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[any] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship to detail records (IMS parent-child: PAUTSUM0 → PAUTDTL1)
    details: Mapped[list["AuthorizationDetail"]] = relationship(
        "AuthorizationDetail",
        back_populates="summary",
        order_by="AuthorizationDetail.processed_at.desc()",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<AuthorizationSummary account_id={self.account_id}>"


class AuthorizationDetail(Base):
    """
    Authorization detail record — one per authorization transaction.
    Maps IMS PAUTDTL1 child segment (CIPAUDTY copybook, 200 bytes).
    COPAUS0C: EXEC DLI GNP PAUTDTL1 (up to 5 per page)
    COPAUS1C: EXEC DLI GNP PAUTDTL1 WHERE(PAUT9CTS = PA-AUTHORIZATION-KEY)
    COPAUS1C: EXEC DLI REPL PAUTDTL1 (fraud flag update — PA-AUTH-FRAUD field)
    IMS key (PA-AUTH-DATE-9C + PA-AUTH-TIME-9C) replaced by processed_at DESC index.
    fraud_status values: N=none (initial), F=fraud confirmed, R=fraud removed
    Match status: P=Pending, D=Declined, E=Expired, M=Matched (88-level conditions)
    """

    __tablename__ = "authorization_detail"

    __table_args__ = (
        CheckConstraint("match_status IN ('P', 'D', 'E', 'M')", name="chk_authdet_match"),
        CheckConstraint("fraud_status IN ('N', 'F', 'R')", name="chk_authdet_fraud"),
        # idx_authdet_processed_at replaces IMS inverted timestamp key for DESC ordering
        Index("idx_authdet_processed_at", "processed_at"),
        Index("idx_authdet_account_id", "account_id"),
        Index("idx_authdet_card_number", "card_number"),
        Index("idx_authdet_transaction_id", "transaction_id"),
        Index("idx_authdet_fraud_status", "fraud_status"),
    )

    # Surrogate key (IMS used compound inverted-timestamp key PA-AUTH-DATE-9C+PA-AUTH-TIME-9C)
    auth_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # PA-ACCT-ID PIC 9(11) — FK to authorization_summary
    account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("authorization_summary.account_id", name="fk_authdet_summary"),
        nullable=False,
    )

    # PA-TRANSACTION-ID PIC X(16)
    transaction_id: Mapped[str] = mapped_column(String(16), nullable=False)

    # PA-CARD-NUM PIC X(16)
    card_number: Mapped[str] = mapped_column(CHAR(16), nullable=False)

    # PA-AUTH-ORIG-DATE YYMMDD → DATE
    auth_date: Mapped[date] = mapped_column(Date, nullable=False)

    # PA-AUTH-ORIG-TIME HHMMSS → TIME
    auth_time: Mapped[time] = mapped_column(Time, nullable=False)

    # PA-AUTH-RESP-CODE PIC X(2) — '00'=approved, other=declined
    # COPAUS1C: DFHGREEN if '00', DFHRED otherwise
    auth_response_code: Mapped[str] = mapped_column(CHAR(2), nullable=False)

    # PA-AUTH-ID-CODE / PA-PROCESSING-CODE PIC X(6)
    auth_code: Mapped[str | None] = mapped_column(String(6), nullable=True)

    # PA-TRANSACTION-AMT S9(7)V99 COMP-3
    transaction_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # PA-POS-ENTRY-MODE PIC X(4)
    pos_entry_mode: Mapped[str | None] = mapped_column(String(4), nullable=True)

    # PA-MESSAGE-SOURCE / auth_source PIC X(10)
    auth_source: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # PA-MERCHANT-CATAGORY-CODE PIC X(4) (note: COBOL typo "CATAGORY" preserved in comments)
    mcc_code: Mapped[str | None] = mapped_column(String(4), nullable=True)

    # PA-CARD-EXPIRY-DATE PIC X(5) — format MM/YY
    card_expiry_date: Mapped[str | None] = mapped_column(String(5), nullable=True)

    # PA-AUTH-TYPE PIC X(14)
    auth_type: Mapped[str | None] = mapped_column(String(14), nullable=True)

    # PA-MATCH-STATUS: 88-level PA-MATCH-PENDING='P', PA-MATCH-DIRECT='D',
    #                  PA-MATCH-EXACT='E', PA-MATCH-MANUAL='M'
    match_status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="P")

    # PA-AUTH-FRAUD: 88-level PA-FRAUD-CONFIRMED='F', PA-FRAUD-REMOVED='R'
    # N = initial state (no flag set), F = fraud confirmed, R = fraud removed
    # COPAUS1C MARK-AUTH-FRAUD: F→R (remove), else→F (confirm)
    # Spec: N→F, F→R, R→F (3-state cycle)
    fraud_status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="N")

    # PA-MERCHANT-NAME PIC X(25)
    merchant_name: Mapped[str | None] = mapped_column(String(25), nullable=True)

    # PA-MERCHANT-ID PIC X(15)
    merchant_id: Mapped[str | None] = mapped_column(String(15), nullable=True)

    # PA-MERCHANT-CITY PIC X(25)
    merchant_city: Mapped[str | None] = mapped_column(String(25), nullable=True)

    # PA-MERCHANT-STATE PIC X(2)
    merchant_state: Mapped[str | None] = mapped_column(CHAR(2), nullable=True)

    # PA-MERCHANT-ZIP PIC X(10)
    merchant_zip: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Replaces IMS inverted timestamp key — DESC index provides newest-first ordering
    processed_at: Mapped[any] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[any] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    summary: Mapped["AuthorizationSummary"] = relationship(
        "AuthorizationSummary", back_populates="details"
    )
    fraud_logs: Mapped[list["AuthFraudLog"]] = relationship(
        "AuthFraudLog", back_populates="detail", lazy="select"
    )

    @property
    def is_approved(self) -> bool:
        """Replaces COPAUS1C: IF PA-AUTH-RESP-CODE = '00' (DFHGREEN)."""
        return self.auth_response_code == "00"

    def __repr__(self) -> str:
        return f"<AuthorizationDetail auth_id={self.auth_id} account_id={self.account_id}>"


class AuthFraudLog(Base):
    """
    Immutable audit log of fraud flag toggle actions.
    Replaces DB2 CARDDEMO.AUTHFRDS table (COPAUS2C).
    INSERT-only: one row per fraud flag toggle action.
    COPAUS2C: EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS (26 columns)
    COPAUS2C: On SQLCODE -803 → EXEC SQL UPDATE (toggle AUTH_FRAUD + FRAUD_RPT_DATE only)
    Unique index on (auth_id, fraud_flag='F') replaces the -803 duplicate key constraint.
    """

    __tablename__ = "auth_fraud_log"

    __table_args__ = (
        # Replaces SQLCODE -803 duplicate key behavior from COPAUS2C
        Index(
            "idx_fraudlog_unique_auth",
            "auth_id",
            "fraud_flag",
            unique=True,
            postgresql_where=Text("fraud_flag = 'F'"),
        ),
        Index("idx_fraudlog_transaction", "transaction_id"),
        Index("idx_fraudlog_account", "account_id"),
    )

    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # FK to authorization_detail.auth_id
    auth_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("authorization_detail.auth_id", name="fk_fraudlog_auth"),
        nullable=False,
    )

    # PA-TRANSACTION-ID PIC X(16)
    transaction_id: Mapped[str] = mapped_column(String(16), nullable=False)

    # PA-CARD-NUM PIC X(16) — DCLAUTHFRDS CARD_NUM
    card_number: Mapped[str] = mapped_column(CHAR(16), nullable=False)

    # WS-ACCT-ID PIC 9(11) — DCLAUTHFRDS ACCT_ID
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # WS-FRD-ACTION PIC X(1) — 'F'=fraud confirmed, 'R'=fraud removed
    # DCLAUTHFRDS AUTH_FRAUD CHAR(1)
    fraud_flag: Mapped[str] = mapped_column(CHAR(1), nullable=False)

    # DCLAUTHFRDS FRAUD_RPT_DATE DATE (DB2 CURRENT DATE)
    fraud_report_date: Mapped[any] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # PA-AUTH-RESP-CODE — DCLAUTHFRDS AUTH_RESP_CODE
    auth_response_code: Mapped[str | None] = mapped_column(CHAR(2), nullable=True)

    # PA-TRANSACTION-AMT — DCLAUTHFRDS TRANSACTION_AMT (or APPROVED_AMT)
    auth_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # DCLAUTHFRDS MERCHANT_NAME VARCHAR(22) — note: BMS field is 25 chars, DB2 is 22
    merchant_name: Mapped[str | None] = mapped_column(String(22), nullable=True)

    # DCLAUTHFRDS MERCHANT_ID VARCHAR(9)
    merchant_id: Mapped[str | None] = mapped_column(String(9), nullable=True)

    # When this log entry was written (equivalent to DB2 CURRENT TIMESTAMP)
    logged_at: Mapped[any] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    detail: Mapped["AuthorizationDetail"] = relationship(
        "AuthorizationDetail", back_populates="fraud_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<AuthFraudLog log_id={self.log_id} auth_id={self.auth_id} flag={self.fraud_flag}>"
        )
