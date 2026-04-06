"""
Pydantic schemas for Account and Customer request/response DTOs.

COBOL origin: COACTVWC (view) and COACTUPC (update).
BMS maps: CACTVWA (view) and CACTUPA (update).

Key mapping decisions:
  - Split year/month/day BMS date fields → single Python date fields
  - Split SSN parts (ACTSSN1/2/3) → separate string fields in request for validation
  - Split phone parts (ACSPH1A/B/C) → combined phone string in storage
  - Currency fields use Decimal to preserve NUMERIC(12,2) precision
  - SSN returned masked (***-**-XXXX) in view; never returned as plain text
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class CustomerDetailResponse(BaseModel):
    """
    Read-only customer data returned within AccountViewResponse.

    Maps rows 11-20 of CACTVWA BMS map (all ASKIP — read-only fields).
    SSN is masked per PCI-DSS guidance: first 5 digits replaced with asterisks.
    """

    customer_id: int = Field(description="ACSTNUM field on CACTVWA map — CUST-ID 9(9)")
    ssn_masked: str = Field(
        description="ACSTSSN — SSN masked as ***-**-XXXX; never expose plain SSN"
    )
    date_of_birth: Optional[date] = Field(
        None, description="ACSTDOB — CUST-DOB-YYYY-MM-DD"
    )
    fico_score: Optional[int] = Field(
        None, description="ACSTFCO — CUST-FICO-CREDIT-SCORE 9(3); range 300-850"
    )
    first_name: str = Field(description="ACSFNAM — CUST-FIRST-NAME X(25)")
    middle_name: Optional[str] = Field(None, description="ACSMNAM — CUST-MIDDLE-NAME X(25)")
    last_name: str = Field(description="ACSLNAM — CUST-LAST-NAME X(25)")
    address_line_1: Optional[str] = Field(None, description="ACSADL1 — CUST-ADDR-LINE-1 X(50)")
    address_line_2: Optional[str] = Field(None, description="ACSADL2 — CUST-ADDR-LINE-2 X(50)")
    city: Optional[str] = Field(None, description="ACSCITY — CUST-ADDR-CITY X(50)")
    state_code: Optional[str] = Field(None, description="ACSSTTE — CUST-ADDR-STATE-CD X(2)")
    zip_code: Optional[str] = Field(None, description="ACSZIPC — CUST-ADDR-ZIP X(10)")
    country_code: Optional[str] = Field(None, description="ACSCTRY — CUST-ADDR-COUNTRY-CD X(3)")
    phone_1: Optional[str] = Field(
        None, description="ACSPHN1 — CUST-PHONE-NUM-1 X(15); single field in view"
    )
    phone_2: Optional[str] = Field(None, description="ACSPHN2 — CUST-PHONE-NUM-2 X(15)")
    government_id_ref: Optional[str] = Field(
        None, description="ACSGOVT — CUST-GOVT-ISSUED-ID X(20)"
    )
    eft_account_id: Optional[str] = Field(
        None, description="ACSEFTC — CUST-EFT-ACCOUNT-ID X(10)"
    )
    primary_card_holder: str = Field(
        description="ACSPFLG — CUST-PRI-CARD-HOLDER-IND X(1); Y/N"
    )

    model_config = {"from_attributes": True}


class AccountViewResponse(BaseModel):
    """
    Full account view response — maps all CACTVWA ASKIP display fields.

    COACTVWC paragraph READ-ACCT-BY-ACCT-ID → READ-CUST-BY-CUST-ID → READ-CARD-BY-ACCT-AIX
    combines three data sources: ACCTDAT + CUSTDAT + CARDAIX.
    Currency amounts formatted with PICOUT='+ZZZ,ZZZ,ZZZ.99' equivalent in the frontend.
    """

    account_id: int = Field(description="ACCTSID — ACCT-ID 9(11); 11-digit primary key")
    active_status: str = Field(description="ACSTTUS — ACCT-ACTIVE-STATUS X(1); Y/N")
    open_date: Optional[date] = Field(None, description="ADTOPEN — ACCT-OPEN-DATE")
    expiration_date: Optional[date] = Field(None, description="AEXPDT — ACCT-EXPIRAION-DATE")
    reissue_date: Optional[date] = Field(None, description="AREISDT — ACCT-REISSUE-DATE")
    credit_limit: Decimal = Field(description="ACRDLIM — PICOUT='+ZZZ,ZZZ,ZZZ.99'")
    cash_credit_limit: Decimal = Field(description="ACSHLIM — cash portion of credit limit")
    current_balance: Decimal = Field(description="ACURBAL — current outstanding balance")
    curr_cycle_credit: Decimal = Field(description="ACRCYCR — credits this cycle")
    curr_cycle_debit: Decimal = Field(description="ACRCYDB — debits this cycle")
    group_id: Optional[str] = Field(None, description="AADDGRP — ACCT-GROUP-ID X(10)")
    updated_at: datetime = Field(
        description="Used as optimistic_lock_version for updates — replaces WS-DATACHANGED-FLAG"
    )
    customer: CustomerDetailResponse

    model_config = {"from_attributes": True}


class CustomerUpdateRequest(BaseModel):
    """
    Customer fields in account update request.

    Maps CACTUPA BMS map — customer section (rows 11-20 of update screen).
    SSN is split into three parts matching ACTSSN1/ACTSSN2/ACTSSN3 BMS fields.
    Phone is split into three parts matching ACSPH1A/B/C BMS fields.

    All validations from COACTUPC VALIDATE-INPUT-FIELDS are preserved here.
    """

    customer_id: int = Field(description="ACSTNUM — read-only customer identifier")

    # Name fields — alpha-only validated (INSPECT CONVERTING equivalent in COACTUPC)
    first_name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=25,
            pattern=r"^[A-Za-z\s\-']+$",
            description="ACSFNAM — alpha/hyphen/apostrophe only; INSPECT CONVERTING validated",
        ),
    ]
    middle_name: Annotated[
        Optional[str],
        Field(
            default=None,
            max_length=25,
            pattern=r"^[A-Za-z\s\-']*$",
        ),
    ] = None
    last_name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=25,
            pattern=r"^[A-Za-z\s\-']+$",
            description="ACSLNAM — alpha/hyphen/apostrophe only",
        ),
    ]

    # Address fields
    address_line_1: Optional[str] = Field(None, max_length=50)
    address_line_2: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    state_code: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country_code: Optional[str] = Field(None, max_length=3)

    # Phone — split into parts matching ACSPH1A (3-digit area) / B (3-digit exchange) / C (4-digit)
    phone_1: Optional[str] = Field(
        None,
        pattern=r"^\d{3}-\d{3}-\d{4}$",
        description="ACSPH1A/B/C combined as NNN-NNN-NNNN",
    )
    phone_2: Optional[str] = Field(None, pattern=r"^\d{3}-\d{3}-\d{4}$")

    # SSN — three separate parts matching ACTSSN1 (3-digit) / ACTSSN2 (2-digit) / ACTSSN3 (4-digit)
    # COACTUPC SSN validation: part1 not 000 or 666, not in range 900-999
    ssn_part1: str = Field(
        ...,
        pattern=r"^\d{3}$",
        description="ACTSSN1 — 3-digit SSN part; validated: not 000, not 666, not 900-999",
    )
    ssn_part2: str = Field(..., pattern=r"^\d{2}$", description="ACTSSN2 — 2-digit SSN part")
    ssn_part3: str = Field(..., pattern=r"^\d{4}$", description="ACTSSN3 — 4-digit SSN part")

    date_of_birth: date = Field(description="DOBYEAR/DOBMON/DOBDAY combined → single date")
    fico_score: Optional[int] = Field(
        None, ge=300, le=850, description="ACSTFCO — CUST-FICO-CREDIT-SCORE; CHECK 300-850"
    )
    government_id_ref: Optional[str] = Field(None, max_length=20)
    eft_account_id: Optional[str] = Field(None, max_length=10)
    primary_card_holder: Literal["Y", "N"] = Field(
        description="ACSPFLG — CUST-PRI-CARD-HOLDER-IND; must be Y or N"
    )

    @model_validator(mode="after")
    def validate_ssn_part1(self) -> "CustomerUpdateRequest":
        """
        Replicates COACTUPC SSN validation:
          IF ACTSSN1 = '000' → error
          IF ACTSSN1 = '666' → error
          IF ACTSSN1 >= '900' AND ACTSSN1 <= '999' → error
        """
        part1 = self.ssn_part1
        part1_int = int(part1)
        if part1_int == 0:
            raise ValueError("SSN part 1 cannot be 000")
        if part1_int == 666:
            raise ValueError("SSN part 1 cannot be 666")
        if 900 <= part1_int <= 999:
            raise ValueError("SSN part 1 cannot be in range 900-999")
        return self


class AccountUpdateRequest(BaseModel):
    """
    Account update request — maps CACTUPA BMS editable fields.

    All 15+ validations from COACTUPC VALIDATE-INPUT-FIELDS are replicated here
    and in account_service.py. Pydantic handles field-level type/range validation;
    service layer handles cross-field validation (cash_limit <= credit_limit, etc.).
    """

    active_status: Literal["Y", "N"] = Field(
        description="ACSTTUS — ACCT-ACTIVE-STATUS; must be Y or N"
    )
    open_date: date = Field(
        description="OPNYEAR/OPNMON/OPNDAY combined → single date; validated via CSUTLDTC equivalent"
    )
    expiration_date: date = Field(
        description="EXPYEAR/EXPMON/EXPDAY combined → single date; validated as future date"
    )
    reissue_date: date = Field(description="RISYEAR/RISMON/RISDAY combined → single date")
    credit_limit: Decimal = Field(
        ..., ge=0, decimal_places=2, description="ACRDLIM — ACCT-CREDIT-LIMIT; must be >= 0"
    )
    cash_credit_limit: Decimal = Field(
        ...,
        ge=0,
        decimal_places=2,
        description="ACSHLIM — ACCT-CASH-CREDIT-LIMIT; must be >= 0 and <= credit_limit",
    )
    current_balance: Decimal = Field(
        ..., decimal_places=2, description="ACURBAL — ACCT-CURR-BAL; signed numeric"
    )
    curr_cycle_credit: Decimal = Field(
        ..., ge=0, decimal_places=2, description="ACRCYCR — ACCT-CURR-CYC-CREDIT"
    )
    curr_cycle_debit: Decimal = Field(
        ..., ge=0, decimal_places=2, description="ACRCYDB — ACCT-CURR-CYC-DEBIT"
    )
    group_id: Optional[str] = Field(
        None, max_length=10, description="AADDGRP — ACCT-GROUP-ID X(10)"
    )
    customer: CustomerUpdateRequest

    @model_validator(mode="after")
    def validate_cash_lte_credit(self) -> "AccountUpdateRequest":
        """
        Replicates COACTUPC: ACCT-CASH-CREDIT-LIMIT must not exceed ACCT-CREDIT-LIMIT.
        """
        if self.cash_credit_limit > self.credit_limit:
            raise ValueError("cash_credit_limit must not exceed credit_limit")
        return self
