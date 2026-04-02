# Technical Specification: COTRTUPC

## 1. Executive Summary

COTRTUPC is an **online CICS COBOL program** that provides the add/update/delete detail screen for the `CARDDEMO.TRANSACTION_TYPE` DB2 table. It is navigated to from the list program COTRTLIC (via PF02 for add, or by selection of a row for update/delete) and presents BMS mapset COTRTUP, map CTRTUPA, via transaction `CTTU`. The program implements a multi-step conversational state machine: the operator first enters a transaction type code, the program fetches the record, then the operator edits the description field and confirms the change with PF05. Delete follows a separate PF04 → confirm → PF04 path. New record creation (INSERT) is triggered when a type code is entered that does not exist. The program issues DB2 UPDATE, INSERT, and DELETE statements and issues `EXEC CICS SYNCPOINT` on success.

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COTRTUPC.cbl | CICS online COBOL program | `app/app-transaction-type-db2/cbl/COTRTUPC.cbl` |
| COTRTUP.bms | BMS mapset | `app/app-transaction-type-db2/bms/COTRTUP.bms` |
| COTRTUP.cpy | BMS symbolic map copybook | `app/app-transaction-type-db2/cpy-bms/COTRTUP.cpy` |
| DCLTRTYP | DB2 DCLGEN for TRANSACTION_TYPE | NOT AVAILABLE FOR INSPECTION |
| DCLTRCAT | DB2 DCLGEN for TRCAT table | NOT AVAILABLE FOR INSPECTION |
| COCOM01Y | Application COMMAREA copybook | Standard CardDemo |
| CVCRD01Y | Card working-storage | Standard CardDemo |
| COTTL01Y | Screen title copybook | Standard CardDemo |
| CSDAT01Y | Date/time variables | Standard CardDemo |
| CSMSG01Y | Common messages | Standard CardDemo |
| CSMSG02Y | Abend variables | Standard CardDemo |
| CSUSR01Y | Signed-on user data | Standard CardDemo |
| CSUTLDWY | Generic date edit variables | Standard CardDemo |
| CSSETATY | Screen attribute setting copybook (with REPLACING) | Standard CardDemo |
| DFHBMSCA | IBM BMS attribute constants | IBM-supplied |
| DFHAID | IBM AID key constants | IBM-supplied |
| CSSTRPFY | PF key storage common code | Standard CardDemo |

---

## 3. Program Identity

| Attribute | Value | Source |
|---|---|---|
| Program-ID | COTRTUPC | Line 22 |
| Transaction ID | CTTU | Line 204 (LIT-THISTRANID) |
| Mapset | COTRTUP | Line 206 (LIT-THISMAPSET) |
| Map | CTRTUPA | Line 208 (LIT-THISMAP) |
| Layer | Business logic | Line 3 |
| Function | Accept and process TRANSACTION TYPE UPDATE | Line 4 |
| List program | COTRTLIC (LIT-LISTTPGM) | Line 218 |
| List transaction | CTLI | Line 220 (LIT-LISTTTRANID) |
| Admin program | COADM01C (LIT-ADMINPGM) | Line 210 |

---

## 4. State Machine — TTUP-CHANGE-ACTION Values

The program's behavior is governed by a single state flag `TTUP-CHANGE-ACTION` (PIC X(1)) in WS-THIS-PROGCOMMAREA:

| Value | Condition Name | Meaning |
|---|---|---|
| LOW-VALUES or SPACE | TTUP-DETAILS-NOT-FETCHED | Initial state — awaiting search key input |
| 'K' | TTUP-INVALID-SEARCH-KEYS | Key validation failed |
| 'X' | TTUP-DETAILS-NOT-FOUND | Key not found in DB2 |
| 'S' | TTUP-SHOW-DETAILS | Record found; displayed for editing |
| 'R' | TTUP-CREATE-NEW-RECORD | User confirmed add for not-found key |
| 'V' | TTUP-REVIEW-NEW-RECORD | Reviewing new record data |
| '9' | TTUP-CONFIRM-DELETE | Awaiting PF04 delete confirmation |
| '8' | TTUP-START-DELETE | Delete was initiated |
| '7' | TTUP-DELETE-DONE | Delete succeeded |
| '6' | TTUP-DELETE-FAILED | Delete failed |
| 'E' | TTUP-CHANGES-NOT-OK | Edit errors found in changed data |
| 'N' | TTUP-CHANGES-OK-NOT-CONFIRMED | Changes validated, awaiting PF05 save |
| 'L' | TTUP-CHANGES-OKAYED-LOCK-ERROR | UPDATE returned SQLCODE -911 (lock) |
| 'F' | TTUP-CHANGES-OKAYED-BUT-FAILED | UPDATE failed with other negative SQLCODE |
| 'C' | TTUP-CHANGES-OKAYED-AND-DONE | UPDATE or INSERT committed |
| 'B' | TTUP-CHANGES-BACKED-OUT | User pressed PF12 to cancel changes |

Source: lines 296-327.

---

## 5. COMMAREA Structure

**Part 1 — CARDDEMO-COMMAREA**: Same as COTRTLIC (from COCOM01Y).

**Part 2 — WS-THIS-PROGCOMMAREA** (lines 294-335):

| Group | Field | PIC | Purpose |
|---|---|---|---|
| TTUP-UPDATE-SCREEN-DATA | TTUP-CHANGE-ACTION | X(1) | State machine flag (see table above) |
| TTUP-OLD-DETAILS | TTUP-OLD-TTYP-TYPE | X(02) | Original type code from DB2 fetch |
| TTUP-OLD-DETAILS | TTUP-OLD-TTYP-TYPE-DESC | X(50) | Original description from DB2 fetch |
| TTUP-NEW-DETAILS | TTUP-NEW-TTYP-TYPE | X(02) | Type code from screen input |
| TTUP-NEW-DETAILS | TTUP-NEW-TTYP-TYPE-DESC | X(50) | Description from screen input |

---

## 6. DB2 SQL Statements

### 6.1 Table Operated Upon

| Table | Schema | Operations |
|---|---|---|
| TRANSACTION_TYPE | CARDDEMO | SELECT, UPDATE, INSERT, DELETE |
| TRCAT | CARDDEMO | [ARTIFACT: DCLTRCAT included but no SQL referencing it was observed in analyzed portions] |

### 6.2 SELECT — Read for Display (paragraph 9100-GET-TRANSACTION-TYPE, lines 1469-1511)

```sql
SELECT TR_TYPE, TR_DESCRIPTION
  INTO :DCL-TR-TYPE, :DCL-TR-DESCRIPTION
  FROM CARDDEMO.TRANSACTION_TYPE
 WHERE TR_TYPE = :DCL-TR-TYPE
```

Host variables set before call: `TTUP-NEW-TTYP-TYPE → DCL-TR-TYPE` (line 1473).

SQLCODE handling:
- `= 0`: SET FOUND-TRANTYPE-IN-TABLE TO TRUE
- `= +100`: SET INPUT-ERROR, SET FLG-TRANFILTER-NOT-OK, SET WS-RECORD-NOT-FOUND
- `< 0`: SET INPUT-ERROR, SET FLG-TRANFILTER-NOT-OK, format error with SQLERRM

### 6.3 UPDATE (paragraph 9600-WRITE-PROCESSING, lines 1531-1592)

```sql
UPDATE CARDDEMO.TRANSACTION_TYPE
   SET TR_DESCRIPTION = :DCL-TR-DESCRIPTION
 WHERE TR_TYPE        = :DCL-TR-TYPE
```

Setup (lines 1538-1542): `TTUP-NEW-TTYP-TYPE → DCL-TR-TYPE`, `FUNCTION TRIM(TTUP-NEW-TTYP-TYPE-DESC) → DCL-TR-DESCRIPTION-TEXT`, length computed.

SQLCODE handling:
- `= 0`: `EXEC CICS SYNCPOINT`, then SET TTUP-CHANGES-OKAYED-AND-DONE
- `= +100`: Falls through to `9700-INSERT-RECORD` (record was deleted by another user between fetch and update)
- `= -911`: SQLCODE lock error — SET TTUP-CHANGES-OKAYED-LOCK-ERROR
- `< 0`: SET TABLE-UPDATE-FAILED, format error string

### 6.4 INSERT — Fallback and New Record (paragraph 9700-INSERT-RECORD, lines 1596-1621)

```sql
INSERT INTO CARDDEMO.TRANSACTION_TYPE
  (TR_TYPE, TR_DESCRIPTION)
  VALUES (:DCL-TR-TYPE, :DCL-TR-DESCRIPTION)
```

Called when UPDATE returns +100 (not found), or directly for new record creation.

SQLCODE handling:
- `= 0`: `EXEC CICS SYNCPOINT`
- `OTHER`: SET TABLE-UPDATE-FAILED, format error string

### 6.5 DELETE (paragraph 9800-DELETE-PROCESSING, lines 1624-1663)

```sql
DELETE FROM CARDDEMO.TRANSACTION_TYPE
 WHERE TR_TYPE = :DCL-TR-TYPE
```

Setup: `TTUP-OLD-TTYP-TYPE → DCL-TR-TYPE` (line 1625).

SQLCODE handling:
- `= 0`: SET TTUP-DELETE-DONE, `EXEC CICS SYNCPOINT`
- `= -532`: Referential integrity violation — SET RECORD-DELETE-FAILED, message "Please delete associated child records first"
- `OTHER`: SET RECORD-DELETE-FAILED, SET TTUP-DELETE-FAILED, format error

---

## 7. CICS Commands

| Command | Paragraph | Purpose |
|---|---|---|
| `EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE)` | `0000-MAIN` line 348 | Register abend handler |
| `EXEC CICS SYNCPOINT` | `9600-WRITE-PROCESSING` (success), `9700-INSERT-RECORD` (success), `9800-DELETE-PROCESSING` (success) | Commit DB2 units of work |
| `EXEC CICS SYNCPOINT` | PF03 exit (line 453) | Commit before XCTL |
| `EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)` | PF03 exit (lines 457-460) | Exit to calling program |
| `EXEC CICS RECEIVE MAP(CTRTUPA) MAPSET(COTRTUP) INTO(CTRTUPAI)` | `1100-RECEIVE-MAP` (lines 641-647) | Read terminal input |
| `EXEC CICS SEND MAP(CCARD-NEXT-MAP) MAPSET(CCARD-NEXT-MAPSET) FROM(CTRTUPAO) CURSOR ERASE FREEKB` | `3400-SEND-SCREEN` (lines 1433-1440) | Write screen to terminal |
| `EXEC CICS SEND FROM(ABEND-DATA) LENGTH(...) NOHANDLE ERASE` | `ABEND-ROUTINE` (lines 1684-1689) | Display abend data |
| `EXEC CICS HANDLE ABEND CANCEL` | `ABEND-ROUTINE` (lines 1691-1693) | Cancel abend trap before forced abend |
| `EXEC CICS ABEND ABCODE(ABEND-CODE)` | `ABEND-ROUTINE` (line 1695-1697) | Force CICS abend with code '9999' |
| `EXEC CICS RETURN TRANSID(CTTU) COMMAREA(WS-COMMAREA) LENGTH(...)` | `COMMON-RETURN` (lines 567-571) | Pseudo-conversational return |

---

## 8. PF Key Navigation and State Transitions

Valid PF keys are determined in `0001-CHECK-PFKEYS` (lines 577-618):

| Key | Context | Action |
|---|---|---|
| ENTER (not TTUP-CONFIRM-DELETE) | Any | Always valid |
| PF03 | Any | Always valid — exit |
| PF04 | TTUP-SHOW-DETAILS or TTUP-CONFIRM-DELETE | Initiate or confirm delete |
| PF05 | TTUP-CHANGES-OK-NOT-CONFIRMED, TTUP-DETAILS-NOT-FOUND, TTUP-DELETE-IN-PROGRESS | Save or add |
| PF12 | TTUP-CHANGES-OK-NOT-CONFIRMED, TTUP-SHOW-DETAILS, TTUP-DETAILS-NOT-FOUND, TTUP-CONFIRM-DELETE, TTUP-CREATE-NEW-RECORD | Cancel |
| Invalid key | Any | Treated as invalid; message set |

### State Transition Table (Main EVALUATE, lines 405-556)

| From State | Key Pressed | Action | Next State |
|---|---|---|---|
| Any terminal/done state | PFK12/TTUP-DELETE-DONE/etc. | Re-initialize, show blank form | TTUP-DETAILS-NOT-FETCHED |
| Any | PF03 | SYNCPOINT, XCTL to calling program | N/A |
| TTUP-DETAILS-NOT-FETCHED, or fresh entry | Not CDEMO-PGM-REENTER | Show blank form | TTUP-DETAILS-NOT-FETCHED |
| TTUP-CONFIRM-DELETE | PF04 | SET TTUP-START-DELETE, PERFORM 9800-DELETE | TTUP-DELETE-DONE or TTUP-DELETE-FAILED |
| TTUP-SHOW-DETAILS | PF04 | Ask delete confirmation | TTUP-CONFIRM-DELETE |
| TTUP-DETAILS-NOT-FOUND | PF05 | Confirm new record creation | TTUP-CREATE-NEW-RECORD |
| TTUP-CHANGES-OK-NOT-CONFIRMED | PF05 | PERFORM 9600-WRITE-PROCESSING | TTUP-CHANGES-OKAYED-AND-DONE or error |
| TTUP-CHANGES-OK-NOT-CONFIRMED, TTUP-SHOW-DETAILS, TTUP-DETAILS-NOT-FOUND, TTUP-CONFIRM-DELETE | PF12 | Cancel action | Varies — `2000-DECIDE-ACTION` |
| WS-INVALID-KEY-PRESSED | Any | Re-display current screen | Unchanged |
| Other | Any | `1000-PROCESS-INPUTS`, `2000-DECIDE-ACTION` | Varies |

---

## 9. PROCEDURE DIVISION — Paragraph-by-Paragraph Logic

### 9.1 0000-MAIN (lines 344-574)

1. `EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE)` (line 348)
2. INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA
3. SET WS-RETURN-MSG-OFF
4. Restore COMMAREA if EIBCALEN > 0; initialize if first entry, or from admin/list without re-entry
5. PERFORM YYYY-STORE-PFKEY
6. SET PFK-INVALID, PERFORM 0001-CHECK-PFKEYS
7. Handle terminal/done states → reset to TTUP-DETAILS-NOT-FETCHED
8. Large EVALUATE for PF key dispatch (lines 423-556)
9. COMMON-RETURN

### 9.2 1000-PROCESS-INPUTS (lines 625-640)

Calls `1100-RECEIVE-MAP`, `1150-STORE-MAP-IN-NEW`, `1200-EDIT-MAP-INPUTS`.

### 9.3 1100-RECEIVE-MAP (lines 641-650)

`EXEC CICS RECEIVE MAP('CTRTUPA') MAPSET('COTRTUP') INTO(CTRTUPAI)`.

### 9.4 1150-STORE-MAP-IN-NEW (lines 652-688)

- Extracts `TRTYPCDI OF CTRTUPAI` → `TTUP-NEW-TTYP-TYPE` (trimmed)
- Extracts `TRTYDSCI OF CTRTUPAI` → `TTUP-NEW-TTYP-TYPE-DESC` (trimmed)
- Handles `'*'` or SPACES as LOW-VALUES

### 9.5 1200-EDIT-MAP-INPUTS (lines 689-781)

- If type code same as previously not-found key: re-confirm not-found state without re-editing
- If CREATE-NEW or CHANGES-OK-NOT-CONFIRMED: skip key edit
- Otherwise: PERFORM `1210-EDIT-TRANTYPE` to validate type code
  - If blank: SET NO-SEARCH-CRITERIA-RECEIVED, TTUP-DETAILS-NOT-FETCHED
  - If invalid: SET TTUP-INVALID-SEARCH-KEYS
- PERFORM `1205-COMPARE-OLD-NEW` to detect if description changed
- If no change and not confirm state: exit without editing desc
- If change detected: PERFORM `1230-EDIT-ALPHANUM-REQD` on description
- If no input errors: SET TTUP-CHANGES-OK-NOT-CONFIRMED

### 9.6 1205-COMPARE-OLD-NEW (lines 783-812)

Compares (case-insensitive, trimmed) `TTUP-NEW-TTYP-TYPE` vs `TTUP-OLD-TTYP-TYPE` AND `TTUP-NEW-TTYP-TYPE-DESC` vs `TTUP-OLD-TTYP-TYPE-DESC`. Sets `NO-CHANGES-FOUND` or `CHANGE-HAS-OCCURRED`.

### 9.7 1210-EDIT-TRANTYPE (lines 820-847)

- Uses `1245-EDIT-NUM-REQD`: must be supplied, must be numeric, must not be zero
- If valid: normalizes to zero-padded 2-digit via NUMVAL + INSPECT REPLACING SPACES BY ZEROS

### 9.8 2000-DECIDE-ACTION (lines 978-1082)

State machine second dispatch. Called after input edits, determines the next TTUP-CHANGE-ACTION state:
- TTUP-DETAILS-NOT-FETCHED: reads DB2 via `9000-READ-TRANTYPE`
- TTUP-CONFIRM-DELETE + PF12: SET WS-DELETE-WAS-CANCELLED
- TTUP-CHANGES-OK-NOT-CONFIRMED + PF12: SET WS-UPDATE-WAS-CANCELLED, TTUP-CHANGES-BACKED-OUT
- TTUP-SHOW-DETAILS: if no errors and changes present → TTUP-CHANGES-OK-NOT-CONFIRMED
- TTUP-CREATE-NEW-RECORD (PF05 not-found): stays CREATE
- TTUP-CHANGES-OKAYED-AND-DONE: reset to TTUP-SHOW-DETAILS

### 9.9 3000-SEND-MAP (lines 1089-1104)

Calls: `3100-SCREEN-INIT`, `3200-SETUP-SCREEN-VARS`, `3250-SETUP-INFOMSG`, `3300-SETUP-SCREEN-ATTRS`, `3390-SETUP-INFOMSG-ATTRS`, `3391-SETUP-PFKEY-ATTRS`, `3400-SEND-SCREEN`.

### 9.10 3100-SCREEN-INIT (lines 1110-1134)

Clear CTRTUPAO, set TITLE01/02, TRNNAME, PGMNAME, CURDATE (MM/DD/YY), CURTIME.

### 9.11 3200-SETUP-SCREEN-VARS (lines 1140-1171)

Based on state:
- TTUP-DETAILS-NOT-FETCHED: `3201-SHOW-INITIAL-VALUES` (blank fields)
- TTUP-SHOW-DETAILS, TTUP-CONFIRM-DELETE, etc.: `3202-SHOW-ORIGINAL-VALUES` (old type+desc from commarea)
- TTUP-CHANGES-MADE, TTUP-CHANGES-NOT-OK, TTUP-DETAILS-NOT-FOUND, TTUP-CREATE-NEW-RECORD, TTUP-CHANGES-OKAYED-AND-DONE: `3203-SHOW-UPDATED-VALUES` (new type+desc from commarea)

### 9.12 3250-SETUP-INFOMSG (lines 1210-1265)

Sets WS-INFO-MSG based on state:

| State | Message |
|---|---|
| TTUP-DETAILS-NOT-FETCHED / TTUP-INVALID-SEARCH-KEYS | 'Enter transaction type to be maintained' |
| TTUP-DETAILS-NOT-FOUND | 'Press F05 to add. F12 to cancel' |
| TTUP-SHOW-DETAILS / TTUP-CHANGES-BACKED-OUT | 'Update transaction type details shown.' |
| TTUP-CHANGES-NOT-OK | 'Update transaction type details shown.' |
| TTUP-CONFIRM-DELETE | 'Delete this record ? Press F4 to confirm' |
| TTUP-DELETE-FAILED | 'Changes unsuccessful' |
| TTUP-DELETE-DONE | 'Delete successful.' |
| TTUP-CREATE-NEW-RECORD | 'Enter new transaction type details.' |
| TTUP-CHANGES-OK-NOT-CONFIRMED | 'Changes validated.Press F5 to save' |
| TTUP-CHANGES-OKAYED-AND-DONE | 'Changes committed to database' |
| TTUP-CHANGES-OKAYED-LOCK-ERROR / TTUP-CHANGES-OKAYED-BUT-FAILED | 'Changes unsuccessful' |

Message is center-justified within 40-character field.

### 9.13 3300-SETUP-SCREEN-ATTRS (lines 1269-1364)

- `3310-PROTECT-ALL-ATTRS`: sets DFHBMPRF (protect) on TRTYPCD, TRTYDSC, INFOMSG
- `3320-UNPROTECT-FEW-ATTRS`: sets DFHBMFSE on TRTYDSC for editing states
- Cursor positioning via TRTYPCDL or TRTYDSCL = -1
- Color: DFHRED on TRTYPCDC if FLG-TRANFILTER-NOT-OK or TTUP-DELETE-FAILED
- Uses `COPY CSSETATY REPLACING ==(TESTVAR1)== BY ==DESCRIPTION==` etc. for description field attribute setup

### 9.14 3391-SETUP-PFKEY-ATTRS (lines 1397-1423)

Activates/deactivates PF key labels:
- ENTER key label: dark (DFHBMDAR) when TTUP-CONFIRM-DELETE; bright (DFHBMASB) otherwise
- F4=Delete: bright when TTUP-SHOW-DETAILS or TTUP-CONFIRM-DELETE
- F5=Save: bright when TTUP-CHANGES-OK-NOT-CONFIRMED or TTUP-DETAILS-NOT-FOUND
- F12=Cancel: bright when TTUP-CHANGES-OK-NOT-CONFIRMED, TTUP-SHOW-DETAILS, TTUP-DETAILS-NOT-FOUND, TTUP-CONFIRM-DELETE, TTUP-CREATE-NEW-RECORD

### 9.15 9000-READ-TRANTYPE (lines 1447-1468)

INITIALIZE TTUP-OLD-DETAILS; calls `9100-GET-TRANSACTION-TYPE`; if not error, calls `9500-STORE-FETCHED-DATA`.

### 9.16 9500-STORE-FETCHED-DATA (lines 1517-1529)

Moves DB2 fetch results into TTUP-OLD-DETAILS: `DCL-TR-TYPE → TTUP-OLD-TTYP-TYPE`, `DCL-TR-DESCRIPTION-TEXT(1:DCL-TR-DESCRIPTION-LEN) → TTUP-OLD-TTYP-TYPE-DESC`.

### 9.17 ABEND-ROUTINE (lines 1675-1699)

- Sets default ABEND-MSG if not already set
- `EXEC CICS SEND FROM(ABEND-DATA) LENGTH(LENGTH OF ABEND-DATA) NOHANDLE ERASE`
- `EXEC CICS HANDLE ABEND CANCEL`
- `EXEC CICS ABEND ABCODE(ABEND-CODE)` — abend code is '9999'

---

## 10. Copybooks Referenced

| Copybook | Location in Source | Purpose |
|---|---|---|
| CSUTLDWY | Line 76 | Generic date edit WS variables CCYYMMDD |
| CVCRD01Y | Line 241 | Card common WS (CC-WORK-AREA) |
| DFHBMSCA | Line 257 | BMS attribute constants |
| DFHAID | Line 258 | AID key definitions |
| COTTL01Y | Line 262 | Screen title text |
| COTRTUP | Line 265 | BMS symbolic map CTRTUPAI / CTRTUPAO |
| CSDAT01Y | Line 268 | Date/time working storage |
| CSMSG01Y | Line 271 | Common message definitions |
| CSMSG02Y | Line 274 | Abend variables (ABEND-DATA, ABEND-CULPRIT, etc.) |
| CSUSR01Y | Line 277 | Signed-on user data |
| SQLCA | Line 282 | DB2 SQL Communications Area |
| DCLTRTYP | Line 286 | DB2 host variables for TRANSACTION_TYPE |
| DCLTRCAT | Line 288 | DB2 host variables for TRCAT (NOT AVAILABLE FOR INSPECTION — no SQL use observed) |
| COCOM01Y | Line 292 | Application COMMAREA (CARDDEMO-COMMAREA) |
| CSSETATY | Line 1358 (with REPLACING) | Screen attribute setting template |
| CSSTRPFY | Line 1671 | PF key mapping common procedure |

---

## 11. Input Validation Rules (Business Logic)

| Field | Rule | Paragraph | Error Message |
|---|---|---|---|
| Transaction Type Code | Must be supplied | `1245-EDIT-NUM-REQD` | 'Tran Type code must be supplied.' |
| Transaction Type Code | Must be numeric | `1245-EDIT-NUM-REQD` | 'Tran Type code must be numeric.' |
| Transaction Type Code | Must not be zero | `1245-EDIT-NUM-REQD` | 'Tran Type code must not be zero.' |
| Description | Must be supplied | `1230-EDIT-ALPHANUM-REQD` | 'Transaction Desc must be supplied.' |
| Description | Alphanumeric only (A-Z, a-z, 0-9, space) | `1230-EDIT-ALPHANUM-REQD` | 'Transaction Desc can have numbers or alphabets only.' |
| Changes detection | Old and new values compared case-insensitively | `1205-COMPARE-OLD-NEW` | 'No change detected with respect to values fetched.' |

---

## 12. VSAM File Operations

None. All data access is via DB2.

---

## 13. MQ Operations

None.

---

## 14. Error Handling

| Condition | State Set | User Message |
|---|---|---|
| Type code not found in DB2 | TTUP-DETAILS-NOT-FOUND | 'No record found for this key in database' |
| DB2 SELECT error (SQLCODE < 0) | FLG-TRANFILTER-NOT-OK | 'Error accessing: TRANSACTION_TYPE table. SQLCODE:... :SQLERRM' |
| UPDATE not found (+100) | Falls into INSERT path | — |
| UPDATE lock error (-911) | TTUP-CHANGES-OKAYED-LOCK-ERROR | 'Could not lock record for update' |
| UPDATE other failure | TTUP-CHANGES-OKAYED-BUT-FAILED | 'Error updating: TRANSACTION_TYPE Table. SQLCODE:...' |
| INSERT failure | TABLE-UPDATE-FAILED | 'Error inserting record into: TRANSACTION_TYPE Table. SQLCODE:...' |
| DELETE referential integrity (-532) | RECORD-DELETE-FAILED | 'Please delete associated child records first: SQLCODE:...' |
| DELETE other failure | RECORD-DELETE-FAILED, TTUP-DELETE-FAILED | 'Delete failed with message: SQLCODE:...' |
| Unexpected state in WHEN OTHER | ABEND-ROUTINE | 'UNEXPECTED DATA SCENARIO' (abend code 0001) |
| CICS abend (HANDLE ABEND) | ABEND-ROUTINE | Raw abend-data sent to terminal; CICS ABEND with code 9999 |

---

## 15. Inter-Program Interactions

| Program | Mechanism | Condition |
|---|---|---|
| COADM01C | `EXEC CICS XCTL` | PF03 with no prior program in commarea |
| COTRTLIC | `EXEC CICS XCTL` (via CDEMO-FROM-PROGRAM) | PF03 when called from COTRTLIC |
| COTRTLIC | Returns commarea | COTRTLIC transfers here via XCTL; COTRTUPC returns via CICS RETURN TRANSID(CTTU) |

---

## 16. Open Questions and Gaps

1. **DCLTRCAT**: Included at line 288 but no SQL statements referencing TRCAT were observed in the analyzed portion. Its purpose in this program is unclear without the full compiled expansion.

2. **DCLTRTYP**: Not available. The fields `DCL-TR-TYPE`, `DCL-TR-DESCRIPTION`, `DCL-TR-DESCRIPTION-TEXT`, and `DCL-TR-DESCRIPTION-LEN` are referenced in SQL but their PIC clauses are unknown.

3. **CSSETATY copybook**: Used with REPLACING clause to set description field attributes. The template logic is not directly visible — behavior inferred from the REPLACING clause pattern.

4. **`9700-INSERT-RECORD` being the "update fallback"**: When UPDATE returns +100 (record vanished between fetch and update), the program silently falls through to INSERT. This is an unusual design — it could create a duplicate if concurrent inserts occur. Requires review of DB2 isolation level in production.
