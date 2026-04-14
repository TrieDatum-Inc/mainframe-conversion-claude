# Technical Specification: COCRDUPC

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COCRDUPC                                             |
| Source File      | app/cbl/COCRDUPC.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CCUP (LIT-THISTRANID, line 222)                      |
| Function         | Accepts and processes credit card field updates. Supports a multi-step workflow: (1) search by account ID + card number, (2) display current card data, (3) user edits name/status/expiry month/year, (4) program validates changes and prompts for PF5 confirmation, (5) PF5 triggers optimistic-locking read-update-rewrite sequence on CARDDAT. Detects concurrent modification between display and save. Name must be alpha-only; status must be Y/N; month must be 1–12; year must be 1950–2099. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CCUP and COMMAREA)

EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE)

INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA
SET WS-RETURN-MSG-OFF

IF EIBCALEN = 0 OR (FROM-PROGRAM = COMEN01C AND NOT CDEMO-PGM-REENTER):
    INITIALIZE CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA
    SET CDEMO-PGM-ENTER, CCUP-DETAILS-NOT-FETCHED

ELSE:
    MOVE DFHCOMMAREA to CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA

PERFORM YYYY-STORE-PFKEY

Valid AIDs: ENTER, PF03, (PF05 when CCUP-CHANGES-OK-NOT-CONFIRMED), (PF12 when NOT CCUP-DETAILS-NOT-FETCHED)
Others: treat as ENTER

EVALUATE TRUE:

    WHEN PF03
    OR (CCUP-CHANGES-OKAYED-AND-DONE AND from COCRDLIC mapset)
    OR (CCUP-CHANGES-FAILED AND from COCRDLIC mapset):
        EXEC CICS SYNCPOINT
        XCTL to CDEMO-FROM-PROGRAM (or COMEN01C)

    WHEN CDEMO-PGM-ENTER AND FROM-PROGRAM = COCRDLIC
    OR PF12 AND FROM-PROGRAM = COCRDLIC:
        Use CDEMO-ACCT-ID/CARD-NUM from COMMAREA
        PERFORM 9000-READ-DATA
        SET CCUP-SHOW-DETAILS
        PERFORM 3000-SEND-MAP; GO TO COMMON-RETURN

    WHEN CCUP-DETAILS-NOT-FETCHED AND CDEMO-PGM-ENTER
    OR FROM-PROGRAM = COMEN01C AND NOT CDEMO-PGM-REENTER:
        INITIALIZE WS-THIS-PROGCOMMAREA
        PERFORM 3000-SEND-MAP (blank search form)
        SET CDEMO-PGM-REENTER, CCUP-DETAILS-NOT-FETCHED
        GO TO COMMON-RETURN

    WHEN CCUP-CHANGES-OKAYED-AND-DONE OR CCUP-CHANGES-FAILED:
        INITIALIZE WS-THIS-PROGCOMMAREA; CDEMO-ACCT-ID/CARD-NUM
        SET CDEMO-PGM-ENTER
        PERFORM 3000-SEND-MAP (blank search form)
        SET CDEMO-PGM-REENTER, CCUP-DETAILS-NOT-FETCHED
        GO TO COMMON-RETURN

    WHEN OTHER (normal re-entry with data shown):
        PERFORM 1000-PROCESS-INPUTS (receive map, validate)
        PERFORM 2000-DECIDE-ACTION
        PERFORM 3000-SEND-MAP
        GO TO COMMON-RETURN

COMMON-RETURN:
    CICS RETURN TRANSID('CCUP') COMMAREA(WS-COMMAREA)
```

### Multi-Step Workflow State Machine

The workflow state is tracked in CCUP-CHANGE-ACTION (PIC X(1) within WS-THIS-PROGCOMMAREA):

| State Value | 88-Level Name | Meaning |
|-------------|---------------|---------|
| LOW-VALUES / SPACES | CCUP-DETAILS-NOT-FETCHED | Initial state; no card fetched yet |
| 'S' | CCUP-SHOW-DETAILS | Card data retrieved and displayed; user can edit |
| 'E' | CCUP-CHANGES-NOT-OK | User submitted changes but validation failed |
| 'N' | CCUP-CHANGES-OK-NOT-CONFIRMED | Changes valid; waiting for PF5 confirmation |
| 'C' | CCUP-CHANGES-OKAYED-AND-DONE | PF5 pressed; update succeeded |
| 'L' | CCUP-CHANGES-OKAYED-LOCK-ERROR | PF5 pressed; READ UPDATE failed to lock |
| 'F' | CCUP-CHANGES-OKAYED-BUT-FAILED | PF5 pressed; REWRITE failed |

### Paragraph-Level Detail

| Paragraph               | Lines       | Description |
|-------------------------|-------------|-------------|
| 0000-MAIN               | 367–544     | Entry: HANDLE ABEND; initialize; commarea load; YYYY-STORE-PFKEY; AID validate; EVALUATE dispatch |
| COMMON-RETURN           | 546–559     | Set CCARD-ERROR-MSG; serialize COMMAREA; CICS RETURN TRANSID('CCUP') |
| 1000-PROCESS-INPUTS     | 564–577     | Calls 1100-RECEIVE-MAP, 1200-EDIT-MAP-INPUTS; sets CCARD-ERROR-MSG/NEXT-PROG/MAPSET/MAP |
| 1100-RECEIVE-MAP        | 578–638     | CICS RECEIVE MAP INTO(CCRDUPAI); cleanse '*'/spaces → LOW-VALUES; collect ACCTID, CARDID, CRDNAME, CRDSTCD, EXPDAY, EXPMON, EXPYEAR into CCUP-NEW-DETAILS |
| 1200-EDIT-MAP-INPUTS    | 641–718     | Two branches: (1) if CCUP-DETAILS-NOT-FETCHED: validate search keys (1210/1220) only; (2) else: load old data from CCUP-OLD-DETAILS; compare new vs. old (FUNCTION UPPER-CASE); if identical: NO-CHANGES-DETECTED; if already confirmed: skip edits; else: SET CCUP-CHANGES-NOT-OK; validate name(1230)/status(1240)/month(1250)/year(1260) |
| 1210-EDIT-ACCOUNT       | 721–758     | Account required; blank/zero = FLG-ACCTFILTER-BLANK + INPUT-ERROR; non-numeric = INPUT-ERROR + error message; else FLG-ACCTFILTER-ISVALID |
| 1220-EDIT-CARD          | 762–803     | Card required; blank/zero = FLG-CARDFILTER-BLANK + INPUT-ERROR; non-numeric = INPUT-ERROR; else FLG-CARDFILTER-ISVALID |
| 1230-EDIT-NAME          | 806–843     | Card name required; blank = FLG-CARDNAME-BLANK + INPUT-ERROR; alpha check: INSPECT CONVERTING LIT-ALL-ALPHA-FROM TO spaces; if TRIM length > 0 non-space remains = INPUT-ERROR + WS-NAME-MUST-BE-ALPHA |
| 1240-EDIT-CARDSTATUS    | 845–875     | Status required; blank = FLG-CARDSTATUS-BLANK + INPUT-ERROR; must be Y or N (FLG-YES-NO-VALID 88-level); else INPUT-ERROR + CARD-STATUS-MUST-BE-YES-NO |
| 1250-EDIT-EXPIRY-MON    | 877–912     | Month required; blank = FLG-CARDEXPMON-BLANK + INPUT-ERROR; must be 1-12 (VALID-MONTH 88-level); else INPUT-ERROR + CARD-EXPIRY-MONTH-NOT-VALID |
| 1260-EDIT-EXPIRY-YEAR   | 913–946     | Year required; blank = FLG-CARDEXPYEAR-BLANK + INPUT-ERROR; must be 1950-2099 (VALID-YEAR 88-level); else INPUT-ERROR + CARD-EXPIRY-YEAR-NOT-VALID |
| 2000-DECIDE-ACTION      | 948–1031    | EVALUATE on CCUP-CHANGE-ACTION: CCUP-DETAILS-NOT-FETCHED → read data; PF12 → re-read and show; CCUP-SHOW-DETAILS → if no errors and changes: SET CCUP-CHANGES-OK-NOT-CONFIRMED; CCUP-CHANGES-OK-NOT-CONFIRMED AND PF05 → PERFORM 9200-WRITE-PROCESSING; evaluate result; CCUP-CHANGES-OKAYED-AND-DONE → reset keys; OTHER → PERFORM ABEND-ROUTINE |
| 3000-SEND-MAP           | 1035–1050   | Calls 3100 → 3200 → 3250 → 3300 → 3400 |
| 3100-SCREEN-INIT        | 1052–1080   | LOW-VALUES to CCRDUPAO; fill title, tran, pgm, date, time |
| 3200-SETUP-SCREEN-VARS  | 1082–1137   | Populate account/card/name/status/expiry fields on screen based on CCUP state; show old values in CCUP-SHOW-DETAILS state, new values in CCUP-CHANGES-MADE states |
| 3250-SETUP-INFOMSG      | 1138–1165   | Set WS-INFO-MSG 88-level based on state: PROMPT-FOR-SEARCH-KEYS / FOUND-CARDS-FOR-ACCOUNT / PROMPT-FOR-CHANGES / PROMPT-FOR-CONFIRMATION / CONFIRM-UPDATE-SUCCESS / INFORM-FAILURE |
| 3300-SETUP-SCREEN-ATTRS | 1168–1319   | Protect/unprotect fields per state; position cursor; highlight error fields red; set FKEYSC bright yellow on confirmation prompt |
| 3400-SEND-SCREEN        | 1324–1339   | CICS SEND MAP(CCRDUPA) MAPSET(COCRDUP) FROM(CCRDUPAO) CURSOR ERASE FREEKB |
| 9000-READ-DATA          | 1343–1374   | Initialize CCUP-OLD-DETAILS; PERFORM 9100-GETCARD-BYACCTCARD; if found: populate CCUP-OLD-CRDNAME, CCUP-OLD-EXPYEAR/MON/DAY, CCUP-OLD-CRDSTCD, CCUP-OLD-CVV-CD; INSPECT CONVERTING lower to upper on CARD-EMBOSSED-NAME |
| 9100-GETCARD-BYACCTCARD | 1376–1416   | READ CARDDAT FILE by WS-CARD-RID-CARDNUM; NORMAL: FOUND-CARDS-FOR-ACCOUNT; NOTFND: INPUT-ERROR + both filter flags not-ok + DID-NOT-FIND-ACCTCARD-COMBO; OTHER: error |
| 9200-WRITE-PROCESSING   | 1420–1495   | READ CARDDAT UPDATE by card number; if lock fails: COULD-NOT-LOCK-FOR-UPDATE; PERFORM 9300-CHECK-CHANGE-IN-REC; if changed: DATA-WAS-CHANGED-BEFORE-UPDATE; else: build CARD-UPDATE-RECORD; EXEC CICS REWRITE; if rewrite fails: LOCKED-BUT-UPDATE-FAILED |
| 9300-CHECK-CHANGE-IN-REC | 1498–1523  | Compare locked record to CCUP-OLD-DETAILS (CVV-CD, name, expiry year/month/day, status); if any mismatch: SET DATA-WAS-CHANGED-BEFORE-UPDATE; refresh CCUP-OLD-DETAILS from file |
| YYYY-STORE-PFKEY        | (COPY 'CSSTRPFY', line 1528) | Common PF key mapping |
| ABEND-ROUTINE           | 1531–1556   | CICS SEND FROM(ABEND-DATA) NOHANDLE ERASE; CICS HANDLE ABEND CANCEL; EXEC CICS ABEND ABCODE('9999') |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook   | Used In              | Contents |
|------------|----------------------|----------|
| CVCRD01Y   | WORKING-STORAGE (line 268) | CC-WORK-AREA: CC-ACCT-ID X(11)/N, CC-CARD-NUM X(16)/N, FOUND-CARDS-FOR-ACCOUNT flag |
| COCOM01Y   | WORKING-STORAGE (line 272) | CARDDEMO-COMMAREA: CDEMO-FROM-PROGRAM, CDEMO-FROM-TRANID, CDEMO-ACCT-ID, CDEMO-CARD-NUM, CDEMO-PGM-ENTER/REENTER, CDEMO-LAST-MAPSET, CDEMO-TO-PROGRAM, CDEMO-TO-TRANID |
| DFHBMSCA   | WORKING-STORAGE (line 327) | BMS attribute byte constants: DFHBMPRF, DFHBMFSE, DFHRED, DFHDFCOL, DFHBMDAR, DFHBMBRY |
| DFHAID     | WORKING-STORAGE (line 328) | EIBAID constants |
| COTTL01Y   | WORKING-STORAGE (line 332) | CCDA-TITLE01, CCDA-TITLE02 title constants |
| COCRDUP    | WORKING-STORAGE (line 334) | BMS mapset: CCRDUPAI (input), CCRDUPAO (output); contains ACCTSIDI/O/A/C/L, CARDSIDI/O/A/C/L, CRDNAMEI/O/A/C/L, CRDSTCDI/O/A/C/L, EXPDAYI/O/A/C, EXPMONI/O/A/C/L, EXPYEARI/O/A/C/L, ERRMSGO, INFOMSGO/A, FKEYSCO/A, TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO |
| CSDAT01Y   | WORKING-STORAGE (line 337) | Current date/time working variables |
| CSMSG01Y   | WORKING-STORAGE (line 340) | Common messages |
| CSMSG02Y   | WORKING-STORAGE (line 343) | ABEND-DATA structure: ABEND-CULPRIT, ABEND-CODE, ABEND-REASON, ABEND-MSG |
| CSUSR01Y   | WORKING-STORAGE (line 346) | Signed-on user data |
| CVACT02Y   | WORKING-STORAGE (line 353) | CARD-RECORD layout |
| CVCUS01Y   | WORKING-STORAGE (line 359) | Customer record layout (copied but not directly referenced in PROCEDURE DIVISION) |

### Key Working Storage Variables

| Variable                      | PIC / Structure | Purpose |
|-------------------------------|-----------------|---------|
| LIT-THISTRANID                | X(4) = 'CCUP'   | Transaction ID for CICS RETURN |
| LIT-THISPGM                   | X(8) = 'COCRDUPC' | Program name constant |
| LIT-CARDFILENAME              | X(8) = 'CARDDAT ' | CICS file name for card read/update |
| LIT-CCLISTPGM                 | X(8) = 'COCRDLIC' | Calling list program |
| LIT-MENUPGM                   | X(8) = 'COMEN01C' | Default return target |
| LIT-ALL-ALPHA-FROM            | X(52) | A-Z + a-z; used in INSPECT CONVERTING for alpha validation |
| LIT-ALL-SPACES-TO             | X(52) = SPACES  | Target of INSPECT CONVERTING (replace all alpha with spaces) |
| LIT-UPPER / LIT-LOWER         | X(26)           | Used in INSPECT CONVERTING for uppercasing embossed name |
| CCUP-CHANGE-ACTION            | PIC X(1) within WS-THIS-PROGCOMMAREA | State machine value (see workflow table above) |
| CCUP-OLD-DETAILS              | Group 76 bytes  | Snapshot of card data at fetch time: ACCTID X(11), CARDID X(16), CVV-CD X(3), CRDNAME X(50), EXPYEAR X(4), EXPMON X(2), EXPDAY X(2), CRDSTCD X(1) |
| CCUP-NEW-DETAILS              | Group 76 bytes  | User-entered values from screen (same layout as OLD) |
| CARD-UPDATE-RECORD            | Group 150 bytes | Assembled record for CICS REWRITE: CARD-NUM X(16), ACCT-ID 9(11), CVV-CD 9(3), EMBOSSED-NAME X(50), EXPIRAION-DATE X(10), ACTIVE-STATUS X(1), FILLER X(59) |
| WS-EDIT-CARDNAME-FLAG         | PIC X(1)        | 88 FLG-CARDNAME-NOT-OK, FLG-CARDNAME-ISVALID, FLG-CARDNAME-BLANK |
| WS-EDIT-CARDSTATUS-FLAG       | PIC X(1)        | 88 FLG-CARDSTATUS-NOT-OK, FLG-CARDSTATUS-ISVALID, FLG-CARDSTATUS-BLANK |
| WS-EDIT-CARDEXPMON-FLAG       | PIC X(1)        | 88 FLG-CARDEXPMON-NOT-OK, FLG-CARDEXPMON-ISVALID, FLG-CARDEXPMON-BLANK |
| WS-EDIT-CARDEXPYEAR-FLAG      | PIC X(1)        | 88 FLG-CARDEXPYEAR-NOT-OK, FLG-CARDEXPYEAR-ISVALID, FLG-CARDEXPYEAR-BLANK |
| CARD-NAME-CHECK               | PIC X(50)       | Copy of CCUP-NEW-CRDNAME; INSPECT CONVERTING all alpha chars to spaces; if TRIM = 0 then pure alpha |
| FLG-YES-NO-CHECK              | PIC X(1)        | 88 FLG-YES-NO-VALID VALUES 'Y','N' |
| CARD-MONTH-CHECK              | PIC 9(2)        | 88 VALID-MONTH VALUES 1 THRU 12 |
| CARD-YEAR-CHECK               | PIC 9(4)        | 88 VALID-YEAR VALUES 1950 THRU 2099 |
| WS-RETURN-MSG                 | PIC X(75)       | Error/return message; 88 levels for all error conditions |
| WS-INFO-MSG                   | PIC X(45)       | Informational message; 88 levels: PROMPT-FOR-SEARCH-KEYS, FOUND-CARDS-FOR-ACCOUNT, PROMPT-FOR-CHANGES, PROMPT-FOR-CONFIRMATION, CONFIRM-UPDATE-SUCCESS, INFORM-FAILURE |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE) | 0000-MAIN (line 370) | Install abend handler |
| EXEC CICS RETURN TRANSID('CCUP') COMMAREA(WS-COMMAREA) | COMMON-RETURN (line 554) | Pseudo-conversational return |
| EXEC CICS SYNCPOINT | 0000-MAIN (line 470) | Commit before XCTL to calling program |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | 0000-MAIN (line 473) | PF3 exit or post-completion exit |
| EXEC CICS SEND MAP(CCRDUPA) MAPSET(COCRDUP) FROM(CCRDUPAO) CURSOR ERASE FREEKB | 3400-SEND-SCREEN (line 1329) | Send card update screen |
| EXEC CICS RECEIVE MAP(CCRDUPA) MAPSET(COCRDUP) INTO(CCRDUPAI) | 1100-RECEIVE-MAP (line 579) | Receive user inputs |
| EXEC CICS READ FILE(CARDDAT) RIDFLD KEYLENGTH INTO RESP RESP2 | 9100-GETCARD-BYACCTCARD (line 1382) | Read card for display (non-update) |
| EXEC CICS READ FILE(CARDDAT) UPDATE RIDFLD KEYLENGTH INTO RESP RESP2 | 9200-WRITE-PROCESSING (line 1427) | Lock card record for update |
| EXEC CICS REWRITE FILE(CARDDAT) FROM(CARD-UPDATE-RECORD) LENGTH RESP RESP2 | 9200-WRITE-PROCESSING (line 1477) | Write updated card record |
| EXEC CICS SEND FROM(ABEND-DATA) NOHANDLE ERASE | ABEND-ROUTINE (line 1539) | Display abend information |
| EXEC CICS HANDLE ABEND CANCEL | ABEND-ROUTINE (line 1546) | Cancel abend handler |
| EXEC CICS ABEND ABCODE('9999') | ABEND-ROUTINE (line 1550) | Force abend with code 9999 |

---

## 5. File/Dataset Access

| CICS File Name | Access Type | Purpose |
|----------------|-------------|---------|
| CARDDAT        | READ (non-update) | 9100-GETCARD-BYACCTCARD: read card data for initial display and compare |
| CARDDAT        | READ UPDATE + REWRITE | 9200-WRITE-PROCESSING: lock-read then rewrite with updated fields |

**Key used**: WS-CARD-RID-CARDNUM (16 bytes, card number only). KEYLENGTH = LENGTH OF WS-CARD-RID-CARDNUM (16).

**CARD-UPDATE-RECORD composition** (built before REWRITE, lines 1461–1475):
- CARD-UPDATE-NUM = CCUP-NEW-CARDID (card number, unchanged)
- CARD-UPDATE-ACCT-ID = CC-ACCT-ID-N (account ID, unchanged)
- CARD-UPDATE-CVV-CD = original CARD-CVV-CD-N (CVV not editable by user — old value preserved)
- CARD-UPDATE-EMBOSSED-NAME = CCUP-NEW-CRDNAME
- CARD-UPDATE-EXPIRAION-DATE = STRING CCUP-NEW-EXPYEAR '-' CCUP-NEW-EXPMON '-' CCUP-NEW-EXPDAY (note: day uses CCUP-OLD-EXPDAY since CCUP-NEW-EXPDAY is not editable)
- CARD-UPDATE-ACTIVE-STATUS = CCUP-NEW-CRDSTCD

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COCRDUP    | CCRDUPA | CCUP        |

**Key Screen Fields:**

| Field         | Direction | Description |
|---------------|-----------|-------------|
| ACCTSIDI/O    | I/O       | Account ID (11 digits; protected after initial fetch) |
| CARDSIDI/O    | I/O       | Card number (16 digits; protected after initial fetch) |
| CRDNAMEI/O    | I/O       | Card embossed name (editable when details shown; alpha-only) |
| CRDSTCDI/O    | I/O       | Card active status (Y/N; editable when details shown) |
| EXPDAYI/O     | I/O       | Expiry day (display only; not editable — DFHBMDAR applied; old value always shown) |
| EXPMONI/O     | I/O       | Expiry month (editable when details shown; 1–12) |
| EXPYEARI/O    | I/O       | Expiry year (editable when details shown; 1950–2099) |
| INFOMSGO/A    | Output    | WS-INFO-MSG with state-specific guidance text |
| ERRMSGO       | Output    | WS-RETURN-MSG: validation errors or status |
| FKEYSCO/A     | Output    | Function key row; highlighted bright yellow when PF5 confirmation pending |
| TITLE01O/TITLE02O | Output | Application titles |
| TRNNAMEO      | Output    | Transaction ID (CCUP) |
| PGMNAMEO      | Output    | Program name (COCRDUPC) |
| CURDATEO      | Output    | Current date MM/DD/YY |
| CURTIMEO      | Output    | Current time HH:MM:SS |

**Field Protection by State:**

| State | ACCTID/CARDID | NAME/STATUS/MON/YEAR |
|-------|---------------|----------------------|
| CCUP-DETAILS-NOT-FETCHED | Unprotected (DFHBMFSE) | Protected (DFHBMPRF) |
| CCUP-SHOW-DETAILS / CCUP-CHANGES-NOT-OK | Protected | Unprotected (DFHBMFSE) |
| CCUP-CHANGES-OK-NOT-CONFIRMED / DONE | Protected | Protected |

**Navigation:**
- ENTER: process inputs based on current state
- PF3: exit to calling program (or COMEN01C)
- PF5: confirm and save changes (only valid when CCUP-CHANGES-OK-NOT-CONFIRMED)
- PF12: cancel changes and re-read card data (only valid when NOT CCUP-DETAILS-NOT-FETCHED)
- Other keys: treated as ENTER

---

## 7. Called Programs / Transfers

| Program   | Method       | Condition |
|-----------|--------------|-----------|
| CDEMO-FROM-PROGRAM (or COMEN01C) | CICS XCTL (with SYNCPOINT first) | PF3 pressed; or CCUP-CHANGES-OKAYED-AND-DONE from COCRDLIC; or CCUP-CHANGES-FAILED from COCRDLIC |

No programs are CALLed. COCRDUPC directly reads and rewrites CARDDAT.

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| Account blank/zero | FLG-ACCTFILTER-BLANK; INPUT-ERROR; WS-PROMPT-FOR-ACCT |
| Account non-numeric | FLG-ACCTFILTER-NOT-OK; INPUT-ERROR; 'ACCOUNT FILTER...11 DIGIT NUMBER' |
| Card blank/zero | FLG-CARDFILTER-BLANK; INPUT-ERROR; WS-PROMPT-FOR-CARD |
| Card non-numeric | FLG-CARDFILTER-NOT-OK; INPUT-ERROR; 'CARD ID FILTER...16 DIGIT NUMBER' |
| Card name blank | FLG-CARDNAME-BLANK; INPUT-ERROR; WS-PROMPT-FOR-NAME |
| Card name contains non-alpha chars | FLG-CARDNAME-NOT-OK; INPUT-ERROR; WS-NAME-MUST-BE-ALPHA (tested via INSPECT CONVERTING) |
| Card status not Y/N | FLG-CARDSTATUS-NOT-OK; INPUT-ERROR; CARD-STATUS-MUST-BE-YES-NO |
| Expiry month blank/invalid | FLG-CARDEXPMON-BLANK/NOT-OK; INPUT-ERROR; CARD-EXPIRY-MONTH-NOT-VALID |
| Expiry year blank/invalid | FLG-CARDEXPYEAR-BLANK/NOT-OK; INPUT-ERROR; CARD-EXPIRY-YEAR-NOT-VALID |
| No changes detected | SET NO-CHANGES-DETECTED; stays in CCUP-SHOW-DETAILS state; no error flag but no confirmation prompt either |
| CARDDAT NOTFND on read | INPUT-ERROR; DID-NOT-FIND-ACCTCARD-COMBO; both filter flags not-ok |
| CARDDAT READ UPDATE failure | SET COULD-NOT-LOCK-FOR-UPDATE; CCUP-CHANGES-OKAYED-LOCK-ERROR; INFORM-FAILURE on screen |
| Concurrent modification detected | DATA-WAS-CHANGED-BEFORE-UPDATE; CCUP-OLD-DETAILS refreshed; user returns to CCUP-SHOW-DETAILS to review new values |
| CICS REWRITE failure | SET LOCKED-BUT-UPDATE-FAILED; CCUP-CHANGES-OKAYED-BUT-FAILED; INFORM-FAILURE on screen |
| WHEN OTHER in 2000-DECIDE-ACTION | ABEND-ROUTINE: CICS ABEND('9999') |
| Any unhandled abend | ABEND-ROUTINE: CICS SEND ABEND-DATA; CICS ABEND('9999') |

---

## 9. Business Rules

1. **Multi-step confirmation workflow**: Changes are not saved until PF5 is pressed after the program explicitly prompts 'Changes validated. Press F5 to save' (PROMPT-FOR-CONFIRMATION 88-level). This prevents accidental updates.
2. **Optimistic locking with change detection**: At PF5 time, COCRDUPC does a READ UPDATE and then calls 9300-CHECK-CHANGE-IN-REC to compare the live record with the snapshot taken at display time (CCUP-OLD-DETAILS). If any field differs, the update is aborted, the snapshot is refreshed with the new data, and the user is returned to the review screen. This pattern detects concurrent modification without holding locks between interactions.
3. **Card day not editable**: EXPDAYI is received from the screen but CCUP-NEW-EXPDAY is written as CCUP-OLD-EXPDAY in the CARD-UPDATE-EXPIRAION-DATE STRING (line 1471). The day field is always shown in dark (DFHBMDAR) and commented out of the editable field list (lines 1178, 1185, 1197). This appears to be a design decision to leave the expiry day unchanged.
4. **CVV-CD not editable**: The CVV code is read from the file but only stored in CCUP-OLD-CVV-CD for change detection. It is not displayed on screen and the CARD-UPDATE-RECORD uses the original CVV value from the locked record (CARD-CVV-CD-N).
5. **Alpha-only name validation**: INSPECT CONVERTING replaces all alpha characters (A-Z, a-z) with spaces. If the trimmed result is empty (all were alpha), the name is valid. Non-alpha characters remaining after conversion fail the test.
6. **Name uppercased on fetch**: INSPECT CONVERTING LIT-LOWER TO LIT-UPPER is applied to CARD-EMBOSSED-NAME at read time (9000-READ-DATA line 1356). The displayed old name is always uppercase. The comparison for change detection uses FUNCTION UPPER-CASE on both old and new values (line 680).
7. **SYNCPOINT before exit**: EXEC CICS SYNCPOINT is issued before the PF3 XCTL (line 470) to ensure any held resources are released before transferring control.
8. **Auto-return after success from COCRDLIC**: When the update completes (CCUP-CHANGES-OKAYED-AND-DONE) and the calling mapset is COCRDLI, the program automatically XCTLs back to the calling program without waiting for another user input.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (CCRDUPA) | ACCTSIDI — account ID; CARDSIDI — card number; CRDNAMEI — name; CRDSTCDI — status; EXPMONI — expiry month; EXPYEARI — expiry year |
| COMMAREA  | CDEMO-FROM-PROGRAM/TRANID (navigation); CDEMO-ACCT-ID/CARD-NUM (pre-populated from COCRDLIC); WS-THIS-PROGCOMMAREA (CCUP-CHANGE-ACTION state + CCUP-OLD/NEW-DETAILS + CARD-UPDATE-RECORD) |
| CARDDAT   | Card record read for display and for optimistic-lock comparison |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (CCRDUPA) | Card data (old or new based on state); info message (state guidance); error message (validation failures) |
| CARDDAT     | CICS REWRITE with CARD-UPDATE-RECORD containing updated name, status, expiry month/year |
| COMMAREA  | CCUP-OLD-DETAILS refreshed with current file data when concurrent modification detected; CDEMO-ACCT-ID/CARD-NUM cleared on exit if from COCRDLIC |

---

## 11. Key Variables and Their Purpose

| Variable               | Purpose |
|------------------------|---------|
| CCUP-CHANGE-ACTION     | State machine driver; persisted across pseudo-conversational cycles in WS-THIS-PROGCOMMAREA; controls EVALUATE dispatch in 0000-MAIN and 2000-DECIDE-ACTION |
| CCUP-OLD-DETAILS       | Snapshot of card data taken at read time; used for change detection in 9300-CHECK-CHANGE-IN-REC and for populating screen in CCUP-SHOW-DETAILS state |
| CCUP-NEW-DETAILS       | User-entered values collected from screen in 1100-RECEIVE-MAP; compared to CCUP-OLD-DETAILS to determine if changes were made |
| CARD-UPDATE-RECORD     | Assembled update record passed to CICS REWRITE; combines new user values with unchanged fields (CVV, account ID, old expiry day) |
| CARD-NAME-CHECK        | Scratch area for alpha validation; INSPECT CONVERTING replaces all alpha with spaces; non-zero TRIM length means invalid characters present |
| WS-INFO-MSG            | State-specific guidance message shown prominently on screen; key part of the user workflow prompts |
