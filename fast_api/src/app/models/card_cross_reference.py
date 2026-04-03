"""Card cross-reference ORM model. Maps CVACT03Y / XREFFILE KSDS."""

from sqlalchemy import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CardCrossReference(Base):
    """Card-to-account cross-reference record (CVACT03Y).

    Primary key: xref_card_num (card number).
    Alternate key: xref_acct_id (used by CBACT04C to look up card num from account).
    """

    __tablename__ = "card_cross_references"

    xref_card_num: Mapped[str] = mapped_column(VARCHAR(16), primary_key=True)
    xref_cust_id: Mapped[str | None] = mapped_column(VARCHAR(9), nullable=True)
    xref_acct_id: Mapped[str | None] = mapped_column(VARCHAR(11), nullable=True)
