"""
SQLAlchemy ORM model for the `account_customer_xref` join table.

COBOL origin: Derived from ACCTDAT/CUSTDAT relationship (CVACT04Y or equivalent).
Purpose: Links accounts to customers — allows COACTVWC to fetch the customer
record for a given account_id without knowing the customer_id in advance.

COACTVWC flow: READ ACCTDAT → READ CARDAIX → READ CUSTDAT
Modern equivalent: JOIN account_customer_xref ON account_id → SELECT customers
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime
from sqlalchemy import Integer as SAInteger
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AccountCustomerXref(Base):
    """
    PostgreSQL `account_customer_xref` join table.

    Links accounts to their primary customer records.
    COACTUPC reads both account and customer data for a single account_id
    — this join table is the bridge between the two VSAM datasets.
    """

    __tablename__ = "account_customer_xref"

    # Composite primary key: (account_id, customer_id)
    account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("accounts.account_id", name="fk_acctcust_account"),
        primary_key=True,
        comment="COBOL: derived from ACCT-ID in ACCTDAT",
    )

    customer_id: Mapped[int] = mapped_column(
        SAInteger,
        ForeignKey("customers.customer_id", name="fk_acctcust_customer"),
        primary_key=True,
        comment="COBOL: derived from CUST-ID in CUSTDAT",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Row creation timestamp",
    )

    def __repr__(self) -> str:
        return (
            f"AccountCustomerXref(account_id={self.account_id!r}, "
            f"customer_id={self.customer_id!r})"
        )
