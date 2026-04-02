# Technical Specification: COUSR00C — User List Program

## 1. Executive Summary

COUSR00C is a CICS COBOL online program that provides paginated browsing of the USRSEC VSAM file. It presents up to 10 user records per screen page and allows an operator to navigate forward (PF8), backward (PF7), or select a specific user record for update (U) or delete (D), transferring control to COUSR02C or COUSR03C respectively. It is the entry point of the user management subsystem for administrators.

---

## 2. Artifact Identification

| Attribute        | Value                    |
|-----------------|--------------------------|
| Program Name    | COUSR00C                 |
| Source File     | app/cbl/COUSR00C.cbl     |
| Program Type    | CICS COBOL Online        |
| Transaction ID  | CU00                     |
| Map Used        | COUSR0A                  |
| Mapset Used     | COUSR00                  |
| VSAM File       | USRSEC                   |
| Version Tag     | CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19 |

---

## 3. Copybooks Referenced

| Copybook       | Source Location               | Purpose                                                    |
|----------------|-------------------------------|------------------------------------------------------------|
| COCOM01Y       | app/cpy/COCOM01Y.cpy          | CARDDEMO-COMMAREA — inter-program communication area       |
| COUSR00        | app/cpy-bms/COUSR00.CPY       | BMS-generated symbolic map for COUSR0AI / COUSR0AO        |
| COTTL01Y       | app/cpy/COTTL01Y.cpy          | Screen title literals (CCDA-TITLE01, CCDA-TITLE02)         |
| CSDAT01Y       | app/cpy/CSDAT01Y.cpy          | Date/time working storage fields (WS-CURDATE-DATA etc.)   |
| CSMSG01Y       | app/cpy/CSMSG01Y.cpy          | Common message literals (CCDA-MSG-INVALID-KEY)            |
| CSUSR01Y       | app/cpy/CSUSR01Y.cpy          | SEC-USER-DATA record layout for USRSEC file               |
| DFHAID         | CICS system                   | Attention Identifier constants (DFHENTER, DFHPF3, etc.)  |
| DFHBMSCA       | CICS system                   | BMS attribute byte constants (DFHGREEN, DFHRED, etc.)     |

### Inline COMMAREA Extension (COUSR00C.cbl, lines 67–75)
After the COPY COCOM01Y statement, the program defines additional fields inline within the COMMAREA structure:

```
05 CDEMO-CU00-INFO.
   10 CDEMO-CU00-USRID-FIRST     PIC X(08)
   10 CDEMO-CU00-USRID-LAST      PIC X(08)
   10 CDEMO-CU00-PAGE-NUM        PIC 9(08)
   10 CDEMO-CU00-NEXT-PAGE-FLG   PIC X(01)  VALUE 'N'
      88 NEXT-PAGE-YES              VALUE 'Y'
      88 NEXT-PAGE-NO               VALUE 'N'
   10 CDEMO-CU00-USR-SEL-FLG     PIC X(01)
   10 CDEMO-CU00-USR-SELECTED    PIC X(08)
```

These fields are passed forward and backward across pseudo-conversational RETURN/re-entry cycles via CARDDEMO-COMMAREA.

---

## 4. Data Structures

### 4.1 CSUSR01Y — USRSEC File Record (app/cpy/CSUSR01Y.cpy)

| Field              | PIC      | Length | Description              |
|--------------------|----------|--------|--------------------------|
| SEC-USR-ID         | X(08)    | 8      | User ID — VSAM key field |
| SEC-USR-FNAME      | X(20)    | 20     | First name               |
| SEC-USR-LNAME      | X(20)    | 20     | Last name                |
| SEC-USR-PWD        | X(08)    | 8      | Password                 |
| SEC-USR-TYPE       | X(01)    | 1      | User type: A=Admin, U=User |
| SEC-USR-FILLER     | X(23)    | 23     | Reserved padding         |
| **Total**          |          | **80** |                          |

### 4.2 WS-USER-DATA — Local Screen Buffer (COUSR00C.cbl, lines 56–64)

An internal working storage array of 10 USER-REC occurrences, each containing:
- USER-SEL  PIC X(01)
- USER-ID   PIC X(08)
- USER-NAME PIC X(25)
- USER-TYPE PIC X(08)

Note: This structure is populated but the program primarily uses the BMS map symbolic fields (COUSR0AI/COUSR0AO) directly for display.

### 4.3 CARDDEMO-COMMAREA (COCOM01Y.cpy)

| Field                | PIC     | Description                              |
|----------------------|---------|------------------------------------------|
| CDEMO-FROM-TRANID    | X(04)   | Originating transaction ID               |
| CDEMO-FROM-PROGRAM   | X(08)   | Originating program name                 |
| CDEMO-TO-TRANID      | X(04)   | Target transaction ID                    |
| CDEMO-TO-PROGRAM     | X(08)   | Target program name for XCTL             |
| CDEMO-USER-ID        | X(08)   | Signed-on user ID                        |
| CDEMO-USER-TYPE      | X(01)   | A=Admin, U=User                          |
| CDEMO-PGM-CONTEXT    | 9(01)   | 0=first entry, 1=re-entry                |

---

## 5. CICS Commands Used

| Command            | Location (Paragraph)         | Purpose                                           |
|--------------------|------------------------------|---------------------------------------------------|
| EXEC CICS RETURN   | MAIN-PARA (line 141)         | Pseudo-conversational return; passes COMMAREA     |
| EXEC CICS XCTL     | PROCESS-ENTER-KEY (line 196) | Transfer control to COUSR02C (update)             |
| EXEC CICS XCTL     | PROCESS-ENTER-KEY (line 206) | Transfer control to COUSR03C (delete)             |
| EXEC CICS XCTL     | RETURN-TO-PREV-SCREEN (line 514) | Return to COADM01C or COSGN00C               |
| EXEC CICS SEND MAP | SEND-USRLST-SCREEN (lines 529–543) | Send COUSR0A map to terminal               |
| EXEC CICS RECEIVE MAP | RECEIVE-USRLST-SCREEN (lines 551–557) | Receive input from terminal           |
| EXEC CICS STARTBR  | STARTBR-USER-SEC-FILE (lines 588–595) | Start browse on USRSEC file            |
| EXEC CICS READNEXT | READNEXT-USER-SEC-FILE (lines 621–629) | Read forward through USRSEC           |
| EXEC CICS READPREV | READPREV-USER-SEC-FILE (lines 655–663) | Read backward through USRSEC          |
| EXEC CICS ENDBR    | ENDBR-USER-SEC-FILE (lines 689–691) | End browse on USRSEC file               |

---

## 6. Program Flow — Paragraph-by-Paragraph

### MAIN-PARA (lines 98–144)

Entry point. Initializes flags (ERR-FLG-OFF, USER-SEC-NOT-EOF, NEXT-PAGE-NO, SEND-ERASE-YES). Clears WS-MESSAGE and ERRMSGO.

**First-time entry (EIBCALEN = 0):** Redirects to COSGN00C via RETURN-TO-PREV-SCREEN. This guards against direct transaction invocation without an established session.

**Subsequent entries:**
1. Moves DFHCOMMAREA into CARDDEMO-COMMAREA.
2. If NOT CDEMO-PGM-REENTER (first programmatic entry): sets CDEMO-PGM-REENTER, initializes map output area (LOW-VALUES to COUSR0AO), calls PROCESS-ENTER-KEY, then SEND-USRLST-SCREEN.
3. If re-entry: calls RECEIVE-USRLST-SCREEN, then dispatches on EIBAID:
   - DFHENTER → PROCESS-ENTER-KEY
   - DFHPF3 → RETURN-TO-PREV-SCREEN targeting COADM01C
   - DFHPF7 → PROCESS-PF7-KEY (page backward)
   - DFHPF8 → PROCESS-PF8-KEY (page forward)
   - OTHER → invalid key error, re-display screen

Terminates with EXEC CICS RETURN TRANSID('CU00') COMMAREA(CARDDEMO-COMMAREA).

### PROCESS-ENTER-KEY (lines 149–232)

1. Scans SEL0001I through SEL0010I looking for the first non-space/non-low-value selection code. Captures the corresponding USRIDnn field into CDEMO-CU00-USR-SELECTED and the selection code into CDEMO-CU00-USR-SEL-FLG.
2. If a valid selection exists:
   - 'U' or 'u': sets CDEMO-TO-PROGRAM='COUSR02C', sets CDEMO-FROM-TRANID/CDEMO-FROM-PROGRAM, zeros CDEMO-PGM-CONTEXT, issues EXEC CICS XCTL to COUSR02C.
   - 'D' or 'd': sets CDEMO-TO-PROGRAM='COUSR03C', issues EXEC CICS XCTL to COUSR03C.
   - Other value: sets error message 'Invalid selection. Valid values are U and D'.
3. Sets SEC-USR-ID from USRIDINI (search anchor field) or LOW-VALUES if blank.
4. Resets CDEMO-CU00-PAGE-NUM to 0, calls PROCESS-PAGE-FORWARD.
5. If no error, clears USRIDINO.

### PROCESS-PF7-KEY (lines 237–255) — Page Backward

Sets SEC-USR-ID from CDEMO-CU00-USRID-FIRST (first user ID of current page) or LOW-VALUES. Sets NEXT-PAGE-YES flag. If page number > 1, calls PROCESS-PAGE-BACKWARD. Otherwise, displays 'You are already at the top of the page...' without erasing screen (SEND-ERASE-NO).

### PROCESS-PF8-KEY (lines 260–277) — Page Forward

Sets SEC-USR-ID from CDEMO-CU00-USRID-LAST (last user ID of current page) or HIGH-VALUES. If NEXT-PAGE-YES, calls PROCESS-PAGE-FORWARD. Otherwise displays 'You are already at the bottom of the page...' without erase.

### PROCESS-PAGE-FORWARD (lines 282–331)

1. Calls STARTBR-USER-SEC-FILE (positions browse at SEC-USR-ID).
2. If not DFHENTER/PF7/PF3 AID (i.e., initial load), reads one READNEXT to skip the anchor record.
3. Initializes all 10 user-data slots (INITIALIZE-USER-DATA loop).
4. Loops up to 10 times: calls READNEXT-USER-SEC-FILE, then POPULATE-USER-DATA to fill the BMS map input fields.
5. After the 10-record loop, attempts one additional READNEXT to test whether more records exist, setting NEXT-PAGE-YES or NEXT-PAGE-NO accordingly.
6. Increments CDEMO-CU00-PAGE-NUM.
7. Calls ENDBR-USER-SEC-FILE, moves page number to PAGENUMI, calls SEND-USRLST-SCREEN.

### PROCESS-PAGE-BACKWARD (lines 336–379)

1. Calls STARTBR-USER-SEC-FILE (positions at first ID of current page).
2. If not DFHENTER/PF8 AID, issues READPREV to skip anchor.
3. Initializes all 10 slots.
4. Loops from WS-IDX=10 down to 1: calls READPREV-USER-SEC-FILE, POPULATE-USER-DATA with decrementing index. This fills slots in reverse-key order, but since the screen displays slot 1 at the top, this results in descending user IDs being populated in ascending slot order (slot 1 = lowest key on page).
5. Issues one more READPREV to test for a prior page, adjusting CDEMO-CU00-PAGE-NUM.
6. Calls ENDBR-USER-SEC-FILE and SEND-USRLST-SCREEN.

### POPULATE-USER-DATA (lines 384–441)

EVALUATE WS-IDX (1 through 10). Maps SEC-USR-ID, SEC-USR-FNAME, SEC-USR-LNAME, SEC-USR-TYPE into the corresponding map fields (USRID01I/FNAME01I/LNAME01I/UTYPE01I through slot 10). When WS-IDX = 1, also saves SEC-USR-ID to CDEMO-CU00-USRID-FIRST. When WS-IDX = 10, also saves SEC-USR-ID to CDEMO-CU00-USRID-LAST.

### INITIALIZE-USER-DATA (lines 446–501)

Clears all 10 rows of USRIDnnI, FNAMEnnI, LNAMEnnI, UTYPEnnI to SPACES.

### RETURN-TO-PREV-SCREEN (lines 506–517)

If CDEMO-TO-PROGRAM is blank, defaults to COSGN00C. Sets CDEMO-FROM-TRANID='CU00', CDEMO-FROM-PROGRAM='COUSR00C', zeros CDEMO-PGM-CONTEXT, then issues EXEC CICS XCTL.

### SEND-USRLST-SCREEN (lines 522–544)

Calls POPULATE-HEADER-INFO. Moves WS-MESSAGE to ERRMSGO. If SEND-ERASE-YES, sends map with ERASE option; otherwise sends without ERASE. Both forms use CURSOR to position cursor at USRIDINL = -1.

### RECEIVE-USRLST-SCREEN (lines 549–557)

Issues EXEC CICS RECEIVE MAP('COUSR0A') MAPSET('COUSR00') INTO(COUSR0AI).

### POPULATE-HEADER-INFO (lines 562–581)

Obtains current date/time via FUNCTION CURRENT-DATE. Populates TITLE01O, TITLE02O (from COTTL01Y), TRNNAMEO='CU00', PGMNAMEO='COUSR00C', CURDATEO (MM/DD/YY format), CURTIMEO (HH:MM:SS format).

### STARTBR-USER-SEC-FILE (lines 586–614)

Issues EXEC CICS STARTBR DATASET('USRSEC') RIDFLD(SEC-USR-ID) KEYLENGTH(8). On DFHRESP(NOTFND), sets USER-SEC-EOF and displays 'You are at the top of the page...'. On other error, sets ERR-FLG-ON and displays generic error.

### READNEXT-USER-SEC-FILE (lines 619–648)

Issues EXEC CICS READNEXT DATASET('USRSEC') INTO(SEC-USER-DATA) RIDFLD(SEC-USR-ID). On DFHRESP(ENDFILE), sets USER-SEC-EOF. On other error, sets ERR-FLG-ON.

### READPREV-USER-SEC-FILE (lines 653–682)

Issues EXEC CICS READPREV DATASET('USRSEC') INTO(SEC-USER-DATA) RIDFLD(SEC-USR-ID). On DFHRESP(ENDFILE), sets USER-SEC-EOF. On other error, sets ERR-FLG-ON.

### ENDBR-USER-SEC-FILE (lines 687–691)

Issues EXEC CICS ENDBR DATASET('USRSEC'). No response code checking.

---

## 7. Inter-Program Interactions

| Direction | Target Program | Mechanism    | Condition                            |
|-----------|---------------|--------------|--------------------------------------|
| Inbound   | COADM01C      | XCTL → CU00 | Admin menu navigates to user list    |
| Outbound  | COUSR02C      | XCTL         | User presses 'U' selection code      |
| Outbound  | COUSR03C      | XCTL         | User presses 'D' selection code      |
| Outbound  | COADM01C      | XCTL         | PF3 pressed (back to admin menu)     |
| Outbound  | COSGN00C      | XCTL         | EIBCALEN=0 or CDEMO-TO-PROGRAM blank |

Data passed to COUSR02C and COUSR03C via CARDDEMO-COMMAREA:
- CDEMO-CU00-USR-SELECTED: the 8-character User ID of the selected row
- CDEMO-CU00-USR-SEL-FLG: the selection character entered ('U', 'D', etc.)
- CDEMO-FROM-TRANID: 'CU00'
- CDEMO-FROM-PROGRAM: 'COUSR00C'
- CDEMO-PGM-CONTEXT: 0 (signals first entry to the target program)

---

## 8. Error Handling

| Error Condition                  | Response                                               | Flag Set    |
|----------------------------------|--------------------------------------------------------|-------------|
| EIBCALEN = 0                     | XCTL to COSGN00C                                      | None        |
| STARTBR NOTFND                   | 'You are at the top of the page...' displayed         | USER-SEC-EOF |
| STARTBR other error              | 'Unable to lookup User...' displayed                  | ERR-FLG-ON  |
| READNEXT ENDFILE                 | 'You have reached the bottom of the page...' displayed | USER-SEC-EOF |
| READNEXT other error             | 'Unable to lookup User...' displayed                  | ERR-FLG-ON  |
| READPREV ENDFILE                 | 'You have reached the top of the page...' displayed   | USER-SEC-EOF |
| READPREV other error             | 'Unable to lookup User...' displayed                  | ERR-FLG-ON  |
| Invalid AID key                  | CCDA-MSG-INVALID-KEY displayed                        | ERR-FLG-ON  |
| Invalid selection character      | 'Invalid selection. Valid values are U and D'         | None        |
| Already at top of page (PF7)     | 'You are already at the top of the page...'           | None        |
| Already at bottom (PF8)          | 'You are already at the bottom of the page...'        | None        |

---

## 9. Transaction Flow Context

```
COSGN00C (Signon)
    |
    v
COADM01C (Admin Menu) --[CU00 transaction]--> COUSR00C (List Users)
                                                    |
                              +---------------------+---------------------+
                              |                                           |
                        [U + ENTER]                               [D + ENTER]
                              |                                           |
                         COUSR02C                                   COUSR03C
                       (Update User)                              (Delete User)
                              |                                           |
                              +--------[PF3/PF12]------+--[PF3/PF12]----+
                                                       |
                                                  COADM01C
```

---

## 10. Business Rules

| Rule                             | Source Location (line)           |
|----------------------------------|----------------------------------|
| Only 'U'/'u' and 'D'/'d' are valid selection codes | PROCESS-ENTER-KEY, lines 189–215 |
| Page size is fixed at 10 records per screen | WS-IDX loop, lines 293–306 |
| First user ID on page saved as CDEMO-CU00-USRID-FIRST for backward paging | POPULATE-USER-DATA, line 389 |
| Last user ID on page saved as CDEMO-CU00-USRID-LAST for forward paging | POPULATE-USER-DATA, line 435 |
| A one-record lookahead determines whether a next page exists | PROCESS-PAGE-FORWARD, lines 308–323 |
| If no COMMAREA (EIBCALEN=0), program bounces to sign-on | MAIN-PARA, lines 110–112 |
| PF3 always returns to COADM01C (admin menu) | MAIN-PARA, lines 126–127 |

---

## 11. Open Questions and Gaps

- The STARTBR command (line 592) has the GTEQ clause commented out. Without GTEQ, the browse positions at an exact key match; records with keys less than the search term will not appear. This may cause unexpected pagination behavior when a search term does not exactly match a key. **Confidence: HIGH (directly observed in source).**
- ENDBR-USER-SEC-FILE (lines 687–691) does not check RESP/RESP2. A failed ENDBR would be silently ignored.
- The WS-USER-DATA structure (lines 56–64) is defined in WORKING-STORAGE but its fields (USER-SEL, USER-ID, USER-NAME, USER-TYPE) are never referenced in the PROCEDURE DIVISION. This appears to be dead code.
