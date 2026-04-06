"""
SQLAlchemy ORM model for the `customers` table.

COBOL origin: CUSTDAT VSAM KSDS (CVCUS01Y copybook).
Record length: 500 bytes.

Field mapping:
  CUST-ID               9(9)   → customer_id INTEGER PRIMARY KEY
  CUST-FIRST-NAME       X(25)  → first_name VARCHAR(25)
  CUST-MIDDLE-NAME      X(25)  → middle_name VARCHAR(25)
  CUST-LAST-NAME        X(25)  → last_name VARCHAR(25)
  CUST-ADDR-LINE-1      X(50)  → street_address_1 VARCHAR(50)
  CUST-ADDR-LINE-2      X(50)  → street_address_2 VARCHAR(50)
  CUST-ADDR-CITY        X(50)  → city VARCHAR(50)
  CUST-ADDR-STATE-CD    X(2)   → state_code CHAR(2)
  CUST-ADDR-COUNTRY-CD  X(3)   → country_code CHAR(3)
  CUST-ADDR-ZIP         X(10)  → zip_code VARCHAR(10)
  CUST-PHONE-NUM-1      X(15)  → phone_number_1 VARCHAR(15)
  CUST-PHONE-NUM-2      X(15)  → phone_number_2 VARCHAR(15)
  CUST-SSN              9(3)+9(2)+9(4) → ssn VARCHAR(11) as NNN-NN-NNNN
  CUST-DOB-YYYY-MM-DD   X(10)  → date_of_birth DATE
  CUST-EFT-ACCOUNT-ID   X(10)  → eft_account_id VARCHAR(10)
  CUST-PRI-CARD-HOLDER-IND X(1) → primary_card_holder_flag CHAR(1)
  CUST-FICO-CREDIT-SCORE 9(3)  → fico_score SMALLINT
  CUST-GOVT-ISSUED-ID   X(20)  → government_id_ref VARCHAR(20)

COACTVWC reads CUSTDAT via account-customer cross-reference.
COACTUPC updates customer fields alongside account fields in a single transaction.
"""

from datetime import date, datetime

from sqlalchemy import CHAR, CheckConstraint, Date, DateTime, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    """
    PostgreSQL `customers` table.

    Replaces CUSTDAT VSAM KSDS.
    COACTVWC reads this for customer display rows 11-20 of CACTVWA map.
    COACTUPC updates customer fields including SSN validation:
      ACTSSN1 part1 not in (000, 666) and not in range 900-999.
    """

    __tablename__ = "customers"

    __table_args__ = (
        CheckConstraint(
            "primary_card_holder_flag IN ('Y', 'N')", name="chk_customers_primary_flag"
        ),
        CheckConstraint(
            "fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)",
            name="chk_customers_fico",
        ),
    )

    # CUST-ID 9(9) — VSAM KSDS primary key
    customer_id: Mapped[int] = mapped_column(
        primary_key=True,
        comment="COBOL: CUST-ID 9(9) — VSAM KSDS primary key; ACSTNUM on map",
    )

    # CUST-FIRST-NAME X(25) — alpha-only validated by COACTUPC INSPECT CONVERTING
    first_name: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        comment="COBOL: CUST-FIRST-NAME X(25) — ACSFNAM on CACTVWA map; alpha-only validated",
    )

    # CUST-MIDDLE-NAME X(25)
    middle_name: Mapped[str | None] = mapped_column(
        String(25),
        nullable=True,
        comment="COBOL: CUST-MIDDLE-NAME X(25) — ACSMNAM on map",
    )

    # CUST-LAST-NAME X(25) — alpha-only validated
    last_name: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        comment="COBOL: CUST-LAST-NAME X(25) — ACSLNAM on map; alpha-only validated",
    )

    # CUST-ADDR-LINE-1 X(50)
    street_address_1: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="COBOL: CUST-ADDR-LINE-1 X(50) — ACSADL1 on map",
    )

    # CUST-ADDR-LINE-2 X(50)
    street_address_2: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="COBOL: CUST-ADDR-LINE-2 X(50) — ACSADL2 on map",
    )

    # CUST-ADDR-CITY X(50)
    city: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="COBOL: CUST-ADDR-CITY X(50) — ACSCITY on map",
    )

    # CUST-ADDR-STATE-CD X(2)
    state_code: Mapped[str | None] = mapped_column(
        CHAR(2),
        nullable=True,
        comment="COBOL: CUST-ADDR-STATE-CD X(2) — ACSSTTE on map",
    )

    # CUST-ADDR-ZIP X(10)
    zip_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="COBOL: CUST-ADDR-ZIP X(10) — ACSZIPC on map",
    )

    # CUST-ADDR-COUNTRY-CD X(3)
    country_code: Mapped[str | None] = mapped_column(
        CHAR(3),
        nullable=True,
        comment="COBOL: CUST-ADDR-COUNTRY-CD X(3) — ACSCTRY on map",
    )

    # CUST-PHONE-NUM-1 X(15) — format NNN-NNN-NNNN; split into parts on map (ACSPH1A/B/C)
    phone_number_1: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
        comment="COBOL: CUST-PHONE-NUM-1 X(15) — ACSPHN1 on view; ACSPH1A/B/C on update",
    )

    # CUST-PHONE-NUM-2 X(15)
    phone_number_2: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
        comment="COBOL: CUST-PHONE-NUM-2 X(15) — ACSPHN2 on view; ACSPH2A/B/C on update",
    )

    # CUST-SSN — parts: ACTSSN1 9(3), ACTSSN2 9(2), ACTSSN3 9(4) stored as NNN-NN-NNNN
    # SSN validation in COACTUPC: part1 not 000 or 666, not in range 900-999
    ssn: Mapped[str | None] = mapped_column(
        String(11),
        nullable=True,
        comment="COBOL: CUST-SSN parts (3+2+4 digits); stored as NNN-NN-NNNN; encrypt at rest",
    )

    # CUST-DOB-YYYY-MM-DD X(10)
    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="COBOL: CUST-DOB-YYYY-MM-DD X(10) — ACSTDOB on map; DOBYEAR/DOBMON/DOBDAY on update",
    )

    # CUST-FICO-CREDIT-SCORE 9(3) — range 300-850
    fico_score: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="COBOL: CUST-FICO-CREDIT-SCORE 9(3) — ACSTFCO on map; CHECK 300-850",
    )

    # CUST-GOVT-ISSUED-ID X(20)
    government_id_ref: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="COBOL: CUST-GOVT-ISSUED-ID X(20) — ACSGOVT on map",
    )

    # CUST-EFT-ACCOUNT-ID X(10)
    eft_account_id: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="COBOL: CUST-EFT-ACCOUNT-ID X(10) — ACSEFTC on map",
    )

    # CUST-PRI-CARD-HOLDER-IND X(1) — Y=primary, N=secondary
    primary_card_holder_flag: Mapped[str] = mapped_column(
        CHAR(1),
        nullable=False,
        default="Y",
        comment="COBOL: CUST-PRI-CARD-HOLDER-IND X(1) — ACSPFLG on map; Y/N",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Row creation timestamp (not in original VSAM record)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last-modified timestamp; updated by trigger on every REWRITE",
    )

    def __repr__(self) -> str:
        return (
            f"Customer(customer_id={self.customer_id!r}, "
            f"last_name={self.last_name!r})"
        )
