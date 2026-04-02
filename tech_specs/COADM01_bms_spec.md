# Technical Specification: COADM01 — Admin Menu BMS Mapset

**Source File:** `app/bms/COADM01.bms`
**BMS-Generated Copybook:** `app/cpy-bms/COADM01.CPY`
**Application:** CardDemo
**Type:** BMS (Basic Mapping Support) Mapset Definition
**Used by Program:** COADM01C (transaction CA00)
**Version Tag:** CardDemo_v1.0-70-g193b394-123 (2022-08-22)

---

## 1. Executive Summary

COADM01 is the BMS mapset containing the single map COADM1A, which is the administrative menu screen for admin users of the CardDemo application. The screen is structurally identical to COMEN01 (COMEN1A) with the sole content difference being the centred title 'Admin Menu' instead of 'Main Menu'. Menu option lines and the selection input field are defined identically. The screen is used exclusively by admin-authenticated users and presents up to 12 dynamically populated administrative function options.

---

## 2. Mapset-Level Attributes (DFHMSD Statement)

Source: `COADM01.bms` lines 19-25.

| Attribute | Value | Meaning |
|---|---|---|
| Mapset Name | COADM01 | Used in CICS SEND/RECEIVE MAP |
| CTRL | (ALARM,FREEKB) | Sound terminal alarm; free keyboard after send |
| EXTATT | YES | Extended attributes (colour, highlighting) generated |
| LANG | COBOL | COBOL symbolic map generated |
| MODE | INOUT | Both input and output structures generated |
| STORAGE | AUTO | Each map instance uses its own storage |
| TIOAPFX | YES | TIOA prefix included (required for CICS) |
| TYPE | &&SYSPARM | Assembly type from SYSPARM |

These attributes are byte-for-byte identical to COMEN01's DFHMSD statement.

---

## 3. Map Definition (DFHMDI Statement)

Source: `COADM01.bms` lines 26-28.

| Attribute | Value | Meaning |
|---|---|---|
| Map Name | COADM1A | Used in MAP parameter of CICS SEND/RECEIVE |
| COLUMN | 1 | Starts at column 1 |
| LINE | 1 | Starts at row 1 |
| SIZE | (24,80) | Standard 24x80 3270 terminal |

---

## 4. Screen Layout

```
Row  Col  Content
---  ---  -----------------------------------------------------------------------
 1    1   'Tran:'  [TRNNAME 4, Blue]  [TITLE01 40, Yellow]  'Date:'  [CURDATE 8, Blue]
 2    1   'Prog:'  [PGMNAME 8, Blue]  [TITLE02 40, Yellow]  'Time:'  [CURTIME 8, Blue]
 3        (blank)
 4   35   'Admin Menu'  [Neutral, Bright, 10 chars]
 5        (blank)
 6   20   [OPTN001 40, Blue]   <- admin option 1 (e.g., "01. User List (Security)")
 7   20   [OPTN002 40, Blue]   <- admin option 2
 8   20   [OPTN003 40, Blue]   <- admin option 3
 9   20   [OPTN004 40, Blue]   <- admin option 4
10   20   [OPTN005 40, Blue]   <- admin option 5
11   20   [OPTN006 40, Blue]   <- admin option 6
12   20   [OPTN007 40, Blue]   <- (blank — only 6 options currently defined)
13   20   [OPTN008 40, Blue]   <- (blank)
14   20   [OPTN009 40, Blue]   <- (blank)
15   20   [OPTN010 40, Blue]   <- (blank)
16   20   [OPTN011 40, Blue]   <- (blank)
17   20   [OPTN012 40, Blue]   <- (blank)
18        (blank)
19        (blank)
20   15   'Please select an option :'  [Turquoise, Bright]  [OPTION 2, underline, NUM, UNPROT]
21        (blank)
22        (blank)
23    1   [ERRMSG 78, Red, Bright]
24    1   'ENTER=Continue  F3=Exit'  [Yellow]
```

---

## 5. Field Definitions

### 5.1 Named Fields

All named fields are structurally identical to COMEN01's named fields. The symbolic map field names and attributes are the same except they are prefixed with COADM1A (map name) rather than COMEN1A.

| Field Name | Row | Col | Length | ATTRB | COLOR | HILIGHT | Initial Value | Symbolic I/O | Purpose |
|---|---|---|---|---|---|---|---|---|---|
| TRNNAME | 1 | 7 | 4 | ASKIP,FSET,NORM | BLUE | — | (none) | TRNNAMEI / TRNNAMEO | Transaction ID in header |
| TITLE01 | 1 | 21 | 40 | ASKIP,FSET,NORM | YELLOW | — | (none) | TITLE01I / TITLE01O | App title line 1 |
| CURDATE | 1 | 71 | 8 | ASKIP,FSET,NORM | BLUE | — | 'mm/dd/yy' | CURDATEI / CURDATEO | Current date |
| PGMNAME | 2 | 7 | 8 | ASKIP,FSET,NORM | BLUE | — | (none) | PGMNAMEI / PGMNAMEO | Program name in header |
| TITLE02 | 2 | 21 | 40 | ASKIP,FSET,NORM | YELLOW | — | (none) | TITLE02I / TITLE02O | App title line 2 |
| CURTIME | 2 | 71 | 8 | ASKIP,FSET,NORM | BLUE | — | 'hh:mm:ss' | CURTIMEI / CURTIMEO | Current time |
| OPTN001 | 6 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN001I / OPTN001O | Admin option line 1 |
| OPTN002 | 7 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN002I / OPTN002O | Admin option line 2 |
| OPTN003 | 8 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN003I / OPTN003O | Admin option line 3 |
| OPTN004 | 9 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN004I / OPTN004O | Admin option line 4 |
| OPTN005 | 10 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN005I / OPTN005O | Admin option line 5 |
| OPTN006 | 11 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN006I / OPTN006O | Admin option line 6 |
| OPTN007 | 12 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN007I / OPTN007O | (unused) |
| OPTN008 | 13 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN008I / OPTN008O | (unused) |
| OPTN009 | 14 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN009I / OPTN009O | (unused) |
| OPTN010 | 15 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN010I / OPTN010O | (unused) |
| OPTN011 | 16 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN011I / OPTN011O | (unused) |
| OPTN012 | 17 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN012I / OPTN012O | (unused) |
| OPTION | 20 | 41 | 2 | FSET,IC,NORM,NUM,UNPROT | — | UNDERLINE | (none) | OPTIONI / OPTIONO | Admin option selection |
| ERRMSG | 23 | 1 | 78 | ASKIP,BRT,FSET | RED | — | (none) | ERRMSGI / ERRMSGO | Error/info message |

---

## 6. Input Field Detail: OPTION

Source: `COADM01.bms` lines 145-153.

```
OPTION DFHMDF ATTRB=(FSET,IC,NORM,NUM,UNPROT),
               HILIGHT=UNDERLINE,
               JUSTIFY=(RIGHT,ZERO),
               LENGTH=2,
               POS=(20,41)
```

Identical definition to the OPTION field in COMEN01. See COMEN01_bms_spec.md Section 6 for full attribute discussion.

**Symbolic fields:**
- Input: `OPTIONI PIC X(2)` in COADM1AI; `OPTIONL COMP PIC S9(4)`.
- Output: `OPTIONO PIC X(2)` in COADM1AO; `OPTIONC/P/H/V` attribute bytes.

---

## 7. Static Display Fields (Unnamed DFHMDF)

| Row | Col | Length | Color | Intensity | Content |
|---|---|---|---|---|---|
| 1 | 1 | 5 | BLUE | NORM | 'Tran:' |
| 1 | 65 | 5 | BLUE | NORM | 'Date:' |
| 2 | 1 | 5 | BLUE | NORM | 'Prog:' |
| 2 | 65 | 5 | BLUE | NORM | 'Time:' |
| 4 | 35 | 10 | NEUTRAL | BRT | 'Admin Menu' |
| 20 | 15 | 25 | TURQUOISE | BRT | 'Please select an option :' |
| 24 | 1 | 23 | YELLOW | NORM | 'ENTER=Continue  F3=Exit' |

The only distinguishing difference from COMEN01's static fields is row 4: 'Admin Menu' (LENGTH=10) vs. COMEN01's 'Main Menu' (LENGTH=9).

---

## 8. BMS-Generated Symbolic Copybook (COADM01.CPY)

Source: `app/cpy-bms/COADM01.CPY`.

The file defines two 01-level structures:

**COADM1AI** (input):
Identical structure to COMEN1AI except the 01-level name is COADM1AI.

**COADM1AO** (output — REDEFINES COADM1AI):
Identical structure to COMEN1AO except the 01-level name is COADM1AO.

All field names within the structures are the same: TRNNAME, TITLE01, CURDATE, PGMNAME, TITLE02, CURTIME, OPTN001–OPTN012, OPTION, ERRMSG — with the same L/F/A/C/P/H/V/I/O suffix conventions.

---

## 9. Runtime Screen Content (Admin Options from COADM02Y)

When COADM01C's BUILD-MENU-OPTIONS paragraph runs, the following content is placed into the screen (based on COADM02Y data as of v2.0-16):

```
Row 6:  '01. User List (Security)               '
Row 7:  '02. User Add (Security)                '
Row 8:  '03. User Update (Security)             '
Row 9:  '04. User Delete (Security)             '
Row 10: '05. Transaction Type List/Update (Db2) '
Row 11: '06. Transaction Type Maintenance (Db2) '
Rows 12-17: (blank — OPTN007O–OPTN012O not populated)
```

---

## 10. Comparison: COADM01 vs. COMEN01

The two mapsets are virtually identical. The complete comparison:

| Aspect | COMEN01 (COMEN1A) | COADM01 (COADM1A) |
|---|---|---|
| Mapset name | COMEN01 | COADM01 |
| Map name | COMEN1A | COADM1A |
| Transaction | CM00 (COMEN01C) | CA00 (COADM01C) |
| Title field | 'Main Menu' (LENGTH=9) | 'Admin Menu' (LENGTH=10) |
| DFHMSD attributes | Identical | Identical |
| DFHMDI attributes | Identical | Identical |
| All named fields | Identical | Identical |
| Input field (OPTION) | Identical | Identical |
| Static labels | 'Tran:' 'Date:' 'Prog:' 'Time:' | Identical |
| Function key legend | 'ENTER=Continue  F3=Exit' | Identical |
| ERRMSG field | Identical | Identical |
| Runtime options displayed | 11 (from COMEN02Y) | 6 (from COADM02Y) |

The BMS source difference between the two files amounts to a single word in a static label: 'Main Menu' vs 'Admin Menu'. All map dimensions, field positions, lengths, and attributes are identical.

---

## 11. Keyboard Navigation

| Key | Action in COADM01C |
|---|---|
| Enter | Submit selected option; EIBAID = DFHENTER |
| PF3 | Return to sign-on screen; EIBAID = DFHPF3 |
| Tab | Move cursor (only one unprotected field: OPTION) |
| Any other PF/PA key | "Invalid key pressed" error message |

---

## 12. Design Notes

1. **12 option slots vs. 6 active options**: The BMS screen defines 12 option display lines (OPTN001–OPTN012) but only 6 are currently populated at runtime by COADM01C. The screen capacity of 12 aligns with the main menu (which has 11 active options), indicating the mapsets were designed as templates for reuse. The BMS definitions therefore support expansion of admin options up to 12 without any BMS changes.

2. **Structural duplication**: The near-identical BMS definitions of COADM01 and COMEN01 are a deliberate design choice to maintain separate CICS resource names for admin vs. user functions, despite the functional equivalence. This allows for independent modification of either screen (e.g., adding admin-specific fields) without affecting the other.

3. **No APPLID / SYSID fields**: Unlike the sign-on screen (COSGN00), neither the main menu nor the admin menu screen includes APPLID or SYSID display fields. This is consistent — those values are only relevant for diagnostic identification at the entry point, not throughout the application navigation.

4. **ERRMSG colour programmatic override**: The ERRMSGC attribute byte in COADM1AO allows COADM01C to dynamically change the error message colour at runtime. COADM01C uses DFHGREEN for "not installed" messages and the field default (RED) for standard errors. This is consistent with the BMS design intent: the RED ATTRB on the ERRMSG field sets the default colour, while the C-suffix byte in the output structure allows runtime override.
