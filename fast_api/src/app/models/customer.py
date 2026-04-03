"""Customer ORM model. Maps CVCUS01Y / CUSTFILE KSDS."""

from datetime import date

from sqlalchemy import CHAR, DATE, INTEGER, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    """Customer master record (CVCUS01Y)."""

    __tablename__ = "customers"

    cust_id: Mapped[str] = mapped_column(VARCHAR(9), primary_key=True)
    cust_first_name: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)
    cust_middle_name: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)
    cust_last_name: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)
    cust_addr_line_1: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    cust_addr_line_2: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    cust_addr_line_3: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    cust_addr_state_cd: Mapped[str | None] = mapped_column(CHAR(2), nullable=True)
    cust_addr_country_cd: Mapped[str | None] = mapped_column(CHAR(3), nullable=True)
    cust_addr_zip: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    cust_phone_num_1: Mapped[str | None] = mapped_column(VARCHAR(15), nullable=True)
    cust_phone_num_2: Mapped[str | None] = mapped_column(VARCHAR(15), nullable=True)
    cust_ssn: Mapped[str | None] = mapped_column(VARCHAR(9), nullable=True)
    cust_govt_issued_id: Mapped[str | None] = mapped_column(VARCHAR(20), nullable=True)
    cust_dob: Mapped[date | None] = mapped_column(DATE, nullable=True)
    cust_eft_account_id: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    cust_pri_card_holder_ind: Mapped[str | None] = mapped_column(CHAR(1), nullable=True)
    cust_fico_credit_score: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
