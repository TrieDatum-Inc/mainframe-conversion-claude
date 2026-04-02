# Technical Specification: COCRDUPC.CBL

## 1. Program Overview

| Attribute        | Value                              |
|------------------|------------------------------------|
| Program Name     | COCRDUPC                           |
| Source File      | app/cbl/COCRDUPC.cbl               |
| Layer            | Business Logic (Online / CICS)     |
| Function         | Update Credit Card Details         |
| Transaction ID   | CCUP                               |
| Mapset           | COCRDUP                            |
| Map              | CCRDUPA                            |
| Date Written     | April 2022                         |
| Version Tag      | CardDemo_v1.0-15-g27d6c6f-68       |

### Purpose

COCRDUPC is a multi-step credit card update program. It accepts an account number and card number, retrieves the corresponding CARDDAT record, presents it to the user for editing, validates the changes, requests explicit confirmation (via PF5), and then rewrites the record. It implements optimistic locking by re-reading the record with UPDATE intent at save time and comparing it against the originally displayed values before applying the rewrite.

The updateable fields are: embossed name, card active status (Y/N), expiry month, and expiry year. CVV code, card number, account ID, and expiry day are not user-editable on screen (expiry day is carried internally from the original record).

---

## 2. Artifact Inventory

| Artifact           | Type              | Location                          |
|--------------------|-------------------|-----------------------------------|
| COCRDUPC.CBL       | COBOL source      | app/cbl/COCRDUPC.cbl              |
| COCRDUP.BMS        | BMS mapset source | app/bms/COCRDUP.bms               |
| COCRDUP.CPY        | BMS map copybook  | app/cpy-bms/COCRDUP.CPY           |
| CVCRD01Y.CPY       | Working storage   | app/cpy/CVCRD01Y.cpy              |
| COCOM01Y.CPY       | COMMAREA layout   | app/cpy/COCOM01Y.cpy              |
| CVACT02Y.CPY       | Card record layout| app/cpy/CVACT02Y.cpy              |
| CVCUS01Y.CPY       | Customer record   | app/cpy/CVCUS01Y.cpy              |
| COTTL01Y.CPY       | Screen titles     | app/cpy/COTTL01Y.cpy              |
| CSDAT01Y.CPY       | Date formatting   | app/cpy/CSDAT01Y.cpy              |
| CSMSG01Y.CPY       | Common messages   | app/cpy/CSMSG01Y.cpy              |
| CSMSG02Y.CPY       | Abend variables   | app/cpy/CSMSG02Y.cpy              |
| CSUSR01Y.CPY       | Signed-on user    | app/cpy/CSUSR01Y.cpy              |
| DFHBMSCA           | IBM BMS attribute | System copybook                   |
| DFHAID             | IBM AID keys      | System copybook                   |
| CSSTRPFY           | PFKey store logic | Inline COPY at line 1528          |

---

## 3. CICS Commands Used

| Command                | Paragraph / Location          | Purpose                                                 |
|------------------------|-------------------------------|---------------------------------------------------------|
| EXEC CICS HANDLE ABEND | 0000-MAIN (~370)              | Route abends to ABEND-ROUTINE                           |
| EXEC CICS RETURN       | COMMON-RETURN (~554)          | Return with TRANSID=CCUP and COMMAREA                   |
| EXEC CICS XCTL         | ~473                          | Transfer back to calling program or COMEN01C (PF3, post-update) |
| EXEC CICS SYNCPOINT    | ~470                          | Commit syncpoint before XCTL on PF3/post-update exit   |
| EXEC CICS SEND MAP     | 3400-SEND-SCREEN (~1329)      | Send CCRDUPA from CCRDUPAO with CURSOR/ERASE/FREEKB     |
| EXEC CICS RECEIVE MAP  | 1100-RECEIVE-MAP (~579)       | Receive CCRDUPA into CCRDUPAI                           |
| EXEC CICS READ         | 9100-GETCARD-BYACCTCARD (~1382) | Direct read of CARDDAT by card number                 |
| EXEC CICS READ UPDATE  | 9200-WRITE-PROCESSING (~1427) | Lock CARDDAT record for update                          |
| EXEC CICS REWRITE      | 9200-WRITE-PROCESSING (~1477) | Write updated record back to CARDDAT                    |
| EXEC CICS SEND TEXT    | SEND-LONG-TEXT, SEND-PLAIN-TEXT | Debug only                                            |

---

## 4. Copybooks Referenced

| Copybook      | Usage in COCRDUPC                                                                     |
|---------------|---------------------------------------------------------------------------------------|
| CVCRD01Y      | CC-WORK-AREAS: CC-ACCT-ID, CC-CARD-NUM, CCARD-AID-xxx, CCARD-NEXT-PROG, CCARD-ERROR-MSG |
| COCOM01Y      | CARDDEMO-COMMAREA: navigation context, CDEMO-ACCT-ID, CDEMO-CARD-NUM, user type, etc. |
| COCRDUP       | BMS symbolic map CCRDUPAI / CCRDUPAO                                                  |
| CVACT02Y      | CARD-RECORD (all fields)                                                              |
| CVCUS01Y      | CUSTOMER-RECORD (included but not used on this screen's active paths)                |
| COTTL01Y      | Screen title literals CCDA-TITLE01, CCDA-TITLE02                                     |
| CSDAT01Y      | Date/time formatting                                                                  |
| CSMSG01Y      | Common message literals                                                               |
| CSMSG02Y      | ABEND-DATA, ABEND-CULPRIT, ABEND-CODE, ABEND-MSG                                     |
| CSUSR01Y      | Signed-on user data                                                                   |
| DFHBMSCA      | DFHBMPRF, DFHBMFSE, DFHBMDAR, DFHBMBRY, DFHRED, DFHDFCOL                            |
| DFHAID        | AID key constants                                                                     |
| CSSTRPFY      | Maps EIBAID to CCARD-AID                                                              |

---

## 5. Data Structures

### 5.1 State Machine — CCUP-CHANGE-ACTION

The central state variable governing all screen flow is CCUP-CHANGE-ACTION (PIC X(1)) within WS-THIS-PROGCOMMAREA:

| Value        | 88-level Name                   | Meaning                                              |
|--------------|---------------------------------|------------------------------------------------------|
| LOW-VALUES or SPACES | CCUP-DETAILS-NOT-FETCHED | Initial state: card data not yet retrieved     |
| 'S'          | CCUP-SHOW-DETAILS               | Card fetched; display for editing                    |
| 'E'          | CCUP-CHANGES-NOT-OK             | User submitted changes; validation failed            |
| 'N'          | CCUP-CHANGES-OK-NOT-CONFIRMED   | Changes validated OK; awaiting PF5 confirmation      |
| 'C'          | CCUP-CHANGES-OKAYED-AND-DONE    | PF5 pressed; update committed successfully           |
| 'L'          | CCUP-CHANGES-OKAYED-LOCK-ERROR  | PF5 pressed; could not lock record for update        |
| 'F'          | CCUP-CHANGES-OKAYED-BUT-FAILED  | PF5 pressed; locked but REWRITE failed               |

### 5.2 Old and New Detail Snapshots (WS-THIS-PROGCOMMAREA)

**CCUP-OLD-DETAILS** — values as read from CARDDAT (used for dirty-check at save time):

| Field              | PIC    | Description                                      |
|--------------------|--------|--------------------------------------------------|
| CCUP-OLD-ACCTID    | X(11)  | Account ID from original read                    |
| CCUP-OLD-CARDID    | X(16)  | Card number from original read                   |
| CCUP-OLD-CVV-CD    | X(3)   | CVV from original read                           |
| CCUP-OLD-CRDNAME   | X(50)  | Embossed name from original read (uppercased)    |
| CCUP-OLD-EXPYEAR   | X(4)   | Expiry year from original read                   |
| CCUP-OLD-EXPMON    | X(2)   | Expiry month from original read                  |
| CCUP-OLD-EXPDAY    | X(2)   | Expiry day from original read                    |
| CCUP-OLD-CRDSTCD   | X(1)   | Active status from original read                 |

**CCUP-NEW-DETAILS** — values entered by user:

| Field              | PIC    | Description                                      |
|--------------------|--------|--------------------------------------------------|
| CCUP-NEW-ACCTID    | X(11)  | Account ID entered (or from COMMAREA)            |
| CCUP-NEW-CARDID    | X(16)  | Card number entered (or from COMMAREA)           |
| CCUP-NEW-CVV-CD    | X(3)   | CVV (carried from old; not user-editable)        |
| CCUP-NEW-CRDNAME   | X(50)  | New embossed name                                |
| CCUP-NEW-EXPYEAR   | X(4)   | New expiry year                                  |
| CCUP-NEW-EXPMON    | X(2)   | New expiry month                                 |
| CCUP-NEW-EXPDAY    | X(2)   | New expiry day (carried from old)                |
| CCUP-NEW-CRDSTCD   | X(1)   | New active status                                |

**CARD-UPDATE-RECORD** — the record written to CARDDAT via REWRITE:

| Field                      | PIC    | Description                                |
|----------------------------|--------|--------------------------------------------|
| CARD-UPDATE-NUM            | X(16)  | Card number                                |
| CARD-UPDATE-ACCT-ID        | 9(11)  | Account ID (numeric)                       |
| CARD-UPDATE-CVV-CD         | 9(03)  | CVV (carried from original)                |
| CARD-UPDATE-EMBOSSED-NAME  | X(50)  | New embossed name                          |
| CARD-UPDATE-EXPIRAION-DATE | X(10)  | Reconstructed as YYYY-MM-DD via STRING     |
| CARD-UPDATE-ACTIVE-STATUS  | X(01)  | New active status                          |
| FILLER                     | X(59)  | Padding                                    |

### 5.3 CARD-RECORD (from CVACT02Y) — see COCRDLIC_spec.md section 5.3.

### 5.4 CARDDEMO-COMMAREA (from COCOM01Y) — see COCRDLIC_spec.md section 5.4.

### 5.5 Input Validation Flags

| Flag Variable             | Values (88-levels)                              | Validated Field         |
|---------------------------|-------------------------------------------------|-------------------------|
| WS-EDIT-ACCT-FLAG         | NOT-OK / ISVALID / BLANK                        | Account ID              |
| WS-EDIT-CARD-FLAG         | NOT-OK / ISVALID / BLANK                        | Card number             |
| WS-EDIT-CARDNAME-FLAG     | NOT-OK / ISVALID / BLANK                        | Embossed name           |
| WS-EDIT-CARDSTATUS-FLAG   | NOT-OK / ISVALID / BLANK                        | Active status (Y/N)     |
| WS-EDIT-CARDEXPMON-FLAG   | NOT-OK / ISVALID / BLANK                        | Expiry month (1-12)     |
| WS-EDIT-CARDEXPYEAR-FLAG  | NOT-OK / ISVALID / BLANK                        | Expiry year (1950-2099) |

---

## 6. File Access

### CARDDAT (LIT-CARDFILENAME = 'CARDDAT ')
- **Type**: VSAM KSDS
- **Primary key**: CARD-NUM X(16)
- **Operations**:
  - **READ** (no update) in 9100-GETCARD-BYACCTCARD: to fetch and display current values.
  - **READ UPDATE** in 9200-WRITE-PROCESSING: to lock the record before rewrite.
  - **REWRITE** in 9200-WRITE-PROCESSING: to write the updated CARD-UPDATE-RECORD.

---

## 7. Program Flow — Paragraph-by-Paragraph

### 0000-MAIN (Entry Point, lines 367–544)

1. EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE).
2. INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA.
3. SET WS-RETURN-MSG-OFF.
4. **COMMAREA load**: If EIBCALEN=0 OR (FROM-PROGRAM=COMEN01C AND NOT REENTER), initialize both COMMAREs; set CDEMO-PGM-ENTER and CCUP-DETAILS-NOT-FETCHED. Else load from DFHCOMMAREA.
5. PERFORM YYYY-STORE-PFKEY.
6. **PFKey validation**: Accept ENTER, PFK03, PFK05 (only if CCUP-CHANGES-OK-NOT-CONFIRMED), PFK12 (only if NOT CCUP-DETAILS-NOT-FETCHED). All others coerced to ENTER.
7. **Main dispatch EVALUATE** (lines 429–543):

| WHEN Condition                                                   | Action                                                                                            |
|------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| CCARD-AID-PFK03                                                  | SYNCPOINT; set return program; XCTL back                                                          |
| CCUP-CHANGES-OKAYED-AND-DONE AND CDEMO-LAST-MAPSET = COCRDLI     | Treat as PF3 (auto-exit back to list after success)                                               |
| CCUP-CHANGES-FAILED AND CDEMO-LAST-MAPSET = COCRDLI              | Treat as PF3 (auto-exit after failed update when called from list)                                |
| CDEMO-PGM-ENTER AND FROM-PROGRAM = COCRDLIC                      | Move COMMAREA keys to CC fields; 9000-READ-DATA; CCUP-SHOW-DETAILS; 3000-SEND-MAP                |
| CCARD-AID-PFK12 AND FROM-PROGRAM = COCRDLIC                      | Re-fetch card; CCUP-SHOW-DETAILS; 3000-SEND-MAP (cancel changes, reload)                         |
| CCUP-DETAILS-NOT-FETCHED AND CDEMO-PGM-ENTER                     | 3000-SEND-MAP (show entry screen); set CCUP-DETAILS-NOT-FETCHED                                   |
| FROM-PROGRAM = COMEN01C AND NOT REENTER                          | 3000-SEND-MAP (fresh entry form)                                                                  |
| CCUP-CHANGES-OKAYED-AND-DONE (standalone) or CCUP-CHANGES-FAILED | Re-initialize, 3000-SEND-MAP (fresh entry after success/failure outside of list context)          |
| OTHER                                                            | 1000-PROCESS-INPUTS; 2000-DECIDE-ACTION; 3000-SEND-MAP                                           |

### COMMON-RETURN (lines 546–558)
- Moves WS-RETURN-MSG to CCARD-ERROR-MSG.
- Packs WS-COMMAREA = CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA.
- EXEC CICS RETURN TRANSID(CCUP) COMMAREA(WS-COMMAREA).

### 1000-PROCESS-INPUTS (lines 564–573)
- Calls 1100-RECEIVE-MAP then 1200-EDIT-MAP-INPUTS.
- Sets CCARD-NEXT-PROG/MAPSET/MAP to this program.

### 1100-RECEIVE-MAP (lines 578–638)
- EXEC CICS RECEIVE MAP(CCRDUPA) MAPSET(COCRDUP) INTO(CCRDUPAI).
- Initializes CCUP-NEW-DETAILS.
- Moves map input fields to CC-ACCT-ID/CCUP-NEW-ACCTID, CC-CARD-NUM/CCUP-NEW-CARDID, CCUP-NEW-CRDNAME, CCUP-NEW-CRDSTCD, CCUP-NEW-EXPDAY, CCUP-NEW-EXPMON, CCUP-NEW-EXPYEAR.
- Treats '*' or SPACES on any field as LOW-VALUES (indicator of empty/unchanged).

### 1200-EDIT-MAP-INPUTS (lines 641–715)
This is the central validation logic:

**Phase 1 — Search key validation (when CCUP-DETAILS-NOT-FETCHED)**:
- Validate account (1210-EDIT-ACCOUNT): numeric, non-zero, 11 digits.
- Validate card (1220-EDIT-CARD): numeric, 16 digits.
- Cross-check: if both blank, set NO-SEARCH-CRITERIA-RECEIVED.
- GO TO exit (skip Phase 2).

**Phase 2 — Field validation (when details already fetched)**:
- Restore OLD values to CDEMO-ACCT-ID/CDEMO-CARD-NUM and working areas.
- **No-change detection**: if CCUP-NEW-CARDDATA equals CCUP-OLD-CARDDATA (case-insensitive), set NO-CHANGES-DETECTED.
- Skip validation if NO-CHANGES-DETECTED, CCUP-CHANGES-OK-NOT-CONFIRMED, or CCUP-CHANGES-OKAYED-AND-DONE.
- Otherwise set CCUP-CHANGES-NOT-OK and validate:
  - 1230-EDIT-NAME
  - 1240-EDIT-CARDSTATUS
  - 1250-EDIT-EXPIRY-MON
  - 1260-EDIT-EXPIRY-YEAR
- If all edits pass: set CCUP-CHANGES-OK-NOT-CONFIRMED.

### 1210-EDIT-ACCOUNT (lines 721–756)
- Blank/zero: INPUT-ERROR, FLG-ACCTFILTER-BLANK, message 'Account number not provided'.
- Not numeric: INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, message 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER'.
- Valid: move to CDEMO-ACCT-ID and CCUP-NEW-ACCTID, set FLG-ACCTFILTER-ISVALID.

### 1220-EDIT-CARD (lines 762–802)
- Same pattern as 1210 for card number, 16-digit numeric.

### 1230-EDIT-NAME (lines 806–841)
- Blank/zero: INPUT-ERROR, FLG-CARDNAME-BLANK, message 'Card name not provided'.
- Must be alphabetic and spaces only — validation technique:
  - Copy name to CARD-NAME-CHECK.
  - INSPECT CONVERTING LIT-ALL-ALPHA-FROM TO LIT-ALL-SPACES-TO (replaces all letters with spaces).
  - If any non-space characters remain (FUNCTION TRIM result length > 0): INPUT-ERROR, FLG-CARDNAME-NOT-OK, message 'Card name can only contain alphabets and spaces'.
- Valid: FLG-CARDNAME-ISVALID.

### 1240-EDIT-CARDSTATUS (lines 845–874)
- Blank/zero: INPUT-ERROR, FLG-CARDSTATUS-BLANK, message 'Card Active Status must be Y or N'.
- Move CCUP-NEW-CRDSTCD to FLG-YES-NO-CHECK; if FLG-YES-NO-VALID (values 'Y' or 'N'): FLG-CARDSTATUS-ISVALID.
- Else: INPUT-ERROR, FLG-CARDSTATUS-NOT-OK.

### 1250-EDIT-EXPIRY-MON (lines 877–910)
- Blank/zero: INPUT-ERROR, FLG-CARDEXPMON-BLANK, message 'Card expiry month must be between 1 and 12'.
- Move CCUP-NEW-EXPMON to CARD-MONTH-CHECK; check 88 VALID-MONTH (values 1 THRU 12).
- Valid: FLG-CARDEXPMON-ISVALID.

### 1260-EDIT-EXPIRY-YEAR (lines 913–945)
- Blank/zero: INPUT-ERROR, FLG-CARDEXPYEAR-BLANK, message 'Invalid card expiry year'.
- Move CCUP-NEW-EXPYEAR to CARD-YEAR-CHECK; check 88 VALID-YEAR (values 1950 THRU 2099).
- Valid: FLG-CARDEXPYEAR-ISVALID.

### 2000-DECIDE-ACTION (lines 948–1028)
This paragraph decides what to do with the post-validation state:

| WHEN Condition                             | Action                                                              |
|--------------------------------------------|---------------------------------------------------------------------|
| CCUP-DETAILS-NOT-FETCHED                   | (fall through — re-fetch is handled in 0000-MAIN)                  |
| CCARD-AID-PFK12 (cancel changes)           | If keys valid: 9000-READ-DATA, re-show old details (CCUP-SHOW-DETAILS) |
| CCUP-SHOW-DETAILS                          | If no error and no no-change: set CCUP-CHANGES-OK-NOT-CONFIRMED     |
| CCUP-CHANGES-NOT-OK                        | Continue (re-display with errors)                                   |
| CCUP-CHANGES-OK-NOT-CONFIRMED AND PFK05    | 9200-WRITE-PROCESSING; evaluate outcome into state                  |
| CCUP-CHANGES-OK-NOT-CONFIRMED (no PFK05)   | Continue (re-display confirmation prompt)                           |
| CCUP-CHANGES-OKAYED-AND-DONE               | Set CCUP-SHOW-DETAILS; clear CDEMO keys if FROM-TRANID blank        |
| OTHER                                      | ABEND-ROUTINE (abend code 9999)                                     |

### 3000-SEND-MAP (lines 1035–1045)
Driver for screen output. Calls in sequence:
- 3100-SCREEN-INIT
- 3200-SETUP-SCREEN-VARS
- 3250-SETUP-INFOMSG
- 3300-SETUP-SCREEN-ATTRS
- 3400-SEND-SCREEN

### 3100-SCREEN-INIT (lines 1052–1078)
- Sets CCRDUPAO to LOW-VALUES.
- Populates header: TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO.

### 3200-SETUP-SCREEN-VARS (lines 1082–1133)
- If CDEMO-PGM-ENTER: no field population (blank screen).
- Else: populate ACCTSIDO and CARDSIDO.
- EVALUATE state:
  - CCUP-DETAILS-NOT-FETCHED: blank out all detail fields.
  - CCUP-SHOW-DETAILS: show OLD values (CCUP-OLD-CRDNAME, etc.).
  - CCUP-CHANGES-MADE: show NEW values entered by user; expiry day always uses OLD value.
  - OTHER: show OLD values (fallback).

### 3250-SETUP-INFOMSG (lines 1138–1163)
- EVALUATE state to set WS-INFO-MSG:

| State                          | Message                               |
|--------------------------------|---------------------------------------|
| CDEMO-PGM-ENTER                | 'Please enter Account and Card Number'|
| CCUP-DETAILS-NOT-FETCHED       | 'Please enter Account and Card Number'|
| CCUP-SHOW-DETAILS              | 'Details of selected card shown above'|
| CCUP-CHANGES-NOT-OK            | 'Update card details presented above.'|
| CCUP-CHANGES-OK-NOT-CONFIRMED  | 'Changes validated.Press F5 to save'  |
| CCUP-CHANGES-OKAYED-AND-DONE   | 'Changes committed to database'       |
| CCUP-CHANGES-OKAYED-LOCK-ERROR | 'Changes unsuccessful. Please try again'|
| CCUP-CHANGES-OKAYED-BUT-FAILED | 'Changes unsuccessful. Please try again'|

### 3300-SETUP-SCREEN-ATTRS (lines 1168–1318)
- **Field protection by state**:
  - CCUP-DETAILS-NOT-FETCHED: ACCTSID/CARDSID unprotected; all detail fields protected.
  - CCUP-SHOW-DETAILS or CCUP-CHANGES-NOT-OK: ACCTSID/CARDSID protected; detail fields unprotected.
  - CCUP-CHANGES-OK-NOT-CONFIRMED or CCUP-CHANGES-OKAYED-AND-DONE: all fields protected.
  - OTHER: ACCTSID/CARDSID unprotected; detail fields protected.
- **Cursor positioning** by error flag priority: account → card → name → status → expiry month → expiry year.
- **Color**:
  - If FROM list: ACCTSID/CARDSID in DFHDFCOL.
  - Blank/invalid fields during CCUP-CHANGES-NOT-OK: DFHRED color, '*' substitution for blank.
  - EXPDAYC always set DFHBMDAR (dark; day is never user-editable).
  - FKEYSC bright (DFHBMBRY) when in CCUP-CHANGES-OK-NOT-CONFIRMED state to highlight F5/F12.
  - INFOMSGA: dark if no message, bright yellow if message.

### 3400-SEND-SCREEN (lines 1324–1337)
- EXEC CICS SEND MAP(CCRDUPA) MAPSET(COCRDUP) FROM(CCRDUPAO) CURSOR ERASE FREEKB.

### 9000-READ-DATA (lines 1343–1372)
- Initialize CCUP-OLD-DETAILS.
- Set CCUP-OLD-ACCTID ← CC-ACCT-ID; CCUP-OLD-CARDID ← CC-CARD-NUM.
- PERFORM 9100-GETCARD-BYACCTCARD.
- If FOUND-CARDS-FOR-ACCOUNT:
  - CCUP-OLD-CVV-CD ← CARD-CVV-CD.
  - INSPECT CARD-EMBOSSED-NAME CONVERTING lower to upper.
  - CCUP-OLD-CRDNAME ← CARD-EMBOSSED-NAME (uppercased).
  - Parse CARD-EXPIRAION-DATE: positions 1:4 → EXPYEAR, 6:2 → EXPMON, 9:2 → EXPDAY.
  - CCUP-OLD-CRDSTCD ← CARD-ACTIVE-STATUS.

### 9100-GETCARD-BYACCTCARD (lines 1376–1415)
- EXEC CICS READ FILE(CARDDAT) RIDFLD(WS-CARD-RID-CARDNUM) INTO(CARD-RECORD).
- NORMAL: FOUND-CARDS-FOR-ACCOUNT.
- NOTFND: INPUT-ERROR, message 'Did not find cards for this search condition'.
- OTHER: INPUT-ERROR, build and set WS-FILE-ERROR-MESSAGE.

### 9200-WRITE-PROCESSING (lines 1420–1494)
The multi-step update sequence:

1. **Lock the record**: EXEC CICS READ FILE(CARDDAT) UPDATE RIDFLD(WS-CARD-RID-CARDNUM) INTO(CARD-RECORD).
   - If not NORMAL: set COULD-NOT-LOCK-FOR-UPDATE; go to exit.
2. **Dirty check**: PERFORM 9300-CHECK-CHANGE-IN-REC.
   - If DATA-WAS-CHANGED-BEFORE-UPDATE: go to exit (will be re-displayed with fresh data).
3. **Prepare update record**: build CARD-UPDATE-RECORD:
   - CARD-UPDATE-NUM ← CCUP-NEW-CARDID
   - CARD-UPDATE-ACCT-ID ← CC-ACCT-ID-N
   - CVV: move CCUP-NEW-CVV-CD to CARD-CVV-CD-X, then CARD-CVV-CD-N to CARD-UPDATE-CVV-CD (numeric)
   - CARD-UPDATE-EMBOSSED-NAME ← CCUP-NEW-CRDNAME
   - STRING CCUP-NEW-EXPYEAR '-' CCUP-NEW-EXPMON '-' CCUP-NEW-EXPDAY into CARD-UPDATE-EXPIRAION-DATE
   - CARD-UPDATE-ACTIVE-STATUS ← CCUP-NEW-CRDSTCD
4. **Rewrite**: EXEC CICS REWRITE FILE(CARDDAT) FROM(CARD-UPDATE-RECORD).
   - If not NORMAL: set LOCKED-BUT-UPDATE-FAILED.

### 9300-CHECK-CHANGE-IN-REC (lines 1498–1521)
Compares the just-read (locked) record against the OLD snapshot saved when the user first saw the data:
- Converts CARD-EMBOSSED-NAME lower to upper for comparison.
- Checks CARD-CVV-CD, CARD-EMBOSSED-NAME, CARD-EXPIRAION-DATE (year/mon/day positions), CARD-ACTIVE-STATUS.
- If any field differs: set DATA-WAS-CHANGED-BEFORE-UPDATE, refresh CCUP-OLD-xxx fields with the new values from disk, and exit. The program will then re-display the updated data (implicitly prompting the user to review and re-submit).
- If all match: continue to REWRITE.

---

## 8. Inter-Program Interactions

| Direction  | Target Program      | Mechanism              | Trigger                                              | Data Passed                               |
|------------|---------------------|------------------------|------------------------------------------------------|-------------------------------------------|
| Outbound   | COMEN01C or caller  | EXEC CICS XCTL (post SYNCPOINT) | PF3; or auto-exit after CCUP-CHANGES-OKAYED-AND-DONE from list | CARDDEMO-COMMAREA         |
| Outbound   | COCRDLIC (caller)   | EXEC CICS XCTL         | Auto-exit after successful/failed update when FROM list | CARDDEMO-COMMAREA (CDEMO-ACCT-ID/CARD-NUM zeroed) |
| Self-loop  | COCRDUPC            | EXEC CICS RETURN TRANSID(CCUP) | Normal screen re-display at any stage           | WS-COMMAREA = CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA |
| Inbound    | COCRDLIC            | XCTL                   | Row selected with 'U' from card list                 | CARDDEMO-COMMAREA with CDEMO-ACCT-ID, CDEMO-CARD-NUM |
| Inbound    | COMEN01C            | XCTL                   | Direct transaction CCUP from menu                    | CARDDEMO-COMMAREA                         |

### SYNCPOINT on Exit
Before XCTL on PF3 or auto-exit, COCRDUPC issues EXEC CICS SYNCPOINT (line ~470). This commits the REWRITE if it was done, ensuring the update is durable before control passes back.

---

## 9. Key Function Keys

| Key    | Valid When                          | Action                                                   |
|--------|-------------------------------------|----------------------------------------------------------|
| ENTER  | Any state                           | Process current screen inputs; advance state machine     |
| PF3    | Any state                           | Exit to calling program (SYNCPOINT first)                |
| PF5    | CCUP-CHANGES-OK-NOT-CONFIRMED only  | Confirm and save changes (triggers REWRITE)              |
| PF12   | Any state except CCUP-DETAILS-NOT-FETCHED | Cancel pending changes; re-fetch original record   |
| Other  | Any                                 | Treated as ENTER                                         |

---

## 10. Update State Machine

```
                         [Initial / PGM-ENTER]
                                  |
                         CCUP-DETAILS-NOT-FETCHED
                                  |
                    [User enters Acct+Card, ENTER]
                                  |
                    [9100-GETCARD-BYACCTCARD READ]
                                  |
                          CCUP-SHOW-DETAILS ('S')
                                  |
                    [User edits name/status/expiry, ENTER]
                                  |
                    [1200-EDIT-MAP-INPUTS validates]
                           /               \
                  [invalid]                 [valid, changed]
                     |                           |
             CCUP-CHANGES-NOT-OK ('E')   CCUP-CHANGES-OK-NOT-CONFIRMED ('N')
                     |                           |
             [user re-edits]             [user presses PF5]
                                               |
                                   [9200-WRITE-PROCESSING]
                                        /       |       \
                             [locked,    [lock     [dirty:
                              written]   failed]    changed]
                                |           |           |
                    CCUP-CHANGES-       CCUP-CHANGES-  CCUP-SHOW-DETAILS
                    OKAYED-AND-         OKAYED-BUT-    (refresh + re-display)
                    DONE ('C')          FAILED ('F')
                                    or
                                CCUP-CHANGES-OKAYED-
                                LOCK-ERROR ('L')
```

---

## 11. Error Handling

| Condition                       | Message / Behavior                                                    |
|---------------------------------|-----------------------------------------------------------------------|
| Account not provided            | 'Account number not provided'; cursor to ACCTSID; RED                 |
| Account not numeric             | '...11 DIGIT NUMBER'; cursor to ACCTSID; RED                         |
| Card not provided               | 'Card number not provided'; cursor to CARDSID; RED                    |
| Card not numeric                | '...16 DIGIT NUMBER'; cursor to CARDSID; RED                         |
| Name blank                      | 'Card name not provided'; cursor to CRDNAME; RED                      |
| Name contains non-alpha/space   | 'Card name can only contain alphabets and spaces'; RED on CRDNAME     |
| Status not Y or N               | 'Card Active Status must be Y or N'; RED on CRDSTCD                   |
| Expiry month not 1-12           | 'Card expiry month must be between 1 and 12'; RED on EXPMON           |
| Expiry year not 1950-2099       | 'Invalid card expiry year'; RED on EXPYEAR                            |
| No changes detected             | 'No change detected with respect to values fetched.'; no state change |
| Card not found (READ)           | 'Did not find cards for this search condition'; both fields RED        |
| Could not lock for update       | 'Could not lock record for update'; state = LOCK-ERROR                |
| Record changed concurrently     | 'Record changed by some one else. Please review'; re-show with fresh data |
| REWRITE failed                  | 'Update of record failed'; state = FAILED                             |
| File I/O other error            | 'File Error: READ on CARDDAT returned RESP x,RESP2 y'                 |
| Unexpected EVALUATE state       | ABEND-ROUTINE: SEND ABEND-DATA; EXEC CICS ABEND ABCODE('9999')        |
| CICS ABEND (HANDLE ABEND)       | Same ABEND-ROUTINE path                                               |

---

## 12. Business Rules

1. **Two-phase update confirmation**: All changes must pass field validation before a confirmation prompt is shown. The user must press PF5 to commit. Pressing ENTER after validation just re-shows the confirmation screen without saving.

2. **Optimistic concurrency**: The original record values (CCUP-OLD-xxx) are stored in the COMMAREA across the user interaction. At REWRITE time, the program re-reads the record with UPDATE lock and compares all fields against the snapshot (9300-CHECK-CHANGE-IN-REC). If any field differs, the update is aborted, and the user is shown the current values.

3. **Name must be alphabetic**: The name validation uses an INSPECT CONVERTING technique: it copies the name and converts all letters A-Z and a-z to spaces. If anything non-space survives, the name contains invalid characters (digits, punctuation).

4. **Case normalization**: When reading the card record (9000-READ-DATA and 9300-CHECK-CHANGE-IN-REC), the program converts CARD-EMBOSSED-NAME to uppercase using INSPECT CONVERTING. The no-change comparison (1200-EDIT-MAP-INPUTS) uses FUNCTION UPPER-CASE on both old and new CARDDATA structures.

5. **Expiry day not user-editable**: The EXPDAY field is DRK/FSET/PROT on the BMS screen and is never modified — the old expiry day is always carried over to the new record.

6. **SYNCPOINT before navigation exit**: To ensure the REWRITE is committed before control passes back to the caller, EXEC CICS SYNCPOINT is issued immediately before the XCTL on PF3 or auto-exit paths (line ~470).

7. **Auto-exit to card list**: When COCRDUPC was entered from COCRDLIC and the update either succeeds (CCUP-CHANGES-OKAYED-AND-DONE) or definitively fails (CCUP-CHANGES-FAILED), the program automatically XCTLs back to COCRDLIC rather than waiting for PF3, and clears CDEMO-ACCT-ID/CDEMO-CARD-NUM to 0 first.
