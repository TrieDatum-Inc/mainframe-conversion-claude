# Technical Specification: COUSR01C — User Add Program

## 1. Executive Summary

COUSR01C is a CICS COBOL online program that allows an administrator to add a new user record (Regular or Admin) to the USRSEC VSAM file. The program collects five required fields — First Name, Last Name, User ID, Password, and User Type — validates them, writes a new KSDS record, and confirms the addition. It is accessed from COADM01C (the Admin menu), not from the user list screen COUSR00C.

---

## 2. Artifact Identification

| Attribute        | Value                    |
|-----------------|--------------------------|
| Program Name    | COUSR01C                 |
| Source File     | app/cbl/COUSR01C.cbl     |
| Program Type    | CICS COBOL Online        |
| Transaction ID  | CU01                     |
| Map Used        | COUSR1A                  |
| Mapset Used     | COUSR01                  |
| VSAM File       | USRSEC                   |
| Version Tag     | CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19 |

---

## 3. Copybooks Referenced

| Copybook    | Source Location             | Purpose                                                    |
|-------------|-----------------------------|------------------------------------------------------------|
| COCOM01Y    | app/cpy/COCOM01Y.cpy        | CARDDEMO-COMMAREA — inter-program communication area       |
| COUSR01     | app/cpy-bms/COUSR01.CPY     | BMS-generated symbolic map for COUSR1AI / COUSR1AO        |
| COTTL01Y    | app/cpy/COTTL01Y.cpy        | Screen title literals                                      |
| CSDAT01Y    | app/cpy/CSDAT01Y.cpy        | Date/time working storage fields                          |
| CSMSG01Y    | app/cpy/CSMSG01Y.cpy        | Common messages (CCDA-MSG-INVALID-KEY)                    |
| CSUSR01Y    | app/cpy/CSUSR01Y.cpy        | SEC-USER-DATA record layout for USRSEC file               |
| DFHAID      | CICS system                 | Attention Identifier constants                            |
| DFHBMSCA    | CICS system                 | BMS attribute byte constants                              |

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

### 4.2 BMS Symbolic Map — COUSR1AI / COUSR1AO (app/cpy-bms/COUSR01.CPY)

Input area (COUSR1AI) key fields:

| Map Field   | PIC    | Description                  |
|-------------|--------|------------------------------|
| FNAMEI      | X(20)  | First name entered by user   |
| LNAMEI      | X(20)  | Last name entered by user    |
| USERIDI     | X(08)  | User ID entered by user      |
| PASSWDI     | X(08)  | Password entered by user     |
| USRTYPEI    | X(01)  | User type entered by user    |
| ERRMSGI     | X(78)  | Error message field (input)  |

Each named field also has length (e.g., FNAMEL COMP PIC S9(4)), flag (FNAMEF), and attribute (FNAMEA) sub-fields. The output redefine COUSR1AO exposes color (e.g., FNAMEC), print (FNAMEP), highlight (FNAMEH), video (FNAMEV), and data (FNAMEO) sub-fields.

### 4.3 CARDDEMO-COMMAREA (COCOM01Y.cpy)

See COUSR00C spec Section 4.3. Same structure. COUSR01C does not use module-specific COMMAREA extension fields.

---

## 5. Working Storage Variables (COUSR01C.cbl, lines 35–44)

| Field           | PIC       | Initial  | Description                     |
|-----------------|-----------|----------|---------------------------------|
| WS-PGMNAME      | X(08)     | COUSR01C | Program name literal            |
| WS-TRANID       | X(04)     | CU01     | Transaction ID literal          |
| WS-MESSAGE      | X(80)     | SPACES   | Message buffer for ERRMSGO      |
| WS-USRSEC-FILE  | X(08)     | USRSEC   | CICS dataset name               |
| WS-ERR-FLG      | X(01)     | N        | Error flag; 88 ERR-FLG-ON='Y'  |
| WS-RESP-CD      | S9(09) COMP | ZEROS  | CICS RESP primary code          |
| WS-REAS-CD      | S9(09) COMP | ZEROS  | CICS RESP2 secondary code       |

---

## 6. CICS Commands Used

| Command                | Location (Paragraph)             | Purpose                                          |
|------------------------|----------------------------------|--------------------------------------------------|
| EXEC CICS RETURN       | MAIN-PARA (line 107)             | Pseudo-conversational return with COMMAREA       |
| EXEC CICS XCTL         | RETURN-TO-PREV-SCREEN (line 175) | Transfer control to COADM01C or COSGN00C        |
| EXEC CICS SEND MAP     | SEND-USRADD-SCREEN (line 190)    | Send COUSR1A map with ERASE and CURSOR          |
| EXEC CICS RECEIVE MAP  | RECEIVE-USRADD-SCREEN (line 203) | Receive input from COUSR1A                      |
| EXEC CICS WRITE        | WRITE-USER-SEC-FILE (line 240)   | Write new record to USRSEC                      |

---

## 7. Program Flow — Paragraph-by-Paragraph

### MAIN-PARA (lines 71–110)

Entry point. Clears WS-MESSAGE and ERRMSGO. Sets ERR-FLG-OFF.

**EIBCALEN = 0:** XCTL to COSGN00C (direct invocation guard).

**First programmatic entry (NOT CDEMO-PGM-REENTER):**
1. Sets CDEMO-PGM-REENTER.
2. Initializes COUSR0AO to LOW-VALUES.
3. Sets FNAMEL = -1 (cursor on First Name field).
4. Calls SEND-USRADD-SCREEN to present blank form.

**Re-entry (CDEMO-PGM-REENTER):**
Receives screen, then dispatches on EIBAID:
- DFHENTER → PROCESS-ENTER-KEY (validate and write)
- DFHPF3 → RETURN-TO-PREV-SCREEN targeting COADM01C
- DFHPF4 → CLEAR-CURRENT-SCREEN (clear all fields)
- OTHER → invalid key error, re-display screen

Terminates with EXEC CICS RETURN TRANSID('CU01') COMMAREA(CARDDEMO-COMMAREA).

### PROCESS-ENTER-KEY (lines 115–160)

Sequential field validation using EVALUATE TRUE (first failing condition wins):

1. FNAMEI = SPACES or LOW-VALUES → 'First Name can NOT be empty...' ; cursor to FNAMEL.
2. LNAMEI = SPACES or LOW-VALUES → 'Last Name can NOT be empty...' ; cursor to LNAMEL.
3. USERIDI = SPACES or LOW-VALUES → 'User ID can NOT be empty...' ; cursor to USERIDL.
4. PASSWDI = SPACES or LOW-VALUES → 'Password can NOT be empty...' ; cursor to PASSWDL.
5. USRTYPEI = SPACES or LOW-VALUES → 'User Type can NOT be empty...' ; cursor to USRTYPEL.
6. WHEN OTHER: sets cursor to FNAMEL, CONTINUEs (no error).

Each failing branch sets ERR-FLG-ON ('Y') and calls SEND-USRADD-SCREEN, stopping further validation.

If NOT ERR-FLG-ON after the EVALUATE:
- Moves USERIDI → SEC-USR-ID (VSAM key)
- Moves FNAMEI  → SEC-USR-FNAME
- Moves LNAMEI  → SEC-USR-LNAME
- Moves PASSWDI → SEC-USR-PWD
- Moves USRTYPEI → SEC-USR-TYPE
- Calls WRITE-USER-SEC-FILE

### RETURN-TO-PREV-SCREEN (lines 165–178)

If CDEMO-TO-PROGRAM blank, defaults to COSGN00C. Sets CDEMO-FROM-TRANID='CU01', CDEMO-FROM-PROGRAM='COUSR01C', zeros CDEMO-PGM-CONTEXT. Issues EXEC CICS XCTL.

### SEND-USRADD-SCREEN (lines 184–196)

Calls POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO, then issues EXEC CICS SEND MAP('COUSR1A') MAPSET('COUSR01') FROM(COUSR1AO) ERASE CURSOR. Note: ERASE is always used; there is no conditional erase path for this program (unlike COUSR00C).

### RECEIVE-USRADD-SCREEN (lines 201–209)

Issues EXEC CICS RECEIVE MAP('COUSR1A') MAPSET('COUSR01') INTO(COUSR1AI) RESP(WS-RESP-CD) RESP2(WS-REAS-CD).

### POPULATE-HEADER-INFO (lines 214–233)

Same pattern as COUSR00C. Populates TITLE01O, TITLE02O, TRNNAMEO='CU01', PGMNAMEO='COUSR01C', date (MM/DD/YY), time (HH:MM:SS).

### WRITE-USER-SEC-FILE (lines 238–274)

Issues EXEC CICS WRITE DATASET('USRSEC') FROM(SEC-USER-DATA) LENGTH(80) RIDFLD(SEC-USR-ID) KEYLENGTH(8).

Response handling:
- DFHRESP(NORMAL): calls INITIALIZE-ALL-FIELDS, sets ERRMSGC to DFHGREEN, builds confirmation message 'User &lt;id&gt; has been added ...', calls SEND-USRADD-SCREEN.
- DFHRESP(DUPKEY) or DFHRESP(DUPREC): sets ERR-FLG-ON, displays 'User ID already exist...', cursor to USERIDL.
- OTHER: sets ERR-FLG-ON, displays 'Unable to Add User...', cursor to FNAMEL.

### CLEAR-CURRENT-SCREEN (lines 279–282)

Calls INITIALIZE-ALL-FIELDS then SEND-USRADD-SCREEN.

### INITIALIZE-ALL-FIELDS (lines 287–295)

Sets FNAMEL = -1 (cursor anchor). Clears USERIDI, FNAMEI, LNAMEI, PASSWDI, USRTYPEI, and WS-MESSAGE to SPACES.

---

## 8. Inter-Program Interactions

| Direction | Target Program | Mechanism | Condition                              |
|-----------|---------------|-----------|----------------------------------------|
| Inbound   | COADM01C      | XCTL → CU01 | Admin menu 'Add User' option         |
| Outbound  | COADM01C      | XCTL      | PF3 pressed (back to admin menu)       |
| Outbound  | COSGN00C      | XCTL      | EIBCALEN=0 or CDEMO-TO-PROGRAM blank   |

COUSR01C does not receive a pre-selected user from any calling program (unlike COUSR02C/COUSR03C). The COMMAREA extension fields (CDEMO-CU00-INFO etc.) are not populated by the caller; the program starts with a blank form.

---

## 9. Error Handling

| Error Condition             | Response                                            | Color   |
|-----------------------------|-----------------------------------------------------|---------|
| First Name blank            | 'First Name can NOT be empty...' ; cursor on FNAME  | Default |
| Last Name blank             | 'Last Name can NOT be empty...' ; cursor on LNAME   | Default |
| User ID blank               | 'User ID can NOT be empty...' ; cursor on USERID    | Default |
| Password blank              | 'Password can NOT be empty...' ; cursor on PASSWD   | Default |
| User Type blank             | 'User Type can NOT be empty...' ; cursor on USRTYPE | Default |
| Duplicate key (DUPKEY/DUPREC) | 'User ID already exist...' ; cursor on USERID     | Default |
| WRITE other error           | 'Unable to Add User...' ; cursor on FNAME           | Default |
| Invalid AID key             | CCDA-MSG-INVALID-KEY                               | Default |
| Successful write            | 'User &lt;id&gt; has been added ...'                | DFHGREEN |
| EIBCALEN = 0                | XCTL to COSGN00C                                   | N/A     |

---

## 10. Business Rules

| Rule                                            | Source Location (line)            |
|-------------------------------------------------|-----------------------------------|
| All five fields are mandatory (no partial saves) | PROCESS-ENTER-KEY, lines 117–151 |
| Validation is sequential; first failing field stops further checks | EVALUATE TRUE, line 117 |
| Password is stored in plaintext (no encryption) | WRITE-USER-SEC-FILE, line 240; CSUSR01Y.cpy SEC-USR-PWD PIC X(08) |
| Duplicate User ID (same key) is rejected        | WRITE-USER-SEC-FILE, lines 260–266 |
| User Type must be non-blank but value is not range-checked (A/U enforcement is not in this program) | PROCESS-ENTER-KEY, lines 142–147 |
| After successful add, the form is cleared and stays on screen (user can add another) | WRITE-USER-SEC-FILE, line 252 |
| PF4 clears the form without saving              | CLEAR-CURRENT-SCREEN, line 280 |

---

## 11. Transaction Flow Context

```
COADM01C (Admin Menu) --[CU01 transaction]--> COUSR01C (Add User)
                                                    |
                                           [ENTER: validate + write]
                                                    |
                            +-------success---------+-------failure-------+
                            |                                             |
                    form cleared; confirmation msg              error msg; form stays
                    (stay on COUSR01C)                         (stay on COUSR01C)
                            |
                         [PF3] Back
                            |
                        COADM01C
```

---

## 12. Open Questions and Gaps

- The User Type field accepts any single non-blank character. The BMS map instruction text shows '(A=Admin, U=User)' but the program does not enforce this constraint in PROCESS-ENTER-KEY. An operator could insert 'X' as a user type without error. **Confidence: HIGH.**
- Password is stored in plaintext (SEC-USR-PWD PIC X(08)). There is no hashing or masking at the COBOL layer. The BMS field PASSWD has ATTRB=DRK (dark/non-display) to prevent shoulder-surfing on the terminal, but the stored value is readable. **Confidence: HIGH.**
- RECEIVE MAP response codes (WS-RESP-CD / WS-REAS-CD) are captured (line 207) but never evaluated. A failed receive is silently ignored.
