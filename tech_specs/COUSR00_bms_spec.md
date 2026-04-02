# Technical Specification: COUSR00 BMS Mapset — User List Screen

## 1. Executive Summary

COUSR00 is a BMS (Basic Mapping Support) mapset that defines the terminal screen layout for the CardDemo user listing function. It renders a paginated tabular list of up to 10 user records with selection columns for triggering update or delete operations. The mapset is consumed by program COUSR00C (transaction CU00).

---

## 2. Artifact Identification

| Attribute         | Value                              |
|------------------|------------------------------------|
| Mapset Name      | COUSR00                            |
| Source File      | app/bms/COUSR00.bms                |
| Map Name         | COUSR0A                            |
| Generated Copybook | app/cpy-bms/COUSR00.CPY          |
| Consuming Program | COUSR00C                          |
| Transaction ID   | CU00                               |
| Screen Size      | 24 rows x 80 columns               |
| Version Tag      | CardDemo_v1.0-70-g193b394-123, 2022-08-22 |

---

## 3. Mapset-Level Attributes (DFHMSD — line 19)

| Attribute   | Value        | Meaning                                      |
|-------------|--------------|----------------------------------------------|
| CTRL        | ALARM,FREEKB | Sound alarm on send; free keyboard after send |
| EXTATT      | YES          | Extended attributes supported (color, highlight) |
| LANG        | COBOL        | Generated copybook is in COBOL format         |
| MODE        | INOUT        | Map can be used for both input and output     |
| STORAGE     | AUTO         | TIOA storage managed automatically           |
| TIOAPFX     | YES          | Include TIOA prefix in generated structures  |
| TYPE        | &&SYSPARM    | Resolved at assembly time (MAP or DSECT)     |

---

## 4. Map Definition — COUSR0A (DFHMDI — line 26)

| Attribute | Value    | Meaning                     |
|-----------|----------|-----------------------------|
| COLUMN    | 1        | Map starts at column 1      |
| LINE      | 1        | Map starts at row 1         |
| SIZE      | (24,80)  | Full 24x80 3270 screen      |

---

## 5. Screen Layout

```
Col:  1         2         3         4         5         6         7         8
      0123456789012345678901234567890123456789012345678901234567890123456789012345678901
Row:
 1   Tran:[TRNNAME ]        [         TITLE01          ]        Date:[CURDATE ]
 2   Prog:[PGMNAME ]        [         TITLE02          ]        Time:[CURTIME ]
 3   (blank)
 4                                    List Users                      Page:[PAGENUM]
 5   (blank)
 6       Search User ID:[USRIDIN ]
 7   (blank)
 8       Sel  User ID   [   First Name   ]         [   Last Name    ]  Type
 9       ---  --------  --------------------        --------------------  ----
10      [S][USRID01 ][      FNAME01      ]         [      LNAME01      ] [U01]
11      [S][USRID02 ][      FNAME02      ]         [      LNAME02      ] [U02]
12      [S][USRID03 ][      FNAME03      ]         [      LNAME03      ] [U03]
13      [S][USRID04 ][      FNAME04      ]         [      LNAME04      ] [U04]
14      [S][USRID05 ][      FNAME05      ]         [      LNAME05      ] [U05]
15      [S][USRID06 ][      FNAME06      ]         [      LNAME06      ] [U06]
16      [S][USRID07 ][      FNAME07      ]         [      LNAME07      ] [U07]
17      [S][USRID08 ][      FNAME08      ]         [      LNAME08      ] [U08]
18      [S][USRID09 ][      FNAME09      ]         [      LNAME09      ] [U09]
19      [S][USRID10 ][      FNAME10      ]         [      LNAME10      ] [U10]
20   (blank)
21              Type 'U' to Update or 'D' to Delete a User from the list
22   (blank)
23   [                          ERRMSG                                        ]
24   ENTER=Continue  F3=Back  F7=Backward  F8=Forward
```

Legend: [S] = 1-char selection field (UNPROT), [USRIDnn] = 8-char protected display field, [FNAMEnn]/[LNAMEnn] = 20-char protected display field, [Unn] = 1-char protected user type field.

---

## 6. Field Definitions

### 6.1 Header Fields (Rows 1–2)

| Field Name | BMS Row | Col | Length | Color  | Attributes      | Content / Purpose              |
|-----------|---------|-----|--------|--------|-----------------|--------------------------------|
| (literal) | 1       | 1   | 5      | BLUE   | ASKIP,NORM      | Static label 'Tran:'          |
| TRNNAME   | 1       | 7   | 4      | BLUE   | ASKIP,FSET,NORM | Transaction name (output)     |
| TITLE01   | 1       | 21  | 40     | YELLOW | ASKIP,FSET,NORM | Application title line 1       |
| (literal) | 1       | 65  | 5      | BLUE   | ASKIP,NORM      | Static label 'Date:'          |
| CURDATE   | 1       | 71  | 8      | BLUE   | ASKIP,FSET,NORM | Current date MM/DD/YY         |
| (literal) | 2       | 1   | 5      | BLUE   | ASKIP,NORM      | Static label 'Prog:'          |
| PGMNAME   | 2       | 7   | 8      | BLUE   | ASKIP,FSET,NORM | Program name (output)         |
| TITLE02   | 2       | 21  | 40     | YELLOW | ASKIP,FSET,NORM | Application title line 2       |
| (literal) | 2       | 65  | 5      | BLUE   | ASKIP,NORM      | Static label 'Time:'          |
| CURTIME   | 2       | 71  | 8      | BLUE   | ASKIP,FSET,NORM | Current time HH:MM:SS         |

### 6.2 Title / Page Fields (Row 4)

| Field Name | BMS Row | Col | Length | Color    | Attributes      | Content / Purpose              |
|-----------|---------|-----|--------|----------|-----------------|--------------------------------|
| (literal) | 4       | 35  | 10     | NEUTRAL  | ASKIP,BRT       | Static label 'List Users'     |
| (literal) | 4       | 65  | 5      | TURQUOISE| ASKIP,BRT       | Static label 'Page:'          |
| PAGENUM   | 4       | 71  | 8      | BLUE     | ASKIP,FSET,NORM | Current page number (output)  |

### 6.3 Search Field (Row 6)

| Field Name | BMS Row | Col | Length | Color | Attributes            | Highlight  | Purpose                          |
|-----------|---------|-----|--------|-------|-----------------------|------------|----------------------------------|
| (literal) | 6       | 5   | 15     | TURQ. | ASKIP,NORM            | None       | 'Search User ID:' label          |
| USRIDIN   | 6       | 21  | 8      | GREEN | FSET,NORM,UNPROT      | UNDERLINE  | User ID search anchor (input)    |
| (stopper) | 6       | 30  | 0      | —     | ASKIP,NORM            | —          | Field terminator after USRIDIN   |

USRIDIN is unprotected and underlined — this is the cursor home field. The operator types a starting User ID here to position the browse. Stored in symbolic map as USRIDINI (input) / USRIDINO (output).

### 6.4 Column Header (Rows 8–9)

| BMS Row | Col | Length | Color   | Attributes | Content                         |
|---------|-----|--------|---------|------------|---------------------------------|
| 8       | 5   | 3      | NEUTRAL | ASKIP,NORM | 'Sel'                           |
| 8       | 12  | 8      | NEUTRAL | ASKIP,NORM | 'User ID '                      |
| 8       | 24  | 20     | NEUTRAL | ASKIP,NORM | '     First Name     '          |
| 8       | 48  | 20     | NEUTRAL | ASKIP,NORM | '     Last Name      '          |
| 8       | 72  | 4      | NEUTRAL | ASKIP,NORM | 'Type'                          |
| 9       | 5   | 3      | NEUTRAL | ASKIP,NORM | '---'                           |
| 9       | 12  | 8      | NEUTRAL | ASKIP,NORM | '--------'                      |
| 9       | 24  | 20     | NEUTRAL | ASKIP,NORM | '--------------------'           |
| 9       | 48  | 20     | NEUTRAL | ASKIP,NORM | '--------------------'           |
| 9       | 72  | 4      | NEUTRAL | ASKIP,NORM | '----'                           |

### 6.5 Data Rows (Rows 10–19) — 10 User Rows

Each row follows the identical pattern. Row 10 = slot 01, Row 19 = slot 10:

| Field Name | BMS Row(s) | Col | Length | Color | Attributes            | Highlight  | Symbolic Map Field | Purpose                      |
|-----------|------------|-----|--------|-------|-----------------------|------------|--------------------|------------------------------|
| SEL000n   | 10–19      | 6   | 1      | GREEN | FSET,NORM,UNPROT      | UNDERLINE  | SEL000nI           | Selection code (U or D)      |
| (stopper) | 10–19      | 8   | 0      | —     | ASKIP,NORM            | —          | —                  | Terminator after SEL field   |
| USRIDnn   | 10–19      | 12  | 8      | BLUE  | ASKIP,FSET,NORM       | None       | USRIDnnI           | User ID (protected display)  |
| FNAMEnn   | 10–19      | 24  | 20     | BLUE  | ASKIP,FSET,NORM       | None       | FNAMEnnI           | First name (protected)       |
| LNAMEnn   | 10–19      | 48  | 20     | BLUE  | ASKIP,FSET,NORM       | None       | LNAMEnnI           | Last name (protected)        |
| UTYPEnn   | 10–19      | 73  | 1      | BLUE  | ASKIP,FSET,NORM       | None       | UTYPEnnI           | User type A/U (protected)    |

Where nn = 01 through 10. BMS row mapping:
- SEL0001/USRID01/FNAME01/LNAME01/UTYPE01 → Row 10
- SEL0002/USRID02/FNAME02/LNAME02/UTYPE02 → Row 11
- SEL0003/USRID03/FNAME03/LNAME03/UTYPE03 → Row 12
- SEL0004/USRID04/FNAME04/LNAME04/UTYPE04 → Row 13
- SEL0005/USRID05/FNAME05/LNAME05/UTYPE05 → Row 14
- SEL0006/USRID06/FNAME06/LNAME06/UTYPE06 → Row 15
- SEL0007/USRID07/FNAME07/LNAME07/UTYPE07 → Row 16
- SEL0008/USRID08/FNAME08/LNAME08/UTYPE08 → Row 17
- SEL0009/USRID09/FNAME09/LNAME09/UTYPE09 → Row 18
- SEL0010/USRID10/FNAME10/LNAME10/UTYPE10 → Row 19

### 6.6 Instruction and Status Fields (Rows 21–24)

| Field Name | BMS Row | Col | Length | Color   | Attributes         | Content / Purpose                                           |
|-----------|---------|-----|--------|---------|--------------------|-------------------------------------------------------------|
| (literal) | 21      | 12  | 56     | NEUTRAL | ASKIP,BRT          | "Type 'U' to Update or 'D' to Delete a User from the list" |
| ERRMSG    | 23      | 1   | 78     | RED     | ASKIP,BRT,FSET     | Error/status message area                                   |
| (literal) | 24      | 1   | 48     | YELLOW  | ASKIP,NORM         | 'ENTER=Continue  F3=Back  F7=Backward  F8=Forward'         |

---

## 7. Symbolic Map Structure (COUSR00.CPY — app/cpy-bms/COUSR00.CPY)

The BMS assembler generates two structures that REDEFINE each other:

**COUSR0AI** (Input): For each named field X, the input structure contains:
- XL (COMP PIC S9(4)): Length of data received from terminal (−1 = cursor positioned here on send)
- XF (PICTURE X): Flag byte
- XA (PICTURE X) via FILLER REDEFINES XF: Attribute byte
- FILLER PICTURE X(4): MDT/color/highlight bytes
- XI (PIC X(n)): Actual field data

**COUSR0AO** (Output, REDEFINES COUSR0AI): For each named field X, exposes:
- XC (PICTURE X): Color byte
- XP (PICTURE X): Print/PS byte
- XH (PICTURE X): Highlight byte
- XV (PICTURE X): Video (underscore/blink) byte
- XO (PIC X(n)): Output data

The COUSR00.CPY file covers 10 rows x 5 fields (SEL, USRID, FNAME, LNAME, UTYPE) plus PAGENUM, USRIDIN, ERRMSG, and header fields — approximately 580+ lines.

---

## 8. Attribute Summary Table

| Attribute Code  | Meaning                                           |
|-----------------|---------------------------------------------------|
| ASKIP           | Auto-skip (protected, cursor skips over field)   |
| UNPROT          | Unprotected (operator can type into this field)  |
| FSET            | Field Set (MDT always on; field included in input stream) |
| NORM            | Normal intensity                                 |
| BRT             | Bright (high intensity)                          |
| DRK             | Dark (not visible — not used in this mapset)     |
| HILIGHT=UNDERLINE | Underline attribute for visual indication      |

---

## 9. Field-to-Program Data Mapping

| BMS Field  | Symbolic Input | Symbolic Output | Program Usage (COUSR00C)                            |
|-----------|----------------|-----------------|------------------------------------------------------|
| USRIDIN   | USRIDINI       | USRIDINO        | Search anchor; moved to/from SEC-USR-ID             |
| PAGENUM   | PAGENUMI       | PAGENUMO        | Page number display; moved from CDEMO-CU00-PAGE-NUM |
| SEL000n   | SEL000nI       | —               | Selection code checked (U/D); drives XCTL logic     |
| USRIDnn   | USRIDnnI       | USRIDnnO        | User ID populated from SEC-USR-ID in browse loop    |
| FNAMEnn   | FNAMEnnI       | FNAMEnnO        | First name from SEC-USR-FNAME                       |
| LNAMEnn   | LNAMEnnI       | LNAMEnnO        | Last name from SEC-USR-LNAME                        |
| UTYPEnn   | UTYPEnnI       | UTYPEnnO        | User type from SEC-USR-TYPE                         |
| ERRMSG    | ERRMSGI        | ERRMSGO         | Error/status messages from WS-MESSAGE               |
| TRNNAME   | TRNNAMEI       | TRNNAMEO        | Transaction ID 'CU00'                               |
| PGMNAME   | PGMNAMEI       | PGMNAMEO        | Program name 'COUSR00C'                             |
| TITLE01   | TITLE01I       | TITLE01O        | From CCDA-TITLE01 (COTTL01Y)                        |
| TITLE02   | TITLE02I       | TITLE02O        | From CCDA-TITLE02 (COTTL01Y)                        |
| CURDATE   | CURDATEI       | CURDATEO        | Current date MM/DD/YY (CSDAT01Y)                   |
| CURTIME   | CURTIMEI       | CURTIMEO        | Current time HH:MM:SS (CSDAT01Y)                   |

---

## 10. Navigation / Function Key Definitions

Defined in static label, Row 24 (BMS line 453–458):

| Key     | Action                                                   |
|---------|----------------------------------------------------------|
| ENTER   | Continue — process selection or search                   |
| F3      | Back — return to COADM01C (admin menu)                  |
| F7      | Backward — page to previous set of users                |
| F8      | Forward — page to next set of users                     |

---

## 11. Design Notes and Observations

- All 10 data row fields (USRIDnn, FNAMEnn, LNAMEnn, UTYPEnn) carry FSET attribute. This ensures they are always included in the inbound data stream regardless of whether the operator modified them, enabling the program to read back the displayed User ID when a selection is made.
- Only the SEL000n fields and USRIDIN are UNPROT (editable by the operator). All data fields are ASKIP (protected/read-only).
- The ERRMSG field uses COLOR=RED and ATTRB=BRT for high-visibility error display. FSET ensures its content is always transmitted back.
- The screen does not have a password column — the USRSEC password field is intentionally hidden from the list view.
- UTYPEnn has length 1, displaying only the single character type code (A or U), not the expanded type name.
