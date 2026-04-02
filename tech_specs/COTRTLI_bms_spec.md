# Technical Specification: COTRTLI (BMS Mapset)

## 1. Executive Summary

COTRTLI is a **BMS (Basic Mapping Support) mapset** that defines the screen layout for the Transaction Type Listing function of the CardDemo application. It contains a single map, `CTRTLIA`, which provides a paginated 24×80 3270 terminal screen supporting filter entry, a 7-row scrollable list of transaction types, and action selection (U=Update, D=Delete) per row. This mapset is used exclusively by program COTRTLIC (transaction `CTLI`). The BMS source file is at `app/app-transaction-type-db2/bms/COTRTLI.bms`; the corresponding COBOL symbolic map copybook is `app/app-transaction-type-db2/cpy-bms/COTRTLI.cpy`.

---

## 2. Mapset Definition

| Attribute | Value | Source |
|---|---|---|
| Mapset name | COTRTLI | BMS `DFHMSD` label, line 20 |
| Language | COBOL | `LANG=COBOL` |
| Mode | Input and Output | `MODE=INOUT` |
| Storage | Automatic | `STORAGE=AUTO` |
| TIOAPFX | YES | `TIOAPFX=YES` |
| Map name | CTRTLIA | BMS `DFHMDI` label, line 25 |
| Screen size | 24 rows × 80 columns | `SIZE=(24,80)` |
| Control | FREEKB | `CTRL=(FREEKB)` — keyboard unlocked on SEND |
| Dynamic attributes | COLOR, HILIGHT, PS, VALIDN | `DSATTS=` and `MAPATTS=` |

---

## 3. Screen Layout (24×80)

```
Row  Col  Content
---  ---  -------
 1    1   'Tran:'  [TRNNAME: 4 chars, blue, ASKIP/FSET]
 1   21   [TITLE01: 40 chars, yellow, ASKIP]
 1   65   'Date:'  [CURDATE: 8 chars, blue, initial='mm/dd/yy']
 2    1   'Prog:'  [PGMNAME: 8 chars, blue, ASKIP]
 2   21   [TITLE02: 40 chars, yellow, ASKIP]
 2   65   'Time:'  [CURTIME: 8 chars, blue, initial='hh:mm:ss']
 4   28   'Maintain Transaction Type' (neutral, 25 chars)
 4   70   'Page '  [PAGENO: 3 chars]
 6   30   'Type Filter:'  (turquoise, 12 chars)
 6   44   [TRTYPE: 2 chars, green, underline, UNPROT/FSET/IC]
 8    4   'Description Filter:'  (turquoise, 19 chars)
 8   25   [TRDESC: 50 chars, green, underline, UNPROT/FSET]
10    4   'Select    '
10   16   'Type'
10   42   'Description'
11    4   '------'
11   15   '-----'
11   25   '-'-repeated 50 chars (separator line)
12    6   [TRTSEL1: 1 char, FSET/PROT/underline]   Row 1 select flag
12   17   [TRTTYP1: 2 chars, FSET/PROT/no-hilight]  Row 1 type code
12   25   [TRTYPD1: 50 chars, FSET/UNPROT/no-hilight] Row 1 description
13    6   [TRTSEL2: 1 char]  Row 2 select flag
13   17   [TRTTYP2: 2 chars] Row 2 type code
13   25   [TRTYPD2: 50 chars] Row 2 description
14    6   [TRTSEL3: 1 char]  Row 3 select flag
14   17   [TRTTYP3: 2 chars] Row 3 type code
14   25   [TRTYPD3: 50 chars] Row 3 description
15    6   [TRTSEL4: 1 char]  Row 4 select flag
15   17   [TRTTYP4: 2 chars] Row 4 type code
15   25   [TRTYPD4: 50 chars] Row 4 description
16    6   [TRTSEL5: 1 char]  Row 5 select flag
16   17   [TRTTYP5: 2 chars] Row 5 type code
16   25   [TRTYPD5: 50 chars] Row 5 description
17    6   [TRTSEL6: 1 char]  Row 6 select flag
17   17   [TRTTYP6: 2 chars] Row 6 type code
17   25   [TRTYPD6: 50 chars] Row 6 description
18    6   [TRTSEL7: 1 char]  Row 7 select flag
18   17   [TRTTYP7: 2 chars] Row 7 type code
18   25   [TRTYPD7: 50 chars] Row 7 description
19    6   [TRTSELA: 1 char, FSET/PROT]  Row 8 overflow/spare select
19   17   [TRTTYPA: 2 chars, FSET/PROT] Row 8 overflow/spare type
19   25   [TRTDSCA: 50 chars, FSET/PROT] Row 8 overflow/spare desc
21   19   [INFOMSG: 45 chars, PROT/neutral] Informational message
23    1   [ERRMSG: 78 chars, ASKIP/BRT/FSET/red] Error message
24    1   'F2=Add'    (turquoise, ASKIP)
24   10   'F3=Exit'   (turquoise, ASKIP)
24   19   'F7=Page Up' (turquoise, ASKIP)
24   32   'F8=Page Dn' (turquoise, ASKIP)
24   44   'F10=Save'  (turquoise, ASKIP)
```

---

## 4. Field Inventory

### 4.1 Header Fields (rows 1-2)

| BMS Name | Row | Col | Len | ATTRB | Color | Hilight | Description |
|---|---|---|---|---|---|---|---|
| (literal) | 1 | 1 | 5 | ASKIP,NORM | BLUE | — | 'Tran:' |
| TRNNAME | 1 | 7 | 4 | ASKIP,FSET,NORM | BLUE | — | Transaction ID (output: 'CTLI') |
| TITLE01 | 1 | 21 | 40 | ASKIP,NORM | YELLOW | — | Application title line 1 |
| (literal) | 1 | 65 | 5 | ASKIP,NORM | BLUE | — | 'Date:' |
| CURDATE | 1 | 71 | 8 | ASKIP,NORM | BLUE | — | Current date MM/DD/YY |
| (literal) | 2 | 1 | 5 | ASKIP,NORM | BLUE | — | 'Prog:' |
| PGMNAME | 2 | 7 | 8 | ASKIP,NORM | BLUE | — | Program name (output: 'COTRTLIC') |
| TITLE02 | 2 | 21 | 40 | ASKIP,NORM | YELLOW | — | Application title line 2 |
| (literal) | 2 | 65 | 5 | ASKIP,NORM | BLUE | — | 'Time:' |
| CURTIME | 2 | 71 | 8 | ASKIP,NORM | BLUE | — | Current time HH:MM:SS |

### 4.2 Navigation / Heading Fields

| BMS Name | Row | Col | Len | Description |
|---|---|---|---|---|
| (literal) | 4 | 28 | 25 | 'Maintain Transaction Type' heading |
| PAGENO | 4 | 76 | 3 | Current page number (output only, unprotected by default) |

### 4.3 Filter Fields (rows 6, 8)

| BMS Name | Row | Col | Len | ATTRB | Color | Hilight | Usage |
|---|---|---|---|---|---|---|---|
| (literal) | 6 | 30 | 12 | ASKIP,NORM | TURQUOISE | — | 'Type Filter:' label |
| TRTYPE | 6 | 44 | 2 | FSET,IC,NORM,UNPROT | GREEN | UNDERLINE | Type code filter — input and output; IC positions cursor here on fresh display |
| (literal) | 8 | 4 | 19 | ASKIP,NORM | TURQUOISE | — | 'Description Filter:' label |
| TRDESC | 8 | 25 | 50 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Description filter — input and output |

**Symbolic map names**: `TRTYPEI`/`TRTYPEO`/`TRTYPEA`/`TRTYPEL` and `TRDESCI`/`TRDESCO`/`TRDESCA`/`TRDESCL`.

The `IC` (Initial Cursor) attribute on TRTYPE positions the cursor to the type filter on initial display.

### 4.4 Data Rows (rows 12-18, 7 scrollable rows)

Each row consists of three fields:

| BMS Name Pattern | Col | Len | ATTRB | Color | Hilight | Usage |
|---|---|---|---|---|---|---|
| TRTSELn (n=1..7) | 6 | 1 | FSET,NORM,PROT | DEFAULT | UNDERLINE | Action selector: operator types 'U' or 'D'; protected by default, program may unprotect |
| TRTTYPn (n=1..7) | 17 | 2 | FSET,NORM,PROT | DEFAULT | OFF | Transaction type code (read-only) |
| TRTYPDn (n=1..7) | 25 | 50 | FSET,NORM,UNPROT | DEFAULT | OFF | Transaction description (editable) |

Rows 1-7 (BMS names TRTSEL1..TRTSEL7, TRTTYP1..TRTTYP7, TRTYPD1..TRTYPD7) correspond to rows 12-18 on screen.

> The BMS source defines rows 1-7 individually (not as a OCCURS). COTRTLIC uses a REDEFINES overlay (lines 434-478 of COTRTLIC.cbl) to superimpose an OCCURS 7 TIMES array structure on the symbolic map for array-based processing.

### 4.5 Row 8 / Overflow (row 19)

| BMS Name | Col | Len | ATTRB | Usage |
|---|---|---|---|---|
| TRTSELA | 6 | 1 | FSET,NORM,PROT | 8th row — appears always protected; used as overflow/padding |
| TRTTYPA | 17 | 2 | FSET,NORM,PROT | — |
| TRTDSCA | 25 | 50 | FSET,NORM,PROT | — |

This is an 8th row defined in the map but not part of the 7-row scroll window. It serves as a visual separator or spare.

### 4.6 Message Fields (rows 21, 23)

| BMS Name | Row | Col | Len | ATTRB | Color | Hilight | Usage |
|---|---|---|---|---|---|---|---|
| INFOMSG | 21 | 19 | 45 | PROT | NEUTRAL | OFF | Informational/instructional message (center-justified by program) |
| ERRMSG | 23 | 1 | 78 | ASKIP,BRT,FSET | RED | — | Error message (bright red, full width) |

### 4.7 PF Key Labels (row 24)

| BMS Name | Col | Len | ATTRB | Color | Initial Value |
|---|---|---|---|---|---|
| BUTNF02 | 1 | 7 | ASKIP,NORM | TURQUOISE | 'F2=Add' |
| BUTNF03 | 10 | 7 | ASKIP,NORM | TURQUOISE | 'F3=Exit' |
| BUTNF07 | 19 | 10 | ASKIP,NORM | TURQUOISE | 'F7=Page Up' |
| BUTNF08 | 32 | 10 | ASKIP,NORM | TURQUOISE | 'F8=Page Dn' |
| BUTNF10 | 44 | 8 | ASKIP,NORM | TURQUOISE | 'F10=Save' |

All PF key labels are permanently visible and non-modifiable from the program (ASKIP/NORM). Note F10 is labeled "Save" but in COTRTLIC's context it functions as the "Confirm" key for delete and update actions.

---

## 5. Symbolic Map Structure (from COTRTLI.cpy)

The copybook defines two structures: `CTRTLIAI` (input) and `CTRTLIAO` (output, REDEFINES CTRTLIAI).

Each BMS field generates a triplet in the symbolic map:
- `fieldL`: PIC S9(4) COMP — length of data entered (input); modified data tag length (output)
- `fieldF` / `fieldA`: PIC X — attribute byte
- `fieldI` / `fieldO`: data field PIC

Selected input fields from `CTRTLIAI`:

| Field | PIC | Description |
|---|---|---|
| TRNNAMEI | PIC X(4) | Transaction name input |
| TITLE01I | PIC X(40) | Title line 1 |
| CURDATEI | PIC X(8) | Date |
| PGMNAMEI | PIC X(8) | Program name |
| TITLE02I | PIC X(40) | Title line 2 |
| CURTIMEI | PIC X(8) | Time |
| PAGENOI | PIC X(3) | Page number |
| TRTYPEI | PIC X(2) | Type filter input |
| TRDESCI | PIC X(50) | Description filter input |
| TRTSEL1I..TRTSEL7I | PIC X(1) each | Row 1-7 action selector input |
| TRTTYP1I..TRTTYP7I | PIC X(2) each | Row 1-7 type code input |
| TRTYPD1I..TRTYPD7I | PIC X(50) each | Row 1-7 description input |

COTRTLIC REDEFINES `CTRTLIAI` (lines 434-456) to create OCCURS 7 array elements with fields:
- `TRTSELL(I)` PIC S9(4) COMP — length for row I selector
- `TRTSELF(I)` / `TRTSELA(I)` PIC X — attribute byte
- `TRTSELI(I)` PIC X(1) — action selector input
- `TRTTYPL(I)` PIC S9(4) COMP — length for type code
- `TRTTYPA(I)` / `TRTTYPO(I)` — attribute / output
- `TRTTYPI(I)` PIC X(2) — type code
- `TRTYPDL(I)` PIC S9(4) COMP — length for description
- `TRTYPDA(I)` / `TRTYPDO(I)` — attribute / output
- `TRTYPDI(I)` PIC X(50) — description input

---

## 6. Program That Uses This Mapset

| Program | Transaction | Usage |
|---|---|---|
| COTRTLIC | CTLI | Exclusive user of COTRTLI / CTRTLIA |

---

## 7. Navigation Flow

```
[Admin Menu COADM01C / Transaction CA00]
          |
          | F2 from admin, or navigate to CTLI
          v
  [COTRTLI / CTRTLIA]  <--- COTRTLIC (trans CTLI)
          |
          | PF02 = Add new type
          v
  [COTRTUP / CTRTUPA]  <--- COTRTUPC (trans CTTU)
          |
          | PF03 = Back
          v
  [COTRTLI / CTRTLIA]  (return)
          |
          | PF03 from list
          v
  [Admin Menu COADM01C]
```

---

## 8. Color Scheme (at Runtime, Dynamic Overrides by COTRTLIC)

The BMS defines initial colors. COTRTLIC overrides these at runtime based on context:

| Field | Override Condition | Applied Color/Attribute |
|---|---|---|
| TRTYPEC (type filter) | FLG-TYPEFILTER-NOT-OK | DFHRED |
| TRTYPEC | WS-ACTIONS-REQUESTED > 0 | DFHBLUE |
| TRDESCC | FLG-DESCFILTER-NOT-OK | DFHRED |
| TRTSELA(I) | WS-CA-EACH-ROW-OUT(I) empty OR FLG-PROTECT-SELECT-ROWS-YES | DFHBMPRO (protected) |
| TRTSELA(I) | WS-ROW-TRTSELECT-ERROR(I) = '1' | DFHRED + cursor positioned |
| TRTTYPC(I) / TRTYPDC(I) | DELETE-REQUESTED-ON(I) | DFHNEUTR |
| TRTYPDA(I) | UPDATE-REQUESTED-ON(I), edit in progress | DFHBMFSE (unprotected) |
| TRTYPDC(I) | UPDATE + row description invalid | DFHRED |
| INFOMSGC | Default | DFHBMDAR (dark, non-display) |
| INFOMSGC | When message set | DFHNEUTR |

---

## 9. Open Questions and Gaps

1. **Row 8 (TRTSELA/TRTTYPA/TRTDSCA at row 19)**: The purpose of an 8th row in a 7-row list is not entirely clear. It may serve as a visual bottom border for the table. The program's `WS-MAX-SCREEN-LINES = 7` confirms only rows 1-7 are data rows.

2. **FKEY label alignment**: F10 is labeled "F10=Save" but the program uses it as a delete/update confirmation key. The label wording may be misleading to users — worth noting for modernization.
