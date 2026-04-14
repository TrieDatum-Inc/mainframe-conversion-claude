"""
AccountCustomerXref ORM model — maps to the `account_customer_xref` table.

COBOL origin: Derived from the relationship between ACCTDAT and CUSTDAT via
the CXACAIX alternate index (cross-reference file, CVACT03Y copybook).
  - XREF-ACCT-ID    9(11) → account_id BIGINT (FK → accounts)
  - XREF-CUST-ID    9(9)  → customer_id INTEGER (FK → customers)

In the COBOL system, COACTVWC and COACTUPC used CXACAIX to navigate from a
known account_id to the associated customer_id:
  EXEC CICS READ DATASET('CXACAIX') RIDFLD(WS-XREF-RID) KEYLENGTH(11) GTEQ RESP RESP2
  → WS-XREF-RID contained CARD-RID-ACCT-ID (11 digits) as the lookup key

The modern equivalent is a simple FK join:
  SELECT c.* FROM customers c
  JOIN account_customer_xref x ON c.customer_id = x.customer_id
  WHERE x.account_id = :account_id
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AccountCustomerXref(Base):
    __tablename__ = "account_customer_xref"

    account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="XREF-ACCT-ID 9(11) — FK to accounts",
    )
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="XREF-CUST-ID 9(9) — FK to customers",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("idx_acctcust_customer", "customer_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AccountCustomerXref "
            f"account_id={self.account_id!r} "
            f"customer_id={self.customer_id!r}>"
        )
