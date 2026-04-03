"""Transaction type reference ORM model. Maps CVTRA03Y / TRANTYPE KSDS."""

from sqlalchemy import CHAR, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransactionType(Base):
    """Transaction type code and description reference (CVTRA03Y).

    Used by CBTRN03C report generation to resolve type descriptions.
    """

    __tablename__ = "transaction_types"

    tran_type: Mapped[str] = mapped_column(CHAR(2), primary_key=True)
    tran_type_desc: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
