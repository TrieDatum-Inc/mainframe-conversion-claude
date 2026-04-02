# Technical Specification: CBTRN02C

## 1. Executive Summary

CBTRN02C is the core daily transaction posting batch COBOL program in the CardDemo application. It reads daily transactions from a sequential input file (DALYTRAN), validates each transaction against the card cross-reference file and the account master file, and for valid transactions posts them by: writing to the transaction master file (TRANSACT), updating the transaction category balance file (TCATBAL), and updating the account master balance fields. Invalid transactions are written to a rejects file (DALYREJS) with a validation failure reason code. The program reports final counts of accepted and rejected transactions and sets RETURN-CODE=4 if any rejections occurred.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBTRN02C.cbl` | COBOL Batch Program | Main program |
| `CVTRA06Y.cpy` | Copybook | Daily transaction record (`DALYTRAN-RECORD`) |
| `CVTRA05Y.cpy` | Copybook | Posted transaction record (`TRAN-RECORD`) |
| `CVACT03Y.cpy` | Copybook | Card cross-reference record (`CARD-XREF-RECORD`) |
| `CVACT01Y.cpy` | Copybook | Account record (`ACCOUNT-RECORD`) |
| `CVTRA01Y.cpy` | Copybook | Transaction category balance record (`TRAN-CAT-BAL-RECORD`) |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBTRN02C` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Post the records from daily transaction file |
| Source Version | CardDemo_v2.0-25-gdb72e6b-235, 2025-04-29 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field | Mode |
|---|---|---|---|---|---|
| `DALYTRAN-FILE` | `DALYTRAN` | Sequential | Sequential | N/A | INPUT |
| `TRANSACT-FILE` | `TRANFILE` | INDEXED (KSDS) | Random | `FD-TRANS-ID` PIC X(16) | OUTPUT |
| `XREF-FILE` | `XREFFILE` | INDEXED (KSDS) | Random | `FD-XREF-CARD-NUM` PIC X(16) | INPUT |
| `DALYREJS-FILE` | `DALYREJS` | Sequential | Sequential | N/A | OUTPUT |
| `ACCOUNT-FILE` | `ACCTFILE` | INDEXED (KSDS) | Random | `FD-ACCT-ID` PIC 9(11) | I-O |
| `TCATBAL-FILE` | `TCATBALF` | INDEXED (KSDS) | Random | `FD-TRAN-CAT-KEY` (composite) | I-O |

---

## 5. File Section — Record Layouts

### 5.1 DALYTRAN-FILE (Input)
```
01 FD-TRAN-RECORD.
   05 FD-TRAN-ID      PIC X(16)
   05 FD-CUST-DATA    PIC X(334)
```
Total: 350 bytes. Read INTO `DALYTRAN-RECORD` (CVTRA06Y).

### 5.2 TRANSACT-FILE (Output)
```
01 FD-TRANFILE-REC.
   05 FD-TRANS-ID     PIC X(16)
   05 FD-ACCT-DATA    PIC X(334)
```
Total: 350 bytes. Written FROM `TRAN-RECORD` (CVTRA05Y).

### 5.3 DALYREJS-FILE (Output)
```
01 FD-REJS-RECORD.
   05 FD-REJECT-RECORD         PIC X(350)   [Full DALYTRAN-RECORD copy]
   05 FD-VALIDATION-TRAILER    PIC X(80)    [Reason code + description]
```
Total: 430 bytes.

### 5.4 ACCOUNT-FILE (I-O)
```
01 FD-ACCTFILE-REC.
   05 FD-ACCT-ID      PIC 9(11)
   05 FD-ACCT-DATA    PIC X(289)
```
Total: 300 bytes. Read INTO / REWRITE FROM `ACCOUNT-RECORD` (CVACT01Y).

### 5.5 TCATBAL-FILE (I-O)
```
01 FD-TRAN-CAT-BAL-RECORD.
   05 FD-TRAN-CAT-KEY.
      10 FD-TRANCAT-ACCT-ID    PIC 9(11)
      10 FD-TRANCAT-TYPE-CD    PIC X(02)
      10 FD-TRANCAT-CD         PIC 9(04)
   05 FD-FD-TRAN-CAT-DATA      PIC X(33)
```
Total: 50 bytes. Read INTO / WRITE / REWRITE FROM `TRAN-CAT-BAL-RECORD` (CVTRA01Y).

---

## 6. Copybooks Referenced

| Copybook | Working-Storage Record | Key Fields |
|---|---|---|
| `CVTRA06Y` | `DALYTRAN-RECORD` | `DALYTRAN-CARD-NUM` X(16), `DALYTRAN-AMT` S9(09)V99, `DALYTRAN-ORIG-TS` X(26), `DALYTRAN-TYPE-CD`, `DALYTRAN-CAT-CD` |
| `CVTRA05Y` | `TRAN-RECORD` | `TRAN-ID`, `TRAN-TYPE-CD`, `TRAN-CAT-CD`, `TRAN-AMT`, `TRAN-CARD-NUM`, `TRAN-ORIG-TS`, `TRAN-PROC-TS` |
| `CVACT03Y` | `CARD-XREF-RECORD` | `XREF-CARD-NUM`, `XREF-ACCT-ID` 9(11) |
| `CVACT01Y` | `ACCOUNT-RECORD` | `ACCT-CURR-BAL`, `ACCT-CREDIT-LIMIT`, `ACCT-CURR-CYC-CREDIT`, `ACCT-CURR-CYC-DEBIT`, `ACCT-EXPIRAION-DATE` |
| `CVTRA01Y` | `TRAN-CAT-BAL-RECORD` | `TRANCAT-ACCT-ID`, `TRANCAT-TYPE-CD`, `TRANCAT-CD`, `TRAN-CAT-BAL` S9(09)V99 |

---

## 7. Working-Storage Data Structures

### 7.1 Timestamp Fields
```
01 COBOL-TS.
   05 COB-YYYY/MM/DD/HH/MIN/SS/MIL/REST

01 DB2-FORMAT-TS    PIC X(26)   [YYYY-MM-DD-HH.MM.SS.cc0000]
   REDEFINES with DB2-YYYY/MM/DD/HH/MIN/SS/MIL/REST and separators
```

### 7.2 Reject Record
```
01 REJECT-RECORD.
   05 REJECT-TRAN-DATA         PIC X(350)
   05 VALIDATION-TRAILER       PIC X(80)

01 WS-VALIDATION-TRAILER.
   05 WS-VALIDATION-FAIL-REASON       PIC 9(04)   [0 = valid; non-zero = error code]
   05 WS-VALIDATION-FAIL-REASON-DESC  PIC X(76)
```

### 7.3 Counters and Flags
```
01 WS-COUNTERS.
   05 WS-TRANSACTION-COUNT    PIC 9(09) VALUE 0   [Total transactions read]
   05 WS-REJECT-COUNT         PIC 9(09) VALUE 0   [Total rejected transactions]
   05 WS-TEMP-BAL             PIC S9(09)V99        [Temporary balance for overlimit check]

01 WS-FLAGS.
   05 WS-CREATE-TRANCAT-REC   PIC X(01) VALUE 'N'  ['Y' = create new TCATBAL record]
```

---

## 8. Procedure Division — Program Flow

### 8.1 Main Control (lines 193–234)
```
DISPLAY 'START OF EXECUTION OF PROGRAM CBTRN02C'
PERFORM 0000-DALYTRAN-OPEN
PERFORM 0100-TRANFILE-OPEN      [OUTPUT]
PERFORM 0200-XREFFILE-OPEN      [INPUT]
PERFORM 0300-DALYREJS-OPEN      [OUTPUT]
PERFORM 0400-ACCTFILE-OPEN      [I-O]
PERFORM 0500-TCATBALF-OPEN      [I-O]

PERFORM UNTIL END-OF-FILE = 'Y'
    IF END-OF-FILE = 'N'
        PERFORM 1000-DALYTRAN-GET-NEXT
        IF END-OF-FILE = 'N'
            ADD 1 TO WS-TRANSACTION-COUNT
            MOVE 0 TO WS-VALIDATION-FAIL-REASON
            MOVE SPACES TO WS-VALIDATION-FAIL-REASON-DESC
            PERFORM 1500-VALIDATE-TRAN
            IF WS-VALIDATION-FAIL-REASON = 0
                PERFORM 2000-POST-TRANSACTION
            ELSE
                ADD 1 TO WS-REJECT-COUNT
                PERFORM 2500-WRITE-REJECT-REC
            END-IF
        END-IF
    END-IF
END-PERFORM

PERFORM 9000-9500 (close all files)
DISPLAY 'TRANSACTIONS PROCESSED: ' WS-TRANSACTION-COUNT
DISPLAY 'TRANSACTIONS REJECTED:  ' WS-REJECT-COUNT
IF WS-REJECT-COUNT > 0
    MOVE 4 TO RETURN-CODE
END-IF
DISPLAY 'END OF EXECUTION OF PROGRAM CBTRN02C'
GOBACK
```

### 8.2 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `0000-DALYTRAN-OPEN` | 236–252 | Opens DALYTRAN-FILE INPUT. Abends on failure. |
| `0100-TRANFILE-OPEN` | 254–270 | Opens TRANSACT-FILE OUTPUT. Abends on failure. **Note: OUTPUT mode destroys existing content.** |
| `0200-XREFFILE-OPEN` | 273–289 | Opens XREF-FILE INPUT. |
| `0300-DALYREJS-OPEN` | 291–307 | Opens DALYREJS-FILE OUTPUT. |
| `0400-ACCTFILE-OPEN` | 309–325 | Opens ACCOUNT-FILE **I-O**. Required for REWRITE operations. |
| `0500-TCATBALF-OPEN` | 327–343 | Opens TCATBAL-FILE **I-O**. Required for READ + WRITE/REWRITE operations. |
| `1000-DALYTRAN-GET-NEXT` | 345–369 | Reads next daily transaction. EOF -> END-OF-FILE='Y'; error -> abend. |
| `1500-VALIDATE-TRAN` | 370–378 | Calls 1500-A-LOOKUP-XREF; if no error, calls 1500-B-LOOKUP-ACCT. |
| `1500-A-LOOKUP-XREF` | 380–392 | Keyed READ of XREF-FILE by DALYTRAN-CARD-NUM. INVALID KEY: sets WS-VALIDATION-FAIL-REASON=100, message='INVALID CARD NUMBER FOUND'. |
| `1500-B-LOOKUP-ACCT` | 393–422 | Keyed READ of ACCOUNT-FILE by XREF-ACCT-ID. INVALID KEY: reason=101, 'ACCOUNT RECORD NOT FOUND'. If found: checks overlimit (reason=102) and expiration (reason=103). |
| `2000-POST-TRANSACTION` | 424–444 | Maps DALYTRAN fields to TRAN-RECORD. Sets TRAN-PROC-TS from Z-GET-DB2-FORMAT-TIMESTAMP. Calls 2700-UPDATE-TCATBAL, 2800-UPDATE-ACCOUNT-REC, 2900-WRITE-TRANSACTION-FILE. |
| `2500-WRITE-REJECT-REC` | 446–465 | Moves DALYTRAN-RECORD to REJECT-TRAN-DATA, moves WS-VALIDATION-TRAILER to VALIDATION-TRAILER. WRITEs FD-REJS-RECORD FROM REJECT-RECORD. Abends on write failure. |
| `2700-UPDATE-TCATBAL` | 467–501 | Sets FD-TRAN-CAT-KEY from XREF-ACCT-ID + DALYTRAN-TYPE-CD + DALYTRAN-CAT-CD. Reads TCATBAL-FILE. Status '23' (not found): sets WS-CREATE-TRANCAT-REC='Y'. If 'Y': calls 2700-A-CREATE-TCATBAL-REC. Else: calls 2700-B-UPDATE-TCATBAL-REC. |
| `2700-A-CREATE-TCATBAL-REC` | 503–524 | INITIALIZEs TRAN-CAT-BAL-RECORD. Populates key fields and sets TRAN-CAT-BAL = 0 + DALYTRAN-AMT. WRITE new record to TCATBAL-FILE. |
| `2700-B-UPDATE-TCATBAL-REC` | 526–542 | Adds DALYTRAN-AMT to existing TRAN-CAT-BAL. REWRITE TCATBAL-FILE record. |
| `2800-UPDATE-ACCOUNT-REC` | 545–560 | Adds DALYTRAN-AMT to ACCT-CURR-BAL. If positive: adds to ACCT-CURR-CYC-CREDIT. If negative: adds to ACCT-CURR-CYC-DEBIT. REWRITE ACCOUNT-FILE record. On INVALID KEY sets reason=109 but does NOT abend — defect. |
| `2900-WRITE-TRANSACTION-FILE` | 562–579 | WRITE FD-TRANFILE-REC FROM TRAN-RECORD to TRANSACT-FILE. Abends on write failure. |
| `Z-GET-DB2-FORMAT-TIMESTAMP` | (same pattern as CBACT04C) | FUNCTION CURRENT-DATE to DB2 timestamp format. |
| `9000-9500` | (close paragraphs) | Close all 6 files. Each abends on close failure. |
| `9910-DISPLAY-IO-STATUS` | — | Standard 4-digit status display. |
| `9999-ABEND-PROGRAM` | — | CEE3ABD with ABCODE=999. |

---

## 9. Validation Rules

| Rule | Failure Code | Condition | Message |
|---|---|---|---|
| Card number valid | 100 | Card number not found in XREFFILE | 'INVALID CARD NUMBER FOUND' |
| Account exists | 101 | Account ID from XREF not found in ACCTFILE | 'ACCOUNT RECORD NOT FOUND' |
| Overlimit check | 102 | (ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT) > ACCT-CREDIT-LIMIT | 'OVERLIMIT TRANSACTION' |
| Expiration check | 103 | ACCT-EXPIRAION-DATE < DALYTRAN-ORIG-TS(1:10) | 'TRANSACTION RECEIVED AFTER ACCT EXPIRATION' |

**Overlimit formula (lines 403–408):**
```
WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL -> valid
ELSE -> reason 102 'OVERLIMIT TRANSACTION'
```
Note: Both validation rules 102 and 103 are checked in sequence within the NOT INVALID KEY branch. If the account is found and the overlimit check sets reason=102, the expiration check at lines 414–419 still runs. If the expiration also fails, it overwrites reason 102 with reason 103. Only the last-checked failure code is stored.

---

## 10. Transaction Posting Operations

For each valid transaction, three updates are performed:

1. **TCATBAL Update (2700):** The running balance for the account/type/category combination is updated. If no record exists yet for this key, a new one is created (CREATE path). If it exists, it is REWRITEn (UPDATE path).

2. **Account Update (2800):** ACCT-CURR-BAL is incremented by the transaction amount. The cycle credit/debit fields are updated based on the sign of the transaction: positive amounts add to cycle credit; negative amounts add to cycle debit.

3. **Transaction Record Write (2900):** A new record is written to TRANSACT-FILE with the DALYTRAN data plus a processing timestamp.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| File open failure | Status != '00' | DISPLAY error, 9910-DISPLAY-IO-STATUS, 9999-ABEND-PROGRAM |
| DALYTRAN read error | APPL-RESULT = 12 | DISPLAY error, abend |
| Validation failure | WS-VALIDATION-FAIL-REASON != 0 | Write to DALYREJS-FILE, continue |
| TCATBAL read error (not '00' or '23') | APPL-RESULT = 12 | DISPLAY error, abend |
| TCATBAL write/rewrite failure | Status != '00' | DISPLAY error, abend |
| Account rewrite failure | INVALID KEY on REWRITE | Sets reason=109, but does NOT abend — processing continues |
| Transaction write failure | Status != '00' | DISPLAY error, abend |
| Reject write failure | Status != '00' | DISPLAY error, abend |

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion, no rejects | 0 (RETURN-CODE not set) |
| Normal completion with rejects | 4 (MOVE 4 TO RETURN-CODE, line 230) |
| Fatal I/O error | U0999 abend via CEE3ABD |

---

## 13. Data Flow Diagram

```
DALYTRAN (sequential) ---> 1500-VALIDATE-TRAN
                                   |
                    +--------------+---------------+
                    |                              |
                  VALID                        INVALID
                    |                              |
                    v                              v
         2000-POST-TRANSACTION             DALYREJS (reject file)
              |         |
              v         v
       TCATBAL-FILE  ACCOUNT-FILE      TRANSACT-FILE
       (create or   (rewrite balance)  (write new record)
        rewrite bal)
```

---

## 14. Known Defects

1. **Account REWRITE failure (line 555–558):** When `REWRITE FD-ACCTFILE-REC FROM ACCOUNT-RECORD` has an INVALID KEY, the code sets `WS-VALIDATION-FAIL-REASON = 109` but does not ABEND or write a reject record. Processing continues. The transaction is still written to TRANSACT-FILE and TCATBAL is still updated, but the account master record is not updated. This creates an inconsistency between posted transactions and account balances.

2. **TRANSACT-FILE opened OUTPUT:** The transaction file is opened in OUTPUT mode (paragraph 0100-TRANFILE-OPEN, line 256). This means the entire transaction history file is replaced on every run. This appears intentional for a daily posting cycle but means re-running the job would destroy previously posted transactions.

3. **Overlimit check uses CYC fields only:** The overlimit formula uses `ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT` rather than `ACCT-CURR-BAL`. This means the check is based on within-cycle credits/debits, not the total outstanding balance. A customer with a large pre-cycle balance could still be approved for additional charges.
