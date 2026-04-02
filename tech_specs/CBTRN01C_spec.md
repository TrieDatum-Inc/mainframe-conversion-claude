# Technical Specification: CBTRN01C

## 1. Executive Summary

CBTRN01C is a batch COBOL program in the CardDemo application that reads a sequential daily transaction input file (DALYTRAN) and validates each transaction by verifying the card number against the cross-reference file (XREFFILE) and the associated account against the account master file (ACCTFILE). It is a validation and diagnostic program — it reads and verifies relationships but does not post transactions, write output records, or update any master files. All results are reported via DISPLAY statements to SYSOUT. This program appears to be a pre-validation or diagnostic step, with the actual posting performed by CBTRN02C.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBTRN01C.cbl` | COBOL Batch Program | Main program |
| `CVTRA06Y.cpy` | Copybook | Daily transaction record (`DALYTRAN-RECORD`) |
| `CVCUS01Y.cpy` | Copybook | Customer record (`CUSTOMER-RECORD`) |
| `CVACT03Y.cpy` | Copybook | Card cross-reference record (`CARD-XREF-RECORD`) |
| `CVACT02Y.cpy` | Copybook | Card record (`CARD-RECORD`) |
| `CVACT01Y.cpy` | Copybook | Account record (`ACCOUNT-RECORD`) |
| `CVTRA05Y.cpy` | Copybook | Transaction record (`TRAN-RECORD`) |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBTRN01C` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Post the records from daily transaction file (validation and lookup) |
| Source Version | CardDemo_v2.0-25-gdb72e6b-235, 2025-04-29 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field | Mode |
|---|---|---|---|---|---|
| `DALYTRAN-FILE` | `DALYTRAN` | Sequential | Sequential | N/A | INPUT |
| `CUSTOMER-FILE` | `CUSTFILE` | INDEXED (KSDS) | Random | `FD-CUST-ID` PIC 9(09) | INPUT |
| `XREF-FILE` | `XREFFILE` | INDEXED (KSDS) | Random | `FD-XREF-CARD-NUM` PIC X(16) | INPUT |
| `CARD-FILE` | `CARDFILE` | INDEXED (KSDS) | Random | `FD-CARD-NUM` PIC X(16) | INPUT |
| `ACCOUNT-FILE` | `ACCTFILE` | INDEXED (KSDS) | Random | `FD-ACCT-ID` PIC 9(11) | INPUT |
| `TRANSACT-FILE` | `TRANFILE` | INDEXED (KSDS) | Random | `FD-TRANS-ID` PIC X(16) | INPUT |

**Note:** TRANSACT-FILE is opened for INPUT, not OUTPUT or I-O. No transaction records are written by this program. The file is opened but never read in the actual processing loop — its open/close is present but the file is not used.

---

## 5. File Section — Record Layouts

### 5.1 DALYTRAN-FILE (Input, Primary Driver)
```
01 FD-TRAN-RECORD.
   05 FD-TRAN-ID      PIC X(16)
   05 FD-CUST-DATA    PIC X(334)
```
Total: 350 bytes. Read INTO `DALYTRAN-RECORD` (from CVTRA06Y).

### 5.2 Other Files — FD layouts
All other files use standard 2-field FD patterns (key + data). Record data is read INTO working-storage copybook records.

---

## 6. Copybooks Referenced

| Copybook | Working-Storage Record | Key Fields Used |
|---|---|---|
| `CVTRA06Y` | `DALYTRAN-RECORD` | `DALYTRAN-CARD-NUM` X(16), `DALYTRAN-ID` X(16) |
| `CVCUS01Y` | `CUSTOMER-RECORD` | Not directly accessed in logic |
| `CVACT03Y` | `CARD-XREF-RECORD` | `XREF-CARD-NUM` X(16), `XREF-ACCT-ID` 9(11), `XREF-CUST-ID` 9(09) |
| `CVACT02Y` | `CARD-RECORD` | Not directly accessed in logic |
| `CVACT01Y` | `ACCOUNT-RECORD` | `ACCT-ID` 9(11) |
| `CVTRA05Y` | `TRAN-RECORD` | Not directly accessed in logic |

### CVTRA06Y — DALYTRAN-RECORD Layout (350 bytes)
```
01 DALYTRAN-RECORD.
   05 DALYTRAN-ID              PIC X(16)
   05 DALYTRAN-TYPE-CD         PIC X(02)
   05 DALYTRAN-CAT-CD          PIC 9(04)
   05 DALYTRAN-SOURCE          PIC X(10)
   05 DALYTRAN-DESC            PIC X(100)
   05 DALYTRAN-AMT             PIC S9(09)V99
   05 DALYTRAN-MERCHANT-ID     PIC 9(09)
   05 DALYTRAN-MERCHANT-NAME   PIC X(50)
   05 DALYTRAN-MERCHANT-CITY   PIC X(50)
   05 DALYTRAN-MERCHANT-ZIP    PIC X(10)
   05 DALYTRAN-CARD-NUM        PIC X(16)
   05 DALYTRAN-ORIG-TS         PIC X(26)
   05 DALYTRAN-PROC-TS         PIC X(26)
   05 FILLER                   PIC X(20)
```

---

## 7. Working-Storage Data Structures

| Field | PIC | Purpose |
|---|---|---|
| `DALYTRAN-STATUS` | 2 x PIC X | File status for DALYTRAN-FILE |
| `CUSTFILE-STATUS` | 2 x PIC X | File status for CUSTOMER-FILE |
| `XREFFILE-STATUS` | 2 x PIC X | File status for XREF-FILE |
| `CARDFILE-STATUS` | 2 x PIC X | File status for CARD-FILE |
| `ACCTFILE-STATUS` | 2 x PIC X | File status for ACCOUNT-FILE |
| `TRANFILE-STATUS` | 2 x PIC X | File status for TRANSACT-FILE |
| `IO-STATUS` | 2 x PIC X | Scratch area for error display |
| `TWO-BYTES-BINARY`/`TWO-BYTES-ALPHA` | PIC 9(4) BINARY / REDEFINES | Extended status code handling |
| `IO-STATUS-04` | PIC 9 + PIC 999 | 4-digit formatted status display |
| `APPL-RESULT` | PIC S9(9) COMP | 88 levels: `APPL-AOK` (0), `APPL-EOF` (16) |
| `END-OF-DAILY-TRANS-FILE` | PIC X(01) VALUE 'N' | EOF flag for DALYTRAN |
| `ABCODE` / `TIMING` | PIC S9(9) BINARY | Abend parameters |
| `WS-XREF-READ-STATUS` | PIC 9(04) | 0 = XREF found, 4 = XREF not found |
| `WS-ACCT-READ-STATUS` | PIC 9(04) | 0 = Account found, 4 = Account not found |

---

## 8. Procedure Division — Program Flow

### 8.1 Main Control (lines 155–197)
```
MAIN-PARA:
    DISPLAY 'START OF EXECUTION OF PROGRAM CBTRN01C'
    PERFORM 0000-DALYTRAN-OPEN
    PERFORM 0100-CUSTFILE-OPEN
    PERFORM 0200-XREFFILE-OPEN
    PERFORM 0300-CARDFILE-OPEN
    PERFORM 0400-ACCTFILE-OPEN
    PERFORM 0500-TRANFILE-OPEN

    PERFORM UNTIL END-OF-DAILY-TRANS-FILE = 'Y'
        IF END-OF-DAILY-TRANS-FILE = 'N'
            PERFORM 1000-DALYTRAN-GET-NEXT
            IF END-OF-DAILY-TRANS-FILE = 'N'
                DISPLAY DALYTRAN-RECORD
            END-IF
            MOVE 0 TO WS-XREF-READ-STATUS
            MOVE DALYTRAN-CARD-NUM TO XREF-CARD-NUM
            PERFORM 2000-LOOKUP-XREF
            IF WS-XREF-READ-STATUS = 0
                MOVE 0 TO WS-ACCT-READ-STATUS
                MOVE XREF-ACCT-ID TO ACCT-ID
                PERFORM 3000-READ-ACCOUNT
                IF WS-ACCT-READ-STATUS NOT = 0
                    DISPLAY 'ACCOUNT ' ACCT-ID ' NOT FOUND'
                END-IF
            ELSE
                DISPLAY 'CARD NUMBER ' DALYTRAN-CARD-NUM
                ' COULD NOT BE VERIFIED. SKIPPING TRANSACTION ID-'
                DALYTRAN-ID
            END-IF
        END-IF
    END-PERFORM

    PERFORM 9000 through 9500 (close all files)
    DISPLAY 'END OF EXECUTION OF PROGRAM CBTRN01C'
    GOBACK
```

**Structural note:** The `MOVE 0 TO WS-XREF-READ-STATUS` and subsequent XREF/account lookups are executed even when END-OF-DAILY-TRANS-FILE = 'Y' (EOF), because they are outside the inner `IF END-OF-DAILY-TRANS-FILE = 'N'` block. This means after the last record triggers EOF, the code still tries to look up the (now undefined/garbage) DALYTRAN-CARD-NUM in XREFFILE. This is likely a defect in the PERFORM UNTIL loop structure.

### 8.2 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `0000-DALYTRAN-OPEN` | 252–268 | Opens DALYTRAN-FILE for INPUT. Abends on failure. |
| `0100-CUSTFILE-OPEN` | 271–287 | Opens CUSTOMER-FILE for INPUT. Abends on failure. |
| `0200-XREFFILE-OPEN` | 289–305 | Opens XREF-FILE for INPUT. Abends on failure. |
| `0300-CARDFILE-OPEN` | 307–323 | Opens CARD-FILE for INPUT. Abends on failure. |
| `0400-ACCTFILE-OPEN` | 325–341 | Opens ACCOUNT-FILE for INPUT. Abends on failure. |
| `0500-TRANFILE-OPEN` | 343–359 | Opens TRANSACT-FILE for INPUT. Abends on failure. **This file is never read.** |
| `1000-DALYTRAN-GET-NEXT` | 202–225 | Reads next daily transaction record. Status '10' = EOF; other = abend. |
| `2000-LOOKUP-XREF` | 227–239 | Keyed READ of XREF-FILE by FD-XREF-CARD-NUM. On INVALID KEY: DISPLAY 'INVALID CARD NUMBER FOR XREF', sets WS-XREF-READ-STATUS=4. On NOT INVALID KEY: DISPLAYs card number, account ID, and customer ID; WS-XREF-READ-STATUS remains 0. |
| `3000-READ-ACCOUNT` | 241–250 | Keyed READ of ACCOUNT-FILE by FD-ACCT-ID. On INVALID KEY: DISPLAY 'INVALID ACCOUNT NUMBER FOUND', sets WS-ACCT-READ-STATUS=4. On NOT INVALID KEY: DISPLAY 'SUCCESSFUL READ OF ACCOUNT FILE'. |
| `9000-DALYTRAN-CLOSE` | 361–377 | Closes DALYTRAN-FILE. **Note defect:** on error, moves CUSTFILE-STATUS (not DALYTRAN-STATUS) to IO-STATUS (line 373 — `MOVE CUSTFILE-STATUS TO IO-STATUS`). Wrong status variable used. |
| `9100-CUSTFILE-CLOSE` | 379–395 | Closes CUSTOMER-FILE. |
| `9200-XREFFILE-CLOSE` | 397–413 | Closes XREF-FILE. |
| `9300-CARDFILE-CLOSE` | 415–431 | Closes CARD-FILE. |
| `9400-ACCTFILE-CLOSE` | 433–449 | Closes ACCOUNT-FILE. |
| `9500-TRANFILE-CLOSE` | 451–467 | Closes TRANSACT-FILE. |
| `Z-ABEND-PROGRAM` | 469–473 | Calls CEE3ABD with ABCODE=999, TIMING=0. |
| `Z-DISPLAY-IO-STATUS` | 476–489 | Formats and displays 2-byte file status as 4-digit code. |

---

## 9. External Program Calls

| Called Program | Mechanism | Purpose |
|---|---|---|
| `CEE3ABD` | CALL ... USING ABCODE, TIMING | LE abnormal termination. |

---

## 10. Business Logic and Processing Rules

1. **Transaction Validation (Lookup Only):** For each DALYTRAN record, the program verifies:
   - The card number (DALYTRAN-CARD-NUM) exists in XREFFILE
   - If found, the linked account ID (XREF-ACCT-ID) exists in ACCTFILE

2. **No Posting or Output:** No records are written or updated. This is a read-and-verify program only.

3. **DISPLAY-Only Reporting:** All validation results are reported via DISPLAY to SYSOUT. There is no structured reject report file.

4. **Non-Fatal Validation Failures:** Both XREF-not-found and Account-not-found conditions produce DISPLAY messages but do not abend the program. Processing continues with the next transaction.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| File open failure | Status != '00' | DISPLAY error, Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM |
| DALYTRAN read error | APPL-RESULT = 12 | DISPLAY 'ERROR READING DAILY TRANSACTION FILE', abend |
| XREF key not found | INVALID KEY | DISPLAY warning, WS-XREF-READ-STATUS = 4, continue |
| Account key not found | INVALID KEY | DISPLAY warning, WS-ACCT-READ-STATUS = 4, continue |
| File close failure | Status != '00' | DISPLAY error, abend |

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion | 0 (implicit GOBACK) |
| Fatal I/O error | U0999 abend via CEE3ABD |

---

## 13. Known Defects

1. **Post-EOF Processing (lines 170–185):** The XREF lookup and account read paragraphs are executed unconditionally within the outer PERFORM UNTIL loop — they are not guarded by the inner `IF END-OF-DAILY-TRANS-FILE = 'N'` check. After EOF is detected, these lookups execute one extra time using stale data from the last DALYTRAN record read (since the failed read does not update DALYTRAN-CARD-NUM). This produces spurious XREF/account lookup messages for the last record.

2. **Wrong Status Variable in 9000-DALYTRAN-CLOSE (line 373):** On DALYTRAN-FILE close error, the code moves `CUSTFILE-STATUS` to IO-STATUS instead of `DALYTRAN-STATUS`. This would display incorrect diagnostic information.

3. **Unused Files:** CUSTOMER-FILE, CARD-FILE, and TRANSACT-FILE are opened and closed but are never read during processing. Their corresponding copybooks (CVCUS01Y, CVACT02Y, CVTRA05Y) are declared in working-storage but never used. This suggests CBTRN01C was scaffolded from a template or is an early prototype.
