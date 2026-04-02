# Technical Specification: COBIL00C — Bill Payment Program

## 1. Executive Summary

COBIL00C is an online CICS COBOL program in the CardDemo application that enables a cardholder to pay their account balance in full. The program presents a bill payment screen (map COBIL0A / mapset COBIL00), accepts an account ID, retrieves the current balance from the ACCTDAT VSAM file, requests a Y/N confirmation from the user, and — upon confirmation — writes a payment transaction record to the TRANSACT file and resets the account balance to zero. The program is invoked under CICS transaction ID CB00.

Source file: `app/cbl/COBIL00C.cbl`
Version stamp: `CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:12:32 CDT`

---

## 2. Artifact Inventory

| Artifact | Type | Location | Role |
|---|---|---|---|
| COBIL00C.cbl | CICS COBOL Program | app/cbl/ | Main bill payment program |
| COBIL00.bms | BMS Mapset | app/bms/ | Screen definition for COBIL0A |
| COBIL00.CPY | BMS-generated Copybook | app/cpy-bms/ | Map data structures COBIL0AI / COBIL0AO |
| COCOM01Y.cpy | Copybook | app/cpy/ | CARDDEMO-COMMAREA + CDEMO-CB00-INFO |
| CVACT01Y.cpy | Copybook | app/cpy/ | ACCOUNT-RECORD layout (ACCTDAT) |
| CVACT03Y.cpy | Copybook | app/cpy/ | CARD-XREF-RECORD layout (CXACAIX) |
| CVTRA05Y.cpy | Copybook | app/cpy/ | TRAN-RECORD layout (TRANSACT) |
| COTTL01Y.cpy | Copybook | app/cpy/ | Screen title literals (CCDA-SCREEN-TITLE) |
| CSDAT01Y.cpy | Copybook | app/cpy/ | Date/time working storage (WS-DATE-TIME) |
| CSMSG01Y.cpy | Copybook | app/cpy/ | Common messages (CCDA-COMMON-MESSAGES) |
| DFHAID | System Copybook | CICS | Attention identifier constants |
| DFHBMSCA | System Copybook | CICS | BMS attribute character constants |

---

## 3. Program Identity

| Attribute | Value | Source Reference |
|---|---|---|
| PROGRAM-ID | COBIL00C | COBIL00C.cbl line 24 |
| Transaction ID | CB00 | COBIL00C.cbl line 38 (WS-TRANID) |
| Application | CardDemo | COBIL00C.cbl line 3 |
| Type | CICS COBOL Online Program | COBIL00C.cbl line 4 |
| Map | COBIL0A | COBIL00C.cbl line 296 |
| Mapset | COBIL00 | COBIL00C.cbl line 297 |

---

## 4. Data Division

### 4.1 Working-Storage Fields (WS-VARIABLES — COBIL00C.cbl lines 36–61)

| Field | PIC | Initial Value | Purpose |
|---|---|---|---|
| WS-PGMNAME | X(08) | 'COBIL00C' | Self-identifying program name |
| WS-TRANID | X(04) | 'CB00' | CICS transaction ID for RETURN |
| WS-MESSAGE | X(80) | SPACES | Error / status message text |
| WS-TRANSACT-FILE | X(08) | 'TRANSACT' | CICS dataset name for transactions |
| WS-ACCTDAT-FILE | X(08) | 'ACCTDAT ' | CICS dataset name for accounts |
| WS-CXACAIX-FILE | X(08) | 'CXACAIX ' | CICS dataset name for card xref AIX |
| WS-ERR-FLG | X(01) | 'N' | Error flag; 88 ERR-FLG-ON = 'Y', OFF = 'N' |
| WS-RESP-CD | S9(09) COMP | ZEROS | CICS RESP code |
| WS-REAS-CD | S9(09) COMP | ZEROS | CICS RESP2 code |
| WS-USR-MODIFIED | X(01) | 'N' | User-modified flag (declared, not used in logic) |
| WS-CONF-PAY-FLG | X(01) | 'N' | Confirmation flag; 88 CONF-PAY-YES = 'Y', NO = 'N' |
| WS-TRAN-AMT | PIC +99999999.99 | — | Display-formatted transaction amount |
| WS-CURR-BAL | PIC +9999999999.99 | — | Display-formatted current balance |
| WS-TRAN-ID-NUM | 9(16) | ZEROS | Numeric working field for new transaction ID |
| WS-TRAN-DATE | X(08) | '00/00/00' | Date working field |
| WS-ABS-TIME | S9(15) COMP-3 | 0 | CICS ASKTIME output |
| WS-CUR-DATE-X10 | X(10) | SPACES | FORMATTIME YYYYMMDD output |
| WS-CUR-TIME-X08 | X(08) | SPACES | FORMATTIME TIME output |

### 4.2 Copybook-Sourced Fields

**COCOM01Y.cpy — CARDDEMO-COMMAREA (lines 19–47 of copybook)**

The full commarea structure, plus program-level extension CDEMO-CB00-INFO defined inline in COBIL00C.cbl lines 64–72:

| Field | PIC | Purpose |
|---|---|---|
| CDEMO-FROM-TRANID | X(04) | Caller's transaction ID |
| CDEMO-FROM-PROGRAM | X(08) | Caller program name |
| CDEMO-TO-PROGRAM | X(08) | Target program for XCTL |
| CDEMO-USER-ID | X(08) | Signed-on user ID |
| CDEMO-USER-TYPE | X(01) | 'A'=Admin, 'U'=User |
| CDEMO-PGM-CONTEXT | 9(01) | 0=first entry, 1=re-entry |
| CDEMO-CB00-TRN-SELECTED | X(16) | Transaction ID pre-selected by caller |

**CVACT01Y.cpy — ACCOUNT-RECORD (300-byte KSDS record)**

| Field | PIC | Purpose |
|---|---|---|
| ACCT-ID | 9(11) | Account key |
| ACCT-ACTIVE-STATUS | X(01) | Active/inactive flag |
| ACCT-CURR-BAL | S9(10)V99 | Current balance (updated on payment) |
| ACCT-CREDIT-LIMIT | S9(10)V99 | Credit limit |
| ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | Cash credit limit |
| ACCT-OPEN-DATE | X(10) | Account open date |
| ACCT-EXPIRAION-DATE | X(10) | Expiration date |

**CVACT03Y.cpy — CARD-XREF-RECORD (50-byte KSDS record)**

| Field | PIC | Purpose |
|---|---|---|
| XREF-CARD-NUM | X(16) | Card number (written to TRAN-CARD-NUM) |
| XREF-CUST-ID | 9(09) | Customer ID |
| XREF-ACCT-ID | 9(11) | Account ID (used as key to read CXACAIX) |

**CVTRA05Y.cpy — TRAN-RECORD (350-byte KSDS record)**

| Field | PIC | Value Set at Payment |
|---|---|---|
| TRAN-ID | X(16) | Last TRAN-ID + 1 (auto-generated) |
| TRAN-TYPE-CD | X(02) | '02' |
| TRAN-CAT-CD | 9(04) | 2 |
| TRAN-SOURCE | X(10) | 'POS TERM' |
| TRAN-DESC | X(100) | 'BILL PAYMENT - ONLINE' |
| TRAN-AMT | S9(09)V99 | ACCT-CURR-BAL (full balance) |
| TRAN-MERCHANT-ID | 9(09) | 999999999 |
| TRAN-MERCHANT-NAME | X(50) | 'BILL PAYMENT' |
| TRAN-MERCHANT-CITY | X(50) | 'N/A' |
| TRAN-MERCHANT-ZIP | X(10) | 'N/A' |
| TRAN-CARD-NUM | X(16) | XREF-CARD-NUM from CXACAIX |
| TRAN-ORIG-TS | X(26) | WS-TIMESTAMP at time of payment |
| TRAN-PROC-TS | X(26) | WS-TIMESTAMP at time of payment |

**CSDAT01Y.cpy — WS-DATE-TIME**
Provides date/time decomposition fields used in POPULATE-HEADER-INFO and GET-CURRENT-TIMESTAMP. The WS-TIMESTAMP sub-structure (format `YYYY-MM-DD HH:MM:SS.microseconds`) is built in GET-CURRENT-TIMESTAMP using CICS ASKTIME / FORMATTIME.

### 4.3 Linkage Section (COBIL00C.cbl lines 91–93)

```
01  DFHCOMMAREA.
  05  LK-COMMAREA  PIC X(01) OCCURS 1 TO 32767 DEPENDING ON EIBCALEN.
```
The commarea received on entry is immediately moved to CARDDEMO-COMMAREA at line 111.

---

## 5. CICS Commands

| Command | Paragraph | Purpose | Source Reference |
|---|---|---|---|
| EXEC CICS RETURN TRANSID COMMAREA | MAIN-PARA | Pseudo-conversational return, setting CB00 as next transid | Line 146–149 |
| EXEC CICS XCTL PROGRAM COMMAREA | RETURN-TO-PREV-SCREEN | Transfer control to previous/next program | Lines 281–284 |
| EXEC CICS SEND MAP MAPSET FROM ERASE CURSOR | SEND-BILLPAY-SCREEN | Send COBIL0A map to terminal | Lines 295–301 |
| EXEC CICS RECEIVE MAP MAPSET INTO RESP RESP2 | RECEIVE-BILLPAY-SCREEN | Receive user input from COBIL0A | Lines 308–314 |
| EXEC CICS ASKTIME ABSTIME | GET-CURRENT-TIMESTAMP | Obtain absolute time | Lines 251–253 |
| EXEC CICS FORMATTIME ABSTIME YYYYMMDD DATESEP TIME TIMESEP | GET-CURRENT-TIMESTAMP | Format date/time for timestamp | Lines 255–261 |
| EXEC CICS READ DATASET INTO RIDFLD UPDATE RESP RESP2 | READ-ACCTDAT-FILE | Read ACCTDAT for update (exclusive lock) | Lines 345–354 |
| EXEC CICS REWRITE DATASET FROM RESP RESP2 | UPDATE-ACCTDAT-FILE | Rewrite updated ACCOUNT-RECORD | Lines 379–385 |
| EXEC CICS READ DATASET INTO RIDFLD RESP RESP2 | READ-CXACAIX-FILE | Read CXACAIX alternate index by account ID | Lines 410–418 |
| EXEC CICS STARTBR DATASET RIDFLD RESP RESP2 | STARTBR-TRANSACT-FILE | Start browse of TRANSACT at HIGH-VALUES | Lines 443–448 |
| EXEC CICS READPREV DATASET INTO RIDFLD RESP RESP2 | READPREV-TRANSACT-FILE | Read last transaction record (highest key) | Lines 474–482 |
| EXEC CICS ENDBR DATASET | ENDBR-TRANSACT-FILE | End browse of TRANSACT | Lines 503–505 |
| EXEC CICS WRITE DATASET FROM RIDFLD RESP RESP2 | WRITE-TRANSACT-FILE | Write new payment transaction record | Lines 512–520 |

---

## 6. Paragraph-by-Paragraph Logic

### MAIN-PARA (lines 99–149)

Entry point. Executed on every CICS pseudo-conversational re-entry under transaction CB00.

1. Initializes WS-ERR-FLG to 'N', WS-USR-MODIFIED to 'N', clears WS-MESSAGE and ERRMSGO.
2. If EIBCALEN = 0 (no commarea — direct invocation without sign-on), sets CDEMO-TO-PROGRAM = 'COSGN00C' and performs RETURN-TO-PREV-SCREEN to redirect to the sign-on program.
3. Otherwise, moves DFHCOMMAREA to CARDDEMO-COMMAREA.
4. If this is the first entry (CDEMO-PGM-CONTEXT = 0, i.e., CDEMO-PGM-ENTER):
   - Sets CDEMO-PGM-REENTER (context = 1).
   - Initializes map output area COBIL0AO to LOW-VALUES.
   - Sets cursor on ACTIDINL.
   - If CDEMO-CB00-TRN-SELECTED is populated (a transaction was pre-selected by a caller), moves it to ACTIDINI and performs PROCESS-ENTER-KEY.
   - Performs SEND-BILLPAY-SCREEN.
5. If this is a re-entry (CDEMO-PGM-REENTER):
   - Performs RECEIVE-BILLPAY-SCREEN to capture user input.
   - Evaluates EIBAID:
     - DFHENTER: PROCESS-ENTER-KEY
     - DFHPF3: Return to CDEMO-FROM-PROGRAM (or COMEN01C if blank) via RETURN-TO-PREV-SCREEN
     - DFHPF4: CLEAR-CURRENT-SCREEN
     - Other: sets error flag, displays 'Invalid key pressed...' message, re-sends screen
6. Falls through to EXEC CICS RETURN to set CB00 as next transaction.

### PROCESS-ENTER-KEY (lines 154–244)

Validates input and orchestrates payment execution.

1. Sets CONF-PAY-NO.
2. If ACTIDINI is SPACES or LOW-VALUES: sets error, message 'Acct ID can NOT be empty...', cursor on ACTIDINL, performs SEND-BILLPAY-SCREEN and returns.
3. Moves ACTIDINI to ACCT-ID and XREF-ACCT-ID.
4. Evaluates CONFIRMI:
   - 'Y' or 'y': sets CONF-PAY-YES, performs READ-ACCTDAT-FILE.
   - 'N' or 'n': calls CLEAR-CURRENT-SCREEN, sets WS-ERR-FLG = 'Y'.
   - SPACES or LOW-VALUES (first pass, no confirmation yet): performs READ-ACCTDAT-FILE only (to display balance).
   - Other: sets error, message 'Invalid value. Valid values are (Y/N)...', cursor on CONFIRML.
5. Moves ACCT-CURR-BAL to WS-CURR-BAL and to CURBALI of COBIL0AI for display.
6. If no error and balance <= 0: sets error, message 'You have nothing to pay...', cursor on ACTIDINL.
7. If no error and CONF-PAY-YES:
   - Reads CXACAIX to obtain card number (XREF-CARD-NUM).
   - Starts browse of TRANSACT at HIGH-VALUES.
   - Reads previous record (last transaction by key) to obtain current highest TRAN-ID.
   - Ends browse.
   - Moves TRAN-ID to WS-TRAN-ID-NUM, adds 1, then uses as new TRAN-ID.
   - Initializes TRAN-RECORD and populates all fields (type '02', category 2, source 'POS TERM', description 'BILL PAYMENT - ONLINE', full balance amount, card number, merchant data).
   - Calls GET-CURRENT-TIMESTAMP to build WS-TIMESTAMP; populates both TRAN-ORIG-TS and TRAN-PROC-TS.
   - Calls WRITE-TRANSACT-FILE; on success computes ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT (effectively zeroing the balance) and calls UPDATE-ACCTDAT-FILE.
8. If no error and CONF-PAY-NO (first pass showing balance): sets message 'Confirm to make a bill payment...', cursor on CONFIRML.
9. Performs SEND-BILLPAY-SCREEN.

### GET-CURRENT-TIMESTAMP (lines 249–267)

Uses CICS ASKTIME to get WS-ABS-TIME, then FORMATTIME to produce a date string in YYYYMMDD format (with '-' separator) into WS-CUR-DATE-X10 and a time string (with ':' separator) into WS-CUR-TIME-X08. Assembles WS-TIMESTAMP as `YYYY-MM-DD HH:MM:SS.000000`. Zero-fills WS-TIMESTAMP-TM-MS6 (microseconds).

### RETURN-TO-PREV-SCREEN (lines 273–284)

Sets CDEMO-FROM-TRANID = WS-TRANID ('CB00'), CDEMO-FROM-PROGRAM = 'COBIL00C', CDEMO-PGM-CONTEXT = 0, then issues EXEC CICS XCTL to CDEMO-TO-PROGRAM passing CARDDEMO-COMMAREA.

### SEND-BILLPAY-SCREEN (lines 289–301)

Performs POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO, issues EXEC CICS SEND MAP('COBIL0A') MAPSET('COBIL00') FROM(COBIL0AO) ERASE CURSOR.

### RECEIVE-BILLPAY-SCREEN (lines 306–314)

Issues EXEC CICS RECEIVE MAP('COBIL0A') MAPSET('COBIL00') INTO(COBIL0AI) capturing RESP and RESP2.

### POPULATE-HEADER-INFO (lines 319–338)

Calls FUNCTION CURRENT-DATE into WS-CURDATE-DATA (from CSDAT01Y). Moves title lines from COTTL01Y (CCDA-TITLE01, CCDA-TITLE02) and current transaction ID / program name to map header fields. Formats date as MM/DD/YY and time as HH:MM:SS.

### READ-ACCTDAT-FILE (lines 343–372)

EXEC CICS READ DATASET('ACCTDAT') INTO(ACCOUNT-RECORD) RIDFLD(ACCT-ID) with UPDATE (exclusive lock for potential subsequent REWRITE). Handles NOTFND ('Account ID NOT found...') and OTHER errors.

### UPDATE-ACCTDAT-FILE (lines 377–403)

EXEC CICS REWRITE DATASET('ACCTDAT') FROM(ACCOUNT-RECORD). Handles NOTFND and OTHER errors.

### READ-CXACAIX-FILE (lines 408–436)

EXEC CICS READ DATASET('CXACAIX') INTO(CARD-XREF-RECORD) RIDFLD(XREF-ACCT-ID). This reads through the alternate index to retrieve the card number associated with the account. Handles NOTFND and OTHER errors.

### STARTBR-TRANSACT-FILE (lines 441–467)

EXEC CICS STARTBR DATASET('TRANSACT') RIDFLD(TRAN-ID) where TRAN-ID is pre-set to HIGH-VALUES. This positions the browse at the logical end of the file. Handles NOTFND and OTHER errors.

### READPREV-TRANSACT-FILE (lines 472–496)

EXEC CICS READPREV DATASET('TRANSACT') INTO(TRAN-RECORD) RIDFLD(TRAN-ID). Reads one record backwards from HIGH-VALUES to obtain the last (highest-keyed) transaction record. ENDFILE condition (empty file) sets TRAN-ID to ZEROS. OTHER errors are treated as failure.

### ENDBR-TRANSACT-FILE (lines 501–505)

EXEC CICS ENDBR DATASET('TRANSACT'). No error handling; unchecked.

### WRITE-TRANSACT-FILE (lines 510–547)

EXEC CICS WRITE DATASET('TRANSACT') FROM(TRAN-RECORD) RIDFLD(TRAN-ID). On NORMAL: clears fields, sets ERRMSGC to DFHGREEN, builds success message 'Payment successful. Your Transaction ID is NNNN.' and calls SEND-BILLPAY-SCREEN. DUPKEY/DUPREC: 'Tran ID already exist...' error. OTHER: 'Unable to Add Bill pay Transaction...' error.

### CLEAR-CURRENT-SCREEN (lines 552–555)

Performs INITIALIZE-ALL-FIELDS then SEND-BILLPAY-SCREEN.

### INITIALIZE-ALL-FIELDS (lines 560–566)

Moves -1 to ACTIDINL (cursor position), SPACES to ACTIDINI, CURBALI, CONFIRMI, and WS-MESSAGE.

---

## 7. Program Flow Diagram

```
Entry (Transaction CB00)
        |
        v
EIBCALEN = 0? --YES--> RETURN-TO-PREV-SCREEN (XCTL to COSGN00C)
        |
        NO
        |
        v
CDEMO-PGM-ENTER? --YES--> Set REENTER, Init screen
        |                  Pre-selected TRN? -> PROCESS-ENTER-KEY
        |                  SEND-BILLPAY-SCREEN
        |                  RETURN CB00
        NO
        |
        v
RECEIVE-BILLPAY-SCREEN
        |
        v
EIBAID?
  ENTER -> PROCESS-ENTER-KEY:
    |  ACTIDINI empty? -> Error, SEND screen
    |  CONFIRMI = Y/y -> READ-ACCTDAT (UPDATE)
    |                    Balance <= 0? -> Error, SEND screen
    |                    READ-CXACAIX
    |                    STARTBR TRANSACT (HIGH-VALUES)
    |                    READPREV TRANSACT (get last TRAN-ID)
    |                    ENDBR TRANSACT
    |                    Build TRAN-RECORD
    |                    GET-CURRENT-TIMESTAMP
    |                    WRITE-TRANSACT-FILE
    |                    COMPUTE balance - payment
    |                    UPDATE-ACCTDAT-FILE
    |                    SEND screen (green success message)
    |  CONFIRMI = N/n -> CLEAR screen
    |  CONFIRMI = blank -> READ-ACCTDAT (show balance, prompt confirm)
    |                      SEND screen (prompt message)
  PF3 -> RETURN-TO-PREV-SCREEN (XCTL to COMEN01C or CDEMO-FROM-PROGRAM)
  PF4 -> CLEAR-CURRENT-SCREEN
  Other -> Error message, SEND screen
        |
        v
RETURN CB00 (pseudo-conversational)
```

---

## 8. Inter-Program Interactions

| Direction | Mechanism | Target Program | Condition | Source Reference |
|---|---|---|---|---|
| Called by | XCTL | COBIL00C | User selects bill pay from COMEN01C menu | Inferred from CDEMO-FROM-PROGRAM pattern |
| Calls | XCTL | COSGN00C | EIBCALEN = 0 (no commarea) | Lines 108–109 |
| Calls | XCTL | COMEN01C | PF3, no CDEMO-FROM-PROGRAM | Lines 130–135 |
| Calls | XCTL | CDEMO-FROM-PROGRAM | PF3, with CDEMO-FROM-PROGRAM set | Lines 132–135 |

No CICS LINK or batch CALL statements are present. All inter-program communication uses XCTL and commarea passing.

---

## 9. File Resources Accessed

| CICS Dataset | Record Structure | Access Mode | Key | Source Reference |
|---|---|---|---|---|
| ACCTDAT | ACCOUNT-RECORD (CVACT01Y) | READ with UPDATE, REWRITE | ACCT-ID (9(11)) | Lines 345, 379 |
| CXACAIX | CARD-XREF-RECORD (CVACT03Y) | READ (alternate index by XREF-ACCT-ID) | XREF-ACCT-ID (9(11)) | Lines 410–418 |
| TRANSACT | TRAN-RECORD (CVTRA05Y) | STARTBR / READPREV / ENDBR / WRITE | TRAN-ID (X(16)) | Lines 443, 474, 503, 512 |

---

## 10. Error Handling

All errors set WS-ERR-FLG = 'Y' (ERR-FLG-ON) and perform SEND-BILLPAY-SCREEN, which re-displays the map with the error message in ERRMSGO. The program does NOT issue CICS ABEND on any error; all conditions are handled by user message display.

| Condition | Message Text | Cursor Field | Source Reference |
|---|---|---|---|
| ACTIDINI empty | 'Acct ID can NOT be empty...' | ACTIDINL | Lines 161–164 |
| CONFIRMI invalid | 'Invalid value. Valid values are (Y/N)...' | CONFIRML | Lines 187–190 |
| ACCTDAT NOTFND | 'Account ID NOT found...' | ACTIDINL | Lines 361–364 |
| ACCTDAT OTHER | 'Unable to lookup Account...' | ACTIDINL | Lines 366–371 |
| ACCTDAT REWRITE NOTFND | 'Account ID NOT found...' | ACTIDINL | Lines 392–395 |
| ACCTDAT REWRITE OTHER | 'Unable to Update Account...' | ACTIDINL | Lines 397–402 |
| Balance <= 0 | 'You have nothing to pay...' | ACTIDINL | Lines 202–205 |
| CXACAIX NOTFND | 'Account ID NOT found...' | ACTIDINL | Lines 424–427 |
| CXACAIX OTHER | 'Unable to lookup XREF AIX file...' | ACTIDINL | Lines 430–435 |
| TRANSACT STARTBR NOTFND | 'Transaction ID NOT found...' | ACTIDINL | Lines 455–459 |
| TRANSACT STARTBR OTHER | 'Unable to lookup Transaction...' | ACTIDINL | Lines 461–466 |
| TRANSACT READPREV ENDFILE | TRAN-ID = ZEROS (empty file, handled silently) | — | Lines 487–488 |
| TRANSACT READPREV OTHER | 'Unable to lookup Transaction...' | ACTIDINL | Lines 491–495 |
| TRANSACT WRITE DUPKEY/DUPREC | 'Tran ID already exist...' | ACTIDINL | Lines 534–539 |
| TRANSACT WRITE OTHER | 'Unable to Add Bill pay Transaction...' | ACTIDINL | Lines 541–546 |
| CONFIRMI = 'N'/'n' | (no message; screen cleared) | ACTIDINL | Lines 179–181 |
| CONFIRMI = blank (first pass) | 'Confirm to make a bill payment...' | CONFIRML | Lines 237–239 |
| Invalid AID key | 'Invalid key pressed. Please see below...' | — | Lines 139–141 |

---

## 11. Transaction Flow

COBIL00C participates in the CardDemo online transaction flow as follows:

1. User is signed on via COSGN00C (transaction COSGN).
2. User navigates to the main menu COMEN01C (or admin menu COADM01C).
3. From the menu, the user selects the Bill Payment option; the menu program XCTLs to COBIL00C with CARDDEMO-COMMAREA populated.
4. COBIL00C displays the COBIL0A screen under transaction CB00.
5. Interaction is pseudo-conversational: each user keystroke triggers a new invocation of CB00 -> COBIL00C.
6. On PF3, COBIL00C XCTLs back to the calling menu program (COMEN01C or CDEMO-FROM-PROGRAM).

---

## 12. Business Rules

| Rule | Condition | Outcome | Source Reference |
|---|---|---|---|
| Account ID is mandatory | ACTIDINI = SPACES or LOW-VALUES | Error; payment blocked | Lines 159–164 |
| Two-phase confirmation required | First Enter with blank CONFIRM | Show balance, prompt for Y/N | Lines 183–184, 237–239 |
| Payment amount equals full balance | CONF-PAY-YES | TRAN-AMT = ACCT-CURR-BAL | Line 224 |
| Zero or negative balance rejected | ACCT-CURR-BAL <= ZEROS | Error; payment blocked | Lines 198–205 |
| New transaction ID = last ID + 1 | Always | Sequential TRAN-ID generation via STARTBR/READPREV | Lines 212–217 |
| Balance decremented by payment | Post-write | ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT | Line 234 |
| Payment type fixed as '02' | Always | TRAN-TYPE-CD = '02' | Line 220 |
| Payment category fixed as 2 | Always | TRAN-CAT-CD = 2 | Line 221 |

---

## 13. Open Questions and Gaps

1. **COBSWAIT/batch relationship**: This program is entirely online; no batch component is involved in the bill payment flow. The gap in COBIL00C.cbl line 64 shows CDEMO-CB00-INFO is defined inline after the COPY COCOM01Y directive rather than inside COCOM01Y itself — the exact extent of COCOM01Y's generated text must be confirmed against the actual compiled copybook.
2. **READPREV on empty TRANSACT**: If the TRANSACT file is truly empty, STARTBR with RIDFLD = HIGH-VALUES returns NOTFND, not NORMAL, which would set ERR-FLG-ON and block payment. The READPREV ENDFILE path (lines 487–488, sets TRAN-ID = 0) would never be reached. This is an edge case that may prevent the first-ever payment transaction from being written.
3. **ACCTDAT record lock**: The READ with UPDATE at line 345 acquires an exclusive lock. If the program terminates abnormally before the REWRITE, the lock will remain until the task ends (CICS automatic backout). Normal path always issues REWRITE before the RETURN.
4. **Timestamp microseconds**: WS-TIMESTAMP-TM-MS6 is always set to ZEROS (line 266), meaning sub-second precision is never captured.
