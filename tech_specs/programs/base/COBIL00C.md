# Technical Specification: COBIL00C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COBIL00C                                             |
| Source File      | app/cbl/COBIL00C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CB00 (WS-TRANID, line 38)                            |
| Function         | Online Bill Payment. Accepts an account ID from the user, displays current balance, and allows the user to confirm payment. On confirmation: reads the card cross-reference (CXACAIX), determines the highest existing transaction ID (STARTBR/READPREV/ENDBR on TRANSACT), generates a new payment transaction record (type '02', category 2), writes to TRANSACT, deducts the payment from ACCT-CURR-BAL, and rewrites ACCTDAT. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CB00 and COMMAREA)

SET ERR-FLG-OFF, USR-MODIFIED-NO
Clear WS-MESSAGE and screen error field

IF EIBCALEN = 0:
    MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM
    PERFORM RETURN-TO-PREV-SCREEN (XCTL to COSGN00C)

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO COBIL0AO; cursor to ACTIDINI (-1)
        IF CDEMO-CB00-TRN-SELECTED not blank:
            MOVE it to ACTIDINI; PERFORM PROCESS-ENTER-KEY
        PERFORM SEND-BILLPAY-SCREEN
    ELSE:
        PERFORM RECEIVE-BILLPAY-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER: PERFORM PROCESS-ENTER-KEY
            WHEN DFHPF3: MOVE CDEMO-FROM-PROGRAM to CDEMO-TO-PROGRAM (or COMEN01C)
                         PERFORM RETURN-TO-PREV-SCREEN
            WHEN DFHPF4: PERFORM CLEAR-CURRENT-SCREEN
            WHEN OTHER: ERR-FLG-ON; CCDA-MSG-INVALID-KEY; SEND-BILLPAY-SCREEN

EXEC CICS RETURN TRANSID('CB00') COMMAREA(CARDDEMO-COMMAREA)
```

### PROCESS-ENTER-KEY Detail

```
PROCESS-ENTER-KEY:
    SET CONF-PAY-NO

    IF ACTIDINI is blank: error "Acct ID can NOT be empty..." → SEND

    MOVE ACTIDINI to ACCT-ID and XREF-ACCT-ID

    EVALUATE CONFIRMI:
        WHEN 'Y'/'y': SET CONF-PAY-YES; READ-ACCTDAT-FILE (READ UPDATE)
        WHEN 'N'/'n': CLEAR-CURRENT-SCREEN; ERR-FLG-ON (no payment)
        WHEN SPACES/LOW-VALUES: READ-ACCTDAT-FILE (display balance, await confirm)
        WHEN OTHER: error "Invalid value. Valid values are (Y/N)..."

    IF ACCT-CURR-BAL <= 0: error "You have nothing to pay..."

    IF CONF-PAY-YES:
        READ-CXACAIX-FILE (get XREF-CARD-NUM via account alternate index)
        MOVE HIGH-VALUES TO TRAN-ID
        STARTBR-TRANSACT-FILE (position at highest key)
        READPREV-TRANSACT-FILE (read last transaction)
        ENDBR-TRANSACT-FILE
        MOVE TRAN-ID TO WS-TRAN-ID-NUM
        ADD 1 TO WS-TRAN-ID-NUM → new TRAN-ID
        INITIALIZE TRAN-RECORD
        Set: TRAN-TYPE-CD='02', TRAN-CAT-CD=2, TRAN-SOURCE='POS TERM'
             TRAN-DESC='BILL PAYMENT - ONLINE', TRAN-AMT=ACCT-CURR-BAL
             TRAN-CARD-NUM=XREF-CARD-NUM, TRAN-MERCHANT-ID=999999999
             TRAN-MERCHANT-NAME='BILL PAYMENT', TRAN-MERCHANT-CITY='N/A'
             TRAN-MERCHANT-ZIP='N/A'
        GET-CURRENT-TIMESTAMP → WS-TIMESTAMP → TRAN-ORIG-TS + TRAN-PROC-TS
        WRITE-TRANSACT-FILE
        COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT
        UPDATE-ACCTDAT-FILE (CICS REWRITE)
    ELSE:
        "Confirm to make a bill payment..." → cursor to CONFIRMI

    SEND-BILLPAY-SCREEN
```

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| MAIN-PARA              | 99–149    | Entry: clear flags; EIBCALEN check; first/reenter dispatch; CICS RETURN |
| PROCESS-ENTER-KEY      | 154–244   | Main business logic: validate acct ID; check confirm flag; read account; confirm/execute payment |
| GET-CURRENT-TIMESTAMP  | 249–267   | CICS ASKTIME; CICS FORMATTIME; build WS-TIMESTAMP (date+time in X(26)) |
| RETURN-TO-PREV-SCREEN  | 272–284   | XCTL to CDEMO-TO-PROGRAM with updated COMMAREA navigation fields |
| SEND-BILLPAY-SCREEN    | 289–301   | POPULATE-HEADER-INFO; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP ERASE CURSOR |
| RECEIVE-BILLPAY-SCREEN | 306–314   | CICS RECEIVE MAP INTO RESP RESP2 |
| POPULATE-HEADER-INFO   | 319–338   | Fill screen header from FUNCTION CURRENT-DATE and literals |
| READ-ACCTDAT-FILE      | 343–372   | CICS READ UPDATE ACCTDAT by ACCT-ID; NOTFND: error + re-send |
| UPDATE-ACCTDAT-FILE    | 377–403   | CICS REWRITE ACCTDAT; NOTFND/OTHER: error + re-send |
| READ-CXACAIX-FILE      | 408–436   | CICS READ CXACAIX by XREF-ACCT-ID (account AIX); NOTFND/OTHER: error + re-send |
| STARTBR-TRANSACT-FILE  | 441–467   | CICS STARTBR TRANSACT RIDFLD(TRAN-ID=HIGH-VALUES); NOTFND/OTHER: error |
| READPREV-TRANSACT-FILE | 472–496   | CICS READPREV TRANSACT; ENDFILE: MOVE ZEROS TO TRAN-ID (no prior transactions) |
| ENDBR-TRANSACT-FILE    | 501–505   | CICS ENDBR TRANSACT |
| WRITE-TRANSACT-FILE    | 510–547   | CICS WRITE TRANSACT; NORMAL: success message + INITIALIZE-ALL-FIELDS; DUPKEY/DUPREC: error |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 63) | CARDDEMO-COMMAREA + CDEMO-CB00-INFO extension (CB00-TRNID-FIRST X(16), CB00-TRNID-LAST X(16), CB00-PAGE-NUM, CB00-NEXT-PAGE-FLG, CB00-TRN-SEL-FLG, CB00-TRN-SELECTED X(16)) |
| COBIL00   | WORKING-STORAGE (line 74) | BMS mapset copybook: COBIL0AI (input), COBIL0AO (output); fields: ACTIDINI, CONFIRMI, CURBALI, ERRMSGO, ERRMSGC, ACTIDINL, CONFIRML |
| COTTL01Y  | WORKING-STORAGE (line 76) | Screen title constants |
| CSDAT01Y  | WORKING-STORAGE (line 77) | WS-CURDATE-DATA, WS-CURDATE-MM-DD-YY, WS-CURTIME-* |
| CSMSG01Y  | WORKING-STORAGE (line 78) | CCDA-MSG-INVALID-KEY |
| CVACT01Y  | WORKING-STORAGE (line 80) | ACCOUNT-RECORD: ACCT-ID, ACCT-CURR-BAL, ACCT-CREDIT-LIMIT, etc. |
| CVACT03Y  | WORKING-STORAGE (line 81) | CARD-XREF-RECORD: XREF-ACCT-ID, XREF-CARD-NUM |
| CVTRA05Y  | WORKING-STORAGE (line 82) | TRAN-RECORD: TRAN-ID, TRAN-TYPE-CD, TRAN-AMT, TRAN-CARD-NUM, timestamps, merchant fields |
| DFHAID    | WORKING-STORAGE (line 84) | DFHENTER, DFHPF3, DFHPF4 |
| DFHBMSCA  | WORKING-STORAGE (line 85) | DFHGREEN attribute |

### Key Working Storage Variables

| Variable              | PIC           | Purpose |
|-----------------------|---------------|---------|
| WS-PGMNAME            | X(8) = 'COBIL00C' | Screen header program name |
| WS-TRANID             | X(4) = 'CB00' | Transaction ID for CICS RETURN |
| WS-TRANSACT-FILE      | X(8) = 'TRANSACT' | CICS file name for transactions |
| WS-ACCTDAT-FILE       | X(8) = 'ACCTDAT ' | CICS file name for accounts |
| WS-CXACAIX-FILE       | X(8) = 'CXACAIX ' | CICS file name for card-to-account AIX |
| WS-ERR-FLG            | X(1)          | 'Y'=error; 'N'=ok |
| WS-USR-MODIFIED       | X(1)          | 'Y' if user confirmed payment (set but not used as guard — WS-CONF-PAY-FLG is the actual control) |
| WS-CONF-PAY-FLG       | X(1)          | 'Y'=CONF-PAY-YES (payment confirmed); 'N'=CONF-PAY-NO |
| WS-TRAN-AMT           | +99999999.99  | Display edit area for transaction amount |
| WS-CURR-BAL           | +9999999999.99 | Display edit area for current balance |
| WS-TRAN-ID-NUM        | 9(16)         | Numeric form of last TRAN-ID; +1 becomes new ID |
| WS-ABS-TIME           | S9(15) COMP-3 | CICS ASKTIME output |
| WS-CUR-DATE-X10       | X(10)         | FORMATTIME YYYYMMDD with DATESEP('-') output |
| WS-CUR-TIME-X08       | X(08)         | FORMATTIME TIME with TIMESEP(':') output |
| CDEMO-CB00-INFO       | Group         | Pagination info (first/last TRAN-ID, page num, next-page flag, selected transaction) passed via COMMAREA |

---

## 4. CICS Commands Used

| Command | Purpose |
|---------|---------|
| EXEC CICS RETURN TRANSID('CB00') COMMAREA | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM COMMAREA | Navigate to previous program or COSGN00C |
| EXEC CICS SEND MAP('COBIL0A') MAPSET('COBIL00') FROM ERASE CURSOR | Send bill payment screen |
| EXEC CICS RECEIVE MAP MAPSET INTO RESP RESP2 | Receive screen input |
| EXEC CICS READ DATASET('ACCTDAT') INTO LENGTH RIDFLD KEYLENGTH UPDATE RESP RESP2 | Read account for balance display and UPDATE lock |
| EXEC CICS REWRITE DATASET('ACCTDAT') FROM LENGTH RESP RESP2 | Update account balance after payment |
| EXEC CICS READ DATASET('CXACAIX') INTO LENGTH RIDFLD KEYLENGTH RESP RESP2 | Read card-to-account cross-reference by account ID |
| EXEC CICS STARTBR DATASET('TRANSACT') RIDFLD KEYLENGTH RESP RESP2 | Start browse at HIGH-VALUES to find last transaction |
| EXEC CICS READPREV DATASET('TRANSACT') INTO LENGTH RIDFLD KEYLENGTH RESP RESP2 | Read last transaction to determine new ID |
| EXEC CICS ENDBR DATASET('TRANSACT') | End browse |
| EXEC CICS WRITE DATASET('TRANSACT') FROM LENGTH RIDFLD KEYLENGTH RESP RESP2 | Write new payment transaction record |
| EXEC CICS ASKTIME ABSTIME | Get absolute time for timestamp |
| EXEC CICS FORMATTIME ABSTIME YYYYMMDD DATESEP TIME TIMESEP | Format timestamp components |

---

## 5. File/Dataset Access

| CICS File Name | Access      | Purpose |
|----------------|-------------|---------|
| ACCTDAT        | READ UPDATE + REWRITE | Read account balance for display; rewrite with reduced balance after payment |
| CXACAIX        | READ (AIX)  | Alternate index on XREF by account ID; obtain XREF-CARD-NUM for TRAN-CARD-NUM |
| TRANSACT       | STARTBR/READPREV/ENDBR + WRITE | Browse to find highest existing TRAN-ID; write new payment transaction |

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COBIL00    | COBIL0A | CB00        |

**Key Screen Fields:**

| Field      | Direction | Description |
|------------|-----------|-------------|
| ACTIDINI   | Input     | Account ID (11 digits) |
| CONFIRMI   | Input     | Confirmation: Y/y to pay, N/n to cancel |
| CURBALI    | Output    | Current balance display (edit format) |
| ERRMSGO    | Output    | WS-MESSAGE: instructions, errors, success message |
| ERRMSGC    | Output    | Color of error message (DFHGREEN on success) |
| ACTIDINL   | Cursor    | Set to -1 to position cursor on account ID field |
| CONFIRML   | Cursor    | Set to -1 to position cursor on confirm field |
| TITLE01O/TITLE02O | Output | Application titles |
| TRNNAMEO/PGMNAMEO | Output | Transaction and program name |
| CURDATEO/CURTIMEO | Output | Current date/time |

**Navigation:**
- ENTER: process payment (step 1: show balance; step 2: confirm with Y)
- PF3: return to previous program (CDEMO-FROM-PROGRAM or COMEN01C)
- PF4: clear current screen
- Other keys: error message

---

## 7. Called Programs / Transfers

| Program  | Method     | Condition |
|----------|------------|-----------|
| CDEMO-FROM-PROGRAM (or COMEN01C) | CICS XCTL | PF3 pressed |
| COSGN00C | CICS XCTL  | EIBCALEN=0 (no commarea) |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN=0 | XCTL to COSGN00C |
| ACTIDINI blank | "Acct ID can NOT be empty..."; cursor to ACTIDINI; re-send |
| CONFIRMI invalid value (not Y/N/space) | "Invalid value. Valid values are (Y/N)..."; cursor to CONFIRMI |
| ACCT-CURR-BAL <= 0 | "You have nothing to pay..."; cursor to ACTIDINI; re-send |
| ACCTDAT NOTFND | "Account ID NOT found..."; cursor to ACTIDINI; re-send |
| ACCTDAT other RESP | DISPLAY RESP/RESP2; "Unable to lookup Account..."; re-send |
| CXACAIX NOTFND | "Account ID NOT found..."; re-send |
| CXACAIX other RESP | DISPLAY RESP/RESP2; "Unable to lookup XREF AIX file..." |
| STARTBR NOTFND | "Transaction ID NOT found..."; re-send |
| READPREV ENDFILE | MOVE ZEROS TO TRAN-ID (this is the first transaction — ID will be 1) |
| WRITE DUPKEY/DUPREC | "Tran ID already exist..."; cursor to ACTIDINI; re-send |
| WRITE NORMAL | Success: "Payment successful. Your Transaction ID is [N]." in green |
| REWRITE NOTFND/OTHER | Error message; cursor to ACTIDINI; re-send |
| Invalid AID | CCDA-MSG-INVALID-KEY; re-send |

---

## 9. Business Rules

1. **Two-step confirmation**: First ENTER with a valid account ID displays the current balance (no payment). Second ENTER with CONFIRMI='Y' executes the payment. CONFIRMI='N' clears the screen and sets error flag (no payment).
2. **Transaction ID generation**: STARTBR at HIGH-VALUES + READPREV reads the last (highest-keyed) transaction. Its 16-digit numeric TRAN-ID is incremented by 1 for the new payment transaction. If READPREV returns ENDFILE (no transactions exist), TRAN-ID is set to 0 and will become 1 after ADD 1.
3. **Payment transaction attributes**: TRAN-TYPE-CD='02' (payment type), TRAN-CAT-CD=2, TRAN-SOURCE='POS TERM', TRAN-DESC='BILL PAYMENT - ONLINE', TRAN-MERCHANT-ID=999999999 (synthetic), TRAN-MERCHANT-NAME='BILL PAYMENT', TRAN-MERCHANT-CITY='N/A', TRAN-MERCHANT-ZIP='N/A'.
4. **Balance deduction formula**: ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT. Since TRAN-AMT = original ACCT-CURR-BAL (the full balance), the result is zero — full payment of balance.
5. **Timestamp generation**: Both TRAN-ORIG-TS and TRAN-PROC-TS are set to the same WS-TIMESTAMP generated by CICS ASKTIME/FORMATTIME at payment time.
6. **CXACAIX lookup**: The alternate index CXACAIX is read by XREF-ACCT-ID to obtain the card number (XREF-CARD-NUM) required for TRAN-CARD-NUM in the transaction record.
7. **CSD COMMAREA extension**: CDEMO-CB00-INFO extends CARDDEMO-COMMAREA inline (defined immediately after COPY COCOM01Y) to carry pagination state. CDEMO-CB00-TRN-SELECTED allows transaction pre-selection from COTRN00C.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COBIL0A) | Account ID (ACTIDINI); Confirm payment Y/N (CONFIRMI) |
| ACCTDAT   | Account record: ACCT-CURR-BAL for display and deduction |
| CXACAIX   | Card cross-reference by account: provides XREF-CARD-NUM |
| TRANSACT  | Browse to find last TRAN-ID for new ID generation |
| COMMAREA  | CDEMO-FROM-PROGRAM, CDEMO-CB00-TRN-SELECTED |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COBIL0A) | Balance display; confirmation prompt; success/error messages |
| TRANSACT   | CICS WRITE: new payment transaction record |
| ACCTDAT    | CICS REWRITE: ACCT-CURR-BAL reduced to zero after payment |

---

## 11. Key Variables and Their Purpose

| Variable          | Purpose |
|-------------------|---------|
| WS-CONF-PAY-FLG   | Two-step guard: CONF-PAY-YES only when CONFIRMI='Y' was received |
| WS-TRAN-ID-NUM    | 9(16) numeric form of last TRAN-ID; +1 produces the new payment transaction ID |
| WS-ABS-TIME       | CICS absolute time; source for TRAN-ORIG-TS and TRAN-PROC-TS |
| XREF-ACCT-ID      | Key used to read CXACAIX; populated from ACTIDINI/ACCT-ID |
| XREF-CARD-NUM     | Retrieved from CXACAIX; placed in TRAN-CARD-NUM of payment record |
| CDEMO-CB00-INFO   | Pagination and selection state extended in COMMAREA beyond CARDDEMO-COMMAREA |
