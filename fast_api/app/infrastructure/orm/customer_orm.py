"""
SQLAlchemy ORM model for the Customer entity.

Source: VSAM KSDS CUSTDAT / copybook CVCUS01Y (500 bytes)
Primary key: CUST-ID PIC 9(09)

Field mapping:
  CUST-ID                  PIC 9(09)     -> cust_id          INTEGER PRIMARY KEY
  CUST-FIRST-NAME          PIC X(25)     -> first_name       VARCHAR(25)
  CUST-MIDDLE-NAME         PIC X(25)     -> middle_name      VARCHAR(25)
  CUST-LAST-NAME           PIC X(25)     -> last_name        VARCHAR(25)
  CUST-ADDR-LINE-1         PIC X(50)     -> addr_line1       VARCHAR(50)
  CUST-ADDR-LINE-2         PIC X(50)     -> addr_line2       VARCHAR(50)
  CUST-ADDR-LINE-3         PIC X(50)     -> addr_line3       VARCHAR(50)  (city)
  CUST-ADDR-STATE-CD       PIC X(02)     -> addr_state_cd    CHAR(2)
  CUST-ADDR-COUNTRY-CD     PIC X(03)     -> addr_country_cd  CHAR(3)
  CUST-ADDR-ZIP            PIC X(10)     -> addr_zip         VARCHAR(10)
  CUST-PHONE-NUM-1         PIC X(15)     -> phone_num1       VARCHAR(15)
  CUST-PHONE-NUM-2         PIC X(15)     -> phone_num2       VARCHAR(15)
  CUST-SSN                 PIC 9(09)     -> ssn              INTEGER
  CUST-GOVT-ISSUED-ID      PIC X(20)     -> govt_issued_id   VARCHAR(20)
  CUST-DOB-YYYY-MM-DD      PIC X(10)     -> dob              DATE
  CUST-EFT-ACCOUNT-ID      PIC X(10)     -> eft_account_id   VARCHAR(10)
  CUST-PRI-CARD-HOLDER-IND PIC X(01)     -> pri_card_holder  CHAR(1)
  CUST-FICO-CREDIT-SCORE   PIC 9(03)     -> fico_score       SMALLINT
  FILLER                   PIC X(168)    -> (omitted)

State code validation from CSLKPCDY.CPY:
  Valid US state codes: 2-letter abbreviations (AL, AK, AZ, AR, CA, ...)
"""

from datetime import date

from sqlalchemy import (
    CHAR,
    DATE,
    VARCHAR,
    BigInteger,
    CheckConstraint,
    Index,
    Integer,
    SmallInteger,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base

# Valid US state codes from CSLKPCDY copybook
VALID_US_STATE_CODES = frozenset([
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP",
])


class CustomerORM(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("cust_id > 0", name="ck_customer_id_positive"),
        CheckConstraint(
            "ssn >= 100000000 AND ssn <= 999999999",
            name="ck_customer_ssn_range",
        ),
        CheckConstraint(
            "fico_score >= 300 AND fico_score <= 850",
            name="ck_customer_fico_range",
        ),
        CheckConstraint(
            "pri_card_holder IN ('Y', 'N')",
            name="ck_customer_pri_card_holder",
        ),
        Index("ix_customers_last_name", "last_name"),
        Index("ix_customers_ssn", "ssn"),
    )

    # CUST-ID PIC 9(09) - max 999999999 = 9 digits
    cust_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # CUST-FIRST-NAME PIC X(25)
    first_name: Mapped[str] = mapped_column(VARCHAR(25), nullable=False)

    # CUST-MIDDLE-NAME PIC X(25)
    middle_name: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)

    # CUST-LAST-NAME PIC X(25)
    last_name: Mapped[str] = mapped_column(VARCHAR(25), nullable=False)

    # CUST-ADDR-LINE-1 PIC X(50)
    addr_line1: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)

    # CUST-ADDR-LINE-2 PIC X(50)
    addr_line2: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)

    # CUST-ADDR-LINE-3 PIC X(50) - used for city in display
    addr_line3: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)

    # CUST-ADDR-STATE-CD PIC X(02) - validated against CSLKPCDY US state table
    addr_state_cd: Mapped[str | None] = mapped_column(CHAR(2), nullable=True)

    # CUST-ADDR-COUNTRY-CD PIC X(03) - 3-char country code
    addr_country_cd: Mapped[str | None] = mapped_column(CHAR(3), nullable=True)

    # CUST-ADDR-ZIP PIC X(10)
    addr_zip: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)

    # CUST-PHONE-NUM-1 PIC X(15) - stored as (999)999-9999 format in COBOL
    phone_num1: Mapped[str | None] = mapped_column(VARCHAR(15), nullable=True)

    # CUST-PHONE-NUM-2 PIC X(15)
    phone_num2: Mapped[str | None] = mapped_column(VARCHAR(15), nullable=True)

    # CUST-SSN PIC 9(09) - 9-digit social security number
    ssn: Mapped[int] = mapped_column(Integer, nullable=False)

    # CUST-GOVT-ISSUED-ID PIC X(20)
    govt_issued_id: Mapped[str | None] = mapped_column(VARCHAR(20), nullable=True)

    # CUST-DOB-YYYY-MM-DD PIC X(10) - stored as DATE
    dob: Mapped[date | None] = mapped_column(DATE, nullable=True)

    # CUST-EFT-ACCOUNT-ID PIC X(10)
    eft_account_id: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)

    # CUST-PRI-CARD-HOLDER-IND PIC X(01) - 'Y'/'N'
    pri_card_holder: Mapped[str | None] = mapped_column(CHAR(1), nullable=True, default="Y")

    # CUST-FICO-CREDIT-SCORE PIC 9(03) - 3-digit FICO score (300-850)
    fico_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Customer id={self.cust_id} "
            f"name={self.first_name} {self.last_name}>"
        )
