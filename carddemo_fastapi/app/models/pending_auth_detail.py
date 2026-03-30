"""Pending authorization detail model.

Derived from COBOL copybook: DALYTRAN / PENDING-AUTH-DETAIL.
Maps individual pending authorization detail records linked to the
pending authorization summary for an account.
"""

from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, SmallInteger, String

from app.database import Base


class PendingAuthDetail(Base):
    """Pending authorization detail record.

    Each row represents a single pending authorization event tied
    to a summary account record in pending_auth_summary.
    """

    __tablename__ = "pending_auth_details"

    # Surrogate primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # PIC 9(11) - Account identifier (FK to pending_auth_summary)
    pa_acct_id = Column(
        BigInteger,
        ForeignKey("pending_auth_summary.pa_acct_id"),
        nullable=False,
    )

    # PIC X(6) - Authorization date (YYMMDD)
    pa_auth_date = Column(String(6))

    # PIC X(6) - Authorization time (HHMMSS)
    pa_auth_time = Column(String(6))

    # PIC X(16) - Card number
    pa_card_num = Column(String(16))

    # PIC X(4) - Authorization type
    pa_auth_type = Column(String(4))

    # PIC X(10) - Card expiry date
    pa_card_expiry_date = Column(String(10))

    # PIC X(4) - Message type
    pa_message_type = Column(String(4))

    # PIC X(10) - Message source
    pa_message_source = Column(String(10))

    # PIC X(6) - Authorization ID code
    pa_auth_id_code = Column(String(6))

    # PIC X(2) - Authorization response code
    pa_auth_resp_code = Column(String(2))

    # PIC X(20) - Authorization response reason
    pa_auth_resp_reason = Column(String(20))

    # PIC 9(3) - Processing code
    pa_processing_code = Column(Integer)

    # PIC S9(10)V99 - Transaction amount
    pa_transaction_amt = Column(Numeric(12, 2))

    # PIC S9(10)V99 - Approved amount
    pa_approved_amt = Column(Numeric(12, 2))

    # PIC X(4) - Merchant category code (MCC)
    pa_merchant_category_code = Column(String(4))

    # PIC X(3) - Acquirer country code
    pa_acqr_country_code = Column(String(3))

    # PIC 9(3) - Point-of-sale entry mode
    pa_pos_entry_mode = Column(SmallInteger)

    # PIC 9(9) - Merchant identifier
    pa_merchant_id = Column(String(15))

    # PIC X(50) - Merchant name
    pa_merchant_name = Column(String(50))

    # PIC X(50) - Merchant city
    pa_merchant_city = Column(String(50))

    # PIC X(2) - Merchant state
    pa_merchant_state = Column(String(2))

    # PIC X(10) - Merchant ZIP code
    pa_merchant_zip = Column(String(10))

    # PIC X(15) - Transaction identifier
    pa_transaction_id = Column(String(15))

    # PIC X(1) - Match status
    pa_match_status = Column(String(1))

    # PIC X(1) - Fraud flag
    pa_auth_fraud = Column(String(1))

    # PIC X(8) - Fraud report date (YYYYMMDD)
    pa_fraud_rpt_date = Column(String(8))

    def __repr__(self) -> str:
        return (
            f"<PendingAuthDetail(id={self.id}, "
            f"acct={self.pa_acct_id}, "
            f"card='{self.pa_card_num}', "
            f"amt={self.pa_transaction_amt})>"
        )
