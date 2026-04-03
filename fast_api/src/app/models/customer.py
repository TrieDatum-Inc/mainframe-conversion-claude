"""Customer ORM model.

Maps to CVCUS01Y copybook / CUSTDAT VSAM file.
"""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    """Customer master record — mirrors CVCUS01Y copybook layout."""

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("cust_pri_card_holder_ind IN ('Y', 'N')", name="ck_cust_pri_card_holder"),
        CheckConstraint(
            "cust_fico_credit_score BETWEEN 300 AND 850",
            name="ck_cust_fico_range",
        ),
    )

    cust_id: Mapped[str] = mapped_column(String(9), primary_key=True)
    cust_first_name: Mapped[str | None] = mapped_column(String(25))
    cust_middle_name: Mapped[str | None] = mapped_column(String(25))
    cust_last_name: Mapped[str | None] = mapped_column(String(25))
    cust_addr_line_1: Mapped[str | None] = mapped_column(String(50))
    cust_addr_line_2: Mapped[str | None] = mapped_column(String(50))
    cust_addr_line_3: Mapped[str | None] = mapped_column(String(50))
    cust_addr_state_cd: Mapped[str | None] = mapped_column(String(2))
    cust_addr_country_cd: Mapped[str | None] = mapped_column(String(3))
    cust_addr_zip: Mapped[str | None] = mapped_column(String(10))
    cust_phone_num_1: Mapped[str | None] = mapped_column(String(15))
    cust_phone_num_2: Mapped[str | None] = mapped_column(String(15))
    cust_ssn: Mapped[str | None] = mapped_column(String(9))
    cust_govt_issued_id: Mapped[str | None] = mapped_column(String(20))
    cust_dob: Mapped[date | None]
    cust_eft_account_id: Mapped[str | None] = mapped_column(String(10))
    cust_pri_card_holder_ind: Mapped[str | None] = mapped_column(String(1))
    cust_fico_credit_score: Mapped[int | None]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
