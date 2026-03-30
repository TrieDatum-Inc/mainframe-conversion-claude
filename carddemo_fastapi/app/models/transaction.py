"""Transaction model.

Derived from COBOL copybook: TRANDATA (TRANDT.CPY / TRNX-RECORD).
Maps the individual financial transaction record produced by
the CardDemo online and batch transaction processing programs.
"""

from sqlalchemy import Column, Integer, Numeric, String

from app.database import Base


class Transaction(Base):
    """Financial transaction record.

    Corresponds to the VSAM KSDS file TRANFILE keyed by TRAN-ID
    as defined in TRANDT.CPY.
    """

    __tablename__ = "transactions"

    # PIC X(16) - Unique transaction identifier
    tran_id = Column(String(16), primary_key=True)

    # PIC X(2) - Transaction type code
    tran_type_cd = Column(String(2))

    # PIC 9(4) - Transaction category code
    tran_cat_cd = Column(Integer)

    # PIC X(10) - Transaction source
    tran_source = Column(String(10))

    # PIC X(100) - Transaction description
    tran_desc = Column(String(100))

    # PIC S9(9)V99 - Transaction amount
    tran_amt = Column(Numeric(11, 2))

    # PIC 9(9) - Merchant identifier
    tran_merchant_id = Column(Integer)

    # PIC X(50) - Merchant name
    tran_merchant_name = Column(String(50))

    # PIC X(50) - Merchant city
    tran_merchant_city = Column(String(50))

    # PIC X(10) - Merchant ZIP code
    tran_merchant_zip = Column(String(10))

    # PIC X(16) - Card number used for transaction
    tran_card_num = Column(String(16))

    # PIC X(26) - Original timestamp
    tran_orig_ts = Column(String(26))

    # PIC X(26) - Processing timestamp
    tran_proc_ts = Column(String(26))

    def __repr__(self) -> str:
        return (
            f"<Transaction(tran_id='{self.tran_id}', "
            f"type='{self.tran_type_cd}', "
            f"amt={self.tran_amt})>"
        )
