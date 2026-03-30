"""Account schemas matching COBOL CVACT01Y.cpy, CVCUS01Y.cpy, and COACTVWC screen.

- AccountView: joined account + customer fields as displayed by COACTVWC
- AccountUpdate: partial update with all fields Optional, matching COACTUP screen
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class AccountView(BaseModel):
    """Account view with joined customer fields, matching COACTVWC output.

    Account fields from CVACT01Y.cpy ACCOUNT-RECORD (RECLN 300).
    Customer fields from CVCUS01Y.cpy CUSTOMER-RECORD (RECLN 500).
    """

    # --- Account fields (CVACT01Y.cpy) ---
    acct_id: int = Field(..., description="Account ID (ACCT-ID PIC 9(11))")
    acct_active_status: str = Field(
        ..., max_length=1, description="Active status Y/N (ACCT-ACTIVE-STATUS PIC X(01))"
    )
    acct_curr_bal: Decimal = Field(
        ..., description="Current balance (ACCT-CURR-BAL PIC S9(10)V99)"
    )
    acct_credit_limit: Decimal = Field(
        ..., description="Credit limit (ACCT-CREDIT-LIMIT PIC S9(10)V99)"
    )
    acct_cash_credit_limit: Decimal = Field(
        ..., description="Cash credit limit (ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99)"
    )
    acct_open_date: str = Field(
        ..., max_length=10, description="Open date (ACCT-OPEN-DATE PIC X(10))"
    )
    acct_expiration_date: str = Field(
        ..., max_length=10, description="Expiration date (ACCT-EXPIRAION-DATE PIC X(10))"
    )
    acct_reissue_date: Optional[str] = Field(
        ..., max_length=10, description="Reissue date (ACCT-REISSUE-DATE PIC X(10))"
    )
    acct_curr_cyc_credit: Decimal = Field(
        ..., description="Current cycle credit (ACCT-CURR-CYC-CREDIT PIC S9(10)V99)"
    )
    acct_curr_cyc_debit: Decimal = Field(
        ..., description="Current cycle debit (ACCT-CURR-CYC-DEBIT PIC S9(10)V99)"
    )
    acct_addr_zip: str = Field(
        ..., max_length=10, description="Account ZIP code (ACCT-ADDR-ZIP PIC X(10))"
    )
    acct_group_id: str = Field(
        ..., max_length=10, description="Account group ID (ACCT-GROUP-ID PIC X(10))"
    )

    # --- Customer fields (CVCUS01Y.cpy) --- Optional since xref may not exist
    cust_id: Optional[int] = Field(None, description="Customer ID (CUST-ID PIC 9(09))")
    cust_first_name: Optional[str] = Field(
        None, max_length=25, description="First name (CUST-FIRST-NAME PIC X(25))"
    )
    cust_middle_name: Optional[str] = Field(
        None, max_length=25, description="Middle name (CUST-MIDDLE-NAME PIC X(25))"
    )
    cust_last_name: Optional[str] = Field(
        None, max_length=25, description="Last name (CUST-LAST-NAME PIC X(25))"
    )
    cust_addr_line_1: Optional[str] = Field(
        None, max_length=50, description="Address line 1 (CUST-ADDR-LINE-1 PIC X(50))"
    )
    cust_addr_line_2: Optional[str] = Field(
        None, max_length=50, description="Address line 2 (CUST-ADDR-LINE-2 PIC X(50))"
    )
    cust_addr_line_3: Optional[str] = Field(
        None, max_length=50, description="Address line 3 (CUST-ADDR-LINE-3 PIC X(50))"
    )
    cust_addr_state_cd: Optional[str] = Field(
        None, max_length=2, description="State code (CUST-ADDR-STATE-CD PIC X(02))"
    )
    cust_addr_country_cd: Optional[str] = Field(
        None, max_length=3, description="Country code (CUST-ADDR-COUNTRY-CD PIC X(03))"
    )
    cust_addr_zip: Optional[str] = Field(
        None, max_length=10, description="Customer ZIP code (CUST-ADDR-ZIP PIC X(10))"
    )
    cust_phone_num_1: Optional[str] = Field(
        None, max_length=15, description="Phone number 1 (CUST-PHONE-NUM-1 PIC X(15))"
    )
    cust_phone_num_2: Optional[str] = Field(
        None, max_length=15, description="Phone number 2 (CUST-PHONE-NUM-2 PIC X(15))"
    )
    cust_ssn: Optional[int] = Field(None, description="SSN (CUST-SSN PIC 9(09))")
    cust_govt_issued_id: Optional[str] = Field(
        None, max_length=20, description="Government ID (CUST-GOVT-ISSUED-ID PIC X(20))"
    )
    cust_dob_yyyymmdd: Optional[str] = Field(
        None, max_length=10, description="Date of birth (CUST-DOB-YYYY-MM-DD PIC X(10))"
    )
    cust_eft_account_id: Optional[str] = Field(
        None, max_length=10, description="EFT account ID (CUST-EFT-ACCOUNT-ID PIC X(10))"
    )
    cust_pri_card_holder_ind: Optional[str] = Field(
        None,
        max_length=1,
        description="Primary cardholder indicator (CUST-PRI-CARD-HOLDER-IND PIC X(01))",
    )
    cust_fico_credit_score: Optional[int] = Field(
        None, description="FICO credit score (CUST-FICO-CREDIT-SCORE PIC 9(03))"
    )


class AccountUpdate(BaseModel):
    """Account update with all fields Optional for partial update.

    Matches COACTUP screen input fields. Only non-None fields are applied.
    """

    # --- Account fields ---
    acct_active_status: Optional[str] = Field(
        None, max_length=1, description="Active status Y/N"
    )
    acct_credit_limit: Optional[Decimal] = Field(None, description="Credit limit")
    acct_cash_credit_limit: Optional[Decimal] = Field(None, description="Cash credit limit")
    acct_open_date: Optional[str] = Field(None, max_length=10, description="Open date")
    acct_expiration_date: Optional[str] = Field(
        None, max_length=10, description="Expiration date"
    )
    acct_reissue_date: Optional[str] = Field(None, max_length=10, description="Reissue date")

    # --- Customer fields ---
    cust_first_name: Optional[str] = Field(None, max_length=25, description="First name")
    cust_middle_name: Optional[str] = Field(None, max_length=25, description="Middle name")
    cust_last_name: Optional[str] = Field(None, max_length=25, description="Last name")
    cust_addr_line_1: Optional[str] = Field(None, max_length=50, description="Address line 1")
    cust_addr_line_2: Optional[str] = Field(None, max_length=50, description="Address line 2")
    cust_addr_line_3: Optional[str] = Field(None, max_length=50, description="Address line 3")
    cust_addr_state_cd: Optional[str] = Field(None, max_length=2, description="State code")
    cust_addr_country_cd: Optional[str] = Field(
        None, max_length=3, description="Country code"
    )
    cust_addr_zip: Optional[str] = Field(None, max_length=10, description="Customer ZIP")
    cust_phone_num_1: Optional[str] = Field(None, max_length=15, description="Phone 1")
    cust_phone_num_2: Optional[str] = Field(None, max_length=15, description="Phone 2")
    cust_ssn: Optional[int] = Field(None, description="SSN")
    cust_govt_issued_id: Optional[str] = Field(
        None, max_length=20, description="Government ID"
    )
    cust_dob_yyyymmdd: Optional[str] = Field(
        None, max_length=10, description="Date of birth"
    )
    cust_eft_account_id: Optional[str] = Field(
        None, max_length=10, description="EFT account ID"
    )
    cust_pri_card_holder_ind: Optional[str] = Field(
        None, max_length=1, description="Primary cardholder indicator"
    )
    cust_fico_credit_score: Optional[int] = Field(None, description="FICO credit score")
