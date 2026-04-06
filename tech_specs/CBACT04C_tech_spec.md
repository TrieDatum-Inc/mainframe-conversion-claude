# Technical Specification: CBACT04C — Interest/Fee Calculator

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBACT04C |
| Source File | `app/cbl/CBACT04C.cbl` |
| Type | Batch COBOL |
| JCL | INTCALC step in monthly batch chain |

## 2. Purpose

CBACT04C is the **core batch interest computation program**. It reads the transaction category balance file (TCATBALF), groups records by account, looks up the discount/interest group rate from DISCGRP, computes monthly interest for each transaction category, and writes system-generated interest/fee transaction records.

## 3. Files Accessed

| File DD | Direction | Access | Key | Layout |
|---------|-----------|--------|-----|--------|
| TCATBALF | Input | KSDS sequential | ACCT-ID(11) + TYPE-CD(2) + CAT-CD(4) = 17 bytes | CVTRA01Y (50 bytes) |
| XREFFILE | Input | KSDS random + AIX | XREF-CARD-NUM or XREF-ACCT-ID | CVACT03Y (50 bytes) |
| ACCTFILE | I/O | KSDS random | ACCT-ID 9(11) | CVACT01Y (300 bytes) |
| DISCGRP | Input | KSDS random | GROUP-ID(10) + TYPE-CD(2) + CAT-CD(4) = 16 bytes | CVTRA02Y (50 bytes) |
| TRANSACT | Output | Sequential | — | CVTRA05Y (350 bytes) |

## 4. JCL Parameters

Receives `PARM='YYYYMMDD'` via JCL for the processing date (e.g., '2022071800').

## 5. Processing Flow

```
1. Read TCATBALF sequentially
2. Group records by TRANCAT-ACCT-ID
3. On account change: call 1050-UPDATE-ACCOUNT
4. For each category:
   a. Look up DIS-INT-RATE from DISCGRP using ACCT-GROUP-ID + TYPE-CD + CAT-CD
   b. If rate non-zero:
      - 1300-COMPUTE-INTEREST: calculate interest amount
      - 1400-COMPUTE-FEES: calculate fee amount
   c. Write interest/fee transaction to TRANSACT (output)
5. Update ACCTFILE balance with accumulated interest
```

## 6. Output

System-generated transactions written to SYSTRAN GDG (FB/350), which are later merged into the main TRANSACT file via the COMBTRAN job.

## 7. Copybooks Used

CVTRA01Y (category balance), CVACT03Y (xref), CVTRA02Y (discount group), CVACT01Y (account), CVTRA05Y (transaction)
