"""Transaction ORM model — maps to the `transactions` table (TRANSACT VSAM KSDS equivalent).

COBOL source copybook: CVTRA05Y.cpy
COBOL 01-level: TRAN-RECORD (350-byte record)
Key field: TRAN-ID PIC X(16) — stored as VARCHAR(16) PRIMARY KEY

COBIL00C uses this file to:
  1. Browse from HIGH-VALUES (STARTBR + READPREV) to find last TRAN-ID
  2. Write new payment transaction (TRAN-TYPE-CD='02', TRAN-CAT-CD=2)
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CHAR, NUMERIC, TIMESTAMP, VARCHAR, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# Bill payment constants — mirroring COBIL00C working storage literals
TRAN_TYPE_BILL_PAYMENT = "02"
TRAN_CAT_BILL_PAYMENT = 2
TRAN_SOURCE_BILL_PAYMENT = "POS TERM"
TRAN_DESC_BILL_PAYMENT = "BILL PAYMENT - ONLINE"
TRAN_MERCHANT_ID_BILL_PAYMENT = 999999999
TRAN_MERCHANT_NAME_BILL_PAYMENT = "BILL PAYMENT"
TRAN_MERCHANT_CITY_BILL_PAYMENT = "N/A"
TRAN_MERCHANT_ZIP_BILL_PAYMENT = "N/A"


class Transaction(Base):
    """Maps to transactions table.

    Transaction ID pattern (COBIL00C lines 212–219):
      Browse TRANSACT from HIGH-VALUES using READPREV to get last TRAN-ID,
      convert to numeric, add 1, format back as 16-char string.
      Modern equivalent: SELECT MAX(tran_id) + 1, left-padded to 16 chars.
    """

    __tablename__ = "transactions"

    tran_id: Mapped[str] = mapped_column(
        VARCHAR(16),
        primary_key=True,
        comment="TRAN-ID PIC X(16) — 16-char sequential transaction ID",
    )
    tran_type_cd: Mapped[str | None] = mapped_column(
        CHAR(2),
        nullable=True,
        comment="TRAN-TYPE-CD PIC X(02): '01'=Purchase, '02'=Payment, etc.",
    )
    tran_cat_cd: Mapped[int | None] = mapped_column(
        NUMERIC(4, 0),
        nullable=True,
        comment="TRAN-CAT-CD PIC 9(04) — transaction category code",
    )
    source: Mapped[str | None] = mapped_column(
        VARCHAR(10),
        nullable=True,
        comment="TRAN-SOURCE PIC X(10) — e.g. 'POS TERM', 'WEB'",
    )
    description: Mapped[str | None] = mapped_column(
        VARCHAR(100),
        nullable=True,
        comment="TRAN-DESC PIC X(100)",
    )
    amount: Mapped[Decimal] = mapped_column(
        NUMERIC(11, 2),
        nullable=False,
        comment="TRAN-AMT S9(09)V99 — transaction amount",
    )
    merchant_id: Mapped[int | None] = mapped_column(
        NUMERIC(9, 0),
        nullable=True,
        comment="TRAN-MERCHANT-ID 9(09)",
    )
    merchant_name: Mapped[str | None] = mapped_column(
        VARCHAR(50),
        nullable=True,
        comment="TRAN-MERCHANT-NAME PIC X(50)",
    )
    merchant_city: Mapped[str | None] = mapped_column(
        VARCHAR(50),
        nullable=True,
        comment="TRAN-MERCHANT-CITY PIC X(50)",
    )
    merchant_zip: Mapped[str | None] = mapped_column(
        VARCHAR(10),
        nullable=True,
        comment="TRAN-MERCHANT-ZIP PIC X(10)",
    )
    card_num: Mapped[str | None] = mapped_column(
        VARCHAR(16),
        nullable=True,
        comment="TRAN-CARD-NUM PIC X(16) — card number from CXACAIX cross-reference",
    )
    orig_timestamp: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="TRAN-ORIG-TS X(26) — original transaction timestamp",
    )
    proc_timestamp: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="TRAN-PROC-TS X(26) — processing timestamp",
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
