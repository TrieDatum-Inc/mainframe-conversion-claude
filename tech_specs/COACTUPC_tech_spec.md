# Technical Specification: COACTUPC — Update Account Details

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COACTUPC |
| Source File | `app/cbl/COACTUPC.cbl` |
| Type | CICS Online |
| Transaction ID | CAUP |
| BMS Mapset | COACTUP |
| BMS Map | CACTUPA |
| Lines of Code | ~4,400 (largest program in the codebase) |

## 2. Purpose

COACTUPC provides a **full account and customer edit form**. It mirrors the COACTVWC layout but all fields are editable (UNPROT). It includes extensive inline input validation for phone numbers, SSN, dates, state codes, zip codes, and numeric financial fields.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| CVCRD01Y | CC-WORK-AREAS (navigation state) |
| CSLKPCDY | Validation lookup tables (phone area codes, state codes, state-zip combos) |
| COCOM01Y | CARDDEMO-COMMAREA |
| COACTUP | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y, CSMSG02Y | Standard infrastructure |
| CSUSR01Y | User record layout |
| CVACT01Y | ACCOUNT-RECORD layout |
| CVACT03Y | CARD-XREF-RECORD layout |
| CVCUS01Y | CUSTOMER-RECORD layout |
| CSSETATY | Screen error highlighting fragment (used 39 times with REPLACING) |
| CSUTLDPY | Date validation procedure paragraphs |
| CSUTLDWY | Date validation working storage |
| CSSTRPFY | PF-key storage paragraph |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| ACCTDAT | Update | READ with UPDATE, REWRITE | ACCT-ID 9(11) |
| CUSTDAT | Update | READ with UPDATE, REWRITE | CUST-ID 9(9) |
| CXACAIX | Read | READ by account | XREF-ACCT-ID 9(11) |
| CARDAIX | Browse | STARTBR, READNEXT, ENDBR | ACCT-ID |

## 5. Screen Fields

Same layout as COACTVWC but all fields are UNPROT (editable). Key differences:
- SSN split into 3 fields: ACTSSN1(3), ACTSSN2(2), ACTSSN3(4) with literal hyphens
- Date fields split into year/month/day subfields (e.g., OPNYEAR(4), OPNMON(2), OPNDAY(2))
- Phone numbers split: ACSPH1A(3), ACSPH1B(3), ACSPH1C(4)

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Validate/process |
| PF3 | Exit to menu |
| PF5 | Save (initially hidden, dynamically revealed) |
| PF12 | Cancel |

## 6. Validation Rules

| Field | Validation |
|-------|-----------|
| Phone numbers | (xxx)xxx-xxxx format, area code validated against CSLKPCDY NANP table |
| SSN | xxx-xx-xxxx format |
| State code | Validated against CSLKPCDY (50 states + DC + territories) |
| Zip code | State-zip cross-validation via CSLKPCDY |
| Dates | Validated via CSUTLDPY/CSUTLDWY paragraphs (calls CSUTLDTC) |
| Financial fields | Signed numeric validation |

## 7. Attribute Management

Uses **39 instances** of `COPY CSSETATY REPLACING` — each generates field-attribute-setting code for a different screen field, controlling BRT/DIM/PROT/UNPROT/RED highlighting for validation errors.

## 8. Program Flow

```
1. ENTER: Accept account ID, READ ACCTDAT and CUSTDAT
2. Display current values in editable fields
3. On re-entry: validate each field inline
4. PF5 (Save):
   a. READ ACCTDAT with UPDATE
   b. READ CUSTDAT with UPDATE
   c. REWRITE both records with new values
5. PF12: Cancel, return to menu
```

## 9. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COCRDLIC | XCTL | Navigate to card list |
| COCRDUPC | XCTL | Navigate to card update |
| COCRDSLC | XCTL | Navigate to card detail |
| COMEN01C | XCTL | PF3/PF12 return |
