"""Transaction type model.

Derived from COBOL copybook: TRANTYPE (TRNTYPE.CPY).
Maps the transaction type reference record that defines the set of
valid two-character transaction type codes in the CardDemo application.
"""

from sqlalchemy import Column, String

from app.database import Base


class TransactionType(Base):
    """Transaction type reference record.

    Corresponds to the VSAM KSDS file TRANTYPF keyed by TRAN-TYPE
    as defined in TRNTYPE.CPY.
    """

    __tablename__ = "transaction_types"

    # PIC X(2) - Transaction type code
    tran_type = Column(String(2), primary_key=True)

    # PIC X(50) - Type description
    tran_type_desc = Column(String(50), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<TransactionType(type='{self.tran_type}', "
            f"desc='{self.tran_type_desc}')>"
        )
