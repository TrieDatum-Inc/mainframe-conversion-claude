# Technical Specification: COUSR03C — User Delete Program

## 1. Executive Summary

COUSR03C is a CICS COBOL online program that allows an administrator to delete an existing user record from the USRSEC VSAM file. It follows the same two-phase confirmation pattern as COUSR02C: an operator first fetches the record by User ID (either supplied by COUSR00C via COMMAREA or typed manually), reviews the displayed data, and then presses PF5 to confirm deletion. A CICS READ UPDATE + DELETE sequence ensures the record is locked before removal. The delete screen is read-only for the user data fields — no edits are possible.

---

## 2. Artifact Identification

| Attribute        | Value                    |
|-----------------|--------------------------|
| Program Name    | COUSR03C                 |
| Source File     | app/cbl/COUSR03C.cbl     |
| Program Type    | CICS COBOL Online        |
| Transaction ID  | CU03                     |
| Map Used        | COUSR3A                  |
| Mapset Used     | COUSR03                  |
| VSAM File       | USRSEC                   |
| Version Tag     | CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19 |

---

## 3. Copybooks Referenced

| Copybook    | Source Location             | Purpose                                                      |
|-------------|-----------------------------|------------------------------------------------------------|
| COCOM01Y    | app/cpy/COCOM01Y.cpy        | CARDDEMO-COMMAREA — inter-program communication area         |
| COUSR03     | app/cpy-bms/COUSR03.CPY     | BMS-generated symbolic map for COUSR3AI / COUSR3AO          |
| COTTL01Y    | app/cpy/COTTL01Y.cpy        | Screen title literals                                        |
| CSDAT01Y    | app/cpy/CSDAT01Y.cpy        | Date/time working storage fields                            |
| CSMSG01Y    | app/cpy/CSMSG01Y.cpy        | Common messages (CCDA-MSG-INVALID-KEY)                      |
| CSUSR01Y    | app/cpy/CSUSR01Y.cpy        | SEC-USER-DATA record layout for USRSEC file                 |
| DFHAID      | CICS system                 | Attention Identifier constants                              |
| DFHBMSCA    | CICS system                 | BMS attribute byte constants                                |

### Inline COMMAREA Extension (COUSR03C.cbl, lines 50–58)

```
05 CDEMO-CU03-INFO.
   10 CDEMO-CU03-USRID-FIRST     PIC X(08)
   10 CDEMO-CU03-USRID-LAST      PIC X(08)
   10 CDEMO-CU03-PAGE-NUM        PIC 9(08)
   10 CDEMO-CU03-NEXT-PAGE-FLG   PIC X(01)  VALUE 'N'
      88 NEXT-PAGE-YES              VALUE 'Y'
      88 NEXT-PAGE-NO               VALUE 'N'
   10 CDEMO-CU03-USR-SEL-FLG     PIC X(01)
   10 CDEMO-CU03-USR-SELECTED    PIC X(08)
```

Same physical byte positions as CDEMO-CU00-INFO passed from COUSR00C. CDEMO-CU03-USR-SELECTED holds the pre-selected User ID.

---

## 4. Data Structures

### 4.1 CSUSR01Y — USRSEC File Record (app/cpy/CSUSR01Y.cpy)

| Field            | PIC   | Length | Description               |
|------------------|-------|--------|---------------------------|
| SEC-USR-ID       | X(08) | 8      | User ID — VSAM key field  |
| SEC-USR-FNAME    | X(20) | 20     | First name                |
| SEC-USR-LNAME    | X(20) | 20     | Last name                 |
| SEC-USR-PWD      | X(08) | 8      | Password (not displayed)  |
| SEC-USR-TYPE     | X(01) | 1      | A=Admin, U=User           |
| SEC-USR-FILLER   | X(23) | 23     | Reserved                  |
| **Total**        |       | **80** |                           |

### 4.2 BMS Symbolic Map — COUSR3AI / COUSR3AO (app/cpy-bms/COUSR03.CPY)

Input area (COUSR3AI) key fields:

| Map Field   | PIC    | Description                                       |
|-------------|--------|---------------------------------------------------|
| USRIDINI    | X(08)  | User ID search field (input)                      |
| USRIDINL    | S9(4)  | Cursor length control                             |
| FNAMEI      | X(20)  | First name (display only — ASKIP in BMS)          |
| LNAMEI      | X(20)  | Last name (display only — ASKIP in BMS)           |
| USRTYPEI    | X(01)  | User type (display only — ASKIP in BMS)           |
| ERRMSGI     | X(78)  | Error/status message                              |

Note: COUSR03.CPY does not contain PASSWDI because the COUSR03 BMS map has no password field (password is not shown on the delete confirmation screen).

Note: FNAMEI, LNAMEI, USRTYPEI map to ASKIP fields in the BMS source — the operator cannot modify them. COUSR03C moves the fetched data into these fields via the COUSR3AI structure, which CICS sends outbound via COUSR3AO.

### 4.3 WS-USR-MODIFIED Flag (COUSR03C.cbl, lines 45–47)

| Field            | PIC   | Initial | Description              |
|------------------|-------|---------|--------------------------|
| WS-USR-MODIFIED  | X(01) | N       | 88 USR-MODIFIED-YES/NO — defined but appears unused in the delete path |

---

## 5. Working Storage Variables (COUSR03C.cbl, lines 35–47)

| Field           | PIC         | Initial  | Description                     |
|-----------------|-------------|----------|---------------------------------|
| WS-PGMNAME      | X(08)       | COUSR03C | Program name literal            |
| WS-TRANID       | X(04)       | CU03     | Transaction ID literal          |
| WS-MESSAGE      | X(80)       | SPACES   | Message buffer                  |
| WS-USRSEC-FILE  | X(08)       | USRSEC   | CICS dataset name               |
| WS-ERR-FLG      | X(01)       | N        | Error flag                      |
| WS-RESP-CD      | S9(09) COMP | ZEROS    | CICS RESP code                  |
| WS-REAS-CD      | S9(09) COMP | ZEROS    | CICS RESP2 code                 |
| WS-USR-MODIFIED | X(01)       | N        | Defined but unused in this program |

---

## 6. CICS Commands Used

| Command                | Location (Paragraph)              | Purpose                                             |
|------------------------|-----------------------------------|-----------------------------------------------------|
| EXEC CICS RETURN       | MAIN-PARA (line 134)              | Pseudo-conversational return with COMMAREA          |
| EXEC CICS XCTL         | RETURN-TO-PREV-SCREEN (line 205)  | Transfer control to caller or COADM01C             |
| EXEC CICS SEND MAP     | SEND-USRDEL-SCREEN (line 219)     | Send COUSR3A map with ERASE and CURSOR             |
| EXEC CICS RECEIVE MAP  | RECEIVE-USRDEL-SCREEN (line 233)  | Receive input from COUSR3A                         |
| EXEC CICS READ UPDATE  | READ-USER-SEC-FILE (line 269)     | Read USRSEC record with UPDATE lock                |
| EXEC CICS DELETE       | DELETE-USER-SEC-FILE (line 307)   | Delete the locked record from USRSEC               |

---

## 7. Program Flow — Paragraph-by-Paragraph

### MAIN-PARA (lines 82–137)

Entry point. Clears flags (ERR-FLG-OFF, USR-MODIFIED-NO). Clears WS-MESSAGE and ERRMSGO.

**EIBCALEN = 0:** XCTL to COSGN00C.

**First programmatic entry (NOT CDEMO-PGM-REENTER):**
1. Sets CDEMO-PGM-REENTER.
2. Initializes COUSR3AO to LOW-VALUES.
3. Sets USRIDINL = -1.
4. If CDEMO-CU03-USR-SELECTED not blank/low: moves it to USRIDINI, calls PROCESS-ENTER-KEY to fetch and display the record.
5. Calls SEND-USRDEL-SCREEN.

**Re-entry (CDEMO-PGM-REENTER):**
Receives screen, dispatches on EIBAID:
- DFHENTER → PROCESS-ENTER-KEY (fetch user record)
- DFHPF3 → determine return target (CDEMO-FROM-PROGRAM if set, else COADM01C) then RETURN-TO-PREV-SCREEN (no delete, just exit)
- DFHPF4 → CLEAR-CURRENT-SCREEN
- DFHPF5 → DELETE-USER-INFO (confirm and execute deletion)
- DFHPF12 → RETURN-TO-PREV-SCREEN targeting COADM01C (cancel)
- OTHER → invalid key error

Terminates with EXEC CICS RETURN TRANSID('CU03') COMMAREA(CARDDEMO-COMMAREA).

### PROCESS-ENTER-KEY (lines 142–169)

1. Validates USRIDINI not blank/low. If blank: ERR-FLG-ON, 'User ID can NOT be empty...', cursor to USRIDINL.
2. If valid: clears FNAMEI, LNAMEI, USRTYPEI to SPACES; moves USRIDINI → SEC-USR-ID.
3. Calls READ-USER-SEC-FILE.
4. If no error: populates FNAMEI, LNAMEI, USRTYPEI from SEC-USER-DATA; calls SEND-USRDEL-SCREEN.

Note: Password (SEC-USR-PWD) is intentionally not copied to the map — the delete confirmation screen does not display the password field.

### DELETE-USER-INFO (lines 174–192)

1. Validates USRIDINI not blank. If blank: ERR-FLG-ON, error, display.
2. Moves USRIDINI → SEC-USR-ID.
3. Calls READ-USER-SEC-FILE (acquires UPDATE lock).
4. Calls DELETE-USER-SEC-FILE (issues CICS DELETE).

Important: READ-USER-SEC-FILE internally calls SEND-USRDEL-SCREEN on success (same issue as COUSR02C). This means PF5 triggers two screen sends: one from READ and one from DELETE-USER-SEC-FILE. The second overwrites the first.

### RETURN-TO-PREV-SCREEN (lines 197–208)

If CDEMO-TO-PROGRAM blank, defaults to COSGN00C. Sets CDEMO-FROM-TRANID='CU03', CDEMO-FROM-PROGRAM='COUSR03C', zeros CDEMO-PGM-CONTEXT. Issues EXEC CICS XCTL.

### SEND-USRDEL-SCREEN (lines 213–225)

Calls POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO, issues EXEC CICS SEND MAP('COUSR3A') MAPSET('COUSR03') ERASE CURSOR.

### RECEIVE-USRDEL-SCREEN (lines 230–238)

Issues EXEC CICS RECEIVE MAP('COUSR3A') MAPSET('COUSR03') INTO(COUSR3AI).

### POPULATE-HEADER-INFO (lines 243–262)

Same pattern as other programs. Populates header with TRNNAMEO='CU03', PGMNAMEO='COUSR03C', date/time.

### READ-USER-SEC-FILE (lines 267–300)

Issues EXEC CICS READ DATASET('USRSEC') INTO(SEC-USER-DATA) LENGTH(80) RIDFLD(SEC-USR-ID) KEYLENGTH(8) **UPDATE**.

Response handling:
- DFHRESP(NORMAL): moves 'Press PF5 key to delete this user ...' to WS-MESSAGE, sets ERRMSGC to DFHNEUTR, calls SEND-USRDEL-SCREEN.
- DFHRESP(NOTFND): ERR-FLG-ON, 'User ID NOT found...', cursor to USRIDINL.
- OTHER: ERR-FLG-ON, 'Unable to lookup User...', cursor to FNAMEL, DISPLAY to console.

### DELETE-USER-SEC-FILE (lines 305–336)

Issues EXEC CICS DELETE DATASET('USRSEC') without specifying RIDFLD. This is valid because the DELETE operates on the record currently held with an UPDATE lock from the preceding READ UPDATE.

Response handling:
- DFHRESP(NORMAL): calls INITIALIZE-ALL-FIELDS (clears the form), sets ERRMSGC to DFHGREEN, builds 'User &lt;id&gt; has been deleted ...' message, calls SEND-USRDEL-SCREEN.
- DFHRESP(NOTFND): ERR-FLG-ON, 'User ID NOT found...'.
- OTHER: ERR-FLG-ON, 'Unable to Update User...' (note: message text says "Update" even for a delete failure — likely a copy-paste defect from COUSR02C), cursor to FNAMEL.

### CLEAR-CURRENT-SCREEN (lines 341–344)

Calls INITIALIZE-ALL-FIELDS then SEND-USRDEL-SCREEN.

### INITIALIZE-ALL-FIELDS (lines 349–356)

Sets USRIDINL = -1. Clears USRIDINI, FNAMEI, LNAMEI, USRTYPEI, and WS-MESSAGE to SPACES. Note: PASSWDI is not referenced here because the delete map has no password field.

---

## 8. Inter-Program Interactions

| Direction | Target Program | Mechanism    | Condition                                          |
|-----------|---------------|--------------|-----------------------------------------------------|
| Inbound   | COUSR00C      | XCTL → CU03  | User selected 'D' on list screen                   |
| Outbound  | COADM01C      | XCTL         | PF3 (back) or PF12 (cancel)                        |
| Outbound  | COUSR00C      | XCTL         | PF3 if CDEMO-FROM-PROGRAM = 'COUSR00C'             |
| Outbound  | COSGN00C      | XCTL         | EIBCALEN=0 or CDEMO-TO-PROGRAM blank               |

Data received from COUSR00C via CARDDEMO-COMMAREA:
- CDEMO-CU03-USR-SELECTED: the 8-char User ID to preload
- CDEMO-FROM-PROGRAM: 'COUSR00C' (determines PF3 return destination)

---

## 9. Error Handling

| Error Condition            | Response                                                | Color    |
|----------------------------|---------------------------------------------------------|----------|
| User ID blank              | 'User ID can NOT be empty...'                          | Default  |
| User ID not found (READ)   | 'User ID NOT found...'                                 | Default  |
| READ other error           | 'Unable to lookup User...' + DISPLAY to console        | Default  |
| DELETE not found           | 'User ID NOT found...'                                 | Default  |
| DELETE other error         | 'Unable to Update User...' + DISPLAY (incorrect msg)  | Default  |
| Invalid AID key            | CCDA-MSG-INVALID-KEY                                   | Default  |
| Successful delete          | 'User &lt;id&gt; has been deleted ...' + form cleared   | DFHGREEN |
| Record fetched ready       | 'Press PF5 key to delete this user ...'                | DFHNEUTR |

---

## 10. Business Rules

| Rule                                                              | Source Location (line)              |
|-------------------------------------------------------------------|--------------------------------------|
| Delete requires explicit confirmation by pressing PF5             | MAIN-PARA, line 121; DELETE-USER-INFO |
| PF3 exits without deleting (no auto-save unlike COUSR02C)        | MAIN-PARA, lines 112–118            |
| PF12 cancels without deleting                                     | MAIN-PARA, lines 124–125            |
| Password is not displayed on the delete confirmation screen       | PROCESS-ENTER-KEY, lines 157–159 (no password copy); BMS COUSR03 has no PASSWD field |
| After successful delete, form is cleared (ready for next delete)  | DELETE-USER-SEC-FILE, line 315      |
| User ID field is the only input field; all other fields are display-only (ASKIP) | BMS COUSR03.bms; COUSR03C program does not write to FNAMEI etc. from user input |

---

## 11. Transaction Flow Context

```
COUSR00C (List Users, D selection)
    |
    v [via XCTL, CDEMO-CU03-USR-SELECTED populated]
COUSR03C (Delete User)
    |
    +-- [first entry: COMMAREA has user ID] --> auto-fetch record --> display read-only
    |
    +-- [ENTER: type new user ID] --> fetch and display record (read-only)
    |
    +-- [PF5: confirm delete] --> READ UPDATE --> DELETE --> success msg + form cleared
    |
    +-- [PF3: back/exit] --> XCTL back (no delete)
    |
    +-- [PF12: cancel] --> XCTL to COADM01C (no delete)
    |
    +-- [PF4: clear form]
    |
    v
COUSR00C or COADM01C
```

---

## 12. Open Questions and Gaps

- DELETE-USER-SEC-FILE error message on OTHER response reads 'Unable to Update User...' (line 333). This is a copy-paste defect — it should read 'Unable to Delete User...'. **Confidence: HIGH.**
- WS-USR-MODIFIED is declared (lines 45–47) and initialized (line 85) but is never SET in the PROCEDURE DIVISION. It is dead code in COUSR03C. **Confidence: HIGH.**
- As with COUSR02C, READ-USER-SEC-FILE sends the screen internally on NORMAL response (line 283). In the PF5 delete path, this causes an extra screen send before DELETE-USER-SEC-FILE sends its own confirmation. **Confidence: HIGH.**
- The CICS DELETE command (line 307) does not include RESP checking prior to — it relies on the preceding READ UPDATE having succeeded (ERR-FLG-OFF). If ERR-FLG-ON is set, the DELETE paragraph is still called from DELETE-USER-INFO (lines 188–192: READ-USER-SEC-FILE is called, then DELETE-USER-SEC-FILE is called without re-checking ERR-FLG-ON). If READ fails and sets ERR-FLG-ON, the flow will fall through to DELETE-USER-SEC-FILE with no valid UPDATE lock held, which will result in a CICS NOTFND response. **Confidence: HIGH — observed in source lines 188–192.**
- There is no "are you sure?" double-confirmation dialog. A single PF5 press deletes the record immediately after the READ UPDATE. **Confidence: HIGH.**
