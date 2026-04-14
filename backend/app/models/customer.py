"""
Customer ORM model — maps to the `customers` PostgreSQL table.

COBOL origin: CUSTDAT VSAM KSDS (CVCUS01Y copybook), record length 500 bytes.
  - CUST-ID                  9(9)  → customer_id INTEGER PRIMARY KEY
  - CUST-FIRST-NAME          X(25) → first_name VARCHAR(25)
  - CUST-MIDDLE-NAME         X(25) → middle_name VARCHAR(25) nullable
  - CUST-LAST-NAME           X(25) → last_name VARCHAR(25)
  - CUST-ADDR-LINE-1         X(50) → street_address_1 VARCHAR(50) nullable
  - CUST-ADDR-LINE-2         X(50) → street_address_2 VARCHAR(50) nullable
  - CUST-ADDR-CITY           X(50) → city VARCHAR(50) nullable
  - CUST-ADDR-STATE-CD       X(2)  → state_code CHAR(2) nullable
  - CUST-ADDR-COUNTRY-CD     X(3)  → country_code CHAR(3) nullable
  - CUST-ADDR-ZIP            X(10) → zip_code VARCHAR(10) nullable
  - CUST-PHONE-NUM-1         X(15) → phone_number_1 VARCHAR(15) nullable
  - CUST-PHONE-NUM-2         X(15) → phone_number_2 VARCHAR(15) nullable
  - CUST-SSN                 9(9) (3+2+4 parts) → ssn VARCHAR(11) formatted NNN-NN-NNNN nullable
    SECURITY: In production, SSN should be encrypted at rest (AES-256).
    Display always uses masked form ***-**-XXXX (last 4 digits only).
    Never returned unmasked in any API response.
  - CUST-DOB-YYYY-MM-DD      X(10) → date_of_birth DATE nullable
  - CUST-EFT-ACCOUNT-ID      X(10) → eft_account_id VARCHAR(10) nullable
  - CUST-PRI-CARD-HOLDER-IND X(1)  → primary_card_holder_flag CHAR(1) default='Y'
  - CUST-FICO-CREDIT-SCORE   9(3)  → fico_score SMALLINT nullable
  - CUST-GOVT-ISSUED-ID      X(20) → government_id_ref VARCHAR(20) nullable

Replaces CICS file-control access pattern:
  EXEC CICS READ DATASET('CUSTDAT') INTO(CUSTOMER-RECORD) RIDFLD(CUST-ID) RESP RESP2
  RESP=NORMAL  → customer found
  RESP=NOTFND  → 404 CUSTOMER_NOT_FOUND
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
        comment="CUST-ID 9(9) — VSAM KSDS primary key",
    )
    first_name: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        comment="CUST-FIRST-NAME X(25) — ACSFNAM BMS field",
    )
    middle_name: Mapped[Optional[str]] = mapped_column(
        String(25),
        nullable=True,
        comment="CUST-MIDDLE-NAME X(25) — ACSMNAM BMS field",
    )
    last_name: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        comment="CUST-LAST-NAME X(25) — ACSLNAM BMS field",
    )
    street_address_1: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="CUST-ADDR-LINE-1 X(50) — ACSADL1 BMS field",
    )
    street_address_2: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="CUST-ADDR-LINE-2 X(50) — ACSADL2 BMS field",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="CUST-ADDR-CITY X(50) — ACSCITY BMS field",
    )
    state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
        comment="CUST-ADDR-STATE-CD X(2) — ACSSTTE BMS field",
    )
    zip_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="CUST-ADDR-ZIP X(10) — ACSZIPC BMS field",
    )
    country_code: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        comment="CUST-ADDR-COUNTRY-CD X(3) — ACSCTRY BMS field",
    )
    phone_number_1: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        comment="CUST-PHONE-NUM-1 X(15) — ACSPHN1 BMS field (NNN-NNN-NNNN format)",
    )
    phone_number_2: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        comment="CUST-PHONE-NUM-2 X(15) — ACSPHN2 BMS field",
    )
    ssn: Mapped[Optional[str]] = mapped_column(
        String(11),
        nullable=True,
        comment=(
            "CUST-SSN 9(9) stored as NNN-NN-NNNN. "
            "SECURITY: encrypt at rest in production. "
            "Never returned unmasked in any API response."
        ),
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="CUST-DOB-YYYY-MM-DD X(10) — ACSTDOB BMS field",
    )
    eft_account_id: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="CUST-EFT-ACCOUNT-ID X(10) — ACSEFTC BMS field",
    )
    primary_card_holder_flag: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
        default="Y",
        comment="CUST-PRI-CARD-HOLDER-IND X(1) — ACSPFLG BMS field; Y/N",
    )
    fico_score: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="CUST-FICO-CREDIT-SCORE 9(3) — ACSTFCO BMS field; 300-850 range",
    )
    government_id_ref: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="CUST-GOVT-ISSUED-ID X(20) — ACSGOVT BMS field",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "primary_card_holder_flag IN ('Y', 'N')",
            name="chk_customers_primary_flag",
        ),
        CheckConstraint(
            "fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)",
            name="chk_customers_fico",
        ),
    )

    def __repr__(self) -> str:
        return f"<Customer customer_id={self.customer_id!r} last_name={self.last_name!r}>"
