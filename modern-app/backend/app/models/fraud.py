"""
SQLAlchemy ORM model for fraud records.

Maps to DB2 table CARDDEMO.AUTHFRDS.
Managed by COPAUS2C (fraud mark/remove) invoked via LINK from COPAUS1C.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class FraudRecord(Base):
    """
    Fraud flag record for an authorization.

    COBOL source: DB2 CARDDEMO.AUTHFRDS table.
    Composite unique key: (card_number, auth_timestamp).

    Operations:
    - INSERT: when fraud first reported ('F' flag)
    - UPDATE: when fraud status changes to removed ('R' flag)
    """

    __tablename__ = "fraud_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_number = Column(String(16), nullable=False, index=True)
    auth_timestamp = Column(DateTime, nullable=False)
    fraud_flag = Column(
        String(1),
        nullable=False,
        comment="F=Fraud reported, R=Fraud removed",
    )
    fraud_report_date = Column(Date, nullable=False)
    match_status = Column(
        String(1),
        nullable=False,
        default="P",
        comment="P=Pending, D=Declined, E=Expired, M=Matched",
    )
    account_id = Column(String(11), nullable=False, index=True)
    customer_id = Column(String(9), nullable=False)
    auth_detail_id = Column(
        Integer,
        ForeignKey("authorization_details.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    auth_detail = relationship("AuthorizationDetail", back_populates="fraud_records")

    __table_args__ = (
        UniqueConstraint(
            "card_number", "auth_timestamp", name="uq_fraud_card_timestamp"
        ),
        CheckConstraint(fraud_flag.in_(["F", "R"]), name="ck_fraud_flag"),
        CheckConstraint(
            match_status.in_(["P", "D", "E", "M"]), name="ck_fraud_match_status"
        ),
    )
