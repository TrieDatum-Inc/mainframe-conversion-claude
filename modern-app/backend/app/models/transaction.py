"""SQLAlchemy ORM models for the transaction module.

Maps to VSAM KSDS files:
  TRANSACT  → Transaction  (CVTRA05Y, TRAN-RECORD 350 bytes)
  TCATBALF  → TransactionCategoryBalance  (CVTRA01Y, TRAN-CAT-BAL-RECORD 50 bytes)
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Transaction(Base):
    """Represents a single credit-card transaction.

    COBOL source: CVTRA05Y — TRAN-RECORD (350 bytes, key TRAN-ID X(16)).
    """

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # TRAN-ID X(16) — zero-padded numeric string, unique, auto-generated max+1
    transaction_id: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)

    # TRAN-TYPE-CD CHAR(2): '01' = Purchase, '02' = Payment
    type_code: Mapped[str] = mapped_column(String(2), nullable=False)

    # TRAN-CAT-CD 9(4): stored as 4-char string to preserve leading zeros
    category_code: Mapped[str] = mapped_column(String(4), nullable=False)

    # TRAN-SOURCE X(10)
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="")

    # TRAN-DESC X(100)
    description: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    # TRAN-AMT S9(9)V99 — signed decimal, range -99999999.99 to +99999999.99
    amount: Mapped[Decimal] = mapped_column(Numeric(11, 2), nullable=False)

    # TRAN-MERCHANT-ID 9(9): all-numeric merchant identifier
    merchant_id: Mapped[str] = mapped_column(String(9), nullable=False, default="")

    # TRAN-MERCHANT-NAME X(50)
    merchant_name: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # TRAN-MERCHANT-CITY X(50)
    merchant_city: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # TRAN-MERCHANT-ZIP X(10)
    merchant_zip: Mapped[str] = mapped_column(String(10), nullable=False, default="")

    # TRAN-CARD-NUM X(16)
    card_number: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    # TRAN-ORIG-TS (26-char COBOL timestamp → Python datetime)
    original_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # TRAN-PROC-TS
    processing_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "amount >= -99999999.99 AND amount <= 99999999.99",
            name="chk_transaction_amount_range",
        ),
        Index("idx_transactions_orig_ts", "original_timestamp"),
        Index("idx_transactions_type_category", "type_code", "category_code"),
    )

    def __repr__(self) -> str:
        return f"<Transaction id={self.transaction_id} amount={self.amount}>"


class TransactionCategoryBalance(Base):
    """Running balance per account / type / category combination.

    COBOL source: CVTRA01Y — TRAN-CAT-BAL-RECORD (50 bytes).
    Composite VSAM key: ACCT-ID(11) + TYPE-CD(2) + CAT-CD(4).
    """

    __tablename__ = "transaction_category_balances"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ACCT-ID 9(11)
    account_id: Mapped[str] = mapped_column(String(11), nullable=False)

    # TRAN-TYPE-CD CHAR(2)
    type_code: Mapped[str] = mapped_column(String(2), nullable=False)

    # TRAN-CAT-CD VARCHAR(4)
    category_code: Mapped[str] = mapped_column(String(4), nullable=False)

    # TRAN-CAT-BAL S9(9)V99
    balance: Mapped[Decimal] = mapped_column(Numeric(11, 2), nullable=False, default=Decimal("0.00"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("account_id", "type_code", "category_code", name="uq_tcat_bal"),
        Index("idx_tcatbal_account", "account_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<TransactionCategoryBalance account={self.account_id} "
            f"type={self.type_code} cat={self.category_code} bal={self.balance}>"
        )
