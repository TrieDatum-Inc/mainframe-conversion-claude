# Screen Specification: COTRTLI / CTRTLIA

## Screen Overview

| Attribute         | Value                                                                |
|-------------------|----------------------------------------------------------------------|
| Mapset Name       | COTRTLI                                                              |
| Map Name          | CTRTLIA                                                              |
| BMS Source        | app/app-transaction-type-db2/bms/COTRTLI.bms                         |
| BMS Copybook      | app/app-transaction-type-db2/cpy-bms/COTRTLI.cpy                     |
| Owning Program    | COTRTLIC                                                             |
| Transaction ID    | CTLI                                                                 |
| Screen Dimensions | 24 rows x 80 columns                                                 |
| Mode              | INOUT (DFHMSD MODE=INOUT)                                            |
| Storage           | AUTO (DFHMSD STORAGE=AUTO)                                           |
| TIOAPFX           | YES                                                                  |
| CTRL              | FREEKB (keyboard unlock on send)                                     |
| Extended Attrs    | DSATTS and MAPATTS = COLOR, HILIGHT, PS, VALIDN                      |
| CSD Resource      | DEFINE MAPSET(COTRTLI) GROUP(CARDDEMO) — csd/CRDDEMOD.csd line 1    |
| CSD Description   | CREDIT CARD TRAN TYPE INQ MAP                                        |
| Function          | List, filter, page, update, and delete transaction type records      |

### Purpose

This is the Transaction Type List/Maintenance screen. It displays up to 7 transaction type records fetched from `CARDDEMO.TRANSACTION_TYPE` with optional type code and description filters. The user can type 'U' or 'D' in the Select column next to a row to mark it for update or delete, respectively.

---

## Screen Layout (ASCII Art)

```
Col:  1         2         3         4         5         6         7         8
      0123456789012345678901234567890123456789012345678901234567890123456789012345678901
Row:
01 |  Tran: CTLI         [     TITLE01 (40)         ]  Date: mm/dd/yy
02 |  Prog: COTRTLIC     [     TITLE02 (40)         ]  Time: hh:mm:ss
03 |
04 |                            Maintain Transaction Type            Page NNN
05 |
06 |                              Type Filter:  [XX]
07 |
08 |   Description Filter: [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
09 |
10 |   Select    Type      Description
11 |   ------    -----     --------------------------------------------------
12 |   [_]       [XX]      [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
13 |   [_]       [XX]      [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
14 |   [_]       [XX]      [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
15 |   [_]       [XX]      [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
16 |   [_]       [XX]      [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
17 |   [_]       [XX]      [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
18 |   [_]       [XX]      [XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX]
19 |   (row 8 - reserved for additional display, protected)
20 |
21 |                   [             INFOMSG (45)             ]
22 |
23 |  [ERRMSG                                                                    ]
24 |  F2=Add  F3=Exit  F7=Page Up  F8=Page Dn  F10=Save
```

**Legend:** `[_]` = input field, `[XX]` = 2-char field, `[XXXX...]` = 50-char field, `( )` = label (static text)

---

## Map Definition Details

```
COTRTLI DFHMSD LANG=COBOL, MODE=INOUT, STORAGE=AUTO, TIOAPFX=YES, TYPE=&&SYSPARM
CTRTLIA DFHMDI CTRL=(FREEKB), DSATTS=(COLOR,HILIGHT,PS,VALIDN),
                MAPATTS=(COLOR,HILIGHT,PS,VALIDN), SIZE=(24,80)
```

---

## Field Definitions

### Header Fields (Rows 1-2)

| BMS Name  | Row | Col | Len | Attr              | Color    | Initial Value | Input/Output | Description                     |
|-----------|-----|-----|-----|-------------------|----------|---------------|--------------|---------------------------------|
| (static)  | 1   | 1   | 5   | ASKIP,NORM        | BLUE     | 'Tran:'       | Output       | Label                           |
| TRNNAME   | 1   | 7   | 4   | ASKIP,FSET,NORM   | BLUE     | (blank)       | Both         | Transaction ID (populated by pgm)|
| TITLE01   | 1   | 21  | 40  | ASKIP,NORM        | YELLOW   | (blank)       | Both         | Screen title line 1             |
| (static)  | 1   | 65  | 5   | ASKIP,NORM        | BLUE     | 'Date:'       | Output       | Label                           |
| CURDATE   | 1   | 71  | 8   | ASKIP,NORM        | BLUE     | 'mm/dd/yy'    | Both         | Current date (MM/DD/YY)         |
| (static)  | 2   | 1   | 5   | ASKIP,NORM        | BLUE     | 'Prog:'       | Output       | Label                           |
| PGMNAME   | 2   | 7   | 8   | ASKIP,NORM        | BLUE     | (blank)       | Both         | Program name                    |
| TITLE02   | 2   | 21  | 40  | ASKIP,NORM        | YELLOW   | (blank)       | Both         | Screen title line 2             |
| (static)  | 2   | 65  | 5   | ASKIP,NORM        | BLUE     | 'Time:'       | Output       | Label                           |
| CURTIME   | 2   | 71  | 8   | ASKIP,NORM        | BLUE     | 'hh:mm:ss'    | Both         | Current time (HH:MM:SS)         |

### Title and Page Fields (Row 4)

| BMS Name | Row | Col | Len | Attr              | Color   | Initial Value              | I/O    | Description              |
|----------|-----|-----|-----|-------------------|---------|----------------------------|--------|--------------------------|
| (static) | 4   | 28  | 25  | (default)         | NEUTRAL | 'Maintain Transaction Type'| Output | Screen title label       |
| (static) | 4   | 70  | 5   | (default)         | n/a     | 'Page '                    | Output | Page label               |
| PAGENO   | 4   | 76  | 3   | (default)         | n/a     | (blank)                    | Both   | Current page number      |

### Filter Fields (Rows 6 and 8)

| BMS Name | Row | Col | Len | Attr                        | Color     | Hilight   | I/O   | Description                             |
|----------|-----|-----|-----|-----------------------------|-----------|-----------|-------|-----------------------------------------|
| (static) | 6   | 30  | 12  | ASKIP,NORM                  | TURQUOISE | (none)    | Out   | Label: 'Type Filter:'                   |
| TRTYPE   | 6   | 44  | 2   | FSET, IC, NORM, UNPROT      | GREEN     | UNDERLINE | Both  | Type code filter (optional, 2 digits)   |
| (null)   | 6   | 47  | 0   | (stopper)                   | n/a       | n/a       | n/a   | Field stopper                           |
| (static) | 8   | 4   | 19  | ASKIP,NORM                  | TURQUOISE | (none)    | Out   | Label: 'Description Filter:'            |
| TRDESC   | 8   | 25  | 50  | FSET, NORM, UNPROT          | GREEN     | UNDERLINE | Both  | Description filter (optional substring) |
| (null)   | 8   | 76  | 0   | (stopper)                   | n/a       | n/a       | n/a   | Field stopper                           |

**Notes on filter fields:**
- TRTYPE has IC (Initial Cursor): cursor starts here on a fresh display
- TRTYPE: program validates as numeric; non-numeric → red, error message
- TRDESC: value is wrapped with '%' on both sides to form a DB2 LIKE pattern
- Both fields have FSET (field set flag always present in output)

### Column Headers and Separator (Rows 10-11)

| Row | Col | Len | Initial Value                                       |
|-----|-----|-----|-----------------------------------------------------|
| 10  | 4   | 10  | 'Select    '                                        |
| 10  | 16  | 4   | 'Type'                                              |
| 10  | 42  | 11  | 'Description'                                       |
| 11  | 4   | 6   | '------'                                            |
| 11  | 15  | 5   | '-----'                                             |
| 11  | 25  | 50  | '--------------------------------------------------' |

### Data Rows (Rows 12-18): 7 Repeating Row Groups

Each row group (rows 12-18) contains three fields: Select, Type Code, and Description. The BMS defines them individually as TRTSEL1/TRTTYP1/TRTYPD1 through TRTSEL7/TRTTYP7/TRTYPD7.

**Row Group Template:**

| Field   | Row  | Col | Len | Default Attr          | Color   | Hilight   | I/O  | Description                            |
|---------|------|-----|-----|-----------------------|---------|-----------|------|----------------------------------------|
| TRTSELn | 12-18| 6   | 1   | FSET, NORM, PROT      | DEFAULT | UNDERLINE | Both | Selection action: D/U/blank            |
| (stopper)| 12-18| 8  | 0   |                       |         |           |      | Field stopper after select             |
| TRTTYPn | 12-18| 17  | 2   | FSET, NORM, PROT      | DEFAULT | OFF       | Both | Transaction type code (always protected)|
| (stopper)| 12-18| 20 | 0   |                       |         |           |      | Field stopper after type code          |
| TRTYPDn | 12-18| 25  | 50  | FSET, NORM, UNPROT    | DEFAULT | OFF       | Both | Description (unprotectable by program) |
| (stopper)| 12-18| 76 | 0   |                       |         |           |      | Field stopper after description        |

**Per-row mapping:**

| Row | Select Field | Type Field | Description Field |
|-----|-------------|------------|-------------------|
| 12  | TRTSEL1     | TRTTYP1    | TRTYPD1           |
| 13  | TRTSEL2     | TRTTYP2    | TRTYPD2           |
| 14  | TRTSEL3     | TRTTYP3    | TRTYPD3           |
| 15  | TRTSEL4     | TRTTYP4    | TRTYPD4           |
| 16  | TRTSEL5     | TRTTYP5    | TRTYPD5           |
| 17  | TRTSEL6     | TRTTYP6    | TRTYPD6           |
| 18  | TRTSEL7     | TRTTYP7    | TRTYPD7           |

### Row 8 (Additional Protected Row) — Row 19

| BMS Name | Row | Col | Len | Attr             | Color   | Hilight | I/O  | Description                     |
|----------|-----|-----|-----|------------------|---------|---------|------|---------------------------------|
| TRTSELA  | 19  | 6   | 1   | FSET, NORM, PROT | DEFAULT | OFF     | Both | 8th select field (always protected, never shown as active data row) |
| TRTTYPA  | 19  | 17  | 2   | FSET, NORM, PROT | DEFAULT | OFF     | Both | 8th type code (protected)       |
| TRTDSCA  | 19  | 25  | 50  | FSET, NORM, PROT | DEFAULT | OFF     | Both | 8th description (protected)     |

**Note:** The BMS defines 8 data rows but `WS-MAX-SCREEN-LINES = 7` in COTRTLIC. The 8th row (TRTSELA/TRTTYPA/TRTDSCA) is defined fully protected and is never actively used by the program for data display. It serves as a visual buffer or was included for potential expansion.

### Message Fields (Rows 21 and 23)

| BMS Name | Row | Col | Len | Attr           | Color   | Hilight | I/O  | Description                                    |
|----------|-----|-----|-----|----------------|---------|---------|------|------------------------------------------------|
| INFOMSG  | 21  | 19  | 45  | PROT           | NEUTRAL | OFF     | Both | Information/instruction message (center-justified by pgm) |
| (stopper)| 21  | 65  | 0   |                |         |         |      | Field stopper                                  |
| ERRMSG   | 23  | 1   | 78  | ASKIP,BRT,FSET | RED     | (none)  | Both | Error message (bright red, full width)         |

### Function Key Labels (Row 24)

| BMS Name | Row | Col | Len | Attr      | Color     | Initial Value | Description          |
|----------|-----|-----|-----|-----------|-----------|---------------|----------------------|
| BUTNF02  | 24  | 1   | 7   | ASKIP,NORM| TURQUOISE | 'F2=Add'      | Transfer to add screen |
| BUTNF03  | 24  | 10  | 7   | ASKIP,NORM| TURQUOISE | 'F3=Exit'     | Exit/back to menu    |
| BUTNF07  | 24  | 19  | 10  | ASKIP,NORM| TURQUOISE | 'F7=Page Up'  | Previous page        |
| BUTNF08  | 24  | 32  | 10  | ASKIP,NORM| TURQUOISE | 'F8=Page Dn'  | Next page            |
| BUTNF10  | 24  | 44  | 8   | ASKIP,NORM| TURQUOISE | 'F10=Save'    | Confirm update/delete|

**Note:** Unlike COTRTUP, the function key labels on this screen are static text fields (always visible, ASKIP,NORM). There is no dynamic show/hide of these labels.

---

## Field-Level COBOL Copybook Layout (cpy-bms/COTRTLI.cpy)

The BMS copybook generates two 01-level areas:

### CTRTLIAI (Input)

Each named field (e.g., TRNNAME) expands to a group of 4 sub-fields:
- `TTTTTTLn` — COMP S9(4): field length returned by CICS (MDT status)
- `TTTTTTFn` — PICTURE X: flag byte
- `TTTTTTAn` — PICTURE X: attribute byte (redefines Fn)
- 4-byte FILLER
- `TTTTTTIn` — PIC X(nn): the actual input data

### CTRTLIAO (Output — REDEFINES CTRTLIAI)

Each named field expands to:
- 3-byte FILLER
- `TTTTTTCn` — PICTURE X: color
- `TTTTTTPn` — PICTURE X: PS (programmed symbols)
- `TTTTTTHn` — PICTURE X: highlighting
- `TTTTTTVn` — PICTURE X: validation
- `TTTTTTOn` — PIC X(nn): the actual output data

**Complete field name list from CTRTLIAI:**

| Input Field  | Length | Map Field | Output Field |
|--------------|--------|-----------|--------------|
| TRNNAMEI     | X(4)   | TRNNAME   | TRNNAMEO     |
| TITLE01I     | X(40)  | TITLE01   | TITLE01O     |
| CURDATEI     | X(8)   | CURDATE   | CURDATEO     |
| PGMNAMEI     | X(8)   | PGMNAME   | PGMNAMEO     |
| TITLE02I     | X(40)  | TITLE02   | TITLE02O     |
| CURTIMEI     | X(8)   | CURTIME   | CURTIMEO     |
| PAGENOI      | X(3)   | PAGENO    | PAGENOO      |
| TRTYPEI      | X(2)   | TRTYPE    | TRTYPEO      |
| TRDESCI      | X(50)  | TRDESC    | TRDESCO      |
| TRTSEL1I     | X(1)   | TRTSEL1   | TRTSEL1O     |
| TRTTYP1I     | X(2)   | TRTTYP1   | TRTTYP1O     |
| TRTYPD1I     | X(50)  | TRTYPD1   | TRTYPD1O     |
| TRTSEL2I ... | ...    | ...       | ...          |
| (rows 2-7 follow same pattern as row 1) |   |  |              |
| TRTSELAI     | X(1)   | TRTSELA   | TRTSELAO     |
| TRTTYPAI     | X(2)   | TRTTYPA   | TRTTYPAO     |
| TRTDSCAI     | X(50)  | TRTDSCA   | TRTDSCAO     |
| INFOMSGI     | X(45)  | INFOMSG   | INFOMSGO     |
| ERRMSGI      | X(78)  | ERRMSG    | ERRMSGO      |
| BUTNF02I     | X(7)   | BUTNF02   | BUTNF02O     |
| BUTNF03I     | X(7)   | BUTNF03   | BUTNF03O     |
| BUTNF07I     | X(10)  | BUTNF07   | BUTNF07O     |
| BUTNF08I     | X(10)  | BUTNF08   | BUTNF08O     |
| BUTNF10I     | X(8)   | BUTNF10   | BUTNF10O     |

---

## Navigation — PF Key Assignments

| Key        | Action                                                                        |
|------------|-------------------------------------------------------------------------------|
| ENTER      | Submit screen; if D/U selected: highlight row and show action prompt; if filters changed: apply new filters |
| F2         | Transfer control to COTRTUPC (Transaction Type add/edit screen, CTTU)        |
| F3         | Exit to calling program (Admin Menu CA00 or other invoker)                   |
| F7         | Page Up: display previous page (if not already on first page)                |
| F8         | Page Down: display next page (if more records exist)                         |
| F10        | Confirm action: execute the pending DELETE or UPDATE for the marked row      |
| CLEAR/PA1/PA2 | Treated as invalid; program resets to ENTER behavior                      |

**Note:** F2, F3, F7, F8, F10 are the only valid PFK values in COTRTLIC (lines 575-582). Any other key is remapped to ENTER.

---

## Data Flow

### Screen to Program

1. CICS RECEIVE MAP fills CTRTLIAI in working storage.
2. `1100-RECEIVE-SCREEN` moves individual fields:
   - `TRTYPEI` → `WS-IN-TYPE-CD` (type code filter)
   - `TRDESCI` → `WS-IN-TYPE-DESC` (description filter)
   - For rows 1-7: `TRTSELI(i)` → `WS-EDIT-SELECT(i)`, `TRTTYPI(i)` → `WS-ROW-TR-CODE-IN(i)`, `TRTYPDI(i)` → `WS-ROW-TR-DESC-IN(i)` (with TRIM and asterisk handling)
3. `1200-EDIT-INPUTS` validates filters and selection array.

### Program to Screen

1. `2100-SCREEN-INIT` clears CTRTLIAO; populates header fields (date, time, tranid, pgmname, titles, page number).
2. `2200-SETUP-ARRAY-ATTRIBS` sets attribute bytes for each of 7 rows based on selection state, error state, and data state.
3. `2300-SCREEN-ARRAY-INIT` moves type codes and descriptions from `WS-CA-EACH-ROW-OUT` to `TRTTYPO(i)` and `TRTYPDO(i)`.
4. `2400-SETUP-SCREEN-ATTRS` sets attributes and values for filter fields (TRTYPEO, TRDESCO).
5. `2500-SETUP-MESSAGE` determines INFOMSG and ERRMSG content.
6. `2600-SEND-SCREEN` executes CICS SEND MAP.

### Commarea Flow

COTRTLIC uses a combined commarea (CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA) packed into WS-COMMAREA (PIC X(2000)) passed on CICS RETURN. On re-entry, the commarea is unpacked from DFHCOMMAREA. The program state, paging keys, filter values, and row data are all carried across the pseudo-conversational loop.

---

## Dynamic Attribute Management

The program overrides BMS-defined field attributes at runtime (paragraph 2200-SETUP-ARRAY-ATTRIBS, lines 1329-1373):

### Select Column (TRTSELn)
| Condition                                                  | Attribute Set      | Color Set |
|------------------------------------------------------------|--------------------|-----------|
| Row data is LOW-VALUES (empty row)                         | DFHBMPRO (protect) | (default) |
| FLG-PROTECT-SELECT-ROWS-YES (filter error)                 | DFHBMPRO (protect) | (default) |
| Row has selection error (WS-ROW-TRTSELECT-ERROR = '1')     | DFHRED on color    | RED       |
| D-selected + 1 valid action + no bad actions               | DFHBMFSE (unprotect)| (default)|
| U-selected + 1 valid action + no bad actions               | DFHBMFSE (unprotect)| (default)|
| Otherwise                                                  | DFHBMFSE           | (default) |

### Type Code Column (TRTTYPn)
| Condition                                                  | Color Set          |
|------------------------------------------------------------|--------------------|
| D-selected + 1 valid action + no bad actions               | DFHNEUTR (neutral) |
| U-selected + 1 valid action + no bad actions               | DFHNEUTR (neutral) |

### Description Column (TRTYPDn)
| Condition                                                  | Attribute Set      | Color Set |
|------------------------------------------------------------|--------------------|-----------|
| D-selected: mark row                                       | DFHNEUTR           | (neutral) |
| U-selected + update completed                              | DFHNEUTR + cursor position away | neutral |
| U-selected + NOT completed                                 | DFHBMFSE (unprotect); cursor here | (default)|
| U-selected + description invalid                           | DFHRED             | RED       |

---

## Related Screens

| Screen     | Mapset   | Program  | Transaction | Relationship                                    |
|------------|----------|----------|-------------|--------------------------------------------------|
| CTRTUPA    | COTRTUP  | COTRTUPC | CTTU        | Add/edit screen reached via F2 from this screen  |
| COADM1A    | COADM01  | COADM01C | CA00        | Admin menu; this screen is option 5; F3 returns here |

---

## Information Messages (INFOMSG, row 21)

Messages are set by `2500-SETUP-MESSAGE` and center-justified by COTRTLIC before display:

| Condition                                  | Message                                          |
|--------------------------------------------|--------------------------------------------------|
| FLG-DELETED-YES                            | 'HIGHLIGHTED row deleted.Hit Enter to continue'  |
| FLG-UPDATE-COMPLETED                       | 'HIGHLIGHTED row was updated'                    |
| D-selected + 1 action + ENTER              | 'Delete HIGHLIGHTED row ? Press F10 to confirm'  |
| U-selected + 1 action + ENTER              | 'Update HIGHLIGHTED row. Press F10 to save'      |
| PF7 on first page                          | 'No previous pages to display' (in ERRMSG)       |
| PF8 with no more records (last pg shown)   | 'No more pages to display' (in ERRMSG)           |
| PF8 with no more records (first encounter) | 'Type U to update, D to delete any record'       |
| Records available to act on                | 'Type U to update, D to delete any record'       |

---

## Error Messages (ERRMSG, row 23)

Messages are placed in WS-RETURN-MSG by COTRTLIC and moved to ERRMSGO:

| Condition                          | Message                                           |
|------------------------------------|---------------------------------------------------|
| Non-numeric type code filter       | 'TYPE CODE FILTER,IF SUPPLIED MUST BE A 2 DIGIT NUMBER' |
| No records for filter conditions   | 'No Records found for these filter conditions'    |
| More than 1 action selected        | 'Please select only 1 action'                     |
| Invalid action code                | 'Action code selected is invalid'                 |
| No changes detected on U row       | 'No change detected with respect to database values.' |
| Update: record not found           | 'Record not found. Deleted by others ?...'        |
| Update: deadlock                   | 'Deadlock. Someone else updating ?...'            |
| Delete: FK violation               | 'Please delete associated child records first:...'|
| DB2 connectivity failure           | 'Db2 access failure. SQLCODE:...' (via DSNTIAC)   |
