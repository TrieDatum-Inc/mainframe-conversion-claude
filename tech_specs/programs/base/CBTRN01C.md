# Technical Specification: CBTRN01C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | CBTRN01C                                             |
| Source File      | app/cbl/CBTRN01C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | Batch COBOL Program                                  |
| Transaction ID   | N/A (batch)                                          |
| Function         | Daily transaction verification. Reads DALYTRAN (sequential daily transaction file) and for each transaction: (1) looks up the card number in XREFFILE to obtain the account ID, (2) reads the account record from ACCTFILE to verify it exists. Does not post or modify any data. Opens CUSTFILE, CARDFILE, and TRANSACT-FILE but never reads or writes to them — these three files appear to be opened for reference/compatibility purposes only. |

---

## 2. Program Flow

### High-Level Flow

```
START
  OPEN INPUT: DALYTRAN-FILE, CUSTOMER-FILE, XREF-FILE,
              CARD-FILE, ACCOUNT-FILE, TRANSACT-FILE (6 files INPUT)

  PERFORM UNTIL END-OF-DAILY-TRANS-FILE = 'Y':
      1000-DALYTRAN-GET-NEXT
          READ DALYTRAN-FILE INTO DALYTRAN-RECORD
          IF status '10': set END-OF-DAILY-TRANS-FILE = 'Y'
      IF not EOF:
          DISPLAY DALYTRAN-RECORD
          MOVE DALYTRAN-CARD-NUM TO XREF-CARD-NUM
          PERFORM 2000-LOOKUP-XREF
              READ XREF-FILE by FD-XREF-CARD-NUM (INVALID KEY: log)
          IF XREF lookup OK (WS-XREF-READ-STATUS = 0):
              MOVE XREF-ACCT-ID TO ACCT-ID
              PERFORM 3000-READ-ACCOUNT
                  READ ACCOUNT-FILE by FD-ACCT-ID (INVALID KEY: log)
          ELSE:
              DISPLAY card number could not be verified

  CLOSE: all 6 files
STOP
```

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| MAIN-PARA              | 155–197   | Opens 6 files; runs main loop; closes 6 files; GOBACK |
| 1000-DALYTRAN-GET-NEXT | 202–225   | READ DALYTRAN-FILE INTO DALYTRAN-RECORD; sets APPL-RESULT to 0/16/12; sets END-OF-DAILY-TRANS-FILE='Y' on EOF; calls Z-ABEND-PROGRAM on error |
| 2000-LOOKUP-XREF       | 227–239   | MOVE XREF-CARD-NUM TO FD-XREF-CARD-NUM; READ XREF-FILE RECORD KEY IS FD-XREF-CARD-NUM; INVALID KEY sets WS-XREF-READ-STATUS=4; NOT INVALID KEY DISPLAYs XREF fields |
| 3000-READ-ACCOUNT      | 241–250   | MOVE ACCT-ID TO FD-ACCT-ID; READ ACCOUNT-FILE KEY IS FD-ACCT-ID; INVALID KEY sets WS-ACCT-READ-STATUS=4 |
| 0000-DALYTRAN-OPEN     | 252–268   | OPEN INPUT DALYTRAN-FILE; abends on failure |
| 0100-CUSTFILE-OPEN     | 271–287   | OPEN INPUT CUSTOMER-FILE; abends on failure |
| 0200-XREFFILE-OPEN     | 289–305   | OPEN INPUT XREF-FILE; abends on failure |
| 0300-CARDFILE-OPEN     | 307–323   | OPEN INPUT CARD-FILE; abends on failure |
| 0400-ACCTFILE-OPEN     | 325–341   | OPEN INPUT ACCOUNT-FILE; abends on failure |
| 0500-TRANFILE-OPEN     | 343–359   | OPEN INPUT TRANSACT-FILE; abends on failure |
| 9000-DALYTRAN-CLOSE    | 361–377   | CLOSE DALYTRAN-FILE; abends on failure (note: error message says 'CLOSING CUSTOMER FILE' — copy/paste error in source) |
| 9100-CUSTFILE-CLOSE    | 379–395   | CLOSE CUSTOMER-FILE |
| 9200-XREFFILE-CLOSE    | 397–413   | CLOSE XREF-FILE |
| 9300-CARDFILE-CLOSE    | 415–431   | CLOSE CARD-FILE |
| 9400-ACCTFILE-CLOSE    | 433–449   | CLOSE ACCOUNT-FILE |
| 9500-TRANFILE-CLOSE    | 451–467   | CLOSE TRANSACT-FILE |
| Z-ABEND-PROGRAM        | 469–473   | MOVE 0 TO TIMING; MOVE 999 TO ABCODE; CALL 'CEE3ABD' USING ABCODE, TIMING |
| Z-DISPLAY-IO-STATUS    | 476–489   | Formats and displays 4-character I/O status; handles VSAM physical error (IO-STAT1='9') |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Used In              | Contents |
|----------|----------------------|----------|
| CVTRA06Y | WORKING-STORAGE (line 99) | DALYTRAN-RECORD layout: DALYTRAN-ID X(16), DALYTRAN-CARD-NUM X(16), and other daily transaction fields — **[UNRESOLVED]** complete field layout requires reading app/cpy/CVTRA06Y.cpy |
| CVCUS01Y | WORKING-STORAGE (line 104) | CUSTOMER-RECORD (500 bytes): CUST-ID 9(9), name/address/SSN/DOB/FICO fields |
| CVACT03Y | WORKING-STORAGE (line 109) | CARD-XREF-RECORD (50 bytes): XREF-CARD-NUM X(16), XREF-CUST-ID 9(9), XREF-ACCT-ID 9(11) |
| CVACT02Y | WORKING-STORAGE (line 114) | CARD-RECORD (150 bytes): CARD-NUM X(16), CARD-ACCT-ID 9(11), etc. |
| CVACT01Y | WORKING-STORAGE (line 119) | ACCOUNT-RECORD (300 bytes): ACCT-ID 9(11), balance, limits, dates |
| CVTRA05Y | WORKING-STORAGE (line 124) | TRAN-RECORD (350 bytes): TRAN-ID X(16), type/cat, amount, merchant fields, timestamps |

### File Description Records

| FD Name        | DD Name   | Key Field               | Record Layout |
|----------------|-----------|-------------------------|---------------|
| DALYTRAN-FILE  | DALYTRAN  | N/A (sequential)        | FD-TRAN-ID X(16) + FD-CUST-DATA X(334) |
| CUSTOMER-FILE  | CUSTFILE  | FD-CUST-ID 9(09)        | FD-CUST-ID 9(9) + FD-CUST-DATA X(491) |
| XREF-FILE      | XREFFILE  | FD-XREF-CARD-NUM X(16)  | FD-XREF-CARD-NUM X(16) + FD-XREF-DATA X(34) |
| CARD-FILE      | CARDFILE  | FD-CARD-NUM X(16)       | FD-CARD-NUM X(16) + FD-CARD-DATA X(134) |
| ACCOUNT-FILE   | ACCTFILE  | FD-ACCT-ID 9(11)        | FD-ACCT-ID 9(11) + FD-ACCT-DATA X(289) |
| TRANSACT-FILE  | TRANFILE  | FD-TRANS-ID X(16)       | FD-TRANS-ID X(16) + FD-ACCT-DATA X(334) |

### Key Working Storage Variables

| Variable                    | PIC         | Purpose |
|-----------------------------|-------------|---------|
| DALYTRAN-STATUS             | X(2)        | File status for DALYTRAN-FILE |
| CUSTFILE-STATUS             | X(2)        | File status for CUSTOMER-FILE |
| XREFFILE-STATUS             | X(2)        | File status for XREF-FILE |
| CARDFILE-STATUS             | X(2)        | File status for CARD-FILE |
| ACCTFILE-STATUS             | X(2)        | File status for ACCOUNT-FILE |
| TRANFILE-STATUS             | X(2)        | File status for TRANSACT-FILE |
| IO-STATUS                   | X(2)        | Work area for Z-DISPLAY-IO-STATUS |
| APPL-RESULT                 | S9(9) COMP  | Result code: 0=AOK (88 APPL-AOK), 16=EOF (88 APPL-EOF) |
| END-OF-DAILY-TRANS-FILE     | X(01)       | Loop control: 'N'=continue, 'Y'=stop |
| WS-XREF-READ-STATUS         | 9(04)       | 0=xref found, 4=not found (INVALID KEY) |
| WS-ACCT-READ-STATUS         | 9(04)       | 0=account found, 4=not found (INVALID KEY) |
| ABCODE                      | S9(9) BINARY | Abend code = 999 |
| TIMING                      | S9(9) BINARY | Timing parameter for CEE3ABD = 0 |
| TWO-BYTES-BINARY            | 9(4) BINARY  | VSAM physical error status decoding |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name   | File Object    | Org        | Access     | Open Mode | Actual Usage |
|-----------|----------------|------------|------------|-----------|--------------|
| DALYTRAN  | DALYTRAN-FILE  | Sequential | Sequential | INPUT     | READ sequentially in main loop |
| CUSTFILE  | CUSTOMER-FILE  | KSDS       | Random     | INPUT     | Opened and closed; never read in PROCEDURE DIVISION |
| XREFFILE  | XREF-FILE      | KSDS       | Random     | INPUT     | READ by card number in 2000-LOOKUP-XREF |
| CARDFILE  | CARD-FILE      | KSDS       | Random     | INPUT     | Opened and closed; never read in PROCEDURE DIVISION |
| ACCTFILE  | ACCOUNT-FILE   | KSDS       | Random     | INPUT     | READ by account ID in 3000-READ-ACCOUNT |
| TRANFILE  | TRANSACT-FILE  | KSDS       | Random     | INPUT     | Opened and closed; never read in PROCEDURE DIVISION |

**Note**: CUSTOMER-FILE, CARD-FILE, and TRANSACT-FILE are opened and closed with no intervening reads or writes. This is likely placeholder code for a more complete verification function that was never implemented.

---

## 6. Screen Interaction

None. Output is DISPLAY to SYSOUT only.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| CEE3ABD        | Static CALL | LE forced abend (USING ABCODE, TIMING) |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| DALYTRAN open failure | DISPLAY error; Z-DISPLAY-IO-STATUS; Z-ABEND-PROGRAM |
| CUSTFILE open failure | DISPLAY error; Z-DISPLAY-IO-STATUS; Z-ABEND-PROGRAM |
| XREFFILE open failure | DISPLAY error; Z-DISPLAY-IO-STATUS; Z-ABEND-PROGRAM |
| CARDFILE open failure | DISPLAY error; Z-DISPLAY-IO-STATUS; Z-ABEND-PROGRAM |
| ACCTFILE open failure | DISPLAY error; Z-DISPLAY-IO-STATUS; Z-ABEND-PROGRAM |
| TRANFILE open failure | DISPLAY error; Z-DISPLAY-IO-STATUS; Z-ABEND-PROGRAM |
| DALYTRAN read error (non-00/10) | DISPLAY 'ERROR READING DAILY TRANSACTION FILE'; Z-DISPLAY-IO-STATUS; Z-ABEND-PROGRAM |
| DALYTRAN EOF (status '10') | MOVE 'Y' TO END-OF-DAILY-TRANS-FILE; exit loop normally |
| XREF INVALID KEY | DISPLAY 'INVALID CARD NUMBER FOR XREF'; MOVE 4 TO WS-XREF-READ-STATUS; continue (no abend) |
| XREF found | DISPLAY card/account/customer IDs |
| ACCOUNT INVALID KEY | DISPLAY 'INVALID ACCOUNT NUMBER FOUND'; MOVE 4 TO WS-ACCT-READ-STATUS; continue (no abend) |
| ACCOUNT found | DISPLAY 'SUCCESSFUL READ OF ACCOUNT FILE' |
| XREF not found | DISPLAY 'CARD NUMBER ... COULD NOT BE VERIFIED. SKIPPING TRANSACTION ID-...' |
| ACCOUNT not found | DISPLAY 'ACCOUNT ... NOT FOUND' |
| Any CLOSE failure | DISPLAY error; Z-DISPLAY-IO-STATUS; Z-ABEND-PROGRAM |

---

## 9. Business Rules

1. **Verification only — no posting**: CBTRN01C performs no writes to any dataset. It is a verification/cross-check program that confirms each daily transaction has a resolvable card number (via XREF) and a valid account (via ACCTFILE).
2. **Cascading INVALID KEY**: If the XREF lookup fails (WS-XREF-READ-STATUS = 4), the account lookup is skipped entirely. The card number verification failure is displayed, and the loop continues with the next DALYTRAN record.
3. **Unused files**: CUSTOMER-FILE, CARD-FILE, and TRANSACT-FILE are opened INPUT but never used. No reads or references exist in the PROCEDURE DIVISION beyond their open/close paragraphs. This is dead code from an incomplete implementation.
4. **DISPLAY-based output**: All results (successful XREF reads, account finds, errors) are written to SYSOUT via DISPLAY. There is no output file.
5. **Error message copy/paste defect**: In 9000-DALYTRAN-CLOSE (line 373), the error message reads 'ERROR CLOSING CUSTOMER FILE' even though it is closing DALYTRAN-FILE. Similarly, it references CUSTFILE-STATUS rather than DALYTRAN-STATUS in the error display path. This is a code defect in the source.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| DALYTRAN  | Sequential daily transaction file; each record contains at minimum DALYTRAN-ID X(16) and DALYTRAN-CARD-NUM X(16) (from CVTRA06Y) |
| XREFFILE  | KSDS; random read by card number to obtain account ID and customer ID |
| ACCTFILE  | KSDS; random read by account ID to confirm account existence |

### Outputs

| Destination | Description |
|-------------|-------------|
| SYSOUT      | DISPLAY of each DALYTRAN-RECORD; XREF lookup results (card/account/customer IDs); error messages for invalid card or account numbers |

---

## 11. Key Variables and Their Purpose

| Variable                 | Purpose |
|--------------------------|---------|
| DALYTRAN-RECORD          | Working area (from CVTRA06Y); populated by READ DALYTRAN-FILE INTO; DALYTRAN-CARD-NUM used as XREF lookup key |
| CARD-XREF-RECORD         | Working area (from CVACT03Y); populated by READ XREF-FILE INTO; XREF-ACCT-ID passed to account read |
| ACCOUNT-RECORD           | Working area (from CVACT01Y); populated by READ ACCOUNT-FILE INTO |
| END-OF-DAILY-TRANS-FILE  | Loop termination flag; set to 'Y' on DALYTRAN EOF |
| WS-XREF-READ-STATUS      | Non-zero value (4) if XREF card number not found; used to gate account lookup |
| WS-ACCT-READ-STATUS      | Non-zero value (4) if account not found; informational only |
| APPL-RESULT              | Maps DALYTRAN file status to application result codes (0=OK, 16=EOF, 12=error) |
