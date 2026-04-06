# Technical Specification: CBTRN01C — Daily Transaction Validation

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBTRN01C |
| Source File | `app/cbl/CBTRN01C.cbl` |
| Type | Batch COBOL |

## 2. Purpose

CBTRN01C is the **first pass** of the daily transaction posting pipeline. It reads the DALYTRAN file sequentially and validates each transaction by looking up the card number in XREFFILE and reading the account from ACCTFILE. Records that cannot be resolved are logged to DISPLAY output. This program performs validation only — no records are written.

## 3. Files Accessed

| File DD | Direction | Access | Key | Layout |
|---------|-----------|--------|-----|--------|
| DALYTRAN | Input | Sequential | — | CVTRA06Y (350 bytes) |
| CUSTFILE | Input | KSDS random | FD-CUST-ID | CVCUS01Y (opened but not read in visible code) |
| XREFFILE | Input | KSDS random | FD-XREF-CARD-NUM | CVACT03Y |
| CARDFILE | Input | KSDS random | — | CVACT02Y (opened but not read) |
| ACCTFILE | Input | KSDS random | FD-ACCT-ID | CVACT01Y |
| TRANSACT | Input | KSDS random | — | CVTRA05Y (opened but not read) |

## 4. Validation Logic

```
For each DALYTRAN record:
  1. 2000-LOOKUP-XREF: READ XREFFILE by DALYTRAN-CARD-NUM
     → INVALID KEY: set WS-XREF-READ-STATUS = 4 (card not found)
  2. 3000-READ-ACCOUNT: READ ACCTFILE by XREF-ACCT-ID
     → INVALID KEY: set WS-ACCT-READ-STATUS = 4 (account not found)
  3. DISPLAY validation results to SYSOUT
```

## 5. Note

No output files are written — this is purely a validation and diagnostic program. CBTRN02C is the production posting program that writes rejected records to DALYREJS.

## 6. Copybooks Used

CVTRA06Y, CVCUS01Y, CVACT03Y, CVACT02Y, CVACT01Y, CVTRA05Y
