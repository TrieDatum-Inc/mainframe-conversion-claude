# Technical Specification: COUSR01C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COUSR01C                                             |
| Source File      | app/cbl/COUSR01C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CU01 (WS-TRANID, line 37)                            |
| Function         | Add new user screen (admin function). Allows an administrator to enter a new user's first name, last name, user ID, password, and user type, then writes the new record to the USRSEC VSAM KSDS file. Validates that all five fields are non-blank. Handles DUPKEY/DUPREC to detect duplicate user IDs. PF3 returns to COADM01C. PF4 clears the screen. After successful add, all fields are cleared to allow adding another user. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CU01 and COMMAREA)

SET ERR-FLG-OFF; MOVE SPACES TO WS-MESSAGE

IF EIBCALEN = 0:
    MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM
    PERFORM RETURN-TO-PREV-SCREEN

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO COUSR1AO
        MOVE -1 TO FNAMEL OF COUSR1AI (cursor on first name)
        PERFORM SEND-USRADD-SCREEN
    ELSE:
        PERFORM RECEIVE-USRADD-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER:  PERFORM PROCESS-ENTER-KEY
            WHEN DFHPF3:    MOVE 'COADM01C' TO CDEMO-TO-PROGRAM
                            PERFORM RETURN-TO-PREV-SCREEN
            WHEN DFHPF4:    PERFORM CLEAR-CURRENT-SCREEN
            WHEN OTHER:     Set ERR-FLG-ON; MOVE -1 TO FNAMEL; CCDA-MSG-INVALID-KEY; SEND-USRADD-SCREEN

EXEC CICS RETURN TRANSID('CU01') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph            | Lines     | Description |
|----------------------|-----------|-------------|
| MAIN-PARA            | 71–110    | Main entry: EIBCALEN check; first/reenter dispatch; AID evaluate; CICS RETURN |
| PROCESS-ENTER-KEY    | 115–160   | EVALUATE TRUE: validate FNAMEI, LNAMEI, USERIDI, PASSWDI, USRTYPEI all non-blank (in that order); on any blank field: ERR-FLG-ON + message + cursor position + SEND; if no error: populate SEC-USER-DATA from screen; PERFORM WRITE-USER-SEC-FILE |
| RETURN-TO-PREV-SCREEN | 165–178  | Default CDEMO-TO-PROGRAM='COSGN00C' if blank; set CDEMO-FROM-TRANID, CDEMO-FROM-PROGRAM; EXEC CICS XCTL |
| SEND-USRADD-SCREEN   | 184–196   | POPULATE-HEADER-INFO; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('COUSR1A') MAPSET('COUSR01') FROM(COUSR1AO) ERASE CURSOR |
| RECEIVE-USRADD-SCREEN | 201–209  | CICS RECEIVE MAP('COUSR1A') MAPSET('COUSR01') INTO(COUSR1AI) RESP RESP2 |
| POPULATE-HEADER-INFO  | 214–233  | Fill TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO |
| WRITE-USER-SEC-FILE   | 238–274  | CICS WRITE DATASET(USRSEC) FROM(SEC-USER-DATA) RIDFLD(SEC-USR-ID); evaluate RESP: NORMAL → INITIALIZE-ALL-FIELDS + success message in DFHGREEN; DUPKEY/DUPREC → 'User ID already exist...'; OTHER → 'Unable to Add User...' |
| CLEAR-CURRENT-SCREEN  | 279–282  | PERFORM INITIALIZE-ALL-FIELDS; PERFORM SEND-USRADD-SCREEN |
| INITIALIZE-ALL-FIELDS | 287–295  | MOVE -1 TO FNAMEL; MOVE SPACES to USERIDI, FNAMEI, LNAMEI, PASSWDI, USRTYPEI, WS-MESSAGE |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 46) | CARDDEMO-COMMAREA: standard commarea fields |
| COUSR01  | WORKING-STORAGE (line 48)  | BMS mapset copybook: COUSR1AI (input map), COUSR1AO (output map); contains FNAMEI/O, LNAMEI/O, USERIDI/O (user ID input), PASSWDI/O, USRTYPEI/O, ERRMSGO, ERRMSGC, TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO, and cursor length fields (FNAMEL, LNAMEL, USERIDL, PASSWDL, USRTYPEL) |
| COTTL01Y  | WORKING-STORAGE (line 50) | Screen title constants |
| CSDAT01Y  | WORKING-STORAGE (line 51) | Current date/time |
| CSMSG01Y  | WORKING-STORAGE (line 52) | Common messages: CCDA-MSG-INVALID-KEY |
| CSUSR01Y  | WORKING-STORAGE (line 53) | SEC-USER-DATA group: SEC-USR-ID X(08), SEC-USR-PWD X(08), SEC-USR-FNAME X(20), SEC-USR-LNAME X(20), SEC-USR-TYPE X(01), SEC-USR-FILLER X(23) |
| DFHAID    | WORKING-STORAGE (line 55) | EIBAID constants: DFHENTER, DFHPF3, DFHPF4 |
| DFHBMSCA  | WORKING-STORAGE (line 56) | BMS attribute bytes: DFHGREEN |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| WS-PGMNAME           | X(08) = 'COUSR01C' | Program name for header |
| WS-TRANID            | X(04) = 'CU01' | Transaction ID |
| WS-MESSAGE           | X(80)     | User-visible message |
| WS-USRSEC-FILE       | X(08) = 'USRSEC  ' | CICS file name |
| WS-ERR-FLG           | X(01)     | Error flag |
| WS-RESP-CD / WS-REAS-CD | S9(09) COMP | CICS response codes |

**No COMMAREA extension**: COUSR01C does not append CDEMO-CU01-INFO inline after COPY COCOM01Y. It uses only the standard CARDDEMO-COMMAREA fields.

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS RETURN TRANSID('CU01') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA (line 107) | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | RETURN-TO-PREV-SCREEN (line 175) | Return to COADM01C |
| EXEC CICS SEND MAP('COUSR1A') MAPSET('COUSR01') FROM(COUSR1AO) ERASE CURSOR | SEND-USRADD-SCREEN (line 190) | Display user add screen with cursor positioning |
| EXEC CICS RECEIVE MAP('COUSR1A') MAPSET('COUSR01') INTO(COUSR1AI) RESP RESP2 | RECEIVE-USRADD-SCREEN (line 203) | Receive all input fields |
| EXEC CICS WRITE DATASET(WS-USRSEC-FILE) FROM(SEC-USER-DATA) RIDFLD(SEC-USR-ID) KEYLENGTH RESP RESP2 | WRITE-USER-SEC-FILE (line 240) | Add new user record to USRSEC |

---

## 5. File/Dataset Access

| File Name | CICS File | Access Type | Key             | Purpose |
|-----------|-----------|-------------|-----------------|---------|
| USRSEC    | USRSEC    | WRITE       | SEC-USR-ID X(08) | Add new user security record |

**WRITE behavior:**
- RESP=NORMAL: user added; INITIALIZE-ALL-FIELDS; success message in DFHGREEN "User [ID] has been added ..."
- RESP=DUPKEY or DUPREC: 'User ID already exist...'; cursor on USERIDL; re-send map
- RESP=OTHER: 'Unable to Add User...'; DISPLAY RESP/RESP2 (commented out in source); cursor on FNAMEL

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COUSR01    | COUSR1A | CU01        |

**Key Screen Fields:**

| Field      | Direction | Description |
|------------|-----------|-------------|
| FNAMEI     | Input     | First name (required, non-blank) |
| LNAMEI     | Input     | Last name (required, non-blank) |
| USERIDI    | Input     | User ID (required, non-blank; becomes VSAM key) |
| PASSWDI    | Input     | Password (required, non-blank; plain text) |
| USRTYPEI   | Input     | User type (required, non-blank; 'A'=Admin, 'R'=Regular) |
| ERRMSGO    | Output    | WS-MESSAGE: error or status message |
| ERRMSGC    | Output    | DFHGREEN on success |
| TITLE01O–CURTIMEO | Output | Standard header fields |

**Cursor positioning**: On first entry and after errors, FNAMEL (or the specific invalid field's length field) is set to -1 to position the cursor at the appropriate input field.

**Navigation:**
- ENTER: validate all fields and add user
- PF3: return to COADM01C (hardcoded at line 94)
- PF4: clear all screen fields
- Other keys: CCDA-MSG-INVALID-KEY; cursor on FNAMEL

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| COADM01C   | CICS XCTL   | PF3 pressed (CDEMO-TO-PROGRAM hardcoded to 'COADM01C' at line 94) |
| COSGN00C   | CICS XCTL   | EIBCALEN=0 (default fallback) |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C |
| FNAMEI blank/LOW-VALUES | ERR-FLG-ON; 'First Name can NOT be empty...'; cursor on FNAMEL |
| LNAMEI blank/LOW-VALUES | ERR-FLG-ON; 'Last Name can NOT be empty...'; cursor on LNAMEL |
| USERIDI blank/LOW-VALUES | ERR-FLG-ON; 'User ID can NOT be empty...'; cursor on USERIDL |
| PASSWDI blank/LOW-VALUES | ERR-FLG-ON; 'Password can NOT be empty...'; cursor on PASSWDL |
| USRTYPEI blank/LOW-VALUES | ERR-FLG-ON; 'User Type can NOT be empty...'; cursor on USRTYPEL |
| WRITE RESP=DUPKEY/DUPREC | ERR-FLG-ON; 'User ID already exist...'; cursor on USERIDL |
| WRITE RESP=OTHER | ERR-FLG-ON; 'Unable to Add User...'; cursor on FNAMEL |
| Invalid AID key | ERR-FLG-ON; CCDA-MSG-INVALID-KEY; cursor on FNAMEL |

**Validation order**: FNAMEI → LNAMEI → USERIDI → PASSWDI → USRTYPEI. First failure stops further validation (EVALUATE TRUE short-circuits after first WHEN match).

---

## 9. Business Rules

1. **Admin-only function**: COUSR01C is reachable from COADM01C only (option 2 in admin menu). PF3 always returns to COADM01C.
2. **All five fields required**: No optional fields. FNAMEI, LNAMEI, USERIDI, PASSWDI, and USRTYPEI must all be non-blank before WRITE is attempted.
3. **Plain-text password storage**: PASSWDI is stored as-is in SEC-USR-PWD with no hashing or encryption.
4. **Duplicate key detection**: CICS WRITE returns DUPKEY or DUPREC if SEC-USR-ID already exists in USRSEC. Both conditions produce the same 'User ID already exist...' message.
5. **Screen reset after success**: INITIALIZE-ALL-FIELDS clears all input fields after a successful WRITE, allowing the administrator to immediately add another user.
6. **No COMMAREA extension**: Unlike COUSR02C and COUSR03C, COUSR01C has no CDEMO-CU01-INFO appended to the commarea. It uses only the base CARDDEMO-COMMAREA.
7. **CURSOR option on SEND**: SEND-USRADD-SCREEN uses CURSOR option, directing the terminal cursor to the field whose length field (-1) was most recently set.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COUSR1A) | FNAMEI, LNAMEI, USERIDI, PASSWDI, USRTYPEI — all required |
| COMMAREA  | CARDDEMO-COMMAREA (standard fields; no CT01-INFO extension) |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COUSR1A) | User add form; success message in DFHGREEN or error messages |
| USRSEC VSAM | New SEC-USER-DATA record written with SEC-USR-ID as key |

---

## 11. Key Variables and Their Purpose

| Variable       | Purpose |
|----------------|---------|
| USERIDI        | New user ID entered on screen; becomes SEC-USR-ID (VSAM key) |
| FNAMEI/LNAMEI  | First/last name; moved to SEC-USR-FNAME/LNAME |
| PASSWDI        | Password; moved to SEC-USR-PWD (plain text) |
| USRTYPEI       | User type; moved to SEC-USR-TYPE ('A' or 'R') |
| SEC-USER-DATA  | Group from CSUSR01Y; the record written to USRSEC |
| WS-ERR-FLG     | Error state; prevents WRITE when validation fails |
