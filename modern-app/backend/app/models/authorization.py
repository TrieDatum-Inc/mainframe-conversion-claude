"""
SQLAlchemy ORM models for authorization processing.

Maps IMS DBPAUTP0 hierarchical database:
- AuthorizationSummary  → PAUTSUM0 root segment (account-level)
- AuthorizationDetail   → PAUTDTL1 child segment (per-authorization)
"""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Time,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class AuthorizationSummary(Base):
    """
    Account-level authorization summary.

    COBOL source: IMS PAUTSUM0 root segment (100 bytes).
    Key field was PA-ACCT-ID (packed decimal 6 bytes).
    """

    __tablename__ = "authorization_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(11), nullable=False, unique=True, index=True)
    customer_id = Column(String(9), nullable=False, index=True)
    auth_status = Column(
        String(1),
        nullable=False,
        default="A",
        comment="A=Active, C=Closed, I=Inactive",
    )
    credit_limit = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    cash_limit = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    credit_balance = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    cash_balance = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    approved_count = Column(Integer, nullable=False, default=0)
    declined_count = Column(Integer, nullable=False, default=0)
    approved_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    declined_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    details = relationship(
        "AuthorizationDetail",
        back_populates="summary",
        cascade="all, delete-orphan",
        order_by="desc(AuthorizationDetail.auth_date), desc(AuthorizationDetail.auth_time)",
    )

    __table_args__ = (
        CheckConstraint(auth_status.in_(["A", "C", "I"]), name="ck_auth_status"),
    )


class AuthorizationDetail(Base):
    """
    Individual authorization record.

    COBOL source: IMS PAUTDTL1 child segment (200 bytes).
    Key was PA-AUTH-DATE-9C + PA-AUTH-TIME-9C (9-complement COMP-3 timestamp).
    """

    __tablename__ = "authorization_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    summary_id = Column(
        Integer,
        ForeignKey("authorization_summaries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    card_number = Column(String(16), nullable=False, index=True)
    auth_date = Column(Date, nullable=False, index=True)
    auth_time = Column(Time, nullable=False)
    auth_type = Column(String(4), nullable=False, default="")
    card_expiry = Column(String(5), nullable=False, default="")
    message_type = Column(String(6), nullable=False, default="")

    # Response fields — maps to decline reason lookup table in COPAUS1C
    auth_response_code = Column(
        String(2),
        nullable=False,
        default="00",
        comment=(
            "00=Approved, 31=Invalid Card, 41=Insuff Fund, "
            "42=Card Not Active, 43=Account Closed, "
            "44=Exceed Daily Limit, 51=Card Fraud, "
            "52=Merchant Fraud, 53=Lost Card, 90=Unknown"
        ),
    )
    auth_response_reason = Column(String(20), nullable=False, default="")
    auth_code = Column(String(6), nullable=False, default="")

    # Amount fields
    transaction_amount = Column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    approved_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    # Terminal / source fields
    pos_entry_mode = Column(String(4), nullable=False, default="")
    auth_source = Column(String(10), nullable=False, default="")

    # Classification fields
    mcc_code = Column(String(4), nullable=False, default="")
    merchant_name = Column(String(25), nullable=False, default="")
    merchant_id = Column(String(15), nullable=False, default="")
    merchant_city = Column(String(25), nullable=False, default="")
    merchant_state = Column(String(2), nullable=False, default="")
    merchant_zip = Column(String(10), nullable=False, default="")

    # Tracking fields
    transaction_id = Column(String(15), nullable=False, default="", index=True)
    match_status = Column(
        String(1),
        nullable=False,
        default="P",
        comment="P=Pending, D=Declined, E=Expired, M=Matched",
    )
    fraud_status = Column(
        String(1),
        nullable=True,
        comment="F=Fraud confirmed, R=Fraud removed, NULL=no action",
    )
    fraud_report_date = Column(Date, nullable=True)
    processing_code = Column(String(6), nullable=False, default="")

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    summary = relationship("AuthorizationSummary", back_populates="details")
    fraud_records = relationship(
        "FraudRecord", back_populates="auth_detail", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            match_status.in_(["P", "D", "E", "M"]), name="ck_match_status"
        ),
        CheckConstraint(
            "fraud_status IS NULL OR fraud_status IN ('F', 'R')",
            name="ck_fraud_status",
        ),
        Index("idx_auth_details_summary_date", "summary_id", "auth_date"),
    )
