# COADM01 — Admin Menu Screen Technical Specification

## 1. Screen Overview

**Purpose:** The primary navigation hub for CardDemo administrator users. Structurally identical to the Main Menu (COMEN01) but populated with administrator-specific function options. Displays up to 12 dynamically loaded menu entries. The operator selects an option number and presses ENTER.

**Driving Program:** COADM01C

**Source File:** `/app/bms/COADM01.bms`
**Copybook:** `/app/cpy-bms/COADM01.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COADM01           |
| MAP name     | COADM1A           |
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

**Design note:** The BMS source for COADM01 is structurally identical to COMEN01 except for:
- The screen title at row 4 reads `Admin Menu` (10 chars) instead of `Main Menu` (9 chars)
- The mapset/map names differ (COADM01/COADM1A vs COMEN01/COMEN1A)
- The version timestamp is one second earlier (17:02:42 vs 17:02:43)

---

## 3. Screen Layout (ASCII Representation)

```
Col:  1         2         3         4         5         6         7         8
      12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row1: Tran:[TRNM]          [----------TITLE01----------]     Date:[CURDATE-]
Row2: Prog:[PGMNAME]       [----------TITLE02----------]     Time:[CURTIME-]
Row3:
Row4:                                  Admin Menu
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

| Row | Col | Length | Content      | ATTRB     | Color   |
|-----|-----|--------|--------------|-----------|---------|
| 4   | 35  | 10     | `Admin Menu` | ASKIP,BRT | NEUTRAL |

### Menu Options (rows 6–17)

| Field Name | Row | Col | Length | ATTRB           | Color | I/O | Notes               |
|------------|-----|-----|--------|-----------------|-------|-----|---------------------|
| OPTN001    | 6   | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 1   |
| OPTN002    | 7   | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 2   |
| OPTN003    | 8   | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 3   |
| OPTN004    | 9   | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 4   |
| OPTN005    | 10  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 5   |
| OPTN006    | 11  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 6   |
| OPTN007    | 12  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 7   |
| OPTN008    | 13  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 8   |
| OPTN009    | 14  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 9   |
| OPTN010    | 15  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 10  |
| OPTN011    | 16  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 11  |
| OPTN012    | 17  | 20  | 40     | ASKIP,FSET,NORM | BLUE  | O   | Admin menu item 12  |

All option fields are ASKIP (output-only at BMS level). The driving program populates them before each SEND MAP.

### Selection Input (row 20)

| Field Name | Row | Col | Length | ATTRB                   | Color     | Hilight   | Other                | I/O   | Notes                                 |
|------------|-----|-----|--------|-------------------------|-----------|-----------|----------------------|-------|---------------------------------------|
| (prompt)   | 20  | 15  | 25     | ASKIP,BRT               | TURQUOISE | —         | —                    | O     | `Please select an option :`           |
| OPTION     | 20  | 41  | 2      | FSET,IC,NORM,NUM,UNPROT | —         | UNDERLINE | JUSTIFY=(RIGHT,ZERO) | Input | Numeric 2-digit option selector; IC   |
| (stopper)  | 20  | 44  | 0      | ASKIP,NORM              | GREEN     | —         | —                    | —     | Zero-length tab stop                  |

### Message Line (row 23)

| Field Name | Row | Col | Length | ATTRB          | Color | I/O |
|------------|-----|-----|--------|----------------|-------|-----|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED   | O   |

### Function Key Legend (row 24)

| Row | Col | Length | Content                   | Color  |
|-----|-----|--------|---------------------------|--------|
| 24  | 1   | 23     | `ENTER=Continue  F3=Exit` | YELLOW |

---

## 5. Generated Copybook Structure (COADM01.CPY)

The generated structure mirrors COMEN01.CPY exactly in layout, substituting the mapset/map prefix `COADM1A`:

### Input Structure: COADM1AI

| Input Field | COBOL Name  | PIC       | Notes                  |
|-------------|-------------|-----------|------------------------|
| TRNNAME     | TRNNAMEI    | PIC X(4)  | Transaction ID         |
| TITLE01     | TITLE01I    | PIC X(40) | Title line 1           |
| CURDATE     | CURDATEI    | PIC X(8)  | Date                   |
| PGMNAME     | PGMNAMEI    | PIC X(8)  | Program name           |
| TITLE02     | TITLE02I    | PIC X(40) | Title line 2           |
| CURTIME     | CURTIMEI    | PIC X(8)  | Time                   |
| OPTN001–012 | OPTN001I–   | PIC X(40) | 12 menu option fields  |
| OPTION      | OPTIONI     | PIC X(2)  | Operator selection     |
| ERRMSG      | ERRMSGI     | PIC X(78) | Error message          |

### Output Structure: COADM1AO (REDEFINES COADM1AI)

Same layout as input; each field provides C/P/H/V attribute bytes and O data field.

---

## 6. Screen Navigation

| Key   | Action                                                                           |
|-------|----------------------------------------------------------------------------------|
| ENTER | Reads OPTION field; routes to corresponding admin function                       |
| PF3   | Returns to login screen or exits application                                     |

**Known admin-accessible screens** (routing resolved in COADM01C — requires program source to confirm all options):
- COUSR00 (List Users)
- COUSR01 (Add User)
- COUSR02 (Update User)
- COUSR03 (Delete User)

---

## 7. Validation Rules

| Field  | BMS Constraint          | Program-Level Validation                         |
|--------|-------------------------|--------------------------------------------------|
| OPTION | Length=2, NUM, UNPROT   | Must be within range of displayed admin options  |

No VALIDN= directives are specified. All validation is in COADM01C.

---

## 8. Related Screens

| Screen  | Mapset  | Relationship                                         |
|---------|---------|------------------------------------------------------|
| COSGN00 | COSGN00 | Navigate FROM (login sends admin users here)         |
| COUSR00 | COUSR00 | Navigate TO (user list management)                   |
| COUSR01 | COUSR01 | Navigate TO (add user)                               |
| COUSR02 | COUSR02 | Navigate TO (update user)                            |
| COUSR03 | COUSR03 | Navigate TO (delete user)                            |
| COMEN01 | COMEN01 | Parallel menu for regular users                      |
