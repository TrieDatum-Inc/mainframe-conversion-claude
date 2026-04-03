"""Disclosure group / interest rate ORM model. Maps CVTRA02Y / DISCGRP KSDS."""

from decimal import Decimal

from sqlalchemy import CHAR, NUMERIC, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DisclosureGroup(Base):
    """Interest rate definition by account group + transaction type + category (CVTRA02Y).

    'DEFAULT' group_id is the fallback used by CBACT04C when specific group not found.
    Rate stored as annual percentage (e.g., 18.00 = 18% APR).
    Monthly interest = (balance * rate) / 1200.
    """

    __tablename__ = "disclosure_groups"

    group_id: Mapped[str] = mapped_column(VARCHAR(10), primary_key=True)
    tran_type_cd: Mapped[str] = mapped_column(CHAR(2), primary_key=True)
    tran_cat_cd: Mapped[str] = mapped_column(VARCHAR(4), primary_key=True)
    interest_rate: Mapped[Decimal] = mapped_column(NUMERIC(7, 4), default=Decimal("0"))
