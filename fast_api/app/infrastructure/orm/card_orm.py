"""
SQLAlchemy ORM models for Credit Card and Card Cross-Reference entities.

Sources:
  CARDDAT   VSAM KSDS / copybook CVACT02Y (150 bytes) - Card record
  CXACAIX   VSAM AIX  / copybook CVACT03Y (50 bytes)  - Card-to-Account XRef

Card field mapping:
  CARD-NUM              PIC X(16)     -> card_num         VARCHAR(16) PRIMARY KEY
  CARD-ACCT-ID          PIC 9(11)     -> acct_id          BIGINT FK->accounts
  CARD-CVV-CD           PIC 9(03)     -> cvv_cd           SMALLINT
  CARD-EMBOSSED-NAME    PIC X(50)     -> embossed_name    VARCHAR(50)
  CARD-EXPIRAION-DATE   PIC X(10)     -> expiration_date  DATE (typo preserved)
  CARD-ACTIVE-STATUS    PIC X(01)     -> active_status    CHAR(1)
  FILLER                PIC X(59)     -> (omitted)

Cross-reference field mapping (CXACAIX - alternate index keyed by XREF-ACCT-ID):
  XREF-CARD-NUM         PIC X(16)     -> card_num         VARCHAR(16) PK
  XREF-CUST-ID          PIC 9(09)     -> cust_id          INTEGER FK->customers
  XREF-ACCT-ID          PIC 9(11)     -> acct_id          BIGINT FK->accounts
  FILLER                PIC X(14)     -> (omitted)

Note: CXACAIX is the alternate index path used by COACTUPC, COACTVWC, COBIL00C,
      COTRN02C for looking up card/customer by account ID.
"""

from datetime import date

from sqlalchemy import (
    CHAR,
    DATE,
    VARCHAR,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class CardORM(Base):
    __tablename__ = "cards"
    __table_args__ = (
        CheckConstraint(
            "active_status IN ('Y', 'N')",
            name="ck_card_active_status",
        ),
        CheckConstraint(
            "cvv_cd >= 0 AND cvv_cd <= 999",
            name="ck_card_cvv_range",
        ),
        Index("ix_cards_acct_id", "acct_id"),
        Index("ix_cards_active_status", "active_status"),
    )

    # CARD-NUM PIC X(16) - 16-character card number (primary key)
    card_num: Mapped[str] = mapped_column(VARCHAR(16), primary_key=True)

    # CARD-ACCT-ID PIC 9(11) - FK to accounts.acct_id
    acct_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("accounts.acct_id", ondelete="RESTRICT"),
        nullable=False,
    )

    # CARD-CVV-CD PIC 9(03) - 3-digit CVV code (stored; not exposed in APIs)
    cvv_cd: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # CARD-EMBOSSED-NAME PIC X(50)
    embossed_name: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)

    # CARD-EXPIRAION-DATE PIC X(10) - note: original COBOL has typo 'EXPIRAION'
    expiration_date: Mapped[date | None] = mapped_column(DATE, nullable=True)

    # CARD-ACTIVE-STATUS PIC X(01) - 'Y'=active, 'N'=inactive
    active_status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="Y")

    def __repr__(self) -> str:
        return f"<Card num={self.card_num} acct={self.acct_id} status={self.active_status}>"


class CardXrefORM(Base):
    """
    Card-to-Account cross-reference (maps to VSAM CXACAIX alternate index).

    This table serves as the PostgreSQL equivalent of the VSAM AIX path
    CXACAIX keyed by account ID. It allows efficient lookup of cards by
    account ID (replaces EXEC CICS READ DATASET('CXACAIX') RIDFLD(acct-id)).
    """
    __tablename__ = "card_xref"
    __table_args__ = (
        Index("ix_card_xref_acct_id", "acct_id"),  # replaces the VSAM AIX
        Index("ix_card_xref_cust_id", "cust_id"),
    )

    # XREF-CARD-NUM PIC X(16) - primary key
    card_num: Mapped[str] = mapped_column(
        VARCHAR(16),
        ForeignKey("cards.card_num", ondelete="CASCADE"),
        primary_key=True,
    )

    # XREF-CUST-ID PIC 9(09) - FK to customers.cust_id
    cust_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.cust_id", ondelete="RESTRICT"),
        nullable=False,
    )

    # XREF-ACCT-ID PIC 9(11) - the alternate key (indexed for AIX behavior)
    acct_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("accounts.acct_id", ondelete="RESTRICT"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CardXref card={self.card_num} cust={self.cust_id} acct={self.acct_id}>"
