"""CardCrossReference ORM model — maps to card_cross_references table.

COBOL source copybook: CVACT03Y.cpy
COBOL 01-level: CARD-XREF-RECORD (50-byte record)
Key field: XREF-CARD-NUM PIC X(16) — primary key
Alternate index: XREF-ACCT-ID PIC 9(11) — accessed by COBIL00C via CXACAIX AIX file

COBIL00C uses this to get the card number for a given account ID
when building the bill payment transaction record.
"""
from datetime import datetime

from sqlalchemy import NUMERIC, TIMESTAMP, VARCHAR, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CardCrossReference(Base):
    """Maps to card_cross_references table.

    CICS access pattern (COBIL00C READ-CXACAIX-FILE):
      EXEC CICS READ DATASET('CXACAIX') RIDFLD(XREF-ACCT-ID)
      → SELECT * FROM card_cross_references WHERE acct_id = :acct_id LIMIT 1
    """

    __tablename__ = "card_cross_references"

    card_num: Mapped[str] = mapped_column(
        VARCHAR(16),
        primary_key=True,
        comment="XREF-CARD-NUM PIC X(16) — credit card number",
    )
    cust_id: Mapped[int] = mapped_column(
        NUMERIC(9, 0),
        nullable=False,
        comment="XREF-CUST-ID PIC 9(09) — customer ID",
    )
    acct_id: Mapped[int] = mapped_column(
        NUMERIC(11, 0),
        nullable=False,
        comment="XREF-ACCT-ID PIC 9(11) — account ID (alternate key in COBOL AIX)",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
