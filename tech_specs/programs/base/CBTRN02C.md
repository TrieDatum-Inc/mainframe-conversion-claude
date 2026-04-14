# Technical Specification: CBTRN02C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | CBTRN02C                                             |
| Source File      | app/cbl/CBTRN02C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | Batch COBOL Program                                  |
| Transaction ID   | N/A (batch)                                          |
| Function         | Daily transaction posting. Reads DALYTRAN (sequential daily transaction file), validates each transaction, and either posts valid transactions to TRANSACT-FILE and updates ACCOUNT-FILE and TCATBAL-FILE, or writes rejected transactions (with reason code and description) to DALYREJS-FILE. Sets RETURN-CODE=4 if any rejections occur. |

---

## 2. Program Flow

### High-Level Flow

```
START
  OPEN INPUT: DALYTRAN-FILE
  OPEN OUTPUT: TRANSACT-FILE, DALYREJS-FILE
  OPEN INPUT: XREF-FILE
  OPEN I-O:   ACCOUNT-FILE, TCATBAL-FILE

  PERFORM UNTIL END-OF-FILE = 'Y':
      1000-DALYTRAN-GET-NEXT (READ DALYTRAN-FILE)
      IF not EOF:
          ADD 1 TO WS-TRANSACTION-COUNT
          MOVE 0 TO WS-VALIDATION-FAIL-REASON
          PERFORM 1500-VALIDATE-TRAN
              1500-A-LOOKUP-XREF (READ XREF by DALYTRAN-CARD-NUM)
              IF xref OK: 1500-B-LOOKUP-ACCT (READ ACCOUNT, check limit+expiry)
          IF WS-VALIDATION-FAIL-REASON = 0:
              PERFORM 2000-POST-TRANSACTION
                  Map DALYTRAN-* fields to TRAN-RECORD
                  Set TRAN-PROC-TS = DB2-FORMAT-TS (current timestamp)
                  2700-UPDATE-TCATBAL (READ/WRITE or REWRITE TCATBAL-FILE)
                  2800-UPDATE-ACCOUNT-REC (ADD DALYTRAN-AMT; REWRITE ACCOUNT)
                  2900-WRITE-TRANSACTION-FILE (WRITE TRAN-RECORD)
          ELSE:
              ADD 1 TO WS-REJECT-COUNT
              2500-WRITE-REJECT-REC (WRITE reject + WS-VALIDATION-TRAILER to DALYREJS)

  CLOSE: all 6 files
  DISPLAY statistics
  IF WS-REJECT-COUNT > 0: MOVE 4 TO RETURN-CODE
STOP
```

### Paragraph-Level Detail

| Paragraph               | Lines     | Description |
|-------------------------|-----------|-------------|
| PROCEDURE DIVISION      | 193–234   | Opens all 6 files; runs main loop; closes; displays stats; sets RETURN-CODE=4 if rejects; GOBACK |
| 0000-DALYTRAN-OPEN      | 236–252   | OPEN INPUT DALYTRAN-FILE; abend on failure |
| 0100-TRANFILE-OPEN      | 254–270   | OPEN OUTPUT TRANSACT-FILE; abend on failure |
| 0200-XREFFILE-OPEN      | 272–289   | OPEN INPUT XREF-FILE; abend on failure |
| 0300-DALYREJS-OPEN      | 291–307   | OPEN OUTPUT DALYREJS-FILE; abend on failure |
| 0400-ACCTFILE-OPEN      | 309–325   | OPEN I-O ACCOUNT-FILE; abend on failure |
| 0500-TCATBALF-OPEN      | 327–343   | OPEN I-O TCATBAL-FILE; abend on failure |
| 1000-DALYTRAN-GET-NEXT  | 345–369   | READ DALYTRAN-FILE INTO DALYTRAN-RECORD; set EOF or abend |
| 1500-VALIDATE-TRAN      | 370–378   | Calls 1500-A-LOOKUP-XREF then 1500-B-LOOKUP-ACCT if xref OK; comment: "ADD MORE VALIDATIONS HERE" |
| 1500-A-LOOKUP-XREF      | 380–392   | READ XREF-FILE by DALYTRAN-CARD-NUM; INVALID KEY: WS-VALIDATION-FAIL-REASON=100, 'INVALID CARD NUMBER FOUND' |
| 1500-B-LOOKUP-ACCT      | 393–422   | READ ACCOUNT-FILE by XREF-ACCT-ID; INVALID KEY: reason=101; if found: compute WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT; check credit limit (reason=102); check expiry (reason=103) |
| 2000-POST-TRANSACTION   | 424–444   | Maps all DALYTRAN-* fields to TRAN-RECORD; calls Z-GET-DB2-FORMAT-TIMESTAMP; sets TRAN-PROC-TS; calls 2700, 2800, 2900 |
| 2500-WRITE-REJECT-REC   | 446–465   | MOVE DALYTRAN-RECORD to REJECT-TRAN-DATA; MOVE WS-VALIDATION-TRAILER to VALIDATION-TRAILER; WRITE DALYREJS record; abend on write failure |
| 2700-UPDATE-TCATBAL     | 467–501   | MOVE composite key (XREF-ACCT-ID + TYPE-CD + CAT-CD) to FD-TRAN-CAT-KEY; READ TCATBAL-FILE; if INVALID KEY (status '23'): PERFORM 2700-A-CREATE-TCATBAL-REC; else: PERFORM 2700-B-UPDATE-TCATBAL-REC |
| 2700-A-CREATE-TCATBAL-REC | 503–524 | INITIALIZE TRAN-CAT-BAL-RECORD; populate; ADD DALYTRAN-AMT TO TRAN-CAT-BAL; WRITE new TCATBAL record |
| 2700-B-UPDATE-TCATBAL-REC | 526–542 | ADD DALYTRAN-AMT TO TRAN-CAT-BAL; REWRITE TCATBAL record |
| 2800-UPDATE-ACCOUNT-REC | 545–560   | ADD DALYTRAN-AMT TO ACCT-CURR-BAL; if positive: ADD to ACCT-CURR-CYC-CREDIT; if negative: ADD to ACCT-CURR-CYC-DEBIT; REWRITE ACCOUNT-FILE |
| 2900-WRITE-TRANSACTION-FILE | 562–579 | WRITE FD-TRANFILE-REC FROM TRAN-RECORD; abend on failure |
| 9000–9500-*-CLOSE       | 582–~680  | Close all 6 files; abend on failure |
| Z-GET-DB2-FORMAT-TIMESTAMP | ~680+  | Build DB2-FORMAT-TS from FUNCTION CURRENT-DATE |
| 9910-DISPLAY-IO-STATUS  | ~700+     | Standard I/O status display routine |
| 9999-ABEND-PROGRAM      | ~720+     | CALL 'CEE3ABD' USING ABCODE, TIMING |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Used In              | Contents |
|----------|----------------------|----------|
| CVTRA06Y | WORKING-STORAGE (line 102) | DALYTRAN-RECORD layout: DALYTRAN-ID X(16), DALYTRAN-CARD-NUM X(16), DALYTRAN-TYPE-CD X(2), DALYTRAN-CAT-CD 9(4), DALYTRAN-SOURCE X(10), DALYTRAN-DESC X(100), DALYTRAN-AMT S9(9)V99, DALYTRAN-MERCHANT-ID 9(9), DALYTRAN-MERCHANT-NAME X(50), DALYTRAN-MERCHANT-CITY X(50), DALYTRAN-MERCHANT-ZIP X(10), DALYTRAN-ORIG-TS X(26) — **[UNRESOLVED]** complete layout requires app/cpy/CVTRA06Y.cpy |
| CVTRA05Y | WORKING-STORAGE (line 107) | TRAN-RECORD (350 bytes): output transaction record |
| CVACT03Y | WORKING-STORAGE (line 112) | CARD-XREF-RECORD (50 bytes): XREF-CARD-NUM, XREF-CUST-ID, XREF-ACCT-ID |
| CVACT01Y | WORKING-STORAGE (line 121) | ACCOUNT-RECORD (300 bytes): ACCT-ID, balances, credit limits, dates |
| CVTRA01Y | WORKING-STORAGE (line 126) | TRAN-CAT-BAL-RECORD: TRANCAT-ACCT-ID 9(11), TRANCAT-TYPE-CD X(2), TRANCAT-CD 9(4), TRAN-CAT-BAL |

### File Description Records

| FD Name       | DD Name   | Key                           | Mode  |
|---------------|-----------|-------------------------------|-------|
| DALYTRAN-FILE | DALYTRAN  | Sequential                    | INPUT |
| TRANSACT-FILE | TRANFILE  | FD-TRANS-ID X(16)             | OUTPUT |
| XREF-FILE     | XREFFILE  | FD-XREF-CARD-NUM X(16)        | INPUT |
| DALYREJS-FILE | DALYREJS  | Sequential                    | OUTPUT |
| ACCOUNT-FILE  | ACCTFILE  | FD-ACCT-ID 9(11)              | I-O |
| TCATBAL-FILE  | TCATBALF  | FD-TRAN-CAT-KEY (composite: ACCT-ID 9(11)+TYPE-CD X(2)+CAT-CD 9(4)) | I-O |

### Key Working Storage Variables

| Variable                       | PIC       | Purpose |
|--------------------------------|-----------|---------|
| WS-VALIDATION-FAIL-REASON      | 9(04)     | 0=valid; 100=invalid card; 101=account not found; 102=overlimit; 103=expired |
| WS-VALIDATION-FAIL-REASON-DESC | X(76)     | Descriptive text for rejection reason |
| REJECT-RECORD                  | Group     | REJECT-TRAN-DATA X(350) + VALIDATION-TRAILER X(80) written to DALYREJS |
| WS-VALIDATION-TRAILER          | Group     | WS-VALIDATION-FAIL-REASON 9(04) + WS-VALIDATION-FAIL-REASON-DESC X(76) |
| WS-TRANSACTION-COUNT           | 9(09)     | Total records read from DALYTRAN |
| WS-REJECT-COUNT                | 9(09)     | Total records rejected |
| WS-TEMP-BAL                    | S9(09)V99 | Computed prospective balance for credit limit check |
| WS-CREATE-TRANCAT-REC          | X(01)     | 'Y' if TCATBAL record must be created (not found); 'N' if update |
| DB2-FORMAT-TS                  | X(26)     | Current timestamp in YYYY-MM-DD-HH.MM.SS.mmm0000 format |
| COBOL-TS                       | Group     | Receives FUNCTION CURRENT-DATE (21 chars) |
| END-OF-FILE                    | X(01)     | Loop control; 'Y' on DALYTRAN EOF |
| APPL-RESULT                    | S9(9) COMP | 0=AOK, 16=EOF, 12=error |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name   | File Object    | Org        | Access  | Open Mode | Purpose |
|-----------|----------------|------------|---------|-----------|---------|
| DALYTRAN  | DALYTRAN-FILE  | Sequential | Sequential | INPUT  | Driving file: daily transaction records |
| TRANFILE  | TRANSACT-FILE  | KSDS       | Random  | OUTPUT    | Write posted transaction records |
| XREFFILE  | XREF-FILE      | KSDS       | Random  | INPUT     | Look up card-to-account cross-reference |
| DALYREJS  | DALYREJS-FILE  | Sequential | Sequential | OUTPUT | Write rejected transaction records + trailers |
| ACCTFILE  | ACCOUNT-FILE   | KSDS       | Random  | I-O       | Read account for validation; REWRITE to update balances |
| TCATBALF  | TCATBAL-FILE   | KSDS       | Random  | I-O       | Read category balance; WRITE if new or REWRITE if existing |

---

## 6. Screen Interaction

None. Batch program.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| CEE3ABD        | Static CALL | LE forced abend |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| Any OPEN failure | DISPLAY error; 9910-DISPLAY-IO-STATUS; 9999-ABEND-PROGRAM |
| DALYTRAN read error (non-00/10) | DISPLAY 'ERROR READING DALYTRAN FILE'; abend |
| DALYTRAN EOF | MOVE 'Y' TO END-OF-FILE |
| XREF INVALID KEY | WS-VALIDATION-FAIL-REASON=100; reject record written |
| ACCOUNT INVALID KEY | WS-VALIDATION-FAIL-REASON=101; reject record |
| Overlimit | WS-VALIDATION-FAIL-REASON=102; reject record |
| Account expired | WS-VALIDATION-FAIL-REASON=103; reject record |
| DALYREJS write failure | DISPLAY error; 9910; abend |
| TCATBAL read error (non-00/23) | DISPLAY error; 9910; abend |
| TCATBAL write failure (new record) | DISPLAY 'ERROR WRITING TRANSACTION BALANCE FILE'; abend |
| TCATBAL rewrite failure | DISPLAY 'ERROR REWRITING TRANSACTION BALANCE FILE'; abend |
| ACCOUNT REWRITE failure | WS-VALIDATION-FAIL-REASON=109; MOVE 'ACCOUNT RECORD NOT FOUND' (no explicit abend at this point — uses INVALID KEY clause) |
| TRANSACT WRITE failure | DISPLAY 'ERROR WRITING TO TRANSACTION FILE'; abend |
| Any CLOSE failure | DISPLAY error; abend |
| WS-REJECT-COUNT > 0 at end | MOVE 4 TO RETURN-CODE (signals partial failure to JCL) |

---

## 9. Business Rules

1. **Validation sequence**: 1500-VALIDATE-TRAN calls XREF lookup first; only if card is valid does it proceed to account lookup and balance checks. The comment at line 377 ('ADD MORE VALIDATIONS HERE') indicates the validation framework is designed for extension.
2. **Rejection codes**: Code 100=invalid card, 101=account not found, 102=overlimit, 103=account expired. Each rejection writes a 430-byte record (350 bytes of original DALYTRAN data + 80 bytes of trailer) to DALYREJS.
3. **TCATBAL create-or-update**: If the transaction category balance record does not exist (INVALID KEY on read), it is created new (2700-A). If it exists, TRAN-CAT-BAL is incremented and the record is rewritten (2700-B).
4. **Account balance update**: DALYTRAN-AMT is added to ACCT-CURR-BAL unconditionally. Additionally: positive amounts increment ACCT-CURR-CYC-CREDIT; negative amounts increment ACCT-CURR-CYC-DEBIT.
5. **TRAN-PROC-TS set to current time**: Unlike TRAN-ORIG-TS (which is copied from DALYTRAN-ORIG-TS), TRAN-PROC-TS is set to the current execution timestamp via Z-GET-DB2-FORMAT-TIMESTAMP.
6. **RETURN-CODE signaling**: MOVE 4 TO RETURN-CODE if any rejects exist. This allows downstream JCL steps to use COND=(4,GE) to bypass or route based on rejection presence.
7. **TRANSACT-FILE opened OUTPUT**: TRANSACT-FILE is opened OUTPUT (not I-O) meaning this is a pure append/create run — the output transaction file is created or replaced in this step.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| DALYTRAN  | Sequential daily transaction file (driving input) |
| XREFFILE  | KSDS cross-reference: card number to account/customer mapping |
| ACCTFILE  | KSDS account master: balance, credit limit, expiry date |

### Outputs

| Destination | Record Type   | Description |
|-------------|---------------|-------------|
| TRANFILE    | TRAN-RECORD   | Posted transaction records (valid transactions only) |
| DALYREJS    | REJECT-RECORD | Rejected transactions (350 bytes) + validation trailer (80 bytes) |
| ACCTFILE    | ACCOUNT-RECORD | REWRITE: updated ACCT-CURR-BAL, ACCT-CURR-CYC-CREDIT, ACCT-CURR-CYC-DEBIT |
| TCATBALF    | TRAN-CAT-BAL-RECORD | New record (WRITE) or updated balance (REWRITE) per account/type/category |
| SYSOUT      | DISPLAY       | Transaction/reject counts; RETURN-CODE=4 if rejects |

---

## 11. Key Variables and Their Purpose

| Variable                    | Purpose |
|-----------------------------|---------|
| DALYTRAN-RECORD             | Working area for each input transaction (from CVTRA06Y) |
| WS-VALIDATION-FAIL-REASON   | Non-zero value identifies reason for rejection; 0 means valid |
| WS-VALIDATION-FAIL-REASON-DESC | Text appended to reject record trailer |
| WS-TEMP-BAL                 | Prospective balance computed during credit-limit check (CYC-CREDIT - CYC-DEBIT + tran amount) |
| WS-CREATE-TRANCAT-REC       | Flag: 'Y' = TCATBAL record not found and must be created; 'N' = update existing |
| DB2-FORMAT-TS               | Current timestamp in DB2 format; set as TRAN-PROC-TS on posted transactions |
| REJECT-RECORD               | 430-byte record written to DALYREJS: raw DALYTRAN data + reason code + description |
| WS-REJECT-COUNT             | Count driving RETURN-CODE=4 at end of run |
