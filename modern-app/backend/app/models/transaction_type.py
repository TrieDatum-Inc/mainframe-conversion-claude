"""ORM models for the Transaction Type module.

Migrated from DB2 tables:
  CARDDEMO.TRANSACTION_TYPE          -> TransactionType
  CARDDEMO.TRANSACTION_TYPE_CATEGORY -> TransactionTypeCategory

COBOL field mapping:
  TR_TYPE          CHAR(2)      -> type_code  CHAR(2)    (PK / unique)
  TR_DESCRIPTION   VARCHAR(50)  -> description VARCHAR(50)
  TR_CAT           VARCHAR(4)   -> category_code VARCHAR(4)
  TR_CAT_DESCRIPTION VARCHAR(50) -> description VARCHAR(50)
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionType(Base):
    """Maps to CARDDEMO.TRANSACTION_TYPE DB2 table."""

    __tablename__ = "transaction_types"
    __table_args__ = (
        UniqueConstraint("type_code", name="uq_transaction_types_type_code"),
        CheckConstraint(
            "length(trim(type_code)) > 0",
            name="ck_transaction_types_type_code_length",
        ),
        CheckConstraint(
            "length(trim(description)) > 0",
            name="ck_transaction_types_description_nonempty",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # TR_TYPE CHAR(2) — 2-char alphanumeric, non-blank (COBOL validation)
    type_code: Mapped[str] = mapped_column(
        String(2), nullable=False, unique=True, index=True
    )
    # TR_DESCRIPTION VARCHAR(50) — non-blank description
    description: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to categories (one-to-many)
    categories: Mapped[list["TransactionTypeCategory"]] = relationship(
        "TransactionTypeCategory",
        back_populates="transaction_type",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<TransactionType type_code={self.type_code!r} description={self.description!r}>"


class TransactionTypeCategory(Base):
    """Maps to CARDDEMO.TRANSACTION_TYPE_CATEGORY DB2 table."""

    __tablename__ = "transaction_type_categories"
    __table_args__ = (
        UniqueConstraint(
            "type_code", "category_code", name="uq_txn_type_category"
        ),
        CheckConstraint(
            "length(trim(category_code)) > 0",
            name="ck_txn_cat_category_code_nonempty",
        ),
        CheckConstraint(
            "length(trim(description)) > 0",
            name="ck_txn_cat_description_nonempty",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # FK to TransactionType.type_code (CASCADE DELETE)
    type_code: Mapped[str] = mapped_column(
        String(2),
        ForeignKey("transaction_types.type_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # TR_CAT VARCHAR(4) — category code, non-blank
    category_code: Mapped[str] = mapped_column(String(4), nullable=False)
    # TR_CAT_DESCRIPTION VARCHAR(50) — human-readable label
    description: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Many-to-one back-reference
    transaction_type: Mapped["TransactionType"] = relationship(
        "TransactionType", back_populates="categories"
    )

    def __repr__(self) -> str:
        return (
            f"<TransactionTypeCategory type_code={self.type_code!r}"
            f" category_code={self.category_code!r}>"
        )
