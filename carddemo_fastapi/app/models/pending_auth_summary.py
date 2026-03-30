"""Pending authorization summary model.

Derived from COBOL copybook: DALYTRAN / PENDING-AUTH-SUMMARY.
Maps the per-account summary of pending authorization activity including
aggregate counts and amounts of approved and declined authorizations.
"""

from sqlalchemy import BigInteger, Column, Integer, Numeric, String

from app.database import Base


class PendingAuthSummary(Base):
    """Pending authorization summary record (per account).

    Provides a roll-up of pending authorization statistics for an
    account, including limits, balances, and approval/decline counts
    and amounts.
    """

    __tablename__ = "pending_auth_summary"

    # PIC 9(11) - Account identifier (primary key)
    pa_acct_id = Column(BigInteger, primary_key=True)

    # PIC 9(09) - Customer identifier
    pa_cust_id = Column(Integer, nullable=False)

    # PIC X(1) - Authorization status
    pa_auth_status = Column(String(1))

    # PIC X(2) - Account status fields 1-5
    pa_account_status_1 = Column(String(2))
    pa_account_status_2 = Column(String(2))
    pa_account_status_3 = Column(String(2))
    pa_account_status_4 = Column(String(2))
    pa_account_status_5 = Column(String(2))

    # PIC S9(9)V99 - Credit limit
    pa_credit_limit = Column(Numeric(11, 2))

    # PIC S9(9)V99 - Cash limit
    pa_cash_limit = Column(Numeric(11, 2))

    # PIC S9(9)V99 - Credit balance
    pa_credit_balance = Column(Numeric(11, 2))

    # PIC S9(9)V99 - Cash balance
    pa_cash_balance = Column(Numeric(11, 2))

    # PIC 9(9) - Approved authorization count
    pa_approved_auth_cnt = Column(Integer)

    # PIC 9(9) - Declined authorization count
    pa_declined_auth_cnt = Column(Integer)

    # PIC S9(9)V99 - Approved authorization amount
    pa_approved_auth_amt = Column(Numeric(11, 2))

    # PIC S9(9)V99 - Declined authorization amount
    pa_declined_auth_amt = Column(Numeric(11, 2))

    def __repr__(self) -> str:
        return (
            f"<PendingAuthSummary(acct={self.pa_acct_id}, "
            f"cust={self.pa_cust_id}, "
            f"approved_cnt={self.pa_approved_auth_cnt}, "
            f"declined_cnt={self.pa_declined_auth_cnt})>"
        )
