"""
SQLAlchemy ORM models for `cards` and `card_xref` tables.

Source copybooks:
  app/cpy/CVACT02Y.cpy — CARD-RECORD (150 bytes)   → `cards` table
  app/cpy/CVACT03Y.cpy — CARD-XREF-RECORD (50 bytes) → `card_xref` table

Source VSAM files:
  CARDDAT (CARDAIX alternate index on CARD-ACCT-ID) → cards + ix_cards_acct_id
  CCXREF  (CXACAIX alternate index on XREF-ACCT-ID) → card_xref + ix_card_xref_acct_id

Browse patterns (STARTBR/READNEXT) mapped to:
  CARDAIX browse → WHERE acct_id = :id ORDER BY card_num LIMIT n OFFSET/keyset
  CXACAIX browse → WHERE acct_id = :id ORDER BY card_num
"""
from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Card(Base):
    """
    Credit card record.

    Maps to COBOL CARD-RECORD (CVACT02Y.cpy).
    CARD-NUM is PIC X(16) — stored as CHAR(16) string, never as a number.
    """

    __tablename__ = "cards"
    __table_args__ = (
        # CARD-ACTIVE-STATUS PIC X(01)
        CheckConstraint("active_status IN ('Y', 'N')", name="ck_cards_active_status"),
        # CARDAIX equivalent: browse cards by account ID
        Index("ix_cards_acct_id", "acct_id"),
    )

    # CARD-NUM PIC X(16) — primary key, stored as string
    card_num: Mapped[str] = mapped_column(String(16), primary_key=True, comment="CARD-NUM PIC X(16)")

    # CARD-ACCT-ID PIC 9(11) — foreign key to accounts
    acct_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.acct_id", ondelete="RESTRICT"), nullable=False,
        comment="CARD-ACCT-ID PIC 9(11)"
    )

    # CARD-CVV-CD PIC 9(03) — 3-digit CVV code
    cvv_cd: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="CARD-CVV-CD PIC 9(03)")

    # CARD-EMBOSSED-NAME PIC X(50)
    embossed_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="CARD-EMBOSSED-NAME PIC X(50)"
    )

    # CARD-EXPIRAION-DATE PIC X(10) — typo in original copybook retained
    expiration_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="CARD-EXPIRAION-DATE PIC X(10) [typo in original copybook]"
    )

    # CARD-ACTIVE-STATUS PIC X(01) 88-level: 'Y'=active, 'N'=inactive
    active_status: Mapped[str] = mapped_column(
        String(1), nullable=False, default="Y", comment="CARD-ACTIVE-STATUS PIC X(01)"
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="cards")
    card_xref: Mapped["CardXref | None"] = relationship(
        "CardXref", back_populates="card", uselist=False, lazy="select"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="card", foreign_keys="Transaction.card_num", lazy="select"
    )


class CardXref(Base):
    """
    Card cross-reference record — links card_num to customer and account.

    Maps to COBOL CARD-XREF-RECORD (CVACT03Y.cpy).
    CXACAIX (alternate index on XREF-ACCT-ID) is replicated as ix_card_xref_acct_id.

    Used by COBIL00C to resolve account → card(s) for payment transactions.
    Used by CBTRN01C to resolve card → account during batch posting.
    """

    __tablename__ = "card_xref"
    __table_args__ = (
        # CXACAIX equivalent: browse xref by account ID
        Index("ix_card_xref_acct_id", "acct_id"),
        Index("ix_card_xref_cust_id", "cust_id"),
    )

    # XREF-CARD-NUM PIC X(16) — primary key
    card_num: Mapped[str] = mapped_column(
        String(16), ForeignKey("cards.card_num", ondelete="CASCADE"),
        primary_key=True, comment="XREF-CARD-NUM PIC X(16)"
    )

    # XREF-CUST-ID PIC 9(09)
    cust_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.cust_id", ondelete="RESTRICT"),
        nullable=False, comment="XREF-CUST-ID PIC 9(09)"
    )

    # XREF-ACCT-ID PIC 9(11)
    acct_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("accounts.acct_id", ondelete="RESTRICT"),
        nullable=False, comment="XREF-ACCT-ID PIC 9(11)"
    )

    # Relationships
    card: Mapped["Card"] = relationship("Card", back_populates="card_xref")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="card_xrefs")
    account: Mapped["Account"] = relationship("Account", back_populates="card_xrefs")
