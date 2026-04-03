"""Transaction category balance ORM model. Maps CVTRA01Y / TCATBALF KSDS."""

from decimal import Decimal

from sqlalchemy import CHAR, NUMERIC, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransactionCategoryBalance(Base):
    """Running balance per account/type/category combination (CVTRA01Y).

    Composite primary key: acct_id + tran_type_cd + tran_cat_cd.
    Updated by CBTRN02C (transaction posting) and read by CBACT04C (interest calc).
    """

    __tablename__ = "transaction_category_balances"

    acct_id: Mapped[str] = mapped_column(VARCHAR(11), primary_key=True)
    tran_type_cd: Mapped[str] = mapped_column(CHAR(2), primary_key=True)
    tran_cat_cd: Mapped[str] = mapped_column(VARCHAR(4), primary_key=True)
    balance: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), default=Decimal("0"))
