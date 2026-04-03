from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CardCrossReference(Base):
    __tablename__ = "card_cross_references"
    xref_card_num: Mapped[str] = mapped_column(String(16), ForeignKey("cards.card_num", ondelete="CASCADE"), primary_key=True)
    xref_cust_id: Mapped[str | None] = mapped_column(String(9), nullable=True, index=True)
    xref_acct_id: Mapped[str | None] = mapped_column(String(11), ForeignKey("accounts.acct_id", ondelete="RESTRICT"), nullable=True, index=True)
    card: Mapped["Card"] = relationship("Card", back_populates="cross_reference", lazy="select")  # type: ignore[name-defined]  # noqa: F821
