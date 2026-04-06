"""
SQLAlchemy ORM model for the `card_account_xref` table.

COBOL origin: CARDXREF VSAM KSDS with AIX (CVACT03Y copybook).
Record: CARD-XREF-RECORD 50 bytes.
  XREF-CARD-NUM   X(16) → card_number CHAR(16) PRIMARY KEY
  XREF-CUST-ID    9(9)  → customer_id INTEGER
  XREF-ACCT-ID    9(11) → account_id BIGINT

Primary access patterns:
  COTRN02C: READ CCXREF by card_number → account_id lookup
  COACTVWC: READ CARDAIX (AIX on XREF-ACCT-ID) → find all cards for account
    → replicated by idx_cardxref_account index

The VSAM AIX (alternate index) on XREF-ACCT-ID is replaced by
a regular PostgreSQL index idx_cardxref_account on account_id.
"""

from datetime import datetime

from sqlalchemy import BigInteger, CHAR, DateTime
from sqlalchemy import Integer as SAInteger
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CardAccountXref(Base):
    """
    PostgreSQL `card_account_xref` table.

    Replaces CARDXREF VSAM KSDS + AIX on XREF-ACCT-ID.
    COACTVWC reads this via account_id to find all cards for the account
    (replaces EXEC CICS STARTBR DATASET(CARDAIX) RIDFLD(account_id)).
    """

    __tablename__ = "card_account_xref"

    # XREF-CARD-NUM X(16) — VSAM KSDS primary key
    card_number: Mapped[str] = mapped_column(
        CHAR(16),
        ForeignKey("credit_cards.card_number", name="fk_cardxref_card"),
        primary_key=True,
        comment="COBOL: XREF-CARD-NUM X(16) — VSAM KSDS primary key",
    )

    # XREF-CUST-ID 9(9)
    customer_id: Mapped[int] = mapped_column(
        SAInteger,
        ForeignKey("customers.customer_id", name="fk_cardxref_customer"),
        nullable=False,
        comment="COBOL: XREF-CUST-ID 9(9)",
    )

    # XREF-ACCT-ID 9(11) — was AIX key in VSAM; now indexed column
    account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("accounts.account_id", name="fk_cardxref_account"),
        nullable=False,
        comment="COBOL: XREF-ACCT-ID 9(11) — was VSAM AIX; now PostgreSQL index",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Row creation timestamp",
    )

    def __repr__(self) -> str:
        return (
            f"CardAccountXref(card_number={self.card_number!r}, "
            f"account_id={self.account_id!r})"
        )
