# Technical Specification: COTRN02C — Transaction Add Program

## 1. Executive Summary

COTRN02C is an online CICS COBOL program in the CardDemo application that accepts user input to add a new transaction record to the TRANSACT VSAM file. Despite the source comment header labeling its function as "Add a new Transaction to TRANSACT file" and the BMS screen title "Add Transaction", the file header at line 5 also bears the label "Add" while the program binary label (`WS-TRANID = 'CT02'`) and the BMS screen confirm this is the add/create program. The program performs account/card cross-reference lookup (via CCXREF and CXACAIX files), validates all input fields including date format using the external CSUTLDTC utility, determines the next Transaction ID by reading the last existing record, and writes the new record with EXEC CICS WRITE. A two-step confirm pattern (Y/N) prevents accidental submission.

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COTRN02C.CBL | CICS COBOL program | app/cbl/COTRN02C.cbl |
| COTRN02.BMS | BMS mapset | app/bms/COTRN02.bms |
| COTRN02.CPY | BMS-generated copybook | app/cpy-bms/COTRN02.CPY |
| COCOM01Y.CPY | Common COMMAREA copybook | app/cpy/COCOM01Y.cpy |
| CVTRA05Y.CPY | Transaction record layout | app/cpy/CVTRA05Y.cpy |
| CVACT01Y.CPY | Account record layout | app/cpy/CVACT01Y.cpy |
| CVACT03Y.CPY | Card cross-reference record layout | app/cpy/CVACT03Y.cpy |
| COTTL01Y.CPY | Screen title constants | app/cpy/COTTL01Y.cpy |
| CSDAT01Y.CPY | Date/time working storage | app/cpy/CSDAT01Y.cpy |
| CSMSG01Y.CPY | Common message constants | app/cpy/CSMSG01Y.cpy |
| CSUTLDTC | External COBOL subprogram (CALL) | not in analyzed source |
| DFHAID | CICS-supplied AID key constants | system |
| DFHBMSCA | CICS-supplied BMS attribute constants | system |

---

## 3. Program Identity

| Attribute | Value |
|---|---|
| Program name | COTRN02C |
| CICS Transaction ID | CT02 |
| Source file | COTRN02C.CBL |
| Version stamp | CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19 |
| BMS Mapset | COTRN02 |
| BMS Map | COTRN2A |

---

## 4. CICS Commands Used

| Command | Purpose | Paragraph |
|---|---|---|
| `EXEC CICS RETURN TRANSID(CT02) COMMAREA(CARDDEMO-COMMAREA)` | Pseudo-conversational return | MAIN-PARA (line 156) and SEND-TRNADD-SCREEN (line 530) |
| `EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)` | Transfer to previous screen or signon | RETURN-TO-PREV-SCREEN (line 508) |
| `EXEC CICS SEND MAP('COTRN2A') MAPSET('COTRN02') FROM(COTRN2AO) ERASE CURSOR` | Send add screen | SEND-TRNADD-SCREEN (line 522) |
| `EXEC CICS RECEIVE MAP('COTRN2A') MAPSET('COTRN02') INTO(COTRN2AI)` | Receive operator input | RECEIVE-TRNADD-SCREEN (line 541) |
| `EXEC CICS READ DATASET('CXACAIX') INTO(CARD-XREF-RECORD) RIDFLD(XREF-ACCT-ID)` | Lookup card number by account ID (AIX) | READ-CXACAIX-FILE (line 578) |
| `EXEC CICS READ DATASET('CCXREF') INTO(CARD-XREF-RECORD) RIDFLD(XREF-CARD-NUM)` | Lookup account ID by card number | READ-CCXREF-FILE (line 611) |
| `EXEC CICS STARTBR DATASET('TRANSACT') RIDFLD(TRAN-ID)` | Begin browse to find last key | STARTBR-TRANSACT-FILE (line 644) |
| `EXEC CICS READPREV DATASET('TRANSACT') INTO(TRAN-RECORD) RIDFLD(TRAN-ID)` | Read last record to determine new ID | READPREV-TRANSACT-FILE (line 675) |
| `EXEC CICS ENDBR DATASET('TRANSACT')` | End browse | ENDBR-TRANSACT-FILE (line 704) |
| `EXEC CICS WRITE DATASET('TRANSACT') FROM(TRAN-RECORD) RIDFLD(TRAN-ID)` | Write new transaction record | WRITE-TRANSACT-FILE (line 713) |

---

## 5. Copybooks Referenced

### COCOM01Y.CPY — CARDDEMO-COMMAREA
Global COMMAREA. See COTRN00C_spec.md Section 5 for full field listing.

Program-local COMMAREA extension (lines 72–80):

```
05 CDEMO-CT02-INFO.
   10 CDEMO-CT02-TRNID-FIRST     PIC X(16)
   10 CDEMO-CT02-TRNID-LAST      PIC X(16)
   10 CDEMO-CT02-PAGE-NUM        PIC 9(08)
   10 CDEMO-CT02-NEXT-PAGE-FLG   PIC X(01)  -- 'Y'=next page
   10 CDEMO-CT02-TRN-SEL-FLG     PIC X(01)  -- selection flag
   10 CDEMO-CT02-TRN-SELECTED    PIC X(16)  -- selected tran ID (used to pre-fill card #)
```

When control arrives from COTRN00C/COTRN01C with a pre-selected transaction, `CDEMO-CT02-TRN-SELECTED` is moved to `CARDNINI` of COTRN2AI at first entry (line 127).

### CVTRA05Y.CPY — TRAN-RECORD (350 bytes)
Full transaction layout. See COTRN00C_spec.md Section 5 for field listing. Used for both reading (READPREV to find last key) and writing (WRITE new record).

### CVACT01Y.CPY — ACCOUNT-RECORD (300 bytes)
Source: app/cpy/CVACT01Y.cpy.

| Field | PIC | Description |
|---|---|---|
| ACCT-ID | 9(11) | Account identifier |
| ACCT-ACTIVE-STATUS | X(01) | Account status |
| ACCT-CURR-BAL | S9(10)V99 | Current balance |
| ACCT-CREDIT-LIMIT | S9(10)V99 | Credit limit |
| ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | Cash credit limit |
| ACCT-OPEN-DATE | X(10) | Account open date |
| ACCT-EXPIRAION-DATE | X(10) | Expiration date |
| ACCT-REISSUE-DATE | X(10) | Reissue date |
| ACCT-CURR-CYC-CREDIT | S9(10)V99 | Current cycle credit |
| ACCT-CURR-CYC-DEBIT | S9(10)V99 | Current cycle debit |
| ACCT-ADDR-ZIP | X(10) | Address ZIP |
| ACCT-GROUP-ID | X(10) | Group ID |
| FILLER | X(178) | Reserved |

Note: CVACT01Y is copied into COTRN02C (line 89) but the ACCOUNT-RECORD structure is not directly accessed by COTRN02C's procedure logic. The copy may be present for compile-time alignment with other programs using the same data division block.

### CVACT03Y.CPY — CARD-XREF-RECORD (50 bytes)
Source: app/cpy/CVACT03Y.cpy.

| Field | PIC | Description |
|---|---|---|
| XREF-CARD-NUM | X(16) | Card number (primary KSDS key for CCXREF) |
| XREF-CUST-ID | 9(09) | Customer ID |
| XREF-ACCT-ID | 9(11) | Account ID (AIX key for CXACAIX) |
| FILLER | X(14) | Reserved |

### COTRN02.CPY — BMS-Generated Map Symbolic Description
Generated from COTRN02.BMS. Defines:
- `COTRN2AI` — input symbolic map
- `COTRN2AO` — output symbolic map (REDEFINES COTRN2AI)

Key map fields (source: app/cpy-bms/COTRN02.CPY):

| Symbolic Name | PIC | Direction | Purpose |
|---|---|---|---|
| ACTIDINI / ACTIDINO | X(11) | In/Out | Account ID entry field |
| ACTIDINL | S9(4) COMP | In | Cursor length control |
| CARDNINI / CARDNINO | X(16) | In/Out | Card number entry field |
| CARDNINL | S9(4) COMP | In | Cursor length control |
| TTYPCDI / TTYPCDO | X(2) | In/Out | Transaction type code |
| TTYPCDL | S9(4) COMP | In | Cursor control |
| TCATCDI / TCATCDO | X(4) | In/Out | Category code |
| TCATCDL | S9(4) COMP | In | Cursor control |
| TRNSRCI / TRNSRCO | X(10) | In/Out | Transaction source |
| TRNSRCL | S9(4) COMP | In | Cursor control |
| TDESCI / TDESCO | X(60) | In/Out | Description |
| TDESCL | S9(4) COMP | In | Cursor control |
| TRNAMTI / TRNAMTO | X(12) | In/Out | Amount (format: +/-99999999.99) |
| TRNAMTL | S9(4) COMP | In | Cursor control |
| TORIGDTI / TORIGDTO | X(10) | In/Out | Original date (YYYY-MM-DD) |
| TORIGDTL | S9(4) COMP | In | Cursor control |
| TPROCDTI / TPROCDTO | X(10) | In/Out | Processing date (YYYY-MM-DD) |
| TPROCDTL | S9(4) COMP | In | Cursor control |
| MIDI / MIDO | X(9) | In/Out | Merchant ID |
| MIDL | S9(4) COMP | In | Cursor control |
| MNAMEI / MNAMEO | X(30) | In/Out | Merchant name |
| MNAMEL | S9(4) COMP | In | Cursor control |
| MCITYI / MCITYO | X(25) | In/Out | Merchant city |
| MCITYL | S9(4) COMP | In | Cursor control |
| MZIPI / MZIPO | X(10) | In/Out | Merchant ZIP |
| MZIPL | S9(4) COMP | In | Cursor control |
| CONFIRMI / CONFIRMO | X(1) | In/Out | Confirmation flag (Y/N) |
| CONFIRML | S9(4) COMP | In | Cursor control |
| ERRMSGI / ERRMSGO | X(78) | Out | Error/status message |
| ERRMSGC | PICTURE X | Out | Color byte for ERRMSG (used to set GREEN on success) |

### CSUTLDTC-PARM (inline, not a copybook)
Defined in WORKING-STORAGE at lines 62–69:

```
01 CSUTLDTC-PARM.
   05 CSUTLDTC-DATE             PIC X(10)   -- date to validate
   05 CSUTLDTC-DATE-FORMAT      PIC X(10)   -- format string ('YYYY-MM-DD')
   05 CSUTLDTC-RESULT.
      10 CSUTLDTC-RESULT-SEV-CD PIC X(04)   -- '0000' = success
      10 FILLER                 PIC X(11)
      10 CSUTLDTC-RESULT-MSG-NUM PIC X(04)  -- '2513' = acceptable warning
      10 CSUTLDTC-RESULT-MSG    PIC X(61)   -- message text
```

---

## 6. Working Storage Variables

| Field | PIC | Value | Purpose |
|---|---|---|---|
| WS-PGMNAME | X(08) | 'COTRN02C' | Program name |
| WS-TRANID | X(04) | 'CT02' | Transaction ID |
| WS-MESSAGE | X(80) | SPACES | Message buffer |
| WS-TRANSACT-FILE | X(08) | 'TRANSACT' | VSAM TRANSACT dataset |
| WS-ACCTDAT-FILE | X(08) | 'ACCTDAT ' | Account data file (declared, not used in procedure) |
| WS-CCXREF-FILE | X(08) | 'CCXREF  ' | Card-to-account cross-reference KSDS |
| WS-CXACAIX-FILE | X(08) | 'CXACAIX ' | Account-to-card AIX (alternate index) |
| WS-ERR-FLG | X(01) | 'N' | Error flag |
| WS-RESP-CD | S9(09) COMP | 0 | CICS RESP |
| WS-REAS-CD | S9(09) COMP | 0 | CICS RESP2 |
| WS-USR-MODIFIED | X(01) | 'N' | User-modified flag (declared, not functionally used) |
| WS-TRAN-AMT | PIC +99999999.99 | — | Formatted display amount |
| WS-TRAN-DATE | X(08) | '00/00/00' | Date work field |
| WS-ACCT-ID-N | 9(11) | 0 | Numeric account ID for NUMVAL conversion |
| WS-CARD-NUM-N | 9(16) | 0 | Numeric card number for NUMVAL conversion |
| WS-TRAN-ID-N | 9(16) | ZEROS | Numeric transaction ID; last ID + 1 = new key |
| WS-TRAN-AMT-N | S9(9)V99 | ZERO | Numeric amount from NUMVAL-C |
| WS-TRAN-AMT-E | PIC +99999999.99 | ZEROS | Edited amount for screen display |
| WS-DATE-FORMAT | X(10) | 'YYYY-MM-DD' | Date format string passed to CSUTLDTC |

---

## 7. Program Flow — Paragraph-by-Paragraph

### MAIN-PARA (entry point, line 106)

```
Set ERR-FLG-OFF, USR-MODIFIED-NO
Clear WS-MESSAGE and ERRMSGO

IF EIBCALEN = 0
    CDEMO-TO-PROGRAM = 'COSGN00C'
    PERFORM RETURN-TO-PREV-SCREEN
ELSE
    Move DFHCOMMAREA into CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER (first entry)
        Set CDEMO-PGM-REENTER = 1
        Move LOW-VALUES to COTRN2AO
        Move -1 to ACTIDINL
        IF CDEMO-CT02-TRN-SELECTED not spaces/low-values
            Move CDEMO-CT02-TRN-SELECTED to CARDNINI  (pre-fill card number)
            PERFORM PROCESS-ENTER-KEY
        END-IF
        PERFORM SEND-TRNADD-SCREEN
    ELSE (re-entry)
        PERFORM RECEIVE-TRNADD-SCREEN
        EVALUATE EIBAID
            DFHENTER → PERFORM PROCESS-ENTER-KEY
            DFHPF3   → CDEMO-TO-PROGRAM = CDEMO-FROM-PROGRAM (or 'COMEN01C')
                       PERFORM RETURN-TO-PREV-SCREEN
            DFHPF4   → PERFORM CLEAR-CURRENT-SCREEN
            DFHPF5   → PERFORM COPY-LAST-TRAN-DATA
            OTHER    → set ERR-FLG, message CCDA-MSG-INVALID-KEY
                       PERFORM SEND-TRNADD-SCREEN
        END-EVALUATE
    END-IF
END-IF

EXEC CICS RETURN TRANSID(CT02) COMMAREA(CARDDEMO-COMMAREA)
```

### PROCESS-ENTER-KEY (line 164)

High-level flow:
1. PERFORM VALIDATE-INPUT-KEY-FIELDS — validates account or card number.
2. PERFORM VALIDATE-INPUT-DATA-FIELDS — validates all transaction fields.
3. EVALUATE CONFIRMI:
   - 'Y' or 'y': PERFORM ADD-TRANSACTION.
   - 'N', 'n', SPACES, LOW-VALUES: sets ERR-FLG, message "Confirm to add this transaction...", cursor on CONFIRML, sends screen.
   - OTHER: sets ERR-FLG, message "Invalid value. Valid values are (Y/N)...", sends screen.

### VALIDATE-INPUT-KEY-FIELDS (line 193)

Determines the account/card cross-reference:

```
EVALUATE TRUE
    WHEN ACTIDINI not spaces/low-values
        Validate ACTIDINI is NUMERIC
        COMPUTE WS-ACCT-ID-N = NUMVAL(ACTIDINI)
        Move WS-ACCT-ID-N to XREF-ACCT-ID and ACTIDINI
        PERFORM READ-CXACAIX-FILE     -- AIX lookup: account ID → card number
        Move XREF-CARD-NUM to CARDNINI
    WHEN CARDNINI not spaces/low-values
        Validate CARDNINI is NUMERIC
        COMPUTE WS-CARD-NUM-N = NUMVAL(CARDNINI)
        Move WS-CARD-NUM-N to XREF-CARD-NUM and CARDNINI
        PERFORM READ-CCXREF-FILE      -- KSDS lookup: card number → account ID
        Move XREF-ACCT-ID to ACTIDINI
    WHEN OTHER
        Error: "Account or Card Number must be entered..."
        Cursor to ACTIDINL, send screen
END-EVALUATE
```

Either the account ID OR the card number may be provided; the program resolves the other via cross-reference.

### VALIDATE-INPUT-DATA-FIELDS (line 235)

If ERR-FLG-ON (from key validation), clears all data fields to SPACES first.

Sequential EVALUATE TRUE chain checks each required field for blank, then checks numeric/format constraints:

**Presence checks (all required):**
| Field | Error Message |
|---|---|
| TTYPCDI | "Type CD can NOT be empty..." |
| TCATCDI | "Category CD can NOT be empty..." |
| TRNSRCI | "Source can NOT be empty..." |
| TDESCI | "Description can NOT be empty..." |
| TRNAMTI | "Amount can NOT be empty..." |
| TORIGDTI | "Orig Date can NOT be empty..." |
| TPROCDTI | "Proc Date can NOT be empty..." |
| MIDI | "Merchant ID can NOT be empty..." |
| MNAMEI | "Merchant Name can NOT be empty..." |
| MCITYI | "Merchant City can NOT be empty..." |
| MZIPI | "Merchant Zip can NOT be empty..." |

**Type code numeric checks:**
- TTYPCDI must be NUMERIC.
- TCATCDI must be NUMERIC.

**Amount format check** (line 340–351):
- Position 1 must be '+' or '-'.
- Positions 2–9 must be NUMERIC.
- Position 10 must be '.'.
- Positions 11–12 must be NUMERIC.
- Error: "Amount should be in format -99999999.99".

**Original date format check** (lines 353–366):
- Positions 1–4 NUMERIC (year).
- Position 5 = '-'.
- Positions 6–7 NUMERIC (month).
- Position 8 = '-'.
- Positions 9–10 NUMERIC (day).
- Error: "Orig Date should be in format YYYY-MM-DD".

**Processing date format check** (lines 368–381): Same structure as original date.

**NUMVAL-C conversion** (line 383–386):
- `COMPUTE WS-TRAN-AMT-N = FUNCTION NUMVAL-C(TRNAMTI)` converts signed amount string to numeric.
- Moves through WS-TRAN-AMT-E back to TRNAMTI to normalize display.

**Date validation via CSUTLDTC** (lines 389–427):
- For both TORIGDTI and TPROCDTI:
  - Moves date to CSUTLDTC-DATE, 'YYYY-MM-DD' to CSUTLDTC-DATE-FORMAT.
  - `CALL 'CSUTLDTC' USING CSUTLDTC-DATE CSUTLDTC-DATE-FORMAT CSUTLDTC-RESULT`.
  - If CSUTLDTC-RESULT-SEV-CD ≠ '0000' AND MSG-NUM ≠ '2513': date is invalid. Sets error, sends screen.
  - Note: message number '2513' is treated as an acceptable warning (likely a leap year or similar informational notice).

**Merchant ID numeric check** (line 430–436):
- MIDI must be NUMERIC.
- Error: "Merchant ID must be Numeric...".

### ADD-TRANSACTION (line 442)

Key generation and record write:

1. Move HIGH-VALUES to TRAN-ID.
2. STARTBR-TRANSACT-FILE (positions at logical end of file).
3. READPREV-TRANSACT-FILE (reads the last record in KSDS key sequence).
4. ENDBR-TRANSACT-FILE.
5. Move TRAN-ID to WS-TRAN-ID-N (9(16)).
6. ADD 1 to WS-TRAN-ID-N → new transaction ID (sequential auto-increment).
7. INITIALIZE TRAN-RECORD.
8. Populate TRAN-RECORD from screen fields:
   - WS-TRAN-ID-N → TRAN-ID
   - TTYPCDI → TRAN-TYPE-CD
   - TCATCDI → TRAN-CAT-CD
   - TRNSRCI → TRAN-SOURCE
   - TDESCI → TRAN-DESC
   - NUMVAL-C(TRNAMTI) → TRAN-AMT
   - CARDNINI → TRAN-CARD-NUM
   - MIDI → TRAN-MERCHANT-ID
   - MNAMEI → TRAN-MERCHANT-NAME
   - MCITYI → TRAN-MERCHANT-CITY
   - MZIPI → TRAN-MERCHANT-ZIP
   - TORIGDTI → TRAN-ORIG-TS
   - TPROCDTI → TRAN-PROC-TS
9. PERFORM WRITE-TRANSACT-FILE.

### COPY-LAST-TRAN-DATA (line 471)

Invoked on F5 ("Copy Last Tran"):
1. PERFORM VALIDATE-INPUT-KEY-FIELDS (account/card must be valid first).
2. Move HIGH-VALUES to TRAN-ID.
3. STARTBR / READPREV / ENDBR to read the last transaction record.
4. If not in error, copies last record's field values into the screen map (TTYPCDI, TCATCDI, TRNSRCI, TRNAMTI, TDESCI, TORIGDTI, TPROCDTI, MIDI, MNAMEI, MCITYI, MZIPI).
5. Calls PROCESS-ENTER-KEY to validate the populated data.

### RETURN-TO-PREV-SCREEN (line 500)

Sets FROM-TRANID = 'CT02', FROM-PROGRAM = 'COTRN02C', PGM-CONTEXT = 0, XCTLs to CDEMO-TO-PROGRAM. Fallback: 'COSGN00C'.

### SEND-TRNADD-SCREEN (line 516)

Calls POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO, issues SEND MAP with ERASE and CURSOR.

**Critical behavior** (line 530–534): After the SEND, SEND-TRNADD-SCREEN issues its own `EXEC CICS RETURN TRANSID(CT02) COMMAREA`. This means SEND-TRNADD-SCREEN is a terminal operation — it sends the screen and ends the task. This is the primary pseudo-conversational exit point used throughout validation paragraphs.

### RECEIVE-TRNADD-SCREEN (line 539)

`EXEC CICS RECEIVE MAP INTO(COTRN2AI)` with RESP/RESP2.

### POPULATE-HEADER-INFO (line 552)

Same header population pattern as COTRN00C/COTRN01C.

### READ-CXACAIX-FILE (line 576)

`EXEC CICS READ DATASET('CXACAIX ') INTO(CARD-XREF-RECORD) RIDFLD(XREF-ACCT-ID) KEYLENGTH(LENGTH OF XREF-ACCT-ID)`.

Note: 'CXACAIX ' is the alternate index path over the CCXREF file, keyed by XREF-ACCT-ID (account ID). This allows account-ID-based lookup of card number.

- NOTFND: "Account ID NOT found...", cursor on ACTIDINL.
- OTHER: DISPLAY resp, "Unable to lookup Acct in XREF AIX file...".

### READ-CCXREF-FILE (line 609)

`EXEC CICS READ DATASET('CCXREF  ') INTO(CARD-XREF-RECORD) RIDFLD(XREF-CARD-NUM) KEYLENGTH(LENGTH OF XREF-CARD-NUM)`.

Primary KSDS access by card number.

- NOTFND: "Card Number NOT found...", cursor on CARDNINL.
- OTHER: DISPLAY resp, "Unable to lookup Card # in XREF file...".

### STARTBR-TRANSACT-FILE (line 642)

`EXEC CICS STARTBR DATASET('TRANSACT') RIDFLD(TRAN-ID) KEYLENGTH(16)`.

- NOTFND: sets ERR-FLG, "Transaction ID NOT found...", cursor on ACTIDINL, sends screen.
- OTHER: sets ERR-FLG, "Unable to lookup Transaction...".

### READPREV-TRANSACT-FILE (line 673)

`EXEC CICS READPREV DATASET('TRANSACT') INTO(TRAN-RECORD) RIDFLD(TRAN-ID)`.

- ENDFILE: MOVE ZEROS TO TRAN-ID (file is empty; new ID will be 1).
- OTHER: sets ERR-FLG, "Unable to lookup Transaction...".

### ENDBR-TRANSACT-FILE (line 702)

`EXEC CICS ENDBR DATASET('TRANSACT')` — unconditional.

### WRITE-TRANSACT-FILE (line 711)

`EXEC CICS WRITE DATASET('TRANSACT') FROM(TRAN-RECORD) RIDFLD(TRAN-ID) KEYLENGTH(16)`.

- NORMAL: success path:
  - PERFORM INITIALIZE-ALL-FIELDS (clears screen for next entry).
  - Clears WS-MESSAGE.
  - Moves DFHGREEN to ERRMSGC (success in green color).
  - STRINGs "Transaction added successfully. Your Tran ID is " + TRAN-ID + "." into WS-MESSAGE.
  - PERFORM SEND-TRNADD-SCREEN (which also issues RETURN).
- DUPKEY / DUPREC: "Tran ID already exist...", cursor on ACTIDINL.
- OTHER: DISPLAY resp, "Unable to Add Transaction...".

### CLEAR-CURRENT-SCREEN (line 754)

Calls INITIALIZE-ALL-FIELDS then SEND-TRNADD-SCREEN.

### INITIALIZE-ALL-FIELDS (line 762)

Moves SPACES to all input fields: ACTIDINI, CARDNINI, TTYPCDI, TCATCDI, TRNSRCI, TRNAMTI, TDESCI, TORIGDTI, TPROCDTI, MIDI, MNAMEI, MCITYI, MZIPI, CONFIRMI, WS-MESSAGE. Sets ACTIDINL = -1 (cursor to account ID field).

---

## 8. Inter-Program Interactions

| Interaction | Target | Mechanism | Condition |
|---|---|---|---|
| Called by | COMEN01C | XCTL (inbound) | User navigates to add transaction |
| Called by | COTRN00C/COTRN01C | XCTL (inbound, optional) | With pre-selected card context |
| Transfer to | CDEMO-FROM-PROGRAM | XCTL | F3 pressed |
| Transfer to | COMEN01C | XCTL | F3 when FROM-PROGRAM empty |
| Transfer to | COSGN00C | XCTL | EIBCALEN=0 or CDEMO-TO-PROGRAM empty |
| Calls | CSUTLDTC | CALL (static link) | Date validation |

### External CALL: CSUTLDTC
[ARTIFACT NOT AVAILABLE FOR INSPECTION: CSUTLDTC source]. Based on call interface observed at lines 393–396 and 413–416:
- Receives: date string (X(10)), format string (X(10)), result area (X(80)).
- Returns: severity code (X(04)) in CSUTLDTC-RESULT-SEV-CD ('0000' = pass) and message number in CSUTLDTC-RESULT-MSG-NUM.
- Message '2513' is tolerated as a non-fatal condition.

---

## 9. Files Accessed

| CICS Dataset Name | Access Mode | Operations | Record Structure | Key |
|---|---|---|---|---|
| TRANSACT | Browse + Write | STARTBR, READPREV, ENDBR, WRITE | TRAN-RECORD 350 bytes | TRAN-ID X(16) |
| CCXREF | Random read | READ | CARD-XREF-RECORD 50 bytes | XREF-CARD-NUM X(16) |
| CXACAIX | Random read (AIX) | READ | CARD-XREF-RECORD 50 bytes | XREF-ACCT-ID 9(11) |
| ACCTDAT | Declared (WS-ACCTDAT-FILE = 'ACCTDAT ') | None observed | ACCOUNT-RECORD 300 bytes | — |

Note: ACCTDAT is declared in WS-VARIABLES (line 40) but no CICS READ command references it in the observed procedure division. The CVACT01Y copybook is copied in but only CARD-XREF-RECORD (CVACT03Y) is used in procedure logic.

---

## 10. Validation Rules Summary (Business Rules Catalog)

| Rule | Source Location | Detail |
|---|---|---|
| Account OR card required | VALIDATE-INPUT-KEY-FIELDS, line 195 | One of ACTIDINI or CARDNINI must be entered |
| Account/card must be numeric | Lines 197–216 | NUMVAL conversion then XREF lookup |
| Type CD required and numeric | Lines 252–334 | TTYPCDI must not be blank and must be NUMERIC |
| Category CD required and numeric | Lines 258–334 | TCATCDI must not be blank and must be NUMERIC |
| Source required | Lines 264–269 | TRNSRCI must not be blank |
| Description required | Lines 270–275 | TDESCI must not be blank |
| Amount required and formatted | Lines 276–351 | +/-99999999.99 format enforced by positional check |
| Orig Date required and formatted | Lines 282–366 | YYYY-MM-DD format, further validated by CSUTLDTC |
| Proc Date required and formatted | Lines 288–381 | YYYY-MM-DD format, further validated by CSUTLDTC |
| Merchant ID required and numeric | Lines 294–436 | Must not be blank and NUMERIC |
| Merchant Name required | Lines 300–305 | Must not be blank |
| Merchant City required | Lines 306–311 | Must not be blank |
| Merchant Zip required | Lines 312–317 | Must not be blank |
| Confirmation required | PROCESS-ENTER-KEY, lines 169–188 | CONFIRMI must be 'Y' or 'y' to proceed |
| New Tran ID = last + 1 | ADD-TRANSACTION, lines 444–451 | READPREV to get max TRAN-ID, increment by 1 |
| Duplicate key detection | WRITE-TRANSACT-FILE, lines 735–741 | DUPKEY/DUPREC response handled |

---

## 11. Error Handling

| Condition | ERR-FLG | Message | Cursor |
|---|---|---|---|
| EIBCALEN = 0 | — | — | XCTL to COSGN00C |
| Account and card both blank | Y | "Account or Card Number must be entered..." | ACTIDINL |
| Account ID not numeric | Y | "Account ID must be Numeric..." | ACTIDINL |
| READ CXACAIX NOTFND | Y | "Account ID NOT found..." | ACTIDINL |
| Card number not numeric | Y | "Card Number must be Numeric..." | CARDNINL |
| READ CCXREF NOTFND | Y | "Card Number NOT found..." | CARDNINL |
| TTYPCDI blank | Y | "Type CD can NOT be empty..." | TTYPCDL |
| TCATCDI blank | Y | "Category CD can NOT be empty..." | TCATCDL |
| TRNSRCI blank | Y | "Source can NOT be empty..." | TRNSRCL |
| TDESCI blank | Y | "Description can NOT be empty..." | TDESCL |
| TRNAMTI blank or wrong format | Y | "Amount can NOT be empty..." / "Amount should be in format..." | TRNAMTL |
| TORIGDTI blank or wrong format | Y | "Orig Date can NOT be empty..." / format/validity message | TORIGDTL |
| TPROCDTI blank or wrong format | Y | "Proc Date can NOT be empty..." / format/validity message | TPROCDTL |
| MIDI blank or not numeric | Y | "Merchant ID can NOT be empty..." / "Merchant ID must be Numeric..." | MIDL |
| MNAMEI blank | Y | "Merchant Name can NOT be empty..." | MNAMEL |
| MCITYI blank | Y | "Merchant City can NOT be empty..." | MCITYL |
| MZIPI blank | Y | "Merchant Zip can NOT be empty..." | MZIPL |
| CONFIRMI not Y/N | Y | "Invalid value. Valid values are (Y/N)..." | CONFIRML |
| CONFIRMI blank | Y | "Confirm to add this transaction..." | CONFIRML |
| WRITE DUPKEY/DUPREC | Y | "Tran ID already exist..." | ACTIDINL |
| WRITE OTHER | Y | "Unable to Add Transaction..." | ACTIDINL |
| WRITE NORMAL | — | "Transaction added successfully. Your Tran ID is XXXX." | — (green) |
| Invalid AID key | Y | CCDA-MSG-INVALID-KEY | — |

---

## 12. Transaction Flow Context

```
COSGN00C (signon)
    --> COMEN01C (main menu)
        --> COTRN02C [CT02] (add transaction)    <-- this program
                VALIDATE-INPUT-KEY-FIELDS
                    READ CXACAIX (account → card) or READ CCXREF (card → account)
                VALIDATE-INPUT-DATA-FIELDS
                    CALL CSUTLDTC (date validation, x2)
                ADD-TRANSACTION (on CONFIRM='Y')
                    STARTBR/READPREV/ENDBR TRANSACT (find max key)
                    WRITE TRANSACT (new record)
            F3 --> XCTL to COMEN01C or calling program
            F4 --> Clear screen
            F5 --> Copy last transaction data and re-validate
```

---

## 13. Design Notes for Modernization

1. **Transaction ID generation strategy**: The new TRAN-ID is computed as the numeric value of the last KSDS record's key plus one. This approach is not atomic — two concurrent CT02 sessions could generate the same ID. Under CICS, there is no serialization mechanism here. DUPKEY on WRITE is the only guard, causing the second writer to fail with "Tran ID already exist...". A modern implementation should use a sequence generator or UUID.

2. **Dual EXEC CICS RETURN**: SEND-TRNADD-SCREEN contains its own RETURN (line 530). MAIN-PARA also contains a RETURN (line 156). The MAIN-PARA RETURN is only reached if SEND-TRNADD-SCREEN is never called (e.g., when RETURN-TO-PREV-SCREEN handles the exit via XCTL which does not return). In practice, all error paths call SEND-TRNADD-SCREEN which terminates the task. This is correct but architecturally unusual.

3. **WS-ACCTDAT-FILE declared, not used**: ACCTDAT and CVACT01Y are included but the procedure division contains no ACCTDAT READ commands. These may be leftovers from an earlier design where account balance validation was intended.

4. **F5 Copy Last Transaction**: This feature copies the most recent transaction's field values into the current screen, useful for batch entry of similar transactions. It uses HIGH-VALUES + READPREV to identify the last record, which works correctly in a KSDS ordered by TRAN-ID (numeric string).

5. **CSUTLDTC tolerance for message 2513**: This tolerance allows dates that would otherwise trigger a non-zero severity to pass validation if the message number is 2513. The meaning of this message number depends on the CSUTLDTC implementation. [ARTIFACT NOT AVAILABLE FOR INSPECTION].
