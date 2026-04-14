# COMEN01 — Main Menu Screen Technical Specification

## 1. Screen Overview

**Purpose:** The primary navigation hub for regular (non-administrator) CardDemo users. Displays up to 12 dynamically populated menu option lines. The operator types an option number and presses ENTER to navigate to the corresponding function.

**Driving Program:** COMEN01C

**Source File:** `/app/bms/COMEN01.bms`
**Copybook:** `/app/cpy-bms/COMEN01.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COMEN01           |
| MAP name     | COMEN1A           |
| SIZE         | (24, 80)          |
| COLUMN       | 1                 |
| LINE         | 1                 |
| CTRL         | ALARM, FREEKB     |
| EXTATT       | YES               |
| LANG         | COBOL             |
| MODE         | INOUT             |
| STORAGE      | AUTO              |
| TIOAPFX      | YES               |
| TYPE         | &&SYSPARM         |

**CTRL=ALARM,FREEKB:** Bell sounds on each map send; keyboard auto-unlocked after send.

---

## 3. Screen Layout (ASCII Representation)

```
Col:  1         2         3         4         5         6         7         8
      12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row1: Tran:[TRNM]          [----------TITLE01----------]     Date:[CURDATE-]
Row2: Prog:[PGMNAME]       [----------TITLE02----------]     Time:[CURTIME-]
Row3:
Row4:                                  Main Menu
Row5:
Row6:                    [-------------OPTN001-------------]
Row7:                    [-------------OPTN002-------------]
Row8:                    [-------------OPTN003-------------]
Row9:                    [-------------OPTN004-------------]
Row10:                   [-------------OPTN005-------------]
Row11:                   [-------------OPTN006-------------]
Row12:                   [-------------OPTN007-------------]
Row13:                   [-------------OPTN008-------------]
Row14:                   [-------------OPTN009-------------]
Row15:                   [-------------OPTN010-------------]
Row16:                   [-------------OPTN011-------------]
Row17:                   [-------------OPTN012-------------]
Row18:
Row19:
Row20:               Please select an option : [OPT]
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Continue  F3=Exit
```

---

## 4. Field Definitions

### Header Fields (rows 1–2)

| Field Name | Row | Col | Length | ATTRB           | Color  | I/O | Notes                          |
|------------|-----|-----|--------|-----------------|--------|-----|--------------------------------|
| (label)    | 1   | 1   | 5      | ASKIP,NORM      | BLUE   | O   | Static literal `Tran:`         |
| TRNNAME    | 1   | 7   | 4      | ASKIP,FSET,NORM | BLUE   | O   | Active CICS transaction name   |
| TITLE01    | 1   | 21  | 40     | ASKIP,FSET,NORM | YELLOW | O   | Application title line 1       |
| (label)    | 1   | 65  | 5      | ASKIP,NORM      | BLUE   | O   | Static literal `Date:`         |
| CURDATE    | 1   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current date; init `mm/dd/yy`  |
| (label)    | 2   | 1   | 5      | ASKIP,NORM      | BLUE   | O   | Static literal `Prog:`         |
| PGMNAME    | 2   | 7   | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current program name           |
| TITLE02    | 2   | 21  | 40     | ASKIP,FSET,NORM | YELLOW | O   | Application title line 2       |
| (label)    | 2   | 65  | 5      | ASKIP,NORM      | BLUE   | O   | Static literal `Time:`         |
| CURTIME    | 2   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current time; init `hh:mm:ss`  |

### Screen Title (row 4)

| Row | Col | Length | Content     | ATTRB      | Color   |
|-----|-----|--------|-------------|------------|---------|
| 4   | 35  | 9      | `Main Menu` | ASKIP,BRT  | NEUTRAL |

### Menu Options (rows 6–17)

All 12 option fields share identical BMS attributes:

| Field Name | Row | Col | Length | ATTRB           | Color | I/O | Notes                                        |
|------------|-----|-----|--------|-----------------|-------|-----|----------------------------------------------|
| OPTN001    | 6   | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 1 text; initial single space       |
| OPTN002    | 7   | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 2 text                             |
| OPTN003    | 8   | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 3 text                             |
| OPTN004    | 9   | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 4 text                             |
| OPTN005    | 10  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 5 text                             |
| OPTN006    | 11  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 6 text                             |
| OPTN007    | 12  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 7 text                             |
| OPTN008    | 13  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 8 text                             |
| OPTN009    | 14  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 9 text                             |
| OPTN010    | 15  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 10 text                            |
| OPTN011    | 16  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 11 text                            |
| OPTN012    | 17  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Menu item 12 text                            |

**Design note:** All option fields use ASKIP (auto-skip), making them output-only at the BMS level. The program populates them dynamically with menu item text before sending the map. FSET causes their current content to be retransmitted on the next RECEIVE MAP even if unchanged.

### Selection Input (row 20)

| Field Name | Row | Col | Length | ATTRB                     | Color     | Hilight   | Other                   | I/O   | Notes                         |
|------------|-----|-----|--------|---------------------------|-----------|-----------|-------------------------|-------|-------------------------------|
| (prompt)   | 20  | 15  | 25     | ASKIP,BRT                 | TURQUOISE | —         | —                       | O     | `Please select an option :`   |
| OPTION     | 20  | 41  | 2      | FSET,IC,NORM,NUM,UNPROT   | —         | UNDERLINE | JUSTIFY=(RIGHT,ZERO)    | Input | Numeric; right-justified with leading zero fill; cursor here on display |
| (stopper)  | 20  | 44  | 0      | ASKIP,NORM                | GREEN     | —         | —                       | —     | Tab-stop after OPTION field   |

**OPTION field notes:**
- NUM attribute restricts input to digits 0–9 and minus/period (terminal hardware validation)
- JUSTIFY=(RIGHT,ZERO) right-aligns and zero-fills the entered value
- IC positions the cursor at this field on each map send
- Length=2 supports option numbers 01–99

### Message Line (row 23)

| Field Name | Row | Col | Length | ATTRB          | Color | I/O | Notes                     |
|------------|-----|-----|--------|----------------|-------|-----|---------------------------|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED   | O   | Error/status messages     |

### Function Key Legend (row 24)

| Row | Col | Length | Content                   | Color  |
|-----|-----|--------|---------------------------|--------|
| 24  | 1   | 23     | `ENTER=Continue  F3=Exit` | YELLOW |

---

## 5. Generated Copybook Structure (COMEN01.CPY)

### Input Structure: COMEN1AI

| Input Field | COBOL Name  | PIC       | Notes                                       |
|-------------|-------------|-----------|---------------------------------------------|
| TRNNAME     | TRNNAMEI    | PIC X(4)  | Transaction ID                              |
| TITLE01     | TITLE01I    | PIC X(40) | Title line 1                                |
| CURDATE     | CURDATEI    | PIC X(8)  | Date                                        |
| PGMNAME     | PGMNAMEI    | PIC X(8)  | Program name                                |
| TITLE02     | TITLE02I    | PIC X(40) | Title line 2                                |
| CURTIME     | CURTIMEI    | PIC X(8)  | Time                                        |
| OPTN001–012 | OPTN001I–   | PIC X(40) | Menu option text (12 fields)                |
| OPTION      | OPTIONI     | PIC X(2)  | Operator's menu selection; read on RECEIVE  |
| ERRMSG      | ERRMSGI     | PIC X(78) | Error message                               |

### Output Structure: COMEN1AO (REDEFINES COMEN1AI)

Each field produces C (color), P (PS), H (highlight), V (validation), O (data) sub-fields.
The program uses `OPTN001O` through `OPTN012O` to load menu text before sending the map.

---

## 6. Screen Navigation

| Key   | Action                                                                         |
|-------|--------------------------------------------------------------------------------|
| ENTER | Reads OPTION field; routes to the corresponding sub-function screen            |
| PF3   | Returns to login screen (COSGN00) or exits the application                     |

**Option routing** (resolved at program level, not BMS level — requires COMEN01C source to confirm exact mapping):
The program evaluates OPTIONI and issues CICS XCTL or LINK to the appropriate program based on the numeric selection.

---

## 7. Validation Rules

| Field  | BMS Constraint                       | Program-Level Validation                            |
|--------|--------------------------------------|-----------------------------------------------------|
| OPTION | Length=2, NUM, UNPROT                | Must be within the range of displayed menu items    |

No VALIDN= directives are present on COMEN1A. All range and existence checking is performed by COMEN01C.

---

## 8. Related Screens

| Screen  | Mapset  | Relationship                                            |
|---------|---------|---------------------------------------------------------|
| COSGN00 | COSGN00 | Navigate FROM (login sends regular user here)           |
| COADM01 | COADM01 | Parallel admin menu (administrator users bypass here)   |
| COBIL00 | COBIL00 | Navigate TO (bill payment option)                       |
| COTRN00 | COTRN00 | Navigate TO (transaction list option)                   |
| COTRN01 | COTRN01 | Navigate TO (transaction view/add option)               |
| COACTVW | COACTVW | Navigate TO (account view option)                       |
| COCRDSL | COCRDSL | Navigate TO (card detail selection option)              |
| CORPT00 | CORPT00 | Navigate TO (transaction reports option)                |
