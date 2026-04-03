"""Account ORM model. Maps CVACT01Y / ACCTFILE KSDS."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CHAR, DATE, NUMERIC, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Account(Base):
    """Credit card account master record (CVACT01Y)."""

    __tablename__ = "accounts"

    acct_id: Mapped[str] = mapped_column(VARCHAR(11), primary_key=True)
    acct_active_status: Mapped[str] = mapped_column(CHAR(1), default="Y")
    acct_curr_bal: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), default=Decimal("0"))
    acct_credit_limit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), default=Decimal("0"))
    acct_cash_credit_limit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), default=Decimal("0"))
    acct_open_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    acct_expiration_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    acct_reissue_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    acct_curr_cyc_credit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), default=Decimal("0"))
    acct_curr_cyc_debit: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), default=Decimal("0"))
    acct_addr_zip: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    acct_group_id: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True)
