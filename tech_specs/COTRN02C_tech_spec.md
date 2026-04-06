# Technical Specification: COTRN02C — Add Transaction

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COTRN02C |
| Source File | `app/cbl/COTRN02C.cbl` |
| Type | CICS Online |
| Transaction ID | CT02 |
| BMS Mapset | COTRN02 |
| BMS Map | COTRN2A |

## 2. Purpose

COTRN02C provides a **data entry form** for creating a new transaction record. It accepts either Account ID or Card Number (resolving the other via cross-reference), validates all fields including amount format and dates, auto-generates a sequential transaction ID, and writes the new record to TRANSACT.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA (extended with CDEMO-CT02-INFO) |
| COTRN02 | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y | Standard infrastructure |
| CVTRA05Y | TRAN-RECORD layout |
| CVACT01Y | ACCOUNT-RECORD layout |
| CVACT03Y | CARD-XREF-RECORD layout |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| TRANSACT | Browse + Write | STARTBR HIGH-VALUES, READPREV, ENDBR, WRITE | TRAN-ID X(16) |
| CCXREF | Read | READ by card number | XREF-CARD-NUM X(16) |
| CXACAIX | Read | READ by account ID (alternate index) | XREF-ACCT-ID 9(11) |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| ACTIDIN | 11 | Account number (cursor initial) |
| CARDNIN | 16 | Card number (alternative to account) |
| TTYPCD | 2 | Transaction type code |
| TCATCD | 4 | Category code |
| TRNSRC | 10 | Source |
| TDESC | 60 | Description |
| TRNAMT | 12 | Amount (format: -99999999.99) |
| TORIGDT | 10 | Original date (YYYY-MM-DD) |
| TPROCDT | 10 | Processing date (YYYY-MM-DD) |
| MID | 9 | Merchant ID (must be numeric) |
| MNAME | 30 | Merchant name |
| MCITY | 25 | Merchant city |
| MZIP | 10 | Merchant zip |
| CONFIRM | 1 | Y/N confirmation before write |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Validate and submit (if CONFIRM=Y) |
| PF3 | Back to calling program |
| PF4 | Clear all fields |
| PF5 | Copy last transaction into fields |

## 6. Program Flow

```
1. On ENTER:
   a. Validate Account ID or Card Number provided
   b. If Account ID: READ CXACAIX to get card number
   c. If Card Number: READ CCXREF to get account ID
   d. Validate amount format (sign + 8 digits + decimal + 2 digits)
   e. Validate dates via CALL CSUTLDTC with format 'YYYY-MM-DD'
   f. Validate Merchant ID is numeric
   g. If CONFIRM = 'Y':
      - STARTBR HIGH-VALUES on TRANSACT
      - READPREV to get last (highest) TRAN-ID
      - ENDBR
      - Add 1 to get new TRAN-ID
      - Build TRAN-RECORD from screen fields
      - WRITE to TRANSACT
   h. If CONFIRM blank or 'N': prompt only

2. On PF5 (Copy Last Transaction):
   → Read most recent TRANSACT record for this card/account
   → Pre-fill all data fields on screen
```

## 7. External Program Calls

| Target | Method | Purpose |
|--------|--------|---------|
| CSUTLDTC | CALL | Date validation (CEEDAYS wrapper) for TORIGDT and TPROCDT |

## 8. Transaction ID Generation

Sequential max+1 approach:
1. STARTBR with HIGH-VALUES key
2. READPREV to get the last record
3. ENDBR
4. Increment by 1

**Warning**: No locking on this operation — potential race condition if two CICS tasks execute simultaneously.

## 9. Business Rules

1. Amount must be in signed format: sign + 8 digits + decimal point + 2 digits.
2. Dates must pass CSUTLDTC validation (IBM LE CEEDAYS API).
3. Merchant ID must be all numeric.
4. CONFIRM='Y' is required to actually write; 'N' or blank only validates.
5. Either Account ID or Card Number must be provided (the other is resolved via cross-reference).

## 10. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| CDEMO-FROM-PROGRAM | XCTL | PF3 |
| COMEN01C | XCTL | PF3 default |
