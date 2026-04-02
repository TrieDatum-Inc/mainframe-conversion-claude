# Technical Specification: COSGN00C — Sign-on Program

**Source File:** `app/cbl/COSGN00C.cbl`
**Application:** CardDemo
**Type:** CICS Online COBOL Program
**Transaction ID:** CC00
**Version Tag:** CardDemo_v1.0-15-g27d6c6f-68 (2022-07-19)

---

## 1. Executive Summary

COSGN00C is the entry-point authentication program for the CardDemo CICS application. It presents the sign-on screen (BMS mapset COSGN00, map COSGN0A), collects a user ID and password, validates credentials against the USRSEC VSAM file, and routes authenticated users to either the admin menu (COADM01C) or the regular user menu (COMEN01C) based on the user type stored in the security file. It is the first program invoked when transaction CC00 is started.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `app/cbl/COSGN00C.cbl` | CICS COBOL Program | Main source |
| `app/bms/COSGN00.bms` | BMS Mapset | Screen definition |
| `app/cpy-bms/COSGN00.CPY` | BMS-generated Copybook | Map symbolic descriptions (COSGN0AI / COSGN0AO) |
| `app/cpy/COCOM01Y.cpy` | Copybook | CARDDEMO-COMMAREA definition |
| `app/cpy/COTTL01Y.cpy` | Copybook | Screen title literals (CCDA-TITLE01, CCDA-TITLE02) |
| `app/cpy/CSDAT01Y.cpy` | Copybook | Date/time working storage layout |
| `app/cpy/CSMSG01Y.cpy` | Copybook | Common message literals |
| `app/cpy/CSUSR01Y.cpy` | Copybook | SEC-USER-DATA record layout |
| `DFHAID` | System Copybook | Attention Identifier (AID) constants |
| `DFHBMSCA` | System Copybook | BMS attribute byte constants |

---

## 3. Program Identity and Entry

| Item | Value | Source Reference |
|---|---|---|
| PROGRAM-ID | COSGN00C | `COSGN00C.cbl` line 23 |
| Transaction ID | CC00 | `WS-TRANID` line 37 |
| Map | COSGN0A | PROCESS-ENTER-KEY paragraph, line 111 |
| Mapset | COSGN00 | PROCESS-ENTER-KEY paragraph, line 112 |
| VSAM file accessed | USRSEC | `WS-USRSEC-FILE` line 39 |

The program is invoked as the first task in the CC00 transaction. There is no calling program; the transaction is started directly by the terminal operator typing `CC00` or by a CICS transaction routing mechanism.

---

## 4. WORKING-STORAGE Data Structures

### 4.1 WS-VARIABLES (defined inline, lines 35-46)

| Field | PIC | Initial Value | Purpose |
|---|---|---|---|
| WS-PGMNAME | X(08) | 'COSGN00C' | Program name displayed on screen header |
| WS-TRANID | X(04) | 'CC00' | Transaction ID for CICS RETURN |
| WS-MESSAGE | X(80) | SPACES | Error/status message buffer for ERRMSGO |
| WS-USRSEC-FILE | X(08) | 'USRSEC  ' | CICS dataset name for the user security VSAM file |
| WS-ERR-FLG | X(01) | 'N' | Error flag; 88 ERR-FLG-ON = 'Y', ERR-FLG-OFF = 'N' |
| WS-RESP-CD | S9(09) COMP | ZEROS | CICS RESP code from READ |
| WS-REAS-CD | S9(09) COMP | ZEROS | CICS RESP2 code from READ |
| WS-USER-ID | X(08) | — | Upper-cased user ID from screen input |
| WS-USER-PWD | X(08) | — | Upper-cased password from screen input |

### 4.2 CARDDEMO-COMMAREA (from COPY COCOM01Y, lines 19-44 of copybook)

This is the application-wide communication area passed between all programs via CICS COMMAREA.

| Field | PIC | Purpose |
|---|---|---|
| CDEMO-FROM-TRANID | X(04) | Transaction ID of the calling program |
| CDEMO-FROM-PROGRAM | X(08) | Name of the calling program |
| CDEMO-TO-TRANID | X(04) | Target transaction ID |
| CDEMO-TO-PROGRAM | X(08) | Target program name |
| CDEMO-USER-ID | X(08) | Authenticated user ID (set on successful login) |
| CDEMO-USER-TYPE | X(01) | User type: 'A' = Admin (88 CDEMO-USRTYP-ADMIN), 'U' = Regular (88 CDEMO-USRTYP-USER) |
| CDEMO-PGM-CONTEXT | 9(01) | Re-entry flag: 0 = first entry (88 CDEMO-PGM-ENTER), 1 = re-entry (88 CDEMO-PGM-REENTER) |
| CDEMO-CUST-ID | 9(09) | Customer ID (not used in this program) |
| CDEMO-ACCT-ID | 9(11) | Account ID (not used in this program) |
| CDEMO-CARD-NUM | 9(16) | Card number (not used in this program) |
| CDEMO-LAST-MAP | X(7) | Last map displayed (not used in this program) |
| CDEMO-LAST-MAPSET | X(7) | Last mapset (not used in this program) |

### 4.3 SEC-USER-DATA (from COPY CSUSR01Y)

Record layout for a user read from the USRSEC VSAM file (keyed by user ID):

| Field | PIC | Purpose |
|---|---|---|
| SEC-USR-ID | X(08) | User ID (VSAM key field) |
| SEC-USR-FNAME | X(20) | First name |
| SEC-USR-LNAME | X(20) | Last name |
| SEC-USR-PWD | X(08) | Password (stored plain-text) |
| SEC-USR-TYPE | X(01) | User type: 'A' = Admin, 'U' = Regular |
| SEC-USR-FILLER | X(23) | Padding |

Total record length: 80 bytes.

### 4.4 Map Symbolic Descriptions (from COPY COSGN00 — resolves to app/cpy-bms/COSGN00.CPY)

The COPY statement `COPY COSGN00` at line 50 expands to the BMS-generated symbolic map. Two 01-level structures are generated:

**COSGN0AI** (input structure) — fields used by the program on RECEIVE MAP:

| Field | PIC | Purpose |
|---|---|---|
| USERIDL | COMP S9(4) | Length of data received in USERID field |
| USERIDI | X(8) | User ID input value |
| PASSWDL | COMP S9(4) | Length of data received in PASSWD field |
| PASSWDI | X(8) | Password input value |

**COSGN0AO** (output structure — REDEFINES COSGN0AI) — fields written on SEND MAP:

| Field | PIC | Purpose |
|---|---|---|
| TRNNAMEO | X(4) | Transaction name area in header |
| TITLE01O | X(40) | Application title line 1 |
| CURDATEO | X(8) | Current date (MM/DD/YY) |
| PGMNAMEO | X(8) | Program name in header |
| TITLE02O | X(40) | Application title line 2 |
| CURTIMEO | X(9) | Current time (HH:MM:SS) |
| APPLIDO | X(8) | CICS APPLID |
| SYSIDO | X(8) | CICS SYSID |
| USERIDO | X(8) | User ID echo on screen |
| PASSWDO | X(8) | Password field (DRK attribute masks it) |
| ERRMSGO | X(78) | Error message display area |
| ERRMSGC | X(1) | Error message colour attribute byte |

### 4.5 Date/Time Data (from COPY CSDAT01Y)

| Field | PIC | Purpose |
|---|---|---|
| WS-CURDATE-DATA | Group | Receives FUNCTION CURRENT-DATE output |
| WS-CURDATE-YEAR | 9(04) | 4-digit year |
| WS-CURDATE-MONTH | 9(02) | Month |
| WS-CURDATE-DAY | 9(02) | Day |
| WS-CURTIME-HOURS | 9(02) | Hours |
| WS-CURTIME-MINUTE | 9(02) | Minutes |
| WS-CURTIME-SECOND | 9(02) | Seconds |
| WS-CURDATE-MM-DD-YY | Group | Formatted date MM/DD/YY for screen |
| WS-CURTIME-HH-MM-SS | Group | Formatted time HH:MM:SS for screen |

### 4.6 Common Literals (from COPY CSMSG01Y and COPY COTTL01Y)

| Field | Value |
|---|---|
| CCDA-MSG-THANK-YOU | 'Thank you for using CardDemo application...' |
| CCDA-MSG-INVALID-KEY | 'Invalid key pressed. Please see below...' |
| CCDA-TITLE01 | '      AWS Mainframe Modernization       ' |
| CCDA-TITLE02 | '              CardDemo                  ' |

---

## 5. LINKAGE SECTION

```
01 DFHCOMMAREA.
   05 LK-COMMAREA PIC X(01) OCCURS 1 TO 32767 TIMES DEPENDING ON EIBCALEN.
```
Source: `COSGN00C.cbl` lines 65-67.

The COMMAREA is received from a prior CICS RETURN (self-reinvocation of CC00). On the first invocation EIBCALEN = 0; on all subsequent invocations after RETURN TRANSID(CC00) COMMAREA(...), EIBCALEN = LENGTH OF CARDDEMO-COMMAREA. The program copies the COMMAREA into CARDDEMO-COMMAREA only within menu programs (not in COSGN00C itself — COSGN00C reads EIBCALEN to determine first vs. subsequent entry but does not explicitly MOVE DFHCOMMAREA to CARDDEMO-COMMAREA before passing it outward via XCTL COMMAREA).

---

## 6. CICS Commands Inventory

| Command | Paragraph | Purpose | Source Lines |
|---|---|---|---|
| `EXEC CICS RETURN TRANSID(CC00) COMMAREA(CARDDEMO-COMMAREA) LENGTH(...)` | MAIN-PARA | Pseudo-conversational return; suspends and re-invokes CC00 | Lines 98-102 |
| `EXEC CICS RECEIVE MAP('COSGN0A') MAPSET('COSGN00') RESP(...) RESP2(...)` | PROCESS-ENTER-KEY | Receives terminal input into COSGN0AI | Lines 110-115 |
| `EXEC CICS SEND MAP('COSGN0A') MAPSET('COSGN00') FROM(COSGN0AO) ERASE CURSOR` | SEND-SIGNON-SCREEN | Sends sign-on screen; ERASE clears terminal; CURSOR positions at -1 field | Lines 151-157 |
| `EXEC CICS SEND TEXT FROM(WS-MESSAGE) LENGTH(...) ERASE FREEKB` | SEND-PLAIN-TEXT | Sends goodbye text when PF3 pressed; FREEKB unlocks keyboard | Lines 164-168 |
| `EXEC CICS RETURN` | SEND-PLAIN-TEXT | Immediate termination after goodbye message | Lines 171-172 |
| `EXEC CICS ASSIGN APPLID(APPLIDO OF COSGN0AO)` | POPULATE-HEADER-INFO | Retrieves CICS application ID for header | Lines 198-200 |
| `EXEC CICS ASSIGN SYSID(SYSIDO OF COSGN0AO)` | POPULATE-HEADER-INFO | Retrieves CICS system ID for header | Lines 202-204 |
| `EXEC CICS READ DATASET('USRSEC') INTO(SEC-USER-DATA) LENGTH(...) RIDFLD(WS-USER-ID) KEYLENGTH(...) RESP(...) RESP2(...)` | READ-USER-SEC-FILE | Reads user security record by user ID key | Lines 211-219 |
| `EXEC CICS XCTL PROGRAM('COADM01C') COMMAREA(CARDDEMO-COMMAREA)` | READ-USER-SEC-FILE | Transfer control to admin menu (user type 'A') | Lines 231-234 |
| `EXEC CICS XCTL PROGRAM('COMEN01C') COMMAREA(CARDDEMO-COMMAREA)` | READ-USER-SEC-FILE | Transfer control to regular user menu (user type 'U') | Lines 236-239 |

---

## 7. Program Flow — Paragraph-by-Paragraph Analysis

### 7.1 MAIN-PARA (lines 73-102) — Entry Point

This is the sole entry paragraph. All logic branches from here.

**Step 1 — Initialize flags:**
- `SET ERR-FLG-OFF TO TRUE` resets WS-ERR-FLG to 'N'.
- `MOVE SPACES TO WS-MESSAGE` and `ERRMSGO OF COSGN0AO` clears any prior error display.

**Step 2 — First entry vs. re-entry check (EIBCALEN test, line 80):**

- **EIBCALEN = 0** (first invocation, no prior COMMAREA): Program initializes the output map area to LOW-VALUES (`MOVE LOW-VALUES TO COSGN0AO`), sets cursor to USERID field (`MOVE -1 TO USERIDL OF COSGN0AI`), then PERFORMs SEND-SIGNON-SCREEN. After SEND, falls through to EXEC CICS RETURN TRANSID(CC00) which suspends the task and re-queues it for next terminal input.

- **EIBCALEN > 0** (re-entry after pseudo-conversational RETURN): Evaluates EIBAID to determine which key was pressed:
  - `DFHENTER`: PERFORMs PROCESS-ENTER-KEY (authentication logic).
  - `DFHPF3`: Sets WS-MESSAGE to CCDA-MSG-THANK-YOU, PERFORMs SEND-PLAIN-TEXT (goodbye message + unconditional RETURN — does not reach the RETURN at line 98).
  - `OTHER`: Sets ERR-FLG-ON, loads CCDA-MSG-INVALID-KEY into WS-MESSAGE, PERFORMs SEND-SIGNON-SCREEN.

**Step 3 — RETURN (line 98-102):**
After all PERFORM branches (except SEND-PLAIN-TEXT which returns early), control falls through to:
```
EXEC CICS RETURN TRANSID(CC00) COMMAREA(CARDDEMO-COMMAREA) LENGTH(LENGTH OF CARDDEMO-COMMAREA)
```
This perpetuates the pseudo-conversational loop for the CC00 transaction.

**Note:** If XCTL was issued in READ-USER-SEC-FILE, control never returns to MAIN-PARA; the RETURN at line 98 is not executed in the success path.

---

### 7.2 PROCESS-ENTER-KEY (lines 108-140)

Called when DFHENTER (Enter key) is detected.

**Step 1 — RECEIVE MAP (lines 110-115):**
`EXEC CICS RECEIVE MAP('COSGN0A') MAPSET('COSGN00')` reads terminal data into COSGN0AI. RESP and RESP2 are captured but not explicitly tested here (relied upon to not abort — no HANDLE CONDITION established for MAP).

**Step 2 — Input validation (lines 117-130):**
`EVALUATE TRUE`:
- If USERIDI = SPACES or LOW-VALUES: set ERR-FLG-ON, message = 'Please enter User ID ...', cursor to USERIDL, PERFORM SEND-SIGNON-SCREEN (returns to caller after send but continues to Step 3).
- If PASSWDI = SPACES or LOW-VALUES: set ERR-FLG-ON, message = 'Please enter Password ...', cursor to PASSWDL, PERFORM SEND-SIGNON-SCREEN.
- OTHERWISE: CONTINUE (fall through).

**Important:** Despite the validation, the EVALUATE does not EXIT PERFORM or GO TO; after SEND-SIGNON-SCREEN returns, execution continues to Step 3. However, ERR-FLG-ON prevents the file read from executing (tested at line 138).

**Step 3 — Upper-case and store input (lines 132-136):**
```
MOVE FUNCTION UPPER-CASE(USERIDI OF COSGN0AI) TO WS-USER-ID CDEMO-USER-ID
MOVE FUNCTION UPPER-CASE(PASSWDI OF COSGN0AI) TO WS-USER-PWD
```
User ID is written to both WS-USER-ID (for VSAM key) and CDEMO-USER-ID (for COMMAREA).

**Step 4 — Conditional file read (lines 138-140):**
```
IF NOT ERR-FLG-ON
    PERFORM READ-USER-SEC-FILE
END-IF
```

---

### 7.3 SEND-SIGNON-SCREEN (lines 145-157)

Called from MAIN-PARA (first entry), PROCESS-ENTER-KEY (validation errors), and READ-USER-SEC-FILE (authentication errors).

1. PERFORMs POPULATE-HEADER-INFO to fill date/time/title fields.
2. MOVEs WS-MESSAGE to ERRMSGO OF COSGN0AO.
3. Sends the map with ERASE and CURSOR options. CURSOR causes the terminal to position at the field whose length field was set to -1.

---

### 7.4 SEND-PLAIN-TEXT (lines 162-172)

Called only when PF3 is pressed.

1. `EXEC CICS SEND TEXT FROM(WS-MESSAGE) LENGTH(...) ERASE FREEKB` — sends plain text (the thank-you message) to the terminal.
2. `EXEC CICS RETURN` — unconditional task termination. Control does not return to MAIN-PARA.

---

### 7.5 POPULATE-HEADER-INFO (lines 177-204)

Called from SEND-SIGNON-SCREEN before every screen send.

1. `MOVE FUNCTION CURRENT-DATE TO WS-CURDATE-DATA` — populates WS-DATE-TIME group from CSDAT01Y.
2. Extracts and formats date as MM/DD/YY into WS-CURDATE-MM-DD-YY.
3. Extracts and formats time as HH:MM:SS into WS-CURTIME-HH-MM-SS.
4. Moves CCDA-TITLE01, CCDA-TITLE02, WS-TRANID, WS-PGMNAME, date, time to corresponding output map fields.
5. `EXEC CICS ASSIGN APPLID(...)` fills APPLIDO.
6. `EXEC CICS ASSIGN SYSID(...)` fills SYSIDO.

---

### 7.6 READ-USER-SEC-FILE (lines 209-257)

Called from PROCESS-ENTER-KEY when no validation errors exist.

**VSAM READ (lines 211-219):**
```
EXEC CICS READ
     DATASET('USRSEC')
     INTO(SEC-USER-DATA)
     LENGTH(LENGTH OF SEC-USER-DATA)
     RIDFLD(WS-USER-ID)
     KEYLENGTH(LENGTH OF WS-USER-ID)
     RESP(WS-RESP-CD)
     RESP2(WS-REAS-CD)
```
Key is WS-USER-ID (8 bytes, upper-cased). KEYLENGTH = 8.

**Response code evaluation (lines 221-257):**

| RESP Code | Meaning | Action |
|---|---|---|
| 0 (NORMAL) | Record found | Proceed to password check |
| 13 (NOTFND) | User not found | ERR-FLG-ON, message 'User not found. Try again ...', cursor to USERIDL, SEND-SIGNON-SCREEN |
| OTHER | Unexpected VSAM error | ERR-FLG-ON, message 'Unable to verify the User ...', cursor to USERIDL, SEND-SIGNON-SCREEN |

**On RESP = 0 — Password check (lines 223-246):**
```
IF SEC-USR-PWD = WS-USER-PWD
```
Password comparison is a plain-text equality check; no hashing or encryption is applied.

- **Password matches:**
  1. Sets COMMAREA routing fields: `MOVE WS-TRANID TO CDEMO-FROM-TRANID`, `MOVE WS-PGMNAME TO CDEMO-FROM-PROGRAM`, `MOVE WS-USER-ID TO CDEMO-USER-ID`, `MOVE SEC-USR-TYPE TO CDEMO-USER-TYPE`, `MOVE ZEROS TO CDEMO-PGM-CONTEXT`.
  2. Tests `IF CDEMO-USRTYP-ADMIN` (88-level, true if CDEMO-USER-TYPE = 'A'):
     - Admin: `EXEC CICS XCTL PROGRAM('COADM01C') COMMAREA(CARDDEMO-COMMAREA)`
     - Regular user: `EXEC CICS XCTL PROGRAM('COMEN01C') COMMAREA(CARDDEMO-COMMAREA)`
  3. XCTL terminates this program; control does not return.

- **Password does not match:**
  - Message = 'Wrong Password. Try again ...', cursor to PASSWDL, PERFORM SEND-SIGNON-SCREEN.

---

## 8. Inter-Program Interactions

| Direction | Target Program | Mechanism | Condition | COMMAREA Passed |
|---|---|---|---|---|
| Outbound (success, admin) | COADM01C | EXEC CICS XCTL | SEC-USR-TYPE = 'A' and password correct | CARDDEMO-COMMAREA with USER-TYPE='A', PGM-CONTEXT=0 |
| Outbound (success, user) | COMEN01C | EXEC CICS XCTL | SEC-USR-TYPE != 'A' and password correct | CARDDEMO-COMMAREA with USER-TYPE='U', PGM-CONTEXT=0 |
| Self (pseudo-conversational loop) | COSGN00C (via CC00) | EXEC CICS RETURN TRANSID(CC00) | After every screen send | CARDDEMO-COMMAREA |
| Called by | None (transaction entry point) | CICS transaction start | CC00 transaction initiated | None on first entry |

---

## 9. File Access Summary

| File (CICS Dataset Name) | Access Type | Key | Record Layout | Paragraph |
|---|---|---|---|---|
| USRSEC | READ (keyed, direct) | WS-USER-ID (X(08)) | SEC-USER-DATA (80 bytes) | READ-USER-SEC-FILE |

The USRSEC VSAM file is a KSDS (Key Sequenced Data Set) inferred from the RIDFLD + KEYLENGTH parameters. The key is the 8-byte user ID.

---

## 10. Error Handling

| Error Condition | Detection Method | Response | User Message |
|---|---|---|---|
| User ID not entered | USERIDI = SPACES or LOW-VALUES after RECEIVE | Re-display screen with cursor on USERID | 'Please enter User ID ...' |
| Password not entered | PASSWDI = SPACES or LOW-VALUES after RECEIVE | Re-display screen with cursor on PASSWD | 'Please enter Password ...' |
| User not found in USRSEC | RESP = 13 (DFHRESP NOTFND) | Re-display screen with cursor on USERID | 'User not found. Try again ...' |
| Wrong password | SEC-USR-PWD != WS-USER-PWD | Re-display screen with cursor on PASSWD | 'Wrong Password. Try again ...' |
| VSAM I/O error | RESP not 0 or 13 | Re-display screen with cursor on USERID | 'Unable to verify the User ...' |
| Invalid AID key (not Enter/PF3) | EVALUATE EIBAID WHEN OTHER | Re-display screen with error message | CCDA-MSG-INVALID-KEY value |
| PF3 pressed | EIBAID = DFHPF3 | Send thank-you text, RETURN (terminate) | CCDA-MSG-THANK-YOU value |

No `EXEC CICS HANDLE CONDITION` or `EXEC CICS HANDLE AID` is established. All error handling is via RESP/RESP2 testing and manual AID evaluation.

---

## 11. Transaction Flow Participation

```
[Terminal] --CC00--> COSGN00C
                        |
                  [First Entry: EIBCALEN=0]
                        |
                  SEND COSGN0A (sign-on screen)
                        |
                  RETURN TRANSID(CC00)
                        |
                  [User enters credentials, presses Enter]
                        |
                  [Re-entry: EIBCALEN>0, EIBAID=DFHENTER]
                        |
                  RECEIVE COSGN0A
                        |
                  READ USRSEC (by user ID)
                        |
               [Auth OK, type='A'] --> XCTL COADM01C (COMMAREA: type='A')
               [Auth OK, type='U'] --> XCTL COMEN01C (COMMAREA: type='U')
               [Auth fail]         --> SEND error screen, RETURN TRANSID(CC00)
                        |
               [PF3 pressed]       --> SEND TEXT "thank you", RETURN (end)
```

---

## 12. Business Rules Catalog

| Rule ID | Rule Description | Source Location |
|---|---|---|
| BR-SGN-001 | User ID and password are mandatory fields; blank entries are rejected before any file access | PROCESS-ENTER-KEY, lines 118-130 |
| BR-SGN-002 | User ID and password are converted to upper-case before validation | PROCESS-ENTER-KEY, lines 132-136 |
| BR-SGN-003 | Passwords are stored and compared as plain-text (no hashing) | READ-USER-SEC-FILE, line 223 |
| BR-SGN-004 | User type 'A' routes to Admin Menu (COADM01C); any other type routes to Main Menu (COMEN01C) | READ-USER-SEC-FILE, lines 230-239 |
| BR-SGN-005 | CDEMO-PGM-CONTEXT is set to ZEROS (CDEMO-PGM-ENTER) before XCTL, signalling the receiving menu program that this is first entry | READ-USER-SEC-FILE, line 228 |
| BR-SGN-006 | PF3 at the sign-on screen terminates the session with a thank-you message | MAIN-PARA, lines 89-91 |

---

## 13. Open Questions and Gaps

1. **No HANDLE CONDITION for MAPFAIL**: If the terminal sends no changed fields (e.g., user presses Enter with no input at all on a fresh screen), RECEIVE MAP may raise a MAPFAIL condition. There is no EXEC CICS HANDLE CONDITION MAPFAIL established, so CICS would abend the task. Confidence: HIGH (no HANDLE CONDITION visible in source).
2. **USRSEC file definition**: The physical dataset name and DCB attributes for the USRSEC VSAM KSDS are not visible in the COBOL source; they would be defined in the CICS CSD (DFHCSDUP) or SIT. These are unavailable for inspection.
3. **Password security**: Passwords are stored and compared in plain-text (SEC-USR-PWD comparison at line 223). This is a known limitation of the reference implementation.
4. **CDEMO-USER-ID population**: WS-USER-ID is moved to CDEMO-USER-ID at line 134 (inside PROCESS-ENTER-KEY, before ERR-FLG check) even if validation fails. This means CDEMO-USER-ID may hold a partial value in an error scenario, though it is never propagated via XCTL in error cases.
