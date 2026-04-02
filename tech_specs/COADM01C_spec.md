# Technical Specification: COADM01C — Admin Menu Program

**Source File:** `app/cbl/COADM01C.cbl`
**Application:** CardDemo
**Type:** CICS Online COBOL Program
**Transaction ID:** CA00
**Version Tag:** CardDemo_v1.0-15-g27d6c6f-68 (2022-07-19)

---

## 1. Executive Summary

COADM01C is the administrative menu program for the CardDemo CICS application. It is invoked via XCTL from COSGN00C after successful authentication of an admin-type user (SEC-USR-TYPE = 'A'). The program presents an admin-only menu screen (BMS mapset COADM01, map COADM1A) whose options are sourced from the COADM02Y copybook data table. Upon receiving a valid selection, it transfers control (XCTL) to the corresponding administrative program, passing CARDDEMO-COMMAREA. Unlike COMEN01C, COADM01C uses a CICS HANDLE CONDITION to intercept PGMIDERR (program not found) errors that would arise if a target program is not installed in CICS.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `app/cbl/COADM01C.cbl` | CICS COBOL Program | Main source |
| `app/bms/COADM01.bms` | BMS Mapset | Screen definition |
| `app/cpy-bms/COADM01.CPY` | BMS-generated Copybook | Map symbolic descriptions (COADM1AI / COADM1AO) |
| `app/cpy/COCOM01Y.cpy` | Copybook | CARDDEMO-COMMAREA definition |
| `app/cpy/COADM02Y.cpy` | Copybook | Admin menu options data table (CDEMO-ADMIN-OPT-*) |
| `app/cpy/COTTL01Y.cpy` | Copybook | Screen title literals |
| `app/cpy/CSDAT01Y.cpy` | Copybook | Date/time working storage |
| `app/cpy/CSMSG01Y.cpy` | Copybook | Common message literals |
| `app/cpy/CSUSR01Y.cpy` | Copybook | SEC-USER-DATA (declared but not used for I/O) |
| `DFHAID` | System Copybook | AID key constants |
| `DFHBMSCA` | System Copybook | BMS attribute byte constants (DFHGREEN) |

---

## 3. Program Identity and Entry

| Item | Value | Source Reference |
|---|---|---|
| PROGRAM-ID | COADM01C | `COADM01C.cbl` line 23 |
| Transaction ID | CA00 | `WS-TRANID` line 37 |
| Map | COADM1A | SEND-MENU-SCREEN paragraph, line 183 |
| Mapset | COADM01 | SEND-MENU-SCREEN paragraph, line 184 |
| Invoked by | COSGN00C via XCTL | When SEC-USR-TYPE = 'A' |

---

## 4. WORKING-STORAGE Data Structures

### 4.1 WS-VARIABLES (inline, lines 35-48)

| Field | PIC | Initial Value | Purpose |
|---|---|---|---|
| WS-PGMNAME | X(08) | 'COADM01C' | Program name for screen header |
| WS-TRANID | X(04) | 'CA00' | Transaction ID for CICS RETURN |
| WS-MESSAGE | X(80) | SPACES | Error/info message buffer |
| WS-USRSEC-FILE | X(08) | 'USRSEC  ' | Declared but not used for I/O |
| WS-ERR-FLG | X(01) | 'N' | Error flag (88 ERR-FLG-ON='Y', ERR-FLG-OFF='N') |
| WS-RESP-CD | S9(09) COMP | ZEROS | CICS RESP return code |
| WS-REAS-CD | S9(09) COMP | ZEROS | CICS RESP2 return code |
| WS-OPTION-X | X(02) JUST RIGHT | — | Right-justified staging area for option input |
| WS-OPTION | 9(02) | 0 | Numeric menu selection |
| WS-IDX | S9(04) COMP | ZEROS | Loop counter for BUILD-MENU-OPTIONS |
| WS-ADMIN-OPT-TXT | X(40) | SPACES | Formatted admin option text line |

### 4.2 CARDDEMO-COMMAREA (COPY COCOM01Y)

Same structure as described in COSGN00C_spec.md. COADM01C uses:
- CDEMO-PGM-CONTEXT to detect first vs. re-entry
- CDEMO-FROM-TRANID and CDEMO-FROM-PROGRAM to stamp routing info before XCTL
- CDEMO-PGM-CONTEXT reset to ZEROS before XCTL

### 4.3 Admin Menu Options Table (COPY COADM02Y — app/cpy/COADM02Y.cpy)

**Active option count:** CDEMO-ADMIN-OPT-COUNT = 6 (line 002200 of copybook). A commented-out value of 4 shows an earlier version had only 4 options; options 5 and 6 were added for a DB2 release.

**Redefined Array Structure:**
```
05 CDEMO-ADMIN-OPTIONS REDEFINES CDEMO-ADMIN-OPTIONS-DATA.
   10 CDEMO-ADMIN-OPT OCCURS 9 TIMES.
      15 CDEMO-ADMIN-OPT-NUM      PIC 9(02).
      15 CDEMO-ADMIN-OPT-NAME     PIC X(35).
      15 CDEMO-ADMIN-OPT-PGMNAME  PIC X(08).
```

Note: Unlike COMEN02Y, COADM02Y does NOT include a CDEMO-ADMIN-OPT-USRTYPE field per entry. All options in this menu are implicitly admin-only (the screen is only reachable by admin users).

**Admin Menu Options (from COADM02Y):**

| Opt# | Option Name | Target Program | Notes |
|---|---|---|---|
| 01 | User List (Security) | COUSR00C | |
| 02 | User Add (Security) | COUSR01C | |
| 03 | User Update (Security) | COUSR02C | |
| 04 | User Delete (Security) | COUSR03C | |
| 05 | Transaction Type List/Update (Db2) | COTRTLIC | Added in DB2 release |
| 06 | Transaction Type Maintenance (Db2) | COTRTUPC | Added in DB2 release |

OCCURS 9 TIMES in the REDEFINES; slots 7-9 are empty/unused.

**Critical discrepancy:** CDEMO-ADMIN-OPT-COUNT = 6 (line 002200), but the REDEFINES declares OCCURS 9 TIMES (line 005200). The loop in BUILD-MENU-OPTIONS runs to CDEMO-ADMIN-OPT-COUNT (6), so only 6 options are ever displayed. The OCCURS 9 TIMES allows future expansion without structural changes.

### 4.4 Map Symbolic Descriptions (COPY COADM01 — resolves to app/cpy-bms/COADM01.CPY)

**COADM1AI** (input):

| Field | PIC | Purpose |
|---|---|---|
| OPTIONL | COMP S9(4) | Length of received OPTION field |
| OPTIONI | X(2) | User's menu selection |

**COADM1AO** (output — REDEFINES COADM1AI):

| Field | PIC | Purpose |
|---|---|---|
| TRNNAMEO | X(4) | Transaction ID in header |
| TITLE01O | X(40) | Title line 1 |
| CURDATEO | X(8) | Current date MM/DD/YY |
| PGMNAMEO | X(8) | Program name in header |
| TITLE02O | X(40) | Title line 2 |
| CURTIMEO | X(8) | Current time HH:MM:SS |
| OPTN001O–OPTN012O | X(40) each | Menu option text lines (12 slots) |
| OPTIONO | X(2) | Echo of selected option |
| ERRMSGO | X(78) | Error message display area |
| ERRMSGC | X(1) | Error message colour attribute |

---

## 5. LINKAGE SECTION

```
01 DFHCOMMAREA.
   05 LK-COMMAREA PIC X(01) OCCURS 1 TO 32767 TIMES DEPENDING ON EIBCALEN.
```
Source: lines 67-69.

On re-entry (EIBCALEN > 0):
```
MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
```
(line 90).

---

## 6. CICS Commands Inventory

| Command | Paragraph | Purpose | Source Lines |
|---|---|---|---|
| `EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA)` | MAIN-PARA | Establishes error handler for program-not-found on any subsequent XCTL | Lines 77-79 |
| `EXEC CICS RETURN TRANSID('CA00') COMMAREA(CARDDEMO-COMMAREA)` | MAIN-PARA | Pseudo-conversational RETURN; also issued in PGMIDERR-ERR-PARA | Lines 111-114, 280-283 |
| `EXEC CICS XCTL PROGRAM(CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)) COMMAREA(CARDDEMO-COMMAREA)` | PROCESS-ENTER-KEY | Transfer control to selected admin program | Lines 145-148 |
| `EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM)` | RETURN-TO-SIGNON-SCREEN | Transfer control to COSGN00C (or override) on PF3 | Lines 168-170 |
| `EXEC CICS RECEIVE MAP('COADM1A') MAPSET('COADM01') INTO(COADM1AI) RESP(...) RESP2(...)` | RECEIVE-MENU-SCREEN | Receives terminal input | Lines 194-200 |
| `EXEC CICS SEND MAP('COADM1A') MAPSET('COADM01') FROM(COADM1AO) ERASE` | SEND-MENU-SCREEN | Sends admin menu screen | Lines 182-187 |

---

## 7. Program Flow — Paragraph-by-Paragraph Analysis

### 7.1 MAIN-PARA (lines 74-114) — Entry Point

**Step 0 — HANDLE CONDITION (lines 77-79):**
```
EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA)
```
This establishes a condition handler that routes to paragraph PGMIDERR-ERR-PARA if any subsequent CICS command raises a PGMIDERR condition. Specifically, this protects the XCTL in PROCESS-ENTER-KEY: if the target admin program is not installed, CICS will jump to PGMIDERR-ERR-PARA rather than abending the task.

**Step 1 — Initialize:**
- `SET ERR-FLG-OFF TO TRUE`
- Clear WS-MESSAGE and ERRMSGO

**Step 2 — COMMAREA check:**

- **EIBCALEN = 0**: `MOVE 'COSGN00C' TO CDEMO-FROM-PROGRAM`, PERFORM RETURN-TO-SIGNON-SCREEN (safety redirect).

- **EIBCALEN > 0**: `MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA`.

  - **NOT CDEMO-PGM-REENTER**: Set CDEMO-PGM-REENTER to TRUE, MOVE LOW-VALUES to COADM1AO, PERFORM SEND-MENU-SCREEN.

  - **CDEMO-PGM-REENTER**: PERFORM RECEIVE-MENU-SCREEN, then EVALUATE EIBAID:
    - `DFHENTER`: PERFORM PROCESS-ENTER-KEY
    - `DFHPF3`: `MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM`, PERFORM RETURN-TO-SIGNON-SCREEN
    - `OTHER`: ERR-FLG-ON, CCDA-MSG-INVALID-KEY, PERFORM SEND-MENU-SCREEN

**Step 3 — RETURN (lines 111-114):**
```
EXEC CICS RETURN TRANSID('CA00') COMMAREA(CARDDEMO-COMMAREA)
```

---

### 7.2 PROCESS-ENTER-KEY (lines 119-158)

**Step 1 — Parse option (lines 121-129):**
Identical algorithm to COMEN01C: scan OPTIONI backwards for last non-space character, right-justify into WS-OPTION-X, replace spaces with '0', move to numeric WS-OPTION.

**Step 2 — Range validation (lines 131-138):**
```
IF WS-OPTION IS NOT NUMERIC OR
   WS-OPTION > CDEMO-ADMIN-OPT-COUNT OR
   WS-OPTION = ZEROS
```
Note: CDEMO-ADMIN-OPT-COUNT = 6. Valid options are 01-06.

**Step 3 — Program dispatch (lines 140-157):**
```
IF NOT ERR-FLG-ON
    IF CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)(1:5) NOT = 'DUMMY'
        MOVE WS-TRANID    TO CDEMO-FROM-TRANID
        MOVE WS-PGMNAME   TO CDEMO-FROM-PROGRAM
        MOVE ZEROS        TO CDEMO-PGM-CONTEXT
        EXEC CICS XCTL PROGRAM(CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)) COMMAREA(CARDDEMO-COMMAREA)
    END-IF
    -- Falls through to here if DUMMY option or after XCTL (unreachable unless PGMIDERR fires)
    MOVE SPACES TO WS-MESSAGE
    MOVE DFHGREEN TO ERRMSGC OF COADM1AO
    STRING 'This option ' ... 'is not installed ...' INTO WS-MESSAGE
    PERFORM SEND-MENU-SCREEN
END-IF
```

**Key difference from COMEN01C:** COADM01C does NOT use `EXEC CICS INQUIRE` to pre-check installation. Instead, it relies on the `EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA)` established in MAIN-PARA. If the XCTL target program is not installed, CICS will raise PGMIDERR and jump to PGMIDERR-ERR-PARA before the XCTL completes. If it IS installed, the XCTL proceeds and the code after the XCTL statement (the "not installed" message) is never reached.

**Note on DUMMY check:** The code checks `CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)(1:5) NOT = 'DUMMY'`. None of the 6 defined admin options have a program name starting with 'DUMMY', so this check is effectively always TRUE for valid options. The commented-out lines 153-154 suggest the intent was to show the option name in the message but it was commented out, leaving a generic 'is not installed ...' message.

---

### 7.3 RETURN-TO-SIGNON-SCREEN (lines 163-170)

Identical structure to COMEN01C:
```
IF CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES
    MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM
END-IF
EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM)
```
No COMMAREA passed — COSGN00C will receive EIBCALEN=0 and display fresh sign-on.

---

### 7.4 SEND-MENU-SCREEN (lines 175-187)

1. PERFORM POPULATE-HEADER-INFO
2. PERFORM BUILD-MENU-OPTIONS
3. MOVE WS-MESSAGE TO ERRMSGO OF COADM1AO
4. `EXEC CICS SEND MAP('COADM1A') MAPSET('COADM01') FROM(COADM1AO) ERASE`

---

### 7.5 RECEIVE-MENU-SCREEN (lines 192-200)

```
EXEC CICS RECEIVE MAP('COADM1A') MAPSET('COADM01') INTO(COADM1AI) RESP(...) RESP2(...)
```

---

### 7.6 POPULATE-HEADER-INFO (lines 205-224)

Same pattern as COMEN01C: populates COADM1AO header fields with current date, time, titles, transaction ID, and program name. Does NOT call ASSIGN APPLID or ASSIGN SYSID.

---

### 7.7 BUILD-MENU-OPTIONS (lines 229-266)

```
PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > CDEMO-ADMIN-OPT-COUNT
    STRING CDEMO-ADMIN-OPT-NUM(WS-IDX) DELIMITED BY SIZE
           '. '                         DELIMITED BY SIZE
           CDEMO-ADMIN-OPT-NAME(WS-IDX) DELIMITED BY SIZE
      INTO WS-ADMIN-OPT-TXT
    EVALUATE WS-IDX
        WHEN 1 MOVE WS-ADMIN-OPT-TXT TO OPTN001O
        ...
        WHEN 10 MOVE WS-ADMIN-OPT-TXT TO OPTN010O
        WHEN OTHER CONTINUE
    END-EVALUATE
END-PERFORM
```

Loops from 1 to CDEMO-ADMIN-OPT-COUNT (6), placing formatted option text into OPTN001O through OPTN006O. OPTN007O–OPTN012O remain blank (LOW-VALUES from initialization).

---

### 7.8 PGMIDERR-ERR-PARA (lines 270-284)

This paragraph is the CICS HANDLE CONDITION target for PGMIDERR errors.

```
MOVE SPACES TO WS-MESSAGE
MOVE DFHGREEN TO ERRMSGC OF COADM1AO
STRING 'This option ' ... 'is not installed ...' INTO WS-MESSAGE
PERFORM SEND-MENU-SCREEN
EXEC CICS RETURN TRANSID('CA00') COMMAREA(CARDDEMO-COMMAREA)
```

The paragraph:
1. Builds a green "not installed" message (same text as the inline message after XCTL in PROCESS-ENTER-KEY).
2. Sends the admin menu screen with the error message.
3. Issues its own `EXEC CICS RETURN TRANSID('CA00')` to perpetuate the pseudo-conversational loop.

**Note:** The commented-out lines 153-154 and 274-275 (both in PROCESS-ENTER-KEY and PGMIDERR-ERR-PARA) suggest the original intent was to include the option name in the error message: `STRING 'This option ' CDEMO-ADMIN-OPT-NAME(WS-OPTION) DELIMITED BY SIZE...` but CDEMO-ADMIN-OPT-NAME reference was commented out, producing only a generic "This option is not installed ..." message.

---

## 8. Inter-Program Interactions

| Direction | Target Program | Mechanism | Condition | COMMAREA |
|---|---|---|---|---|
| Inbound from | COSGN00C | XCTL | Successful login, user type 'A' | CARDDEMO-COMMAREA with USER-TYPE='A', PGM-CONTEXT=0 |
| Inbound from | Any admin sub-program | XCTL (PF3 back) | Admin presses PF3 in sub-program | CARDDEMO-COMMAREA updated by sub-program |
| Outbound | COUSR00C | XCTL | Option 01 | CARDDEMO-COMMAREA with FROM=CA00/COADM01C, CONTEXT=0 |
| Outbound | COUSR01C | XCTL | Option 02 | Same pattern |
| Outbound | COUSR02C | XCTL | Option 03 | Same pattern |
| Outbound | COUSR03C | XCTL | Option 04 | Same pattern |
| Outbound | COTRTLIC | XCTL | Option 05 | Same pattern |
| Outbound | COTRTUPC | XCTL | Option 06 | Same pattern |
| Outbound | COSGN00C | XCTL (no COMMAREA) | PF3 pressed | None |
| Self | COADM01C (via CA00) | RETURN TRANSID | After every screen send | CARDDEMO-COMMAREA |

---

## 9. Error Handling

| Error Condition | Detection | Response | Message |
|---|---|---|---|
| No COMMAREA on entry | EIBCALEN = 0 | XCTL to COSGN00C | None (silent redirect) |
| Invalid option (non-numeric, zero, or > 6) | WS-OPTION validation | Re-display menu | 'Please enter a valid option number...' |
| Target program not installed | CICS PGMIDERR condition | Jump to PGMIDERR-ERR-PARA; display green message + RETURN | 'This option is not installed ...' (green) |
| DUMMY option selected | PGMNAME(1:5) = 'DUMMY' (logic in PROCESS-ENTER-KEY) | Falls through to "not installed" message + SEND | 'This option is not installed ...' (green) |
| Invalid AID key | EVALUATE EIBAID WHEN OTHER | Re-display menu | CCDA-MSG-INVALID-KEY |

**HANDLE CONDITION scope:** The `EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA)` established at line 77 remains in effect for the entire task lifetime (CICS handle conditions are task-scoped, not paragraph-scoped). This means if any subsequent CICS command in the task raises PGMIDERR, control will jump to PGMIDERR-ERR-PARA.

---

## 10. Transaction Flow Participation

```
COSGN00C (XCTL, type='A')
    |
COADM01C (first entry: PGM-CONTEXT=0)
    |
    HANDLE CONDITION PGMIDERR -> PGMIDERR-ERR-PARA
    |
    SEND COADM1A (admin menu with 6 options)
    RETURN TRANSID(CA00)
    |
    [Admin selects option N, presses Enter]
    |
    RECEIVE COADM1A
    Parse + validate option (1-6)
    |
    [Valid option, not DUMMY] --> XCTL to CDEMO-ADMIN-OPT-PGMNAME(N)
                                  [If not installed: PGMIDERR -> PGMIDERR-ERR-PARA
                                   -> SEND "not installed" msg, RETURN TRANSID(CA00)]
    [Invalid option]          --> SEND error screen, RETURN TRANSID(CA00)
    [PF3]                     --> XCTL COSGN00C (no COMMAREA, fresh sign-on)
```

---

## 11. Business Rules Catalog

| Rule ID | Rule Description | Source Location |
|---|---|---|
| BR-ADM-001 | Admin menu is only reachable after authentication as user type 'A' in COSGN00C | COSGN00C.cbl line 230-234 (routing decision) |
| BR-ADM-002 | A task arriving without a COMMAREA is silently redirected to sign-on | MAIN-PARA, lines 86-88 |
| BR-ADM-003 | CDEMO-PGM-REENTER is set to TRUE (1) on first entry to prevent menu re-send loop | MAIN-PARA, line 92 |
| BR-ADM-004 | Admin options 01-04 are user management functions; 05-06 are DB2 transaction type management | COADM02Y copybook data |
| BR-ADM-005 | Valid option range is 01 to CDEMO-ADMIN-OPT-COUNT (currently 6) | PROCESS-ENTER-KEY, lines 131-138 |
| BR-ADM-006 | Missing/uninstalled programs are handled via CICS HANDLE CONDITION PGMIDERR (not INQUIRE) | MAIN-PARA lines 77-79; PGMIDERR-ERR-PARA lines 270-284 |
| BR-ADM-007 | CDEMO-PGM-CONTEXT is reset to ZEROS before every XCTL to a sub-program | PROCESS-ENTER-KEY, line 144 |
| BR-ADM-008 | PF3 returns to sign-on screen WITHOUT a COMMAREA, forcing fresh authentication | RETURN-TO-SIGNON-SCREEN, line 168 |
| BR-ADM-009 | Error messages for "not installed" programs are displayed in GREEN (DFHGREEN) | PROCESS-ENTER-KEY line 151; PGMIDERR-ERR-PARA line 272 |

---

## 12. Comparison with COMEN01C (Key Differences)

| Aspect | COMEN01C | COADM01C |
|---|---|---|
| Transaction ID | CM00 | CA00 |
| User type | Regular ('U') | Admin ('A') |
| Menu options count | 11 | 6 |
| Missing program detection | EXEC CICS INQUIRE before XCTL | EXEC CICS HANDLE CONDITION PGMIDERR |
| Access control check | CDEMO-MENU-OPT-USRTYPE field checked | Not applicable (all admin-only) |
| User type field in options table | Yes (CDEMO-MENU-OPT-USRTYPE) | No |
| Error message colour for "not installed" | RED (DFHRED) | GREEN (DFHGREEN) |
| COPAUS0C special case | Yes (explicit INQUIRE + WHEN branch) | Not applicable |

---

## 13. Open Questions and Gaps

1. **PGMIDERR-ERR-PARA does not know which option was selected**: WS-OPTION is set in PROCESS-ENTER-KEY before XCTL, but the PGMIDERR-ERR-PARA paragraph has the option name reference commented out (lines 274-275). As a result, the error message always says "This option is not installed" without naming the option. Confidence: HIGH.
2. **Duplicate error path**: After the `IF NOT = 'DUMMY'` block in PROCESS-ENTER-KEY (lines 140-157), if the XCTL succeeds, control never returns. If the XCTL triggers PGMIDERR, control jumps to PGMIDERR-ERR-PARA. The code at lines 150-157 (the inline "not installed" message path) would only execute if a DUMMY-named program were selected, which is currently unreachable given the option table contents. This represents dead code for the current dataset. Confidence: HIGH.
3. **WS-USRSEC-FILE declared but not used**: Same pattern as COMEN01C — appears to be a copy-paste artefact. Confidence: HIGH.
4. **RECEIVE MAP RESP not tested**: RESP and RESP2 from RECEIVE-MENU-SCREEN are not evaluated. MAPFAIL would go unhandled. Confidence: HIGH.
5. **COADM02Y version mismatch**: The copybook version tag is `CardDemo_v2.0-16-gbdcb6ea-226 (2024-01-21)` — substantially newer than the COADM01C program version tag `CardDemo_v1.0-15-g27d6c6f-68 (2022-07-19)`. This means the program and its menu options copybook were updated on different release cycles. The program logic was not updated to handle the DB2 options differently from other options. Confidence: HIGH.
