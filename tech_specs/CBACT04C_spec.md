# Technical Specification: CBACT04C

## 1. Executive Summary

CBACT04C is the interest calculator batch COBOL program in the CardDemo application. It reads the transaction category balance file (TCATBAL) sequentially, and for each account/category combination: retrieves the account record, retrieves the cross-reference record, looks up the applicable interest rate from the disclosure group file, computes monthly interest, and writes a system-generated interest transaction to the transaction file. At end-of-file it updates the account master record with accumulated interest and resets the cycle credit/debit fields to zero. This is the core end-of-cycle batch processing program.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBACT04C.cbl` | COBOL Batch Program | Main program |
| `CVTRA01Y.cpy` | Copybook | Transaction category balance record (`TRAN-CAT-BAL-RECORD`) |
| `CVACT03Y.cpy` | Copybook | Card cross-reference record (`CARD-XREF-RECORD`) |
| `CVTRA02Y.cpy` | Copybook | Disclosure group record (`DIS-GROUP-RECORD`) |
| `CVACT01Y.cpy` | Copybook | Account master record (`ACCOUNT-RECORD`) |
| `CVTRA05Y.cpy` | Copybook | Transaction record (`TRAN-RECORD`) |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBACT04C` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Interest calculator |
| Entry | `PROCEDURE DIVISION USING EXTERNAL-PARMS` |
| Source Version | CardDemo_v2.0-25-gdb72e6b-235, 2025-04-29 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field(s) |
|---|---|---|---|---|
| `TCATBAL-FILE` | `TCATBALF` | INDEXED (KSDS) | Sequential | `FD-TRAN-CAT-KEY` (composite: ACCT-ID 9(11) + TYPE-CD X(02) + CAT-CD 9(04)) |
| `XREF-FILE` | `XREFFILE` | INDEXED (KSDS) | Random | Primary: `FD-XREF-CARD-NUM` X(16); Alternate: `FD-XREF-ACCT-ID` 9(11) |
| `ACCOUNT-FILE` | `ACCTFILE` | INDEXED (KSDS) | Random | `FD-ACCT-ID` PIC 9(11) |
| `DISCGRP-FILE` | `DISCGRP` | INDEXED (KSDS) | Random | `FD-DISCGRP-KEY` (composite: ACCT-GROUP-ID X(10) + TRAN-TYPE-CD X(02) + TRAN-CAT-CD 9(04)) |
| `TRANSACT-FILE` | `TRANSACT` | Sequential | Sequential | N/A |

---

## 5. File Section — Record Layouts

### 5.1 TCATBAL-FILE (Input, Primary Driver)
```
01 FD-TRAN-CAT-BAL-RECORD.
   05 FD-TRAN-CAT-KEY.
      10 FD-TRANCAT-ACCT-ID     PIC 9(11)
      10 FD-TRANCAT-TYPE-CD     PIC X(02)
      10 FD-TRANCAT-CD          PIC 9(04)
   05 FD-FD-TRAN-CAT-DATA       PIC X(33)
```
Total record length: 50 bytes. Read INTO `TRAN-CAT-BAL-RECORD` (CVTRA01Y).

### 5.2 XREF-FILE (Input, Random)
```
01 FD-XREFFILE-REC.
   05 FD-XREF-CARD-NUM    PIC X(16)
   05 FD-XREF-CUST-NUM    PIC 9(09)
   05 FD-XREF-ACCT-ID     PIC 9(11)
   05 FD-XREF-FILLER      PIC X(14)
```
Total record length: 50 bytes. Read via alternate key `FD-XREF-ACCT-ID`.

### 5.3 DISCGRP-FILE (Input, Random)
```
01 FD-DISCGRP-REC.
   05 FD-DISCGRP-KEY.
      10 FD-DIS-ACCT-GROUP-ID    PIC X(10)
      10 FD-DIS-TRAN-TYPE-CD     PIC X(02)
      10 FD-DIS-TRAN-CAT-CD      PIC 9(04)
   05 FD-DISCGRP-DATA            PIC X(34)
```
Total record length: 50 bytes. Read INTO `DIS-GROUP-RECORD` (CVTRA02Y).

### 5.4 ACCOUNT-FILE (I-O, Random)
```
01 FD-ACCTFILE-REC.
   05 FD-ACCT-ID      PIC 9(11)
   05 FD-ACCT-DATA    PIC X(289)
```
Total record length: 300 bytes. Read/REWRITE INTO/FROM `ACCOUNT-RECORD` (CVACT01Y).

### 5.5 TRANSACT-FILE (Output, Sequential)
```
01 FD-TRANFILE-REC.
   05 FD-TRANS-ID    PIC X(16)
   05 FD-ACCT-DATA   PIC X(334)
```
Total record length: 350 bytes. Written FROM `TRAN-RECORD` (CVTRA05Y).

---

## 6. Copybooks Referenced

| Copybook | Location in Source | Record Defined | Key Fields |
|---|---|---|---|
| `CVTRA01Y` | Line 97 | `TRAN-CAT-BAL-RECORD` | `TRANCAT-ACCT-ID`, `TRANCAT-TYPE-CD`, `TRANCAT-CD`, `TRAN-CAT-BAL` S9(09)V99 |
| `CVACT03Y` | Line 102 | `CARD-XREF-RECORD` | `XREF-CARD-NUM` X(16), `XREF-CUST-ID` 9(09), `XREF-ACCT-ID` 9(11) |
| `CVTRA02Y` | Line 107 | `DIS-GROUP-RECORD` | `DIS-ACCT-GROUP-ID` X(10), `DIS-TRAN-TYPE-CD` X(02), `DIS-TRAN-CAT-CD` 9(04), `DIS-INT-RATE` S9(04)V99 |
| `CVACT01Y` | Line 112 | `ACCOUNT-RECORD` | `ACCT-ID`, `ACCT-CURR-BAL`, `ACCT-CURR-CYC-CREDIT`, `ACCT-CURR-CYC-DEBIT`, `ACCT-GROUP-ID` |
| `CVTRA05Y` | Line 117 | `TRAN-RECORD` | `TRAN-ID`, `TRAN-TYPE-CD`, `TRAN-CAT-CD`, `TRAN-AMT`, `TRAN-ORIG-TS`, `TRAN-PROC-TS`, `TRAN-CARD-NUM` |

---

## 7. Linkage Section — External Parameters

```
01 EXTERNAL-PARMS.
   05 PARM-LENGTH    PIC S9(04) COMP
   05 PARM-DATE      PIC X(10)
```
The program receives a run date via JCL PARM, stored in `PARM-DATE`. This date is used as the prefix of generated transaction IDs.

---

## 8. Working-Storage Data Structures

| Field | PIC / Type | Purpose |
|---|---|---|
| `COBOL-TS` | Group (7 x PIC X) | Receives FUNCTION CURRENT-DATE result |
| `DB2-FORMAT-TS` | PIC X(26) + REDEFINES | DB2-style timestamp: YYYY-MM-DD-HH.MM.SS.cc0000 |
| `WS-LAST-ACCT-NUM` | PIC X(11) VALUE SPACES | Tracks current account ID for change-of-account detection |
| `WS-MONTHLY-INT` | PIC S9(09)V99 | Computed monthly interest for one category |
| `WS-TOTAL-INT` | PIC S9(09)V99 | Accumulated total interest for current account |
| `WS-FIRST-TIME` | PIC X(01) VALUE 'Y' | Flag to skip account update on very first account group |
| `WS-RECORD-COUNT` | PIC 9(09) VALUE 0 | Count of TCATBAL records processed |
| `WS-TRANID-SUFFIX` | PIC 9(06) VALUE 0 | Sequential suffix counter for generated TRAN-ID |

---

## 9. Procedure Division — Program Flow

### 9.1 Invocation
Program is called with `PROCEDURE DIVISION USING EXTERNAL-PARMS`. The PARM-DATE field is populated by JCL.

### 9.2 Main Control (lines 181–232)
```
PERFORM 0000-TCATBALF-OPEN
PERFORM 0100-XREFFILE-OPEN
PERFORM 0200-DISCGRP-OPEN
PERFORM 0300-ACCTFILE-OPEN   (I-O mode)
PERFORM 0400-TRANFILE-OPEN   (OUTPUT mode)

PERFORM UNTIL END-OF-FILE = 'Y'
    IF END-OF-FILE = 'N'
        PERFORM 1000-TCATBALF-GET-NEXT
        IF END-OF-FILE = 'N'
            ADD 1 TO WS-RECORD-COUNT
            DISPLAY TRAN-CAT-BAL-RECORD
            IF TRANCAT-ACCT-ID NOT= WS-LAST-ACCT-NUM
                IF WS-FIRST-TIME NOT = 'Y'
                    PERFORM 1050-UPDATE-ACCOUNT   [post previous account]
                ELSE
                    MOVE 'N' TO WS-FIRST-TIME
                END-IF
                MOVE 0 TO WS-TOTAL-INT
                MOVE TRANCAT-ACCT-ID TO WS-LAST-ACCT-NUM, FD-ACCT-ID
                PERFORM 1100-GET-ACCT-DATA
                MOVE TRANCAT-ACCT-ID TO FD-XREF-ACCT-ID
                PERFORM 1110-GET-XREF-DATA
            END-IF
            MOVE ACCT-GROUP-ID TO FD-DIS-ACCT-GROUP-ID
            MOVE TRANCAT-CD TO FD-DIS-TRAN-CAT-CD
            MOVE TRANCAT-TYPE-CD TO FD-DIS-TRAN-TYPE-CD
            PERFORM 1200-GET-INTEREST-RATE
            IF DIS-INT-RATE NOT = 0
                PERFORM 1300-COMPUTE-INTEREST
                PERFORM 1400-COMPUTE-FEES
            END-IF
        END-IF
    ELSE
        PERFORM 1050-UPDATE-ACCOUNT  [post last account after EOF]
    END-IF
END-PERFORM

PERFORM 9000-9400 (close all files)
GOBACK
```

### 9.3 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `0000-TCATBALF-OPEN` | 234–250 | Opens TCATBAL-FILE for INPUT. Abends on failure. |
| `0100-XREFFILE-OPEN` | 252–268 | Opens XREF-FILE for INPUT. Abends on failure. |
| `0200-DISCGRP-OPEN` | 270–286 | Opens DISCGRP-FILE for INPUT. Abends on failure. |
| `0300-ACCTFILE-OPEN` | 289–305 | Opens ACCOUNT-FILE for I-O (read + rewrite). Abends on failure. |
| `0400-TRANFILE-OPEN` | 307–323 | Opens TRANSACT-FILE for OUTPUT. Abends on failure. |
| `1000-TCATBALF-GET-NEXT` | 325–348 | Reads next TCATBAL record sequentially. Status '10' = EOF; other = abend. |
| `1050-UPDATE-ACCOUNT` | 350–370 | Adds WS-TOTAL-INT to ACCT-CURR-BAL. Zeros ACCT-CURR-CYC-CREDIT and ACCT-CURR-CYC-DEBIT. REWRITEs FD-ACCTFILE-REC FROM ACCOUNT-RECORD. Abends on failure. |
| `1100-GET-ACCT-DATA` | 372–391 | Random READ of ACCOUNT-FILE by FD-ACCT-ID. Displays 'ACCOUNT NOT FOUND' on INVALID KEY but does not abend on not-found; abends on other errors. |
| `1110-GET-XREF-DATA` | 393–413 | Random READ of XREF-FILE by alternate key FD-XREF-ACCT-ID. Displays 'ACCOUNT NOT FOUND' on INVALID KEY; abends on other errors. |
| `1200-GET-INTEREST-RATE` | 415–440 | Random READ of DISCGRP-FILE by FD-DISCGRP-KEY. If status '23' (not found), sets group to 'DEFAULT' and calls 1200-A-GET-DEFAULT-INT-RATE. Abends on other errors. |
| `1200-A-GET-DEFAULT-INT-RATE` | 443–460 | Second READ of DISCGRP-FILE with 'DEFAULT' group ID to retrieve fallback interest rate. Abends on failure. |
| `1300-COMPUTE-INTEREST` | 462–470 | COMPUTE WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200. Adds to WS-TOTAL-INT. Calls 1300-B-WRITE-TX. |
| `1300-B-WRITE-TX` | 473–515 | Constructs a system-generated transaction record. Builds TRAN-ID by STRINGing PARM-DATE and WS-TRANID-SUFFIX. Sets TRAN-TYPE-CD='01', TRAN-CAT-CD='05', TRAN-SOURCE='System'. Builds TRAN-DESC as 'Int. for a/c ' + ACCT-ID. Sets TRAN-AMT=WS-MONTHLY-INT. Calls Z-GET-DB2-FORMAT-TIMESTAMP for timestamps. WRITEs to TRANSACT-FILE. |
| `1400-COMPUTE-FEES` | 518–520 | Stub paragraph — EXIT only. Fee computation not implemented. |
| `Z-GET-DB2-FORMAT-TIMESTAMP` | 613–626 | Uses FUNCTION CURRENT-DATE to build DB2-format timestamp string YYYY-MM-DD-HH.MM.SS.cc0000. |
| `9000-9400` | 522–611 | Close paragraphs for all 5 files. Each abends on close failure. |
| `9910-DISPLAY-IO-STATUS` | 635–648 | Formats and displays 2-byte file status as 4-digit code. |
| `9999-ABEND-PROGRAM` | 628–632 | Calls CEE3ABD with ABCODE=999, TIMING=0. |

---

## 10. Business Logic and Processing Rules

### 10.1 Change-of-Account Processing
The TCATBAL file is assumed to be sorted by ACCT-ID within the composite key. The program detects account breaks by comparing `TRANCAT-ACCT-ID` to `WS-LAST-ACCT-NUM`. When an account break is detected:
- The previous account's accumulated interest is posted (1050-UPDATE-ACCOUNT)
- WS-TOTAL-INT is reset to zero
- The new account's data is fetched from ACCOUNT-FILE and XREF-FILE

The WS-FIRST-TIME flag ('Y' at start) prevents a spurious update call on the first account encountered.

### 10.2 Interest Rate Lookup with Default Fallback
The interest rate is looked up from DISCGRP-FILE using a composite key of (ACCT-GROUP-ID, TRAN-TYPE-CD, TRAN-CAT-CD). If the key is not found (status '23'), the program substitutes 'DEFAULT' for the account group and re-reads. If the DEFAULT key is also not found, the program abends. If DIS-INT-RATE = 0, no interest or transaction is generated for that category.

### 10.3 Interest Computation Formula
```
WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200
```
This implements a standard monthly interest computation: annual rate divided by 12 months, divided by 100 (implicit in the rate stored as S9(04)V99). The total for all categories is accumulated in WS-TOTAL-INT.

### 10.4 Generated Transaction ID Format
```
TRAN-ID = PARM-DATE (10 chars) || WS-TRANID-SUFFIX (6 digits, zero-filled)
```
The PARM-DATE is supplied via JCL PARM. The suffix increments for each interest transaction written.

### 10.5 Account Update
After processing all TCATBAL records for an account, `1050-UPDATE-ACCOUNT` REWRITEs the account master record with:
- `ACCT-CURR-BAL` += WS-TOTAL-INT
- `ACCT-CURR-CYC-CREDIT` = 0 (reset)
- `ACCT-CURR-CYC-DEBIT` = 0 (reset)

### 10.6 Fee Computation (Not Implemented)
Paragraph `1400-COMPUTE-FEES` exists but contains only `EXIT`. Fee calculation is a planned but unimplemented feature.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| Any file open failure | Status != '00' | DISPLAY error, 9910-DISPLAY-IO-STATUS, 9999-ABEND-PROGRAM |
| TCATBAL read error | Status not '00' or '10' | DISPLAY error, abend |
| Account not found (1100) | INVALID KEY on READ | DISPLAY 'ACCOUNT NOT FOUND', continues (no abend) |
| XREF not found (1110) | INVALID KEY on READ | DISPLAY 'ACCOUNT NOT FOUND', continues (no abend) |
| DISCGRP not found, no default | Status not '00' or '23' | Abend |
| DISCGRP default not found | Status != '00' | DISPLAY error, abend |
| Account REWRITE failure | Status != '00' | DISPLAY 'ERROR RE-WRITING ACCOUNT FILE', abend |
| Transaction WRITE failure | Status != '00' | DISPLAY 'ERROR WRITING TRANSACTION RECORD', abend |
| Any close failure | Status != '00' | DISPLAY error, abend |

---

## 12. Return Codes and Abend Handling

| Condition | Return Code / Abend |
|---|---|
| Normal completion | 0 (implicit GOBACK) |
| Any fatal I/O error | U0999 abend via CEE3ABD |

---

## 13. Data Flow Diagram

```
TCATBAL-FILE (sequential) -->+
                              |
                              v
                        [For each record]
                              |
                        ACCOUNT-FILE (random read by ACCT-ID)
                        XREF-FILE (random read by ACCT-ID alternate key)
                        DISCGRP-FILE (random read by GROUP+TYPE+CAT)
                              |
                        [Compute interest]
                              |
                        TRANSACT-FILE (write interest transaction)
                              |
                        [On account break]
                              |
                        ACCOUNT-FILE (rewrite with updated balance)
```

---

## 14. Observations

- The program requires TCATBAL-FILE to be sorted by TRANCAT-ACCT-ID for correct change-of-account processing. No explicit sort step is documented within this program — it must be pre-sorted by the calling JCL.
- The last account group is updated by the `ELSE` branch of the main PERFORM loop (after EOF), not by an explicit end-of-run paragraph.
- TRANSACT-FILE is opened OUTPUT — the file is created fresh each run. Any prior contents are destroyed.
- The `1400-COMPUTE-FEES` stub paragraph is called unconditionally when DIS-INT-RATE != 0, suggesting fees were originally planned to be computed alongside interest for the same rate group.
