from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CHAR, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Account(Base):
    """
    Mirrors ACCOUNT-RECORD from CVACT01Y.cpy.
    Maps to ACCTDAT VSAM KSDS file.
    """

    __tablename__ = "accounts"

    acct_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    acct_active_status: Mapped[str] = mapped_column(CHAR(1), nullable=False, default="Y")
    acct_curr_bal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_cash_credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_open_date: Mapped[date | None] = mapped_column(nullable=True)
    acct_expiration_date: Mapped[date | None] = mapped_column(nullable=True)
    acct_reissue_date: Mapped[date | None] = mapped_column(nullable=True)
    acct_curr_cyc_credit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_curr_cyc_debit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_addr_zip: Mapped[str | None] = mapped_column(String(10), nullable=True)
    acct_group_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
