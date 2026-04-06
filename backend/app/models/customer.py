"""
Customer ORM model — maps CUSTDAT VSAM KSDS to PostgreSQL `customers` table.

COBOL source: CVCUS01Y copybook, CUSTDAT VSAM KSDS (500-byte record)

Record layout (CVCUS01Y):
  CUST-ID                  PIC 9(09)       → customer_id     INTEGER PK
  CUST-FIRST-NAME          PIC X(25)       → first_name      VARCHAR(25)
  CUST-MIDDLE-NAME         PIC X(25)       → middle_name     VARCHAR(25)
  CUST-LAST-NAME           PIC X(25)       → last_name       VARCHAR(25)
  CUST-ADDR-LINE-1         PIC X(50)       → address_line_1  VARCHAR(50)
  CUST-ADDR-LINE-2         PIC X(50)       → address_line_2  VARCHAR(50)
  CUST-ADDR-LINE-3         PIC X(50)       → address_line_3  VARCHAR(50)
  CUST-ADDR-STATE-CD       PIC X(02)       → state_code      CHAR(2)
  CUST-ADDR-COUNTRY-CD     PIC X(03)       → country_code    CHAR(3)
  CUST-ADDR-ZIP            PIC X(10)       → zip_code        VARCHAR(10)
  CUST-PHONE-NUM-1         PIC X(15)       → phone_1         VARCHAR(15)
  CUST-PHONE-NUM-2         PIC X(15)       → phone_2         VARCHAR(15)
  CUST-SSN                 PIC 9(09)       → ssn             VARCHAR(11) NNN-NN-NNNN
  CUST-GOVT-ISSUED-ID      PIC X(20)       → government_id_ref VARCHAR(20)
  CUST-DOB-YYYY-MM-DD      PIC X(10)       → date_of_birth   DATE
  CUST-EFT-ACCOUNT-ID      PIC X(10)       → eft_account_id  VARCHAR(10)
  CUST-PRI-CARD-HOLDER-IND PIC X(01)       → primary_card_holder CHAR(1)
  CUST-FICO-CREDIT-SCORE   PIC 9(03)       → fico_score      SMALLINT CHECK 300-850
"""

from datetime import date, datetime

from sqlalchemy import (
    CHAR, CheckConstraint, Date, DateTime, Integer, SmallInteger,
    String, func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    """
    PostgreSQL `customers` table.

    Replaces CUSTDAT VSAM KSDS (CVCUS01Y copybook, 500-byte record).
    SSN stored as VARCHAR(11) in NNN-NN-NNNN format (not as 9-digit integer).
    SSN is NEVER returned in API responses — only a masked version.
    FICO score constrained to valid credit bureau range 300-850.
    """

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint(
            "primary_card_holder IN ('Y', 'N')",
            name="chk_customers_primary_card_holder",
        ),
        CheckConstraint(
            "fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)",
            name="chk_customers_fico_range",
        ),
    )

    # CUST-ID PIC 9(09) — VSAM KSDS primary key
    customer_id: Mapped[int] = mapped_column(
        Integer, primary_key=True,
        comment="COBOL: CUST-ID PIC 9(09) — VSAM KSDS primary key",
    )

    # Name fields
    first_name: Mapped[str] = mapped_column(
        String(25), nullable=False,
        comment="COBOL: CUST-FIRST-NAME PIC X(25)",
    )
    middle_name: Mapped[str | None] = mapped_column(
        String(25), nullable=True,
        comment="COBOL: CUST-MIDDLE-NAME PIC X(25)",
    )
    last_name: Mapped[str] = mapped_column(
        String(25), nullable=False,
        comment="COBOL: CUST-LAST-NAME PIC X(25)",
    )

    # Address fields
    address_line_1: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="COBOL: CUST-ADDR-LINE-1 PIC X(50)",
    )
    address_line_2: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="COBOL: CUST-ADDR-LINE-2 PIC X(50)",
    )
    address_line_3: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="COBOL: CUST-ADDR-LINE-3 PIC X(50)",
    )
    state_code: Mapped[str | None] = mapped_column(
        CHAR(2), nullable=True,
        comment="COBOL: CUST-ADDR-STATE-CD PIC X(02)",
    )
    country_code: Mapped[str | None] = mapped_column(
        CHAR(3), nullable=True,
        comment="COBOL: CUST-ADDR-COUNTRY-CD PIC X(03)",
    )
    zip_code: Mapped[str | None] = mapped_column(
        String(10), nullable=True,
        comment="COBOL: CUST-ADDR-ZIP PIC X(10)",
    )

    # Contact
    phone_1: Mapped[str | None] = mapped_column(
        String(15), nullable=True,
        comment="COBOL: CUST-PHONE-NUM-1 PIC X(15)",
    )
    phone_2: Mapped[str | None] = mapped_column(
        String(15), nullable=True,
        comment="COBOL: CUST-PHONE-NUM-2 PIC X(15)",
    )

    # SSN — stored as VARCHAR NNN-NN-NNNN; NEVER exposed in API responses plain
    ssn: Mapped[str | None] = mapped_column(
        String(11), nullable=True,
        comment="COBOL: CUST-SSN PIC 9(09) — stored NNN-NN-NNNN; masked in responses",
    )

    # Government ID
    government_id_ref: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        comment="COBOL: CUST-GOVT-ISSUED-ID PIC X(20)",
    )

    # Dates
    date_of_birth: Mapped[date | None] = mapped_column(
        Date, nullable=True,
        comment="COBOL: CUST-DOB-YYYY-MM-DD PIC X(10)",
    )

    # EFT
    eft_account_id: Mapped[str | None] = mapped_column(
        String(10), nullable=True,
        comment="COBOL: CUST-EFT-ACCOUNT-ID PIC X(10)",
    )

    # Card holder flag
    primary_card_holder: Mapped[str] = mapped_column(
        CHAR(1), nullable=False, default="Y",
        comment="COBOL: CUST-PRI-CARD-HOLDER-IND PIC X(01) Y/N",
    )

    # FICO score — CHECK 300-850
    fico_score: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True,
        comment="COBOL: CUST-FICO-CREDIT-SCORE PIC 9(03) — valid range 300-850",
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Customer customer_id={self.customer_id} name={self.last_name!r}>"
