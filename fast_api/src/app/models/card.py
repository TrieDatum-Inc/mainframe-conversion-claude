from datetime import date, datetime
from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from app.database import Base


class Card(Base):
    __tablename__ = "cards"
    card_num: Mapped[str] = mapped_column(String(16), primary_key=True)
    card_acct_id: Mapped[str] = mapped_column(String(11), ForeignKey("accounts.acct_id", ondelete="RESTRICT"), nullable=False, index=True)
    card_cvv_cd: Mapped[str | None] = mapped_column(String(3), nullable=True)
    card_embossed_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    card_expiration_date: Mapped[date | None] = mapped_column(nullable=True)
    card_active_status: Mapped[str] = mapped_column(String(1), nullable=False, default="Y")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    account: Mapped["Account"] = relationship("Account", back_populates="cards", lazy="select")  # type: ignore[name-defined]  # noqa: F821
    cross_reference: Mapped["CardCrossReference | None"] = relationship("CardCrossReference", back_populates="card", lazy="select")  # type: ignore[name-defined]  # noqa: F821
    __table_args__ = (CheckConstraint("card_active_status IN ('Y', 'N')", name="chk_cards_active_status"),)
