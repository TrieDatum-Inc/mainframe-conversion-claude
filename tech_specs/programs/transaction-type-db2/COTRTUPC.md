# Technical Specification: COTRTUPC

## Program Overview

| Attribute         | Value                                                                         |
|-------------------|-------------------------------------------------------------------------------|
| Program ID        | COTRTUPC                                                                      |
| Source File       | app/app-transaction-type-db2/cbl/COTRTUPC.cbl                                 |
| Language          | COBOL with embedded static DB2 SQL                                            |
| Environment       | CICS online                                                                   |
| Transaction ID    | CTTU                                                                          |
| BMS Mapset        | COTRTUP                                                                       |
| BMS Map           | CTRTUPA                                                                       |
| Function          | Add and update individual transaction type records                            |
| Layer             | Business logic — CICS online add/edit with DB2 static SQL                    |
| Date Written      | Dec 2022                                                                      |

### Purpose

COTRTUPC is the online CICS program for Transaction Type add and update operations. It displays a single-record detail form allowing a user to enter a 2-digit transaction type code and a 50-character description. The program searches DB2 for an existing record; if found it supports update or delete; if not found it offers to create a new record. It is menu option 6 from the Admin Menu (CA00) and can also be reached via PF2 from the list screen (COTRTLIC/CTLI).

---

## Program Flow

### Entry Point and Commarea Handling

The PROCEDURE DIVISION entry is paragraph `0000-MAIN` (line 344).

**On initial entry or fresh entry (EIBCALEN=0, or from Admin/List without CDEMO-PGM-REENTER):**
```
INITIALIZE CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA
SET CDEMO-PGM-ENTER TO TRUE
SET TTUP-DETAILS-NOT-FETCHED TO TRUE
```

**On re-entry (EIBCALEN > 0, from same program):**
```
MOVE DFHCOMMAREA(1:LENGTH OF CARDDEMO-COMMAREA) TO CARDDEMO-COMMAREA
MOVE DFHCOMMAREA(offset:LENGTH OF WS-THIS-PROGCOMMAREA) TO WS-THIS-PROGCOMMAREA
```

**State reset conditions (lines 405-419):** The following conditions reset the program to initial entry state (CDEMO-PGM-ENTER + TTUP-DETAILS-NOT-FETCHED):
- PF12 pressed when TTUP-SHOW-DETAILS or TTUP-CREATE-NEW-RECORD or TTUP-DETAILS-NOT-FOUND
- TTUP-CHANGES-OKAYED-AND-DONE (update just completed)
- TTUP-CHANGES-FAILED (update failed)
- TTUP-CHANGES-BACKED-OUT with no old data
- TTUP-DELETE-DONE or TTUP-DELETE-FAILED

### Main Control Flow (0000-MAIN EVALUATE, lines 423-556)

```
EVALUATE TRUE
  WHEN PFK03
    --> Set return target (calling program or CA00)
    --> SYNCPOINT + CICS XCTL to CDEMO-TO-PROGRAM

  WHEN NOT CDEMO-PGM-REENTER AND FROM-PROGRAM = COADM01C
  WHEN NOT CDEMO-PGM-REENTER AND FROM-PROGRAM = COTRTLIC
  WHEN CDEMO-PGM-ENTER AND TTUP-DETAILS-NOT-FETCHED
    --> INITIALIZE WS-THIS-PROGCOMMAREA, WS-MISC-STORAGE
    --> PERFORM 3000-SEND-MAP
    --> SET CDEMO-PGM-REENTER
    --> SET TTUP-DETAILS-NOT-FETCHED
    --> GO TO COMMON-RETURN

  WHEN PFK04 AND TTUP-CONFIRM-DELETE
    --> SET TTUP-START-DELETE
    --> PERFORM 9800-DELETE-PROCESSING
    --> PERFORM 3000-SEND-MAP
    --> GO TO COMMON-RETURN

  WHEN PFK04 AND TTUP-SHOW-DETAILS
    --> SET TTUP-CONFIRM-DELETE
    --> PERFORM 3000-SEND-MAP
    --> GO TO COMMON-RETURN

  WHEN PFK05 AND TTUP-DETAILS-NOT-FOUND
    --> SET TTUP-CREATE-NEW-RECORD
    --> PERFORM 3000-SEND-MAP
    --> GO TO COMMON-RETURN

  WHEN PFK05 AND TTUP-CHANGES-OK-NOT-CONFIRMED
    --> PERFORM 9600-WRITE-PROCESSING (UPDATE or INSERT)
    --> PERFORM 3000-SEND-MAP
    --> GO TO COMMON-RETURN

  WHEN PFK12 AND (TTUP-CHANGES-OK-NOT-CONFIRMED
                  OR TTUP-CONFIRM-DELETE
                  OR TTUP-SHOW-DETAILS)
    --> SET FOUND-TRANTYPE-IN-TABLE
    --> PERFORM 2000-DECIDE-ACTION
    --> PERFORM 3000-SEND-MAP
    --> GO TO COMMON-RETURN

  WHEN WS-INVALID-KEY-PRESSED
    --> PERFORM 3000-SEND-MAP
    --> GO TO COMMON-RETURN

  WHEN OTHER
    --> PERFORM 1000-PROCESS-INPUTS
    --> PERFORM 2000-DECIDE-ACTION
    --> PERFORM 3000-SEND-MAP
    --> GO TO COMMON-RETURN
END-EVALUATE
```

### Program State Machine

COTRTUPC uses a state machine encoded in `TTUP-CHANGE-ACTION` (part of `WS-THIS-PROGCOMMAREA`). States drive both processing decisions and screen attribute/message display.

| State Code | 88-Level Name                  | Meaning                                                |
|------------|--------------------------------|--------------------------------------------------------|
| LOW-V/SPC  | TTUP-DETAILS-NOT-FETCHED       | Initial / no key entered yet                           |
| 'K'        | TTUP-INVALID-SEARCH-KEYS       | Key entered but failed validation                      |
| 'X'        | TTUP-DETAILS-NOT-FOUND         | Key valid but not found in DB2                         |
| 'S'        | TTUP-SHOW-DETAILS              | Record found and displayed                             |
| 'R'        | TTUP-CREATE-NEW-RECORD         | User confirmed they want to create new                 |
| 'V'        | TTUP-REVIEW-NEW-RECORD         | (defined but not observed in active path)              |
| '9'        | TTUP-CONFIRM-DELETE            | User pressed F4; awaiting confirmation                 |
| '8'        | TTUP-START-DELETE              | Confirmation given; delete in progress                 |
| '7'        | TTUP-DELETE-DONE               | Delete succeeded                                       |
| '6'        | TTUP-DELETE-FAILED             | Delete failed                                          |
| 'E'        | TTUP-CHANGES-NOT-OK            | Edit errors found in input                             |
| 'N'        | TTUP-CHANGES-OK-NOT-CONFIRMED  | Edits passed; awaiting F5 to save                      |
| 'L'        | TTUP-CHANGES-OKAYED-LOCK-ERROR | F5 pressed but lock failed (SQLCODE -911)              |
| 'F'        | TTUP-CHANGES-OKAYED-BUT-FAILED | F5 pressed but DB2 error                               |
| 'C'        | TTUP-CHANGES-OKAYED-AND-DONE   | Update/insert succeeded                                |
| 'B'        | TTUP-CHANGES-BACKED-OUT        | User cancelled after changes confirmed                 |

### Paragraph Index

| Paragraph                       | Lines       | Description                                              |
|---------------------------------|-------------|----------------------------------------------------------|
| 0000-MAIN                       | 344-573     | Entry, commarea handling, PFK dispatch                   |
| COMMON-RETURN                   | 559-571     | Package commarea; CICS RETURN TRANSID(CTTU)              |
| 0001-CHECK-PFKEYS                | 577-618     | Validates PFK against current state                      |
| 1000-PROCESS-INPUTS             | 625-636     | Calls receive, store, edit sub-paragraphs                |
| 1100-RECEIVE-MAP                | 641-648     | CICS RECEIVE MAP into CTRTUPAI                           |
| 1150-STORE-MAP-IN-NEW           | 652-685     | Copies screen fields to TTUP-NEW-TTYP-TYPE and -DESC     |
| 1200-EDIT-MAP-INPUTS            | 689-780     | Validates search key + description; sets confirm state   |
| 1205-COMPARE-OLD-NEW            | 783-811     | Compares new values to old (case-insensitive UPPER-CASE) |
| 1210-EDIT-TRANTYPE              | 820-843     | Edits TR-TYPE code: required, numeric, non-zero          |
| 1230-EDIT-ALPHANUM-REQD         | 849-901     | Generic required alphanumeric field validator            |
| 1245-EDIT-NUM-REQD              | 907-973     | Generic required numeric field validator                 |
| 2000-DECIDE-ACTION              | 978-1081    | State machine: decides next TTUP state                   |
| 3000-SEND-MAP                   | 1089-1103   | Orchestrates all screen init and send sub-paragraphs     |
| 3100-SCREEN-INIT                | 1110-1134   | Clears output; loads date/time/header                    |
| 3200-SETUP-SCREEN-VARS          | 1140-1170   | Routes to 3201/3202/3203 based on state                  |
| 3201-SHOW-INITIAL-VALUES        | 1176-1179   | Clears TRTYPCD and TRTYDSC output                        |
| 3202-SHOW-ORIGINAL-VALUES       | 1185-1191   | Puts TTUP-OLD data into output fields                    |
| 3203-SHOW-UPDATED-VALUES        | 1197-1200   | Puts TTUP-NEW data into output fields                    |
| 3250-SETUP-INFOMSG              | 1210-1265   | Sets WS-INFO-MSG + centers it + moves to INFOMSGO        |
| 3300-SETUP-SCREEN-ATTRS         | 1269-1363   | Protect/unprotect fields; set field colors; cursor pos   |
| 3310-PROTECT-ALL-ATTRS          | 1368-1372   | DFHBMPRF to TRTYPCDA, TRTYDSCA, INFOMSGA                 |
| 3320-UNPROTECT-FEW-ATTRS        | 1377-1381   | DFHBMFSE to TRTYDSCA; DFHBMPRF to INFOMSGA               |
| 3390-SETUP-INFOMSG-ATTRS        | 1386-1391   | DFHBMDAR (no msg) or DFHBMASB (has msg) to INFOMSGA      |
| 3391-SETUP-PFKEY-ATTRS          | 1397-1423   | Show/hide FKEYS/FKEY04/FKEY05/FKEY12 on PF key bar       |
| 3400-SEND-SCREEN                | 1428-1441   | CICS SEND MAP CTRTUPA ERASE FREEKB CURSOR                |
| 9000-READ-TRANTYPE              | 1447-1463   | Calls 9100 to read from DB2; then 9500 to store          |
| 9100-GET-TRANSACTION-TYPE       | 1469-1511   | SELECT TR_TYPE, TR_DESCRIPTION WHERE TR_TYPE = :key      |
| 9500-STORE-FETCHED-DATA         | 1517-1527   | Moves DCL-TR-TYPE, DCL-TR-DESCRIPTION to TTUP-OLD-DETAILS|
| 9600-WRITE-PROCESSING           | 1531-1591   | UPDATE then INSERT if +100; SYNCPOINT on success          |
| 9700-INSERT-RECORD              | 1596-1619   | INSERT if UPDATE returned +100; SYNCPOINT on success      |
| 9800-DELETE-PROCESSING          | 1624-1663   | DELETE WHERE TR_TYPE; SYNCPOINT; handles -532             |
| ABEND-ROUTINE                   | 1675-1698   | CICS SEND + CICS ABEND with ABEND-CODE                   |
| YYYY-STORE-PFKEY                | (CSSTRPFY)  | Map PF key from EIBAID                                   |

---

## Data Structures

### Program Commarea (WS-THIS-PROGCOMMAREA)

This structure is appended to CARDDEMO-COMMAREA in WS-COMMAREA (PIC X(2000)).

| Field                      | Type   | States/Values                                                     |
|----------------------------|--------|-------------------------------------------------------------------|
| TTUP-CHANGE-ACTION         | X(1)   | State code (see state machine table above)                        |
| TTUP-OLD-TTYP-TYPE         | X(02)  | TR_TYPE as fetched from DB2 (original value)                      |
| TTUP-OLD-TTYP-TYPE-DESC    | X(50)  | TR_DESCRIPTION as fetched from DB2 (original value)               |
| TTUP-NEW-TTYP-TYPE         | X(02)  | TR_TYPE as entered by user on screen                              |
| TTUP-NEW-TTYP-TYPE-DESC    | X(50)  | TR_DESCRIPTION as entered by user on screen                       |

### Working Storage — Flags

| Field                    | 88-Level(s)                                       | Purpose                                    |
|--------------------------|---------------------------------------------------|--------------------------------------------|
| WS-INPUT-FLAG            | INPUT-OK ('0'), INPUT-ERROR ('1'), INPUT-PENDING  | Overall input validation state             |
| WS-RETURN-FLAG           | WS-RETURN-FLAG-OFF/ON                             | Return flow control                        |
| WS-PFK-FLAG              | PFK-VALID ('0'), PFK-INVALID ('1')                | PF key validation result                   |
| WS-EDIT-TTYP-FLAG        | FLG-TRANFILTER-ISVALID, -NOT-OK, -BLANK           | Type code field validation                 |
| WS-EDIT-DESC-FLAGS       | FLG-DESCRIPTION-ISVALID, -NOT-OK, -BLANK          | Description field validation               |
| WS-DATACHANGED-FLAG      | NO-CHANGES-FOUND ('0'), CHANGE-HAS-OCCURRED ('1') | Whether screen differs from DB2 data       |
| WS-TRANTYPE-MASTER-READ-FLAG | FOUND-TRANTYPE-IN-TABLE ('1')                 | DB2 SELECT result indicator                |

### Working Storage — Edit Variables

| Field                    | Type       | Description                                          |
|--------------------------|------------|------------------------------------------------------|
| WS-DISP-SQLCODE          | PIC ----9  | Formatted SQLCODE for screen/message display         |
| WS-STRING-MID            | PIC 9(3)   | Center-justify calculation: offset position          |
| WS-STRING-LEN            | PIC 9(3)   | Center-justify calculation: text length              |
| WS-STRING-OUT            | PIC X(40)  | Centered info message buffer                         |
| WS-EDIT-ALPHANUM-ONLY    | X(256)     | Generic field value for validation routines          |
| WS-EDIT-ALPHANUM-LENGTH  | S9(4) COMP-3 | Length of field to validate                        |
| WS-EDIT-VARIABLE-NAME    | X(25)      | Field name for error messages                        |
| WS-EDIT-NUMERIC-2        | 9(02)      | Numeric conversion result                            |
| WS-EDIT-ALPHANUMERIC-2   | X(02)      | Alpha version for zero-fill                          |

### Working Storage — Info/Error Messages

| 88-Level                       | Value (literal)                                          |
|--------------------------------|----------------------------------------------------------|
| FOUND-TRANTYPE-DATA            | 'Selected transaction type shown above'                  |
| PROMPT-FOR-SEARCH-KEYS         | 'Enter transaction type to be maintained'                |
| PROMPT-CREATE-NEW-RECORD       | 'Press F05 to add. F12 to cancel'                        |
| PROMPT-DELETE-CONFIRM          | 'Delete this record ? Press F4 to confirm'               |
| CONFIRM-DELETE-SUCCESS         | 'Delete successful.'                                     |
| PROMPT-FOR-CHANGES             | 'Update transaction type details shown.'                 |
| PROMPT-FOR-NEWDATA             | 'Enter new transaction type details.'                    |
| PROMPT-FOR-CONFIRMATION        | 'Changes validated.Press F5 to save'                     |
| CONFIRM-UPDATE-SUCCESS         | 'Changes committed to database'                          |
| INFORM-FAILURE                 | 'Changes unsuccessful'                                   |
| WS-EXIT-MESSAGE                | 'PF03 pressed.Exiting              '                     |
| WS-INVALID-KEY                 | 'Invalid Key pressed. '                                  |
| WS-RECORD-NOT-FOUND            | 'No record found for this key in database'               |
| NO-SEARCH-CRITERIA-RECEIVED    | 'No input received'                                      |
| NO-CHANGES-DETECTED            | 'No change detected with respect to values fetched.'     |
| COULD-NOT-LOCK-REC-FOR-UPDATE  | 'Could not lock record for update'                       |
| DATA-WAS-CHANGED-BEFORE-UPDATE | 'Record changed by some one else. Please review'         |
| WS-UPDATE-WAS-CANCELLED        | 'Update was cancelled'                                   |
| TABLE-UPDATE-FAILED            | 'Update of record failed'                                |
| RECORD-DELETE-FAILED           | 'Delete of record failed'                                |
| WS-DELETE-WAS-CANCELLED        | 'Delete was cancelled'                                   |
| WS-INVALID-KEY-PRESSED         | 'Invalid key pressed'                                    |

---

## CICS/DB2 Commands

### CICS Commands

| Command              | Paragraph             | Parameters                                              | Purpose                                    |
|----------------------|-----------------------|---------------------------------------------------------|--------------------------------------------|
| HANDLE ABEND         | 0000-MAIN (line 348)  | LABEL(ABEND-ROUTINE)                                    | Catch unexpected abends                    |
| RECEIVE MAP          | 1100-RECEIVE-MAP      | MAP(CTRTUPA) MAPSET(COTRTUP) INTO(CTRTUPAI) RESP/RESP2  | Receive screen input                       |
| SEND MAP             | 3400-SEND-SCREEN      | MAP(CTRTUPA) MAPSET(COTRTUP) FROM(CTRTUPAO) CURSOR ERASE FREEKB RESP | Send screen output  |
| SYNCPOINT            | 9600-WRITE-PROCESSING (line 1557) | (no parms)                                | Commit UPDATE                              |
| SYNCPOINT            | 9700-INSERT-RECORD (line 1606)    | (no parms)                                | Commit INSERT                              |
| SYNCPOINT            | 9800-DELETE-PROCESSING (line 1637)| (no parms)                                | Commit DELETE                              |
| SYNCPOINT            | PFK03 exit (line 453) | (no parms)                                              | Commit before XCTL                         |
| XCTL                 | PFK03 exit (line 457) | PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)   | Exit to calling program or Admin menu      |
| RETURN               | COMMON-RETURN         | TRANSID(CTTU) COMMAREA(WS-COMMAREA) LENGTH(WS-COMMAREA) | Pseudo-conversational return              |
| SEND                 | ABEND-ROUTINE         | FROM(ABEND-DATA) NOHANDLE ERASE                         | Display abend information                  |
| ABEND                | ABEND-ROUTINE         | ABCODE(ABEND-CODE)                                      | Force CICS abend with code '9999'          |
| HANDLE ABEND CANCEL  | ABEND-ROUTINE         | CANCEL                                                  | Cancel abend handler before CICS ABEND    |

### DB2 SQL Operations

| SQL                         | Paragraph                | Host Variables                                      | Purpose                             |
|-----------------------------|--------------------------|-----------------------------------------------------|-------------------------------------|
| SELECT TR_TYPE,TR_DESCRIPTION INTO ... | 9100-GET-TRANSACTION-TYPE | :DCL-TR-TYPE (WHERE), :DCL-TR-TYPE, :DCL-TR-DESCRIPTION (INTO) | Fetch single record by key   |
| UPDATE TRANSACTION_TYPE SET TR_DESCRIPTION | 9600-WRITE-PROCESSING | :DCL-TR-DESCRIPTION (SET), :DCL-TR-TYPE (WHERE)    | Update description            |
| INSERT INTO TRANSACTION_TYPE | 9700-INSERT-RECORD      | :DCL-TR-TYPE, :DCL-TR-DESCRIPTION                   | Insert new record (upsert fallback) |
| DELETE FROM TRANSACTION_TYPE | 9800-DELETE-PROCESSING  | :DCL-TR-TYPE (WHERE)                                | Delete record by key           |
| SELECT 1 FROM SYSIBM.SYSDUMMY1 | (via CSDB2RPY)        | :WS-DUMMY-DB2-INT                                   | Connectivity priming query     |

**Note:** COTRTUPC also includes `EXEC SQL INCLUDE DCLTRCAT END-EXEC` (line 288), making DCLTRANSACTION-TYPE-CATEGORY available as a host variable structure. However, no SQL against TRANSACTION_TYPE_CATEGORY is issued in the program's procedure division. This include is present for completeness or potential future use.

---

## Input Validation Details

### 1210-EDIT-TRANTYPE (lines 820-843)
1. Calls 1245-EDIT-NUM-REQD: field must be supplied, must be numeric (FUNCTION TEST-NUMVAL), must not be zero
2. If valid: COMPUTE WS-EDIT-NUMERIC-2 = FUNCTION NUMVAL(value); zero-fills to 2 digits; stores back to TTUP-NEW-TTYP-TYPE

**Business implication:** The type code is strictly a 2-digit numeric value between 01 and 99. Zero is explicitly rejected.

### 1230-EDIT-ALPHANUM-REQD (lines 849-901)
Generic validator for description field:
1. Required: must not be LOW-VALUES, SPACES, or zero-length after TRIM
2. Alphanumeric: converts all alphanumerics to spaces using INSPECT CONVERTING, checks if residual = zero length. If residual is non-zero, the field contains characters outside A-Z/a-z/0-9.

### 1245-EDIT-NUM-REQD (lines 907-973)
Generic validator for numeric fields:
1. Required: not LOW-VALUES, not SPACES, not zero TRIM length
2. Numeric: FUNCTION TEST-NUMVAL = 0
3. Non-zero: FUNCTION NUMVAL <> 0

### 1205-COMPARE-OLD-NEW (lines 783-811)
Compares new values against old (fetched) values using FUNCTION UPPER-CASE and FUNCTION TRIM on both. Sets NO-CHANGES-DETECTED if identical (same content, same trimmed length). This prevents spurious updates when the user presses Enter without changing anything.

---

## Screen Interaction

### Map Receive (1100-RECEIVE-MAP, lines 641-648)
EXEC CICS RECEIVE MAP('CTRTUPA') MAPSET('COTRTUP') INTO(CTRTUPAI).

Fields read:
- `TRTYPCDI OF CTRTUPAI` → `TTUP-NEW-TTYP-TYPE` (transaction type code)
- `TRTYDSCI OF CTRTUPAI` → `TTUP-NEW-TTYP-TYPE-DESC` (description)

### Map Send (3400-SEND-SCREEN, lines 1428-1441)
EXEC CICS SEND MAP('CTRTUPA') MAPSET('COTRTUP') FROM(CTRTUPAO) CURSOR ERASE FREEKB.

Output field management:
- `TRTYPCDO OF CTRTUPAO` ← TTUP-OLD or TTUP-NEW type code depending on state
- `TRTYDSCO OF CTRTUPAO` ← TTUP-OLD or TTUP-NEW description depending on state
- `INFOMSGO OF CTRTUPAO` ← centered WS-INFO-MSG
- `ERRMSGO OF CTRTUPAO` ← WS-RETURN-MSG

### Field Attribute Control

**3300-SETUP-SCREEN-ATTRS (lines 1269-1363):**
All fields protected first (3310-PROTECT-ALL-ATTRS). Then unprotected based on state:

| State                           | TRTYPCD        | TRTYDSC        | Notes                                        |
|---------------------------------|----------------|----------------|----------------------------------------------|
| TTUP-DETAILS-NOT-FETCHED        | DFHBMFSE (edit)| Protected      | User enters search key                       |
| TTUP-INVALID-SEARCH-KEYS        | DFHBMFSE (edit)| Protected      | Correct the key                              |
| TTUP-DETAILS-NOT-FOUND          | DFHBMFSE (edit)| Protected      | Key not in DB2                               |
| TTUP-SHOW-DETAILS               | Protected      | DFHBMFSE (edit)| Edit the description                         |
| TTUP-CHANGES-NOT-OK             | Protected      | DFHBMFSE (edit)| Correct the description                      |
| TTUP-CREATE-NEW-RECORD          | Protected      | DFHBMFSE (edit)| Enter new description                        |
| TTUP-CHANGES-BACKED-OUT (no old)| DFHBMFSE (edit)| Protected      | Back to search                               |
| TTUP-CHANGES-OK-NOT-CONFIRMED   | Protected      | Protected      | Awaiting F5                                  |
| TTUP-DELETE-IN-PROGRESS         | Protected      | Protected      | Awaiting F4 confirm                          |
| TTUP-CHANGES-OKAYED-AND-DONE    | Protected      | Protected      | Complete                                     |

**Cursor positioning (lines 1303-1325):**
- Cursor to TRTYPCD: TTUP-DETAILS-NOT-FETCHED, -NOT-FOUND, -INVALID-SEARCH-KEYS, filter errors, okayed/done
- Cursor to TRTYDSC: TTUP-CREATE-NEW-RECORD, NO-CHANGES-DETECTED, description errors, TTUP-CHANGES-MADE, TTUP-BACKED-OUT, TTUP-SHOW-DETAILS

**PF key bar visibility (3391-SETUP-PFKEY-ATTRS):**
- ENTER (FKEYS): hidden (DFHBMDAR) when TTUP-CONFIRM-DELETE, visible otherwise
- F4 (FKEY04): shown (DFHBMASB) when TTUP-SHOW-DETAILS or TTUP-CONFIRM-DELETE
- F5 (FKEY05): shown when TTUP-CHANGES-OK-NOT-CONFIRMED or TTUP-DETAILS-NOT-FOUND
- F12 (FKEY12): shown when TTUP-CHANGES-OK-NOT-CONFIRMED, TTUP-SHOW-DETAILS, TTUP-DETAILS-NOT-FOUND, TTUP-CONFIRM-DELETE, TTUP-CREATE-NEW-RECORD

**Color:**
- TRTYPCD: DFHRED when FLG-TRANFILTER-NOT-OK or TTUP-DELETE-FAILED
- TRTYDSC: Set by COPY CSSETATY (replacing pattern, line 1358-1361). This IBM-supplied routine sets color based on FLG-DESCRIPTION-ISVALID/-NOT-OK/-BLANK.

---

## DB2 Write Processing Detail

### 9600-WRITE-PROCESSING (lines 1531-1590): Upsert Pattern

```
MOVE TTUP-NEW-TTYP-TYPE TO DCL-TR-TYPE
MOVE FUNCTION TRIM(TTUP-NEW-TTYP-TYPE-DESC) TO DCL-TR-DESCRIPTION-TEXT
COMPUTE DCL-TR-DESCRIPTION-LEN = FUNCTION LENGTH(TTUP-NEW-TTYP-TYPE-DESC)

EXEC SQL UPDATE CARDDEMO.TRANSACTION_TYPE
    SET TR_DESCRIPTION = :DCL-TR-DESCRIPTION
  WHERE TR_TYPE = :DCL-TR-TYPE
END-EXEC

EVALUATE TRUE
  WHEN SQLCODE = 0    --> SYNCPOINT; SET TTUP-CHANGES-OKAYED-AND-DONE
  WHEN SQLCODE = +100 --> PERFORM 9700-INSERT-RECORD  (row doesn't exist; insert)
  WHEN SQLCODE = -911 --> COULD-NOT-LOCK-REC-FOR-UPDATE; SET TTUP-CHANGES-OKAYED-LOCK-ERROR
  WHEN SQLCODE < 0    --> TABLE-UPDATE-FAILED; STRING error msg
END-EVALUATE

EVALUATE TRUE
  WHEN COULD-NOT-LOCK-REC-FOR-UPDATE  --> SET TTUP-CHANGES-OKAYED-LOCK-ERROR
  WHEN TABLE-UPDATE-FAILED            --> SET TTUP-CHANGES-OKAYED-BUT-FAILED
  WHEN DATA-WAS-CHANGED-BEFORE-UPDATE --> SET TTUP-SHOW-DETAILS
  WHEN OTHER                          --> SET TTUP-CHANGES-OKAYED-AND-DONE
END-EVALUATE
```

**Upsert behavior:** If UPDATE finds no row (SQLCODE +100), the program automatically falls through to INSERT (9700-INSERT-RECORD). This means pressing F5 on a "new record" creation attempt will insert the record.

### 9800-DELETE-PROCESSING (lines 1624-1663)

```
MOVE TTUP-OLD-TTYP-TYPE TO DCL-TR-TYPE

EXEC SQL DELETE FROM CARDDEMO.TRANSACTION_TYPE
  WHERE TR_TYPE = :DCL-TR-TYPE
END-EXEC

EVALUATE TRUE
  WHEN SQLCODE = 0    --> SET TTUP-DELETE-DONE; SYNCPOINT
  WHEN SQLCODE = -532 --> RECORD-DELETE-FAILED; "delete child records first" + SQLERRM
  WHEN OTHER          --> RECORD-DELETE-FAILED; SET TTUP-DELETE-FAILED; format error
END-EVALUATE
```

**Note:** Uses `TTUP-OLD-TTYP-TYPE` (the originally-fetched record) as the delete key, not the current screen input. This prevents a user from altering the key after requesting delete.

---

## Called Programs

| Program     | Method          | Trigger                          | Purpose                                      |
|-------------|-----------------|----------------------------------|----------------------------------------------|
| COADM01C    | CICS XCTL       | PF3 (exit, no prior caller)      | Admin menu                                   |
| COTRTLIC    | (return via CDEMO-FROM-PROGRAM) | PF3 (if called from CTLI)  | Return to list screen                    |
| DSNTIAC     | CICS CALL       | 9999-FORMAT-DB2-MESSAGE          | Format DB2 SQL error text (via CSDB2RPY)    |

**[UNRESOLVED]** COADM01C is a base CardDemo program. CSSETATY is referenced at line 1358 (COPY CSSETATY REPLACING) but not present in this extension directory.

---

## Error Handling

### Abend Handler (lines 348-350, 1675-1698)
EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE) is established at program entry. If any CICS or DB2 command raises an unexpected condition:
1. If ABEND-MSG is LOW-VALUES, set to 'UNEXPECTED ABEND OCCURRED.'
2. Move LIT-THISPGM to ABEND-CULPRIT; move '9999' to ABEND-CODE
3. EXEC CICS SEND FROM(ABEND-DATA) NOHANDLE ERASE
4. EXEC CICS HANDLE ABEND CANCEL
5. EXEC CICS ABEND ABCODE(ABEND-CODE)

### PFK Validation (0001-CHECK-PFKEYS, lines 577-618)
Valid keys at each state:
- ENTER: Always valid except TTUP-CONFIRM-DELETE state
- PFK03: Always valid
- PFK04: Valid when TTUP-SHOW-DETAILS or TTUP-CONFIRM-DELETE
- PFK05: Valid when TTUP-CHANGES-OK-NOT-CONFIRMED, TTUP-DETAILS-NOT-FOUND, TTUP-DELETE-IN-PROGRESS
- PFK12: Valid when TTUP-CHANGES-OK-NOT-CONFIRMED, TTUP-SHOW-DETAILS, TTUP-DETAILS-NOT-FOUND, TTUP-CONFIRM-DELETE, TTUP-CREATE-NEW-RECORD

Invalid key → SET PFK-INVALID; if WS-RETURN-MSG-OFF: SET WS-INVALID-KEY-PRESSED.

### DB2 SQLCODE Handling

| Operation | SQLCODE | Handling                                                              |
|-----------|---------|-----------------------------------------------------------------------|
| SELECT    | 0       | FOUND-TRANTYPE-IN-TABLE; store to TTUP-OLD-DETAILS                    |
| SELECT    | +100    | INPUT-ERROR + FLG-TRANFILTER-NOT-OK + WS-RECORD-NOT-FOUND            |
| SELECT    | < 0     | INPUT-ERROR + FLG-TRANFILTER-NOT-OK + STRING error+SQLERRM           |
| UPDATE    | 0       | SYNCPOINT; TTUP-CHANGES-OKAYED-AND-DONE                               |
| UPDATE    | +100    | Fall through to 9700-INSERT-RECORD (upsert)                           |
| UPDATE    | -911    | COULD-NOT-LOCK-REC-FOR-UPDATE; TTUP-CHANGES-OKAYED-LOCK-ERROR        |
| UPDATE    | < 0     | TABLE-UPDATE-FAILED; TTUP-CHANGES-OKAYED-BUT-FAILED + error msg      |
| INSERT    | 0       | SYNCPOINT; (TTUP-CHANGES-OKAYED-AND-DONE from outer EVALUATE)         |
| INSERT    | OTHER   | TABLE-UPDATE-FAILED + error msg; GO TO INSERT-RECORD-EXIT            |
| DELETE    | 0       | SET TTUP-DELETE-DONE; SYNCPOINT                                       |
| DELETE    | -532    | RECORD-DELETE-FAILED + "delete child records first"                   |
| DELETE    | OTHER   | RECORD-DELETE-FAILED; SET TTUP-DELETE-FAILED + error msg              |

---

## Business Rules

1. **Transaction type code is the primary key and cannot be changed.** Once a record is found and TTUP-SHOW-DETAILS is set, the type code field is protected. Update only modifies TR_DESCRIPTION.

2. **Type code must be a non-zero 2-digit numeric.** Validated by 1210-EDIT-TRANTYPE/1245-EDIT-NUM-REQD: must be numeric, must not be zero, zero-padded to 2 digits.

3. **Description must be alphanumeric (A-Z, a-z, 0-9, space).** Validated by 1230-EDIT-ALPHANUM-REQD. Special characters are rejected.

4. **Two-step confirmation for save:** After input passes validation (ENTER), state transitions to TTUP-CHANGES-OK-NOT-CONFIRMED with the message "Changes validated. Press F5 to save". User must press F5 to actually write to DB2.

5. **Two-step confirmation for delete:** User presses F4 on a displayed record → TTUP-CONFIRM-DELETE + "Delete this record? Press F4 to confirm". User presses F4 again → 9800-DELETE-PROCESSING executes.

6. **Upsert semantics for save (F5):** If UPDATE returns SQLCODE +100 (row not found, typically because user confirmed create new), the program falls through to INSERT without user notification of the distinction.

7. **Change detection prevents no-op updates.** 1205-COMPARE-OLD-NEW compares trimmed, uppercased new and old values. Identical values result in NO-CHANGES-DETECTED and the update is blocked.

8. **FK constraint enforced on delete.** SQLCODE -532 (referential integrity violation) produces "Please delete associated child records first: SQLCODE: -532: [SQLERRM]".

9. **Lock failure on update (SQLCODE -911):** Sets TTUP-CHANGES-OKAYED-LOCK-ERROR state. Screen shows "Could not lock record for update" and INFORM-FAILURE. User must retry.

10. **Cancel (F12) behavior:**
    - In TTUP-CONFIRM-DELETE: WS-DELETE-WAS-CANCELLED + TTUP-DETAILS-NOT-FETCHED
    - In TTUP-CHANGES-OK-NOT-CONFIRMED: WS-UPDATE-WAS-CANCELLED + TTUP-CHANGES-BACKED-OUT
    - In TTUP-SHOW-DETAILS or TTUP-DETAILS-NOT-FOUND: re-fetches record (if key valid) and redisplays
    - After TTUP-CHANGES-OKAYED-AND-DONE/FAILED/DELETE-DONE/FAILED: resets to initial state

---

## Input/Output Specification

### Inputs

| Source                | Field          | Description                                          |
|-----------------------|----------------|------------------------------------------------------|
| CTRTUPAI.TRTYPCDI     | Type code      | 2-digit numeric transaction type code (search key)   |
| CTRTUPAI.TRTYDSCI     | Description    | Up to 50 alphanumeric characters                     |
| DFHCOMMAREA           | Program state  | TTUP-CHANGE-ACTION + TTUP-OLD/NEW-DETAILS             |
| EIBAID                | PF key         | ENTER/PF03/PFK04/PFK05/PFK12                         |
| EIBCALEN              | Commarea length| 0 = first invocation                                 |

### Outputs

| Target                | Field          | Description                                                  |
|-----------------------|----------------|--------------------------------------------------------------|
| CTRTUPAO.TRTYPCDO     | Type code      | Displayed (and colorized) transaction type code              |
| CTRTUPAO.TRTYDSCO     | Description    | Displayed (and editable when appropriate) description         |
| CTRTUPAO.INFOMSGO     | Info message   | Center-justified instructional/status message                 |
| CTRTUPAO.ERRMSGO      | Error message  | Red, bright error text                                        |
| CTRTUPAO.FKEYS/04/05/12 | PF key labels| Visible/hidden based on valid actions for current state      |
| CARDDEMO-COMMAREA     | Return commarea| Updated state + old/new data                                 |

---

## Copybook Dependencies

| Copybook    | Include Method                           | Content                                                       |
|-------------|------------------------------------------|---------------------------------------------------------------|
| CSUTLDWY    | COPY 'CSUTLDWY' (line 76)                | Generic date edit variables CCYYMMDD                          |
| CVCRD01Y    | COPY CVCRD01Y (line 241)                 | Common card/account working storage                           |
| DFHBMSCA    | COPY DFHBMSCA (line 257)                 | IBM BMS attribute byte constants                              |
| DFHAID      | COPY DFHAID (line 258)                   | IBM CICS AID (PF key) constants                               |
| COTTL01Y    | COPY COTTL01Y (line 262)                 | Screen title lines                                            |
| COTRTUP     | COPY COTRTUP (line 265)                  | BMS copybook: CTRTUPAI / CTRTUPAO structures                  |
| CSDAT01Y    | COPY CSDAT01Y (line 268)                 | Current date/time working variables                           |
| CSMSG01Y    | COPY CSMSG01Y (line 271)                 | Common messages                                               |
| CSMSG02Y    | COPY CSMSG02Y (line 274)                 | Abend variables (ABEND-DATA structure)                        |
| CSUSR01Y    | COPY CSUSR01Y (line 277)                 | Signed-on user data                                           |
| SQLCA       | EXEC SQL INCLUDE SQLCA (line 282-284)    | SQL Communication Area                                        |
| DCLTRTYP    | EXEC SQL INCLUDE DCLTRTYP (line 286)     | DCLGEN for CARDDEMO.TRANSACTION_TYPE                          |
| DCLTRCAT    | EXEC SQL INCLUDE DCLTRCAT (line 288)     | DCLGEN for CARDDEMO.TRANSACTION_TYPE_CATEGORY (included but not used in SQL) |
| COCOM01Y    | COPY COCOM01Y (line 292)                 | CARDDEMO application commarea layout                          |
| CSSETATY    | COPY CSSETATY (line 1358, REPLACING)     | Screen attribute setting routine (DESCRIPTION field)          |
| CSSTRPFY    | COPY 'CSSTRPFY' (line 1671)              | PF key store/map routine                                      |

**[UNRESOLVED]** The following are base CardDemo copybooks not present in this extension directory:
- CSUTLDWY, CVCRD01Y, COTTL01Y, CSDAT01Y, CSMSG01Y, CSMSG02Y, CSUSR01Y, COCOM01Y, CSSETATY, CSSTRPFY
