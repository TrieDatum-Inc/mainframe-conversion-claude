# Technical Specification: CORPT00C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | CORPT00C                                             |
| Source File      | app/cbl/CORPT00C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CR00 (WS-TRANID, line 37)                            |
| Function         | Transaction report request screen. Allows users to enter a date range (start date, end date) and a confirmation flag, then submits a JCL job to the CICS internal reader (TDQ QUEUE='JOBS') to produce a batch transaction report. End date defaults to the last day of the prior month if left blank. CONFIRMI must be 'Y' or 'y' before submission. Date input fields are optional; blank start date submits with no lower bound. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CR00 and COMMAREA)

Clear WS-MESSAGE; SET ERR-FLG-OFF

IF EIBCALEN = 0:
    MOVE 'COSGN00C' TO CDEMO-FROM-PROGRAM
    PERFORM RETURN-TO-PREV-SCREEN (XCTL to COSGN00C)

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO CORPT0AO
        PERFORM SEND-REPTRQST-SCREEN
    ELSE:
        PERFORM RECEIVE-REPTRQST-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER: PERFORM PROCESS-ENTER-KEY
            WHEN DFHPF3:   PERFORM RETURN-TO-PREV-SCREEN
            WHEN OTHER:    Set ERR-FLG-ON; CCDA-MSG-INVALID-KEY; SEND-REPTRQST-SCREEN

EXEC CICS RETURN TRANSID('CR00') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph               | Lines     | Description |
|-------------------------|-----------|-------------|
| MAIN-PARA               | 78–121    | Main entry: EIBCALEN check; first/reenter dispatch; AID evaluate; CICS RETURN |
| PROCESS-ENTER-KEY       | 126–213   | Validate CONFIRMI ('Y'/'y' required); determine end date (default to last day of prior month if blank); validate start/end date format; PERFORM WIRTE-JOBSUB-TDQ; display confirmation message; INITIALIZE-ALL-FIELDS |
| RETURN-TO-PREV-SCREEN   | 218–228   | Default CDEMO-TO-PROGRAM=CDEMO-FROM-PROGRAM; EXEC CICS XCTL |
| SEND-REPTRQST-SCREEN    | 233–247   | POPULATE-HEADER-INFO; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('CORPT0A') MAPSET('CORPT00') FROM(CORPT0AO) ERASE |
| RECEIVE-REPTRQST-SCREEN | 252–261   | CICS RECEIVE MAP('CORPT0A') MAPSET('CORPT00') INTO(CORPT0AI) RESP RESP2 |
| POPULATE-HEADER-INFO    | 266–283   | Fill TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO |
| WIRTE-JOBSUB-TDQ        | 288–430   | Build JCL in JOB-DATA OCCURS array; EXEC CICS WRITEQ TD QUEUE('JOBS') for each JCL line; submits batch TRANREPT job |
| INITIALIZE-ALL-FIELDS   | 435–460   | Resets CONFIRMI, SDTMMI, SDTDDI, SDTYYY1I, EDTMMI, EDTDDI, EDTYYYY1I screen fields to LOW-VALUES after successful submission |
| CALCULATE-END-DATE      | 465–530   | If end date blank: compute last day of prior month using FUNCTION DATE-OF-INTEGER(FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1) |

**Note on misspelling**: The paragraph name is `WIRTE-JOBSUB-TDQ` (not WRITE-JOBSUB-TDQ). This misspelling is in the source and must be referenced exactly.

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 51) | CARDDEMO-COMMAREA: CDEMO-GENERAL-INFO, CDEMO-FROM-PROGRAM, CDEMO-TO-PROGRAM, CDEMO-PGM-REENTER, etc. |
| CORPT00  | WORKING-STORAGE (line 53)  | BMS mapset copybook: CORPT0AI (input map), CORPT0AO (output map); contains CONFIRMI/O, SDTMMI, SDTDDI, SDTYYY1I (start date month/day/year), EDTMMI, EDTDDI, EDTYYYY1I (end date month/day/year), ERRMSGO, TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO |
| COTTL01Y  | WORKING-STORAGE (line 55) | Screen title constants |
| CSDAT01Y  | WORKING-STORAGE (line 56) | Current date/time: WS-CURDATE-N (numeric YYYYMMDD), WS-CURDATE-* |
| CSMSG01Y  | WORKING-STORAGE (line 57) | Common messages: CCDA-MSG-INVALID-KEY |
| CSUSR01Y  | WORKING-STORAGE (line 58) | Signed-on user data |
| DFHAID    | WORKING-STORAGE (line 60) | EIBAID constants |
| DFHBMSCA  | WORKING-STORAGE (line 61) | BMS attribute byte constants |

### Key Working Storage Variables

| Variable             | PIC         | Purpose |
|----------------------|-------------|---------|
| WS-PGMNAME           | X(08) = 'CORPT00C' | Program name for screen header |
| WS-TRANID            | X(04) = 'CR00' | Transaction ID for CICS RETURN |
| WS-MESSAGE           | X(80)       | User-visible message |
| WS-ERR-FLG           | X(01)       | 'Y'=error flag |
| WS-CURDATE-N         | 9(08)       | Current date as YYYYMMDD numeric; used in end-date calculation |
| WS-START-DATE        | X(08)       | Assembled start date YYYYMMDD from SDTYYY1I+SDTMMI+SDTDDI |
| WS-END-DATE          | X(08)       | Assembled end date YYYYMMDD from EDTYYYY1I+EDTMMI+EDTDDI; or computed |
| JOB-DATA             | Group: OCCURS 1000 | JCL lines array; JOB-DATA-2 REDEFINES JOB-DATA-1 (2-level array for building JCL cards) |
| JOB-DATA-LINE        | X(80)       | Individual JCL line within JOB-DATA |
| PARM-START-DATE-1    | X(08)       | Start date embedded in JCL SYSIN SYMNAMES section |
| PARM-END-DATE-1      | X(08)       | End date embedded in JCL SYSIN SYMNAMES section |
| PARM-START-DATE-2    | X(08)       | Start date embedded in JCL DATEPARM DD statement |
| PARM-END-DATE-2      | X(08)       | End date embedded in JCL DATEPARM DD statement |

### JCL Content (hardcoded in WIRTE-JOBSUB-TDQ)

The JCL submits a job with:
- **PROC**: TRANREPT (in JCLLIB 'AWS.M2.CARDDEMO.PROC')
- **JOB name**: TRANREPT
- **MSGCLASS**: X
- **Date parameters**: Passed via SYSIN SYMNAMES and a DATEPARM DD containing start/end date values

The JCLLIB reference `AWS.M2.CARDDEMO.PROC` is an environment-specific dataset name hardcoded in the JCL.

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS RETURN TRANSID('CR00') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | RETURN-TO-PREV-SCREEN | Return to calling program |
| EXEC CICS SEND MAP('CORPT0A') MAPSET('CORPT00') FROM(CORPT0AO) ERASE | SEND-REPTRQST-SCREEN | Display report request screen |
| EXEC CICS RECEIVE MAP('CORPT0A') MAPSET('CORPT00') INTO(CORPT0AI) RESP RESP2 | RECEIVE-REPTRQST-SCREEN | Receive date range and confirmation input |
| EXEC CICS WRITEQ TD QUEUE('JOBS') FROM(JOB-DATA-LINE) LENGTH(80) | WIRTE-JOBSUB-TDQ | Write each JCL line to internal reader TDQ |

---

## 5. File/Dataset Access

None directly. CORPT00C writes JCL to TDQ 'JOBS' (CICS internal reader) which causes z/OS JES to initiate the TRANREPT batch job. No VSAM file I/O occurs in this program.

**TDQ 'JOBS'**: CICS transient data queue connected to the JES internal reader. Each WRITEQ TD writes one 80-byte JCL card. The batch job runs asynchronously after submission.

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| CORPT00    | CORPT0A | CR00        |

**Key Screen Fields:**

| Field       | Direction | Description |
|-------------|-----------|-------------|
| CONFIRMI    | Input     | Confirmation flag — must be 'Y' or 'y' to submit |
| SDTMMI      | Input     | Start date month (MM) |
| SDTDDI      | Input     | Start date day (DD) |
| SDTYYY1I    | Input     | Start date year (YYYY) |
| EDTMMI      | Input     | End date month (MM) |
| EDTDDI      | Input     | End date day (DD) |
| EDTYYYY1I   | Input     | End date year (YYYY) |
| ERRMSGO     | Output    | WS-MESSAGE: error or status message |
| TITLE01O    | Output    | Application title line 1 |
| TITLE02O    | Output    | Application title line 2 |
| TRNNAMEO    | Output    | Transaction ID (CR00) |
| PGMNAMEO    | Output    | Program name (CORPT00C) |
| CURDATEO    | Output    | Current date |
| CURTIMEO    | Output    | Current time |

**Navigation:**
- ENTER: validate inputs and submit JCL job
- PF3: return to previous program (CDEMO-FROM-PROGRAM)
- Other keys: CCDA-MSG-INVALID-KEY, re-send map

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| CDEMO-FROM-PROGRAM (typically COMEN01C) | CICS XCTL | PF3 pressed or EIBCALEN=0 |

No sub-programs are called. The batch TRANREPT job is submitted via TDQ 'JOBS' (asynchronous — CORPT00C does not wait for completion).

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C (must arrive via menu) |
| CONFIRMI not 'Y' or 'y' | ERR-FLG-ON; 'Please confirm your request...'; re-send map |
| Start date entered but invalid format | ERR-FLG-ON; error message; re-send map |
| End date entered but invalid format | ERR-FLG-ON; error message; re-send map |
| Both dates blank | End date defaults to last day of prior month; start date = no lower bound; job submitted |
| End date blank, start date provided | End date computed from prior month calculation |
| CICS WRITEQ TD failure | [UNRESOLVED] — no explicit RESP checking found on WRITEQ TD; failure would cause abend or silent error |
| Invalid AID key | ERR-FLG-ON; CCDA-MSG-INVALID-KEY; re-send map |

**Note on DISPLAY statements**: CORPT00C contains DISPLAY statements in WIRTE-JOBSUB-TDQ for debug purposes (showing JCL lines written). These produce sysprint output in a CICS environment if CEEMSG or similar is routed.

---

## 9. Business Rules

1. **Confirmation required**: The user must type 'Y' or 'y' in CONFIRMI before submission. This prevents accidental job submission.
2. **Default end date**: If end date is left blank, CORPT00C computes the last day of the prior calendar month using: `FUNCTION DATE-OF-INTEGER(FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1)`. This gives "yesterday from the first of the current month" which is the last day of the prior month.
3. **Asynchronous batch**: CORPT00C submits JCL to the internal reader and returns. The batch TRANREPT job runs independently. There is no feedback mechanism to the online user about job status or completion.
4. **JCLLIB hardcoded**: The JCL references `AWS.M2.CARDDEMO.PROC` as the JCLLIB. This is environment-specific and must be overridden in non-AWS environments.
5. **Field reset after submission**: INITIALIZE-ALL-FIELDS clears all date and confirmation fields on the screen after a successful submission, allowing the user to request another report.
6. **Date format**: Dates are entered as separate month/day/year fields and assembled into YYYYMMDD format for the JCL parameters (PARM-START-DATE-1, PARM-START-DATE-2, etc.).
7. **No date range validation**: CORPT00C does not verify that start date precedes end date. The batch TRANREPT job is responsible for handling invalid ranges.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (CORPT0A) | CONFIRMI (Y/y), SDTMMI, SDTDDI, SDTYYY1I (start date), EDTMMI, EDTDDI, EDTYYYY1I (end date) |
| COMMAREA  | CARDDEMO-COMMAREA (CDEMO-FROM-PROGRAM for PF3 return routing) |
| CSDAT01Y  | WS-CURDATE-N: current date for default end-date calculation |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (CORPT0A) | Report request screen with confirmation and date fields; error/status messages |
| TDQ JOBS   | 80-byte JCL card records for TRANREPT batch job (written via EXEC CICS WRITEQ TD) |

---

## 11. Key Variables and Their Purpose

| Variable           | Purpose |
|--------------------|---------|
| CONFIRMI           | User confirmation ('Y'/'y' required); gating condition for job submission |
| WS-START-DATE      | Assembled start date YYYYMMDD; substituted into JCL PARM-START-DATE-1 and PARM-START-DATE-2 |
| WS-END-DATE        | Assembled or computed end date YYYYMMDD; substituted into JCL parameters |
| JOB-DATA / JOB-DATA-LINE | JCL card storage; each line written individually to TDQ JOBS |
| PARM-START-DATE-1/2 | Date parameter slots in the hardcoded JCL; receive WS-START-DATE value before submission |
| PARM-END-DATE-1/2  | Date parameter slots in the hardcoded JCL; receive WS-END-DATE value before submission |
| WS-CURDATE-N       | Current date YYYYMMDD; used as reference for end-date default calculation |
