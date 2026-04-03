"""Account ORM model.

Maps to CVACT01Y copybook / ACCTDAT VSAM file.
Note: The original COBOL source has a typo "EXPIRAION" which is preserved
in spec comments but corrected to "expiration" in our modern naming.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Account(Base):
    """Account master record — mirrors CVACT01Y copybook layout."""

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("acct_active_status IN ('Y', 'N')", name="ck_acct_active_status"),
    )

    acct_id: Mapped[str] = mapped_column(String(11), primary_key=True)
    acct_active_status: Mapped[str] = mapped_column(String(1), nullable=False, default="Y")
    acct_curr_bal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    acct_cash_credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    acct_open_date: Mapped[date | None]
    acct_expiration_date: Mapped[date | None]
    acct_reissue_date: Mapped[date | None]
    acct_curr_cyc_credit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    acct_curr_cyc_debit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0
    )
    acct_addr_zip: Mapped[str | None] = mapped_column(String(10))
    acct_group_id: Mapped[str | None] = mapped_column(String(10))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
