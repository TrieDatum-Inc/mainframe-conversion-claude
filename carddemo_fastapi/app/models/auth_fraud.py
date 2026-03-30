"""Authorization and fraud detection model.

Derived from COBOL copybook: DALYTRAN / AUTH-FRAUD-DATA.
Maps the authorization record used by the CardDemo batch fraud-detection
program (CBACT04C) to evaluate and flag potentially fraudulent transactions.
"""

from sqlalchemy import Column, Date, DateTime, Integer, Numeric, SmallInteger, String

from app.database import Base


class AuthFraud(Base):
    """Authorization / fraud detection record.

    Corresponds to the DB2 / flat-file layout used by CBACT04C
    for daily authorization and fraud analysis, with a composite key
    of CARD-NUM + AUTH-TS.
    """

    __tablename__ = "auth_fraud"

    # PIC X(16) - Card number (part of composite PK)
    card_num = Column(String(16), primary_key=True)

    # Timestamp of the authorization (part of composite PK)
    auth_ts = Column(DateTime, primary_key=True)

    # PIC X(2) - Authorization type
    auth_type = Column(String(2))

    # PIC X(10) - Card expiry date
    card_expiry_date = Column(String(10))

    # PIC X(4) - Message type
    message_type = Column(String(4))

    # PIC X(10) - Message source
    message_source = Column(String(10))

    # PIC X(6) - Authorization ID code
    auth_id_code = Column(String(6))

    # PIC X(2) - Authorization response code
    auth_resp_code = Column(String(2))

    # PIC X(20) - Authorization response reason
    auth_resp_reason = Column(String(20))

    # PIC X(3) - Processing code
    processing_code = Column(String(3))

    # PIC S9(10)V99 - Transaction amount
    transaction_amt = Column(Numeric(12, 2))

    # PIC S9(10)V99 - Approved amount
    approved_amt = Column(Numeric(12, 2))

    # PIC X(4) - Merchant category code (MCC)
    merchant_category_code = Column(String(4))

    # PIC X(3) - Acquirer country code
    acqr_country_code = Column(String(3))

    # PIC 9(3) - Point-of-sale entry mode
    pos_entry_mode = Column(SmallInteger)

    # PIC 9(9) - Merchant identifier
    merchant_id = Column(Integer)

    # PIC X(50) - Merchant name
    merchant_name = Column(String(50))

    # PIC X(50) - Merchant city
    merchant_city = Column(String(50))

    # PIC X(2) - Merchant state
    merchant_state = Column(String(2))

    # PIC X(10) - Merchant ZIP code
    merchant_zip = Column(String(10))

    # PIC X(15) - Transaction identifier
    transaction_id = Column(String(15))

    # PIC X(1) - Match status
    match_status = Column(String(1))

    # PIC X(1) - Fraud flag (column name: auth_fraud)
    auth_fraud_flag = Column("auth_fraud", String(1))

    # Fraud report date
    fraud_rpt_date = Column(Date)

    # PIC 9(11) - Account identifier
    acct_id = Column(Numeric(11))

    # PIC 9(9) - Customer identifier
    cust_id = Column(Numeric(9))

    def __repr__(self) -> str:
        return (
            f"<AuthFraud(card='{self.card_num}', "
            f"ts={self.auth_ts}, "
            f"amt={self.transaction_amt}, "
            f"fraud='{self.auth_fraud_flag}')>"
        )
