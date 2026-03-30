"""Card cross-reference model.

Derived from COBOL copybook: CARDXREF (CXREF.CPY).
Maps the cross-reference record that links a card number to both
a customer and an account in the CardDemo application.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String

from app.database import Base


class CardXref(Base):
    """Card-to-customer-to-account cross-reference record.

    Corresponds to the VSAM KSDS file CARDXREF keyed by XREF-CARD-NUM
    as defined in CXREF.CPY.
    """

    __tablename__ = "card_xref"

    # PIC X(16) - Card number (primary key)
    xref_card_num = Column(String(16), primary_key=True)

    # PIC 9(09) - Customer ID (FK to customers)
    xref_cust_id = Column(
        Integer,
        ForeignKey("customers.cust_id"),
        nullable=False,
    )

    # PIC 9(11) - Account ID (FK to accounts)
    xref_acct_id = Column(
        BigInteger,
        ForeignKey("accounts.acct_id"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<CardXref(card='{self.xref_card_num}', "
            f"cust={self.xref_cust_id}, "
            f"acct={self.xref_acct_id})>"
        )
