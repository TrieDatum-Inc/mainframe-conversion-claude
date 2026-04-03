"""Transaction ORM model. Maps CVTRA05Y / TRANSACT KSDS."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CHAR, NUMERIC, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Transaction(Base):
    """Posted transaction record (CVTRA05Y)."""

    __tablename__ = "transactions"

    tran_id: Mapped[str] = mapped_column(VARCHAR(16), primary_key=True)
    tran_type_cd: Mapped[str | None] = mapped_column(CHAR(2), nullable=True)
    tran_cat_cd: Mapped[str | None] = mapped_column(VARCHAR(4), nullable=True)
    tran_source: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    tran_desc: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    tran_amt: Mapped[Decimal | None] = mapped_column(NUMERIC(11, 2), nullable=True)
    tran_merchant_id: Mapped[str | None] = mapped_column(VARCHAR(9), nullable=True)
    tran_merchant_name: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    tran_merchant_city: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    tran_merchant_zip: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    tran_card_num: Mapped[str | None] = mapped_column(VARCHAR(16), nullable=True)
    tran_orig_ts: Mapped[datetime | None] = mapped_column(nullable=True)
    tran_proc_ts: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(nullable=True)
