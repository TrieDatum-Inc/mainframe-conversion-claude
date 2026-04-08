"""
SQLAlchemy ORM model for the `customers` table.

Source copybook: app/cpy/CVCUS01Y.cpy — CUSTOMER-RECORD (500 bytes)
Source VSAM file: AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS (CUSTDAT)
Primary key: CUST-ID PIC 9(09) → Integer

Security note: CUST-SSN and CUST-GOVT-ISSUED-ID are sensitive fields.
In production, encrypt at rest using column-level encryption.
"""
from sqlalchemy import CheckConstraint, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    """
    Customer record.

    Maps to COBOL CUSTOMER-RECORD (CVCUS01Y.cpy).
    CUST-ID is a 9-digit number (PIC 9(09)) used as integer PK.
    """

    __tablename__ = "customers"
    __table_args__ = (
        # CUST-FICO-CREDIT-SCORE range 300-850
        CheckConstraint(
            "fico_credit_score BETWEEN 300 AND 850 OR fico_credit_score = 0",
            name="ck_customers_fico_score_range",
        ),
        # CUST-PRI-CARD-HOLDER-IND PIC X(01)
        CheckConstraint(
            "pri_card_holder_ind IN ('Y', 'N')",
            name="ck_customers_pri_card_holder",
        ),
        Index("ix_customers_last_name", "last_name"),
        Index("ix_customers_ssn", "ssn"),
    )

    # CUST-ID PIC 9(09)
    cust_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment="CUST-ID PIC 9(09)")

    # CUST-FIRST-NAME PIC X(25)
    first_name: Mapped[str | None] = mapped_column(String(25), nullable=True, comment="CUST-FIRST-NAME PIC X(25)")

    # CUST-MIDDLE-NAME PIC X(25)
    middle_name: Mapped[str | None] = mapped_column(String(25), nullable=True, comment="CUST-MIDDLE-NAME PIC X(25)")

    # CUST-LAST-NAME PIC X(25)
    last_name: Mapped[str | None] = mapped_column(String(25), nullable=True, comment="CUST-LAST-NAME PIC X(25)")

    # CUST-ADDR-LINE-1 PIC X(50)
    addr_line_1: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="CUST-ADDR-LINE-1 PIC X(50)")

    # CUST-ADDR-LINE-2 PIC X(50)
    addr_line_2: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="CUST-ADDR-LINE-2 PIC X(50)")

    # CUST-ADDR-LINE-3 PIC X(50)
    addr_line_3: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="CUST-ADDR-LINE-3 PIC X(50)")

    # CUST-ADDR-STATE-CD PIC X(02)
    addr_state_cd: Mapped[str | None] = mapped_column(String(2), nullable=True, comment="CUST-ADDR-STATE-CD PIC X(02)")

    # CUST-ADDR-COUNTRY-CD PIC X(03)
    addr_country_cd: Mapped[str | None] = mapped_column(
        String(3), nullable=True, comment="CUST-ADDR-COUNTRY-CD PIC X(03)"
    )

    # CUST-ADDR-ZIP PIC X(10)
    addr_zip: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="CUST-ADDR-ZIP PIC X(10)")

    # CUST-PHONE-NUM-1 PIC X(15)
    phone_num_1: Mapped[str | None] = mapped_column(String(15), nullable=True, comment="CUST-PHONE-NUM-1 PIC X(15)")

    # CUST-PHONE-NUM-2 PIC X(15)
    phone_num_2: Mapped[str | None] = mapped_column(String(15), nullable=True, comment="CUST-PHONE-NUM-2 PIC X(15)")

    # CUST-SSN PIC 9(09) — sensitive, encrypt at rest in production
    ssn: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="CUST-SSN PIC 9(09) [sensitive]")

    # CUST-GOVT-ISSUED-ID PIC X(20) — sensitive
    govt_issued_id: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="CUST-GOVT-ISSUED-ID PIC X(20) [sensitive]"
    )

    # CUST-DOB-YYYY-MM-DD PIC X(10)
    dob: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="CUST-DOB-YYYY-MM-DD PIC X(10)")

    # CUST-EFT-ACCOUNT-ID PIC X(10)
    eft_account_id: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="CUST-EFT-ACCOUNT-ID PIC X(10)"
    )

    # CUST-PRI-CARD-HOLDER-IND PIC X(01) 'Y'/'N'
    pri_card_holder_ind: Mapped[str | None] = mapped_column(
        String(1), nullable=True, default="Y", comment="CUST-PRI-CARD-HOLDER-IND PIC X(01)"
    )

    # CUST-FICO-CREDIT-SCORE PIC 9(03) — range 300-850
    fico_credit_score: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="CUST-FICO-CREDIT-SCORE PIC 9(03)"
    )

    # Relationships
    card_xrefs: Mapped[list["CardXref"]] = relationship("CardXref", back_populates="customer", lazy="select")
