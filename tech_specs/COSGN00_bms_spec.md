# Technical Specification: COSGN00 — Sign-on BMS Mapset

**Source File:** `app/bms/COSGN00.bms`
**BMS-Generated Copybook:** `app/cpy-bms/COSGN00.CPY`
**Application:** CardDemo
**Type:** BMS (Basic Mapping Support) Mapset Definition
**Used by Program:** COSGN00C (transaction CC00)
**Version Tag:** CardDemo_v1.0-70-g193b394-123 (2022-08-22)

---

## 1. Executive Summary

COSGN00 is the BMS mapset containing the single map COSGN0A, which is the sign-on (login) screen for the CardDemo application. The screen presents application identification information in the header, a decorative ASCII-art "National Reserve Note" motif in the centre, and two input fields (User ID and Password) in the lower portion. It is the first screen seen by every user of the system.

---

## 2. Mapset-Level Attributes (DFHMSD Statement)

Source: `COSGN00.bms` line 19-25.

| Attribute | Value | Meaning |
|---|---|---|
| Mapset Name | COSGN00 | Name used in CICS SEND/RECEIVE MAP statements |
| CTRL | (ALARM,FREEKB) | Sound terminal alarm on send; free (unlock) keyboard after send |
| EXTATT | YES | Extended attributes (colour, highlighting) are generated |
| LANG | COBOL | Generated copybook in COBOL format |
| MODE | INOUT | Both input and output symbolic maps are generated |
| STORAGE | AUTO | Each map instance gets its own storage (not shared) |
| TIOAPFX | YES | Terminal I/O area prefix is included (required for CICS) |
| TYPE | &&SYSPARM | Assembled with TYPE passed via SYSPARM (MAP for definition, DSECT for copybook generation) |

---

## 3. Map Definition (DFHMDI Statement)

Source: `COSGN00.bms` line 26-28.

| Attribute | Value | Meaning |
|---|---|---|
| Map Name | COSGN0A | Name used in MAP parameter of CICS SEND/RECEIVE |
| COLUMN | 1 | Starts at column 1 |
| LINE | 1 | Starts at row 1 |
| SIZE | (24,80) | Standard 24 rows by 80 columns 3270 terminal size |

---

## 4. Screen Layout

The screen occupies a standard 24x80 3270 terminal display.

```
Row  Col  Content
---  ---  -----------------------------------------------------------------------
 1    1   'Tran :'  [TRNNAME 4 chars, Blue]  [TITLE01 40 chars, Yellow]  'Date :'  [CURDATE 8 chars, Blue]
 2    1   'Prog :'  [PGMNAME 8 chars, Blue]  [TITLE02 40 chars, Yellow]  'Time :'  [CURTIME 9 chars, Blue]
 3    1   'AppID:'  [APPLID 8 chars, Blue]                                'SysID:'  [SYSID 8 chars, Blue]
 4        (blank)
 5    6   'This is a Credit Card Demo Application for Mainframe Modernization'  [Neutral/White]
 6        (blank)
 7   21   '+========================================+'  [Blue, 42 chars]
 8   21   '|%%%%%%%  NATIONAL RESERVE NOTE  %%%%%%%%|'  [Blue]
 9   21   '|%(1)  THE UNITED STATES OF KICSLAND (1)%|'  [Blue]
10   21   '|%$$              ___       ********  $$%|'  [Blue]
11   21   '|%$    {x}       (o o)                 $%|'  [Blue]
12   21   '|%$     ******  (  V  )      O N E     $%|'  [Blue]
13   21   '|%(1)          ---m-m---             (1)%|'  [Blue]
14   21   '|%%~~~~~~~~~~~ ONE DOLLAR ~~~~~~~~~~~~~%%|'  [Blue]
15   21   '+========================================+'  [Blue]
16        (blank)
17   16   'Type your User ID and Password, then press ENTER:'  [Turquoise, 49 chars]
18        (blank)
19   29   'User ID     :'  [Turquoise]  [USERID 8 chars, Green, UNPROT/IC]  '(8 Char)'  [Blue]
20   29   'Password    :'  [Turquoise]  [PASSWD 8 chars, Green, DRK/UNPROT]  '(8 Char)'  [Blue]
21        (blank)
22        (blank)
23    1   [ERRMSG 78 chars, Red, BRIGHT]
24    1   'ENTER=Sign-on  F3=Exit'  [Yellow]
```

---

## 5. Field Definitions

### 5.1 Named Fields

All DFHMDF statements with a label become named fields in the symbolic map. Fields without a label are static (ASKIP, NORM) display-only literals that are NOT represented in the symbolic copybook.

| Field Name | Row | Col | Length | ATTRB | COLOR | HILIGHT | Initial Value | Symbolic Map Field | Purpose |
|---|---|---|---|---|---|---|---|---|---|
| TRNNAME | 1 | 8 | 4 | ASKIP,FSET,NORM | BLUE | — | (none) | TRNNAMEI / TRNNAMEO | Transaction ID in header |
| TITLE01 | 1 | 21 | 40 | ASKIP,FSET,NORM | YELLOW | — | (none) | TITLE01I / TITLE01O | Application title line 1 |
| CURDATE | 1 | 71 | 8 | ASKIP,FSET,NORM | BLUE | — | 'mm/dd/yy' | CURDATEI / CURDATEO | Current date display |
| PGMNAME | 2 | 8 | 8 | FSET,NORM,PROT | BLUE | — | (none) | PGMNAMEI / PGMNAMEO | Program name in header |
| TITLE02 | 2 | 21 | 40 | ASKIP,FSET,NORM | YELLOW | — | (none) | TITLE02I / TITLE02O | Application title line 2 |
| CURTIME | 2 | 71 | 9 | FSET,NORM,PROT | BLUE | — | 'Ahh:mm:ss' | CURTIMEI / CURTIMEO | Current time display |
| APPLID | 3 | 8 | 8 | FSET,NORM,PROT | BLUE | — | (none) | APPLIDI / APPLIDO | CICS Application ID |
| SYSID | 3 | 71 | 8 | FSET,NORM,PROT | BLUE | — | '        ' | SYSIDI / SYSIDO | CICS System ID |
| USERID | 19 | 43 | 8 | FSET,IC,NORM,UNPROT | GREEN | OFF | (none) | USERIDI / USERIDO | User ID input field |
| PASSWD | 20 | 43 | 8 | DRK,FSET,UNPROT | GREEN | OFF | '________' | PASSWDI / PASSWDO | Password input (dark/hidden) |
| ERRMSG | 23 | 1 | 78 | ASKIP,BRT,FSET | RED | — | (none) | ERRMSGI / ERRMSGO | Error/status message display |

### 5.2 Attribute Byte Glossary

| Attribute | Meaning |
|---|---|
| ASKIP | Autoskip — cursor skips over this field; field is display-only |
| PROT | Protected — field cannot receive keyboard input |
| UNPROT | Unprotected — field accepts keyboard input |
| NORM | Normal intensity |
| BRT | Bright (high) intensity |
| DRK | Dark (non-display) — field content is not visible on screen (used for passwords) |
| FSET | Field Set — the Modified Data Tag (MDT) is pre-set to 1, causing the field to be included in 3270 data stream even if user does not type in it |
| IC | Insert Cursor — initial cursor position is placed at this field |

---

## 6. Input Fields Detail

### 6.1 USERID Field (Row 19, Col 43)

```
USERID DFHMDF ATTRB=(FSET,IC,NORM,UNPROT),
               COLOR=GREEN,
               HILIGHT=OFF,
               LENGTH=8,
               POS=(19,43)
```

- **FSET**: The MDT is always set, so the field value (even spaces) is always transmitted to the host on Enter. This ensures RECEIVE MAP always gets the USERID value.
- **IC**: Cursor is initially positioned here when the map is first displayed.
- **UNPROT**: Accepts up to 8 characters of input.
- **NORM**: Normal intensity (visible, not highlighted or dark).
- **Symbolic input field**: `USERIDI PIC X(8)` in COSGN0AI; the length of received data in `USERIDL COMP PIC S9(4)`.

### 6.2 PASSWD Field (Row 20, Col 43)

```
PASSWD DFHMDF ATTRB=(DRK,FSET,UNPROT),
               COLOR=GREEN,
               HILIGHT=OFF,
               LENGTH=8,
               POS=(20,43),
               INITIAL='________'
```

- **DRK**: Dark intensity — the 8 underscore initial value is displayed as blanks (invisible). Anything typed by the user is also invisible. This is the standard 3270 mechanism for password masking.
- **FSET**: MDT pre-set; password field always transmitted.
- **UNPROT**: Accepts keyboard input despite DRK attribute.
- **INITIAL='________'**: Eight underscores provide a visual hint of the field length even though the DRK attribute makes them invisible on a real 3270. On some terminal emulators this may render as visible placeholder characters.
- **Zero-length field at (19,52) and (20,52)**: Two unnamed zero-length DFHMDF fields (lines 163-164 and 183-184) act as field terminators (stopper bytes), preventing the user from typing past the 8-character limit into adjacent areas.
- **Symbolic input field**: `PASSWDI PIC X(8)` in COSGN0AI; length in `PASSWDL COMP PIC S9(4)`.

### 6.3 ERRMSG Field (Row 23, Col 1)

```
ERRMSG DFHMDF ATTRB=(ASKIP,BRT,FSET),
               COLOR=RED,
               LENGTH=78,
               POS=(23,1)
```

- **BRT**: Bright (highlighted) intensity for visibility.
- **ASKIP**: Display-only; terminal does not place cursor here.
- **FSET**: Pre-set MDT; always returned on transmission (ensures previous error messages are always refreshed).
- **COLOR=RED**: Error messages display in red.
- **Symbolic fields**: `ERRMSGI PIC X(78)` / `ERRMSGO PIC X(78)` and attribute byte `ERRMSGC PICTURE X` (for dynamic colour override).

---

## 7. Static Display Fields (Unnamed DFHMDF — Not in Symbolic Map)

These are display-only literals that cannot be programmatically modified at runtime:

| Row | Col | Length | Color | Content |
|---|---|---|---|---|
| 1 | 1 | 6 | BLUE | 'Tran :' |
| 1 | 64 | 6 | BLUE | 'Date :' |
| 2 | 1 | 6 | BLUE | 'Prog :' |
| 2 | 64 | 6 | BLUE | 'Time :' |
| 3 | 1 | 6 | BLUE | 'AppID:' |
| 3 | 64 | 6 | BLUE | 'SysID:' |
| 5 | 6 | 66 | NEUTRAL | 'This is a Credit Card Demo Application for Mainframe Modernization' |
| 7 | 21 | 42 | BLUE | '+========================================+' |
| 8 | 21 | 42 | BLUE | '\|%%%%%%%  NATIONAL RESERVE NOTE  %%%%%%%%\|' |
| 9 | 21 | 42 | BLUE | '\|%(1)  THE UNITED STATES OF KICSLAND (1)%\|' |
| 10 | 21 | 42 | BLUE | '\|%$$              ___       ********  $$%\|' |
| 11 | 21 | 42 | BLUE | '\|%$    {x}       (o o)                 $%\|' |
| 12 | 21 | 42 | BLUE | '\|%$     ******  (  V  )      O N E     $%\|' |
| 13 | 21 | 42 | BLUE | '\|%(1)          ---m-m---             (1)%\|' |
| 14 | 21 | 42 | BLUE | '\|%%~~~~~~~~~~~ ONE DOLLAR ~~~~~~~~~~~~~%%\|' |
| 15 | 21 | 42 | BLUE | '+========================================+' |
| 17 | 16 | 49 | TURQUOISE | 'Type your User ID and Password, then press ENTER:' |
| 19 | 29 | 13 | TURQUOISE | 'User ID     :' |
| 19 | 52 | 8 | BLUE | '(8 Char)' |
| 20 | 29 | 13 | TURQUOISE | 'Password    :' |
| 20 | 52 | 8 | BLUE | '(8 Char)' |
| 24 | 1 | 22 | YELLOW | 'ENTER=Sign-on  F3=Exit' |

---

## 8. BMS-Generated Symbolic Copybook (COSGN00.CPY)

The BMS assembler generates a dual-structure copybook in `app/cpy-bms/COSGN00.CPY`. The COPY statement in COSGN00C is `COPY COSGN00` (line 50), which resolves to this file.

### 8.1 Input Map Structure: COSGN0AI

For each named field XXXXX, the input structure contains:
- `XXXXXL COMP PIC S9(4)` — length of data received (negative if field not modified)
- `XXXXXF PICTURE X` — flags byte
- `XXXXXF REDEFINES` → `XXXXXА PICTURE X` — attribute byte
- `FILLER PICTURE X(4)` — colour/extended attribute bytes
- `XXXXXІ PIC X(n)` — the actual data value

### 8.2 Output Map Structure: COSGN0AO (REDEFINES COSGN0AI)

For each named field XXXXX, the output structure contains:
- `FILLER PICTURE X(3)` — alignment
- `XXXXXC PICTURE X` — colour attribute (e.g., DFHRED, DFHGREEN, DFHBLUE)
- `XXXXXP PICTURE X` — PS (programmatic selection) byte
- `XXXXXH PICTURE X` — highlight byte
- `XXXXXV PICTURE X` — validation byte
- `XXXXXO PIC X(n)` — the output data value

**Fields in COSGN0AI / COSGN0AO:**

| Symbolic Base Name | Input (I) PIC | Output (O) PIC | Notes |
|---|---|---|---|
| TRNNAME | X(4) | X(4) | Transaction ID |
| TITLE01 | X(40) | X(40) | App title line 1 |
| CURDATE | X(8) | X(8) | Date MM/DD/YY |
| PGMNAME | X(8) | X(8) | Program name |
| TITLE02 | X(40) | X(40) | App title line 2 |
| CURTIME | X(9) | X(9) | Time HH:MM:SS |
| APPLID | X(8) | X(8) | CICS APPLID |
| SYSID | X(8) | X(8) | CICS SYSID |
| USERID | X(8) | X(8) | User ID |
| PASSWD | X(8) | X(8) | Password (dark) |
| ERRMSG | X(78) | X(78) | Error message |

---

## 9. Keyboard Navigation

| Key | Action |
|---|---|
| Enter | Submit credentials; EIBAID = DFHENTER in COSGN00C |
| PF3 | Exit application; EIBAID = DFHPF3 in COSGN00C |
| Tab / Backtab | Move between USERID and PASSWD fields |
| All other PF/PA keys | Trigger "Invalid key pressed" error in COSGN00C |

---

## 10. Screen I/O Flow in COSGN00C

| Operation | CICS Command | Map | Mapset | Direction |
|---|---|---|---|---|
| Display sign-on screen | SEND MAP COSGN0A MAPSET COSGN00 FROM(COSGN0AO) ERASE CURSOR | COSGN0A | COSGN00 | Program -> Terminal |
| Receive credentials | RECEIVE MAP COSGN0A MAPSET COSGN00 | COSGN0A | COSGN00 | Terminal -> Program (COSGN0AI) |

The CURSOR option on SEND positions the cursor at the field whose symbolic length field (xxxxxL) has been set to -1. COSGN00C sets:
- `MOVE -1 TO USERIDL OF COSGN0AI` — cursor on User ID (first entry, User ID blank)
- `MOVE -1 TO PASSWDL OF COSGN0AI` — cursor on Password (Password blank)

---

## 11. Design Notes and Observations

1. **Dual stopper bytes for PASSWD (rows 19-20, col 52)**: Zero-length unnamed fields at positions (19,52) and (20,52) act as field stopper bytes between the 8-char input fields and the '(8 Char)' label. This prevents typed input from overwriting the label area.

2. **PGMNAME uses PROT not ASKIP**: Unlike TRNNAME and CURDATE which use ASKIP, PGMNAME and CURTIME use `FSET,NORM,PROT`. The distinction between PROT and ASKIP is subtle: ASKIP fields cause the cursor to skip automatically; PROT fields stop the cursor. Both prevent input. The mix appears intentional for cursor flow control.

3. **CURTIME length is 9 on COSGN00 vs. 8 on COMEN01/COADM01**: The CURTIME field in COSGN00 is LENGTH=9 with initial value 'Ahh:mm:ss' (9 characters). In COMEN01 and COADM01, CURTIME is LENGTH=8 with initial value 'hh:mm:ss'. In COSGN00C, CURTIMEO receives `WS-CURTIME-HH-MM-SS` which is 8 characters (HH:MM:SS format from CSDAT01Y). The 9th character of CURTIMEO would receive a space. The leading 'A' in the initial value 'Ahh:mm:ss' is a placeholder annotation character in the BMS source, not a literal character sent at runtime (the FROM(COSGN0AO) overrides the INITIAL).

4. **Decorative art**: The "National Reserve Note" art (rows 7-15) references "THE UNITED STATES OF KICSLAND" — a playful reference to CICS (Customer Information Control System). This is purely decorative and has no functional significance.
