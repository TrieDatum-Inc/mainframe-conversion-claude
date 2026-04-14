# Technical Specification: COUSR00C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COUSR00C                                             |
| Source File      | app/cbl/COUSR00C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CU00 (WS-TRANID, line 37)                            |
| Function         | User list/browse screen (admin function). Displays up to 10 user records per page from the USRSEC VSAM KSDS file, using STARTBR/READNEXT/READPREV for forward/backward pagination. An optional user ID filter (USRIDINI) limits results to IDs >= the entered value. Row selection 'U'/'u' XCTLs to COUSR02C (update user); 'D'/'d' XCTLs to COUSR03C (delete user). PF3 returns to COADM01C (admin menu — not COMEN01C). Admin-only function. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CU00 and COMMAREA)

Clear WS-MESSAGE; SET ERR-FLG-OFF

IF EIBCALEN = 0:
    MOVE 'COSGN00C' TO CDEMO-FROM-PROGRAM
    PERFORM RETURN-TO-PREV-SCREEN

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO COUSR0AO
        PERFORM SEND-USRLST-SCREEN (initial display)
    ELSE:
        PERFORM RECEIVE-USRLST-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER:  PERFORM PROCESS-ENTER-KEY
            WHEN DFHPF3:    MOVE 'COADM01C' TO CDEMO-TO-PROGRAM
                            PERFORM RETURN-TO-PREV-SCREEN
            WHEN DFHPF7:    PERFORM PROCESS-PF7-KEY (previous page)
            WHEN DFHPF8:    PERFORM PROCESS-PF8-KEY (next page)
            WHEN OTHER:     Set ERR-FLG-ON; CCDA-MSG-INVALID-KEY; SEND-USRLST-SCREEN

EXEC CICS RETURN TRANSID('CU00') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph               | Lines     | Description |
|-------------------------|-----------|-------------|
| MAIN-PARA               | 79–128    | Main entry: EIBCALEN check; first/reenter dispatch; AID evaluate; CICS RETURN |
| PROCESS-ENTER-KEY       | 133–213   | Scan SEL-FLAG fields for 'U'/'u' or 'D'/'d'; set CDEMO-CU00-USR-SELECTED; XCTL to COUSR02C or COUSR03C; else re-populate and send screen |
| PROCESS-PF7-KEY         | 218–246   | Set direction=backward; POPULATE-USER-DATA reading backward; send screen |
| PROCESS-PF8-KEY         | 251–279   | Set direction=forward; POPULATE-USER-DATA reading forward; send screen |
| RETURN-TO-PREV-SCREEN   | 284–294   | CDEMO-TO-PROGRAM defaulted if blank; EXEC CICS XCTL |
| SEND-USRLST-SCREEN      | 299–315   | POPULATE-HEADER-INFO; POPULATE-USER-DATA; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('COUSR0A') MAPSET('COUSR00') FROM(COUSR0AO) ERASE |
| RECEIVE-USRLST-SCREEN   | 320–330   | CICS RECEIVE MAP('COUSR0A') MAPSET('COUSR00') INTO(COUSR0AI) RESP RESP2 |
| POPULATE-HEADER-INFO    | 335–355   | Fill header fields |
| POPULATE-USER-DATA      | 360–520   | STARTBR USRSEC; READNEXT/READPREV for up to 10 rows; look-ahead READNEXT; ENDBR; fill COUSR0AO array fields (USRID1O–USRID10O, FNAME1O–FNAME10O, LNAME1O–LNAME10O, UTYPE1O–UTYPE10O) |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 50) | CARDDEMO-COMMAREA: standard commarea; extended inline with CDEMO-CU00-INFO |
| COUSR00  | WORKING-STORAGE (line 52)  | BMS mapset copybook: COUSR0AI (input map), COUSR0AO (output map); contains USRIDINI, SEL0001I–SEL0010I, USRID1O–USRID10O, FNAME1O–FNAME10O, LNAME1O–LNAME10O, UTYPE1O–UTYPE10O, ERRMSGO, header fields |
| CSUSR01Y  | WORKING-STORAGE (line 54) | SEC-USR-ID, SEC-USR-PWD, SEC-USR-FNAME, SEC-USR-LNAME, SEC-USR-TYPE — USRSEC record layout |
| COTTL01Y  | WORKING-STORAGE (line 56) | Screen title constants |
| CSDAT01Y  | WORKING-STORAGE (line 57) | Current date/time |
| CSMSG01Y  | WORKING-STORAGE (line 58) | Common messages |
| DFHAID    | WORKING-STORAGE (line 60) | EIBAID constants: DFHENTER, DFHPF3, DFHPF7, DFHPF8 |
| DFHBMSCA  | WORKING-STORAGE (line 61) | BMS attribute bytes |

### COMMAREA Extension (inline after COPY COCOM01Y)

| Field              | PIC       | Purpose |
|--------------------|-----------|---------|
| CDEMO-CU00-INFO    | Group     | CU00-specific commarea fields |
| CDEMO-CU00-USRID-FIRST | X(08) | First user ID on current page (backward browse anchor) |
| CDEMO-CU00-USRID-LAST  | X(08) | Last user ID on current page (forward browse anchor) |
| CDEMO-CU00-PAGE-NUM    | 9(08)  | Current page number |
| CDEMO-CU00-NEXT-PAGE-FLG | X(01) | 'Y'=more pages forward |
| CDEMO-CU00-USR-SEL-FLG | X(01)  | 'Y'=a row was selected |
| CDEMO-CU00-USR-SELECTED | X(08) | User ID of selected row; passed to COUSR02C or COUSR03C |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| WS-PGMNAME           | X(08) = 'COUSR00C' | Program name for header |
| WS-TRANID            | X(04) = 'CU00' | Transaction ID |
| WS-MESSAGE           | X(80)     | User-visible message |
| WS-ERR-FLG           | X(01)     | Error flag |
| WS-USRSEC-FILE       | X(08) = 'USRSEC  ' | CICS file name |
| WS-USR-ID-SRCH       | X(08)     | User ID used as STARTBR RIDFLD (from USRIDINI filter or pagination anchor) |
| WS-BROWSE-DIR        | X(01)     | 'F'=forward (READNEXT), 'B'=backward (READPREV) |
| WS-PAGE-NUM          | 9(08)     | Current page number |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS RETURN TRANSID('CU00') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM('COUSR02C') COMMAREA | PROCESS-ENTER-KEY | Transfer to user update (selection 'U') |
| EXEC CICS XCTL PROGRAM('COUSR03C') COMMAREA | PROCESS-ENTER-KEY | Transfer to user delete (selection 'D') |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | RETURN-TO-PREV-SCREEN | PF3 return to COADM01C |
| EXEC CICS SEND MAP('COUSR0A') MAPSET('COUSR00') FROM(COUSR0AO) ERASE | SEND-USRLST-SCREEN | Display user list |
| EXEC CICS RECEIVE MAP('COUSR0A') MAPSET('COUSR00') INTO(COUSR0AI) RESP RESP2 | RECEIVE-USRLST-SCREEN | Receive selection and filter input |
| EXEC CICS STARTBR FILE(WS-USRSEC-FILE) RIDFLD(WS-USR-ID-SRCH) RESP RESP2 | POPULATE-USER-DATA | Begin browse at filter key or pagination anchor |
| EXEC CICS READNEXT FILE(WS-USRSEC-FILE) INTO(CDEMO-USRSEC-REC) RIDFLD(WS-USR-ID) RESP RESP2 | POPULATE-USER-DATA | Read forward through USRSEC |
| EXEC CICS READPREV FILE(WS-USRSEC-FILE) INTO(CDEMO-USRSEC-REC) RIDFLD(WS-USR-ID) RESP RESP2 | POPULATE-USER-DATA (backward) | Read backward through USRSEC |
| EXEC CICS ENDBR FILE(WS-USRSEC-FILE) | POPULATE-USER-DATA | End browse |

---

## 5. File/Dataset Access

| File Name | CICS File | Access Type | Key              | Purpose |
|-----------|-----------|-------------|------------------|---------|
| USRSEC    | USRSEC    | STARTBR/READNEXT/READPREV/ENDBR | WS-USR-ID-SRCH X(08) | Browse user security records for display |

**Browse pattern:**
- STARTBR key = USRIDINI filter value (if entered) or LOW-VALUES (first page) or CDEMO-CU00-USRID-LAST (next page) or CDEMO-CU00-USRID-FIRST (prior page)
- STARTBR does not use GTEQ
- Fill up to 10 rows READNEXT (forward) or READPREV (backward)
- One look-ahead READNEXT after 10th row to set CDEMO-CU00-NEXT-PAGE-FLG
- ENDBR after each browse

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COUSR00    | COUSR0A | CU00        |

**Key Screen Fields:**

| Field              | Direction | Description |
|--------------------|-----------|-------------|
| USRIDINI           | Input     | Optional user ID filter (start browse at this key) |
| SEL0001I–SEL0010I  | Input     | Row selection flags: 'U'/'u'=update, 'D'/'d'=delete |
| USRID1O–USRID10O   | Output    | User IDs for displayed rows |
| FNAME1O–FNAME10O   | Output    | First names |
| LNAME1O–LNAME10O   | Output    | Last names |
| UTYPE1O–UTYPE10O   | Output    | User types ('A'=Admin, 'R'=Regular) |
| ERRMSGO            | Output    | WS-MESSAGE: error or status |
| TITLE01O–CURTIMEO  | Output    | Standard header fields |

**Navigation:**
- ENTER: process row selection (U=update, D=delete)
- PF3: XCTL to COADM01C (admin menu — hardcoded, not CDEMO-FROM-PROGRAM)
- PF7: previous page
- PF8: next page
- Other keys: CCDA-MSG-INVALID-KEY

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| COUSR02C   | CICS XCTL   | Row selected with 'U'/'u'; CDEMO-CU00-USR-SELECTED set to user ID |
| COUSR03C   | CICS XCTL   | Row selected with 'D'/'d'; CDEMO-CU00-USR-SELECTED set to user ID |
| COADM01C   | CICS XCTL   | PF3 pressed (hardcoded CDEMO-TO-PROGRAM='COADM01C') |
| COSGN00C   | CICS XCTL   | EIBCALEN=0 (default CDEMO-FROM-PROGRAM when not set) |

**COMMAREA passed to COUSR02C/COUSR03C:**
- CDEMO-CU00-USR-SELECTED = selected SEC-USR-ID (8 bytes)
- CDEMO-FROM-PROGRAM = 'COUSR00C'
- CDEMO-FROM-TRANID = 'CU00'

**Admin-only routing note**: PF3 always XCTLs to COADM01C regardless of CDEMO-FROM-PROGRAM. This reflects that COUSR00C is an admin-only function always reached from the admin menu (COADM01C).

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C |
| STARTBR RESP = NOTFND | Display 'No users found' message; empty list |
| STARTBR other RESP | Display error with RESP/RESP2; re-send map |
| READNEXT/READPREV AT END | Normal — stop filling rows; set NEXT-PAGE-FLG |
| Invalid selection code (not 'U', 'u', 'D', 'd') | ERR-FLG-ON; 'Invalid selection' message; re-send map |
| Multiple rows selected | First selected row processed; [UNRESOLVED] — behavior with multiple simultaneous selections not explicitly documented |
| Invalid AID key | ERR-FLG-ON; CCDA-MSG-INVALID-KEY; re-send map |

---

## 9. Business Rules

1. **Admin-only function**: COUSR00C is accessible only from COADM01C (admin menu). Regular users cannot reach it. PF3 always returns to COADM01C.
2. **10 users per page**: POPULATE-USER-DATA fills up to 10 rows. Look-ahead READNEXT after the 10th record determines CDEMO-CU00-NEXT-PAGE-FLG.
3. **Two selection operations**: Unlike COTRN00C (which has only 'S' for view), COUSR00C supports two selection codes: 'U' for update (→COUSR02C) and 'D' for delete (→COUSR03C).
4. **USRIDINI filter**: If entered, STARTBR begins at the supplied user ID (exact or next higher). The filter is only applied on ENTER; PF7/PF8 use the pagination anchors.
5. **Pagination state in COMMAREA**: CDEMO-CU00-USRID-FIRST and CDEMO-CU00-USRID-LAST stored in commarea enable accurate STARTBR repositioning on PF7/PF8.
6. **User data display**: For each row, USRID, FNAME, LNAME, and UTYPE are displayed. SEC-USR-PWD is never displayed.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COUSR0A) | USRIDINI (filter), SEL0001I–SEL0010I (row selections) |
| COMMAREA  | CDEMO-CU00-INFO (pagination anchors, next-page flag) |
| USRSEC VSAM file | User records: ID, first/last name, type (password not displayed) |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COUSR0A) | User list: up to 10 rows with user ID, first name, last name, user type |
| COMMAREA   | CDEMO-CU00-USRID-FIRST, CDEMO-CU00-USRID-LAST (pagination anchors); CDEMO-CU00-USR-SELECTED (for COUSR02C/COUSR03C); CDEMO-CU00-NEXT-PAGE-FLG |

---

## 11. Key Variables and Their Purpose

| Variable                  | Purpose |
|---------------------------|---------|
| WS-USR-ID-SRCH            | STARTBR RIDFLD; set to USRIDINI (filter), LOW-VALUES (first page), or pagination anchor |
| WS-BROWSE-DIR             | 'F'=READNEXT, 'B'=READPREV; controls browse direction |
| CDEMO-CU00-USRID-FIRST    | First user ID on current page; STARTBR anchor for PF7 |
| CDEMO-CU00-USRID-LAST     | Last user ID on current page; STARTBR anchor for PF8 |
| CDEMO-CU00-NEXT-PAGE-FLG  | 'Y'/'N'; determined by look-ahead READNEXT |
| CDEMO-CU00-USR-SELECTED   | User ID of selected row; passed to COUSR02C or COUSR03C via COMMAREA |
| SEC-USR-ID/FNAME/LNAME/TYPE | Fields from USRSEC record mapped to screen output columns |
