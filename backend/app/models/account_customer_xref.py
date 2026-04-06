"""
AccountCustomerXref model — links accounts to customers.

COBOL origin: COACTVWC used CARDAIX (Alt Index on XREF-CUST-ID) to find the
customer linked to an account. This cross-reference table provides that join.

In the original system:
  1. READ ACCTDAT by ACCT-ID → get account
  2. STARTBR DATASET(CARDAIX) RIDFLD(ACCT-ID) → browse CARDXREF to find CUST-ID
  3. READ CUSTDAT by CUST-ID → get customer

Here replaced by a direct FK join via account_customer_xref.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, PrimaryKeyConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AccountCustomerXref(Base):
    """
    PostgreSQL `account_customer_xref` table.

    Links accounts to customers. Replaces the indirect lookup via CARDXREF
    that COACTVWC used to find the customer for a given account.
    Composite PK (account_id, customer_id).
    """

    __tablename__ = "account_customer_xref"
    __table_args__ = (
        PrimaryKeyConstraint("account_id", "customer_id", name="pk_account_customer_xref"),
    )

    account_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="FK → accounts.account_id",
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="FK → customers.customer_id",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<AccountCustomerXref acct={self.account_id} cust={self.customer_id}>"
