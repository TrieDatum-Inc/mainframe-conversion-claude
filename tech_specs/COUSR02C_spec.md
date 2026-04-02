# Technical Specification: COUSR02C — User Update Program

## 1. Executive Summary

COUSR02C is a CICS COBOL online program that allows an administrator to update an existing user record in the USRSEC VSAM file. It operates in a two-phase workflow: first the operator enters or receives a User ID (fetched from COUSR00C via COMMAREA) and presses ENTER to read and display the current record; then the operator modifies fields and presses PF5 to save, or PF3 to save-and-exit. The program uses CICS READ with UPDATE followed by REWRITE for optimistic record-level locking.

---

## 2. Artifact Identification

| Attribute        | Value                    |
|-----------------|--------------------------|
| Program Name    | COUSR02C                 |
| Source File     | app/cbl/COUSR02C.cbl     |
| Program Type    | CICS COBOL Online        |
| Transaction ID  | CU02                     |
| Map Used        | COUSR2A                  |
| Mapset Used     | COUSR02                  |
| VSAM File       | USRSEC                   |
| Version Tag     | CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19 |

---

## 3. Copybooks Referenced

| Copybook    | Source Location             | Purpose                                                      |
|-------------|-----------------------------|------------------------------------------------------------|
| COCOM01Y    | app/cpy/COCOM01Y.cpy        | CARDDEMO-COMMAREA — inter-program communication area         |
| COUSR02     | app/cpy-bms/COUSR02.CPY     | BMS-generated symbolic map for COUSR2AI / COUSR2AO          |
| COTTL01Y    | app/cpy/COTTL01Y.cpy        | Screen title literals                                        |
| CSDAT01Y    | app/cpy/CSDAT01Y.cpy        | Date/time working storage fields                            |
| CSMSG01Y    | app/cpy/CSMSG01Y.cpy        | Common messages (CCDA-MSG-INVALID-KEY)                      |
| CSUSR01Y    | app/cpy/CSUSR01Y.cpy        | SEC-USER-DATA record layout for USRSEC file                 |
| DFHAID      | CICS system                 | Attention Identifier constants                              |
| DFHBMSCA    | CICS system                 | BMS attribute byte constants                                |

### Inline COMMAREA Extension (COUSR02C.cbl, lines 50–58)

```
05 CDEMO-CU02-INFO.
   10 CDEMO-CU02-USRID-FIRST     PIC X(08)
   10 CDEMO-CU02-USRID-LAST      PIC X(08)
   10 CDEMO-CU02-PAGE-NUM        PIC 9(08)
   10 CDEMO-CU02-NEXT-PAGE-FLG   PIC X(01)  VALUE 'N'
      88 NEXT-PAGE-YES              VALUE 'Y'
      88 NEXT-PAGE-NO               VALUE 'N'
   10 CDEMO-CU02-USR-SEL-FLG     PIC X(01)
   10 CDEMO-CU02-USR-SELECTED    PIC X(08)
```

These fields overlap CDEMO-CU00-INFO in the COMMAREA when COUSR02C is invoked from COUSR00C (same physical byte positions). CDEMO-CU02-USR-SELECTED contains the User ID selected on the list screen.

---

## 4. Data Structures

### 4.1 CSUSR01Y — USRSEC File Record (app/cpy/CSUSR01Y.cpy)

| Field            | PIC   | Length | Description               |
|------------------|-------|--------|---------------------------|
| SEC-USR-ID       | X(08) | 8      | User ID — VSAM key field  |
| SEC-USR-FNAME    | X(20) | 20     | First name                |
| SEC-USR-LNAME    | X(20) | 20     | Last name                 |
| SEC-USR-PWD      | X(08) | 8      | Password (plaintext)      |
| SEC-USR-TYPE     | X(01) | 1      | A=Admin, U=User           |
| SEC-USR-FILLER   | X(23) | 23     | Reserved                  |
| **Total**        |       | **80** |                           |

### 4.2 BMS Symbolic Map — COUSR2AI / COUSR2AO (app/cpy-bms/COUSR02.CPY)

Input area (COUSR2AI) key fields:

| Map Field   | PIC    | Description                           |
|-------------|--------|---------------------------------------|
| USRIDINI    | X(08)  | User ID search field (input)          |
| USRIDINL    | S9(4)  | Cursor length control for USRIDIN     |
| FNAMEI      | X(20)  | First name (editable after fetch)     |
| LNAMEI      | X(20)  | Last name (editable after fetch)      |
| PASSWDI     | X(08)  | Password (editable after fetch)       |
| USRTYPEI    | X(01)  | User type (editable after fetch)      |
| ERRMSGI     | X(78)  | Error message (input)                 |

Output redefine COUSR2AO exposes USRIDINO, FNAMEO, LNAMEO, PASSWDO, USRTYPEO, ERRMSGC (color control for error msg), etc.

### 4.3 WS-USR-MODIFIED Flag (COUSR02C.cbl, lines 45–47)

| Field            | PIC   | Initial | Description                             |
|------------------|-------|---------|-----------------------------------------|
| WS-USR-MODIFIED  | X(01) | N       | 88 USR-MODIFIED-YES VALUE 'Y'; set when any field differs from USRSEC record |

---

## 5. Working Storage Variables (COUSR02C.cbl, lines 35–47)

| Field           | PIC         | Initial  | Description                     |
|-----------------|-------------|----------|---------------------------------|
| WS-PGMNAME      | X(08)       | COUSR02C | Program name literal            |
| WS-TRANID       | X(04)       | CU02     | Transaction ID literal          |
| WS-MESSAGE      | X(80)       | SPACES   | Message buffer                  |
| WS-USRSEC-FILE  | X(08)       | USRSEC   | CICS dataset name               |
| WS-ERR-FLG      | X(01)       | N        | Error flag                      |
| WS-RESP-CD      | S9(09) COMP | ZEROS    | CICS RESP code                  |
| WS-REAS-CD      | S9(09) COMP | ZEROS    | CICS RESP2 code                 |
| WS-USR-MODIFIED | X(01)       | N        | Dirty flag for change detection |

---

## 6. CICS Commands Used

| Command                | Location (Paragraph)              | Purpose                                             |
|------------------------|-----------------------------------|-----------------------------------------------------|
| EXEC CICS RETURN       | MAIN-PARA (line 135)              | Pseudo-conversational return with COMMAREA          |
| EXEC CICS XCTL         | RETURN-TO-PREV-SCREEN (line 258)  | Transfer control to COADM01C or prior program      |
| EXEC CICS SEND MAP     | SEND-USRUPD-SCREEN (line 272)     | Send COUSR2A map with ERASE and CURSOR             |
| EXEC CICS RECEIVE MAP  | RECEIVE-USRUPD-SCREEN (line 285)  | Receive input from COUSR2A                         |
| EXEC CICS READ UPDATE  | READ-USER-SEC-FILE (line 322)     | Read USRSEC record with UPDATE lock                |
| EXEC CICS REWRITE      | UPDATE-USER-SEC-FILE (line 360)   | Rewrite updated record to USRSEC                  |

---

## 7. Program Flow — Paragraph-by-Paragraph

### MAIN-PARA (lines 82–138)

Entry point. Clears flags (ERR-FLG-OFF, USR-MODIFIED-NO). Clears WS-MESSAGE and ERRMSGO.

**EIBCALEN = 0:** XCTL to COSGN00C.

**First programmatic entry (NOT CDEMO-PGM-REENTER):**
1. Sets CDEMO-PGM-REENTER.
2. Initializes COUSR2AO to LOW-VALUES.
3. Sets USRIDINL = -1 (cursor on User ID field).
4. If CDEMO-CU02-USR-SELECTED is not blank/low (i.e., caller passed a User ID): moves it to USRIDINI and immediately calls PROCESS-ENTER-KEY to fetch the record.
5. Calls SEND-USRUPD-SCREEN.

This design means that when invoked from COUSR00C with a selected user, the screen opens pre-populated with that user's data.

**Re-entry (CDEMO-PGM-REENTER):**
Receives screen, dispatches on EIBAID:
- DFHENTER → PROCESS-ENTER-KEY (fetch user by typed User ID)
- DFHPF3 → UPDATE-USER-INFO then RETURN-TO-PREV-SCREEN (save and exit)
- DFHPF4 → CLEAR-CURRENT-SCREEN
- DFHPF5 → UPDATE-USER-INFO (save without exit)
- DFHPF12 → RETURN-TO-PREV-SCREEN targeting COADM01C (cancel/exit without save)
- OTHER → invalid key error

PF3 return target: if CDEMO-FROM-PROGRAM is populated, returns there; otherwise COADM01C.

Terminates with EXEC CICS RETURN TRANSID('CU02') COMMAREA(CARDDEMO-COMMAREA).

### PROCESS-ENTER-KEY (lines 143–172)

1. Validates USRIDINI not blank. If blank: error 'User ID can NOT be empty...', cursor to USRIDINL.
2. If valid: clears FNAMEI, LNAMEI, PASSWDI, USRTYPEI to SPACES, moves USRIDINI to SEC-USR-ID.
3. Calls READ-USER-SEC-FILE.
4. If no error: populates map fields (FNAMEI, LNAMEI, PASSWDI, USRTYPEI) from SEC-USER-DATA, calls SEND-USRUPD-SCREEN.

### UPDATE-USER-INFO (lines 177–245)

Two-phase paragraph:

**Phase 1 — Validation (EVALUATE TRUE):**
1. USRIDINI blank → 'User ID can NOT be empty...'
2. FNAMEI blank → 'First Name can NOT be empty...'
3. LNAMEI blank → 'Last Name can NOT be empty...'
4. PASSWDI blank → 'Password can NOT be empty...'
5. USRTYPEI blank → 'User Type can NOT be empty...'
6. WHEN OTHER: cursor to FNAMEL, continue.

**Phase 2 — Change Detection and Save:**
1. Moves USRIDINI to SEC-USR-ID, calls READ-USER-SEC-FILE (acquires UPDATE lock).
2. Compares each field individually:
   - If FNAMEI ≠ SEC-USR-FNAME: moves FNAMEI → SEC-USR-FNAME, sets USR-MODIFIED-YES.
   - If LNAMEI ≠ SEC-USR-LNAME: moves LNAMEI → SEC-USR-LNAME, sets USR-MODIFIED-YES.
   - If PASSWDI ≠ SEC-USR-PWD: moves PASSWDI → SEC-USR-PWD, sets USR-MODIFIED-YES.
   - If USRTYPEI ≠ SEC-USR-TYPE: moves USRTYPEI → SEC-USR-TYPE, sets USR-MODIFIED-YES.
3. If USR-MODIFIED-YES: calls UPDATE-USER-SEC-FILE (REWRITE).
4. If USR-MODIFIED-NO: displays 'Please modify to update ...' in DFHRED, re-displays screen (no REWRITE issued).

**Important:** This paragraph calls READ-USER-SEC-FILE which itself calls SEND-USRUPD-SCREEN internally on success. READ-USER-SEC-FILE was designed for the display path, not specifically for the update path — it issues a SEND on DFHRESP(NORMAL) with the message 'Press PF5 key to save your updates...'. This means PF5/PF3 paths that invoke UPDATE-USER-INFO will trigger an extra screen send from within READ-USER-SEC-FILE before the REWRITE logic proceeds.

### RETURN-TO-PREV-SCREEN (lines 250–261)

If CDEMO-TO-PROGRAM blank, defaults to COSGN00C. Sets CDEMO-FROM-TRANID='CU02', CDEMO-FROM-PROGRAM='COUSR02C', zeros CDEMO-PGM-CONTEXT. Issues EXEC CICS XCTL.

### SEND-USRUPD-SCREEN (lines 266–278)

Calls POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO, issues EXEC CICS SEND MAP('COUSR2A') MAPSET('COUSR02') ERASE CURSOR.

### RECEIVE-USRUPD-SCREEN (lines 283–291)

Issues EXEC CICS RECEIVE MAP('COUSR2A') MAPSET('COUSR02') INTO(COUSR2AI).

### POPULATE-HEADER-INFO (lines 296–315)

Same pattern as other programs. Populates header with TRNNAMEO='CU02', PGMNAMEO='COUSR02C', date/time.

### READ-USER-SEC-FILE (lines 320–353)

Issues EXEC CICS READ DATASET('USRSEC') INTO(SEC-USER-DATA) LENGTH(80) RIDFLD(SEC-USR-ID) KEYLENGTH(8) **UPDATE**.

Response handling:
- DFHRESP(NORMAL): moves 'Press PF5 key to save your updates ...' to WS-MESSAGE, sets ERRMSGC to DFHNEUTR (neutral color), calls SEND-USRUPD-SCREEN. Note: this internal SEND is reached both from PROCESS-ENTER-KEY (display path) and from UPDATE-USER-INFO (save path).
- DFHRESP(NOTFND): ERR-FLG-ON, 'User ID NOT found...', cursor to USRIDINL.
- OTHER: ERR-FLG-ON, 'Unable to lookup User...', cursor to FNAMEL.

### UPDATE-USER-SEC-FILE (lines 358–390)

Issues EXEC CICS REWRITE DATASET('USRSEC') FROM(SEC-USER-DATA) LENGTH(80).

Response handling:
- DFHRESP(NORMAL): sets ERRMSGC to DFHGREEN, builds 'User &lt;id&gt; has been updated ...' message, calls SEND-USRUPD-SCREEN.
- DFHRESP(NOTFND): ERR-FLG-ON, 'User ID NOT found...'.
- OTHER: ERR-FLG-ON, 'Unable to Update User...'.

### CLEAR-CURRENT-SCREEN (lines 395–398)

Calls INITIALIZE-ALL-FIELDS then SEND-USRUPD-SCREEN.

### INITIALIZE-ALL-FIELDS (lines 403–411)

Sets USRIDINL = -1. Clears USRIDINI, FNAMEI, LNAMEI, PASSWDI, USRTYPEI, and WS-MESSAGE to SPACES.

---

## 8. Inter-Program Interactions

| Direction | Target Program | Mechanism    | Condition                                          |
|-----------|---------------|--------------|-----------------------------------------------------|
| Inbound   | COUSR00C      | XCTL → CU02  | User selected 'U' on list screen                   |
| Inbound   | COADM01C      | XCTL → CU02  | Admin menu direct access (if configured)           |
| Outbound  | COADM01C      | XCTL         | PF3 or PF12 (return to admin menu)                 |
| Outbound  | COUSR00C      | XCTL         | PF3 if CDEMO-FROM-PROGRAM = 'COUSR00C'             |
| Outbound  | COSGN00C      | XCTL         | EIBCALEN=0 or CDEMO-TO-PROGRAM blank               |

Data received from COUSR00C via CARDDEMO-COMMAREA:
- CDEMO-CU02-USR-SELECTED (= CDEMO-CU00-USR-SELECTED): the 8-char User ID to preload
- CDEMO-FROM-PROGRAM: 'COUSR00C' (determines PF3 return destination)

---

## 9. Error Handling

| Error Condition            | Response                                          | Color    |
|----------------------------|---------------------------------------------------|----------|
| User ID blank              | 'User ID can NOT be empty...'                    | Default  |
| First Name blank           | 'First Name can NOT be empty...'                 | Default  |
| Last Name blank            | 'Last Name can NOT be empty...'                  | Default  |
| Password blank             | 'Password can NOT be empty...'                   | Default  |
| User Type blank            | 'User Type can NOT be empty...'                  | Default  |
| User ID not found (READ)   | 'User ID NOT found...'                           | Default  |
| READ other error           | 'Unable to lookup User...' + DISPLAY to console  | Default  |
| No changes detected        | 'Please modify to update ...'                    | DFHRED   |
| REWRITE not found          | 'User ID NOT found...'                           | Default  |
| REWRITE other error        | 'Unable to Update User...' + DISPLAY             | Default  |
| Invalid AID key            | CCDA-MSG-INVALID-KEY                             | Default  |
| Successful update          | 'User &lt;id&gt; has been updated ...'            | DFHGREEN |
| User fetched successfully  | 'Press PF5 key to save your updates ...'         | DFHNEUTR |

---

## 10. Business Rules

| Rule                                                              | Source Location (line)                |
|-------------------------------------------------------------------|---------------------------------------|
| User ID field is read-only after fetch (populated by program from COMMAREA or ENTER key) | PROCESS-ENTER-KEY, lines 162-163 |
| All fields (FNAME, LNAME, PASSWD, USRTYPE) are mandatory before save | UPDATE-USER-INFO, lines 179–213 |
| Only fields that have changed are written back (field-level comparison) | UPDATE-USER-INFO, lines 219–234 |
| If no fields changed, save is suppressed with an error message    | UPDATE-USER-INFO, lines 236–242       |
| PF3 triggers a save attempt before exiting (combines UPDATE-USER-INFO + RETURN) | MAIN-PARA, lines 112–119 |
| PF5 saves without exiting (stays on update screen)               | MAIN-PARA, line 123                   |
| PF12 exits without saving (direct cancel)                         | MAIN-PARA, lines 125–126              |
| Returning to caller: uses CDEMO-FROM-PROGRAM if set, else COADM01C | MAIN-PARA, lines 113–118           |
| VSAM record key (User ID) cannot be changed — only non-key fields | READ-USER-SEC-FILE uses existing key; no key change logic |

---

## 11. Transaction Flow Context

```
COUSR00C (List Users, U selection)
    |
    v [via XCTL, CDEMO-CU02-USR-SELECTED populated]
COUSR02C (Update User)
    |
    +-- [first entry: COMMAREA has user ID] --> auto-fetch record --> display with data
    |
    +-- [ENTER: type new user ID] --> fetch and display record
    |
    +-- [PF5: modify fields] --> validate --> change-detect --> REWRITE --> success msg
    |
    +-- [PF3: modify fields] --> validate --> change-detect --> REWRITE --> XCTL back
    |
    +-- [PF12: cancel] --> XCTL back (no save)
    |
    +-- [PF4: clear form]
    |
    v
COUSR00C or COADM01C (depending on CDEMO-FROM-PROGRAM)
```

---

## 12. Open Questions and Gaps

- READ-USER-SEC-FILE issues a SEND MAP internally on DFHRESP(NORMAL) (line 337). When called from UPDATE-USER-INFO (PF5/PF3 path), this sends an extra screen ('Press PF5 key to save your updates...') before the REWRITE happens. This results in two screen sends per PF5 keystroke: one from READ-USER-SEC-FILE and one from UPDATE-USER-SEC-FILE. The second send (from REWRITE success) will overwrite the first due to ERASE. While functionally acceptable, it is an inefficiency and could cause a brief screen flicker. **Confidence: HIGH.**
- The REWRITE command does not explicitly specify RIDFLD. Under CICS, REWRITE operates on the record most recently read with UPDATE in the current task, which is correct behavior here. **Confidence: HIGH.**
- User Type is not range-validated (only non-blank check). **Confidence: HIGH.**
- Password is stored and transmitted in plaintext. **Confidence: HIGH.**
