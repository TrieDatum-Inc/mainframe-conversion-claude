# Technical Specification: COADM01C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COADM01C                                             |
| Source File      | app/cbl/COADM01C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CA00 (WS-TRANID, line 37)                            |
| Function         | Admin menu for CardDemo administrator users. Displays up to 10 numbered menu options (from COADM02Y copybook). Validates option selection; uses CICS HANDLE CONDITION PGMIDERR to catch uninstalled programs. PF3 returns to signon screen (COSGN00C). |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CA00 and COMMAREA)

EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA)

SET ERR-FLG-OFF
Clear WS-MESSAGE and screen error message field

IF EIBCALEN = 0:
    MOVE 'COSGN00C' TO CDEMO-FROM-PROGRAM
    PERFORM RETURN-TO-SIGNON-SCREEN (XCTL to COSGN00C)

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO COADM1AO
        PERFORM SEND-MENU-SCREEN
    ELSE:
        PERFORM RECEIVE-MENU-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER: PERFORM PROCESS-ENTER-KEY
            WHEN DFHPF3:   MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM
                           PERFORM RETURN-TO-SIGNON-SCREEN
            WHEN OTHER:    Set ERR-FLG-ON; CCDA-MSG-INVALID-KEY; SEND-MENU-SCREEN

EXEC CICS RETURN TRANSID('CA00') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| MAIN-PARA              | 75–114    | Main entry: HANDLE CONDITION PGMIDERR; EIBCALEN check; first/reenter dispatch; CICS RETURN |
| PROCESS-ENTER-KEY      | 119–158   | Strip trailing spaces from OPTIONI; convert to numeric; validate 1-N range; XCTL to selected program (if not 'DUMMY'); or display "not installed" message |
| RETURN-TO-SIGNON-SCREEN | 163–170  | Default CDEMO-TO-PROGRAM='COSGN00C'; EXEC CICS XCTL to CDEMO-TO-PROGRAM |
| SEND-MENU-SCREEN       | 175–187   | POPULATE-HEADER-INFO; BUILD-MENU-OPTIONS; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('COADM1A') MAPSET('COADM01') FROM(COADM1AO) ERASE |
| RECEIVE-MENU-SCREEN    | 192–200   | CICS RECEIVE MAP('COADM1A') MAPSET('COADM01') INTO(COADM1AI) RESP RESP2 |
| POPULATE-HEADER-INFO   | 205–224   | Fill TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO from literals and FUNCTION CURRENT-DATE |
| BUILD-MENU-OPTIONS     | 229–266   | PERFORM VARYING WS-IDX 1 to CDEMO-ADMIN-OPT-COUNT: STRING option number + name into WS-ADMIN-OPT-TXT; MOVE to OPTN001O through OPTN010O |
| PGMIDERR-ERR-PARA      | 270–284   | HANDLE CONDITION target: display 'This option is not installed...' in green; PERFORM SEND-MENU-SCREEN; EXEC CICS RETURN TRANSID COMMAREA |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 50) | CARDDEMO-COMMAREA: CDEMO-GENERAL-INFO, CDEMO-CUSTOMER-INFO, etc.; CDEMO-ADMIN-OPT-COUNT, CDEMO-ADMIN-OPT-PGMNAME, CDEMO-ADMIN-OPT-NAME, CDEMO-ADMIN-OPT-NUM |
| COADM02Y  | WORKING-STORAGE (line 51) | CARDDEMO-ADMIN-MENU-OPTIONS: option table with up to 6 entries (COUSR00C, COUSR01C, COUSR02C, COUSR03C, COTRTLIC, COTRTUPC) |
| COADM01   | WORKING-STORAGE (line 53) | BMS mapset copybook: COADM1AI (input map), COADM1AO (output map); contains OPTIONI, OPTIONO, ERRMSGO, OPTN001O–OPTN010O, TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO |
| COTTL01Y  | WORKING-STORAGE (line 55) | Screen title constants CCDA-TITLE01, CCDA-TITLE02 |
| CSDAT01Y  | WORKING-STORAGE (line 56) | Current date/time: WS-CURDATE-DATA, WS-CURDATE-MONTH, WS-CURDATE-DAY, WS-CURDATE-YEAR, WS-CURDATE-MM-DD-YY, WS-CURTIME-* |
| CSMSG01Y  | WORKING-STORAGE (line 57) | Common messages: CCDA-MSG-INVALID-KEY |
| CSUSR01Y  | WORKING-STORAGE (line 58) | Signed-on user data |
| DFHAID    | WORKING-STORAGE (line 60) | EIBAID key constants: DFHENTER, DFHPF3 |
| DFHBMSCA  | WORKING-STORAGE (line 61) | BMS attribute byte constants (e.g., DFHGREEN) |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| WS-PGMNAME           | X(08) = 'COADM01C' | Program name placed in screen header |
| WS-TRANID            | X(04) = 'CA00' | Transaction ID for CICS RETURN |
| WS-MESSAGE           | X(80)     | User-visible message moved to ERRMSGO |
| WS-USRSEC-FILE       | X(08) = 'USRSEC  ' | File name literal (present but not used in COADM01C — USRSEC is used in signon, not here) |
| WS-ERR-FLG           | X(01)     | 'Y'=error; 'N'=ok; 88 ERR-FLG-ON/ERR-FLG-OFF |
| WS-RESP-CD / WS-REAS-CD | S9(09) COMP | CICS response codes |
| WS-OPTION-X          | X(02) JUST RIGHT | Raw option input from screen, right-justified |
| WS-OPTION            | 9(02)     | Numeric option value after conversion |
| WS-IDX               | S9(04) COMP | Loop index for BUILD-MENU-OPTIONS |
| WS-ADMIN-OPT-TXT     | X(40)     | Formatted "N. Option Name" string for each menu item |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA) | MAIN-PARA (line 77) | Intercepts attempt to XCTL to uninstalled program |
| EXEC CICS RETURN TRANSID('CA00') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA (line 111) | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM(CDEMO-ADMIN-OPT-PGMNAME) COMMAREA | PROCESS-ENTER-KEY (line 145) | Transfer to selected admin function |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) | RETURN-TO-SIGNON-SCREEN (line 168) | Return to COSGN00C |
| EXEC CICS SEND MAP('COADM1A') MAPSET('COADM01') FROM(COADM1AO) ERASE | SEND-MENU-SCREEN (line 182) | Display admin menu |
| EXEC CICS RECEIVE MAP('COADM1A') MAPSET('COADM01') INTO(COADM1AI) RESP RESP2 | RECEIVE-MENU-SCREEN (line 194) | Receive option selection |
| EXEC CICS RETURN TRANSID('CA00') COMMAREA | PGMIDERR-ERR-PARA (line 280) | Return after PGMIDERR |

---

## 5. File/Dataset Access

None. COADM01C does not directly access any VSAM or CICS files. It only navigates to sub-programs that perform file access.

WS-USRSEC-FILE = 'USRSEC' is defined in working storage but not referenced in the PROCEDURE DIVISION.

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COADM01    | COADM1A | CA00        |

**Key Screen Fields:**

| Field      | Direction | Description |
|------------|-----------|-------------|
| OPTIONI    | Input     | Option number typed by user (1–N) |
| OPTIONO    | Output    | Echoes selected option number |
| OPTN001O–OPTN010O | Output | Formatted menu option text ("N. Option Name") |
| ERRMSGO    | Output    | WS-MESSAGE: error or status message |
| TITLE01O   | Output    | Application title line 1 (CCDA-TITLE01) |
| TITLE02O   | Output    | Application title line 2 (CCDA-TITLE02) |
| TRNNAMEO   | Output    | Current transaction ID (CA00) |
| PGMNAMEO   | Output    | Program name (COADM01C) |
| CURDATEO   | Output    | Current date MM/DD/YY |
| CURTIMEO   | Output    | Current time HH:MM:SS |
| ERRMSGC    | Output    | Color attribute of error message (DFHGREEN when option not installed) |

**Navigation:**
- ENTER: validate and transfer to selected option
- PF3: XCTL to COSGN00C (signon screen)
- Other keys: display CCDA-MSG-INVALID-KEY

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION) | CICS XCTL | ENTER with valid option; option name not 'DUMMY...' |
| COSGN00C   | CICS XCTL   | PF3 pressed or EIBCALEN=0 |

**Admin menu options (from COADM02Y):**

| Option | Program  | Function |
|--------|----------|----------|
| 1      | COUSR00C | User list |
| 2      | COUSR01C | User add |
| 3      | COUSR02C | User update |
| 4      | COUSR03C | User delete |
| 5      | COTRTLIC | Transaction list (admin) |
| 6      | COTRTUPC | Transaction update (admin) |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C (must arrive via signon) |
| Option non-numeric or out of range (0 or >CDEMO-ADMIN-OPT-COUNT) | ERR-FLG-ON; 'Please enter a valid option number...'; re-send map |
| Option program name starts with 'DUMMY' | Display "This option is not installed..." in green; re-send map |
| CICS PGMIDERR (program not installed) | PGMIDERR-ERR-PARA: display "not installed" in green; CICS RETURN |
| Invalid AID key (not ENTER or PF3) | ERR-FLG-ON; CCDA-MSG-INVALID-KEY; re-send map |

---

## 9. Business Rules

1. **Admin-only screen**: COADM01C is the entry point for admin users. It is reached via XCTL from COSGN00C when the authenticated user type is Admin (CDEMO-USRTYP-ADMIN).
2. **Option range validation**: WS-OPTION must be numeric, non-zero, and not exceed CDEMO-ADMIN-OPT-COUNT (from COADM02Y). The count comes from the copybook and matches the number of defined admin options.
3. **DUMMY program guard**: If CDEMO-ADMIN-OPT-PGMNAME(option) starts with 'DUMMY', the program is not installed and an informational message is displayed without attempting XCTL.
4. **PGMIDERR handler**: EXEC CICS HANDLE CONDITION PGMIDERR intercepts XCTL to programs not installed in the CICS region. This duplicates the DUMMY check but handles programs that are listed (non-DUMMY) but actually not installed.
5. **First entry sends screen**: CDEMO-PGM-REENTER is set to TRUE on first entry (when CDEMO-PGM-REENTER was FALSE); screen is sent without receiving. On subsequent entries (CDEMO-PGM-REENTER already TRUE), screen is received then processed.
6. **No direct file access**: All business processing is delegated to the selected sub-program via XCTL.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COADM1A) | OPTIONI — user's option selection |
| COMMAREA  | CARDDEMO-COMMAREA (CDEMO-ADMIN-OPT-COUNT, CDEMO-ADMIN-OPT-PGMNAME, etc.) |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COADM1A) | Admin menu with 1–10 formatted option lines; error/status messages |
| COMMAREA   | CDEMO-FROM-PROGRAM='COADM01C', CDEMO-FROM-TRANID='CA00', CDEMO-PGM-CONTEXT=0 (passed to selected program) |

---

## 11. Key Variables and Their Purpose

| Variable           | Purpose |
|--------------------|---------|
| WS-OPTION          | Numeric value of user's selection; used as index into CDEMO-ADMIN-OPT-PGMNAME table |
| WS-OPTION-X        | Raw X(2) input; INSPECT replaces spaces with '0' before numeric conversion |
| WS-ADMIN-OPT-TXT   | "N. OptionName" string built for each menu option position |
| CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION) | Resolved program name for XCTL (from COADM02Y via COCOM01Y) |
| WS-ERR-FLG         | Error state; prevents double processing when error has already been handled |
