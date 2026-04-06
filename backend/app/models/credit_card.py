"""
CreditCard ORM model — maps CARDDAT VSAM KSDS to PostgreSQL `credit_cards` table.

COBOL source: CVACT02Y copybook, CARDDAT VSAM KSDS (150-byte record)
CICS access: EXEC CICS READ/REWRITE DATASET('CARDDAT') RIDFLD(CARD-NUM)

Record layout (CVACT02Y):
  CARD-NUM              PIC X(16)    → card_number      CHAR(16) PK
  CARD-ACCT-ID          PIC 9(11)    → account_id       BIGINT FK→accounts
  CARD-CVV-CD           PIC 9(03)    → (not stored — security policy)
  CARD-EMBOSSED-NAME    PIC X(50)    → card_embossed_name VARCHAR(50)
  CARD-EXPIRAION-DATE   PIC X(10)    → expiration_date   DATE (derived from EXPMON+EXPYEAR+EXPDAY)
  CARD-ACTIVE-STATUS    PIC X(01)    → active_status     CHAR(1)

Key COCRDUPC business rules:
  - ACCTSID is PROT — account_id CANNOT be changed via update
  - EXPDAY is a DRK PROT FSET hidden BMS field — stored separately so it can be restored
  - Optimistic lock: updated_at replaces CCUP-OLD-DETAILS snapshot comparison
"""

from datetime import date, datetime

from sqlalchemy import BigInteger, CHAR, CheckConstraint, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CreditCard(Base):
    """
    PostgreSQL `credit_cards` table.

    Replaces CARDDAT VSAM KSDS (CVACT02Y copybook, 150-byte record).
    CVV-CD is intentionally not stored (PCI-DSS compliance).
    expiration_day preserved from EXPDAY DRK PROT FSET BMS field (COCRDUPC).
    """

    __tablename__ = "credit_cards"
    __table_args__ = (
        CheckConstraint("active_status IN ('Y', 'N')", name="chk_cards_active_status"),
    )

    # CARD-NUM PIC X(16) — VSAM KSDS primary key
    card_number: Mapped[str] = mapped_column(
        CHAR(16), primary_key=True,
        comment="COBOL: CARD-NUM PIC X(16) — VSAM KSDS primary key",
    )

    # CARD-ACCT-ID PIC 9(11) — FK to accounts
    # PROT in COCRDUPC: cannot be changed via the update endpoint
    account_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="COBOL: CARD-ACCT-ID PIC 9(11) — PROT in COCRDUPC (cannot change)",
    )

    # Customer ID (from CARD-XREF-RECORD)
    customer_id: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="From CARD-XREF-RECORD XREF-CUST-ID PIC 9(09)",
    )

    # CARD-EMBOSSED-NAME PIC X(50) — alpha-only (INSPECT CONVERTING in COCRDUPC)
    card_embossed_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="COBOL: CARD-EMBOSSED-NAME PIC X(50) — alpha-only validated in COCRDUPC",
    )

    # CARD-EXPIRAION-DATE PIC X(10) → stored as DATE (COBOL typo preserved in comment)
    expiration_date: Mapped[date | None] = mapped_column(
        Date, nullable=True,
        comment="COBOL: CARD-EXPIRAION-DATE PIC X(10) — derived from EXPMON+EXPYEAR+EXPDAY",
    )

    # Hidden EXPDAY field from COCRDUPC BMS map (DRK PROT FSET)
    # Stored so the day can be preserved across MM/YYYY-only updates
    expiration_day: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="COBOL: EXPDAY DRK PROT FSET — hidden day component of expiry date in COCRDUPC",
    )

    # CARD-ACTIVE-STATUS PIC X(01) — Y/N
    active_status: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="Y",
        comment="COBOL: CARD-ACTIVE-STATUS PIC X(01) — Y/N",
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
        comment="Optimistic lock version — replaces CCUP-OLD-DETAILS snapshot in COCRDUPC",
    )

    def __repr__(self) -> str:
        return f"<CreditCard card_number=****{self.card_number[-4:]} account_id={self.account_id}>"
