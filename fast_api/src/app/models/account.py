from datetime import date, datetime
from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"
    acct_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    acct_active_status: Mapped[str] = mapped_column(String(1), nullable=False, default="Y")
    acct_curr_bal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_credit_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_cash_credit_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_open_date: Mapped[date | None] = mapped_column(nullable=True)
    acct_expiration_date: Mapped[date | None] = mapped_column(nullable=True)
    acct_reissue_date: Mapped[date | None] = mapped_column(nullable=True)
    acct_curr_cyc_credit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_curr_cyc_debit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_addr_zip: Mapped[str | None] = mapped_column(String(10), nullable=True)
    acct_group_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    cards: Mapped[list["Card"]] = relationship("Card", back_populates="account", lazy="select")  # type: ignore[name-defined]  # noqa: F821
    __table_args__ = (CheckConstraint("acct_active_status IN ('Y', 'N')", name="chk_accounts_active_status"),)
