# Technical Specification: COMEN01C — Main Menu Program (Regular Users)

**Source File:** `app/cbl/COMEN01C.cbl`
**Application:** CardDemo
**Type:** CICS Online COBOL Program
**Transaction ID:** CM00
**Version Tag:** CardDemo_v1.0-15-g27d6c6f-68 (2022-07-19)

---

## 1. Executive Summary

COMEN01C is the main menu program for regular (non-admin) users of the CardDemo CICS application. It is invoked via XCTL from COSGN00C after successful authentication of a non-admin user. The program presents a dynamically built menu screen (BMS mapset COMEN01, map COMEN1A) whose options are sourced entirely from the COMEN02Y copybook data table at compile time. Upon receiving a valid menu selection, it transfers control (XCTL) to the corresponding functional program, passing the CARDDEMO-COMMAREA. It also enforces a simple access control check preventing regular users from selecting admin-only menu options. A secondary access mechanism checks whether the target program is installed in CICS before transferring control.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `app/cbl/COMEN01C.cbl` | CICS COBOL Program | Main source |
| `app/bms/COMEN01.bms` | BMS Mapset | Screen definition |
| `app/cpy-bms/COMEN01.CPY` | BMS-generated Copybook | Map symbolic descriptions (COMEN1AI / COMEN1AO) |
| `app/cpy/COCOM01Y.cpy` | Copybook | CARDDEMO-COMMAREA definition |
| `app/cpy/COMEN02Y.cpy` | Copybook | Menu options data table (CDEMO-MENU-OPT-*) |
| `app/cpy/COTTL01Y.cpy` | Copybook | Screen title literals |
| `app/cpy/CSDAT01Y.cpy` | Copybook | Date/time working storage |
| `app/cpy/CSMSG01Y.cpy` | Copybook | Common message literals |
| `app/cpy/CSUSR01Y.cpy` | Copybook | SEC-USER-DATA (not used for I/O here; included for record layout availability) |
| `DFHAID` | System Copybook | AID key constants |
| `DFHBMSCA` | System Copybook | BMS attribute byte constants (DFHRED, DFHGREEN) |

---

## 3. Program Identity and Entry

| Item | Value | Source Reference |
|---|---|---|
| PROGRAM-ID | COMEN01C | `COMEN01C.cbl` line 23 |
| Transaction ID | CM00 | `WS-TRANID` line 37 |
| Map | COMEN1A | SEND-MENU-SCREEN paragraph, line 216 |
| Mapset | COMEN01 | SEND-MENU-SCREEN paragraph, line 217 |
| Invoked by | COSGN00C via XCTL | When SEC-USR-TYPE != 'A' |

---

## 4. WORKING-STORAGE Data Structures

### 4.1 WS-VARIABLES (inline, lines 35-48)

| Field | PIC | Initial Value | Purpose |
|---|---|---|---|
| WS-PGMNAME | X(08) | 'COMEN01C' | Program name for screen header |
| WS-TRANID | X(04) | 'CM00' | Transaction ID for CICS RETURN |
| WS-MESSAGE | X(80) | SPACES | Error/info message buffer |
| WS-USRSEC-FILE | X(08) | 'USRSEC  ' | Declared but not used for I/O in this program |
| WS-ERR-FLG | X(01) | 'N' | Error flag (88 ERR-FLG-ON='Y', ERR-FLG-OFF='N') |
| WS-RESP-CD | S9(09) COMP | ZEROS | CICS RESP return code |
| WS-REAS-CD | S9(09) COMP | ZEROS | CICS RESP2 return code |
| WS-OPTION-X | X(02) JUST RIGHT | — | Right-justified alphanumeric staging area for option input |
| WS-OPTION | 9(02) | 0 | Numeric option selected by user |
| WS-IDX | S9(04) COMP | ZEROS | Loop index for scanning OPTIONI and building menu lines |
| WS-MENU-OPT-TXT | X(40) | SPACES | Formatted menu line text (e.g., "01. Account View") |

### 4.2 CARDDEMO-COMMAREA (COPY COCOM01Y)

Same structure as described in COSGN00C_spec.md. In COMEN01C, the COMMAREA is received from COSGN00C (or from a returning sub-program) and is used to:
- Determine first vs. re-entry via CDEMO-PGM-CONTEXT (88 CDEMO-PGM-REENTER)
- Read CDEMO-USRTYP-USER for access control enforcement
- Populate CDEMO-FROM-TRANID and CDEMO-FROM-PROGRAM before XCTL
- Reset CDEMO-PGM-CONTEXT to ZEROS before XCTL to functional programs

### 4.3 Menu Options Table (COPY COMEN02Y — app/cpy/COMEN02Y.cpy)

This copybook defines a static in-memory data table of 11 active menu options (CDEMO-MENU-OPT-COUNT = 11). The table is defined as FILLER data that is REDEFINED by the CDEMO-MENU-OPTIONS array.

**Redefined Array Structure (CDEMO-MENU-OPTIONS):**
```
05 CDEMO-MENU-OPTIONS REDEFINES CDEMO-MENU-OPTIONS-DATA.
   10 CDEMO-MENU-OPT OCCURS 12 TIMES.
      15 CDEMO-MENU-OPT-NUM      PIC 9(02).
      15 CDEMO-MENU-OPT-NAME     PIC X(35).
      15 CDEMO-MENU-OPT-PGMNAME  PIC X(08).
      15 CDEMO-MENU-OPT-USRTYPE  PIC X(01).
```

**Menu Options Data (as defined in COMEN02Y, lines 25-91 of copybook):**

| Opt# | Option Name | Target Program | User Type |
|---|---|---|---|
| 01 | Account View | COACTVWC | U |
| 02 | Account Update | COACTUPC | U |
| 03 | Credit Card List | COCRDLIC | U |
| 04 | Credit Card View | COCRDSLC | U |
| 05 | Credit Card Update | COCRDUPC | U |
| 06 | Transaction List | COTRN00C | U |
| 07 | Transaction View | COTRN01C | U |
| 08 | Transaction Add | COTRN02C | U |
| 09 | Transaction Reports | CORPT00C | U |
| 10 | Bill Payment | COBIL00C | U |
| 11 | Pending Authorization View | COPAUS0C | U |

All options have CDEMO-MENU-OPT-USRTYPE = 'U' (regular user access). The copybook declares OCCURS 12 TIMES in the REDEFINES but only 11 options are populated; slot 12 is empty.

**Note:** The file is named COMEN02Y but its 01-level group is `CARDDEMO-MAIN-MENU-OPTIONS`, not an admin options structure. The naming implies it was the second (02) companion copybook to COMEN01C's BMS copybook.

### 4.4 Map Symbolic Descriptions (COPY COMEN01 — resolves to app/cpy-bms/COMEN01.CPY)

**COMEN1AI** (input):

| Field | PIC | Purpose |
|---|---|---|
| OPTIONL | COMP S9(4) | Length of received OPTION field data |
| OPTIONI | X(2) | User's menu selection (2-digit numeric) |

**COMEN1AO** (output — REDEFINES COMEN1AI):

| Field | PIC | Purpose |
|---|---|---|
| TRNNAMEO | X(4) | Transaction ID in header |
| TITLE01O | X(40) | Title line 1 |
| CURDATEO | X(8) | Current date MM/DD/YY |
| PGMNAMEO | X(8) | Program name in header |
| TITLE02O | X(40) | Title line 2 |
| CURTIMEO | X(8) | Current time HH:MM:SS |
| OPTN001O–OPTN012O | X(40) each | Menu option text lines (12 slots) |
| OPTIONO | X(2) | Echo of selected option number |
| ERRMSGO | X(78) | Error message display area |
| ERRMSGC | X(1) | Error message colour attribute (DFHRED / DFHGREEN) |

---

## 5. LINKAGE SECTION

```
01 DFHCOMMAREA.
   05 LK-COMMAREA PIC X(01) OCCURS 1 TO 32767 TIMES DEPENDING ON EIBCALEN.
```
Source: lines 67-69.

On re-entry (EIBCALEN > 0), the program executes:
```
MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
```
(line 86), copying the incoming COMMAREA into the working storage structure before processing.

---

## 6. CICS Commands Inventory

| Command | Paragraph | Purpose | Source Lines |
|---|---|---|---|
| `EXEC CICS RETURN TRANSID('CM00') COMMAREA(CARDDEMO-COMMAREA)` | MAIN-PARA | Pseudo-conversational RETURN; re-invokes CM00 on next AID | Lines 107-110 |
| `EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM)` | RETURN-TO-SIGNON-SCREEN | Transfer control back to COSGN00C (or override program) on PF3 | Lines 201-203 |
| `EXEC CICS XCTL PROGRAM(CDEMO-MENU-OPT-PGMNAME(WS-OPTION)) COMMAREA(CARDDEMO-COMMAREA)` | PROCESS-ENTER-KEY (COPAUS0C branch) | XCTL to COPAUS0C if INQUIRE confirms it is installed | Lines 156-159 |
| `EXEC CICS XCTL PROGRAM(CDEMO-MENU-OPT-PGMNAME(WS-OPTION)) COMMAREA(CARDDEMO-COMMAREA)` | PROCESS-ENTER-KEY (OTHER branch) | XCTL to any other installed functional program | Lines 184-187 |
| `EXEC CICS INQUIRE PROGRAM(...) NOHANDLE` | PROCESS-ENTER-KEY | Checks if COPAUS0C is installed before XCTL | Lines 148-151 |
| `EXEC CICS RECEIVE MAP('COMEN1A') MAPSET('COMEN01') INTO(COMEN1AI) RESP(...) RESP2(...)` | RECEIVE-MENU-SCREEN | Receives terminal input from menu screen | Lines 227-233 |
| `EXEC CICS SEND MAP('COMEN1A') MAPSET('COMEN01') FROM(COMEN1AO) ERASE` | SEND-MENU-SCREEN | Sends menu screen to terminal | Lines 215-220 |

---

## 7. Program Flow — Paragraph-by-Paragraph Analysis

### 7.1 MAIN-PARA (lines 75-110) — Entry Point

**Step 1 — Initialize:**
- `SET ERR-FLG-OFF TO TRUE`
- Clear WS-MESSAGE and ERRMSGO

**Step 2 — COMMAREA / first entry check (line 82):**

- **EIBCALEN = 0**: No COMMAREA — this means the program was invoked without authentication context (bypassing COSGN00C). The program immediately calls RETURN-TO-SIGNON-SCREEN with `MOVE 'COSGN00C' TO CDEMO-FROM-PROGRAM` (line 83). This is a safety guard.

- **EIBCALEN > 0**: Copies COMMAREA into CARDDEMO-COMMAREA (line 86).

  - **NOT CDEMO-PGM-REENTER** (CDEMO-PGM-CONTEXT = 0, first entry from COSGN00C): Sets CDEMO-PGM-REENTER to TRUE (line 88, sets value to 1), initializes COMEN1AO to LOW-VALUES, PERFORMs SEND-MENU-SCREEN.

  - **CDEMO-PGM-REENTER** (context = 1, returning from self or from a functional program pressing PF3/back): PERFORMs RECEIVE-MENU-SCREEN, then evaluates EIBAID:
    - `DFHENTER`: PERFORMs PROCESS-ENTER-KEY
    - `DFHPF3`: Sets CDEMO-TO-PROGRAM = 'COSGN00C', PERFORMs RETURN-TO-SIGNON-SCREEN
    - `OTHER`: ERR-FLG-ON, CCDA-MSG-INVALID-KEY, PERFORM SEND-MENU-SCREEN

**Step 3 — RETURN (lines 107-110):**
```
EXEC CICS RETURN TRANSID('CM00') COMMAREA(CARDDEMO-COMMAREA)
```
Perpetuates pseudo-conversational loop under CM00. Not reached if XCTL was issued.

---

### 7.2 PROCESS-ENTER-KEY (lines 115-191)

**Step 1 — Parse option number (lines 117-125):**
The option field OPTIONI is X(2). The program scans backwards from LENGTH OF OPTIONI to find the last non-space character, then moves the significant portion to WS-OPTION-X. All spaces in WS-OPTION-X are replaced with '0' via INSPECT, then WS-OPTION-X is moved to WS-OPTION (numeric). The effect is right-justification with zero-fill (e.g., ' 3' becomes '03', '11' stays '11').

This is redundant with the JUSTIFY=(RIGHT,ZERO) attribute defined in the BMS for the OPTION field; it provides defensive handling in case the terminal sends left-justified data.

**Step 2 — Range validation (lines 127-134):**
```
IF WS-OPTION IS NOT NUMERIC OR
   WS-OPTION > CDEMO-MENU-OPT-COUNT OR
   WS-OPTION = ZEROS
```
If any condition is true: ERR-FLG-ON, message = 'Please enter a valid option number...', PERFORM SEND-MENU-SCREEN.

**Step 3 — Access control check (lines 136-143):**
```
IF CDEMO-USRTYP-USER AND
   CDEMO-MENU-OPT-USRTYPE(WS-OPTION) = 'A'
```
If a regular user attempts to select an option flagged as Admin-Only ('A'): ERR-FLG-ON, message = 'No access - Admin Only option...', PERFORM SEND-MENU-SCREEN.

Note: All 11 options in COMEN02Y have USRTYPE = 'U', so this check will never trigger for any currently defined option. It is a future-proofing guard.

**Step 4 — Program dispatch (lines 145-190):**
If NOT ERR-FLG-ON:

```
EVALUATE TRUE
    WHEN CDEMO-MENU-OPT-PGMNAME(WS-OPTION) = 'COPAUS0C'
        -- Special handling: check if installed first
        EXEC CICS INQUIRE PROGRAM(CDEMO-MENU-OPT-PGMNAME(WS-OPTION)) NOHANDLE
        IF EIBRESP = DFHRESP(NORMAL)
            [set COMMAREA routing fields]
            EXEC CICS XCTL PROGRAM(COPAUS0C) COMMAREA(CARDDEMO-COMMAREA)
        ELSE
            -- Not installed: format message in red
            STRING 'This option ' ... ' is not installed...' INTO WS-MESSAGE
    WHEN CDEMO-MENU-OPT-PGMNAME(WS-OPTION)(1:5) = 'DUMMY'
        -- Placeholder option: format "coming soon" message in green
        STRING 'This option ' ... 'is coming soon ...' INTO WS-MESSAGE
    WHEN OTHER
        [set COMMAREA routing fields]
        EXEC CICS XCTL PROGRAM(CDEMO-MENU-OPT-PGMNAME(WS-OPTION)) COMMAREA(CARDDEMO-COMMAREA)
END-EVALUATE
```

Before every XCTL in the dispatch logic, the following COMMAREA fields are set:
- `MOVE WS-TRANID TO CDEMO-FROM-TRANID` (CM00)
- `MOVE WS-PGMNAME TO CDEMO-FROM-PROGRAM` (COMEN01C) — note: set twice for the OTHER branch (lines 179-180, apparent copy-paste)
- `MOVE ZEROS TO CDEMO-PGM-CONTEXT` (reset to CDEMO-PGM-ENTER = 0)

**After EVALUATE (line 190):** If no XCTL was issued (COPAUS0C not installed, or DUMMY option), `PERFORM SEND-MENU-SCREEN` is called to re-display with the message.

---

### 7.3 RETURN-TO-SIGNON-SCREEN (lines 196-203)

```
IF CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES
    MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM
END-IF
EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM)
```
Defaults to COSGN00C if CDEMO-TO-PROGRAM is not set. No COMMAREA is passed in this XCTL — source line 202 shows `XCTL PROGRAM(CDEMO-TO-PROGRAM)` without a COMMAREA clause, which means the target program (COSGN00C) will receive EIBCALEN=0 and will display the sign-on screen fresh.

---

### 7.4 SEND-MENU-SCREEN (lines 208-220)

1. PERFORMs POPULATE-HEADER-INFO
2. PERFORMs BUILD-MENU-OPTIONS
3. Moves WS-MESSAGE to ERRMSGO
4. `EXEC CICS SEND MAP('COMEN1A') MAPSET('COMEN01') FROM(COMEN1AO) ERASE`

Note: Unlike COSGN00C's SEND-SIGNON-SCREEN, the CURSOR option is not specified here. The cursor position will default to the first unprotected field (OPTION at row 20, col 41).

---

### 7.5 RECEIVE-MENU-SCREEN (lines 225-233)

```
EXEC CICS RECEIVE MAP('COMEN1A') MAPSET('COMEN01') INTO(COMEN1AI) RESP(...) RESP2(...)
```
Reads terminal input into COMEN1AI. RESP and RESP2 are captured but not explicitly tested after the receive.

---

### 7.6 POPULATE-HEADER-INFO (lines 238-257)

Identical pattern to COSGN00C's POPULATE-HEADER-INFO:
1. `MOVE FUNCTION CURRENT-DATE TO WS-CURDATE-DATA`
2. Formats MM/DD/YY and HH:MM:SS
3. Moves titles, transaction ID, program name, date, and time to COMEN1AO output fields

Note: Unlike COSGN00C, this paragraph does NOT issue `EXEC CICS ASSIGN APPLID` or `EXEC CICS ASSIGN SYSID`. Those fields are absent from the COMEN01 BMS screen definition.

---

### 7.7 BUILD-MENU-OPTIONS (lines 262-303)

```
PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > CDEMO-MENU-OPT-COUNT
    STRING CDEMO-MENU-OPT-NUM(WS-IDX)  DELIMITED BY SIZE
           '. '                         DELIMITED BY SIZE
           CDEMO-MENU-OPT-NAME(WS-IDX) DELIMITED BY SIZE
      INTO WS-MENU-OPT-TXT
    EVALUATE WS-IDX
        WHEN 1 MOVE WS-MENU-OPT-TXT TO OPTN001O
        ...
        WHEN 11 MOVE WS-MENU-OPT-TXT TO OPTN011O
        WHEN OTHER CONTINUE
    END-EVALUATE
END-PERFORM
```

Iterates from 1 to CDEMO-MENU-OPT-COUNT (11) and formats each menu option as "NN. Option Name" into the corresponding OPTN00nO screen field. OPTN012O is never populated (WHEN OTHER CONTINUE) since only 11 options are defined.

---

## 8. Inter-Program Interactions

| Direction | Target Program | Mechanism | Condition | COMMAREA |
|---|---|---|---|---|
| Inbound from | COSGN00C | XCTL | Successful login, user type 'U' | CARDDEMO-COMMAREA with USER-TYPE='U', PGM-CONTEXT=0 |
| Inbound from | Any functional program | XCTL (PF3 back) | User presses PF3 in sub-program | CARDDEMO-COMMAREA updated by sub-program |
| Outbound | COACTVWC | XCTL | Option 01 selected | CARDDEMO-COMMAREA with FROM=CM00/COMEN01C, CONTEXT=0 |
| Outbound | COACTUPC | XCTL | Option 02 selected | Same pattern |
| Outbound | COCRDLIC | XCTL | Option 03 selected | Same pattern |
| Outbound | COCRDSLC | XCTL | Option 04 selected | Same pattern |
| Outbound | COCRDUPC | XCTL | Option 05 selected | Same pattern |
| Outbound | COTRN00C | XCTL | Option 06 selected | Same pattern |
| Outbound | COTRN01C | XCTL | Option 07 selected | Same pattern |
| Outbound | COTRN02C | XCTL | Option 08 selected | Same pattern |
| Outbound | CORPT00C | XCTL | Option 09 selected | Same pattern |
| Outbound | COBIL00C | XCTL | Option 10 selected | Same pattern |
| Outbound | COPAUS0C | XCTL (guarded by INQUIRE) | Option 11 selected AND program installed | Same pattern |
| Outbound | COSGN00C | XCTL (no COMMAREA) | PF3 pressed | None |
| Self | COMEN01C (via CM00) | RETURN TRANSID | After every screen send | CARDDEMO-COMMAREA |

---

## 9. Error Handling

| Error Condition | Detection | Response | Message |
|---|---|---|---|
| No COMMAREA on entry | EIBCALEN = 0 | XCTL to COSGN00C | None (silent redirect) |
| Invalid option (non-numeric, zero, or > 11) | WS-OPTION validation | Re-display menu with error | 'Please enter a valid option number...' |
| Regular user selects admin-only option | CDEMO-USRTYP-USER + USRTYPE='A' | Re-display menu with error | 'No access - Admin Only option...' |
| COPAUS0C not installed | EIBRESP != DFHRESP(NORMAL) after INQUIRE | Re-display menu with red message | 'This option ... is not installed...' |
| DUMMY program option selected | PGMNAME(1:5) = 'DUMMY' | Re-display menu with green message | 'This option ...is coming soon ...' |
| Invalid AID key | EVALUATE EIBAID WHEN OTHER | Re-display menu with error | CCDA-MSG-INVALID-KEY |

No EXEC CICS HANDLE CONDITION is established.

---

## 10. Transaction Flow Participation

```
COSGN00C (XCTL, type='U')
    |
COMEN01C (first entry: PGM-CONTEXT=0)
    |
    SEND COMEN1A (menu screen with 11 options)
    RETURN TRANSID(CM00)
    |
    [User selects option N, presses Enter]
    |
    RECEIVE COMEN1A
    Parse + validate option
    |
    [Valid option]  --> XCTL to CDEMO-MENU-OPT-PGMNAME(N)
    [Invalid]       --> SEND error screen, RETURN TRANSID(CM00)
    [PF3]           --> XCTL COSGN00C (no COMMAREA, fresh sign-on)
```

---

## 11. Business Rules Catalog

| Rule ID | Rule Description | Source Location |
|---|---|---|
| BR-MNU-001 | A user arriving without a COMMAREA is redirected to sign-on (security guard) | MAIN-PARA, lines 82-84 |
| BR-MNU-002 | On first entry (PGM-CONTEXT=0), the menu is sent without receiving input first | MAIN-PARA, lines 87-90 |
| BR-MNU-003 | CDEMO-PGM-REENTER is set to TRUE (value=1) on first entry to prevent re-send loop | MAIN-PARA, line 88 |
| BR-MNU-004 | Menu option '0' and any value greater than CDEMO-MENU-OPT-COUNT are invalid | PROCESS-ENTER-KEY, lines 127-134 |
| BR-MNU-005 | Regular users cannot select options with USRTYPE='A' | PROCESS-ENTER-KEY, lines 136-143 |
| BR-MNU-006 | COPAUS0C (Pending Authorization View) is verified as installed via CICS INQUIRE before XCTL | PROCESS-ENTER-KEY, lines 147-168 |
| BR-MNU-007 | Options with program name starting 'DUMMY' display a "coming soon" message in green | PROCESS-ENTER-KEY, lines 169-176 |
| BR-MNU-008 | CDEMO-PGM-CONTEXT is reset to ZEROS before every XCTL to a functional program, signalling first entry | PROCESS-ENTER-KEY, lines 155, 183 |
| BR-MNU-009 | PF3 returns to sign-on screen WITHOUT passing a COMMAREA, forcing a fresh sign-on | RETURN-TO-SIGNON-SCREEN, line 202 |

---

## 12. Open Questions and Gaps

1. **WS-USRSEC-FILE declared but not used**: The field `WS-USRSEC-FILE PIC X(08) VALUE 'USRSEC  '` is declared (line 39) but COMEN01C does not issue any CICS READ against USRSEC. This appears to be a copy-paste artefact from COSGN00C. Confidence: HIGH.
2. **RECEIVE MAP RESP not tested**: After RECEIVE-MENU-SCREEN, WS-RESP-CD is populated but never evaluated. A MAPFAIL condition (user presses Enter with nothing changed) would be unhandled. Confidence: HIGH.
3. **Duplicate MOVE at lines 179-180**: `MOVE WS-PGMNAME TO CDEMO-FROM-PROGRAM` appears twice consecutively for the OTHER WHEN branch. This is likely a copy-paste defect with no functional impact. Confidence: HIGH.
4. **CSUSR01Y included but SEC-USER-DATA not used**: The copybook is included (line 58) making SEC-USER-DATA available in WORKING-STORAGE, but COMEN01C performs no VSAM reads. Included for uniformity with other programs in the suite.
5. **No APPLID/SYSID on header**: Unlike COSGN00C, COMEN01C does not call ASSIGN APPLID/SYSID. The COMEN01 BMS map does not define those fields, confirming this is intentional.
