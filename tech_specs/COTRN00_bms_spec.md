# Technical Specification: COTRN00 BMS Mapset — Transaction List Screen

## 1. Executive Summary

COTRN00 is a BMS (Basic Mapping Support) mapset definition for the CardDemo Transaction List screen. It defines a single physical map (COTRN0A) that presents a paginated 10-row list of transactions with selection, search filter, and page navigation capabilities. The screen is used exclusively by program COTRN00C (transaction CT00).

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COTRN00.BMS | BMS macro source | app/bms/COTRN00.bms |
| COTRN00.CPY | Generated symbolic description copybook | app/cpy-bms/COTRN00.CPY |
| COTRN00C.CBL | Owning CICS program | app/cbl/COTRN00C.cbl |

---

## 3. Mapset Definition

| Parameter | Value | Meaning |
|---|---|---|
| Mapset name | COTRN00 | CICS resource definition name |
| CTRL | (ALARM,FREEKB) | Sound alarm on send; free keyboard after send |
| EXTATT | YES | Extended attributes (color, highlight) enabled |
| LANG | COBOL | Generated copybook language |
| MODE | INOUT | Both input and output symbolic maps generated |
| STORAGE | AUTO | Separate storage for each map in mapset |
| TIOAPFX | YES | 12-byte TIOA prefix included in symbolic map |
| TYPE | &&SYSPARM | Assembly type controlled by job parameter |

---

## 4. Map Definition

| Parameter | Value |
|---|---|
| Map name | COTRN0A |
| COLUMN | 1 |
| LINE | 1 |
| SIZE | (24, 80) — 24 rows by 80 columns |

---

## 5. Screen Layout

```
Col:  1         10        20        30        40        50        60        70        80
      |---------|---------|---------|---------|---------|---------|---------|---------|
R01:  Tran: TTTT         [      TITLE01 (40)       ]         Date: mm/dd/yy
R02:  Prog: PPPPPPPP     [      TITLE02 (40)       ]         Time: hh:mm:ss
R03:  (blank)
R04:                               List Transactions          Page: NNNNNNNN
R05:  (blank)
R06:      Search Tran ID: [TRNIDINI_______________ ]
R07:  (blank)
R08:   Sel  Transaction ID    Date      Description               Amount
R09:   ---  ----------------  --------  --------------------------  ------------
R10:   _ [TRNID01__________] [TDATE01] [TDESC01__________________] [TAMT001___]
R11:   _ [TRNID02__________] [TDATE02] [TDESC02__________________] [TAMT002___]
R12:   _ [TRNID03__________] [TDATE03] [TDESC03__________________] [TAMT003___]
R13:   _ [TRNID04__________] [TDATE04] [TDESC04__________________] [TAMT004___]
R14:   _ [TRNID05__________] [TDATE05] [TDESC05__________________] [TAMT005___]
R15:   _ [TRNID06__________] [TDATE06] [TDESC06__________________] [TAMT006___]
R16:   _ [TRNID07__________] [TDATE07] [TDESC07__________________] [TAMT007___]
R17:   _ [TRNID08__________] [TDATE08] [TDESC08__________________] [TAMT008___]
R18:   _ [TRNID09__________] [TDATE09] [TDESC09__________________] [TAMT009___]
R19:   _ [TRNID10__________] [TDATE10] [TDESC10__________________] [TAMT010___]
R20:  (blank)
R21:             Type 'S' to View Transaction details from the list
R22:  (blank)
R23:  [ERRMSG______________________________________________________________ (78)]
R24:  ENTER=Continue  F3=Back  F7=Backward  F8=Forward
```

Legend: `_` = UNPROT input field, `[ ]` = ASKIP/protected display field, `TTTT` = transaction name, `PPPPPPPP` = program name.

---

## 6. Field Definitions

### Header Fields (Row 1)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Tran:') | (1,1) | 5 | ASKIP,NORM | BLUE | Label |
| TRNNAME | (1,7) | 4 | ASKIP,FSET,NORM | BLUE | Transaction ID ('CT00') |
| TITLE01 | (1,21) | 40 | ASKIP,FSET,NORM | YELLOW | App title line 1 |
| (literal 'Date:') | (1,65) | 5 | ASKIP,NORM | BLUE | Label |
| CURDATE | (1,71) | 8 | ASKIP,FSET,NORM | BLUE | Current date (MM/DD/YY) |

### Header Fields (Row 2)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Prog:') | (2,1) | 5 | ASKIP,NORM | BLUE | Label |
| PGMNAME | (2,7) | 8 | ASKIP,FSET,NORM | BLUE | Program name ('COTRN00C') |
| TITLE02 | (2,21) | 40 | ASKIP,FSET,NORM | YELLOW | App title line 2 |
| (literal 'Time:') | (2,65) | 5 | ASKIP,NORM | BLUE | Label |
| CURTIME | (2,71) | 8 | ASKIP,FSET,NORM | BLUE | Current time (HH:MM:SS) |

### Title and Page Bar (Row 4)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'List Transactions') | (4,30) | 17 | ASKIP,BRT | NEUTRAL | Screen function title |
| (literal 'Page:') | (4,65) | 5 | ASKIP,BRT | TURQUOISE | Label |
| PAGENUM | (4,71) | 8 | ASKIP,FSET,NORM | BLUE | Current page number |

### Search Filter (Row 6)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Highlight | Description |
|---|---|---|---|---|---|---|
| (literal 'Search Tran ID:') | (6,5) | 15 | ASKIP,NORM | TURQUOISE | — | Label |
| TRNIDIN | (6,21) | 16 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Search Transaction ID input |
| (stopper) | (6,38) | 0 | ASKIP,NORM | — | — | Field terminator |

### Column Headers (Rows 8–9)

All label literals at rows 8 and 9 use ATTRB=(ASKIP,NORM) COLOR=NEUTRAL. Row 9 contains separator dashes.

| Literal | POS | Content |
|---|---|---|
| Column header 1 | (8,2) | 'Sel' |
| Column header 2 | (8,8) | ' Transaction ID ' |
| Column header 3 | (8,27) | '  Date  ' |
| Column header 4 | (8,38) | '     Description          ' |
| Column header 5 | (8,67) | '   Amount   ' |

### Transaction Data Rows (Rows 10–19)

Ten identical row groups, one per transaction. Pattern shown for row 1 (SEL0001, TRNID01, etc.); rows 2–10 follow the same layout at consecutive row numbers.

| Field Name | POS | Length | ATTRB | Color | Highlight | Description |
|---|---|---|---|---|---|---|
| SEL0001 | (10,3) | 1 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Selection character (enter 'S') |
| (stopper) | (10,5) | 0 | ASKIP,NORM | — | — | Field terminator |
| TRNID01 | (10,8) | 16 | ASKIP,FSET,NORM | BLUE | — | Transaction ID (display only) |
| TDATE01 | (10,27) | 8 | ASKIP,FSET,NORM | BLUE | — | Transaction date MM/DD/YY |
| TDESC01 | (10,38) | 26 | ASKIP,FSET,NORM | BLUE | — | Description (first 26 chars) |
| TAMT001 | (10,67) | 12 | ASKIP,FSET,NORM | BLUE | — | Amount (+/-99999999.99) |

Rows 11–19 (SEL0002–SEL0010, TRNID02–TRNID10, etc.) occupy screen rows 11 through 19 with identical attributes and the row number incrementing by 1 for each group.

### Instruction Line (Row 21)

| Literal | POS | Length | ATTRB | Color |
|---|---|---|---|---|
| "Type 'S' to View Transaction details from the list" | (21,12) | 50 | ASKIP,BRT | NEUTRAL |

### Error/Message Line (Row 23)

| Field Name | POS | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| ERRMSG | (23,1) | 78 | ASKIP,BRT,FSET | RED | Error or status message |

### Function Key Legend (Row 24)

| Literal | POS | Length | ATTRB | Color |
|---|---|---|---|---|
| 'ENTER=Continue  F3=Back  F7=Backward  F8=Forward' | (24,1) | 48 | ASKIP,NORM | YELLOW |

---

## 7. Input Fields Summary

| Field | Row,Col | Len | Editable | Description |
|---|---|---|---|---|
| TRNIDIN | 6,21 | 16 | Yes | Search/filter starting Transaction ID |
| SEL0001–SEL0010 | 10,3 – 19,3 | 1 each | Yes | Row selection (enter 'S') |

All other named fields are ASKIP (auto-skip, protected) and serve as display-only output.

---

## 8. Output-Only Fields Summary

| Field Group | Row Range | Fields |
|---|---|---|
| Header | 1–2 | TRNNAME, TITLE01, CURDATE, PGMNAME, TITLE02, CURTIME |
| Page | 4 | PAGENUM |
| Row data (×10) | 10–19 | TRNID01–10, TDATE01–10, TDESC01–10, TAMT001–010 |
| Error | 23 | ERRMSG |

---

## 9. Symbolic Map Fields in COTRN00.CPY

The generated copybook creates COTRN0AI (input) and COTRN0AO (output, REDEFINES COTRN0AI). Each named field generates:
- `fieldnameL` — COMP PIC S9(4): field length (for cursor positioning, set to -1 for cursor)
- `fieldnameF` / `fieldnameA` — PICTURE X: attribute byte (input map)
- `fieldnameI` — PIC X(n): data value (input map)
- `fieldnameC/P/H/V` — PICTURE X: color/protected/highlight/validation (output map)
- `fieldnameO` — PIC X(n): data value (output map)

---

## 10. BMS Attribute Reference

| ATTRB Value | Meaning |
|---|---|
| ASKIP | Auto-skip (protected, cursor skips field) |
| UNPROT | Unprotected (user can type in field) |
| FSET | Field Set — field is always transmitted on RECEIVE |
| NORM | Normal intensity |
| BRT | Bright (highlighted) intensity |
| IC | Initial Cursor — cursor positioned here on initial SEND |

| Color Value | Terminal Display |
|---|---|
| BLUE | Blue |
| YELLOW | Yellow |
| TURQUOISE | Turquoise/Cyan |
| GREEN | Green |
| NEUTRAL | Default terminal color |
| RED | Red (used for error messages) |

---

## 11. Program Usage

COTRN00C uses this mapset as follows:

| Operation | CICS Command | Map | Mapset |
|---|---|---|---|
| Display list | EXEC CICS SEND MAP('COTRN0A') MAPSET('COTRN00') FROM(COTRN0AO) ERASE CURSOR | COTRN0A | COTRN00 |
| Display without erase | EXEC CICS SEND MAP('COTRN0A') MAPSET('COTRN00') FROM(COTRN0AO) CURSOR | COTRN0A | COTRN00 |
| Read operator input | EXEC CICS RECEIVE MAP('COTRN0A') MAPSET('COTRN00') INTO(COTRN0AI) | COTRN0A | COTRN00 |

---

## 12. Version and Change History

Source version stamp: `CardDemo_v1.0-70-g193b394-123  Date: 2022-08-22 17:02:43 CDT`
