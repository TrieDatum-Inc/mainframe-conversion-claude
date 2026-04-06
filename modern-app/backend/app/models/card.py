"""ORM models for the Card and Card Cross-Reference module.

Migrated from VSAM KSDS files:
  CARDDATA (CARDDAT) -> Card      (CVACT02Y, 150 bytes, key CARD-NUM X(16))
  CARDXREF (CCXREF)  -> CardXref  (CVACT03Y, 50 bytes, key XREF-CARD-NUM X(16))
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Card(Base):
    """Maps to CARDDATA VSAM KSDS — CARD-RECORD (CVACT02Y).

    Key: CARD-NUM PIC X(16) -> card_number VARCHAR(16)
    """

    __tablename__ = "cards"
    __table_args__ = (
        CheckConstraint(
            "active_status IN ('Y', 'N')",
            name="ck_cards_active_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # CARD-NUM PIC X(16) — primary VSAM key
    card_number: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, index=True
    )

    # CARD-ACCT-ID PIC 9(11) — FK to accounts
    account_id: Mapped[str] = mapped_column(
        String(11),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # CARD-CVV-CD PIC 9(3) — stored as string
    cvv_code: Mapped[str] = mapped_column(String(3), nullable=False, default="")

    # CARD-EMBOSSED-NAME PIC X(50)
    embossed_name: Mapped[str] = mapped_column(String(50), nullable=False, default="")

    # CARD-EXPIRAION-DATE — stored as DATE (month/year from BMS fields EXPMON/EXPYEAR)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # CARD-ACTIVE-STATUS PIC X(1) — 'Y' active, 'N' inactive
    active_status: Mapped[str] = mapped_column(
        String(1), nullable=False, default="Y"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Many-to-one back to account
    account: Mapped["Account"] = relationship(  # noqa: F821
        "Account", back_populates="cards"
    )

    # One-to-one with xref (typically)
    card_xref: Mapped["CardXref | None"] = relationship(  # noqa: F821
        "CardXref", back_populates="card", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<Card card_number={self.card_number!r} "
            f"account_id={self.account_id!r} status={self.active_status!r}>"
        )


class CardXref(Base):
    """Maps to CARDXREF VSAM KSDS — CARD-XREF-RECORD (CVACT03Y).

    Key: XREF-CARD-NUM PIC X(16)
    AIX: CXACAIX on XREF-ACCT-ID 9(11) — allows lookup by account.

    This cross-reference links card numbers to customers and accounts,
    enabling the account view to pull customer demographics.
    """

    __tablename__ = "card_xref"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # XREF-CARD-NUM PIC X(16) — primary VSAM key, FK to cards
    card_number: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("cards.card_number", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # XREF-CUST-ID PIC 9(9) — FK to customers
    customer_id: Mapped[str] = mapped_column(
        String(9),
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # XREF-ACCT-ID PIC 9(11) — FK to accounts (the AIX field)
    account_id: Mapped[str] = mapped_column(
        String(11),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    card: Mapped["Card"] = relationship("Card", back_populates="card_xref")
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        "Customer", back_populates="card_xrefs", lazy="selectin"
    )
    account: Mapped["Account"] = relationship(  # noqa: F821
        "Account", back_populates="card_xrefs"
    )

    def __repr__(self) -> str:
        return (
            f"<CardXref card_number={self.card_number!r} "
            f"customer_id={self.customer_id!r} account_id={self.account_id!r}>"
        )
