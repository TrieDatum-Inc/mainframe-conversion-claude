"""Customer model.

Derived from COBOL copybook: CUSTDATA (CUSTDAT.CPY).
Maps the customer master record used throughout the CardDemo application
for cardholder personal information and contact details.
"""

from sqlalchemy import Column, Integer, SmallInteger, String

from app.database import Base


class Customer(Base):
    """Customer master record.

    Corresponds to the VSAM KSDS file CUSTFILE keyed by CUST-ID
    and the DB2 table equivalent defined in CUSTDAT.CPY.
    """

    __tablename__ = "customers"

    # PIC 9(09) - Customer identifier
    cust_id = Column(Integer, primary_key=True)

    # PIC X(25) - Name fields
    cust_first_name = Column(String(25), nullable=False)
    cust_middle_name = Column(String(25))
    cust_last_name = Column(String(25), nullable=False)

    # PIC X(50) - Address lines
    cust_addr_line_1 = Column(String(50))
    cust_addr_line_2 = Column(String(50))
    cust_addr_line_3 = Column(String(50))

    # PIC X(2) - State code
    cust_addr_state_cd = Column(String(2))

    # PIC X(3) - Country code
    cust_addr_country_cd = Column(String(3))

    # PIC X(10) - ZIP / postal code
    cust_addr_zip = Column(String(10))

    # PIC X(15) - Phone numbers
    cust_phone_num_1 = Column(String(15))
    cust_phone_num_2 = Column(String(15))

    # PIC 9(09) - Social Security Number
    cust_ssn = Column(Integer)

    # PIC X(20) - Government-issued ID
    cust_govt_issued_id = Column(String(20))

    # PIC X(10) - Date of birth (YYYY-MM-DD)
    cust_dob_yyyymmdd = Column(String(10))

    # PIC X(10) - EFT account identifier
    cust_eft_account_id = Column(String(10))

    # PIC X(1) - Primary card holder indicator
    cust_pri_card_holder_ind = Column(String(1))

    # PIC 9(3) - FICO credit score
    cust_fico_credit_score = Column(SmallInteger)

    def __repr__(self) -> str:
        return (
            f"<Customer(cust_id={self.cust_id}, "
            f"name='{self.cust_first_name} {self.cust_last_name}')>"
        )
