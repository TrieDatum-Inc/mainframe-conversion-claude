# Technical Specification: CBTRN02C — Daily Transaction Posting

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBTRN02C |
| Source File | `app/cbl/CBTRN02C.cbl` |
| Type | Batch COBOL |
| JCL | POSTTRAN job, STEP15 |

## 2. Purpose

CBTRN02C is the **production daily transaction posting program**. It reads DALYTRAN, validates each transaction via XREFFILE, posts valid records to TRANSACT VSAM, updates ACCTFILE balance, updates TCATBALF category totals, and writes rejected records to DALYREJS.

## 3. Files Accessed

| File DD | Direction | Access | Key | Layout |
|---------|-----------|--------|-----|--------|
| DALYTRAN | Input | Sequential | — | CVTRA06Y (350 bytes) |
| TRANSACT | Output | KSDS random WRITE | TRAN-ID X(16) | CVTRA05Y (350 bytes) |
| XREFFILE | Input | KSDS random READ | XREF-CARD-NUM X(16) | CVACT03Y (50 bytes) |
| DALYREJS | Output | Sequential | — | Rejection records (430 bytes) |
| ACCTFILE | I/O | KSDS random READ/REWRITE | ACCT-ID 9(11) | CVACT01Y (300 bytes) |
| TCATBALF | I/O | KSDS random READ/REWRITE/WRITE | Composite 17-byte | CVTRA01Y (50 bytes) |

## 4. Processing Flow

```
For each DALYTRAN record:
  1. Validate card via XREFFILE lookup
  2. Validate account via ACCTFILE lookup
  3. Check for duplicate TRAN-ID in TRANSACT
  4. If valid:
     a. WRITE to TRANSACT
     b. READ ACCTFILE with UPDATE → update balance → REWRITE
     c. READ TCATBALF:
        - If found: REWRITE with updated category balance
        - If not found: WRITE new category balance record
  5. If invalid:
     → WRITE rejection record + validation trailer to DALYREJS
```

## 5. Output

- Valid transactions → TRANSACT VSAM KSDS
- Updated balances → ACCTFILE VSAM KSDS
- Updated category totals → TCATBALF VSAM KSDS
- Rejected records → DALYREJS GDG (+1, 430-byte records)

## 6. Copybooks Used

CVTRA06Y, CVTRA05Y, CVACT03Y, CVACT01Y, CVTRA01Y
