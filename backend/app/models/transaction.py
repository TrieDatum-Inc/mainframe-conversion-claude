"""
SQLAlchemy ORM model for the `transactions` table.

COBOL origin: TRANSACT VSAM KSDS (CVTRA05Y / COTRN02Y copybook).
  TRAN-ID           X(16)       → transaction_id VARCHAR(16) PRIMARY KEY
  TRAN-TYPE-CD      X(02)       → transaction_type_code VARCHAR(2) FK → transaction_types
  TRAN-CAT-CD       9(04)       → transaction_category_code VARCHAR(4)
  TRAN-SOURCE       X(10)       → transaction_source VARCHAR(10)
  TRAN-DESC         X(24/60)   → description VARCHAR(60)
  TRAN-AMT          S9(09)V99   → amount NUMERIC(10,2)
  TRAN-CARD-NUM     X(16)       → card_number CHAR(16) FK → credit_cards
  TRAN-ORIG-TS      X(26)       → original_date DATE
  TRAN-PROC-TS      X(26)       → processed_date DATE
  TRAN-MERCHANT-ID  9(09)       → merchant_id VARCHAR(9)
  TRAN-MERCHANT-NAME X(50)      → merchant_name VARCHAR(30)
  TRAN-MERCHANT-CITY X(50)      → merchant_city VARCHAR(25)
  TRAN-MERCHANT-ZIP  X(10)      → merchant_zip VARCHAR(10)

Key design decisions:
  - transaction_id_seq PostgreSQL SEQUENCE replaces the COTRN02C / COBIL00C
    STARTBR(HIGH-VALUES) + READPREV + ADD-1 pattern which had a race condition
    under concurrent writes.
  - FK on transaction_type_code replicates COTRTLIC SQLCODE -532 (FK violation
    on delete of type code that has referencing transactions).
"""

from datetime import date, datetime

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Transaction(Base):
    """
    Persistent transaction record — maps to the `transactions` PostgreSQL table.

    COBOL equivalent: TRAN-RECORD (COTRN02Y copybook) stored in TRANSACT VSAM KSDS.

    Transaction IDs are generated via PostgreSQL sequence `transaction_id_seq`.
    This is a documented fix for the COTRN02C STARTBR/READPREV/ADD-1 race condition.

    The FK on transaction_type_code enforces referential integrity equivalent to
    the COTRTLIC SQLCODE -532 protection against deleting referenced type codes.
    """

    __tablename__ = "transactions"

    __table_args__ = (
        CheckConstraint("amount != 0", name="chk_transactions_nonzero_amount"),
    )

    transaction_id: Mapped[str] = mapped_column(
        String(16),
        primary_key=True,
        comment=(
            "TRAN-ID X(16) — was generated via STARTBR(HIGH-VALUES)+READPREV+ADD-1 in "
            "COTRN02C/COBIL00C; now assigned from transaction_id_seq (race condition fix)."
        ),
    )
    card_number: Mapped[str] = mapped_column(
        CHAR(16),
        ForeignKey("credit_cards.card_number", name="fk_transactions_card"),
        nullable=False,
        comment="TRAN-CARD-NUM X(16) — FK to credit_cards; looked up from card_account_xref.",
    )
    transaction_type_code: Mapped[str] = mapped_column(
        String(2),
        ForeignKey("transaction_types.type_code", name="fk_transactions_type"),
        nullable=False,
        comment=(
            "TRAN-TYPE-CD X(02) — FK to transaction_types. "
            "'02' is hardcoded for bill payments (COBIL00C TRAN-TYPE-CD='02')."
        ),
    )
    transaction_category_code: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
        comment="TRAN-CAT-CD 9(04) — 4-digit numeric category; '0002' for bill payments.",
    )
    transaction_source: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="TRAN-SOURCE X(10) — e.g. 'POS TERM' hardcoded in COBIL00C.",
    )
    description: Mapped[str | None] = mapped_column(
        String(60),
        nullable=True,
        comment=(
            "TRAN-DESC X(24) in COTRN02Y; extended to 60 chars in target schema. "
            "Bill payments hardcode 'BILL PAYMENT - ONLINE' (COBIL00C)."
        ),
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment=(
            "TRAN-AMT S9(09)V99 — signed packed decimal. "
            "Must not be zero (validated at service layer, replaces COTRN02C VALIDATE-INPUT-FIELDS)."
        ),
    )
    original_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment=(
            "TRAN-ORIG-TS X(26) — original 26-byte COBOL timestamp; "
            "date portion extracted and stored as DATE."
        ),
    )
    processed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment=(
            "TRAN-PROC-TS X(26) — process timestamp date portion. "
            "Must be >= original_date (validated at service layer)."
        ),
    )
    merchant_id: Mapped[str | None] = mapped_column(
        String(9),
        nullable=True,
        comment=(
            "TRAN-MERCHANT-ID 9(09) — 9-digit numeric stored as string. "
            "'999999999' hardcoded for bill payments (COBIL00C)."
        ),
    )
    merchant_name: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="TRAN-MERCHANT-NAME X(50) — truncated to 30 chars in target schema.",
    )
    merchant_city: Mapped[str | None] = mapped_column(
        String(25),
        nullable=True,
        comment="TRAN-MERCHANT-CITY X(50) — truncated to 25 chars; 'N/A' for bill payments.",
    )
    merchant_zip: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="TRAN-MERCHANT-ZIP X(10) — 'N/A' for bill payments (COBIL00C).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Row creation timestamp (not in original VSAM record).",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Row last-modified timestamp; managed by trigger.",
    )

    def __repr__(self) -> str:
        return (
            f"Transaction(transaction_id={self.transaction_id!r}, "
            f"card_number={self.card_number!r}, amount={self.amount!r})"
        )
