# Technical Specification: COUSR02C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COUSR02C                                             |
| Source File      | app/cbl/COUSR02C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CU02 (WS-TRANID, line 37)                            |
| Function         | Update user screen (admin function). Allows an administrator to look up a user by user ID, view and modify their first name, last name, password, and user type, and save changes to the USRSEC VSAM file. ENTER looks up the user; PF5 saves changes (only if fields differ from current values); PF3 attempts to save and returns to calling program; PF12 returns to COADM01C without save. Pre-populates user ID from CDEMO-CU02-USR-SELECTED on first entry. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CU02 and COMMAREA)

SET ERR-FLG-OFF; SET USR-MODIFIED-NO; MOVE SPACES TO WS-MESSAGE

IF EIBCALEN = 0:
    MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM
    PERFORM RETURN-TO-PREV-SCREEN

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO COUSR2AO; MOVE -1 TO USRIDINL
        IF CDEMO-CU02-USR-SELECTED NOT = SPACES/LOW-VALUES:
            MOVE CDEMO-CU02-USR-SELECTED TO USRIDINI
            PERFORM PROCESS-ENTER-KEY (auto-lookup)
        PERFORM SEND-USRUPD-SCREEN
    ELSE:
        PERFORM RECEIVE-USRUPD-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER:  PERFORM PROCESS-ENTER-KEY (lookup user)
            WHEN DFHPF3:    PERFORM UPDATE-USER-INFO; XCTL to CDEMO-FROM-PROGRAM
            WHEN DFHPF4:    PERFORM CLEAR-CURRENT-SCREEN
            WHEN DFHPF5:    PERFORM UPDATE-USER-INFO (save without exit)
            WHEN DFHPF12:   MOVE 'COADM01C' TO CDEMO-TO-PROGRAM; XCTL
            WHEN OTHER:     ERR-FLG-ON; CCDA-MSG-INVALID-KEY; re-send

EXEC CICS RETURN TRANSID('CU02') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| MAIN-PARA              | 82–138    | Main entry: EIBCALEN check; first-entry auto-lookup; reenter AID dispatch; CICS RETURN |
| PROCESS-ENTER-KEY      | 143–164   | Validate USRIDINI non-blank; clear FNAME/LNAME/PWD/TYPE fields; MOVE USRIDINI to SEC-USR-ID; PERFORM READ-USER-SEC-FILE |
| UPDATE-USER-INFO       | 177–245   | Validate all five fields non-blank; READ-USER-SEC-FILE; compare each field to existing; SET USR-MODIFIED-YES if different; if USR-MODIFIED-YES: PERFORM UPDATE-USER-SEC-FILE; else 'Please modify to update...' in DFHRED |
| RETURN-TO-PREV-SCREEN  | 250–261   | Default CDEMO-TO-PROGRAM='COSGN00C' if blank; EXEC CICS XCTL |
| SEND-USRUPD-SCREEN     | 266–278   | POPULATE-HEADER-INFO; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('COUSR2A') MAPSET('COUSR02') FROM(COUSR2AO) ERASE CURSOR |
| RECEIVE-USRUPD-SCREEN  | 283–291   | CICS RECEIVE MAP('COUSR2A') MAPSET('COUSR02') INTO(COUSR2AI) RESP RESP2 |
| POPULATE-HEADER-INFO   | 296–315   | Fill header fields |
| READ-USER-SEC-FILE     | 320–353   | CICS READ DATASET(USRSEC) UPDATE; NORMAL → 'Press PF5 key to save...' in DFHNEUTR + SEND; NOTFND → 'User ID NOT found...'; OTHER → DISPLAY + error message |
| UPDATE-USER-SEC-FILE   | 358–390   | CICS REWRITE DATASET(USRSEC) FROM(SEC-USER-DATA); NORMAL → success message in DFHGREEN + SEND; NOTFND → error; OTHER → DISPLAY + error |
| CLEAR-CURRENT-SCREEN   | 395–398   | PERFORM INITIALIZE-ALL-FIELDS; PERFORM SEND-USRUPD-SCREEN |
| INITIALIZE-ALL-FIELDS  | 403–411   | MOVE -1 TO USRIDINL; MOVE SPACES to USRIDINI, FNAMEI, LNAMEI, PASSWDI, USRTYPEI, WS-MESSAGE |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 49) | CARDDEMO-COMMAREA standard fields |
| COUSR02  | WORKING-STORAGE (line 60)  | BMS mapset copybook: COUSR2AI (input map), COUSR2AO (output map); contains USRIDINI/O (user ID search), FNAMEI/O, LNAMEI/O, PASSWDI/O, USRTYPEI/O, ERRMSGO, ERRMSGC, cursor length fields, header fields |
| COTTL01Y  | WORKING-STORAGE (line 62) | Screen title constants |
| CSDAT01Y  | WORKING-STORAGE (line 63) | Current date/time |
| CSMSG01Y  | WORKING-STORAGE (line 64) | Common messages |
| CSUSR01Y  | WORKING-STORAGE (line 65) | SEC-USER-DATA group (USRSEC record layout) |
| DFHAID    | WORKING-STORAGE (line 67) | EIBAID constants: DFHENTER, DFHPF3, DFHPF4, DFHPF5, DFHPF12 |
| DFHBMSCA  | WORKING-STORAGE (line 68) | BMS attribute bytes: DFHGREEN, DFHRED, DFHNEUTR |

### COMMAREA Extension (inline after COPY COCOM01Y, lines 50–58)

| Field                    | PIC       | Purpose |
|--------------------------|-----------|---------|
| CDEMO-CU02-INFO          | Group     | CU02-specific commarea extension |
| CDEMO-CU02-USRID-FIRST   | X(08)     | (Informational — not used for browse) |
| CDEMO-CU02-USRID-LAST    | X(08)     | (Informational) |
| CDEMO-CU02-PAGE-NUM      | 9(08)     | (Informational) |
| CDEMO-CU02-NEXT-PAGE-FLG | X(01)     | (Informational); 88 NEXT-PAGE-YES/NO |
| CDEMO-CU02-USR-SEL-FLG   | X(01)     | Selection flag from COUSR00C |
| CDEMO-CU02-USR-SELECTED  | X(08)     | User ID selected in COUSR00C; pre-populates USRIDINI on first entry |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| WS-PGMNAME           | X(08) = 'COUSR02C' | Program name for header |
| WS-TRANID            | X(04) = 'CU02' | Transaction ID |
| WS-MESSAGE           | X(80)     | User-visible message |
| WS-USRSEC-FILE       | X(08) = 'USRSEC  ' | CICS file name |
| WS-ERR-FLG           | X(01)     | Error flag |
| WS-USR-MODIFIED      | X(01)     | 'Y'=at least one field changed; 88 USR-MODIFIED-YES/USR-MODIFIED-NO |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS RETURN TRANSID('CU02') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA (line 135) | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | RETURN-TO-PREV-SCREEN (line 258) | Return to calling program |
| EXEC CICS SEND MAP('COUSR2A') MAPSET('COUSR02') FROM(COUSR2AO) ERASE CURSOR | SEND-USRUPD-SCREEN (line 272) | Display update screen with cursor |
| EXEC CICS RECEIVE MAP('COUSR2A') MAPSET('COUSR02') INTO(COUSR2AI) RESP RESP2 | RECEIVE-USRUPD-SCREEN (line 285) | Receive input |
| EXEC CICS READ DATASET(WS-USRSEC-FILE) INTO(SEC-USER-DATA) RIDFLD(SEC-USR-ID) UPDATE RESP RESP2 | READ-USER-SEC-FILE (line 322) | Read user record with update lock |
| EXEC CICS REWRITE DATASET(WS-USRSEC-FILE) FROM(SEC-USER-DATA) RESP RESP2 | UPDATE-USER-SEC-FILE (line 360) | Rewrite updated user record |

**Note on READ UPDATE**: READ-USER-SEC-FILE uses `UPDATE` to acquire an exclusive lock. The lock is held until REWRITE is issued (UPDATE-USER-SEC-FILE) or the task ends. If PROCESS-ENTER-KEY triggers READ-USER-SEC-FILE but no PF5/PF3 save occurs, the lock is held for the remainder of the pseudo-conversational interaction. Since CICS RETURN releases all locks, the lock duration is bounded to one interaction cycle.

---

## 5. File/Dataset Access

| File Name | CICS File | Access Type | Key              | Purpose |
|-----------|-----------|-------------|------------------|---------|
| USRSEC    | USRSEC    | READ UPDATE | SEC-USR-ID X(08) | Read existing user record with lock (for display and update) |
| USRSEC    | USRSEC    | REWRITE     | (implied by prior UPDATE) | Write modified user record back |

**Update logic**: READ-USER-SEC-FILE is called twice in the UPDATE-USER-INFO flow: once to re-read current values for comparison, then if modified: UPDATE-USER-SEC-FILE REWRITEs. The field-level comparison (lines 219–234) detects which fields changed and sets USR-MODIFIED-YES. If no fields differ, REWRITE is not performed.

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COUSR02    | COUSR2A | CU02        |

**Key Screen Fields:**

| Field      | Direction | Description |
|------------|-----------|-------------|
| USRIDINI   | Input     | User ID to look up (read-only after lookup — operator can change to look up different user) |
| FNAMEI     | Input/Output | First name — displayed after lookup; editable |
| LNAMEI     | Input/Output | Last name — displayed after lookup; editable |
| PASSWDI    | Input/Output | Password — displayed after lookup; editable (plain text) |
| USRTYPEI   | Input/Output | User type — displayed after lookup; editable |
| ERRMSGO    | Output    | WS-MESSAGE; DFHNEUTR for 'save' prompt; DFHRED for 'please modify' warning; DFHGREEN for success |
| ERRMSGC    | Output    | Color attribute of error message |
| TITLE01O–CURTIMEO | Output | Standard header fields |

**Navigation:**
- ENTER: look up user by USRIDINI; display current field values
- PF3: validate, save if modified, XCTL to CDEMO-FROM-PROGRAM
- PF4: clear all fields
- PF5: validate and save changes (stay on screen after save)
- PF12: XCTL to COADM01C (no save attempt)
- Other keys: CCDA-MSG-INVALID-KEY

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| CDEMO-FROM-PROGRAM (COUSR00C or COADM01C) | CICS XCTL | PF3: UPDATE-USER-INFO attempted, then XCTL |
| COADM01C   | CICS XCTL   | PF12 pressed (hardcoded at line 125) |
| COSGN00C   | CICS XCTL   | EIBCALEN=0 or CDEMO-TO-PROGRAM blank |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C |
| USRIDINI blank | ERR-FLG-ON; 'User ID can NOT be empty...'; cursor on USRIDINL |
| READ NOTFND | ERR-FLG-ON; 'User ID NOT found...'; cursor on USRIDINL |
| READ OTHER | DISPLAY RESP/RESP2 (to sysprint); ERR-FLG-ON; 'Unable to lookup User...'; cursor on FNAMEL |
| FNAMEI blank (UPDATE-USER-INFO) | ERR-FLG-ON; 'First Name can NOT be empty...' |
| LNAMEI blank | ERR-FLG-ON; 'Last Name can NOT be empty...' |
| PASSWDI blank | ERR-FLG-ON; 'Password can NOT be empty...' |
| USRTYPEI blank | ERR-FLG-ON; 'User Type can NOT be empty...' |
| No fields modified | USR-MODIFIED-NO; 'Please modify to update...' in DFHRED; no REWRITE |
| REWRITE NOTFND | ERR-FLG-ON; 'User ID NOT found...' |
| REWRITE OTHER | DISPLAY RESP/RESP2; ERR-FLG-ON; 'Unable to Update User...' |
| Invalid AID key | ERR-FLG-ON; CCDA-MSG-INVALID-KEY |

---

## 9. Business Rules

1. **Admin-only function**: COUSR02C is reached from COUSR00C (selection 'U') or COADM01C (option 3). PF12 always returns to COADM01C.
2. **Two-step workflow**: ENTER first looks up and displays the user record. PF5 (or PF3) then saves changes. This prevents accidental overwrites.
3. **Field-level change detection**: UPDATE-USER-INFO compares each editable field (FNAME, LNAME, PWD, TYPE) against the current value from READ-USER-SEC-FILE. Only if at least one field differs is REWRITE performed. If no changes: 'Please modify to update...' in red.
4. **User ID not editable**: USRIDINI is the lookup key and cannot be changed in this screen. To change a user ID, the admin would need to delete and re-add.
5. **PF3 save-and-exit**: PF3 calls UPDATE-USER-INFO (which saves if changed) and then XCTLs to CDEMO-FROM-PROGRAM. This is a convenience to save and navigate in one keystroke.
6. **PF12 exit without save**: PF12 always goes to COADM01C immediately without attempting to save.
7. **Pre-population from COUSR00C**: On first entry, if CDEMO-CU02-USR-SELECTED is set, PROCESS-ENTER-KEY is called automatically to look up and display the user without requiring the operator to re-enter the user ID.
8. **DISPLAY statements**: READ-USER-SEC-FILE (line 347) and UPDATE-USER-SEC-FILE (line 384) contain `DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD` on the OTHER error path.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COUSR2A) | USRIDINI (lookup key); FNAMEI, LNAMEI, PASSWDI, USRTYPEI (editable fields) |
| COMMAREA  | CDEMO-CU02-USR-SELECTED (pre-selected user ID from COUSR00C) |
| USRSEC VSAM | Current user record read for display and comparison |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COUSR2A) | User detail form populated from USRSEC; success/error messages |
| USRSEC VSAM | Updated SEC-USER-DATA record via REWRITE (only if fields changed) |

---

## 11. Key Variables and Their Purpose

| Variable                  | Purpose |
|---------------------------|---------|
| USRIDINI                  | User ID lookup key; RIDFLD for READ UPDATE |
| CDEMO-CU02-USR-SELECTED   | User ID from COUSR00C selection; auto-populates USRIDINI on first entry |
| WS-USR-MODIFIED           | Tracks whether any field changed; gates REWRITE in UPDATE-USER-INFO |
| SEC-USER-DATA             | Full USRSEC record; read into for comparison, modified, then REWRITten |
| ERRMSGC                   | Color attribute: DFHNEUTR (prompt), DFHRED (no-change warning), DFHGREEN (success) |
