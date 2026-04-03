"""Card ORM model. Maps CVACT02Y / CARDFILE KSDS."""

from datetime import date

from sqlalchemy import CHAR, DATE, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Card(Base):
    """Credit card record (CVACT02Y)."""

    __tablename__ = "cards"

    card_num: Mapped[str] = mapped_column(VARCHAR(16), primary_key=True)
    card_acct_id: Mapped[str | None] = mapped_column(VARCHAR(11), nullable=True)
    card_cvv_cd: Mapped[str | None] = mapped_column(VARCHAR(3), nullable=True)
    card_embossed_name: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    card_expiration_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    card_active_status: Mapped[str] = mapped_column(CHAR(1), default="Y")
