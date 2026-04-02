# Technical Specification: CORPT00C — Transaction Report Submission Program

## 1. Executive Summary

CORPT00C is an online CICS COBOL program in the CardDemo application that allows an authorized user to submit a transaction report batch job from the online terminal. The program presents a report selection screen (map CORPT0A / mapset CORPT00) where the user selects one of three report periods: Monthly (current month), Yearly (current year), or Custom (user-defined date range). Upon confirmation, the program constructs JCL records in-memory and writes them to the CICS extra-partition Transient Data Queue (TDQ) named 'JOBS', which feeds an internal reader to submit the batch job TRNRPT00 / procedure TRANREPT. The program runs under CICS transaction ID CR00.

Source file: `app/cbl/CORPT00C.cbl`
Version stamp: `CardDemo_v1.0-15-g27d6c6f-68 Date: 2022-07-19 23:12:33 CDT`

---

## 2. Artifact Inventory

| Artifact | Type | Location | Role |
|---|---|---|---|
| CORPT00C.cbl | CICS COBOL Program | app/cbl/ | Main report submission program |
| CORPT00.bms | BMS Mapset | app/bms/ | Screen definition for CORPT0A |
| CORPT00.CPY | BMS-generated Copybook | app/cpy-bms/ | Map data structures CORPT0AI / CORPT0AO |
| COCOM01Y.cpy | Copybook | app/cpy/ | CARDDEMO-COMMAREA |
| CVTRA05Y.cpy | Copybook | app/cpy/ | TRAN-RECORD layout (referenced but not used for file I/O in this program) |
| COTTL01Y.cpy | Copybook | app/cpy/ | Screen title literals |
| CSDAT01Y.cpy | Copybook | app/cpy/ | Date/time working storage |
| CSMSG01Y.cpy | Copybook | app/cpy/ | Common messages |
| DFHAID | System Copybook | CICS | Attention identifier constants |
| DFHBMSCA | System Copybook | CICS | BMS attribute character constants |
| CSUTLDTC | Called Subprogram | app/cbl/ | Date validation utility (CALL 'CSUTLDTC') |

---

## 3. Program Identity

| Attribute | Value | Source Reference |
|---|---|---|
| PROGRAM-ID | CORPT00C | CORPT00C.cbl line 24 |
| Transaction ID | CR00 | CORPT00C.cbl line 38 (WS-TRANID) |
| Application | CardDemo | CORPT00C.cbl line 3 |
| Type | CICS COBOL Online Program | CORPT00C.cbl line 4 |
| Map | CORPT0A | CORPT00C.cbl line 564–565 |
| Mapset | CORPT00 | CORPT00C.cbl line 565 |
| TDQ Written | JOBS | CORPT00C.cbl line 518 |

---

## 4. Data Division

### 4.1 Working-Storage Fields (WS-VARIABLES — lines 36–78)

| Field | PIC | Initial | Purpose |
|---|---|---|---|
| WS-PGMNAME | X(08) | 'CORPT00C' | Self-identifying program name |
| WS-TRANID | X(04) | 'CR00' | CICS transaction ID for RETURN |
| WS-MESSAGE | X(80) | SPACES | Error / status message text |
| WS-TRANSACT-FILE | X(08) | 'TRANSACT' | Declared but not directly accessed in this program |
| WS-ERR-FLG | X(01) | 'N' | Error flag; 88 ERR-FLG-ON = 'Y', OFF = 'N' |
| WS-TRANSACT-EOF | X(01) | 'N' | EOF flag (declared, not used) |
| WS-SEND-ERASE-FLG | X(01) | 'Y' | Controls ERASE on SEND (always 'Y' in practice) |
| WS-END-LOOP | X(01) | 'N' | Loop-exit flag used in SUBMIT-JOB-TO-INTRDR |
| WS-RESP-CD | S9(09) COMP | ZEROS | CICS RESP code |
| WS-REAS-CD | S9(09) COMP | ZEROS | CICS RESP2 code |
| WS-REC-COUNT | S9(04) COMP | ZEROS | Record count (declared, not used) |
| WS-IDX | S9(04) COMP | ZEROS | Loop index for JCL record iteration |
| WS-REPORT-NAME | X(10) | SPACES | Report type label ('Monthly', 'Yearly', 'Custom') |
| WS-START-DATE | X(10) | SPACES | Start date in YYYY-MM-DD format (composite) |
| WS-END-DATE | X(10) | SPACES | End date in YYYY-MM-DD format (composite) |
| WS-DATE-FORMAT | X(10) | 'YYYY-MM-DD' | Format string passed to CSUTLDTC |
| WS-NUM-99 | PIC 99 | 0 | Numeric conversion work field (NUMVAL-C result) |
| WS-NUM-9999 | PIC 9999 | 0 | Numeric conversion work field (NUMVAL-C result) |
| WS-TRAN-AMT | PIC +99999999.99 | — | Not used in active logic |
| WS-TRAN-DATE | X(08) | '00/00/00' | Not used in active logic |
| JCL-RECORD | X(80) | ' ' | One 80-byte JCL record written to TDQ |

### 4.2 JCL Template Data Structure (lines 81–127)

A critical embedded data structure that holds the complete JCL for batch job TRNRPT00.

**JOB-DATA-1 (literal JCL lines, each PIC X(80)):**

| Line# | Content |
|---|---|
| 1 | `//TRNRPT00 JOB 'TRAN REPORT',CLASS=A,MSGCLASS=0,` |
| 2 | `// NOTIFY=&SYSUID` |
| 3 | `//*` |
| 4 | `//JOBLIB JCLLIB ORDER=('AWS.M2.CARDDEMO.PROC')` |
| 5 | `//*` |
| 6 | `//STEP10 EXEC PROC=TRANREPT` |
| 7 | `//*` |
| 8 | `//STEP05R.SYMNAMES DD *` |
| 9 | `TRAN-CARD-NUM,263,16,ZD` |
| 10 | `TRAN-PROC-DT,305,10,CH` |
| 11 | `PARM-START-DATE,C'`[PARM-START-DATE-1 PIC X(10)]`'` |
| 12 | `PARM-END-DATE,C'`[PARM-END-DATE-1 PIC X(10)]`'` |
| 13 | `/*` |
| 14 | `//STEP10R.DATEPARM DD *` |
| 15 | [PARM-START-DATE-2 PIC X(10)] + space + [PARM-END-DATE-2 PIC X(10)] + filler |
| 16 | `/*` |
| 17 | `/*EOF` |

**JOB-DATA-2 REDEFINES JOB-DATA-1** (line 126–127): Provides array access `JOB-LINES(WS-IDX)` — OCCURS 1000 TIMES PIC X(80) — used to iterate JCL lines in SUBMIT-JOB-TO-INTRDR.

Variable parameter fields within JOB-DATA-1:
- `PARM-START-DATE-1` (PIC X(10), lines 103–107): Start date embedded in SYMNAMES DD
- `PARM-END-DATE-1` (PIC X(10), lines 109–112): End date embedded in SYMNAMES DD
- `PARM-START-DATE-2` (PIC X(10), line 118): Start date in DATEPARM DD
- `PARM-END-DATE-2` (PIC X(10), line 119): End date in DATEPARM DD

### 4.3 CSUTLDTC-PARM Structure (lines 129–137)

Interface to the CSUTLDTC date validation subprogram:

| Field | PIC | Purpose |
|---|---|---|
| CSUTLDTC-DATE | X(10) | Date string to validate (passed as LS-DATE) |
| CSUTLDTC-DATE-FORMAT | X(10) | Format mask (passed as LS-DATE-FORMAT) |
| CSUTLDTC-RESULT-SEV-CD | X(04) | Severity code ('0000' = valid date) |
| FILLER | X(11) | Internal |
| CSUTLDTC-RESULT-MSG-NUM | X(04) | CEEDAYS message number ('2513' = future date warning) |
| CSUTLDTC-RESULT-MSG | X(61) | Full result message text |

### 4.4 Linkage Section (lines 155–157)

```cobol
01  DFHCOMMAREA.
  05  LK-COMMAREA  PIC X(01) OCCURS 1 TO 32767 DEPENDING ON EIBCALEN.
```

---

## 5. CICS Commands

| Command | Paragraph | Purpose | Source Reference |
|---|---|---|---|
| EXEC CICS RETURN TRANSID COMMAREA | MAIN-PARA / RETURN-TO-CICS | Pseudo-conversational return | Lines 199–202, 587–591 |
| EXEC CICS XCTL PROGRAM COMMAREA | RETURN-TO-PREV-SCREEN | Transfer control to previous program | Lines 548–551 |
| EXEC CICS SEND MAP MAPSET FROM ERASE CURSOR | SEND-TRNRPT-SCREEN | Send CORPT0A with ERASE | Lines 563–570 |
| EXEC CICS SEND MAP MAPSET FROM CURSOR | SEND-TRNRPT-SCREEN | Send CORPT0A without ERASE | Lines 571–578 |
| EXEC CICS RECEIVE MAP MAPSET INTO RESP RESP2 | RECEIVE-TRNRPT-SCREEN | Receive user input from CORPT0A | Lines 598–604 |
| EXEC CICS WRITEQ TD QUEUE FROM LENGTH RESP RESP2 | WIRTE-JOBSUB-TDQ | Write one JCL record to TDQ 'JOBS' | Lines 517–523 |

**Note**: No CICS file I/O commands are present in CORPT00C. All data access is indirect — through the batch job submitted to the internal reader via the TDQ.

---

## 6. Paragraph-by-Paragraph Logic

### MAIN-PARA (lines 163–202)

Entry point. Executed on every CICS pseudo-conversational re-entry under transaction CR00.

1. Sets ERR-FLG-OFF, TRANSACT-NOT-EOF, SEND-ERASE-YES.
2. Clears WS-MESSAGE and ERRMSGO.
3. If EIBCALEN = 0: sets CDEMO-TO-PROGRAM = 'COSGN00C', performs RETURN-TO-PREV-SCREEN.
4. Otherwise, moves DFHCOMMAREA to CARDDEMO-COMMAREA.
5. First entry (CDEMO-PGM-ENTER):
   - Sets CDEMO-PGM-REENTER.
   - Initializes CORPT0AO to LOW-VALUES.
   - Sets cursor on MONTHLYL (-1).
   - Performs SEND-TRNRPT-SCREEN.
6. Re-entry (CDEMO-PGM-REENTER):
   - Performs RECEIVE-TRNRPT-SCREEN.
   - EIBAID DFHENTER: PROCESS-ENTER-KEY.
   - EIBAID DFHPF3: sets CDEMO-TO-PROGRAM = 'COMEN01C', performs RETURN-TO-PREV-SCREEN.
   - EIBAID OTHER: sets error flag and displays invalid key message.
7. Falls through to EXEC CICS RETURN CR00.

### PROCESS-ENTER-KEY (lines 208–456)

Main business logic for date calculation and job submission.

**Branch 1 — Monthly (lines 213–238)**

Triggered when MONTHLYI OF CORPT0AI is not SPACES/LOW-VALUES.

1. Sets WS-REPORT-NAME = 'Monthly'.
2. Gets FUNCTION CURRENT-DATE into WS-CURDATE-DATA.
3. Calculates start date: first day of current month (day = '01').
4. Calculates end date: last day of current month using intrinsic functions:
   - Adds 1 to WS-CURDATE-MONTH (with year rollover if month > 12).
   - Computes end-of-previous-month using `DATE-OF-INTEGER(INTEGER-OF-DATE(date) - 1)`.
5. Moves start date and end date to both PARM-START-DATE-1/2 and PARM-END-DATE-1/2 in JOB-DATA-1.
6. Performs SUBMIT-JOB-TO-INTRDR.

**Branch 2 — Yearly (lines 239–255)**

Triggered when YEARLYI OF CORPT0AI is not SPACES/LOW-VALUES.

1. Sets WS-REPORT-NAME = 'Yearly'.
2. Gets FUNCTION CURRENT-DATE.
3. Start date: `[current year]-01-01`.
4. End date: `[current year]-12-31`.
5. Moves dates to JOB-DATA-1 parameters.
6. Performs SUBMIT-JOB-TO-INTRDR.

**Branch 3 — Custom Date Range (lines 256–436)**

Triggered when CUSTOMI OF CORPT0AI is not SPACES/LOW-VALUES.

Validation sequence (each failure immediately sends error screen):
1. SDTMMI empty -> 'Start Date - Month can NOT be empty...'
2. SDTDDI empty -> 'Start Date - Day can NOT be empty...'
3. SDTYYYYI empty -> 'Start Date - Year can NOT be empty...'
4. EDTMMI empty -> 'End Date - Month can NOT be empty...'
5. EDTDDI empty -> 'End Date - Day can NOT be empty...'
6. EDTYYYYI empty -> 'End Date - Year can NOT be empty...'

Then numeric normalization using FUNCTION NUMVAL-C:
- Month/Day fields normalized via WS-NUM-99.
- Year fields normalized via WS-NUM-9999.

Then range validation:
- SDTMMI not numeric or > '12': 'Start Date - Not a valid Month...'
- SDTDDI not numeric or > '31': 'Start Date - Not a valid Day...'
- SDTYYYYI not numeric: 'Start Date - Not a valid Year...'
- EDTMMI not numeric or > '12': 'End Date - Not a valid Month...'
- EDTDDI not numeric or > '31': 'End Date - Not a valid Day...'
- EDTYYYYI not numeric: 'End Date - Not a valid Year...'

Then semantic date validation via CSUTLDTC:
- Assembles WS-START-DATE (YYYY-MM-DD format).
- `CALL 'CSUTLDTC' USING CSUTLDTC-DATE CSUTLDTC-DATE-FORMAT CSUTLDTC-RESULT`.
  - If result severity code not '0000' AND message number not '2513': 'Start Date - Not a valid date...' error.
  - (Message '2513' = CEEDAYS future date notice, which is accepted as valid.)
- Same sequence for WS-END-DATE.

If no errors: moves dates to JOB-DATA-1, sets WS-REPORT-NAME = 'Custom', performs SUBMIT-JOB-TO-INTRDR.

**Default Branch (lines 437–442)**: No report type selected:
'Select a report type to print report...' error, cursor on MONTHLY.

**Post-submission (lines 445–455)**: If ERR-FLG-OFF:
- INITIALIZE-ALL-FIELDS.
- Sets ERRMSGC to DFHGREEN.
- Builds success message '[ReportName] report submitted for printing ...'.
- Performs SEND-TRNRPT-SCREEN.

### SUBMIT-JOB-TO-INTRDR (lines 462–510)

Writes JCL records from JOB-DATA to TDQ 'JOBS'.

1. Checks CONFIRMI OF CORPT0AI:
   - SPACES/LOW-VALUES: prompts 'Please confirm to print the [name] report...', cursor on CONFIRML, sends screen.
   - 'Y'/'y': continues to write.
   - 'N'/'n': INITIALIZE-ALL-FIELDS, sets error flag, sends screen.
   - Other: builds error message '"X" is not a valid value to confirm...', sends screen.
2. If not error:
   - Iterates WS-IDX from 1 to 1000 (or until END-LOOP-YES or ERR-FLG-ON).
   - For each iteration: moves JOB-LINES(WS-IDX) to JCL-RECORD.
   - If JCL-RECORD = '/*EOF' or SPACES/LOW-VALUES: sets END-LOOP-YES to terminate iteration.
   - Performs WIRTE-JOBSUB-TDQ for each record.

### WIRTE-JOBSUB-TDQ (lines 515–535)

Issues EXEC CICS WRITEQ TD QUEUE('JOBS') FROM(JCL-RECORD) LENGTH(80). On non-NORMAL response: sets error flag, message 'Unable to Write TDQ (JOBS)...', cursor on MONTHLY, performs SEND-TRNRPT-SCREEN.

### RETURN-TO-PREV-SCREEN (lines 540–551)

Sets CDEMO-FROM-TRANID = 'CR00', CDEMO-FROM-PROGRAM = 'CORPT00C', CDEMO-PGM-CONTEXT = 0. Issues EXEC CICS XCTL to CDEMO-TO-PROGRAM (defaulting to 'COSGN00C' if blank).

### SEND-TRNRPT-SCREEN (lines 556–580)

Performs POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO. If SEND-ERASE-YES: sends with ERASE. Else: sends without ERASE. Then issues GO TO RETURN-TO-CICS.

**Note**: SEND-TRNRPT-SCREEN always performs `GO TO RETURN-TO-CICS` (line 580), which issues EXEC CICS RETURN. This means any PERFORM of SEND-TRNRPT-SCREEN is non-returning — execution does not resume at the calling paragraph. The calling paragraph is effectively terminated.

### RETURN-TO-CICS (lines 585–591)

Issues EXEC CICS RETURN TRANSID('CR00') COMMAREA(CARDDEMO-COMMAREA). This is the only way the program returns to CICS after sending a screen.

### RECEIVE-TRNRPT-SCREEN (lines 596–604)

Issues EXEC CICS RECEIVE MAP('CORPT0A') MAPSET('CORPT00') INTO(CORPT0AI) with RESP/RESP2.

### POPULATE-HEADER-INFO (lines 609–628)

Identical pattern to COBIL00C: populates TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO from WS-CURDATE-DATA and constants.

### INITIALIZE-ALL-FIELDS (lines 633–646)

Moves -1 to MONTHLYL; initializes MONTHLYI, YEARLYI, CUSTOMI, SDTMMI, SDTDDI, SDTYYYYI, EDTMMI, EDTDDI, EDTYYYYI, CONFIRMI, and WS-MESSAGE to their default values.

---

## 7. Program Flow Diagram

```
Entry (Transaction CR00)
        |
        v
EIBCALEN = 0? --YES--> RETURN-TO-PREV-SCREEN (XCTL to COSGN00C)
        |
        NO
        |
        v
CDEMO-PGM-ENTER? --YES--> Init screen, SEND-TRNRPT-SCREEN -> RETURN-TO-CICS
        |
        NO
        |
        v
RECEIVE-TRNRPT-SCREEN
        |
        v
EIBAID?
  PF3 -> RETURN-TO-PREV-SCREEN (XCTL to COMEN01C)
  |
  ENTER -> PROCESS-ENTER-KEY:
    |
    MONTHLY set? -> Calculate current month dates
    |                -> SUBMIT-JOB-TO-INTRDR
    |
    YEARLY set?  -> Calculate current year dates (Jan-1 to Dec-31)
    |                -> SUBMIT-JOB-TO-INTRDR
    |
    CUSTOM set?  -> Validate all date fields (empty check)
    |               -> Numeric validation (NUMVAL-C)
    |               -> Range validation (>12, >31)
    |               -> Semantic validation (CALL CSUTLDTC x2)
    |               -> SUBMIT-JOB-TO-INTRDR (if no errors)
    |
    None set?    -> Error: 'Select a report type...'
    |
    SUBMIT-JOB-TO-INTRDR:
      |
      CONFIRM blank? -> Prompt, SEND-TRNRPT-SCREEN -> RETURN-TO-CICS
      CONFIRM = N/n -> Clear, SEND-TRNRPT-SCREEN -> RETURN-TO-CICS
      CONFIRM = Y/y -> Loop through JOB-LINES(1..1000):
                         WIRTE-JOBSUB-TDQ (WRITEQ TD 'JOBS')
                         Stop at '/*EOF' or blank line
    |
    Success: INIT fields, green message, SEND-TRNRPT-SCREEN -> RETURN-TO-CICS
  |
  Other -> Error message, SEND-TRNRPT-SCREEN -> RETURN-TO-CICS
```

---

## 8. Inter-Program Interactions

| Direction | Mechanism | Target | Condition | Source Reference |
|---|---|---|---|---|
| Called by | XCTL | CORPT00C | User selects report option from COMEN01C | Inferred from commarea flow |
| Calls | XCTL | COSGN00C | EIBCALEN = 0 | Lines 173–174 |
| Calls | XCTL | COMEN01C | PF3 | Lines 188–189 |
| Calls | CALL (static) | CSUTLDTC | Custom date validation | Lines 392–394, 412–414 |
| Writes | WRITEQ TD | TDQ 'JOBS' (internal reader) | On confirmed submission | Lines 517–523 |

The CALL to CSUTLDTC is a static COBOL CALL (not CICS LINK). CSUTLDTC must be link-edited with CORPT00C or available as a load module in the DFHRPL.

---

## 9. Batch Job Submitted (JCL Template Analysis)

The embedded JCL (CORPT00C.cbl lines 83–125) submits the following batch job:

```jcl
//TRNRPT00 JOB 'TRAN REPORT',CLASS=A,MSGCLASS=0,
// NOTIFY=&SYSUID
//*
//JOBLIB JCLLIB ORDER=('AWS.M2.CARDDEMO.PROC')
//*
//STEP10 EXEC PROC=TRANREPT
//*
//STEP05R.SYMNAMES DD *
TRAN-CARD-NUM,263,16,ZD
TRAN-PROC-DT,305,10,CH
PARM-START-DATE,C'[start-date]'
PARM-END-DATE,C'[end-date]'
/*
//STEP10R.DATEPARM DD *
[start-date] [end-date]
/*
/*EOF
```

Key observations:
- Job name: TRNRPT00, CLASS=A, MSGCLASS=0.
- Procedure library: `AWS.M2.CARDDEMO.PROC`.
- Procedure: `TRANREPT` (cataloged in that library).
- Start/end dates injected into two DD statements: SYMNAMES (for SORT utility symbol names) and DATEPARM.
- The SYMNAMES DD defines TRAN-CARD-NUM at offset 263, length 16 (ZD) and TRAN-PROC-DT at offset 305, length 10 (CH) — these are field positions within the TRANSACT VSAM record used by a SORT step inside TRANREPT.
- The `/*EOF` record acts as the loop-exit sentinel in SUBMIT-JOB-TO-INTRDR.

---

## 10. Error Handling

All errors set WS-ERR-FLG = 'Y' and perform SEND-TRNRPT-SCREEN (which issues GO TO RETURN-TO-CICS, terminating the current task iteration). No CICS ABEND is issued.

| Condition | Message | Cursor | Source Reference |
|---|---|---|---|
| No report type selected | 'Select a report type to print report...' | MONTHLYL | Lines 438–442 |
| CONFIRM blank | 'Please confirm to print the [name] report...' | CONFIRML | Lines 465–473 |
| CONFIRM invalid | '"X" is not a valid value to confirm...' | CONFIRML | Lines 485–493 |
| CONFIRM = N/n | (no message; screen cleared) | MONTHLYL | Lines 480–483 |
| Start month empty | 'Start Date - Month can NOT be empty...' | SDTMML | Lines 260–265 |
| Start day empty | 'Start Date - Day can NOT be empty...' | SDTDDL | Lines 266–271 |
| Start year empty | 'Start Date - Year can NOT be empty...' | SDTYYYYL | Lines 272–279 |
| End month empty | 'End Date - Month can NOT be empty...' | EDTMML | Lines 280–285 |
| End day empty | 'End Date - Day can NOT be empty...' | EDTDDL | Lines 286–291 |
| End year empty | 'End Date - Year can NOT be empty...' | EDTYYYYL | Lines 292–299 |
| Start month not numeric or > 12 | 'Start Date - Not a valid Month...' | SDTMML | Lines 329–335 |
| Start day not numeric or > 31 | 'Start Date - Not a valid Day...' | SDTDDL | Lines 338–345 |
| Start year not numeric | 'Start Date - Not a valid Year...' | SDTYYYYL | Lines 347–353 |
| End month not numeric or > 12 | 'End Date - Not a valid Month...' | EDTMML | Lines 355–361 |
| End day not numeric or > 31 | 'End Date - Not a valid Day...' | EDTDDL | Lines 364–370 |
| End year not numeric | 'End Date - Not a valid Year...' | EDTYYYYL | Lines 372–378 |
| Start date invalid (CSUTLDTC) | 'Start Date - Not a valid date...' | SDTMML | Lines 398–405 |
| End date invalid (CSUTLDTC) | 'End Date - Not a valid date...' | EDTMML | Lines 418–425 |
| TDQ write failure | 'Unable to Write TDQ (JOBS)...' | MONTHLYL | Lines 530–534 |
| Invalid AID key | 'Invalid key pressed. Please see below...' | MONTHLYL | Lines 191–194 |

---

## 11. Business Rules

| Rule | Condition | Outcome | Source Reference |
|---|---|---|---|
| Monthly report spans current month | MONTHLY selected | Start = YYYY-MM-01, End = last day of month | Lines 217–237 |
| Yearly report spans current calendar year | YEARLY selected | Start = YYYY-01-01, End = YYYY-12-31 | Lines 243–254 |
| Custom date requires all 6 fields | CUSTOM selected | All empty-field checks fire before any validation | Lines 258–303 |
| Day validation is coarse | Day > '31' | Does not validate day-in-month semantics (e.g., Feb 30 accepted) | Lines 338–345 |
| Future dates accepted with warning | CSUTLDTC msg '2513' | Future dates not blocked (line 399: `NOT = '2513'`) | Lines 396–406 |
| Two-phase confirmation required | On any report type | First Enter without CONFIRM causes prompt | Lines 464–473 |
| JCL written record-by-record | Confirmed submission | Loop 1–1000, each line individually written to TDQ | Lines 498–508 |
| Batch job class fixed as A | Always | CLASS=A hardcoded in JOB-DATA-1 | Line 84 |

---

## 12. Transaction Flow

1. User authenticated via COSGN00C.
2. User navigates to COMEN01C menu and selects the report option.
3. COMEN01C XCTLs to CORPT00C; transaction CR00 begins.
4. Pseudo-conversational: each key press triggers a new CR00 invocation.
5. First ENTER: user selects report type and optionally enters custom dates.
6. Second ENTER (if CONFIRM was blank on first): user enters Y or N in CONFIRM field.
7. On Y: JCL written to TDQ 'JOBS' → internal reader picks up → TRNRPT00 job submitted.
8. On PF3: XCTL back to COMEN01C.

---

## 13. Open Questions and Gaps

1. **GO TO RETURN-TO-CICS side effect**: SEND-TRNRPT-SCREEN always ends with GO TO RETURN-TO-CICS (line 580), which calls EXEC CICS RETURN. This means every PERFORM SEND-TRNRPT-SCREEN never returns to the calling paragraph. The program relies on this to terminate each response path. This is an unusual construct that complicates any dead-code analysis.
2. **WS-SEND-ERASE-FLG**: Declared and initialized to 'Y' (SEND-ERASE-YES), but no code in the program ever sets it to 'N'. The non-ERASE branch in SEND-TRNRPT-SCREEN (lines 571–578) is therefore dead code as written.
3. **PROC library dependency**: The JCL references `AWS.M2.CARDDEMO.PROC` and procedure `TRANREPT`. Neither is available in the analyzed codebase. [ARTIFACT NOT AVAILABLE FOR INSPECTION: TRANREPT proc / AWS.M2.CARDDEMO.PROC dataset].
4. **TDQ 'JOBS' definition**: The extra-partition TDQ named 'JOBS' must be defined in the CICS CSD (resource definition). Its definition, DCB attributes, and the associated internal reader JES configuration are not available in the analyzed source.
5. **Date arithmetic for monthly end date**: The computation at lines 229–230 (`DATE-OF-INTEGER(INTEGER-OF-DATE(date) - 1)`) is a standard COBOL technique for finding the last day of the previous month after incrementing the month. This correctly handles month-end variations (28, 29, 30, 31 days) but relies on the COBOL runtime's correct implementation of DATE-OF-INTEGER and INTEGER-OF-DATE.
6. **CVTRA05Y copied but unused**: COPY CVTRA05Y is included (line 146) but CORPT00C performs no direct TRANSACT file I/O. This may be a leftover inclusion from copy-paste template reuse.
