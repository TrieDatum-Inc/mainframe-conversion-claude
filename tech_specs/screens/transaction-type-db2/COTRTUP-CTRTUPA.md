# Screen Specification: COTRTUP / CTRTUPA

## Screen Overview

| Attribute         | Value                                                                |
|-------------------|----------------------------------------------------------------------|
| Mapset Name       | COTRTUP                                                              |
| Map Name          | CTRTUPA                                                              |
| BMS Source        | app/app-transaction-type-db2/bms/COTRTUP.bms                         |
| BMS Copybook      | app/app-transaction-type-db2/cpy-bms/COTRTUP.cpy                     |
| Owning Program    | COTRTUPC                                                             |
| Transaction ID    | CTTU                                                                 |
| Screen Dimensions | 24 rows x 80 columns                                                 |
| Mode              | INOUT (DFHMSD MODE=INOUT)                                            |
| Storage           | AUTO (DFHMSD STORAGE=AUTO)                                           |
| TIOAPFX           | YES                                                                  |
| CTRL              | FREEKB (keyboard unlock on send)                                     |
| Extended Attrs    | DSATTS and MAPATTS = COLOR, HILIGHT, PS, VALIDN                      |
| CSD Resource      | DEFINE MAPSET(COTRTUP) GROUP(CARDDEMO) — csd/CRDDEMOD.csd line 6    |
| CSD Description   | CREDIT CARD TRAN TYPE MAINT MAP                                      |
| Function          | Add new or update/delete an existing transaction type record         |

### Purpose

This is the Transaction Type Add/Edit/Delete screen. It presents a single-record detail form for maintaining an individual entry in `CARDDEMO.TRANSACTION_TYPE`. The user enters a 2-digit transaction type code to search, and the program either displays the existing record for editing/deletion or prompts to create a new one.

---

## Screen Layout (ASCII Art)

```
Col:  1         2         3         4         5         6         7         8
      0123456789012345678901234567890123456789012345678901234567890123456789012345678901
Row:
01 |  Tran: CTTU         [          TITLE01 (40)          ]  Date: mm/dd/yy
02 |  Prog: COTRTUPC     [          TITLE02 (40)          ]  Time: hh:mm:ss
03 |
04 |
05 |
06 |
07 |                            Maintain Transaction Type
08 |
09 |
10 |
11 |
12 |   Transaction Type  : [XX]
13 |
14 |   Description       : [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
15 |
16 |
17 |
18 |
19 |
20 |
21 |
22 |                       [            INFOMSG (45)           ]
23 |  [ERRMSG                                                                    ]
24 |  ENTER=Process F3=Exit  F4=Delete  F5=Save  F6=Add  [dark]     F12=Cancel
```

**Legend:** `[XX]` = 2-char input field, `[XXXX...]` = 50-char input field, `[dark]` = dark/hidden field, `[text]` = output-only field

---

## Map Definition Details

```
COTRTUP DFHMSD LANG=COBOL, MODE=INOUT, STORAGE=AUTO, TIOAPFX=YES, TYPE=&&SYSPARM
CTRTUPA DFHMDI CTRL=(FREEKB), DSATTS=(COLOR,HILIGHT,PS,VALIDN),
                MAPATTS=(COLOR,HILIGHT,PS,VALIDN), SIZE=(24,80)
```

---

## Field Definitions

### Header Fields (Rows 1-2)

| BMS Name  | Row | Col | Len | Attr            | Color    | Initial Value | I/O    | Description                   |
|-----------|-----|-----|-----|-----------------|----------|---------------|--------|-------------------------------|
| (static)  | 1   | 1   | 5   | ASKIP,NORM      | BLUE     | 'Tran:'       | Output | Label                         |
| TRNNAME   | 1   | 7   | 4   | ASKIP,FSET,NORM | BLUE     | (blank)       | Both   | Transaction ID (CTTU)         |
| TITLE01   | 1   | 21  | 40  | ASKIP,NORM      | YELLOW   | (blank)       | Both   | Screen title line 1           |
| (static)  | 1   | 65  | 5   | ASKIP,NORM      | BLUE     | 'Date:'       | Output | Label                         |
| CURDATE   | 1   | 71  | 8   | ASKIP,NORM      | BLUE     | 'mm/dd/yy'    | Both   | Current date                  |
| (static)  | 2   | 1   | 5   | ASKIP,NORM      | BLUE     | 'Prog:'       | Output | Label                         |
| PGMNAME   | 2   | 7   | 8   | ASKIP,NORM      | BLUE     | (blank)       | Both   | Program name (COTRTUPC)       |
| TITLE02   | 2   | 21  | 40  | ASKIP,NORM      | YELLOW   | (blank)       | Both   | Screen title line 2           |
| (static)  | 2   | 65  | 5   | ASKIP,NORM      | BLUE     | 'Time:'       | Output | Label                         |
| CURTIME   | 2   | 71  | 8   | ASKIP,NORM      | BLUE     | 'hh:mm:ss'    | Both   | Current time                  |

### Screen Title (Row 7)

| BMS Name | Row | Col | Len | Attr        | Color   | Initial Value              | I/O    | Description        |
|----------|-----|-----|-----|-------------|---------|----------------------------|--------|--------------------|
| (static) | 7   | 28  | 25  | (default)   | NEUTRAL | 'Maintain Transaction Type'| Output | Screen function title |

### Data Entry Fields (Rows 12 and 14)

| BMS Name | Row | Col | Len | BMS Attr      | Hilight   | I/O  | Description                                       |
|----------|-----|-----|-----|---------------|-----------|------|---------------------------------------------------|
| (static) | 12  | 4   | 19  | ASKIP,NORM    | (none)    | Out  | Label: 'Transaction Type  :' — TURQUOISE          |
| TRTYPCD  | 12  | 26  | 2   | IC, UNPROT    | UNDERLINE | Both | Transaction type code (2-digit, numeric, required)|
| (stopper)| 12  | 29  | 0   |               |           |      | Field stopper after TRTYPCD                       |
| (static) | 14  | 4   | 19  | (default)     | (none)    | Out  | Label: 'Description       :' — TURQUOISE          |
| TRTYDSC  | 14  | 26  | 50  | UNPROT        | UNDERLINE | Both | Transaction description (alphanumeric, required)  |
| (stopper)| 14  | 77  | 0   |               |           |      | Field stopper after TRTYDSC                       |

**Notes on data fields:**
- TRTYPCD has IC (Initial Cursor): cursor starts here on fresh display
- TRTYPCD: no explicit FSET in BMS definition — the program manages attribute bytes programmatically
- TRTYDSC: no explicit FSET in BMS definition — the program manages attribute bytes programmatically
- Both fields default to UNPROT; program applies DFHBMPRF (protect) or DFHBMFSE (unprotect) based on state

### Message Fields (Rows 22 and 23)

| BMS Name | Row | Col | Len | Attr         | Color   | Hilight | I/O  | Description                                            |
|----------|-----|-----|-----|--------------|---------|---------|------|--------------------------------------------------------|
| INFOMSG  | 22  | 23  | 45  | ASKIP        | NEUTRAL | OFF     | Both | Information/instruction message (center-justified)     |
| (stopper)| 22  | 69  | 0   |              |         |         |      | Field stopper                                          |
| ERRMSG   | 23  | 1   | 78  | ASKIP,BRT,FSET| RED    | (none)  | Both | Error message (bright red, full width)                 |

### Function Key Labels (Row 24)

| BMS Name | Row | Col | Len | BMS Attr   | Color  | Initial Value       | Description                                          |
|----------|-----|-----|-----|------------|--------|---------------------|------------------------------------------------------|
| FKEYS    | 24  | 1   | 21  | ASKIP,NORM | YELLOW | 'ENTER=Process F3=Exit' | Base keys (always visible, but ENTER controlled by pgm) |
| FKEY04   | 24  | 23  | 9   | ASKIP,DRK  | YELLOW | 'F4=Delete'         | Delete key (dark by default; shown when TTUP-SHOW-DETAILS or TTUP-CONFIRM-DELETE) |
| FKEY05   | 24  | 33  | 8   | ASKIP,DRK  | YELLOW | 'F5=Save'           | Save key (dark by default; shown when confirm-needed or not-found) |
| FKEY06   | 24  | 43  | 6   | ASKIP,DRK  | YELLOW | 'F6=Add'            | Add key (dark by default; **not activated by program logic** — [SEE NOTE]) |
| FKEY12   | 24  | 69  | 10  | ASKIP,DRK  | YELLOW | 'F12=Cancel'        | Cancel key (dark by default; shown in multiple states) |

**Note on FKEY06 (F6=Add):** The BMS defines this field as an initially dark label but COTRTUPC does not contain any logic to set FKEY06A (its attribute byte) to DFHBMASB. The program uses F5 for both add (INSERT) and save (UPDATE), not F6. This label appears to be a BMS artifact or was reserved for a separate "add mode" that was not implemented in the current program logic.

**Dynamic visibility** is controlled by COTRTUPC paragraph 3391-SETUP-PFKEY-ATTRS (lines 1397-1422):
- FKEYS (ENTER area) attribute: DFHBMDAR (dark/invisible) when TTUP-CONFIRM-DELETE; DFHBMASB (visible) otherwise
- FKEY04: DFHBMASB when TTUP-SHOW-DETAILS or TTUP-CONFIRM-DELETE; otherwise remains initial DRK
- FKEY05: DFHBMASB when TTUP-CHANGES-OK-NOT-CONFIRMED or TTUP-DETAILS-NOT-FOUND
- FKEY12: DFHBMASB when any of: TTUP-CHANGES-OK-NOT-CONFIRMED, TTUP-SHOW-DETAILS, TTUP-DETAILS-NOT-FOUND, TTUP-CONFIRM-DELETE, TTUP-CREATE-NEW-RECORD

---

## Field-Level COBOL Copybook Layout (cpy-bms/COTRTUP.cpy)

Two 01-level areas are generated:

### CTRTUPAI (Input)

| Input Field   | Length | Description                                        |
|---------------|--------|----------------------------------------------------|
| TRNNAMEI      | X(4)   | Transaction ID (CTTU)                              |
| TITLE01I      | X(40)  | Title 1                                            |
| CURDATEI      | X(8)   | Current date                                       |
| PGMNAMEI      | X(8)   | Program name                                       |
| TITLE02I      | X(40)  | Title 2                                            |
| CURTIMEI      | X(8)   | Current time                                       |
| TRTYPCDI      | X(2)   | **Transaction type code input** (key field)        |
| TRTYDSCI      | X(50)  | **Description input**                              |
| INFOMSGI      | X(45)  | Info message input (normally protected)            |
| ERRMSGI       | X(78)  | Error message input (normally ASKIP)               |
| FKEYSI        | X(21)  | ENTER+F3 key labels area                           |
| FKEY04I       | X(9)   | F4 label area                                      |
| FKEY05I       | X(8)   | F5 label area                                      |
| FKEY06I       | X(6)   | F6 label area                                      |
| FKEY12I       | X(10)  | F12 label area                                     |

**Associated attribute bytes (input side, used by program):**
- `TRTYPCDA` — attribute byte for TRTYPCD field (set by 3310-PROTECT-ALL-ATTRS, 3320-UNPROTECT-FEW-ATTRS, 3300-SETUP-SCREEN-ATTRS)
- `TRTYDSCA` — attribute byte for TRTYDSC field
- `INFOMSGA` — attribute byte for INFOMSG field
- `TRTYPCDL` — length field; set to -1 to position cursor on TRTYPCD (lines 1313, 1324)
- `TRTYDSCL` — length field; set to -1 to position cursor on TRTYDSC (line 1322)
- `FKEYSA`, `FKEY04A`, `FKEY05A`, `FKEY12A` — attribute bytes for PF key labels

### CTRTUPAO (Output — REDEFINES CTRTUPAI)

Each field expands to: 3-byte FILLER + C (color) + P (PS) + H (highlight) + V (validation) + O (data).

Relevant output fields used by COTRTUPC:
- `TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO`
- `TRTYPCDO` — displayed transaction type code (X(2))
- `TRTYDSCO` — displayed description (X(50))
- `TRTYPCDC` — color byte for TRTYPCD (set to DFHRED on error/delete-failed, line 1333)
- `INFOMSGO` — information message (X(45))
- `ERRMSGO` — error message (X(78))

---

## Navigation — PF Key Assignments

| Key    | State(s) Where Valid                              | Action                                                                  |
|--------|---------------------------------------------------|-------------------------------------------------------------------------|
| ENTER  | All states except TTUP-CONFIRM-DELETE             | Submit input; validate; search DB2; advance state                       |
| F3     | Always                                            | Exit to calling program (Admin Menu CA00 or COTRTLIC)                   |
| F4     | TTUP-SHOW-DETAILS                                 | Request delete — transition to TTUP-CONFIRM-DELETE                      |
| F4     | TTUP-CONFIRM-DELETE                               | Confirm delete — execute 9800-DELETE-PROCESSING                         |
| F5     | TTUP-DETAILS-NOT-FOUND                            | Confirm intent to create new record (TTUP-CREATE-NEW-RECORD)            |
| F5     | TTUP-CHANGES-OK-NOT-CONFIRMED                     | Confirm save — execute 9600-WRITE-PROCESSING (UPDATE or INSERT)         |
| F12    | TTUP-CHANGES-OK-NOT-CONFIRMED                     | Cancel update — TTUP-CHANGES-BACKED-OUT                                 |
| F12    | TTUP-SHOW-DETAILS, TTUP-DETAILS-NOT-FOUND         | Cancel / re-fetch data and return to display state                      |
| F12    | TTUP-CONFIRM-DELETE                               | Cancel delete — TTUP-DETAILS-NOT-FETCHED                                |
| F12    | TTUP-CREATE-NEW-RECORD                            | Cancel add — reset to initial state                                     |

**Invalid key handling:** Any unrecognized key is treated as invalid; WS-INVALID-KEY-PRESSED message is set and the screen is resent without state change.

---

## Data Flow

### Screen to Program

1. CICS RECEIVE MAP fills CTRTUPAI (paragraph 1100-RECEIVE-MAP, line 641).
2. Paragraph 1150-STORE-MAP-IN-NEW (lines 652-685) copies:
   - `TRTYPCDI OF CTRTUPAI` → `TTUP-NEW-TTYP-TYPE` (after TRIM; asterisk/spaces → LOW-VALUES)
   - `TRTYDSCI OF CTRTUPAI` → `TTUP-NEW-TTYP-TYPE-DESC` (after TRIM; asterisk/spaces → LOW-VALUES)
3. Paragraph 1200-EDIT-MAP-INPUTS validates both fields, calls 9000-READ-TRANTYPE if key is valid and not already fetched.

### Program to Screen

1. `3100-SCREEN-INIT`: clears CTRTUPAO; loads date/time/tranid/pgmname/titles.
2. `3200-SETUP-SCREEN-VARS`: routes to one of:
   - 3201-SHOW-INITIAL-VALUES: LOW-VALUES to both output fields
   - 3202-SHOW-ORIGINAL-VALUES: TTUP-OLD data → TRTYPCDO, TRTYDSCO
   - 3203-SHOW-UPDATED-VALUES: TTUP-NEW data → TRTYPCDO, TRTYDSCO
3. `3250-SETUP-INFOMSG`: selects and centers the information message; moves to INFOMSGO + ERRMSGO.
4. `3300-SETUP-SCREEN-ATTRS`: sets attribute bytes for TRTYPCD and TRTYDSC; sets cursor position.
5. `3390-SETUP-INFOMSG-ATTRS`: sets INFOMSGA.
6. `3391-SETUP-PFKEY-ATTRS`: shows/hides PF key labels.
7. `3400-SEND-SCREEN`: EXEC CICS SEND MAP ERASE FREEKB CURSOR.

---

## State-Driven Screen Behavior

The screen appearance changes based on the program state machine (`TTUP-CHANGE-ACTION`). The following table summarizes the complete screen behavior per state:

| State                        | TRTYPCD Field     | TRTYDSC Field     | Info Message                                | PF Keys Shown       |
|------------------------------|-------------------|-------------------|---------------------------------------------|---------------------|
| TTUP-DETAILS-NOT-FETCHED     | Editable (FSET)   | Protected         | 'Enter transaction type to be maintained'   | ENTER, F3           |
| TTUP-INVALID-SEARCH-KEYS     | Editable (FSET)   | Protected         | 'Enter transaction type to be maintained'   | ENTER, F3           |
| TTUP-DETAILS-NOT-FOUND       | Editable (FSET)   | Protected         | 'Press F05 to add. F12 to cancel'           | ENTER, F3, F5, F12  |
| TTUP-SHOW-DETAILS            | Protected         | Editable (FSET)   | 'Update transaction type details shown.'    | ENTER, F3, F4, F12  |
| TTUP-CREATE-NEW-RECORD       | Protected         | Editable (FSET)   | 'Enter new transaction type details.'       | ENTER, F3, F12      |
| TTUP-CHANGES-NOT-OK          | Protected         | Editable (FSET)   | 'Update transaction type details shown.'    | ENTER, F3           |
| TTUP-CHANGES-BACKED-OUT      | Protected (has old data) | Editable  | 'Update transaction type details shown.'    | ENTER, F3           |
| TTUP-CHANGES-BACKED-OUT (no old) | Editable      | Protected         | 'Enter transaction type to be maintained'   | ENTER, F3           |
| TTUP-CONFIRM-DELETE          | Protected         | Protected         | 'Delete this record ? Press F4 to confirm'  | F3, F4, F12         |
| TTUP-DELETE-FAILED           | Editable (FSET)   | Protected         | 'Changes unsuccessful'                      | ENTER, F3           |
| TTUP-DELETE-DONE             | Editable          | Protected         | (reset to initial)                          | ENTER, F3           |
| TTUP-CHANGES-OK-NOT-CONFIRMED| Protected         | Protected         | 'Changes validated.Press F5 to save'        | ENTER, F3, F5, F12  |
| TTUP-CHANGES-OKAYED-AND-DONE | Protected         | Protected         | 'Changes committed to database'             | ENTER, F3           |
| TTUP-CHANGES-OKAYED-LOCK-ERROR| Protected        | Protected         | 'Changes unsuccessful'                      | ENTER, F3           |
| TTUP-CHANGES-OKAYED-BUT-FAILED| Protected        | Protected         | 'Changes unsuccessful'                      | ENTER, F3           |

### Cursor Position Rules (3300-SETUP-SCREEN-ATTRS, lines 1303-1325)

| Condition                                    | Cursor Goes To |
|----------------------------------------------|----------------|
| TTUP-DETAILS-NOT-FETCHED                     | TRTYPCD        |
| TTUP-DETAILS-NOT-FOUND                       | TRTYPCD        |
| TTUP-INVALID-SEARCH-KEYS                     | TRTYPCD        |
| FLG-TRANFILTER-NOT-OK or blank               | TRTYPCD        |
| TTUP-CHANGES-OKAYED-AND-DONE                 | TRTYPCD        |
| TTUP-CHANGES-BACKED-OUT (no old data)        | TRTYPCD        |
| TTUP-CREATE-NEW-RECORD                       | TRTYDSC        |
| NO-CHANGES-DETECTED                          | TRTYDSC        |
| FLG-DESCRIPTION-NOT-OK or BLANK              | TRTYDSC        |
| TTUP-CHANGES-MADE or BACKED-OUT (has data)   | TRTYDSC        |
| TTUP-SHOW-DETAILS                            | TRTYDSC        |
| OTHER                                        | TRTYPCD        |

### Color Rules

| Field    | Condition                                   | Color     |
|----------|---------------------------------------------|-----------|
| TRTYPCD  | FLG-TRANFILTER-NOT-OK                       | DFHRED    |
| TRTYPCD  | TTUP-DELETE-FAILED                          | DFHRED    |
| TRTYPCD  | FLG-TRANFILTER-BLANK and CDEMO-PGM-REENTER  | DFHRED (+ display '*') |
| TRTYDSC  | FLG-DESCRIPTION-NOT-OK (via CSSETATY COPY)  | DFHRED    |
| TRTYDSC  | FLG-DESCRIPTION-BLANK (via CSSETATY COPY)   | DFHRED    |
| TRTYDSC  | FLG-DESCRIPTION-ISVALID (via CSSETATY COPY) | Default   |

The TRTYDSC color is set via `COPY CSSETATY REPLACING ==(TESTVAR1)== BY ==DESCRIPTION== ==(SCRNVAR2)== BY ==TRTYDSC== ==(MAPNAME3)== BY ==CTRTUPA==` (lines 1358-1361). The actual attribute constants used are defined within CSSETATY and not directly visible in this source.

---

## Information Messages (INFOMSG, row 22)

Messages are set by `3250-SETUP-INFOMSG` (lines 1210-1265) and center-justified before display:

| State / Condition                          | Info Message                                   |
|--------------------------------------------|------------------------------------------------|
| CDEMO-PGM-ENTER                            | 'Enter transaction type to be maintained'      |
| TTUP-DETAILS-NOT-FETCHED                   | 'Enter transaction type to be maintained'      |
| TTUP-INVALID-SEARCH-KEYS                   | 'Enter transaction type to be maintained'      |
| TTUP-DETAILS-NOT-FOUND                     | 'Press F05 to add. F12 to cancel'              |
| TTUP-SHOW-DETAILS (with no old data)       | 'Enter transaction type to be maintained'      |
| TTUP-CHANGES-BACKED-OUT (no old data)      | 'Enter transaction type to be maintained'      |
| TTUP-CHANGES-BACKED-OUT (has data)         | 'Update transaction type details shown.'       |
| TTUP-CHANGES-NOT-OK                        | 'Update transaction type details shown.'       |
| TTUP-CONFIRM-DELETE                        | 'Delete this record ? Press F4 to confirm'     |
| TTUP-DELETE-FAILED                         | 'Changes unsuccessful'                         |
| TTUP-DELETE-DONE                           | 'Delete successful.'                           |
| TTUP-CREATE-NEW-RECORD                     | 'Enter new transaction type details.'          |
| TTUP-CHANGES-OK-NOT-CONFIRMED              | 'Changes validated.Press F5 to save'           |
| TTUP-CHANGES-OKAYED-AND-DONE               | 'Changes committed to database'                |
| TTUP-CHANGES-OKAYED-LOCK-ERROR             | 'Changes unsuccessful'                         |
| TTUP-CHANGES-OKAYED-BUT-FAILED             | 'Changes unsuccessful'                         |
| WS-NO-INFO-MESSAGE (default)               | 'Enter transaction type to be maintained'      |

---

## Error Messages (ERRMSG, row 23)

Messages are placed in WS-RETURN-MSG and moved to ERRMSGO via `3250-SETUP-INFOMSG` (line 1264):

| Condition                                  | Error Message                                          |
|--------------------------------------------|--------------------------------------------------------|
| WS-INVALID-KEY-PRESSED                     | 'Invalid key pressed'                                  |
| PF03 exit                                  | 'PF03 pressed.Exiting              '                   |
| Type code blank                            | 'Tran Type code must be supplied.'                     |
| Type code not numeric                      | 'Tran Type code must be numeric.'                      |
| Type code = 0                              | 'Tran Type code must not be zero.'                     |
| Description blank                          | 'Transaction Desc must be supplied.'                   |
| Description has special chars              | 'Transaction Desc can have numbers or alphabets only.' |
| No input received                          | 'No input received'                                    |
| Record not found in DB2                    | 'No record found for this key in database'             |
| No change detected                         | 'No change detected with respect to values fetched.'   |
| Lock error on update                       | 'Could not lock record for update'                     |
| Record changed concurrently                | 'Record changed by some one else. Please review'       |
| Update cancelled                           | 'Update was cancelled'                                 |
| Table update failed                        | 'Update of record failed'                              |
| Delete failed                              | 'Delete of record failed'                              |
| Delete cancelled                           | 'Delete was cancelled'                                 |
| DB2 UPDATE error                           | 'Error updating: TRANSACTION_TYPE Table. SQLCODE: NNN: [SQLERRM]' |
| DB2 INSERT error                           | 'Error inserting record into: TRANSACTION_TYPE Table. SQLCODE: NNN: [SQLERRM]' |
| DB2 SELECT error                           | 'Error accessing: TRANSACTION_TYPE table. SQLCODE: NNN: [SQLERRM]' |
| Delete FK violation (SQLCODE -532)         | 'Please delete associated child records first: SQLCODE: -532: [SQLERRM]' |
| Delete general failure                     | 'Delete failed with message: SQLCODE: NNN: [SQLERRM]'  |

---

## Related Screens

| Screen     | Mapset   | Program  | Transaction | Relationship                                                  |
|------------|----------|----------|-------------|---------------------------------------------------------------|
| CTRTLIA    | COTRTLI  | COTRTLIC | CTLI        | List screen; F2 from CTLI transfers to CTTU; F3 returns to CTLI |
| COADM1A    | COADM01  | COADM01C | CA00        | Admin menu; option 6 enters CTTU; F3 returns to CA00 if no CTLI caller |

---

## Commarea Structure

COTRTUPC uses WS-COMMAREA (PIC X(2000)) packed as:
- Bytes 1 to LENGTH OF CARDDEMO-COMMAREA: application commarea (COCOM01Y)
- Bytes following: WS-THIS-PROGCOMMAREA containing:
  - TTUP-CHANGE-ACTION (X(1)): state code
  - TTUP-OLD-TTYP-TYPE (X(2)): original type code from DB2
  - TTUP-OLD-TTYP-TYPE-DESC (X(50)): original description from DB2
  - TTUP-NEW-TTYP-TYPE (X(2)): type code from screen
  - TTUP-NEW-TTYP-TYPE-DESC (X(50)): description from screen

The commarea is passed via CICS RETURN TRANSID(CTTU) COMMAREA(WS-COMMAREA) on every screen cycle, preserving state across the pseudo-conversational interaction.
