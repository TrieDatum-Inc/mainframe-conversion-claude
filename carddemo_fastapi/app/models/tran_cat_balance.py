"""Transaction category balance model.

Derived from COBOL copybook: TCATBAL (TCATBAL.CPY).
Maps the aggregated balance record per account, transaction type,
and transaction category used for reporting in the CardDemo application.
"""

from sqlalchemy import BigInteger, Column, Integer, Numeric, String

from app.database import Base


class TranCatBalance(Base):
    """Aggregated balance by account, transaction type, and category.

    Corresponds to the VSAM KSDS file TCATBALF with a composite key
    of TRANCAT-ACCT-ID + TRANCAT-TYPE-CD + TRANCAT-CD
    as defined in TCATBAL.CPY.
    """

    __tablename__ = "tran_cat_balance"

    # PIC 9(11) - Account identifier (part of composite PK)
    trancat_acct_id = Column(BigInteger, primary_key=True)

    # PIC X(2) - Transaction type code (part of composite PK)
    trancat_type_cd = Column(String(2), primary_key=True)

    # PIC 9(4) - Transaction category code (part of composite PK)
    trancat_cd = Column(Integer, primary_key=True)

    # PIC S9(9)V99 - Category balance
    tran_cat_bal = Column(Numeric(11, 2), default=0)

    def __repr__(self) -> str:
        return (
            f"<TranCatBalance(acct={self.trancat_acct_id}, "
            f"type='{self.trancat_type_cd}', "
            f"cat={self.trancat_cd}, "
            f"bal={self.tran_cat_bal})>"
        )
