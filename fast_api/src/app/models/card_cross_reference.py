"""Card Cross-Reference ORM model.

Maps to CVACT03Y copybook / CXACAIX VSAM alternate index.
In COBOL, CXACAIX was a KSDS alternate index keyed by XREF-ACCT-ID.
Here it is a regular table with an index on xref_acct_id.
"""

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CardCrossReference(Base):
    """Card cross-reference — mirrors CVACT03Y copybook layout.

    Provides account→customer→card linkage, replacing the CXACAIX alternate index.
    """

    __tablename__ = "card_cross_references"
    __table_args__ = (
        Index("idx_card_xref_acct_id", "xref_acct_id"),
        Index("idx_card_xref_cust_id", "xref_cust_id"),
    )

    xref_card_num: Mapped[str] = mapped_column(String(16), primary_key=True)
    xref_cust_id: Mapped[str | None] = mapped_column(
        String(9), ForeignKey("customers.cust_id", ondelete="SET NULL")
    )
    xref_acct_id: Mapped[str | None] = mapped_column(
        String(11), ForeignKey("accounts.acct_id", ondelete="SET NULL")
    )
