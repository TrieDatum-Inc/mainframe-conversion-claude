"""
Pydantic v2 schemas for the accounts module.

COBOL origin: COACTVWC (Account View) and COACTUPC (Account Update).
  BMS Mapset COACTVW (map CACTVWA) — all fields ASKIP/output-only except ACCTSID
  BMS Mapset COACTUP (map CACTUPA) — all data fields UNPROT/editable

Key security constraint preserved:
  - SSN is NEVER returned unmasked. AccountViewResponse.customer.ssn_masked
    always shows "***-**-XXXX" (last 4 digits only).
    COBOL stored CUST-SSN as plain text; this API prevents full exposure.
"""

from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Response models (maps COACTVWC display screen — all ASKIP fields)
# ---------------------------------------------------------------------------


class CustomerDetailResponse(BaseModel):
    """
    Customer detail section of the Account View screen.

    COBOL origin: COACTVWC 9000-READ-ACCT paragraph — CUSTDAT read via
    CXACAIX alternate index, then EXEC CICS READ DATASET('CUSTDAT').
    Maps BMS screen rows 11-20 of COACTVW (all ASKIP/output-only).
    """

    customer_id: int
    # SECURITY: SSN always masked — last 4 digits only.
    # Replaces ACSTSSN BMS field (12 chars, single field in view).
    # Full SSN NEVER appears in any API response.
    ssn_masked: str = Field(
        ...,
        description="SSN displayed as ***-**-XXXX — last 4 digits only. Never unmasked.",
    )
    date_of_birth: Optional[date] = None        # ACSTDOB single 10-char field
    fico_score: Optional[int] = None             # ACSTFCO 3-digit
    first_name: str                              # ACSFNAM X(25)
    middle_name: Optional[str] = None            # ACSMNAM X(25)
    last_name: str                               # ACSLNAM X(25)
    address_line_1: Optional[str] = None         # ACSADL1 X(50)
    address_line_2: Optional[str] = None         # ACSADL2 X(50)
    city: Optional[str] = None                   # ACSCITY X(50)
    state_code: Optional[str] = None             # ACSSTTE X(2)
    zip_code: Optional[str] = None               # ACSZIPC X(5–10)
    country_code: Optional[str] = None           # ACSCTRY X(3)
    phone_1: Optional[str] = None                # ACSPHN1 single 13-char field
    phone_2: Optional[str] = None                # ACSPHN2
    government_id_ref: Optional[str] = None      # ACSGOVT X(20)
    eft_account_id: Optional[str] = None         # ACSEFTC X(10)
    primary_card_holder: str                     # ACSPFLG X(1) Y/N


class AccountViewResponse(BaseModel):
    """
    Full account view response.

    COBOL origin: COACTVWC — combines ACCTDAT record (account section)
    and CUSTDAT record (customer section) into a single display screen.
    Maps COACTVW BMS map rows 4-20.

    Financial amounts: PICOUT='+ZZZ,ZZZ,ZZZ.99' in BMS → Decimal in JSON.
    Frontend should format as signed currency: +$X,XXX,XXX.XX / -$X,XXX,XXX.XX.
    """

    account_id: int                             # ACCTSID 11-digit
    active_status: str                          # ACSTTUS Y/N
    open_date: Optional[date] = None            # ADTOPEN single 10-char field
    expiration_date: Optional[date] = None      # AEXPDT
    reissue_date: Optional[date] = None         # AREISDT
    credit_limit: Decimal                       # ACRDLIM PICOUT='+ZZZ,ZZZ,ZZZ.99'
    cash_credit_limit: Decimal                  # ACSHLIM
    current_balance: Decimal                    # ACURBAL
    curr_cycle_credit: Decimal                  # ACRCYCR
    curr_cycle_debit: Decimal                   # ACRCYDB
    group_id: Optional[str] = None              # AADDGRP X(10)
    customer: CustomerDetailResponse            # Customer detail rows 11-20


# ---------------------------------------------------------------------------
# Update request models (maps COACTUPC — all fields UNPROT/editable)
# ---------------------------------------------------------------------------


class CustomerUpdateRequest(BaseModel):
    """
    Customer fields editable on the Account Update screen.

    COBOL origin: COACTUPC 2000-PROCESS-INPUTS — validates customer-section
    fields from COACTUP BMS map (rows 12-20, all UNPROT).
    """

    customer_id: int = Field(
        ...,
        description="ACSTNUM — 9-digit customer identifier",
    )
    # Alpha-only fields — maps COACTUPC WS-EDIT-ALPHA-ONLY-FLAGS validation
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=25,
        description="ACSFNAM X(25) — alpha/space/hyphen/apostrophe only",
    )
    middle_name: Optional[str] = Field(
        None,
        max_length=25,
        description="ACSMNAM X(25)",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=25,
        description="ACSLNAM X(25) — alpha/space/hyphen/apostrophe only",
    )
    address_line_1: Optional[str] = Field(None, max_length=50)   # ACSADL1
    address_line_2: Optional[str] = Field(None, max_length=50)   # ACSADL2
    city: Optional[str] = Field(None, max_length=50)             # ACSCITY
    state_code: Optional[str] = Field(None, max_length=2)        # ACSSTTE
    zip_code: Optional[str] = Field(None, max_length=10)         # ACSZIPC
    country_code: Optional[str] = Field(None, max_length=3)      # ACSCTRY
    # Phone format: NNN-NNN-NNNN (maps COACTUPC WS-EDIT-US-PHONE-NUM validation)
    phone_1: Optional[str] = Field(
        None,
        pattern=r"^\d{3}-\d{3}-\d{4}$",
        description="ACSPH1A/B/C combined — NNN-NNN-NNNN format",
    )
    phone_2: Optional[str] = Field(
        None,
        pattern=r"^\d{3}-\d{3}-\d{4}$",
        description="ACSPH2A/B/C combined — NNN-NNN-NNNN format",
    )
    # SSN in three separate parts (maps ACTSSN1/ACTSSN2/ACTSSN3 BMS split fields)
    ssn_part1: str = Field(
        ...,
        pattern=r"^\d{3}$",
        description="ACTSSN1 — 3-digit area number; cannot be 000, 666, or 900-999",
    )
    ssn_part2: str = Field(
        ...,
        pattern=r"^\d{2}$",
        description="ACTSSN2 — 2-digit group number",
    )
    ssn_part3: str = Field(
        ...,
        pattern=r"^\d{4}$",
        description="ACTSSN3 — 4-digit serial number",
    )
    date_of_birth: date = Field(
        ...,
        description="DOBYEAR/DOBMON/DOBDAY combined — CCYYMMDD in COBOL",
    )
    fico_score: Optional[int] = Field(
        None,
        ge=300,
        le=850,
        description="ACSTFCO 9(3) — FICO credit score; valid range 300-850",
    )
    government_id_ref: Optional[str] = Field(None, max_length=20)  # ACSGOVT
    eft_account_id: Optional[str] = Field(None, max_length=10)     # ACSEFTC
    primary_card_holder: Literal["Y", "N"] = Field(
        ...,
        description="ACSPFLG X(1) — primary card holder indicator",
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def alpha_only(cls, v: str) -> str:
        """
        Validate alpha-only name fields.

        COBOL origin: COACTUPC 2000-PROCESS-INPUTS — WS-EDIT-ALPHA-ONLY-FLAGS.
        INSPECT CONVERTING (ALPHA chars) equivalent: only letters, spaces,
        hyphens, and apostrophes are accepted.
        """
        if v and not all(c.isalpha() or c in (" ", "-", "'") for c in v):
            raise ValueError(
                "Name fields must contain letters, spaces, hyphens, or apostrophes only"
            )
        return v

    @field_validator("middle_name")
    @classmethod
    def middle_name_alpha_only(cls, v: Optional[str]) -> Optional[str]:
        """Apply alpha-only check to optional middle name."""
        if v and not all(c.isalpha() or c in (" ", "-", "'") for c in v):
            raise ValueError(
                "Middle name must contain letters, spaces, hyphens, or apostrophes only"
            )
        return v

    @model_validator(mode="after")
    def validate_ssn_part1(self) -> "CustomerUpdateRequest":
        """
        Validate SSN area number (part 1).

        COBOL origin: COACTUPC INVALID-SSN-PART1 88-level condition:
          88 INVALID-SSN-PART1 VALUES '000' '666' THRU '999' (900-999 range).
        IRS/SSA rule: area code 000, 666, and 900-999 are never validly assigned.
        """
        p1 = self.ssn_part1
        if p1 in ("000", "666") or ("900" <= p1 <= "999"):
            raise ValueError(
                "SSN area number (part 1) is invalid: cannot be 000, 666, or 900-999"
            )
        return self


class AccountUpdateRequest(BaseModel):
    """
    Account update request body.

    COBOL origin: COACTUPC MAIN-PARA (CDEMO-PGM-REENTER + ENTER/PF5 path)
    → 2000-PROCESS-INPUTS: all 15+ field-level validations.
    → 9000-UPDATE-ACCOUNT: conditional REWRITE gated by WS-DATACHANGED-FLAG.

    All validations from COACTUPC are preserved:
      - Signed number validation (WS-EDIT-SIGNED-NUMBER-9V2-X) → Decimal ge=0
      - Y/N flag validation (WS-EDIT-YES-NO, FLG-YES-NO-ISVALID) → Literal['Y','N']
      - Date validation (CSUTLDWY) → Pydantic date type
      - Alpha-only validation (WS-EDIT-ALPHA-ONLY-FLAGS) → field_validator
      - SSN part1 validation (INVALID-SSN-PART1) → model_validator
      - Cash limit vs credit limit (implicit, enforced by DB constraint too) → model_validator
      - FICO range 300-850 (WS-EDIT-FICO-SCORE-FLGS) → Field(ge=300, le=850)
      - Phone format NNN-NNN-NNNN (WS-EDIT-US-PHONE-NUM) → pattern validator
    """

    active_status: Literal["Y", "N"] = Field(
        ...,
        description="ACSTTUS X(1) — account active flag",
    )
    open_date: date = Field(
        ...,
        description="OPNYEAR/OPNMON/OPNDAY combined — account open date",
    )
    expiration_date: date = Field(
        ...,
        description="EXPYEAR/EXPMON/EXPDAY combined",
    )
    reissue_date: date = Field(
        ...,
        description="RISYEAR/RISMON/RISDAY combined",
    )
    credit_limit: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="ACRDLIM X(15) — FSET,UNPROT; signed numeric >= 0",
    )
    cash_credit_limit: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="ACSHLIM X(15) — must be >= 0 and <= credit_limit",
    )
    current_balance: Decimal = Field(
        ...,
        description="ACURBAL X(15) — signed numeric; can be negative",
    )
    curr_cycle_credit: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="ACRCYCR X(15)",
    )
    curr_cycle_debit: Decimal = Field(
        ...,
        ge=Decimal("0"),
        description="ACRCYDB X(15)",
    )
    group_id: Optional[str] = Field(
        None,
        max_length=10,
        description="AADDGRP X(10)",
    )
    customer: CustomerUpdateRequest

    @model_validator(mode="after")
    def validate_cash_limit_lte_credit(self) -> "AccountUpdateRequest":
        """
        Enforce cash_credit_limit <= credit_limit.

        COBOL origin: COACTUPC validation — WS-EDIT-SIGNED-NUMBER-9V2-X
        applied to both limits; implicit rule that cash <= credit.
        Also enforced by DB CHECK constraint chk_accounts_cash_lte_credit.
        Checking here gives a descriptive 422 before hitting the DB.
        """
        if self.cash_credit_limit > self.credit_limit:
            raise ValueError(
                "Cash credit limit cannot exceed credit limit"
            )
        return self
