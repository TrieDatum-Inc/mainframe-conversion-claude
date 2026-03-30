"""Card model.

Derived from COBOL copybook: CARDDATA (CARDDAT.CPY).
Maps the credit-card detail record linking a physical card number
to an account in the CardDemo application.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, SmallInteger, String

from app.database import Base


class Card(Base):
    """Credit-card detail record.

    Corresponds to the VSAM KSDS file CARDFILE with a composite key
    of CARD-NUM + CARD-ACCT-ID as defined in CARDDAT.CPY.
    """

    __tablename__ = "cards"

    # PIC X(16) - Card number (part of composite PK)
    card_num = Column(String(16), primary_key=True)

    # PIC 9(11) - Account ID (part of composite PK, FK to accounts)
    card_acct_id = Column(
        BigInteger,
        ForeignKey("accounts.acct_id"),
        primary_key=True,
    )

    # PIC 9(3) - Card verification value
    card_cvv_cd = Column(SmallInteger, nullable=False)

    # PIC X(50) - Name embossed on card
    card_embossed_name = Column(String(50))

    # PIC X(10) - Expiration date
    card_expiration_date = Column(String(10))

    # PIC X(1) - Active status flag ('Y'/'N')
    card_active_status = Column(String(1), default="Y")

    def __repr__(self) -> str:
        return (
            f"<Card(card_num='{self.card_num}', "
            f"acct_id={self.card_acct_id}, "
            f"status='{self.card_active_status}')>"
        )
