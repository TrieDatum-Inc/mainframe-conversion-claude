"""
SQLAlchemy ORM models for Authorization Subsystem entities.

Sources:
  IMS CIPAUSMY segment -> auth_summary table
  IMS CIPAUDTY segment -> auth_detail table
  DB2 CARDDEMO.AUTHFRDS -> auth_fraud table

These replace the IMS DL/I hierarchy (PAUT PCB) used by COPAUS0C, COPAUS1C,
COPAUS2C, COPAUA0C, and batch programs CBPAUP0C, PAUDBLOD, PAUDBUNL.

IMS hierarchy was:
  Root (PAUT): Authorization Summary (PA-ACCT-ID as key)
    Child: Authorization Detail (PA-AUTH-DATE-9C + PA-AUTH-TIME-9C as key)

PostgreSQL equivalent:
  auth_summary (acct_id PK)
    -> auth_detail (auth_date + auth_time + acct_id PK, FK->auth_summary)

CIPAUSMY segment (Authorization Summary) field mapping:
  PA-ACCT-ID           9(11)    -> acct_id           BIGINT PK
  PA-CUST-ID           9(09)    -> cust_id            INTEGER
  PA-AUTH-STATUS       X(01)    -> auth_status        CHAR(1)
  PA-CREDIT-LIMIT      S9(09)V99 -> credit_limit      NUMERIC(11,2)
  PA-CASH-LIMIT        S9(09)V99 -> cash_limit        NUMERIC(11,2)
  PA-CURR-BAL          S9(09)V99 -> curr_bal          NUMERIC(11,2)
  PA-CASH-BAL          S9(09)V99 -> cash_bal          NUMERIC(11,2)
  PA-APPROVED-COUNT    9(09)    -> approved_count     INTEGER
  PA-APPROVED-AMT      S9(09)V99 -> approved_amt      NUMERIC(11,2)
  PA-DECLINED-COUNT    9(09)    -> declined_count     INTEGER
  PA-DECLINED-AMT      S9(09)V99 -> declined_amt      NUMERIC(11,2)

CIPAUDTY segment (Authorization Detail) field mapping:
  PA-AUTH-DATE-9C      9(08)    -> auth_date          DATE (YYYYMMDD)
  PA-AUTH-TIME-9C      9(06)    -> auth_time          TIME (HHMMSS)
  PA-CARD-NUM          X(16)    -> card_num           VARCHAR(16)
  PA-TRAN-ID           X(16)    -> tran_id            VARCHAR(16)
  PA-AUTH-ID-CODE      X(10)    -> auth_id_code       VARCHAR(10)
  PA-RESPONSE-CODE     X(02)    -> response_code      CHAR(2)
  PA-RESPONSE-REASON   X(25)    -> response_reason    VARCHAR(25)
  PA-APPROVED-AMT      S9(09)V99 -> approved_amt      NUMERIC(11,2)
  PA-AUTH-TYPE         X(01)    -> auth_type          CHAR(1)
  PA-MATCH-STATUS      X(01)    -> match_status       CHAR(1)
  PA-FRAUD-FLAG        X(01)    -> fraud_flag         CHAR(1)

AUTHFRDS (DB2 CARDDEMO.AUTHFRDS) - written by COPAUS2C:
  (inferred from COPAUS2C INSERT/UPDATE operations)
"""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    DATE,
    NUMERIC,
    TIME,
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


class AuthSummaryORM(Base):
    """
    IMS CIPAUSMY segment (Authorization Summary).
    One record per account showing aggregate authorization state.
    """
    __tablename__ = "auth_summary"
    __table_args__ = (
        Index("ix_auth_summary_cust_id", "cust_id"),
    )

    acct_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cust_id: Mapped[int] = mapped_column(Integer, nullable=False)
    auth_status: Mapped[str | None] = mapped_column(CHAR(1), nullable=True)
    credit_limit: Mapped[Decimal] = mapped_column(NUMERIC(11, 2), nullable=False, default=Decimal("0.00"))
    cash_limit: Mapped[Decimal] = mapped_column(NUMERIC(11, 2), nullable=False, default=Decimal("0.00"))
    curr_bal: Mapped[Decimal] = mapped_column(NUMERIC(11, 2), nullable=False, default=Decimal("0.00"))
    cash_bal: Mapped[Decimal] = mapped_column(NUMERIC(11, 2), nullable=False, default=Decimal("0.00"))
    approved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    approved_amt: Mapped[Decimal] = mapped_column(NUMERIC(11, 2), nullable=False, default=Decimal("0.00"))
    declined_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    declined_amt: Mapped[Decimal] = mapped_column(NUMERIC(11, 2), nullable=False, default=Decimal("0.00"))


class AuthDetailORM(Base):
    """
    IMS CIPAUDTY segment (Authorization Detail).
    Child records under AuthSummary; keyed by date+time+acct_id.
    """
    __tablename__ = "auth_detail"
    __table_args__ = (
        Index("ix_auth_detail_card_num", "card_num"),
        Index("ix_auth_detail_acct_id", "acct_id"),
        CheckConstraint(
            "fraud_flag IN ('Y', 'N')",
            name="ck_auth_detail_fraud_flag",
        ),
    )

    # Composite key: auth_date + auth_time + acct_id (from IMS segment key)
    auth_date: Mapped[date] = mapped_column(DATE, primary_key=True)
    auth_time: Mapped[time] = mapped_column(TIME, primary_key=True)
    acct_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("auth_summary.acct_id", ondelete="CASCADE"),
        primary_key=True,
    )

    card_num: Mapped[str | None] = mapped_column(VARCHAR(16), nullable=True)
    tran_id: Mapped[str | None] = mapped_column(VARCHAR(16), nullable=True)
    auth_id_code: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)

    # PA-RESPONSE-CODE X(02) - '00'=approved, other=declined
    response_code: Mapped[str | None] = mapped_column(CHAR(2), nullable=True)
    response_reason: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)
    approved_amt: Mapped[Decimal] = mapped_column(NUMERIC(11, 2), nullable=False, default=Decimal("0.00"))

    # PA-AUTH-TYPE X(01) - authorization type code
    auth_type: Mapped[str | None] = mapped_column(CHAR(1), nullable=True)

    # PA-MATCH-STATUS X(01) - whether the auth was matched to a transaction
    match_status: Mapped[str | None] = mapped_column(CHAR(1), nullable=True)

    # PA-FRAUD-FLAG X(01) - 'Y'=fraud flagged, 'N'=clean (set by COPAUS2C)
    fraud_flag: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="N")


class AuthFraudORM(Base):
    """
    DB2 CARDDEMO.AUTHFRDS table.
    Written by COPAUS2C when operator flags an authorization as fraudulent.
    Supports both INSERT (new fraud record) and UPDATE (update existing).
    """
    __tablename__ = "auth_fraud"
    __table_args__ = (
        Index("ix_auth_fraud_card_num", "card_num"),
        Index("ix_auth_fraud_acct_id", "acct_id"),
    )

    # Surrogate PK (AUTHFRDS table structure inferred from COPAUS2C operations)
    fraud_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    card_num: Mapped[str] = mapped_column(VARCHAR(16), nullable=False)
    acct_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    auth_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    auth_time: Mapped[time | None] = mapped_column(TIME, nullable=True)
    fraud_reason: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    flagged_by: Mapped[str | None] = mapped_column(VARCHAR(8), nullable=True)
    flagged_ts: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    fraud_status: Mapped[str | None] = mapped_column(CHAR(1), nullable=True, default="P")
