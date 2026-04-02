# Technical Specification: COTRTLIC

## 1. Executive Summary

COTRTLIC is an **online CICS COBOL program** that provides a paginated list screen for the `CARDDEMO.TRANSACTION_TYPE` DB2 table. It serves as the primary list/selection interface from which an operator can browse transaction type records with optional filter criteria, then select individual records for update (action code `U`) or delete (action code `D`). Selection transfers control to the update/add program COTRTUPC. DB2 cursor-based paging (forward cursor `C-TR-TYPE-FORWARD` and backward cursor `C-TR-TYPE-BACKWARD`) supports bidirectional page navigation. The screen displays up to 7 records at a time on BMS mapset COTRTLI, map CTRTLIA, via transaction `CTLI`.

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COTRTLIC.cbl | CICS online COBOL program | `app/app-transaction-type-db2/cbl/COTRTLIC.cbl` |
| COTRTLI.bms | BMS mapset | `app/app-transaction-type-db2/bms/COTRTLI.bms` |
| COTRTLI.cpy | BMS-generated symbolic map copybook | `app/app-transaction-type-db2/cpy-bms/COTRTLI.cpy` |
| CSDB2RWY.cpy | DB2 common working-storage copybook | `app/app-transaction-type-db2/cpy/CSDB2RWY.cpy` |
| CSDB2RPY.cpy | DB2 common procedure copybook | `app/app-transaction-type-db2/cpy/CSDB2RPY.cpy` |
| COCOM01Y | Application COMMAREA copybook | Standard CardDemo (not in this directory) |
| CVCRD01Y | Card working-storage copybook | Standard CardDemo |
| COTTL01Y | Screen title copybook | Standard CardDemo |
| CVACT02Y | Card account record layout | Standard CardDemo |
| CSDAT01Y | Current date variables | Standard CardDemo |
| CSMSG01Y | Common messages | Standard CardDemo |
| CSUSR01Y | Signed-on user data | Standard CardDemo |
| DFHBMSCA | IBM BMS attribute constants | IBM-supplied |
| DFHAID | IBM AID key constants | IBM-supplied |
| DCLTRTYP | DB2 DCLGEN for TRANSACTION_TYPE | NOT AVAILABLE FOR INSPECTION |

---

## 3. Program Identity

| Attribute | Value | Source |
|---|---|---|
| Program-ID | COTRTLIC | Line 26 |
| Transaction ID | CTLI | Line 44 (LIT-THISTRANID) |
| Mapset | COTRTLI | Line 45 (LIT-THISMAPSET) |
| Map | CTRTLIA | Line 46 (LIT-THISMAP) |
| Layer | Business logic | Line 3 |
| Function | List Transaction Types for updates and deletes; demonstrates DB2 cursor paging | Lines 4-5 |
| Max screen rows | 7 | Line 60 (WS-MAX-SCREEN-LINES) |

---

## 4. COMMAREA Structure

COTRTLIC uses a two-part COMMAREA:

**Part 1 — CARDDEMO-COMMAREA** (from copybook COCOM01Y): Application-wide navigation state including `CDEMO-FROM-PROGRAM`, `CDEMO-TO-PROGRAM`, `CDEMO-FROM-TRANID`, `CDEMO-PGM-ENTER`/`CDEMO-PGM-REENTER`, `CDEMO-USRTYP-ADMIN`, `CDEMO-LAST-MAPSET`, `CDEMO-LAST-MAP`, `CCARD-AID-*` (mapped PF key flags), `CCARD-ERROR-MSG`, `CCARD-NEXT-PROG/MAPSET/MAP`.

**Part 2 — WS-THIS-PROGCOMMAREA** (lines 377-419): Program-specific paging and row-selection state.

| Field | PIC / Type | Purpose |
|---|---|---|
| WS-CA-TYPE-CD | X(02) | Current type-code filter retained across pages |
| WS-CA-TYPE-CD-N | 9(02) REDEFINES | Numeric form of above |
| WS-CA-TYPE-DESC | X(50) | Current description filter retained across pages |
| WS-CA-ALL-ROWS-OUT | X(364) | 7 rows × 52 chars — screen data preserved in commarea |
| WS-CA-SCREEN-ROWS-OUT (OCCURS 7) | — | Array redefinition of above |
| WS-CA-ROW-TR-CODE-OUT(n) | X(02) | Type code for row n |
| WS-CA-ROW-TR-DESC-OUT(n) | X(50) | Description for row n |
| WS-CA-ROW-SELECTED | S9(4) COMP | Row index of currently selected row |
| WS-CA-LAST-TR-CODE | X(02) | Last type code on current page (start key for next page) |
| WS-CA-FIRST-TR-CODE | X(02) | First type code on current page (start key for this page) |
| WS-CA-SCREEN-NUM | 9(1) | Current page number (1 = first page) |
| WS-CA-LAST-PAGE-DISPLAYED | 9(1) | 0 = last page shown; 9 = not shown |
| WS-CA-NEXT-PAGE-IND | X(1) | 'Y' = next page exists; LOW-VALUES = no next page |
| WS-CA-DELETE-FLAG | X | 'Y' = delete requested/pending |
| WS-CA-UPDATE-FLAG | X | 'Y' = update requested/pending |
| WS-COMMAREA | X(2000) | Combined COMMAREA buffer for CICS RETURN |

---

## 5. DB2 Declarations

### 5.1 Table

| Table | Schema |
|---|---|
| TRANSACTION_TYPE | CARDDEMO |

### 5.2 Cursor Declarations

**C-TR-TYPE-FORWARD** (lines 338-352) — used by `8000-READ-FORWARD`:

```sql
DECLARE C-TR-TYPE-FORWARD CURSOR FOR
    SELECT TR_TYPE, TR_DESCRIPTION
      FROM CARDDEMO.TRANSACTION_TYPE
     WHERE TR_TYPE >= :WS-START-KEY
       AND ((:WS-EDIT-TYPE-FLAG = '1' AND TR_TYPE = :WS-TYPE-CD-FILTER)
             OR (:WS-EDIT-TYPE-FLAG <> '1'))
       AND ((:WS-EDIT-DESC-FLAG = '1'
             AND TR_DESCRIPTION LIKE TRIM(:WS-TYPE-DESC-FILTER))
             OR (:WS-EDIT-DESC-FLAG <> '1'))
     ORDER BY TR_TYPE
```

**C-TR-TYPE-BACKWARD** (lines 354-368) — used by `8100-READ-BACKWARDS`:

```sql
DECLARE C-TR-TYPE-BACKWARD CURSOR FOR
    SELECT TR_TYPE, TR_DESCRIPTION
      FROM CARDDEMO.TRANSACTION_TYPE
     WHERE TR_TYPE < :WS-START-KEY
       AND ((:WS-EDIT-TYPE-FLAG = '1' AND TR_TYPE = :WS-TYPE-CD-FILTER)
             OR (:WS-EDIT-TYPE-FLAG <> '1'))
       AND ((:WS-EDIT-DESC-FLAG = '1'
             AND TR_DESCRIPTION LIKE TRIM(:WS-TYPE-DESC-FILTER))
             OR (:WS-EDIT-DESC-FLAG <> '1'))
     ORDER BY TR_TYPE DESC
```

### 5.3 Filter Logic

- `WS-EDIT-TYPE-FLAG = '1'` activates the exact-match type code filter
- `WS-EDIT-DESC-FLAG = '1'` activates the LIKE description filter
- Description filter is wrapped with `%` wildcards at input time (paragraph `1230-EDIT-DESC`, lines 1155-1163): e.g., user enters "PAYMENT" → filter becomes `'%PAYMENT%'`

### 5.4 Additional SQL Statements

**9100-CHECK-FILTERS** (lines 1801-1836) — COUNT query to validate filters produce results:

```sql
SELECT COUNT(1) INTO :WS-RECORDS-COUNT
  FROM CARDDEMO.TRANSACTION_TYPE
 WHERE ((:WS-EDIT-TYPE-FLAG = '1' AND TR_TYPE = :WS-TYPE-CD-FILTER)
         OR :WS-EDIT-TYPE-FLAG <> '1')
   AND ((:WS-EDIT-DESC-FLAG = '1'
         AND TR_DESCRIPTION LIKE TRIM(:WS-TYPE-DESC-FILTER))
         OR :WS-EDIT-DESC-FLAG <> '1')
```

**9200-UPDATE-RECORD** (lines 1837-~1900) — Inline update from list screen:

```sql
UPDATE CARDDEMO.TRANSACTION_TYPE
   SET TR_DESCRIPTION = :DCL-TR-DESCRIPTION
 WHERE TR_TYPE        = :DCL-TR-TYPE
```

Followed by `EXEC CICS SYNCPOINT` on SQLCODE = 0.

**9300-DELETE-RECORD** (lines ~1900-~1960) — Inline delete from list screen:

```sql
DELETE FROM CARDDEMO.TRANSACTION_TYPE
 WHERE TR_TYPE = :DCL-TR-TYPE
```

Followed by `EXEC CICS SYNCPOINT` on SQLCODE = 0.

**9998-PRIMING-QUERY** (via CSDB2RPY.cpy, lines 21-48 of that file):

```sql
SELECT 1 INTO :WS-DUMMY-DB2-INT
  FROM SYSIBM.SYSDUMMY1
  FETCH FIRST 1 ROW ONLY
```

Executed at startup to verify DB2 connectivity before any user query.

---

## 6. CICS Commands

| Command | Location | Purpose |
|---|---|---|
| `EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE)` | [referenced in architecture; full flow follows COTRTUPC pattern] | Catch unexpected abends |
| `EXEC CICS RECEIVE MAP(CTRTLIA) MAPSET(COTRTLI) INTO(CTRTLIAI)` | `1100-RECEIVE-SCREEN` (lines 930-935) | Receive data from terminal |
| `EXEC CICS SEND MAP(LIT-THISMAP) MAPSET(LIT-THISMAPSET) FROM(CTRTLIAO) CURSOR ERASE FREEKB` | `2600-SEND-SCREEN` (lines 1588-1595) | Send updated screen to terminal |
| `EXEC CICS SYNCPOINT` | `9200-UPDATE-RECORD`, `9300-DELETE-RECORD` | Commit DB2 changes |
| `EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)` | PF03 handler (lines 620-623) | Exit to admin menu or calling program |
| `EXEC CICS XCTL PROGRAM(LIT-ADDTPGM) COMMAREA(CARDDEMO-COMMAREA)` | PF02 handler (lines 648-651) | Transfer to COTRTUPC (add new type) |
| `EXEC CICS RETURN TRANSID(CTLI) COMMAREA(WS-COMMAREA) LENGTH(...)` | `COMMON-RETURN` (lines 910-914) | Return to CICS with pseudo-conversational re-entry |
| `EXEC CICS SEND FROM(ABEND-DATA) LENGTH(...) NOHANDLE ERASE` | `SEND-LONG-TEXT` (via DB2 error path) | Display error text on terminal |

---

## 7. Screen Flow and PF Key Handling

| AID Key | Context Condition | Action |
|---|---|---|
| PF03 | Any | SYNCPOINT then XCTL to calling program (admin menu or CDEMO-FROM-PROGRAM) |
| PF02 | From this program | XCTL to COTRTUPC (add new transaction type) |
| PF07 | First page | Re-read forward from first key (already on first page) |
| PF07 | Not first page | `8100-READ-BACKWARDS`, decrement page number |
| PF08 | Next page exists | `8000-READ-FORWARD` from WS-CA-LAST-TR-CODE, increment page number |
| ENTER | Deletes requested > 0 | Re-read to show confirmation; then PF10 confirms actual delete |
| ENTER | Updates requested > 0 | Re-read to show inline edit row |
| PF10 | Deletes requested > 0 | `9300-DELETE-RECORD` |
| PF10 | Updates requested > 0 | `9200-UPDATE-RECORD` |
| PF10 | Filter/selection changed | Treated as ENTER |
| INVALID KEY | Any | Re-set to ENTER, re-display |

Valid PF keys (line 575-583): ENTER, PF02, PF03, PF07, PF08, PF10 (only when delete or update requested).

---

## 8. PROCEDURE DIVISION — Paragraph-by-Paragraph Logic

### 8.1 0000-MAIN (lines 498-916)

Entry point. Sequence:
1. `EXEC CICS HANDLE ABEND` (implied from architecture)
2. INITIALIZE working storage
3. Set `WS-TRANID = 'CTLI'`
4. Clear `WS-RETURN-MSG`
5. **COMMAREA retrieval**: If `EIBCALEN = 0` (first entry), initialize both commarea halves; else unpack DFHCOMMAREA into `CARDDEMO-COMMAREA` and `WS-THIS-PROGCOMMAREA`
6. If entering fresh from menu (CDEMO-PGM-ENTER and not from this program), or PF03 from COTRTUPC: reset paging state to page 1
7. If from this program with data: PERFORM `1000-RECEIVE-MAP`
8. Validate PF key via inline IF block (lines 575-587)
9. PF03 exit logic (lines 591-625)
10. PF02 to COTRTUPC (lines 630-652)
11. Reset `CA-LAST-PAGE-NOT-SHOWN` if not PF08 (line 660)
12. Handle PF10 with changed filter (treat as ENTER, line 666-678)
13. **`9998-PRIMING-QUERY`** — DB2 connectivity check
14. **Main EVALUATE** (lines 698-897) — dispatches to read/send operations

### 8.2 1000-RECEIVE-MAP (lines 919-928)

Calls `1100-RECEIVE-SCREEN` then `1200-EDIT-INPUTS`.

### 8.3 1100-RECEIVE-SCREEN (lines 930-954)

- `EXEC CICS RECEIVE MAP INTO(CTRTLIAI)`
- Moves `TRTYPEI` → `WS-IN-TYPE-CD`, `TRDESCI` → `WS-IN-TYPE-DESC`
- Loops I=1 to 7: moves `TRTSELI(I)` → `WS-EDIT-SELECT(I)`, `TRTTYPI(I)` → `WS-ROW-TR-CODE-IN(I)`, and `TRTYPDI(I)` → `WS-ROW-TR-DESC-IN(I)` (trimmed)

### 8.4 1200-EDIT-INPUTS (lines 960-976)

Calls:
1. `1210-EDIT-ARRAY` — validate row selection flags
2. `1230-EDIT-DESC` — validate description filter
3. `1220-EDIT-TYPECD` — validate type code filter
4. `1290-CROSS-EDITS` — if filters valid, COUNT query to confirm records exist

### 8.5 1210-EDIT-ARRAY (lines 982-1053)

- Counts `D`, `U`, SPACE/LOW-VALUES in `WS-EDIT-SELECT-FLAGS`
- Computes `WS-ACTIONS-REQUESTED`, `WS-DELETES-REQUESTED`, `WS-UPDATES-REQUESTED`
- Validates only one action at a time is selected
- For update rows: calls `1211-EDIT-ARRAY-DESC` to detect description changes

### 8.6 1211-EDIT-ARRAY-DESC (lines 1060-1094)

- Compares `WS-ROW-TR-DESC-IN(I)` against `WS-CA-ROW-TR-DESC-OUT(I)` (commarea copy)
- Sets `CHANGES-HAVE-OCCURRED` or `NO-CHANGES-FOUND`
- Validates description alphanumeric via `1240-EDIT-ALPHANUM-REQD`

### 8.7 1220-EDIT-TYPECD (lines 1096-1140)

- If type code blank/zero: set `FLG-TYPEFILTER-BLANK`, clear filter
- If not numeric: set `FLG-TYPEFILTER-NOT-OK`, set INPUT-ERROR
- Otherwise: move to `WS-TYPE-CD-FILTER`, set `FLG-TYPEFILTER-ISVALID`
- Detects filter change vs commarea (`FLG-TYPEFILTER-CHANGED-YES/NO`)

### 8.8 1230-EDIT-DESC (lines 1142-1178)

- If blank: set `FLG-DESCFILTER-BLANK`
- If supplied: wraps in `%..%` wildcard, sets `FLG-DESCFILTER-ISVALID`
- Detects filter change vs commarea

### 8.9 2000-SEND-MAP (lines 1274-1292)

Calls in sequence:
1. `2100-SCREEN-INIT` — clear output map, set titles/date/time/page number
2. `2200-SETUP-ARRAY-ATTRIBS` — set attributes per row (protect, color, cursor position)
3. `2300-SCREEN-ARRAY-INIT` — populate row data (type code + description) into map output
4. `2400-SETUP-SCREEN-ATTRS` — set filter field attributes (colors, cursor)
5. `2500-SETUP-MESSAGE` — determine and format informational message
6. `2600-SEND-SCREEN` — `EXEC CICS SEND MAP ... CURSOR ERASE FREEKB`

### 8.10 8000-READ-FORWARD (lines 1603-1724)

- Clears `WS-CA-ALL-ROWS-OUT`
- Calls `9400-OPEN-FORWARD-CURSOR` (OPEN cursor C-TR-TYPE-FORWARD)
- LOOPs UNTIL `READ-LOOP-EXIT`:
  - `FETCH C-TR-TYPE-FORWARD INTO :DCL-TR-TYPE, :DCL-TR-DESCRIPTION`
  - SQLCODE=0: stores row in `WS-CA-ROW-TR-CODE-OUT(n)` / `WS-CA-ROW-TR-DESC-OUT(n)`
  - After filling 7 rows: does a look-ahead FETCH to determine if next page exists, sets `CA-NEXT-PAGE-EXISTS` or `CA-NEXT-PAGE-NOT-EXISTS`
  - SQLCODE=+100: sets `CA-NEXT-PAGE-NOT-EXISTS`
- Calls `9450-CLOSE-FORWARD-CURSOR`

### 8.11 8100-READ-BACKWARDS (lines 1727-1799)

- Reverses row array (fills from row 7 downward)
- Opens `C-TR-TYPE-BACKWARD`, FETCHes up to 7 rows in descending key order
- Fills `WS-CA-EACH-ROW-OUT` array from position 7 downward
- Closes cursor via `9550-CLOSE-BACK-CURSOR`

### 8.12 9998-PRIMING-QUERY (from CSDB2RPY.cpy)

Executes `SELECT 1 FROM SYSIBM.SYSDUMMY1`. Sets `WS-DB2-ERROR` on failure; program calls `SEND-LONG-TEXT` and returns early.

### 8.13 9999-FORMAT-DB2-MESSAGE (from CSDB2RPY.cpy)

Calls IBM utility `DSNTIAC` (`CALL LIT-DSNTIAC USING DFHEIBLK DFHCOMMAREA SQLCA WS-DSNTIAC-FORMATTED WS-DSNTIAC-LRECL`) to format DB2 error details. Builds WS-LONG-MSG and copies to WS-RETURN-MSG.

### 8.14 COMMON-RETURN (lines 899-915)

- Moves LIT-THISTRANID to CDEMO-FROM-TRANID
- Moves LIT-THISPGM to CDEMO-FROM-PROGRAM
- Assembles `WS-COMMAREA` = CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA
- `EXEC CICS RETURN TRANSID('CTLI') COMMAREA(WS-COMMAREA) LENGTH(...)`

---

## 9. Copybooks Referenced

| Copybook | Declared At | Purpose |
|---|---|---|
| SQLCA | Working-Storage (line 331) | DB2 SQLCA |
| DCLTRTYP | Working-Storage (line 333) | Host variables for TRANSACTION_TYPE |
| CSDB2RWY | `EXEC SQL INCLUDE CSDB2RWY` (line 304) | DB2 common WS: WS-DB2-COMMON-VARS, DSNTIAC vars |
| CVCRD01Y | COPY (line 327) | Card working-storage (CC-WORK-AREA) |
| COCOM01Y | COPY (line 375) | Application COMMAREA (CARDDEMO-COMMAREA) |
| DFHBMSCA | COPY (line 425) | BMS attribute byte constants |
| DFHAID | COPY (line 426) | AID key equates |
| COTTL01Y | COPY (line 430) | Screen title constants (CCDA-TITLE01/02) |
| COTRTLI | COPY (line 433) | BMS symbolic map (CTRTLIAI / CTRTLIAO + REDEFINES) |
| CSDAT01Y | COPY (line 480) | Date/time working storage |
| CSMSG01Y | COPY (line 482) | Common message literals |
| CSUSR01Y | COPY (line 485) | Signed-on user data |
| CVACT02Y | COPY (line 490) | Card account record layout |
| CSDB2RPY | COPY (procedures section) | `9998-PRIMING-QUERY` and `9999-FORMAT-DB2-MESSAGE` procedures |
| CSSTRPFY | COPY (in YYYY-STORE-PFKEY section) | PF key storage common code |

---

## 10. Inter-Program Interactions

| Program | Mechanism | Condition | Direction |
|---|---|---|---|
| COADM01C (admin menu) | `EXEC CICS XCTL` | PF03 with no prior program or from admin | Exits to |
| COTRTUPC | `EXEC CICS XCTL PROGRAM(LIT-ADDTPGM)` | PF02 | Transfers to (add/update) |
| COTRTUPC | Returns via CDEMO-FROM-PROGRAM | After update/delete in COTRTUPC | Returns from |
| DSNTIAC | `CALL LIT-DSNTIAC` | DB2 error formatting | Calls |

---

## 11. Business Rules

| Rule | Location | Description |
|---|---|---|
| Only one action per submit | `1210-EDIT-ARRAY` (lines 1024-1051) | If more than one row has D or U, flag INPUT-ERROR |
| Type code filter must be numeric 2 digits | `1220-EDIT-TYPECD` (lines 1111-1122) | Non-numeric type filter rejects input |
| Description filter uses LIKE with wildcards | `1230-EDIT-DESC` (lines 1155-1163) | User's text is wrapped as `%TEXT%` |
| Row description must be alphanumeric | `1211-EDIT-ARRAY-DESC` / `1240-EDIT-ALPHANUM-REQD` | Alphabets, digits, and spaces only |
| Filter changes reset paging | `1220-EDIT-TYPECD-EXIT` / `1230-EDIT-DESC-EXIT` | `WS-CA-PAGING-VARIABLES` is re-initialized |
| Action change on same row resets CA_DELETE/UPDATE | Logic in `1210-EDIT-ARRAY` | Row selection index change detected |

---

## 12. VSAM File Operations

None. All data access is via DB2.

---

## 13. MQ Operations

None.

---

## 14. Error Handling

| Condition | Response |
|---|---|
| DB2 not accessible (priming query fails) | SEND-LONG-TEXT (error message display), COMMON-RETURN |
| Cursor fetch error | SET WS-DB2-ERROR, format message via DSNTIAC, close cursor, return |
| Invalid action code (not D/U/blank) | SET INPUT-ERROR, WS-MESG-INVALID-ACTION-CODE, re-display |
| More than 1 action selected | SET INPUT-ERROR, WS-MESG-MORE-THAN-1-ACTION, highlight offending rows in RED |
| Filter finds no records | SET INPUT-ERROR, "No Records found for these filter conditions" |
| UPDATE SQL failure | SQLCODE formatted, message placed in WS-RETURN-MSG, re-display |
| DELETE SQL failure | SQLCODE formatted, message placed in WS-RETURN-MSG, re-display |
| ABEND (via HANDLE ABEND) | ABEND-ROUTINE: SEND abend data, CICS ABEND with code '9999' |

---

## 15. Open Questions and Gaps

1. **DCLTRTYP**: Not available for inspection. Host-variable mapping between `DCL-TR-TYPE`, `DCL-TR-DESCRIPTION`, `DCL-TR-DESCRIPTION-TEXT`, and `DCL-TR-DESCRIPTION-LEN` cannot be fully verified without the DCLGEN source.

2. **COTRTLIC.cbl lines after ~1850**: The complete `9200-UPDATE-RECORD` and `9300-DELETE-RECORD` paragraphs plus cursor open/close paragraphs (9400, 9450, 9500, 9550) and `YYYY-STORE-PFKEY` were cut off in reading. The logic described is based on context from earlier in the file plus what is visible.

3. **CSSTRPFY copybook**: The `YYYY-STORE-PFKEY` paragraph is copied via `COPY 'CSSTRPFY'` — this member was not provided. Its content maps EIBAID values to CCARD-AID-* flags in CARDDEMO-COMMAREA.
