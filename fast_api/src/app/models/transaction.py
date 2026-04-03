from datetime import datetime
from decimal import Decimal

from sqlalchemy import CHAR, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Transaction(Base):
    """
    Mirrors TRAN-RECORD layout from CVTRA05Y.cpy (350 bytes, key TRAN-ID X(16)).
    Maps to the TRANSACT VSAM KSDS file.
    """

    __tablename__ = "transactions"

    tran_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    tran_type_cd: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    tran_cat_cd: Mapped[str] = mapped_column(String(4), nullable=False)
    tran_source: Mapped[str] = mapped_column(String(10), nullable=False)
    tran_desc: Mapped[str] = mapped_column(String(100), nullable=False)
    tran_amt: Mapped[Decimal] = mapped_column(Numeric(11, 2), nullable=False)
    tran_merchant_id: Mapped[str] = mapped_column(String(9), nullable=False)
    tran_merchant_name: Mapped[str] = mapped_column(String(50), nullable=False)
    tran_merchant_city: Mapped[str] = mapped_column(String(50), nullable=False)
    tran_merchant_zip: Mapped[str] = mapped_column(String(10), nullable=False)
    tran_card_num: Mapped[str] = mapped_column(String(16), nullable=False)
    tran_orig_ts: Mapped[datetime] = mapped_column(nullable=False)
    tran_proc_ts: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
