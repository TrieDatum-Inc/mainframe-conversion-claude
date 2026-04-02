# Technical Specification: COMEN01 — Main Menu BMS Mapset

**Source File:** `app/bms/COMEN01.bms`
**BMS-Generated Copybook:** `app/cpy-bms/COMEN01.CPY`
**Application:** CardDemo
**Type:** BMS (Basic Mapping Support) Mapset Definition
**Used by Program:** COMEN01C (transaction CM00)
**Version Tag:** CardDemo_v1.0-70-g193b394-123 (2022-08-22)

---

## 1. Executive Summary

COMEN01 is the BMS mapset containing the single map COMEN1A, which is the main menu screen for regular (non-admin) users of the CardDemo application. The screen presents a two-row header with transaction/program/date/time identification, a centred "Main Menu" title, up to 12 dynamically populated menu option lines, a single-option entry field, an error message area, and a function key legend. Menu option text is not defined in the BMS source; it is built dynamically at runtime by COMEN01C from the COMEN02Y data table.

---

## 2. Mapset-Level Attributes (DFHMSD Statement)

Source: `COMEN01.bms` lines 19-25.

| Attribute | Value | Meaning |
|---|---|---|
| Mapset Name | COMEN01 | Used in CICS SEND/RECEIVE MAP |
| CTRL | (ALARM,FREEKB) | Sound terminal alarm; free keyboard after send |
| EXTATT | YES | Extended attributes (colour, highlighting) generated |
| LANG | COBOL | COBOL symbolic map generated |
| MODE | INOUT | Both input and output structures generated |
| STORAGE | AUTO | Each map instance uses its own storage |
| TIOAPFX | YES | TIOA prefix included (required for CICS) |
| TYPE | &&SYSPARM | Assembly type from SYSPARM |

---

## 3. Map Definition (DFHMDI Statement)

Source: `COMEN01.bms` lines 26-28.

| Attribute | Value | Meaning |
|---|---|---|
| Map Name | COMEN1A | Used in MAP parameter of CICS SEND/RECEIVE |
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
 4   35   'Main Menu'  [Neutral, Bright, 9 chars]
 5        (blank)
 6   20   [OPTN001 40, Blue]   <- menu option 1 text (e.g., "01. Account View")
 7   20   [OPTN002 40, Blue]   <- menu option 2 text
 8   20   [OPTN003 40, Blue]   <- menu option 3 text
 9   20   [OPTN004 40, Blue]   <- menu option 4 text
10   20   [OPTN005 40, Blue]   <- menu option 5 text
11   20   [OPTN006 40, Blue]   <- menu option 6 text
12   20   [OPTN007 40, Blue]   <- menu option 7 text
13   20   [OPTN008 40, Blue]   <- menu option 8 text
14   20   [OPTN009 40, Blue]   <- menu option 9 text
15   20   [OPTN010 40, Blue]   <- menu option 10 text
16   20   [OPTN011 40, Blue]   <- menu option 11 text
17   20   [OPTN012 40, Blue]   <- menu option 12 text (unused currently)
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

| Field Name | Row | Col | Length | ATTRB | COLOR | HILIGHT | Initial Value | Symbolic I/O | Purpose |
|---|---|---|---|---|---|---|---|---|---|
| TRNNAME | 1 | 7 | 4 | ASKIP,FSET,NORM | BLUE | — | (none) | TRNNAMEI / TRNNAMEO | Transaction ID in header |
| TITLE01 | 1 | 21 | 40 | ASKIP,FSET,NORM | YELLOW | — | (none) | TITLE01I / TITLE01O | App title line 1 |
| CURDATE | 1 | 71 | 8 | ASKIP,FSET,NORM | BLUE | — | 'mm/dd/yy' | CURDATEI / CURDATEO | Current date |
| PGMNAME | 2 | 7 | 8 | ASKIP,FSET,NORM | BLUE | — | (none) | PGMNAMEI / PGMNAMEO | Program name in header |
| TITLE02 | 2 | 21 | 40 | ASKIP,FSET,NORM | YELLOW | — | (none) | TITLE02I / TITLE02O | App title line 2 |
| CURTIME | 2 | 71 | 8 | ASKIP,FSET,NORM | BLUE | — | 'hh:mm:ss' | CURTIMEI / CURTIMEO | Current time |
| OPTN001 | 6 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN001I / OPTN001O | Menu option line 1 |
| OPTN002 | 7 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN002I / OPTN002O | Menu option line 2 |
| OPTN003 | 8 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN003I / OPTN003O | Menu option line 3 |
| OPTN004 | 9 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN004I / OPTN004O | Menu option line 4 |
| OPTN005 | 10 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN005I / OPTN005O | Menu option line 5 |
| OPTN006 | 11 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN006I / OPTN006O | Menu option line 6 |
| OPTN007 | 12 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN007I / OPTN007O | Menu option line 7 |
| OPTN008 | 13 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN008I / OPTN008O | Menu option line 8 |
| OPTN009 | 14 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN009I / OPTN009O | Menu option line 9 |
| OPTN010 | 15 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN010I / OPTN010O | Menu option line 10 |
| OPTN011 | 16 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN011I / OPTN011O | Menu option line 11 |
| OPTN012 | 17 | 20 | 40 | ASKIP,FSET,NORM | BLUE | — | ' ' | OPTN012I / OPTN012O | Menu option line 12 (unused) |
| OPTION | 20 | 41 | 2 | FSET,IC,NORM,NUM,UNPROT | — | UNDERLINE | (none) | OPTIONI / OPTIONO | Menu selection entry field |
| ERRMSG | 23 | 1 | 78 | ASKIP,BRT,FSET | RED | — | (none) | ERRMSGI / ERRMSGO | Error/info message |

---

## 6. Input Field Detail: OPTION

Source: `COMEN01.bms` lines 145-153.

```
OPTION DFHMDF ATTRB=(FSET,IC,NORM,NUM,UNPROT),
               HILIGHT=UNDERLINE,
               JUSTIFY=(RIGHT,ZERO),
               LENGTH=2,
               POS=(20,41)
```

| Attribute | Meaning |
|---|---|
| FSET | MDT pre-set — field always included in 3270 data stream on Enter |
| IC | Initial cursor position — cursor placed here when map is sent |
| NORM | Normal intensity |
| NUM | Numeric only — 3270 terminal enforces numeric-only keyboard input |
| UNPROT | Accepts keyboard input |
| HILIGHT=UNDERLINE | Field is displayed with underline highlighting (visual affordance for input) |
| JUSTIFY=(RIGHT,ZERO) | Data is right-justified with zero fill — terminal hardware justification |
| LENGTH=2 | Accepts 1-2 digit option number |

The zero-length unnamed field at (20,44) (line 150-153) is a stopper byte after the OPTION field.

**Symbolic fields:**
- Input: `OPTIONI PIC X(2)` in COMEN1AI; `OPTIONL COMP PIC S9(4)` for received data length.
- Output: `OPTIONO PIC X(2)` in COMEN1AO; `OPTIONC/P/H/V` for attribute override bytes.

---

## 7. Menu Option Fields Detail (OPTN001–OPTN012)

All 12 option fields share identical attributes:

```
OPTNnnn DFHMDF ATTRB=(ASKIP,FSET,NORM),
                COLOR=BLUE,
                LENGTH=40,
                POS=(row,20),
                INITIAL=' '
```

| Attribute | Meaning |
|---|---|
| ASKIP | Display-only; cursor skips over these fields |
| FSET | MDT pre-set (ensures option text is always transmitted back, though COMEN01C only reads OPTIONI) |
| NORM | Normal intensity |
| INITIAL=' ' | Single-space initial value (cleared on LOW-VALUES initialization in COMEN01C) |
| COLOR=BLUE | Blue display colour |
| LENGTH=40 | Maximum option text length |

**Runtime population:** COMEN01C's BUILD-MENU-OPTIONS paragraph writes to OPTN001O through OPTN011O using data from COMEN02Y. OPTN012O is never written by COMEN01C (WHEN OTHER CONTINUE in the EVALUATE) because CDEMO-MENU-OPT-COUNT = 11.

**Typical rendered content (at runtime):**
```
Row 6:  '01. Account View                       '
Row 7:  '02. Account Update                     '
Row 8:  '03. Credit Card List                   '
Row 9:  '04. Credit Card View                   '
Row 10: '05. Credit Card Update                 '
Row 11: '06. Transaction List                   '
Row 12: '07. Transaction View                   '
Row 13: '08. Transaction Add                    '
Row 14: '09. Transaction Reports                '
Row 15: '10. Bill Payment                       '
Row 16: '11. Pending Authorization View         '
Row 17: (blank — OPTN012O not populated)
```

---

## 8. Static Display Fields (Unnamed DFHMDF)

| Row | Col | Length | Color | Content |
|---|---|---|---|---|
| 1 | 1 | 5 | BLUE | 'Tran:' |
| 1 | 65 | 5 | BLUE | 'Date:' |
| 2 | 1 | 5 | BLUE | 'Prog:' |
| 2 | 65 | 5 | BLUE | 'Time:' |
| 4 | 35 | 9 | NEUTRAL | 'Main Menu' (BRIGHT) |
| 20 | 15 | 25 | TURQUOISE | 'Please select an option :' (BRIGHT) |
| 24 | 1 | 23 | YELLOW | 'ENTER=Continue  F3=Exit' |

---

## 9. BMS-Generated Symbolic Copybook (COMEN01.CPY)

Source: `app/cpy-bms/COMEN01.CPY`.

The file defines two 01-level structures:

**COMEN1AI** (input) — 653 bytes total (approx.):
- 12-byte FILLER prefix (TIOA prefix)
- For each named field: L (COMP S9(4)), F (X), REDEFINES (A), FILLER X(4), I (data)
- Named fields: TRNNAME, TITLE01, CURDATE, PGMNAME, TITLE02, CURTIME, OPTN001–OPTN012, OPTION, ERRMSG

**COMEN1AO** (output — REDEFINES COMEN1AI):
- For each named field: FILLER X(3), C (colour), P (PS), H (highlight), V (validation), O (data)

---

## 10. Differences from COSGN00 BMS Screen

| Aspect | COSGN00 (COSGN0A) | COMEN01 (COMEN1A) |
|---|---|---|
| Purpose | Sign-on / authentication | Main menu |
| Input fields | USERID (8), PASSWD (8) | OPTION (2) |
| Content area | Fixed decorative art (rows 5-15) | Dynamic menu options (rows 6-17) |
| Header fields | TRNNAME, TITLE01/02, CURDATE, PGMNAME, CURTIME, APPLID, SYSID | TRNNAME, TITLE01/02, CURDATE, PGMNAME, CURTIME (no APPLID/SYSID) |
| Centred title | None | 'Main Menu' at row 4 |
| Label prefix | 'Tran :' (6 chars with space) | 'Tran:' (5 chars) |
| CURTIME length | 9 | 8 |
| PGMNAME attribute | FSET,NORM,PROT | ASKIP,FSET,NORM |
| OPTION field | N/A | HILIGHT=UNDERLINE, NUM, JUSTIFY=(RIGHT,ZERO) |
| Password masking | DRK attribute on PASSWD | Not applicable |

---

## 11. Keyboard Navigation

| Key | Action in COMEN01C |
|---|---|
| Enter | Submit selected option; EIBAID = DFHENTER |
| PF3 | Return to sign-on screen; EIBAID = DFHPF3 |
| Tab | Move cursor (only one unprotected input field: OPTION) |
| Any other PF/PA key | "Invalid key pressed" error |

---

## 12. Design Notes

1. **FSET on all OPTN fields**: Setting MDT on the display-only OPTN001–OPTN012 fields means their content is always transmitted back in the 3270 inbound data stream on Enter, even though COMEN01C never reads OPTNnnnI. This is slightly inefficient for the 3270 data stream but is the standard pattern for this application and ensures idempotent behaviour.

2. **OPTION field with JUSTIFY=(RIGHT,ZERO) and NUM**: The BMS-level justification and the COMEN01C application-level scan-and-replace logic (lines 117-124 of COMEN01C.cbl) are redundant but defensive. If a terminal sends '3 ' (left-justified), both mechanisms independently result in '03' being stored in WS-OPTION.

3. **OPTN fields use INITIAL=' ' (single space)**: This means if COMEN01C sends LOW-VALUES in COMEN1AO (as it does on first entry: `MOVE LOW-VALUES TO COMEN1AO`), the INITIAL value is NOT used — LOW-VALUES clears all fields including INITIAL values, which is the correct behaviour (blank screen before BUILD-MENU-OPTIONS populates the fields with runtime data).
