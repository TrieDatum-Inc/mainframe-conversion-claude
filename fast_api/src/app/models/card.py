"""Card ORM model.

Maps to CVACT02Y copybook / CARDDAT VSAM file.
"""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Card(Base):
    """Credit card record — mirrors CVACT02Y copybook layout."""

    __tablename__ = "cards"
    __table_args__ = (
        CheckConstraint("card_active_status IN ('Y', 'N')", name="ck_card_active_status"),
    )

    card_num: Mapped[str] = mapped_column(String(16), primary_key=True)
    card_acct_id: Mapped[str | None] = mapped_column(
        String(11), ForeignKey("accounts.acct_id", ondelete="SET NULL")
    )
    card_cvv_cd: Mapped[str | None] = mapped_column(String(3))
    card_embossed_name: Mapped[str | None] = mapped_column(String(50))
    card_expiration_date: Mapped[date | None]
    card_active_status: Mapped[str] = mapped_column(String(1), nullable=False, default="Y")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
