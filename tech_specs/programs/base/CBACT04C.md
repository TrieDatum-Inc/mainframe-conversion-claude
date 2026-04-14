# Technical Specification: CBACT04C

## 1. Program Overview

| Attribute        | Value                                              |
|------------------|----------------------------------------------------|
| Program ID       | CBACT04C                                           |
| Source File      | app/cbl/CBACT04C.cbl                               |
| Application      | CardDemo                                           |
| Type             | Batch COBOL Program                                |
| Transaction ID   | N/A (batch)                                        |
| Function         | Interest calculator. Reads the Transaction Category Balance file (TCATBALF) sequentially, looks up interest rates from the Disclosure Group file (DISCGRP) using each account's group and transaction category, computes monthly interest, generates interest charge transaction records into TRANSACT, and updates account balances in ACCTFILE. |

---

## 2. Program Flow

### High-Level Flow

```
RECEIVE parm: EXTERNAL-PARMS (PARM-LENGTH S9(4) COMP, PARM-DATE X(10))
OPEN TCATBAL-FILE (INPUT), XREF-FILE (INPUT), DISCGRP-FILE (INPUT),
     ACCOUNT-FILE (I-O), TRANSACT-FILE (OUTPUT)

PERFORM UNTIL END-OF-FILE = 'Y'
    READ TCATBAL-FILE into TRAN-CAT-BAL-RECORD
    IF new account (TRANCAT-ACCT-ID != WS-LAST-ACCT-NUM):
        IF not first time: PERFORM 1050-UPDATE-ACCOUNT (REWRITE account)
        RESET WS-TOTAL-INT = 0
        READ ACCOUNT-FILE for this account (1100-GET-ACCT-DATA)
        READ XREF-FILE for this account (1110-GET-XREF-DATA)
    SET disclosure group key (ACCT-GROUP-ID + TRANCAT-TYPE-CD + TRANCAT-CD)
    READ DISCGRP-FILE (1200-GET-INTEREST-RATE)
    IF interest rate != 0:
        COMPUTE monthly interest = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200
        ADD to WS-TOTAL-INT
        WRITE interest transaction to TRANSACT-FILE (1300-B-WRITE-TX)
        [1400-COMPUTE-FEES is a stub -- EXIT only]
    ON EOF: perform 1050-UPDATE-ACCOUNT for the last account

CLOSE all files
STOP
```

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| PROCEDURE DIVISION     | 180–232   | Main driver with USING EXTERNAL-PARMS; opens 5 files, runs loop, closes, GOBACK |
| 1000-TCATBALF-GET-NEXT | 325–348   | Sequential READ of TCATBAL-FILE into TRAN-CAT-BAL-RECORD |
| 1050-UPDATE-ACCOUNT    | 350–370   | Adds WS-TOTAL-INT to ACCT-CURR-BAL, zeroes cycle credit/debit, REWRITEs account record |
| 1100-GET-ACCT-DATA     | 372–391   | Random READ of ACCOUNT-FILE by FD-ACCT-ID; abends on not-found |
| 1110-GET-XREF-DATA     | 393–413   | Random READ of XREF-FILE by alternate key FD-XREF-ACCT-ID |
| 1200-GET-INTEREST-RATE | 415–440   | Random READ of DISCGRP-FILE; if status '23' (not found), sets group to 'DEFAULT' and calls 1200-A |
| 1200-A-GET-DEFAULT-INT-RATE | 443–460 | Fallback read of DISCGRP-FILE with 'DEFAULT' group key |
| 1300-COMPUTE-INTEREST  | 462–470   | COMPUTE WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200; adds to WS-TOTAL-INT; calls 1300-B |
| 1300-B-WRITE-TX        | 473–515   | Builds TRAN-RECORD (interest charge); generates TRAN-ID from PARM-DATE + suffix counter; writes to TRANSACT-FILE |
| 1400-COMPUTE-FEES      | 518–520   | Stub — EXIT only; fees not yet implemented |
| Z-GET-DB2-FORMAT-TIMESTAMP | 613–626 | Builds DB2-format timestamp string (YYYY-MM-DD-HH.MM.SS.mmm0000) from FUNCTION CURRENT-DATE |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Record / Structure | Used For |
|----------|--------------------|----------|
| CVTRA01Y | `TRAN-CAT-BAL-RECORD`: TRANCAT-ACCT-ID 9(11), TRANCAT-TYPE-CD X(2), TRANCAT-CD 9(4), TRAN-CAT-BAL S9(9)V99 (approx) | Driving file; transaction category balance per account |
| CVACT03Y | `CARD-XREF-RECORD`: XREF-CARD-NUM X(16), XREF-CUST-ID 9(9), XREF-ACCT-ID 9(11), FILLER X(14) | Cross-reference lookup |
| CVTRA02Y | `DIS-GROUP-RECORD` (disclosure group): FD-DIS-ACCT-GROUP-ID X(10) + FD-DIS-TRAN-TYPE-CD X(2) + FD-DIS-TRAN-CAT-CD 9(4) + DIS-INT-RATE (numeric) | Interest rate lookup |
| CVACT01Y | `ACCOUNT-RECORD`: ACCT-ID 9(11), ACCT-ACTIVE-STATUS X(1), ACCT-CURR-BAL S9(10)V99, ACCT-CREDIT-LIMIT, ACCT-CASH-CREDIT-LIMIT, dates, ACCT-CURR-CYC-CREDIT, ACCT-CURR-CYC-DEBIT, ACCT-ADDR-ZIP, ACCT-GROUP-ID X(10) | Account balance update |
| CVTRA05Y | `TRAN-RECORD`: TRAN-ID X(16), TRAN-TYPE-CD X(2), TRAN-CAT-CD 9(4), TRAN-SOURCE X(10), TRAN-DESC X(100), TRAN-AMT S9(9)V99, TRAN-MERCHANT-ID 9(9), TRAN-MERCHANT-NAME X(50), TRAN-MERCHANT-CITY X(50), TRAN-MERCHANT-ZIP X(10), TRAN-CARD-NUM X(16), TRAN-ORIG-TS X(26), TRAN-PROC-TS X(26), FILLER X(20) | Output transaction record for TRANSACT file |

### File Description Records

| FD Name        | DD Name   | Key                           | Access  |
|----------------|-----------|-------------------------------|---------|
| TCATBAL-FILE   | TCATBALF  | FD-TRAN-CAT-KEY (composite: ACCT-ID+TYPE-CD+CAT-CD) | Sequential |
| XREF-FILE      | XREFFILE  | FD-XREF-CARD-NUM X(16); alternate: FD-XREF-ACCT-ID 9(11) | Random |
| DISCGRP-FILE   | DISCGRP   | FD-DISCGRP-KEY (composite: GROUP-ID+TYPE-CD+CAT-CD) | Random |
| ACCOUNT-FILE   | ACCTFILE  | FD-ACCT-ID 9(11) | Random |
| TRANSACT-FILE  | TRANSACT  | N/A sequential output | Sequential |

### Key Working Storage Variables

| Variable           | PIC           | Purpose |
|--------------------|---------------|---------|
| WS-LAST-ACCT-NUM   | X(11)         | Tracks previous account; used to detect account change |
| WS-MONTHLY-INT     | S9(9)V99      | Monthly interest computed for one category |
| WS-TOTAL-INT       | S9(9)V99      | Accumulated interest for current account (all categories) |
| WS-FIRST-TIME      | X(1)          | 'Y' on first record; prevents premature account update |
| WS-RECORD-COUNT    | 9(9)          | Count of TCATBALF records processed |
| WS-TRANID-SUFFIX   | 9(6)          | Incremented counter appended to PARM-DATE to form TRAN-ID |
| PARM-DATE          | X(10)         | Date passed as JCL PARM; used as first 10 chars of TRAN-ID |
| DB2-FORMAT-TS      | X(26)         | DB2-format timestamp built from CURRENT-DATE |
| COBOL-TS           | Group         | Receives FUNCTION CURRENT-DATE (21 chars) |
| EXTERNAL-PARMS     | Linkage 01    | PARM-LENGTH S9(4) COMP + PARM-DATE X(10) |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name   | File Object    | Org  | Access     | Open Mode | Purpose |
|-----------|----------------|------|------------|-----------|---------|
| TCATBALF  | TCATBAL-FILE   | KSDS | Sequential | INPUT     | Driving file: balance per transaction category per account |
| XREFFILE  | XREF-FILE      | KSDS | Random     | INPUT     | Looks up card number for account (for TRAN-CARD-NUM) |
| DISCGRP   | DISCGRP-FILE   | KSDS | Random     | INPUT     | Interest rate lookup by group/type/category |
| ACCTFILE  | ACCOUNT-FILE   | KSDS | Random     | I-O       | Read account for ACCT-GROUP-ID; REWRITE to post interest |
| TRANSACT  | TRANSACT-FILE  | Sequential | Sequential | OUTPUT | Generated interest charge transactions |

---

## 6. Screen Interaction

None. Batch program.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| CEE3ABD        | Static CALL | LE forced abnormal termination |

No other programs are called.

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| TCATBALF status '00' | Normal |
| TCATBALF status '10' | EOF: set END-OF-FILE='Y'; trigger final 1050-UPDATE-ACCOUNT |
| TCATBALF other status | DISPLAY error, 9910, 9999 abend |
| ACCOUNT-FILE not found (INVALID KEY) | DISPLAY 'ACCOUNT NOT FOUND:' + FD-ACCT-ID; continues (no abend) |
| ACCOUNT-FILE other error | DISPLAY, 9910, abend |
| XREF-FILE not found (INVALID KEY) | DISPLAY 'ACCOUNT NOT FOUND:' + FD-XREF-ACCT-ID; continues |
| DISCGRP-FILE not found (status '23') | Retry with 'DEFAULT' as group ID |
| DISCGRP-FILE error (non '00'/'23') | DISPLAY, 9910, abend |
| ACCOUNT-FILE REWRITE error | DISPLAY 'ERROR RE-WRITING ACCOUNT FILE', 9910, abend |
| TRANSACT-FILE WRITE error | DISPLAY 'ERROR WRITING TRANSACTION RECORD', 9910, abend |
| Any OPEN/CLOSE failure | DISPLAY specific message, 9910, abend |

---

## 9. Business Rules

1. **Interest formula**: `WS-MONTHLY-INT = (TRAN-CAT-BAL × DIS-INT-RATE) / 1200`. Dividing by 1200 converts an annual percentage rate to a monthly fraction (annual rate / 12 months / 100 percent).
2. **Interest rate lookup**: The program first looks up the rate using the actual account group ID. If not found (status '23'), it falls back to the group code 'DEFAULT'.
3. **Zero-rate bypass**: If DIS-INT-RATE = 0, neither interest computation nor fee computation is performed for that category.
4. **Account grouping by TCATBALF**: The input file is assumed to be sorted by TRANCAT-ACCT-ID. Each change in account ID triggers an account record update (REWRITE) for the previous account before loading the new one.
5. **Interest transaction attributes**: Generated transaction records use TRAN-TYPE-CD='01', TRAN-CAT-CD='05', TRAN-SOURCE='System', TRAN-MERCHANT-ID=0, TRAN-DESC='Int. for a/c ' + ACCT-ID.
6. **Account balance update on interest**: ACCT-CURR-BAL += WS-TOTAL-INT; ACCT-CURR-CYC-CREDIT = 0; ACCT-CURR-CYC-DEBIT = 0.
7. **Fee computation stub**: Paragraph 1400-COMPUTE-FEES is defined but contains only EXIT; fees are not yet implemented.
8. **PARM-DATE required**: The program PROCEDURE DIVISION uses `USING EXTERNAL-PARMS`, meaning it must be called with a JCL PARM containing a date value; this date is embedded in each generated transaction ID.

---

## 10. Inputs and Outputs

### Inputs

| Source        | Description |
|---------------|-------------|
| TCATBALF      | Transaction category balance records (driving file, sequential) |
| XREFFILE      | Card cross-reference — provides card number for interest transaction record |
| DISCGRP       | Disclosure group interest rates per group/type/category |
| ACCTFILE      | Account master — read for ACCT-GROUP-ID; updated with interest |
| JCL PARM      | PARM-DATE (X(10)): date string embedded in generated TRAN-IDs |

### Outputs

| Destination | Record Type    | Description |
|-------------|----------------|-------------|
| TRANSACT    | TRAN-RECORD    | One interest charge transaction per account category with non-zero rate |
| ACCTFILE    | ACCOUNT-RECORD | REWRITE with updated ACCT-CURR-BAL and zeroed cycle amounts |
| SYSOUT      | DISPLAY        | Each TRAN-CAT-BAL-RECORD content; start/end messages; error messages |

---

## 11. Key Variables and Their Purpose

| Variable          | Purpose |
|-------------------|---------|
| EXTERNAL-PARMS    | Linkage section: receives JCL PARM; PARM-DATE used for transaction ID prefix |
| WS-LAST-ACCT-NUM  | Previous account number; trigger for account-change processing |
| WS-FIRST-TIME     | Guards against REWRITE of uninitialized account on the very first record |
| WS-TOTAL-INT      | Accumulates all category interest charges for one account before REWRITE |
| WS-TRANID-SUFFIX  | Per-run sequence counter appended to PARM-DATE to ensure unique TRAN-IDs |
| DB2-FORMAT-TS     | Timestamp in DB2 format (YYYY-MM-DD-HH.MM.SS.mmm0000) applied to TRAN-ORIG-TS and TRAN-PROC-TS |
| TRAN-CAT-BAL      | Balance for this transaction category (from TRAN-CAT-BAL-RECORD); basis for interest calculation |
| DIS-INT-RATE      | Annual interest rate (from DIS-GROUP-RECORD); used in interest formula |
