# Technical Specification: COTRTLIC

## Program Overview

| Attribute         | Value                                                                         |
|-------------------|-------------------------------------------------------------------------------|
| Program ID        | COTRTLIC                                                                      |
| Source File       | app/app-transaction-type-db2/cbl/COTRTLIC.cbl                                 |
| Language          | COBOL with embedded static DB2 SQL                                            |
| Environment       | CICS online                                                                   |
| Transaction ID    | CTLI                                                                          |
| BMS Mapset        | COTRTLI                                                                       |
| BMS Map           | CTRTLIA                                                                       |
| Function          | List, filter, page, update, and delete transaction type records               |
| Layer             | Business logic — CICS online CRUD with DB2 cursor paging                     |
| Date Written      | Jan 2023                                                                      |

### Purpose

COTRTLIC is the online CICS program for Transaction Type list/update/delete operations. It displays up to 7 transaction type records per page from `CARDDEMO.TRANSACTION_TYPE`, supports forward and backward paging using DB2 cursors, allows inline editing of the description field, and allows deletion with referential integrity handling. It is menu option 5 from the Admin Menu (CA00).

---

## Program Flow

### Entry Point and Commarea Handling

The PROCEDURE DIVISION entry is paragraph `0000-MAIN` (line 498).

**On initial entry (EIBCALEN = 0) or fresh entry from Admin Menu:**
- INITIALIZE CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA
- SET CDEMO-PGM-ENTER TO TRUE
- SET CA-FIRST-PAGE, CA-LAST-PAGE-NOT-SHOWN TO TRUE
- MOVE LIT-THISMAP/MAPSET to CDEMO-LAST-MAP/MAPSET

**On re-entry (EIBCALEN > 0):**
- MOVE DFHCOMMAREA(1:LENGTH OF CARDDEMO-COMMAREA) TO CARDDEMO-COMMAREA
- MOVE DFHCOMMAREA(offset: length) TO WS-THIS-PROGCOMMAREA

**Fresh-entry reset (lines 544-554):**
If entering from Admin menu (CDEMO-PGM-ENTER and CDEMO-FROM-PROGRAM != LIT-THISPGM) or pressing PF3 from CTTU, the commarea is re-initialized and paging is reset to first page.

### Main Control Flow Diagram

```
0000-MAIN
  |
  +--> PERFORM YYYY-STORE-PFKEY
  |
  +--> Validate PFK (CCARD-AID-ENTER/PFK02/PFK03/PFK07/PFK08/PFK10)
  |        Invalid key --> SET CCARD-AID-ENTER
  |
  +--> IF EIBCALEN > 0 AND FROM-PROGRAM = LIT-THISPGM
  |        PERFORM 1000-RECEIVE-MAP
  |
  +--> PFK03: SYNCPOINT + XCTL to calling program
  |
  +--> PFK02: XCTL to COTRTUPC (add screen)
  |
  +--> PERFORM 9998-PRIMING-QUERY  (DB2 connectivity check)
  |        If WS-DB2-ERROR --> SEND-LONG-TEXT + COMMON-RETURN
  |
  +--> EVALUATE TRUE (main dispatch, lines 698-897)
  |        WHEN INPUT-ERROR + filter errors --> re-read + SEND-MAP
  |        WHEN PFK07 + first page --> re-read forward + SEND-MAP
  |        WHEN PFK03 or fresh entry --> read forward + SEND-MAP
  |        WHEN PFK08 + next page exists --> read forward (next page)
  |        WHEN PFK07 + not first page --> read backwards
  |        WHEN ENTER + deletes requested --> read + SEND-MAP (highlight)
  |        WHEN PFK10 + deletes requested --> PERFORM 9300-DELETE-RECORD
  |        WHEN ENTER + updates requested --> read + SEND-MAP (highlight)
  |        WHEN PFK10 + updates requested --> PERFORM 9200-UPDATE-RECORD
  |        WHEN OTHER --> read forward + SEND-MAP
  |
  +--> COMMON-RETURN
         MOVE WS-RETURN-MSG TO CCARD-ERROR-MSG
         Package commarea
         EXEC CICS RETURN TRANSID(CTLI) COMMAREA(WS-COMMAREA)
```

### Paragraph Index

| Paragraph                  | Lines       | Description                                                      |
|----------------------------|-------------|------------------------------------------------------------------|
| 0000-MAIN                  | 498-918     | Entry point; commarea init; PFK validation; main dispatch        |
| COMMON-RETURN              | 899-915     | Package commarea; CICS RETURN                                    |
| 1000-RECEIVE-MAP           | 919-928     | Calls 1100-RECEIVE-SCREEN then 1200-EDIT-INPUTS                  |
| 1100-RECEIVE-SCREEN        | 930-953     | CICS RECEIVE MAP; moves fields to working storage arrays         |
| 1200-EDIT-INPUTS           | 960-976     | Calls edit paragraphs for array, desc filter, type code filter   |
| 1210-EDIT-ARRAY            | 982-1053    | Counts/validates selection flags; detects U/D; multi-select check|
| 1211-EDIT-ARRAY-DESC       | 1060-1090   | For UPDATE-selected rows: validates description is alphanumeric  |
| 1220-EDIT-TYPECD           | 1096-1140   | Validates type code filter (numeric 2-digit or blank)            |
| 1230-EDIT-DESC             | 1142-1178   | Validates description filter; wraps with % wildcards for LIKE    |
| 1240-EDIT-ALPHANUM-REQD    | 1181-1234   | Generic: required alphanumeric field validation                  |
| 1290-CROSS-EDITS           | 1239-1271   | If filter active: calls 9100-CHECK-FILTERS; errors if 0 rows     |
| 2000-SEND-MAP              | 1274-1292   | Orchestrates all screen-init and send sub-paragraphs             |
| 2100-SCREEN-INIT           | 1293-1323   | Clears output map; loads date/time/title/tranid/pgmname/pageno   |
| 2200-SETUP-ARRAY-ATTRIBS   | 1329-1374   | Sets attribute bytes for each of 7 rows based on select/state    |
| 2300-SCREEN-ARRAY-INIT     | 1383-1431   | Loads type code and description into each row output area        |
| 2400-SETUP-SCREEN-ATTRS    | 1438-1498   | Sets filter field attributes and cursor position                 |
| 2500-SETUP-MESSAGE         | 1504-1581   | Sets WS-INFO-MSG and ERRMSG based on state                       |
| 2600-SEND-SCREEN           | 1587-1596   | CICS SEND MAP CTRTLIA ERASE FREEKB CURSOR                        |
| 8000-READ-FORWARD          | 1603-1723   | Opens C-TR-TYPE-FORWARD; fetches up to 7 rows; peeks for next    |
| 8100-READ-BACKWARDS        | 1727-1799   | Opens C-TR-TYPE-BACKWARD; fills rows in reverse order            |
| 9100-CHECK-FILTERS         | 1801-1836   | SELECT COUNT(1) with filter conditions                           |
| 9200-UPDATE-RECORD         | 1837-1893   | UPDATE TRANSACTION_TYPE for selected row; SYNCPOINT on success   |
| 9300-DELETE-RECORD         | 1896-1936   | DELETE TRANSACTION_TYPE for selected row; SYNCPOINT on success   |
| 9400-OPEN-FORWARD-CURSOR   | 1942-1964   | OPEN C-TR-TYPE-FORWARD                                           |
| 9450-CLOSE-FORWARD-CURSOR  | 1970-1992   | CLOSE C-TR-TYPE-FORWARD                                          |
| 9500-OPEN-BACKWARD-CURSOR  | 1997-2020   | OPEN C-TR-TYPE-BACKWARD                                          |
| 9550-CLOSE-BACK-CURSOR     | 2026-2048   | CLOSE C-TR-TYPE-BACKWARD                                         |
| 9998-PRIMING-QUERY         | (CSDB2RPY)  | SELECT 1 FROM SYSIBM.SYSDUMMY1 to verify DB2 connectivity        |
| 9999-FORMAT-DB2-MESSAGE    | (CSDB2RPY)  | CALL DSNTIAC to format DB2 error into WS-LONG-MSG                |
| YYYY-STORE-PFKEY           | (CSSTRPFY)  | Stores/remaps PF key from EIBAID into CCARD-AID-xxx flags        |
| SEND-LONG-TEXT             | 2085-2095   | Debug: CICS SEND TEXT from WS-LONG-MSG then CICS RETURN          |

---

## Data Structures

### Working Storage — Constants

| Field                    | Value         | Purpose                                        |
|--------------------------|---------------|------------------------------------------------|
| LIT-THISPGM              | 'COTRTLIC'    | This program's name                            |
| LIT-THISTRANID           | 'CTLI'        | This transaction ID                            |
| LIT-THISMAPSET           | 'COTRTLI'     | This mapset name                               |
| LIT-THISMAP              | 'CTRTLIA'     | This map name                                  |
| LIT-ADMINPGM             | 'COADM01C'    | Admin menu program                             |
| LIT-ADMINTRANID          | 'CA00'        | Admin menu transaction                         |
| LIT-ADDTPGM              | 'COTRTUPC'    | Add/Update transaction type program            |
| LIT-ADDTTRANID           | 'CTTU'        | Add/Update transaction ID                      |
| LIT-ADDTMAPSET           | 'COTRTUP'     | Add/Update mapset                              |
| LIT-ADDTMAP              | 'CTRTUPA'     | Add/Update map                                 |
| LIT-DSNTIAC              | 'DSNTIAC'     | DB2 message formatting utility (literal)       |
| LIT-DELETE-FLAG          | 'D'           | Selection action: delete                       |
| LIT-UPDATE-FLAG          | 'U'           | Selection action: update                       |
| WS-MAX-SCREEN-LINES      | 7             | Maximum rows displayed per page                |

### Working Storage — Flags and Edit Variables

| Field                          | Type    | 88-levels                                           | Purpose                                 |
|--------------------------------|---------|-----------------------------------------------------|-----------------------------------------|
| WS-INPUT-FLAG                  | X(1)    | INPUT-OK ('0'/' '/LOW-V), INPUT-ERROR ('1')         | Overall input validation flag           |
| WS-EDIT-TYPE-FLAG              | X(1)    | FLG-TYPEFILTER-NOT-OK, -ISVALID, -BLANK             | Type code filter validation             |
| WS-EDIT-DESC-FLAG              | X(1)    | FLG-DESCFILTER-NOT-OK, -ISVALID, -BLANK             | Description filter validation           |
| WS-TYPEFILTER-CHANGED          | X(1)    | FLG-TYPEFILTER-CHANGED-NO/YES                       | Detects filter change (resets paging)   |
| WS-DESCFILTER-CHANGED          | X(1)    | FLG-DESCFILTER-CHANGED-NO/YES                       | Detects filter change                   |
| WS-ROW-RECORDS-CHANGED(1:7)    | X(1)x7  | FLG-ROW-DESCR-CHANGED-NO/YES                        | Per-row: description changed            |
| WS-DELETE-STATUS               | X(1)    | FLG-DELETED-NO/YES                                  | Whether delete completed                |
| WS-UPDATE-STATUS               | X(1)    | FLG-UPDATED-NO/YES, FLG-UPDATE-COMPLETED            | Whether update completed                |
| WS-ROW-SELECTION-CHANGED       | X(1)    | -NO/YES                                             | Whether selected row index changed      |
| WS-BAD-SELECTION-ACTION        | X(1)    | -NO/YES                                             | Invalid action code or >1 action        |
| WS-ARRAY-DESCRIPTION-FLGS      | X(1)    | FLG-ROW-DESCRIPTION-ISVALID, -NOT-OK, -BLANK        | Per-selected-row description flag       |
| WS-DATACHANGED-FLAG            | X(1)    | NO-CHANGES-FOUND ('0'), CHANGES-HAVE-OCCURRED ('1') | Whether user actually changed data      |
| FLG-PROTECT-SELECT-ROWS        | X(1)    | -NO/YES                                             | Whether select column is protected      |

### Working Storage — Screen Input Array

```
WS-SCREEN-DATA-IN              PIC X(364)     -- 7 rows x 52 bytes
  FILLER REDEFINES WS-ALL-ROWS-IN:
    WS-SCREEN-ROWS-IN OCCURS 7 TIMES
      WS-EACH-ROW-IN
        WS-EACH-TTYP-IN
          WS-ROW-TR-CODE-IN(i)   PIC X(02)    -- transaction type code
          WS-ROW-TR-DESC-IN(i)   PIC X(50)    -- description (from screen)
```

### Working Storage — Action Counters

| Field                   | Type         | Description                                  |
|-------------------------|--------------|----------------------------------------------|
| WS-EDIT-SELECT-COUNTER  | S9(04) COMP-3| General counter                              |
| WS-EDIT-SELECT-FLAGS    | X(7)         | Per-row selection: D/U/blank/LOW-V           |
| WS-EDIT-SELECT(i)       | X(1) x7      | Select field value for row i (redefines)     |
| SELECT-OK(i)            | 88           | Values 'D', 'U'                              |
| DELETE-REQUESTED-ON(i)  | 88           | Value 'D'                                    |
| UPDATE-REQUESTED-ON(i)  | 88           | Value 'U'                                    |
| WS-EDIT-SELECT-ERRORS(i)| X(1) x7      | Per-row error flag '1'                       |
| I                       | S9(4) COMP   | Loop subscript                               |
| I-SELECTED              | S9(4) COMP   | Subscript of selected row                    |
| WS-ACTIONS-REQUESTED    | S9(04) COMP-3| Total actions on screen                      |
| WS-DELETES-REQUESTED    | S9(04) COMP-3| Count of D selections                        |
| WS-UPDATES-REQUESTED    | S9(04) COMP-3| Count of U selections                        |
| WS-VALID-ACTIONS-SELECTED| S9(04) COMP-3| Sum of valid (D+U) actions                  |

### Working Storage — Data Filters

| Field                      | Type    | Description                                                      |
|----------------------------|---------|------------------------------------------------------------------|
| WS-START-KEY               | X(02)   | Cursor start key for forward/backward paging                     |
| WS-TYPE-CD-FILTER          | X(02)   | Type code to filter by (blank = no filter)                       |
| WS-TYPE-DESC-FILTER        | X(52)   | Description LIKE pattern (wraps input with %)                    |
| WS-TYPE-CD-DELETE-FILTER   | complex | Parenthesized IN-list structure for delete key list              |

### Commarea Structure (WS-THIS-PROGCOMMAREA)

This section is appended to CARDDEMO-COMMAREA (from COCOM01Y) in WS-COMMAREA (PIC X(2000)).

| Field                       | Type         | Description                                           |
|-----------------------------|--------------|-------------------------------------------------------|
| WS-CA-TYPE-CD               | X(02)        | Current type code filter value                        |
| WS-CA-TYPE-DESC             | X(50)        | Current description filter value                      |
| WS-CA-ALL-ROWS-OUT          | X(364)       | 7 rows x 52 bytes of screen data from last read       |
| WS-CA-ROW-TR-CODE-OUT(i)    | X(02) x7     | Type code for row i                                   |
| WS-CA-ROW-TR-DESC-OUT(i)    | X(50) x7     | Description for row i                                 |
| WS-CA-ROW-SELECTED          | S9(4) COMP   | Row index of last selected row                        |
| WS-CA-LAST-TR-CODE          | X(02)        | Last type code on current page (forward cursor start) |
| WS-CA-FIRST-TR-CODE         | X(02)        | First type code on current page (backward cursor start)|
| WS-CA-SCREEN-NUM            | 9(1)         | Current page number (88: CA-FIRST-PAGE = 1)           |
| WS-CA-LAST-PAGE-DISPLAYED   | 9(1)         | 88: CA-LAST-PAGE-SHOWN=0, CA-LAST-PAGE-NOT-SHOWN=9    |
| WS-CA-NEXT-PAGE-IND         | X(1)         | 88: CA-NEXT-PAGE-NOT-EXISTS=LOW-V, CA-NEXT-PAGE-EXISTS='Y'|
| WS-CA-DELETE-FLAG           | X(1)         | 88: CA-DELETE-NOT-REQUESTED=LOW-V, CA-DELETE-REQUESTED='Y', CA-DELETE-SUCCEEDED=LOW-V |
| WS-CA-UPDATE-FLAG           | X(1)         | 88: CA-UPDATE-NOT-REQUESTED=LOW-V, CA-UPDATE-REQUESTED='Y', CA-UPDATE-SUCCEEDED=LOW-V |

---

## DB2 Cursor Declarations

### Forward Cursor (lines 338-352)

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

- Used by: 8000-READ-FORWARD
- Paging key: WS-START-KEY is the TR_TYPE of the first row of the NEXT page
- Filter flags: WS-EDIT-TYPE-FLAG = '1' activates type code exact match; '1' for description activates LIKE with % wildcards

### Backward Cursor (lines 354-368)

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

- Used by: 8100-READ-BACKWARDS
- Logic: Reads up to 7 rows with TR_TYPE < WS-CA-FIRST-TR-CODE (first key of current page), ordered descending. Rows are written into output array from position WS-MAX-SCREEN-LINES down to 1 to reverse the DESC fetch order, resulting in an ascending display.

---

## CICS/DB2 Commands

### CICS Commands

| Command               | Paragraph           | Parameters                                          | Purpose                           |
|-----------------------|---------------------|-----------------------------------------------------|-----------------------------------|
| EXEC CICS RECEIVE MAP | 1100-RECEIVE-SCREEN | MAP(CTRTLIA) MAPSET(COTRTLI) INTO(CTRTLIAI)         | Receive screen input              |
| EXEC CICS SEND MAP    | 2600-SEND-SCREEN    | MAP(CTRTLIA) MAPSET(COTRTLI) FROM(CTRTLIAO) CURSOR ERASE FREEKB | Send screen output   |
| EXEC CICS SYNCPOINT   | 9200-UPDATE-RECORD  | (no parms)                                          | Commit DB2 UPDATE                 |
| EXEC CICS SYNCPOINT   | 9300-DELETE-RECORD  | (no parms)                                          | Commit DB2 DELETE                 |
| EXEC CICS XCTL        | 0000-MAIN (PFK03)   | PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA) | Exit to calling program         |
| EXEC CICS XCTL        | 0000-MAIN (PFK02)   | PROGRAM(LIT-ADDTPGM) COMMAREA(CARDDEMO-COMMAREA)   | Transfer to COTRTUPC (add screen) |
| EXEC CICS RETURN      | COMMON-RETURN       | TRANSID(CTLI) COMMAREA(WS-COMMAREA) LENGTH(2000)    | Pseudo-conversational return      |
| EXEC CICS SEND TEXT   | SEND-LONG-TEXT      | FROM(WS-LONG-MSG) ERASE FREEKB                      | Debug/error text display          |

### DB2 SQL Operations

| SQL                     | Paragraph             | Host Variables                                    | Purpose                               |
|-------------------------|-----------------------|---------------------------------------------------|---------------------------------------|
| SELECT COUNT(1)          | 9100-CHECK-FILTERS    | :WS-EDIT-TYPE-FLAG,:WS-TYPE-CD-FILTER,:WS-EDIT-DESC-FLAG,:WS-TYPE-DESC-FILTER | Count matching rows for filter validation |
| OPEN C-TR-TYPE-FORWARD   | 9400-OPEN-FORWARD-CURSOR | (inherits declared cursor variables)            | Start forward page read               |
| FETCH C-TR-TYPE-FORWARD  | 8000-READ-FORWARD     | INTO :DCL-TR-TYPE, :DCL-TR-DESCRIPTION           | Fetch each forward row                |
| CLOSE C-TR-TYPE-FORWARD  | 9450-CLOSE-FORWARD-CURSOR | (none)                                         | End forward read                      |
| OPEN C-TR-TYPE-BACKWARD  | 9500-OPEN-BACKWARD-CURSOR | (inherits declared cursor variables)           | Start backward page read              |
| FETCH C-TR-TYPE-BACKWARD | 8100-READ-BACKWARDS   | INTO :DCL-TR-TYPE, :DCL-TR-DESCRIPTION           | Fetch each backward row               |
| CLOSE C-TR-TYPE-BACKWARD | 9550-CLOSE-BACK-CURSOR | (none)                                          | End backward read                     |
| UPDATE TRANSACTION_TYPE  | 9200-UPDATE-RECORD    | :DCL-TR-DESCRIPTION WHERE :DCL-TR-TYPE           | Update selected row description        |
| DELETE TRANSACTION_TYPE  | 9300-DELETE-RECORD    | WHERE :DCL-TR-TYPE                               | Delete selected row                    |
| SELECT 1 FROM SYSDUMMY1  | 9998-PRIMING-QUERY    | INTO :WS-DUMMY-DB2-INT                           | Verify DB2 connectivity on entry       |

---

## Screen Interaction

### Map Receive (1100-RECEIVE-SCREEN, lines 930-953)

Input fields received from CTRTLIAI (map CTRTLIA of mapset COTRTLI):
- `TRTYPEI OF CTRTLIAI` → `WS-IN-TYPE-CD` (type code filter)
- `TRDESCI OF CTRTLIAI` → `WS-IN-TYPE-DESC` (description filter)
- For each row i (1-7):
  - `TRTSELI(i)` → `WS-EDIT-SELECT(i)` (action code D/U/blank)
  - `TRTTYPI(i)` → `WS-ROW-TR-CODE-IN(i)` (type code, protected, carried back)
  - `TRTYPDI(i)` → `WS-ROW-TR-DESC-IN(i)` (description, editable)

**Note:** The array redefine (lines 434-456 in COTRTLIC) maps `CTRTLIAI` fields differently from the generated BMS copybook. The program uses a REDEFINES overlay of CTRTLIAI starting at offset 238, creating `EACH-ROWI OCCURS 7 TIMES` with fields TRTSELL/TRTSELF/TRTSELI/TRTTYPL/TRTTYPF/TRTTYPI/TRTYPDL/TRTYPDF/TRTYPDI per row.

### Map Send (2600-SEND-SCREEN, lines 1587-1596)

Output fields written to CTRTLIAO:
- Header: TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO
- Paging: PAGENOO
- Filter fields: TRTYPEO, TRDESCO (with attribute control)
- Per row (via EACH-ROWO OCCURS 7, lines 457-478): TRTSELC/TRTSELP/TRTSELH/TRTSELV/TRTSELO / TRTTYPC/TRTTYPP/TRTTYPH/TRTTYPH/TRTTYPO / TRTYPDC/TRTYPDP/TRTYPDH/TRTYPDV/TRTYPDO
- Messages: INFOMSGO, ERRMSGO

### Screen State Management

The program drives field attributes programmatically:
- Select column (TRTSELA) is protected when FLG-PROTECT-SELECT-ROWS-YES or row data is LOW-VALUES
- When D-selected: type code and description turn DFHNEUTR (neutral), cursor to select column
- When U-selected and FLG-UPDATE-COMPLETED: turn DFHNEUTR, cursor to select
- When U-selected and NOT completed: DFHBMFSE on description (unprotect), cursor to description
- Invalid select codes get DFHRED on select field, cursor positioned there

---

## Called Programs

| Program     | Method     | Trigger              | Purpose                                          |
|-------------|------------|----------------------|--------------------------------------------------|
| COADM01C    | CICS XCTL  | PF3 (exit)           | Admin menu (return if called from there)         |
| COTRTUPC    | CICS XCTL  | PF2                  | Transfer to Transaction Type add/edit screen     |
| DSNTIAC     | CICS CALL  | 9999-FORMAT-DB2-MESSAGE | Format DB2 SQL error text (via CSDB2RPY)      |

**[UNRESOLVED]** COADM01C and COTRTUPC are referenced by literal name. Their source is not present in this extension directory; they belong to the base CardDemo application.

---

## Error Handling

### PFK Validation (lines 574-587)
Valid keys: ENTER, PFK02, PFK03, PFK07, PFK08, PFK10 (conditional). Any other key is treated as ENTER (SET CCARD-AID-ENTER).

### DB2 Connectivity (lines 684-691)
Before any data access, 9998-PRIMING-QUERY (from CSDB2RPY.cpy) executes `SELECT 1 FROM SYSIBM.SYSDUMMY1`. If WS-DB2-ERROR is set, SEND-LONG-TEXT displays WS-LONG-MSG and program returns without further DB2 access.

### Filter Validation
- Non-numeric type code filter → INPUT-ERROR + FLG-TYPEFILTER-NOT-OK + FLG-PROTECT-SELECT-ROWS-YES (lines 1111-1118)
- No rows found for filters → INPUT-ERROR + FLG-TYPEFILTER-NOT-OK/FLG-DESCFILTER-NOT-OK + message (lines 1251-1267)

### Selection Validation
- More than 1 action selected → INPUT-ERROR + WS-MESG-MORE-THAN-1-ACTION (lines 1049-1052)
- Invalid action code (not D/U/blank) → INPUT-ERROR + error per row (lines 1034-1038)

### DB2 UPDATE SQLCODE Handling (9200-UPDATE-RECORD)
| SQLCODE      | Action                                                              |
|--------------|---------------------------------------------------------------------|
| 0            | SYNCPOINT; SET CA-UPDATE-SUCCEEDED; set success message             |
| +100         | SET CA-UPDATE-REQUESTED (re-show as still pending); format DB2 msg  |
| -911         | Deadlock; SET CA-UPDATE-REQUESTED + INPUT-ERROR; format DB2 msg     |
| < 0          | SET CA-UPDATE-REQUESTED + format DB2 msg                            |

### DB2 DELETE SQLCODE Handling (9300-DELETE-RECORD)
| SQLCODE      | Action                                                              |
|--------------|---------------------------------------------------------------------|
| 0            | SYNCPOINT; SET CA-DELETE-SUCCEEDED; set success message             |
| -532         | FK violation; format "delete child records first" message           |
| OTHER        | Format general failure message                                      |

### Cursor Open/Close Error Handling
All cursor OPEN/CLOSE paragraphs check SQLCODE WHEN OTHER and set WS-DB2-ERROR, then call 9999-FORMAT-DB2-MESSAGE. The error is reflected in WS-RETURN-MSG and displayed on screen via ERRMSGO.

---

## Business Rules

1. **7-row page size:** Only 7 transaction type records are displayed per page (WS-MAX-SCREEN-LINES = 7, line 60).

2. **Only one action per submit:** The user may mark only one row with D or U per screen submission. Marking multiple rows results in WS-MESG-MORE-THAN-1-ACTION and INPUT-ERROR.

3. **Description is the only editable field:** TR_TYPE (type code) is always protected on the list screen. Only TR_DESCRIPTION can be changed by marking 'U'.

4. **Delete confirmation via PF10:** Pressing ENTER with 'D' highlights the row and sets CA-DELETE-REQUESTED. The user must then press PF10 to confirm. If filter conditions change between ENTER and PF10, the action is treated as a fresh ENTER.

5. **Update confirmation via PF10:** Pressing ENTER with 'U' and a changed description highlights the row. The user must press PF10 to save. If no change is detected (description matches stored value), WS-MESG-NO-CHANGES-DETECTED is shown and the update is not applied.

6. **FK constraint on delete:** Deleting a TRANSACTION_TYPE record that has associated TRANSACTION_TYPE_CATEGORY rows (FK: TRC_TYPE_CODE REFERENCES TR_TYPE ON DELETE RESTRICT) results in SQLCODE -532. The message "Please delete associated child records first" is shown.

7. **Forward paging:** PF8 advances to the next page. The cursor uses WS-CA-LAST-TR-CODE as the start key (>= logic in cursor). If no next page exists and PF8 is pressed again after the last page is shown, "No more pages to display" is shown.

8. **Backward paging:** PF7 retreats to the previous page. The cursor uses WS-CA-FIRST-TR-CODE as the upper bound (< logic, DESC order). Cannot go before page 1; pressing PF7 on page 1 re-reads the same page.

9. **Filter resets paging:** Changing either the type code filter or description filter field causes WS-CA-PAGING-VARIABLES to be re-initialized (paging reset to beginning).

10. **Description filter uses LIKE with wildcards:** The user's input is wrapped with '%' on both sides (lines 1156-1162): `'%' + TRIM(input) + '%'`. This provides contains-style substring matching.

11. **SYNCPOINT on DML success:** Both UPDATE and DELETE issue EXEC CICS SYNCPOINT immediately after a successful SQLCODE=0, committing the transaction before returning to the pseudo-conversational loop.

---

## Input/Output Specification

### Inputs

| Source              | Field                    | Description                              |
|---------------------|--------------------------|------------------------------------------|
| CTRTLIAI.TRTYPEI    | Type code filter         | Optional 2-digit numeric filter           |
| CTRTLIAI.TRDESCI    | Description filter       | Optional substring filter (LIKE)          |
| CTRTLIAI.TRTSELI(i) | Selection code for row i | D=Delete, U=Update, blank=no action       |
| CTRTLIAI.TRTYPDI(i) | Description input row i  | Editable description (for U action)       |
| DFHCOMMAREA         | Program commarea         | Page state, filter state, row data        |
| EIBAID              | PF key                   | ENTER/PF02/PF03/PF07/PF08/PF10           |

### Outputs

| Target              | Field                    | Description                              |
|---------------------|--------------------------|------------------------------------------|
| CTRTLIAO.TRTYPEO    | Type code filter display | Echo of current filter value              |
| CTRTLIAO.TRDESCO    | Description filter display| Echo of current filter value             |
| CTRTLIAO.TRTTYPO(i) | Type code for row i      | Always protected; from commarea           |
| CTRTLIAO.TRTYPDO(i) | Description for row i    | Editable when U-selected                  |
| CTRTLIAO.TRTSELO(i) | Select field for row i   | Echoed back / cleared on post-action      |
| CTRTLIAO.INFOMSGO   | Information message      | Centered instruction/status text          |
| CTRTLIAO.ERRMSGO    | Error message            | Red, bright error text                    |
| CTRTLIAO.PAGENOO    | Page number              | Current page number                       |
| CARDDEMO-COMMAREA   | Return commarea          | Updated page state, filter state          |

---

## Copybook Dependencies

| Copybook     | Include Method                           | Content                                                      |
|--------------|------------------------------------------|--------------------------------------------------------------|
| SQLCA        | EXEC SQL INCLUDE SQLCA (line 331)        | DB2 SQL Communication Area                                   |
| DCLTRTYP     | EXEC SQL INCLUDE DCLTRTYP (line 333)     | DCLGEN for CARDDEMO.TRANSACTION_TYPE                         |
| CSDB2RWY     | EXEC SQL INCLUDE CSDB2RWY (line 304)     | DB2 common working storage (WS-DB2-COMMON-VARS, DSNTIAC vars)|
| CVCRD01Y     | COPY CVCRD01Y (line 327)                 | Common card/account working storage                          |
| COCOM01Y     | COPY COCOM01Y (line 375)                 | CARDDEMO application commarea layout                         |
| DFHBMSCA     | COPY DFHBMSCA (line 425)                 | IBM BMS attribute byte constants (DFHBMPRF, DFHRED, etc.)    |
| DFHAID       | COPY DFHAID (line 426)                   | IBM CICS AID (PF key) constants                              |
| COTTL01Y     | COPY COTTL01Y (line 430)                 | Screen title lines (CCDA-TITLE01, CCDA-TITLE02)              |
| COTRTLI      | COPY COTRTLI (line 433)                  | BMS-generated copybook: CTRTLIAI / CTRTLIAO structures       |
| CSDAT01Y     | COPY CSDAT01Y (line 480)                 | Current date/time working variables                          |
| CSMSG01Y     | COPY CSMSG01Y (line 482)                 | Common messages                                              |
| CSUSR01Y     | COPY CSUSR01Y (line 485)                 | Signed-on user data                                          |
| CVACT02Y     | COPY CVACT02Y (line 490)                 | Card/account record layout                                   |
| CSDB2RPY     | EXEC SQL INCLUDE CSDB2RPY (line 2055)    | DB2 priming query + DSNTIAC message format routines          |
| CSSTRPFY     | COPY CSSTRPFY (line 2060)                | PF key store/map routine (YYYY-STORE-PFKEY)                  |

**[UNRESOLVED]** The following copybooks are referenced but not present in this extension directory. They belong to the base CardDemo application:
- CVCRD01Y
- COCOM01Y
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CSUSR01Y
- CVACT02Y
- CSSTRPFY
- DFHBMSCA (IBM-supplied)
- DFHAID (IBM-supplied)
