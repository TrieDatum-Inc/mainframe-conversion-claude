# Technical Specification: COUSR03C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COUSR03C                                             |
| Source File      | app/cbl/COUSR03C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CU03 (WS-TRANID, line 37)                            |
| Function         | Delete user screen (admin function). Allows an administrator to look up a user by user ID, review their details (first name, last name, user type), and confirm deletion by pressing PF5. ENTER looks up the user; PF5 deletes the record from USRSEC; PF3 returns to calling program without delete; PF12 returns to COADM01C without delete. Pre-populates user ID from CDEMO-CU03-USR-SELECTED on first entry. Password is not displayed. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CU03 and COMMAREA)

SET ERR-FLG-OFF; SET USR-MODIFIED-NO; MOVE SPACES TO WS-MESSAGE

IF EIBCALEN = 0:
    MOVE 'COSGN00C' TO CDEMO-TO-PROGRAM
    PERFORM RETURN-TO-PREV-SCREEN

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO COUSR3AO; MOVE -1 TO USRIDINL
        IF CDEMO-CU03-USR-SELECTED NOT = SPACES/LOW-VALUES:
            MOVE CDEMO-CU03-USR-SELECTED TO USRIDINI
            PERFORM PROCESS-ENTER-KEY (auto-lookup)
        PERFORM SEND-USRDEL-SCREEN
    ELSE:
        PERFORM RECEIVE-USRDEL-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER:  PERFORM PROCESS-ENTER-KEY (lookup)
            WHEN DFHPF3:    CDEMO-TO-PROGRAM = CDEMO-FROM-PROGRAM; XCTL
            WHEN DFHPF4:    PERFORM CLEAR-CURRENT-SCREEN
            WHEN DFHPF5:    PERFORM DELETE-USER-INFO (delete and stay)
            WHEN DFHPF12:   MOVE 'COADM01C' TO CDEMO-TO-PROGRAM; XCTL
            WHEN OTHER:     ERR-FLG-ON; CCDA-MSG-INVALID-KEY; re-send

EXEC CICS RETURN TRANSID('CU03') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| MAIN-PARA              | 82–137    | Main entry: EIBCALEN check; first-entry auto-lookup; reenter AID dispatch; CICS RETURN |
| PROCESS-ENTER-KEY      | 142–169   | Validate USRIDINI non-blank; clear FNAME/LNAME/TYPE fields; MOVE USRIDINI to SEC-USR-ID; PERFORM READ-USER-SEC-FILE; on success: populate FNAMEI, LNAMEI, USRTYPEI from SEC-USER-DATA; SEND-USRDEL-SCREEN |
| DELETE-USER-INFO       | 174–192   | Validate USRIDINI non-blank; PERFORM READ-USER-SEC-FILE; PERFORM DELETE-USER-SEC-FILE |
| RETURN-TO-PREV-SCREEN  | 197–208   | Default CDEMO-TO-PROGRAM='COSGN00C' if blank; EXEC CICS XCTL |
| SEND-USRDEL-SCREEN     | 213–225   | POPULATE-HEADER-INFO; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('COUSR3A') MAPSET('COUSR03') FROM(COUSR3AO) ERASE CURSOR |
| RECEIVE-USRDEL-SCREEN  | 230–238   | CICS RECEIVE MAP('COUSR3A') MAPSET('COUSR03') INTO(COUSR3AI) RESP RESP2 |
| POPULATE-HEADER-INFO   | 243–262   | Fill header fields |
| READ-USER-SEC-FILE     | 267–300   | CICS READ DATASET(USRSEC) UPDATE; NORMAL → 'Press PF5 key to delete...' in DFHNEUTR + SEND; NOTFND → 'User ID NOT found...'; OTHER → DISPLAY + error |
| DELETE-USER-SEC-FILE   | 305–336   | CICS DELETE DATASET(USRSEC); NORMAL → INITIALIZE-ALL-FIELDS + success message in DFHGREEN; NOTFND → error; OTHER → DISPLAY + 'Unable to Update User...' |
| CLEAR-CURRENT-SCREEN   | 341–344   | PERFORM INITIALIZE-ALL-FIELDS; PERFORM SEND-USRDEL-SCREEN |
| INITIALIZE-ALL-FIELDS  | 349–356   | MOVE -1 TO USRIDINL; MOVE SPACES to USRIDINI, FNAMEI, LNAMEI, USRTYPEI, WS-MESSAGE |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 49) | CARDDEMO-COMMAREA standard fields |
| COUSR03  | WORKING-STORAGE (line 60)  | BMS mapset copybook: COUSR3AI (input map), COUSR3AO (output map); contains USRIDINI/O (user ID search), FNAMEI/O, LNAMEI/O, USRTYPEI/O (no PASSWDI — password not shown), ERRMSGO, ERRMSGC, cursor length fields, header fields |
| COTTL01Y  | WORKING-STORAGE (line 62) | Screen title constants |
| CSDAT01Y  | WORKING-STORAGE (line 63) | Current date/time |
| CSMSG01Y  | WORKING-STORAGE (line 64) | Common messages |
| CSUSR01Y  | WORKING-STORAGE (line 65) | SEC-USER-DATA group (USRSEC record layout) |
| DFHAID    | WORKING-STORAGE (line 67) | EIBAID constants: DFHENTER, DFHPF3, DFHPF4, DFHPF5, DFHPF12 |
| DFHBMSCA  | WORKING-STORAGE (line 68) | BMS attribute bytes: DFHGREEN, DFHNEUTR |

### COMMAREA Extension (inline after COPY COCOM01Y, lines 50–58)

| Field                    | PIC       | Purpose |
|--------------------------|-----------|---------|
| CDEMO-CU03-INFO          | Group     | CU03-specific commarea extension |
| CDEMO-CU03-USRID-FIRST   | X(08)     | (Informational) |
| CDEMO-CU03-USRID-LAST    | X(08)     | (Informational) |
| CDEMO-CU03-PAGE-NUM      | 9(08)     | (Informational) |
| CDEMO-CU03-NEXT-PAGE-FLG | X(01)     | 88 NEXT-PAGE-YES/NO |
| CDEMO-CU03-USR-SEL-FLG   | X(01)     | Selection flag |
| CDEMO-CU03-USR-SELECTED  | X(08)     | User ID selected in COUSR00C; pre-populates USRIDINI on first entry |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| WS-PGMNAME           | X(08) = 'COUSR03C' | Program name for header |
| WS-TRANID            | X(04) = 'CU03' | Transaction ID |
| WS-MESSAGE           | X(80)     | User-visible message |
| WS-USRSEC-FILE       | X(08) = 'USRSEC  ' | CICS file name |
| WS-ERR-FLG           | X(01)     | Error flag |
| WS-USR-MODIFIED      | X(01)     | Present in WS (lines 45–47) but not used in delete logic; carried over from COUSR02C template |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS RETURN TRANSID('CU03') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA (line 134) | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | RETURN-TO-PREV-SCREEN (line 205) | Return to calling program |
| EXEC CICS SEND MAP('COUSR3A') MAPSET('COUSR03') FROM(COUSR3AO) ERASE CURSOR | SEND-USRDEL-SCREEN (line 219) | Display delete confirmation screen |
| EXEC CICS RECEIVE MAP('COUSR3A') MAPSET('COUSR03') INTO(COUSR3AI) RESP RESP2 | RECEIVE-USRDEL-SCREEN (line 232) | Receive user ID input |
| EXEC CICS READ DATASET(WS-USRSEC-FILE) INTO(SEC-USER-DATA) RIDFLD(SEC-USR-ID) UPDATE RESP RESP2 | READ-USER-SEC-FILE (line 269) | Read user record with update lock (required before DELETE) |
| EXEC CICS DELETE DATASET(WS-USRSEC-FILE) RESP RESP2 | DELETE-USER-SEC-FILE (line 307) | Delete the locked user record from USRSEC |

**Note on READ UPDATE before DELETE**: The CICS READ with UPDATE acquires the exclusive record lock required for a subsequent DELETE. The DELETE-USER-SEC-FILE paragraph issues `EXEC CICS DELETE DATASET(WS-USRSEC-FILE)` without a RIDFLD — this is valid because the record is already held via the UPDATE lock from the preceding READ.

---

## 5. File/Dataset Access

| File Name | CICS File | Access Type | Key              | Purpose |
|-----------|-----------|-------------|------------------|---------|
| USRSEC    | USRSEC    | READ UPDATE | SEC-USR-ID X(08) | Read user record and acquire exclusive lock for subsequent DELETE |
| USRSEC    | USRSEC    | DELETE      | (implied by prior UPDATE lock) | Delete the locked user record |

**Two-READ pattern in DELETE-USER-INFO**: DELETE-USER-INFO calls READ-USER-SEC-FILE before DELETE-USER-SEC-FILE. This means the record is read (and locked) once when the operator presses ENTER (PROCESS-ENTER-KEY → READ-USER-SEC-FILE), but the CICS RETURN at end of task releases that lock. When PF5 is pressed, DELETE-USER-INFO calls READ-USER-SEC-FILE again to reacquire the lock, then immediately deletes.

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COUSR03    | COUSR3A | CU03        |

**Key Screen Fields:**

| Field      | Direction | Description |
|------------|-----------|-------------|
| USRIDINI   | Input     | User ID to look up and delete |
| FNAMEI     | Output    | First name displayed after lookup (not editable for delete) |
| LNAMEI     | Output    | Last name displayed after lookup |
| USRTYPEI   | Output    | User type displayed after lookup |
| ERRMSGO    | Output    | WS-MESSAGE: error or status message |
| ERRMSGC    | Output    | Color: DFHNEUTR (prompt), DFHGREEN (success) |
| TITLE01O–CURTIMEO | Output | Standard header fields |

**Note**: Password (PASSWDI) is NOT present on the COUSR3A map. Unlike COUSR02C which shows the password for editing, COUSR03C only shows non-sensitive fields (first/last name, type) for confirmation before deletion.

**Navigation:**
- ENTER: look up user; display name and type
- PF3: XCTL to CDEMO-FROM-PROGRAM (no delete)
- PF4: clear all fields
- PF5: delete the looked-up user
- PF12: XCTL to COADM01C (no delete)
- Other keys: CCDA-MSG-INVALID-KEY

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| CDEMO-FROM-PROGRAM (COUSR00C) | CICS XCTL | PF3: uses CDEMO-FROM-PROGRAM if set (line 115–117) |
| COADM01C   | CICS XCTL   | PF12 pressed (hardcoded at line 124) |
| COSGN00C   | CICS XCTL   | EIBCALEN=0 or CDEMO-TO-PROGRAM blank |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C |
| USRIDINI blank (PROCESS-ENTER-KEY) | ERR-FLG-ON; 'User ID can NOT be empty...' |
| USRIDINI blank (DELETE-USER-INFO) | ERR-FLG-ON; 'User ID can NOT be empty...' |
| READ NOTFND | ERR-FLG-ON; 'User ID NOT found...'; cursor on USRIDINL |
| READ OTHER | DISPLAY RESP/RESP2 (to sysprint, line 294); ERR-FLG-ON; 'Unable to lookup User...' |
| DELETE NOTFND | ERR-FLG-ON; 'User ID NOT found...' |
| DELETE OTHER | DISPLAY RESP/RESP2 (line 330); ERR-FLG-ON; 'Unable to Update User...' (error message text says "Update" even for DELETE — copied from COUSR02C template) |
| Invalid AID key | ERR-FLG-ON; CCDA-MSG-INVALID-KEY |

**Note on error message text**: The OTHER branch of DELETE-USER-SEC-FILE displays 'Unable to Update User...' (line 333) — this is a copy-paste artifact from COUSR02C. The correct message would reference deletion, not update.

---

## 9. Business Rules

1. **Admin-only function**: COUSR03C is reached from COUSR00C (selection 'D') or COADM01C (option 4). PF12 always returns to COADM01C.
2. **Two-step delete workflow**: ENTER looks up and displays the user record (first/last name, type) for review. PF5 confirms the deletion. This prevents accidental deletes.
3. **Password not displayed**: The BMS map COUSR3A does not include a password field. Only identifying information (name, type) is shown to help the admin confirm the correct user before deletion.
4. **Re-read before DELETE**: DELETE-USER-INFO re-reads the record with UPDATE before issuing DELETE, ensuring the lock is acquired even if the operator paused between ENTER and PF5 (the prior lock from PROCESS-ENTER-KEY was released at CICS RETURN).
5. **Screen reset after delete**: INITIALIZE-ALL-FIELDS clears all fields after successful deletion, allowing the admin to delete another user.
6. **PF3 respects CDEMO-FROM-PROGRAM**: Unlike PF12 (hardcoded to COADM01C), PF3 uses CDEMO-FROM-PROGRAM if set, defaulting to COADM01C if blank (lines 112–117). This allows callers other than COUSR00C to navigate back correctly.
7. **WS-USR-MODIFIED unused**: WS-USR-MODIFIED and its 88-levels are defined (lines 45–47) but never referenced in the PROCEDURE DIVISION. This is a copy-paste remnant from COUSR02C.
8. **DISPLAY statements**: READ-USER-SEC-FILE (line 294) and DELETE-USER-SEC-FILE (line 330) emit RESP/RESP2 to sysprint on the OTHER error path.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COUSR3A) | USRIDINI — user ID to look up and delete |
| COMMAREA  | CDEMO-CU03-USR-SELECTED (pre-selected user ID from COUSR00C) |
| USRSEC VSAM | User record read for display and pre-deletion lock |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COUSR3A) | User detail for confirmation (first/last name, type); success/error messages |
| USRSEC VSAM | Record deleted on PF5 confirmation |

---

## 11. Key Variables and Their Purpose

| Variable                  | Purpose |
|---------------------------|---------|
| USRIDINI                  | User ID to delete; RIDFLD for READ UPDATE |
| CDEMO-CU03-USR-SELECTED   | User ID from COUSR00C 'D' selection; auto-populates USRIDINI on first entry |
| SEC-USER-DATA             | Full USRSEC record read for display; held under UPDATE lock for DELETE |
| WS-USR-MODIFIED           | Defined but never used — dead working storage from COUSR02C template |
| ERRMSGC                   | Color: DFHNEUTR (lookup prompt), DFHGREEN (deletion success) |
