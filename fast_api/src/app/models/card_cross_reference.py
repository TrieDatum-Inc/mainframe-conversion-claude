from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CardCrossReference(Base):
    """
    Mirrors CARD-XREF-RECORD from CVACT03Y.cpy.
    Maps to CCXREF VSAM KSDS (primary key: card number).
    The unique constraint on xref_acct_id provides the CXACAIX alternate-index behavior.
    """

    __tablename__ = "card_cross_references"

    xref_card_num: Mapped[str] = mapped_column(String(16), primary_key=True)
    xref_cust_id: Mapped[str] = mapped_column(String(9), nullable=False)
    xref_acct_id: Mapped[str] = mapped_column(String(11), nullable=False, unique=True)
