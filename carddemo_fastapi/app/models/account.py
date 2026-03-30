"""Account model.

Derived from COBOL copybook: ACCTDATA (ACCTDAT.CPY).
Maps the credit-card account master record used throughout the CardDemo
application for account balances, limits, and cycle tracking.
"""

from sqlalchemy import BigInteger, Column, Numeric, String

from app.database import Base


class Account(Base):
    """Credit-card account master record.

    Corresponds to the VSAM KSDS file ACCTFILE keyed by ACCT-ID
    and the DB2 table equivalent defined in ACCTDAT.CPY.
    """

    __tablename__ = "accounts"

    # PIC 9(11) - Account identifier
    acct_id = Column(BigInteger, primary_key=True)

    # PIC X(1) - Active status flag ('Y'/'N')
    acct_active_status = Column(String(1), nullable=False, default="Y")

    # PIC S9(10)V99 - Current balance
    acct_curr_bal = Column(Numeric(12, 2), default=0)

    # PIC S9(10)V99 - Credit limit
    acct_credit_limit = Column(Numeric(12, 2), default=0)

    # PIC S9(10)V99 - Cash credit limit
    acct_cash_credit_limit = Column(Numeric(12, 2), default=0)

    # PIC X(10) - Account open date
    acct_open_date = Column(String(10))

    # PIC X(10) - Expiration date
    acct_expiration_date = Column(String(10))

    # PIC X(10) - Reissue date
    acct_reissue_date = Column(String(10))

    # PIC S9(10)V99 - Current cycle credit total
    acct_curr_cyc_credit = Column(Numeric(12, 2), default=0)

    # PIC S9(10)V99 - Current cycle debit total
    acct_curr_cyc_debit = Column(Numeric(12, 2), default=0)

    # PIC X(10) - Account ZIP code
    acct_addr_zip = Column(String(10))

    # PIC X(10) - Account group identifier
    acct_group_id = Column(String(10))

    def __repr__(self) -> str:
        return (
            f"<Account(acct_id={self.acct_id}, "
            f"status='{self.acct_active_status}', "
            f"bal={self.acct_curr_bal})>"
        )
