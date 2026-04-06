"""
SQLAlchemy ORM model for the `credit_cards` table.

COBOL origin: CARDDAT VSAM KSDS (CVACT02Y copybook).
Record length: 150 bytes.

Field mapping:
  CARD-NUM          X(16)  → card_number CHAR(16) PRIMARY KEY
  CARD-ACCT-ID      9(11)  → account_id BIGINT FK → accounts
  CARD-CUST-ID      9(9)   → customer_id INTEGER FK → customers
  CARD-EMBOSSED-NAME X(50) → card_embossed_name VARCHAR(50)
  CARD-ACTIVE-STATUS X(1)  → active_status CHAR(1) CHECK IN ('Y','N')
  CARD-EXPIRY-DATE  X(10)  → expiration_date DATE (YYYY-MM-DD)
  EXPDAY (hidden BMS field on COCRDUP map) → expiration_day SMALLINT

COCRDUPC validates:
  - card_embossed_name: alpha-only (INSPECT CONVERTING equivalent)
  - expiration_month: 1-12
  - expiration_year: 1950-2099
  - Optimistic lock via CCUP-OLD-DETAILS snapshot → updated_at comparison
  - account_id: PROT field (cannot be changed in update)
"""

from datetime import date, datetime

from sqlalchemy import CHAR, BigInteger, CheckConstraint, Date, DateTime, ForeignKey
from sqlalchemy import Integer as SAInteger
from sqlalchemy import SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CreditCard(Base):
    """
    PostgreSQL `credit_cards` table.

    Replaces CARDDAT VSAM KSDS.
    COCRDLIC browses this with optional account_id/card_number filters (STARTBR/READNEXT).
    COCRDSLC reads by card_number for detail display.
    COCRDUPC reads then updates card fields; account_id is PROT (read-only).

    PCI-DSS note: card_number stored as-is for demo purposes.
    Production systems should tokenize or mask and store only last 4 digits.
    """

    __tablename__ = "credit_cards"

    __table_args__ = (
        CheckConstraint("active_status IN ('Y', 'N')", name="chk_cards_active"),
        CheckConstraint(
            "EXTRACT(MONTH FROM expiration_date) BETWEEN 1 AND 12",
            name="chk_cards_exp_month",
        ),
        CheckConstraint(
            "EXTRACT(YEAR FROM expiration_date) BETWEEN 1950 AND 2099",
            name="chk_cards_exp_year",
        ),
    )

    # CARD-NUM X(16) — VSAM KSDS primary key; fixed 16-char card number
    card_number: Mapped[str] = mapped_column(
        CHAR(16),
        primary_key=True,
        comment="COBOL: CARD-NUM X(16) — VSAM KSDS primary key; CARDSID on CCRDUPA map",
    )

    # CARD-ACCT-ID 9(11) — FK to accounts; PROT (cannot change) in COCRDUPC
    account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("accounts.account_id", name="fk_cards_account"),
        nullable=False,
        comment="COBOL: CARD-ACCT-ID 9(11) — ACCTSID on map; PROT in COCRDUPC (cannot update)",
    )

    # CARD-CUST-ID 9(9)
    customer_id: Mapped[int] = mapped_column(
        SAInteger,
        ForeignKey("customers.customer_id", name="fk_cards_customer"),
        nullable=False,
        comment="COBOL: CARD-CUST-ID 9(9)",
    )

    # CARD-EMBOSSED-NAME X(50) — alpha-only validated by COCRDUPC
    card_embossed_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="COBOL: CARD-EMBOSSED-NAME X(50) — CRDNAME on map; alpha-only validated",
    )

    # CARD-ACTIVE-STATUS X(1) — Y=active, N=inactive; CRDSTCD on map
    active_status: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        default="Y",
        comment="COBOL: CARD-ACTIVE-STATUS X(1) — CRDSTCD on CCRDUPA map",
    )

    # Expiration stored as full date; month/year shown on COCRDUP map (EXPMON/EXPYEAR)
    expiration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="COBOL: CARD-EXPIRY-DATE — derived from EXPMON+EXPYEAR+EXPDAY on map",
    )

    # EXPDAY — hidden DRK PROT FSET field on COCRDUP map; maintained in state not shown to user
    expiration_day: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="COBOL: EXPDAY — DRK PROT FSET on COCRDUP map; hidden in UI",
    )

    # cvv — never shown in any update screen; stored encrypted in production
    cvv: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
        comment="CVV — not in any COBOL update screen; stored encrypted; never returned by API",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Row creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last-modified; replaces CCUP-OLD-DETAILS snapshot comparison in COCRDUPC",
    )

    def __repr__(self) -> str:
        return (
            f"CreditCard(card_number={self.card_number!r}, "
            f"account_id={self.account_id!r}, active_status={self.active_status!r})"
        )
