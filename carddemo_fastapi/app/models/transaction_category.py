"""Transaction category model.

Derived from COBOL copybook: TRANCATG (TRNCAT.CPY).
Maps the transaction category reference record that subdivides
transaction types into finer categories in the CardDemo application.
"""

from sqlalchemy import Column, ForeignKey, Integer, String

from app.database import Base


class TransactionCategory(Base):
    """Transaction category reference record.

    Corresponds to the VSAM KSDS file TRANCATF with a composite key
    of TRAN-TYPE-CD + TRAN-CAT-CD as defined in TRNCAT.CPY.
    """

    __tablename__ = "transaction_categories"

    # PIC X(2) - Transaction type code (part of composite PK, FK)
    tran_type_cd = Column(
        String(2),
        ForeignKey("transaction_types.tran_type"),
        primary_key=True,
    )

    # PIC 9(4) - Transaction category code (part of composite PK)
    tran_cat_cd = Column(Integer, primary_key=True)

    # PIC X(50) - Category description
    tran_cat_type_desc = Column(String(50), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<TransactionCategory(type='{self.tran_type_cd}', "
            f"cat={self.tran_cat_cd}, "
            f"desc='{self.tran_cat_type_desc}')>"
        )
