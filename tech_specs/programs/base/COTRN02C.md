# Technical Specification: COTRN02C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COTRN02C                                             |
| Source File      | app/cbl/COTRN02C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CT02 (WS-TRANID, line 37)                            |
| Function         | Transaction add screen. Allows users to enter a new transaction record. Accepts card number or account number (cross-references between them via CCXREF/CXACAIX VSAM files). Validates date fields using CSUTLDTC subprogram. Generates a new transaction ID by reading the last existing record from TRANSACT and adding 1. Confirmation ('Y'/'y') required before WRITE. PF5 copies the last submitted transaction into input fields for reuse. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CT02 and COMMAREA)

Clear WS-MESSAGE; SET ERR-FLG-OFF

IF EIBCALEN = 0:
    PERFORM RETURN-TO-PREV-SCREEN (XCTL to COSGN00C)

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO COTRN2AO
        PERFORM SEND-TRNADD-SCREEN (initial display)
    ELSE:
        PERFORM RECEIVE-TRNADD-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER:  PERFORM PROCESS-ENTER-KEY
            WHEN DFHPF3:    PERFORM RETURN-TO-PREV-SCREEN
            WHEN DFHPF4:    PERFORM CLEAR-CURRENT-SCREEN
            WHEN DFHPF5:    PERFORM COPY-LAST-TRAN-DATA
            WHEN OTHER:     Set ERR-FLG-ON; CCDA-MSG-INVALID-KEY; SEND-TRNADD-SCREEN

[Note: SEND-TRNADD-SCREEN contains EXEC CICS RETURN TRANSID('CT02') COMMAREA — unusual placement]
```

### Paragraph-Level Detail

| Paragraph               | Lines     | Description |
|-------------------------|-----------|-------------|
| MAIN-PARA               | 82–133    | Main entry: EIBCALEN check; first/reenter dispatch; AID evaluate |
| PROCESS-ENTER-KEY       | 138–249   | Validate CONFIRMI; validate all fields; call ADD-TRANSACTION if valid |
| ADD-TRANSACTION         | 254–380   | STARTBR HIGH-VALUES/READPREV/ENDBR to get max TRAN-ID; ADD 1; populate TRAN-RECORD; WRITE TRANSACT; display success message |
| COPY-LAST-TRAN-DATA     | 385–430   | Copy last successfully added transaction fields back to screen output fields |
| RETURN-TO-PREV-SCREEN   | 435–448   | Default CDEMO-TO-PROGRAM=CDEMO-FROM-PROGRAM; EXEC CICS XCTL |
| CLEAR-CURRENT-SCREEN    | 453–465   | MOVE LOW-VALUES to COTRN2AO; clear WS-MESSAGE; send blank screen |
| SEND-TRNADD-SCREEN      | 470–489   | POPULATE-HEADER-INFO; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP; **EXEC CICS RETURN TRANSID('CT02') COMMAREA** |
| RECEIVE-TRNADD-SCREEN   | 494–504   | CICS RECEIVE MAP('COTRN2A') MAPSET('COTRN02') INTO(COTRN2AI) |
| POPULATE-HEADER-INFO    | 509–529   | Fill header fields |
| VALIDATE-INPUT-FIELDS   | 534–650   | Validate each required field: card/account non-blank, dates valid, amount format, merchant ID numeric, type/category numeric |
| LOOKUP-ACCT-FROM-CARD   | 655–700   | READ CCXREF by card number → get XREF-ACCT-ID |
| LOOKUP-CARD-FROM-ACCT   | 705–750   | READ CXACAIX (alternate index) by account ID → get XREF-CARD-NUM |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 51) | CARDDEMO-COMMAREA: standard commarea; extended inline with CDEMO-CT02-INFO |
| COTRN02  | WORKING-STORAGE (line 53)  | BMS mapset copybook: COTRN2AI (input map), COTRN2AO (output map); contains TRNIDINI, CARDINPI, ACCTIDOI, TRNTYPEI, TRNCATI, TRNSRCI, TRNDESI, TRNAMI, TRNORIGI, TRNPROCI, TRNMRCHI, TRNMRCNMI, TRNMRCCTI, TRNMRCSTATI, TRNMRCZPI, CONFIRMI, ERRMSGO, header fields |
| COTRN02Y  | WORKING-STORAGE (line 55)  | TRAN-RECORD: TRAN-ID X(16), TRAN-TYPE-CD X(02), TRAN-CAT-CD 9(04), TRAN-SOURCE X(10), TRAN-DESC X(24), TRAN-AMT S9(09)V99, TRAN-MERCHANT-ID 9(09), TRAN-MERCHANT-NAME X(50), TRAN-MERCHANT-CITY X(50), TRAN-MERCHANT-ZIP X(10), TRAN-CARD-NUM X(16), TRAN-ORIG-TS X(26), TRAN-PROC-TS X(26) |
| CCXREF    | WORKING-STORAGE (line 57)  | CARD-XREF-RECORD: XREF-CARD-NUM X(16), XREF-CUST-ID 9(09), XREF-ACCT-ID 9(11); key=XREF-CARD-NUM |
| COTTL01Y  | WORKING-STORAGE (line 59) | Screen title constants |
| CSDAT01Y  | WORKING-STORAGE (line 60) | Current date/time |
| CSMSG01Y  | WORKING-STORAGE (line 61) | Common messages |
| CSUSR01Y  | WORKING-STORAGE (line 62) | Signed-on user data |
| DFHAID    | WORKING-STORAGE (line 64) | EIBAID constants: DFHENTER, DFHPF3, DFHPF4, DFHPF5 |
| DFHBMSCA  | WORKING-STORAGE (line 65) | BMS attribute bytes |

### COMMAREA Extension (inline after COPY COCOM01Y)

| Field              | PIC       | Purpose |
|--------------------|-----------|---------|
| CDEMO-CT02-INFO    | Group     | CT02-specific commarea fields |
| CDEMO-CT02-LAST-TRAN-ID | X(16) | Last successfully added transaction ID (for PF5 copy) |

### Key Working Storage Variables

| Variable              | PIC         | Purpose |
|-----------------------|-------------|---------|
| WS-PGMNAME            | X(08) = 'COTRN02C' | Program name |
| WS-TRANID             | X(04) = 'CT02' | Transaction ID |
| WS-MESSAGE            | X(80)       | User-visible message |
| WS-ERR-FLG            | X(01)       | Error flag |
| WS-TRANSACT-FILE      | X(08) = 'TRANSACT' | TRANSACT CICS file name |
| WS-CCXREF-FILE        | X(08) = 'CCXREF  ' | CCXREF CICS file name |
| WS-CXACAIX-FILE       | X(08) = 'CXACAIX ' | CXACAIX alternate index file name |
| WS-ACCTDAT-FILE       | X(08) = 'ACCTDAT ' | Defined but never used in PROCEDURE DIVISION |
| WS-NEW-TRAN-ID        | X(16)       | Newly generated transaction ID (max existing + 1) |
| WS-TRAN-ID-NUM        | 9(16)       | Numeric form of last TRAN-ID from READPREV; ADD 1 to generate new |
| WS-CARD-NUM           | X(16)       | Card number input (from CARDINPI) |
| WS-ACCT-ID            | 9(11)       | Account ID (from ACCTIDOI or derived from XREF lookup) |
| WS-DATE-FORMAT        | X(30) = 'YYYYMMDD' | Format string passed to CSUTLDTC |
| WS-DATE-TO-VALIDATE   | X(10)       | Date string passed to CSUTLDTC |
| WS-DATE-RESULT        | Group (15b) | SEV-CD + message from CSUTLDTC |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS RETURN TRANSID('CT02') COMMAREA(CARDDEMO-COMMAREA) | SEND-TRNADD-SCREEN | Pseudo-conversational return — **embedded inside SEND-TRNADD-SCREEN paragraph** |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | RETURN-TO-PREV-SCREEN | Return to calling menu |
| EXEC CICS SEND MAP('COTRN2A') MAPSET('COTRN02') FROM(COTRN2AO) ERASE | SEND-TRNADD-SCREEN | Display transaction add screen |
| EXEC CICS RECEIVE MAP('COTRN2A') MAPSET('COTRN02') INTO(COTRN2AI) RESP RESP2 | RECEIVE-TRNADD-SCREEN | Receive all input fields |
| EXEC CICS STARTBR FILE(WS-TRANSACT-FILE) RIDFLD(WS-TRAN-ID) RESP RESP2 | ADD-TRANSACTION | Position at HIGH-VALUES for READPREV to get last record |
| EXEC CICS READPREV FILE(WS-TRANSACT-FILE) INTO(TRAN-RECORD) RIDFLD(WS-TRAN-ID) RESP RESP2 | ADD-TRANSACTION | Read last transaction record to determine max TRAN-ID |
| EXEC CICS ENDBR FILE(WS-TRANSACT-FILE) | ADD-TRANSACTION | End browse after READPREV |
| EXEC CICS WRITE FILE(WS-TRANSACT-FILE) FROM(TRAN-RECORD) RIDFLD(WS-NEW-TRAN-ID) RESP RESP2 | ADD-TRANSACTION | Write new transaction record |
| EXEC CICS READ FILE(WS-CCXREF-FILE) INTO(CARD-XREF-RECORD) RIDFLD(WS-CARD-NUM) RESP RESP2 | LOOKUP-ACCT-FROM-CARD | Get account ID from card number |
| EXEC CICS READ FILE(WS-CXACAIX-FILE) INTO(CARD-XREF-RECORD) RIDFLD(WS-ACCT-ID) RESP RESP2 | LOOKUP-CARD-FROM-ACCT | Get card number from account ID (via alternate index) |

**Structural anomaly — CICS RETURN inside SEND-TRNADD-SCREEN**: The `EXEC CICS RETURN TRANSID('CT02') COMMAREA(CARDDEMO-COMMAREA)` statement is located at the end of the SEND-TRNADD-SCREEN paragraph rather than at the end of MAIN-PARA. This means every call to SEND-TRNADD-SCREEN terminates the current task. Control never returns to MAIN-PARA after SEND-TRNADD-SCREEN executes. This is an unusual but functional pattern in pseudo-conversational CICS COBOL.

---

## 5. File/Dataset Access

| File Name | CICS File  | Access Type | Key | Purpose |
|-----------|------------|-------------|-----|---------|
| TRANSACT  | TRANSACT   | STARTBR/READPREV/ENDBR | HIGH-VALUES (STARTBR to position at end) | Retrieve last TRAN-ID for new ID generation |
| TRANSACT  | TRANSACT   | WRITE | WS-NEW-TRAN-ID (X(16)) | Write new transaction record |
| CCXREF    | CCXREF     | READ | WS-CARD-NUM X(16) | Look up account ID from card number |
| CXACAIX   | CXACAIX    | READ | WS-ACCT-ID 9(11) | Look up card number from account ID (alternate index on CCXREF by account) |
| ACCTDAT   | ACCTDAT    | (none) | N/A | **Defined in WS (WS-ACCTDAT-FILE) but never accessed in PROCEDURE DIVISION** |

**Transaction ID generation sequence:**
1. STARTBR TRANSACT with RIDFLD = HIGH-VALUES (positions past last record)
2. READPREV to read the last (highest key) TRAN-RECORD
3. ENDBR
4. Convert TRAN-ID to numeric WS-TRAN-ID-NUM; ADD 1; format back to X(16) as WS-NEW-TRAN-ID
5. WRITE with WS-NEW-TRAN-ID as RIDFLD

**Risk**: This STARTBR/READPREV/ADD-1 sequence is not atomic. Concurrent transactions adding records simultaneously could generate duplicate TRAN-IDs. CICS WRITE with DUPKEY would be the failure indicator, but no DUPKEY handling is present.

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COTRN02    | COTRN2A | CT02        |

**Key Screen Fields:**

| Field       | Direction | Description |
|-------------|-----------|-------------|
| CARDINPI    | Input     | Card number (16 digits) |
| ACCTIDOI    | Input     | Account ID (alternative to card number) |
| TRNTYPEI    | Input     | Transaction type code (2 characters) |
| TRNCATI     | Input     | Transaction category code (numeric 4 digits) |
| TRNSRCI     | Input     | Transaction source (10 characters) |
| TRNDESI     | Input     | Transaction description (24 characters) |
| TRNAMI      | Input     | Amount: format +/-NNNNNNNN.NN |
| TRNORIGI    | Input     | Original transaction date (YYYYMMDD) |
| TRNPROCI    | Input     | Process date (YYYYMMDD) |
| TRNMRCHI    | Input     | Merchant ID (9 digits) |
| TRNMRCNMI   | Input     | Merchant name |
| TRNMRCCTI   | Input     | Merchant city |
| TRNMRCSTATI | Input     | Merchant state |
| TRNMRCZPI   | Input     | Merchant ZIP |
| CONFIRMI    | Input     | Confirmation ('Y'/'y' required to submit) |
| ERRMSGO     | Output    | WS-MESSAGE: error or status message |
| TITLE01O–CURTIMEO | Output | Standard header fields |

**Navigation:**
- ENTER: validate and submit new transaction
- PF3: return to previous menu
- PF4: clear screen
- PF5: copy last successfully added transaction to screen fields

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| CSUTLDTC   | Static CALL  | VALIDATE-INPUT-FIELDS: validate TRNORIGI (orig date) and TRNPROCI (proc date) |
| CDEMO-FROM-PROGRAM | CICS XCTL | PF3 pressed or EIBCALEN=0 |

**CSUTLDTC call (date validation):**
```
CALL 'CSUTLDTC' USING WS-DATE-TO-VALIDATE, WS-DATE-FORMAT, WS-DATE-RESULT
```
- WS-DATE-FORMAT = 'YYYYMMDD'
- If WS-DATE-RESULT.SEV-CD NOT = '0000' (and not '2513'), date is invalid

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C |
| CONFIRMI not 'Y'/'y' | ERR-FLG-ON; 'Please confirm...' message; re-send |
| Card number blank AND account ID blank | ERR-FLG-ON; error message |
| Card number not found in CCXREF | ERR-FLG-ON; error message |
| Account ID not found in CXACAIX | ERR-FLG-ON; error message |
| TRNORIGI invalid date (CSUTLDTC SEV-CD != '0000') | ERR-FLG-ON; 'Invalid original date' message |
| TRNPROCI invalid date (CSUTLDTC SEV-CD != '0000') | ERR-FLG-ON; 'Invalid process date' message |
| TRNAMI invalid format (not +/-NNNNNNNN.NN) | ERR-FLG-ON; amount format error |
| TRNMRCHI not numeric | ERR-FLG-ON; merchant ID error |
| TRNTYPEI/TRNCATI non-numeric | ERR-FLG-ON; type/category error |
| TRANSACT WRITE RESP != NORMAL | ERR-FLG-ON; write error message with RESP/RESP2 |
| TRANSACT STARTBR NOTFND (empty file) | Handle as first record; WS-NEW-TRAN-ID = '0000000000000001' |
| Invalid AID key | ERR-FLG-ON; CCDA-MSG-INVALID-KEY |

---

## 9. Business Rules

1. **Card-account cross-reference**: Either card number or account ID may be entered. If card number is entered, LOOKUP-ACCT-FROM-CARD reads CCXREF to get XREF-ACCT-ID. If account ID is entered, LOOKUP-CARD-FROM-ACCT reads CXACAIX alternate index to get XREF-CARD-NUM. Both card number and account ID are stored in the transaction record.
2. **Transaction ID generation**: New TRAN-ID = last TRAN-ID in TRANSACT file + 1. This requires the file to be non-empty for normal path; empty file is handled with first-record logic (ID = '0000000000000001').
3. **Confirmation gate**: CONFIRMI must be 'Y' or 'y'. All validation passes first, then confirmation is checked before WRITE.
4. **Date validation via CSUTLDTC**: Both TRNORIGI and TRNPROCI are validated using CSUTLDTC with format 'YYYYMMDD'. Severity code '0000' (and tolerating '2513') = valid.
5. **Amount format**: Transaction amount must be entered as +NNNNNNNN.NN or -NNNNNNNN.NN (signed numeric with 2 decimal places, explicit sign, explicit decimal point). Parsed into S9(09)V99 for storage.
6. **PF5 copy-last**: PF5 repopulates screen output fields from the last successfully added transaction stored in WS-LAST-TRAN-* working storage fields, allowing rapid entry of similar transactions.
7. **ACCTDAT not used**: WS-ACCTDAT-FILE is defined as 'ACCTDAT' in working storage but no CICS file command references it. This represents either dead code or a removed feature.
8. **SEND-TRNADD-SCREEN owns RETURN**: The CICS RETURN statement is inside SEND-TRNADD-SCREEN rather than in MAIN-PARA. Every screen send immediately terminates the task. Callers of SEND-TRNADD-SCREEN do not return.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COTRN2A) | All transaction fields: card/account, type, category, source, description, amount, dates, merchant info, confirmation |
| COMMAREA  | CDEMO-CT02-INFO (last tran ID for PF5 copy) |
| CCXREF VSAM | Card → account cross-reference |
| CXACAIX VSAM | Account → card cross-reference (alternate index) |
| TRANSACT VSAM | Last TRAN-ID via STARTBR/READPREV for new ID generation |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COTRN2A) | Transaction add screen with success/error messages |
| TRANSACT VSAM | New TRAN-RECORD written with generated TRAN-ID |
| COMMAREA   | CDEMO-CT02-LAST-TRAN-ID updated after successful write |

---

## 11. Key Variables and Their Purpose

| Variable                  | Purpose |
|---------------------------|---------|
| WS-NEW-TRAN-ID            | Generated new transaction ID (max existing + 1); used as WRITE RIDFLD |
| WS-TRAN-ID-NUM            | Numeric conversion of last TRAN-ID from READPREV; ADD 1 generates next ID |
| WS-CARD-NUM               | Card number for CCXREF lookup; stored in TRAN-CARD-NUM |
| WS-ACCT-ID                | Account ID for CXACAIX lookup; used for cross-reference validation |
| CONFIRMI                  | User confirmation; gates the WRITE operation |
| WS-DATE-TO-VALIDATE / WS-DATE-FORMAT | Inputs to CSUTLDTC for date validation |
| WS-DATE-RESULT            | Output from CSUTLDTC: SEV-CD determines date validity |
| WS-ACCTDAT-FILE           | Defined as 'ACCTDAT' but never used — dead reference |
| CDEMO-CT02-LAST-TRAN-ID   | Last submitted transaction ID; restored to screen by PF5 |
