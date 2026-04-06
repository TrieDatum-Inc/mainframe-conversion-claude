"""
CardXref ORM model — maps CARDXREF VSAM KSDS to PostgreSQL `card_account_xref` table.

COBOL source: CVACT03Y copybook (CARD-XREF-RECORD, 50-byte record)

Record layout:
  XREF-CARD-NUM   PIC X(16)   → card_number   CHAR(16) PK
  XREF-CUST-ID    PIC 9(09)   → customer_id   INTEGER
  XREF-ACCT-ID    PIC 9(11)   → account_id    BIGINT

CICS access pattern:
  EXEC CICS READ DATASET(CARDXREF) RIDFLD(XREF-CARD-NUM)     → get_by_card()
  EXEC CICS STARTBR DATASET(CARDAIX) RIDFLD(XREF-ACCT-ID)   → get_cards_by_account()
  (CARDAIX = Alternate Index on XREF-ACCT-ID)
  Replaced by PostgreSQL index idx_cardxref_account on account_id.
"""

from sqlalchemy import BigInteger, CHAR, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CardXref(Base):
    """
    PostgreSQL `card_account_xref` table.

    Replaces CARDXREF VSAM KSDS + CARDAIX (Alternate Index on account_id).
    The CARDAIX browse (STARTBR/READNEXT by XREF-ACCT-ID) is replaced by
    a SQL query on the idx_cardxref_account index.
    """

    __tablename__ = "card_account_xref"
    __table_args__ = (
        Index("idx_cardxref_account", "account_id"),
        Index("idx_cardxref_customer", "customer_id"),
    )

    # XREF-CARD-NUM PIC X(16) — VSAM KSDS primary key
    card_number: Mapped[str] = mapped_column(
        CHAR(16), primary_key=True,
        comment="COBOL: XREF-CARD-NUM PIC X(16) — VSAM KSDS primary key",
    )

    # XREF-CUST-ID PIC 9(09)
    customer_id: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="COBOL: XREF-CUST-ID PIC 9(09)",
    )

    # XREF-ACCT-ID PIC 9(11) — indexed to replace CARDAIX VSAM AIX
    account_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
        comment="COBOL: XREF-ACCT-ID PIC 9(11) — idx_cardxref_account replaces CARDAIX",
    )

    def __repr__(self) -> str:
        return f"<CardXref card=****{self.card_number[-4:]} acct={self.account_id}>"
