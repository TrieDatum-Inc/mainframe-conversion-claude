# COSGN00 — Login Screen Technical Specification

## 1. Screen Overview

**Purpose:** The CardDemo application entry point. Presents a sign-on form where an operator enters their User ID and Password. Successful authentication routes the user to either the Main Menu (COMEN01) for regular users or the Admin Menu (COADM01) for administrators.

**Driving Program:** COSGN00C (CICS transaction entry point for the application sign-on flow)

**Source File:** `/app/bms/COSGN00.bms`
**Copybook:** `/app/cpy-bms/COSGN00.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value                |
|--------------|----------------------|
| MAPSET name  | COSGN00              |
| MAP name     | COSGN0A              |
| SIZE         | (24, 80)             |
| COLUMN       | 1                    |
| LINE         | 1                    |
| CTRL         | ALARM, FREEKB        |
| EXTATT       | YES                  |
| LANG         | COBOL                |
| MODE         | INOUT                |
| STORAGE      | AUTO                 |
| TIOAPFX      | YES                  |
| TYPE         | &&SYSPARM            |

**CTRL=ALARM,FREEKB:** The terminal bell sounds on each send, and the keyboard is unlocked automatically after the send completes (the operator does not need to press RESET).

**TIOAPFX=YES:** A 12-byte TIOA prefix is prepended to the symbolic map; programs must account for this prefix when computing map offsets.

---

## 3. Screen Layout (ASCII Representation)

```
Col:  1         2         3         4         5         6         7         8
      12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row1: Tran :[TRNM]            [--------TITLE01---------]    Date :[CURDATE-]
Row2: Prog :[PGMNAME]         [--------TITLE02---------]    Time :[CURTIME--]
Row3: AppID:[APPLID  ]                                       SysID:[SYSID   ]
Row4:
Row5:      This is a Credit Card Demo Application for Mainframe Modernization
Row6:
Row7:                     +========================================+
Row8:                     |%%%%%%%  NATIONAL RESERVE NOTE  %%%%%%%%|
Row9:                     |%(1)  THE UNITED STATES OF KICSLAND (1)%|
Row10:                    |%$$              ___       ********  $$%|
Row11:                    |%$    {x}       (o o)                 $%|
Row12:                    |%$     ******  (  V  )      O N E     $%|
Row13:                    |%(1)          ---m-m---             (1)%|
Row14:                    |%%~~~~~~~~~~~ ONE DOLLAR ~~~~~~~~~~~~~%%|
Row15:                    +========================================+
Row16:
Row17:               Type your User ID and Password, then press ENTER:
Row18:
Row19:             User ID     :[USERID  ] (8 Char)
Row20:             Password    :[PASSWD  ] (8 Char)
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Sign-on  F3=Exit
```

---

## 4. Field Definitions

### Header Fields (rows 1–3)

| Field Name | Row | Col | Length | ATTRB           | Color    | I/O | Notes                                   |
|------------|-----|-----|--------|-----------------|----------|-----|-----------------------------------------|
| (label)    | 1   | 1   | 6      | ASKIP,NORM      | BLUE     | O   | Static literal `Tran :`                 |
| TRNNAME    | 1   | 8   | 4      | ASKIP,FSET,NORM | BLUE     | O   | Current CICS transaction ID; output-only after initial send |
| TITLE01    | 1   | 21  | 40     | ASKIP,FSET,NORM | YELLOW   | O   | Application title line 1                |
| (label)    | 1   | 64  | 6      | ASKIP,NORM      | BLUE     | O   | Static literal `Date :`                 |
| CURDATE    | 1   | 71  | 8      | ASKIP,FSET,NORM | BLUE     | O   | Current date; initial value `mm/dd/yy`  |
| (label)    | 2   | 1   | 6      | ASKIP,NORM      | BLUE     | O   | Static literal `Prog :`                 |
| PGMNAME    | 2   | 8   | 8      | FSET,NORM,PROT  | BLUE     | O   | Current program name; PROT (protected)  |
| TITLE02    | 2   | 21  | 40     | ASKIP,FSET,NORM | YELLOW   | O   | Application title line 2                |
| (label)    | 2   | 64  | 6      | ASKIP,NORM      | BLUE     | O   | Static literal `Time :`                 |
| CURTIME    | 2   | 71  | 9      | FSET,NORM,PROT  | BLUE     | O   | Current time; initial value `Ahh:mm:ss` |
| (label)    | 3   | 1   | 6      | FSET,NORM,PROT  | BLUE     | O   | Static literal `AppID:`                 |
| APPLID     | 3   | 8   | 8      | FSET,NORM,PROT  | BLUE     | O   | CICS Application ID                     |
| (label)    | 3   | 64  | 6      | ASKIP,NORM      | BLUE     | O   | Static literal `SysID:`                 |
| SYSID      | 3   | 71  | 8      | FSET,NORM,PROT  | BLUE     | O   | CICS system ID; initial value spaces    |

### Decorative Area (rows 5–15)

| Row | Col | Length | Content                                      | Color    |
|-----|-----|--------|----------------------------------------------|----------|
| 5   | 6   | 66     | `This is a Credit Card Demo Application...` | NEUTRAL  |
| 7   | 21  | 42     | `+========================================+` | BLUE     |
| 8   | 21  | 42     | `|%%%%%%%  NATIONAL RESERVE NOTE  %%%%%%%%|` | BLUE     |
| 9   | 21  | 42     | `|%(1)  THE UNITED STATES OF KICSLAND (1)%|` | BLUE     |
| 10  | 21  | 42     | `|%$$              ___       ********  $$%|` | BLUE     |
| 11  | 21  | 42     | `|%$    {x}       (o o)                 $%|` | BLUE     |
| 12  | 21  | 42     | `|%$     ******  (  V  )      O N E     $%|` | BLUE     |
| 13  | 21  | 42     | `|%(1)          ---m-m---             (1)%|` | BLUE     |
| 14  | 21  | 42     | `|%%~~~~~~~~~~~ ONE DOLLAR ~~~~~~~~~~~~~%%|` | BLUE     |
| 15  | 21  | 42     | `+========================================+` | BLUE     |

All decorative fields: ATTRB=(ASKIP,NORM), output-only, no symbolic map name.

### Instruction Line (row 17)

| Row | Col | Length | Content                                               | Color     |
|-----|-----|--------|-------------------------------------------------------|-----------|
| 17  | 16  | 49     | `Type your User ID and Password, then press ENTER:` | TURQUOISE |

ATTRB=(ASKIP,NORM), output-only, no symbolic name.

### Input Fields (rows 19–20)

| Field Name | Row | Col | Length | ATTRB                  | Color | Hilight | I/O   | Notes                                         |
|------------|-----|-----|--------|------------------------|-------|---------|-------|-----------------------------------------------|
| (label)    | 19  | 29  | 13     | ASKIP,NORM             | TURQUOISE | —   | O     | Static literal `User ID     :`                |
| USERID     | 19  | 43  | 8      | FSET,IC,NORM,UNPROT    | GREEN | OFF     | Input | Cursor initial position (IC); 8 alphanumeric  |
| (stopper)  | 19  | 52  | 0      | ASKIP,NORM             | GREEN | —       | —     | Zero-length field stops cursor tab             |
| (hint)     | 19  | 52  | 8      | ASKIP,NORM             | BLUE  | —       | O     | Literal `(8 Char)`                            |
| (label)    | 20  | 29  | 13     | ASKIP,NORM             | TURQUOISE | —   | O     | Static literal `Password    :`                |
| PASSWD     | 20  | 43  | 8      | DRK,FSET,UNPROT        | GREEN | OFF     | Input | DRK: characters typed are not displayed; initial `________` |
| (stopper)  | 20  | 52  | 0      | ASKIP,NORM             | GREEN | —       | —     | Zero-length field stops cursor tab             |
| (hint)     | 20  | 52  | 8      | ASKIP,NORM             | BLUE  | —       | O     | Literal `(8 Char)`                            |
| (pad)      | 20  | 61  | 1      | DRK,UNPROT             | —     | —       | —     | Dark padding field; initial space; absorbs overflow |
| (stopper)  | 20  | 63  | 0      | ASKIP,NORM             | —     | —       | —     | Tab stop after password group                  |

**USERID notes:** FSET causes the field to be transmitted to the program even if the operator does not modify it. IC sets the initial cursor position here on first display.

**PASSWD notes:** DRK suppresses display of typed characters (password masking). FSET forces transmission. The initial value `________` provides visual cue to field width but is not a default password value—the program reads PASSWDI from the symbolic map input area.

### Message Line (row 23)

| Field Name | Row | Col | Length | ATTRB          | Color | I/O | Notes                              |
|------------|-----|-----|--------|----------------|-------|-----|------------------------------------|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED   | O   | Error/status message; BRT=high intensity |

### Function Key Legend (row 24)

| Row | Col | Length | Content                  | Color  |
|-----|-----|--------|--------------------------|--------|
| 24  | 1   | 22     | `ENTER=Sign-on  F3=Exit` | YELLOW |

ATTRB=(ASKIP,NORM), output-only, no symbolic name.

---

## 5. Generated Copybook Structure (COSGN00.CPY)

The BMS assembler generates two 01-level structures under the mapset:

### Input Structure: COSGN0AI

Each named field produces three sub-fields in the input structure:
- `fieldL` — COMP PIC S9(4): actual length of data received from terminal (0 if field not modified)
- `fieldF`/`fieldA` (REDEFINES): attribute byte as received
- `fieldI` — PIC X(n): the actual character data

| Input Field  | COBOL Name   | PIC         | Notes                           |
|--------------|--------------|-------------|---------------------------------|
| TRNNAME      | TRNNAMEI     | PIC X(4)    | Transaction name                |
| TITLE01      | TITLE01I     | PIC X(40)   | Title line 1                    |
| CURDATE      | CURDATEI     | PIC X(8)    | Current date                    |
| PGMNAME      | PGMNAMEI     | PIC X(8)    | Program name                    |
| TITLE02      | TITLE02I     | PIC X(40)   | Title line 2                    |
| CURTIME      | CURTIMEI     | PIC X(9)    | Current time                    |
| APPLID       | APPLIDI      | PIC X(8)    | Application ID                  |
| SYSID        | SYSIDI       | PIC X(8)    | System ID                       |
| USERID       | USERIDI      | PIC X(8)    | User ID entered by operator      |
| PASSWD       | PASSWDI      | PIC X(8)    | Password entered (masked on screen) |
| ERRMSG       | ERRMSGI      | PIC X(78)   | Error message area              |

### Output Structure: COSGN0AO (REDEFINES COSGN0AI)

Each named field produces four sub-fields in the output structure:
- `fieldC` — color attribute
- `fieldP` — PS (programmatic symbol set)
- `fieldH` — highlight attribute
- `fieldV` — validation attribute
- `fieldO` — PIC X(n): data to be sent to terminal

The program populates the `O` fields to send data and the `C`/`H` fields to dynamically change colors or highlighting (e.g., turning ERRMSG red).

---

## 6. Screen Navigation

| Key      | Action                                                                          |
|----------|---------------------------------------------------------------------------------|
| ENTER    | Submits User ID and Password; program validates credentials and routes to menu  |
| PF3      | Exits the application (CICS RETURN with no transaction)                        |
| PF1–PF24 | Not defined in this map; behavior depends on program handling of EIBAID        |

**Navigation flow:** COSGN00 is the application entry point. A successful login navigates to:
- COMEN01 (Main Menu) for user-type accounts
- COADM01 (Admin Menu) for administrator accounts

---

## 7. Validation Rules

Validation logic resides in COSGN00C, not in the BMS map itself. The BMS provides the following structural constraints:

| Field  | BMS Constraint                       | Program-Level Validation                            |
|--------|--------------------------------------|-----------------------------------------------------|
| USERID | Length=8, UNPROT, NORM               | Must be non-blank; looked up in user file/table     |
| PASSWD | Length=8, UNPROT, DRK                | Must match stored password for given USERID         |

**No VALIDN= clauses** are present in COSGN00.bms (the DFHMDI does not specify DSATTS or MAPATTS with VALIDN), so all field-level validation is performed by the driving program.

**Error display:** On invalid credentials, the program MOVEs an error string to ERRMSGO and re-sends the map. ERRMSG has ATTRB=(ASKIP,BRT,FSET), ensuring the message always appears in bright red and is retransmitted.

---

## 8. Related Screens

| Screen  | Mapset  | Relationship                                               |
|---------|---------|------------------------------------------------------------|
| COMEN01 | COMEN01 | Navigate TO on successful login as regular user            |
| COADM01 | COADM01 | Navigate TO on successful login as administrator           |

COSGN00 has no predecessor screen; it is the application root.
