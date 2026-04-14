# Technical Specification: COMEN01C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COMEN01C                                             |
| Source File      | app/cbl/COMEN01C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CM00 (WS-TRANID, line 37)                            |
| Function         | Main menu for CardDemo regular (non-admin) users. Displays up to 12 numbered menu options from COMEN02Y copybook. Validates option selection; performs CICS INQUIRE PROGRAM NOHANDLE to detect uninstalled programs at runtime. Admin-only options (CDEMO-MENU-OPT-USRTYPE='A') blocked for regular users. PF3 sends thank-you message and returns cleanly without re-entering the transaction. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CM00 and COMMAREA)

EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA)

SET ERR-FLG-OFF
Clear WS-MESSAGE and screen error message field

IF EIBCALEN = 0:
    MOVE 'COSGN00C' TO CDEMO-FROM-PROGRAM
    PERFORM RETURN-TO-PREV-SCREEN (XCTL to COSGN00C)

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO COMEN1AO
        PERFORM SEND-MENU-SCREEN
    ELSE:
        PERFORM RECEIVE-MENU-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER: PERFORM PROCESS-ENTER-KEY
            WHEN DFHPF3:   PERFORM RETURN-TO-PREV-SCREEN
            WHEN OTHER:    Set ERR-FLG-ON; CCDA-MSG-INVALID-KEY; SEND-MENU-SCREEN

EXEC CICS RETURN TRANSID('CM00') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| MAIN-PARA              | 75–117    | Main entry: HANDLE CONDITION PGMIDERR; EIBCALEN check; first/reenter dispatch; CICS RETURN |
| PROCESS-ENTER-KEY      | 122–197   | Strip trailing spaces from OPTIONI; convert to numeric; validate range; check admin-only; CICS INQUIRE PROGRAM (COPAUS0C special case); XCTL or display error |
| RETURN-TO-PREV-SCREEN  | 202–213   | Default CDEMO-TO-PROGRAM='COSGN00C'; PF3 sends CCDA-MSG-THANK-YOU via SEND-MENU-SCREEN then executes bare CICS RETURN (no TRANSID — ends session) |
| SEND-MENU-SCREEN       | 218–233   | POPULATE-HEADER-INFO; BUILD-MENU-OPTIONS; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('COMEN1A') MAPSET('COMEN01') FROM(COMEN1AO) ERASE |
| RECEIVE-MENU-SCREEN    | 238–246   | CICS RECEIVE MAP('COMEN1A') MAPSET('COMEN01') INTO(COMEN1AI) RESP RESP2 |
| POPULATE-HEADER-INFO   | 251–270   | Fill TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO |
| BUILD-MENU-OPTIONS     | 275–316   | PERFORM VARYING WS-IDX 1 to CDEMO-MENU-OPT-COUNT: STRING option number + name; skip options with USRTYPE='A' if not admin; MOVE to OPTN001O–OPTN012O |
| PGMIDERR-ERR-PARA      | 320–337   | HANDLE CONDITION target: display 'not installed' in DFHGREEN; PERFORM SEND-MENU-SCREEN; EXEC CICS RETURN TRANSID COMMAREA |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 50) | CARDDEMO-COMMAREA: CDEMO-GENERAL-INFO, CDEMO-CUSTOMER-INFO, etc.; CDEMO-MENU-OPT-COUNT, CDEMO-MENU-OPT-PGMNAME, CDEMO-MENU-OPT-NAME, CDEMO-MENU-OPT-NUM, CDEMO-MENU-OPT-USRTYPE |
| COMEN02Y  | WORKING-STORAGE (line 51) | CARDDEMO-MAIN-MENU-OPTIONS: option table with regular user menu entries (ACCTVIEW, TRANVIEW, TRANLIST, TRANREPT, PAYMTUPD entries pointing to programs like COACTVWC, COTRN00C, COTRN01C, CORPT00C, COBIL00C, COPAUS0C) |
| COMEN01  | WORKING-STORAGE (line 53)  | BMS mapset copybook: COMEN1AI (input map), COMEN1AO (output map); contains OPTIONI, OPTIONO, ERRMSGO, OPTN001O–OPTN012O, TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO, ERRMSGC |
| COTTL01Y  | WORKING-STORAGE (line 55) | Screen title constants CCDA-TITLE01, CCDA-TITLE02 |
| CSDAT01Y  | WORKING-STORAGE (line 56) | Current date/time working storage fields |
| CSMSG01Y  | WORKING-STORAGE (line 57) | Common messages: CCDA-MSG-INVALID-KEY, CCDA-MSG-THANK-YOU |
| CSUSR01Y  | WORKING-STORAGE (line 58) | Signed-on user data |
| DFHAID    | WORKING-STORAGE (line 60) | EIBAID constants: DFHENTER, DFHPF3 |
| DFHBMSCA  | WORKING-STORAGE (line 61) | BMS attribute byte constants: DFHGREEN |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| WS-PGMNAME           | X(08) = 'COMEN01C' | Program name for screen header |
| WS-TRANID            | X(04) = 'CM00' | Transaction ID for CICS RETURN |
| WS-MESSAGE           | X(80)     | User-visible message displayed in ERRMSGO |
| WS-ERR-FLG           | X(01)     | 'Y'=error; 'N'=ok; 88 ERR-FLG-ON/ERR-FLG-OFF |
| WS-RESP-CD / WS-REAS-CD | S9(09) COMP | CICS response/reason codes |
| WS-OPTION-X          | X(02) JUST RIGHT | Raw option input, right-justified |
| WS-OPTION            | 9(02)     | Numeric option value after conversion |
| WS-IDX               | S9(04) COMP | Loop index for BUILD-MENU-OPTIONS |
| WS-MENU-OPT-TXT      | X(40)     | Formatted "N. Option Name" string |
| WS-PGM-NAME          | X(08)     | Program name retrieved from CDEMO-MENU-OPT-PGMNAME; used in CICS INQUIRE |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA) | MAIN-PARA | Intercepts XCTL to uninstalled program |
| EXEC CICS RETURN TRANSID('CM00') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA | Pseudo-conversational return |
| EXEC CICS INQUIRE PROGRAM(WS-PGM-NAME) NOHANDLE | PROCESS-ENTER-KEY | Checks if COPAUS0C is installed before XCTL |
| EXEC CICS XCTL PROGRAM(CDEMO-MENU-OPT-PGMNAME) COMMAREA | PROCESS-ENTER-KEY | Transfer to selected menu function |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) | RETURN-TO-PREV-SCREEN | Return to COSGN00C |
| EXEC CICS SEND MAP('COMEN1A') MAPSET('COMEN01') FROM(COMEN1AO) ERASE | SEND-MENU-SCREEN | Display main menu |
| EXEC CICS RECEIVE MAP('COMEN1A') MAPSET('COMEN01') INTO(COMEN1AI) RESP RESP2 | RECEIVE-MENU-SCREEN | Receive option selection |
| EXEC CICS RETURN (bare, no TRANSID) | RETURN-TO-PREV-SCREEN (PF3 path) | Ends the CICS task cleanly (no re-entry) |
| EXEC CICS RETURN TRANSID COMMAREA | PGMIDERR-ERR-PARA | Return after PGMIDERR condition |

---

## 5. File/Dataset Access

None. COMEN01C does not directly access any VSAM or CICS files. All data access is delegated to sub-programs via XCTL.

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COMEN01    | COMEN1A | CM00        |

**Key Screen Fields:**

| Field      | Direction | Description |
|------------|-----------|-------------|
| OPTIONI    | Input     | Option number typed by user (1–N) |
| OPTIONO    | Output    | Echoes selected option |
| OPTN001O–OPTN012O | Output | Formatted menu option text ("N. Option Name"); up to 12 options |
| ERRMSGO    | Output    | WS-MESSAGE: error or status message |
| ERRMSGC    | Output    | Color attribute (DFHGREEN for 'not installed' messages) |
| TITLE01O   | Output    | Application title line 1 |
| TITLE02O   | Output    | Application title line 2 |
| TRNNAMEO   | Output    | Current transaction ID (CM00) |
| PGMNAMEO   | Output    | Program name (COMEN01C) |
| CURDATEO   | Output    | Current date MM/DD/YY |
| CURTIMEO   | Output    | Current time HH:MM:SS |

**Navigation:**
- ENTER: validate and transfer to selected option
- PF3: display CCDA-MSG-THANK-YOU, send screen, then bare CICS RETURN (session ends)
- Other keys: display CCDA-MSG-INVALID-KEY, re-send map

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| CDEMO-MENU-OPT-PGMNAME(WS-OPTION) | CICS XCTL | ENTER with valid, non-admin, non-DUMMY option |
| COSGN00C   | CICS XCTL   | EIBCALEN=0 or PF3 (before bare RETURN) |

**Regular user menu options (from COMEN02Y — representative; exact names from copybook):**

| Option | Program   | Function |
|--------|-----------|----------|
| 1      | COACTVWC  | Account view |
| 2      | COTRN00C  | Transaction list |
| 3      | COTRN01C  | Transaction view |
| 4      | COTRN02C  | Transaction add |
| 5      | CORPT00C  | Statement/report request |
| 6      | COBIL00C  | Bill payment [UNRESOLVED — COBIL00C not found in app/cbl/] |
| 7      | COPAUS0C  | Pause/placeholder (CICS INQUIRE check applied) |

**Note on COPAUS0C special handling**: In PROCESS-ENTER-KEY, if the selected option resolves to program name 'COPAUS0C', a CICS INQUIRE PROGRAM NOHANDLE is performed. If EIBRESP is not DFHRESP(NORMAL), the program is not installed and a 'coming soon' message is displayed. This check is applied only to COPAUS0C; all other programs rely on PGMIDERR handler.

**Note on DUMMY prefix**: If CDEMO-MENU-OPT-PGMNAME(WS-OPTION) starts with 'DUMMY', no XCTL is attempted; a 'coming soon' or 'not installed' message is shown.

**Note on admin-option guard**: If CDEMO-MENU-OPT-USRTYPE(WS-OPTION) = 'A', the option is blocked for non-admin users with an error message. Admin users accessing COMEN01C would not normally see admin-only options (those users go to COADM01C).

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C (must arrive via signon) |
| Option non-numeric or out of range (0 or >CDEMO-MENU-OPT-COUNT) | ERR-FLG-ON; error message; re-send map |
| Option USRTYPE = 'A' (admin-only) | Error: 'This option is not available...'; re-send map |
| Option PGMNAME starts with 'DUMMY' | Display 'coming soon' message; re-send map |
| COPAUS0C INQUIRE fails (EIBRESP != NORMAL) | Display 'not installed' in DFHGREEN; re-send map |
| CICS PGMIDERR (any other uninstalled program) | PGMIDERR-ERR-PARA: 'not installed' in DFHGREEN; CICS RETURN |
| Invalid AID key (not ENTER or PF3) | ERR-FLG-ON; CCDA-MSG-INVALID-KEY; re-send map |

---

## 9. Business Rules

1. **Regular user entry point**: COMEN01C is reached from COSGN00C when authenticated user is not admin (CDEMO-USRTYP-ADMIN is false).
2. **Option count**: CDEMO-MENU-OPT-COUNT (from COMEN02Y via COCOM01Y) drives both BUILD-MENU-OPTIONS loop and validation upper bound. Supports up to 12 options (OPTN001O–OPTN012O on the BMS map).
3. **Admin option suppression**: Options with CDEMO-MENU-OPT-USRTYPE(idx)='A' are skipped during BUILD-MENU-OPTIONS (not displayed to regular users) and blocked in PROCESS-ENTER-KEY (error if somehow submitted).
4. **COPAUS0C runtime check**: CICS INQUIRE PROGRAM NOHANDLE provides a runtime installed-check specifically for COPAUS0C before attempting XCTL. This is distinct from the PGMIDERR handler and DUMMY prefix checks.
5. **First entry / reenter pattern**: CDEMO-PGM-REENTER distinguishes first display (send without receive) from subsequent interactions (receive then evaluate).
6. **PF3 clean exit**: PF3 path sends thank-you message, then issues bare EXEC CICS RETURN (no TRANSID), which terminates the task. The session does not re-enter CM00; the user must log in again.
7. **No direct file access**: COMEN01C contains no VSAM or DB2 I/O. All business logic is in sub-programs.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COMEN1A) | OPTIONI — user's option selection (1–12) |
| COMMAREA  | CARDDEMO-COMMAREA (CDEMO-MENU-OPT-COUNT, CDEMO-MENU-OPT-PGMNAME, CDEMO-MENU-OPT-USRTYPE, signed-on user info) |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COMEN1A) | Main menu with up to 12 formatted option lines; error/status messages |
| COMMAREA   | CDEMO-FROM-PROGRAM='COMEN01C', CDEMO-FROM-TRANID='CM00', CDEMO-PGM-CONTEXT=0 (passed to sub-program via XCTL) |

---

## 11. Key Variables and Their Purpose

| Variable           | Purpose |
|--------------------|---------|
| WS-OPTION          | Numeric option selected; used as index into CDEMO-MENU-OPT-PGMNAME and CDEMO-MENU-OPT-USRTYPE |
| WS-OPTION-X        | Raw X(2) input; INSPECT replaces spaces with '0' before conversion |
| WS-MENU-OPT-TXT    | "N. OptionName" string built for each displayed option |
| WS-PGM-NAME        | Program name copied from CDEMO-MENU-OPT-PGMNAME for CICS INQUIRE (COPAUS0C check) |
| WS-ERR-FLG         | Error state flag; prevents double processing |
| CDEMO-MENU-OPT-USRTYPE(WS-OPTION) | 'A'=admin-only; blocks regular users from admin options |
