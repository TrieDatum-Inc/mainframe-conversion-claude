from sqlalchemy import CHAR, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionType(Base):
    """Maps to TRANTYPE VSAM KSDS (2-char type code key)."""

    __tablename__ = "transaction_types"

    tran_type: Mapped[str] = mapped_column(CHAR(2), primary_key=True)
    tran_type_desc: Mapped[str] = mapped_column(String(50), nullable=False)

    categories: Mapped[list["TransactionCategory"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        back_populates="transaction_type", lazy="select"
    )
