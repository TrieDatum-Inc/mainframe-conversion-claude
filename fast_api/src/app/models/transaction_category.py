"""Transaction category reference ORM model. Maps CVTRA04Y / TRANCATG KSDS."""

from sqlalchemy import CHAR, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransactionCategory(Base):
    """Transaction category code and description reference (CVTRA04Y).

    Composite key: tran_type + tran_cat_cd.
    Used by CBTRN03C report generation to resolve category descriptions.
    """

    __tablename__ = "transaction_categories"

    tran_type: Mapped[str] = mapped_column(CHAR(2), primary_key=True)
    tran_cat_cd: Mapped[str] = mapped_column(VARCHAR(4), primary_key=True)
    tran_cat_desc: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
