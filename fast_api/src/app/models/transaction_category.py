from sqlalchemy import CHAR, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionCategory(Base):
    """Maps to TRANCATG VSAM KSDS (composite key: type + category code)."""

    __tablename__ = "transaction_categories"

    tran_type: Mapped[str] = mapped_column(
        CHAR(2), ForeignKey("transaction_types.tran_type"), primary_key=True
    )
    tran_cat_cd: Mapped[str] = mapped_column(String(4), primary_key=True)
    tran_cat_desc: Mapped[str] = mapped_column(String(50), nullable=False)

    transaction_type: Mapped["TransactionType"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="categories"
    )
