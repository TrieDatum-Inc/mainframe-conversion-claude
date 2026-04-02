# Technical Specification: CORPT00 — Transaction Reports BMS Mapset

## 1. Executive Summary

CORPT00 is a BMS (Basic Mapping Support) mapset definition for the CardDemo transaction report submission screen. It defines a single map, CORPT0A, rendered on a 24-row by 80-column 3270 terminal. The mapset is used exclusively by program CORPT00C under CICS transaction CR00. The screen presents three mutually exclusive report type selectors (Monthly, Yearly, Custom), a custom date range entry section, and a confirmation field. The generated symbolic description copybook is CORPT00.CPY (app/cpy-bms/), which defines CORPT0AI (input) and CORPT0AO (output) structures.

Source file: `app/bms/CORPT00.bms`
Generated copybook: `app/cpy-bms/CORPT00.CPY`
Version stamp: `CardDemo_v1.0-70-g193b394-123 Date: 2022-08-22 17:02:43 CDT`

---

## 2. Artifact Inventory

| Artifact | Type | Location | Role |
|---|---|---|---|
| CORPT00.bms | BMS Source | app/bms/ | Mapset definition |
| CORPT00.CPY | BMS-generated Copybook | app/cpy-bms/ | Symbolic map structures CORPT0AI/O |
| CORPT00C.cbl | CICS COBOL Program | app/cbl/ | Consuming program |

---

## 3. Mapset-Level Definition (DFHMSD)

Source: CORPT00.bms lines 19–25

| Parameter | Value | Meaning |
|---|---|---|
| Name | CORPT00 | Mapset name |
| CTRL | (ALARM,FREEKB) | Sound alarm; free keyboard after send |
| EXTATT | YES | Extended attributes enabled |
| LANG | COBOL | Generate COBOL copybook |
| MODE | INOUT | Bidirectional (send and receive) |
| STORAGE | AUTO | Automatic storage allocation |
| TIOAPFX | YES | 12-byte TIOA prefix in symbolic map |
| TYPE | &&SYSPARM | MAP or DSECT at assembly time |

---

## 4. Map Definition: CORPT0A (DFHMDI)

Source: CORPT00.bms lines 26–28

| Parameter | Value | Meaning |
|---|---|---|
| Name | CORPT0A | Map name for SEND/RECEIVE |
| COLUMN | 1 | Start column 1 |
| LINE | 1 | Start line 1 |
| SIZE | (24,80) | Full 24x80 screen |

---

## 5. Screen Layout

```
Row  Col  1         2         3         4         5         6         7         8
         12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row  1:  Tran: TTTT         [        TITLE01 (40)          ]  Date: MM/DD/YY
Row  2:  Prog: PPPPPPPP     [        TITLE02 (40)          ]  Time: HH:MM:SS
Row  3:  (blank)
Row  4:                              Transaction Reports
Row  5:  (blank)
Row  6:  (blank)
Row  7:           [M]          Monthly (Current Month)
Row  8:  (blank)
Row  9:           [Y]          Yearly (Current Year)
Row 10:  (blank)
Row 11:           [C]          Custom (Date Range)
Row 12:  (blank)
Row 13:               Start Date : [MM]/[DD]/[YYYY]   (MM/DD/YYYY)
Row 14:                 End Date : [MM]/[DD]/[YYYY]   (MM/DD/YYYY)
Row 15:  (blank)
Row 16:  (blank)
Row 17:  (blank)
Row 18:  (blank)
Row 19:       The Report will be submitted for printing. Please confirm:  [C] (Y/N)
Row 20:  (blank)
Row 21:  (blank)
Row 22:  (blank)
Row 23:  [ERRMSG - 78 chars - RED]
Row 24:  ENTER=Continue  F3=Back
```

Legend: `[ ]` = unprotected (input-capable) field; `( )` = static label

---

## 6. Field Inventory

All entries sourced from CORPT00.bms and confirmed against CORPT00.CPY.

### 6.1 Static (ASKIP) Label Fields — No symbolic names

| Row | Col | Length | Color | Content | Attr |
|---|---|---|---|---|---|
| 1 | 1 | 5 | BLUE | 'Tran:' | ASKIP,NORM |
| 1 | 65 | 5 | BLUE | 'Date:' | ASKIP,NORM |
| 2 | 1 | 5 | BLUE | 'Prog:' | ASKIP,NORM |
| 2 | 65 | 5 | BLUE | 'Time:' | ASKIP,NORM |
| 4 | 30 | 19 | NEUTRAL | 'Transaction Reports' | ASKIP,BRT |
| 7 | 15 | 23 | TURQUOISE | 'Monthly (Current Month)' | ASKIP,BRT |
| 9 | 15 | 23 | TURQUOISE | 'Yearly (Current Year)' | ASKIP,BRT |
| 11 | 15 | 23 | TURQUOISE | 'Custom (Date Range)' | ASKIP,BRT |
| 13 | 15 | 12 | TURQUOISE | 'Start Date :' | ASKIP,NORM |
| 13 | 32 | 1 | BLUE | '/' | ASKIP,NORM (date separator) |
| 13 | 37 | 1 | BLUE | '/' | ASKIP,NORM (date separator) |
| 13 | 46 | 12 | BLUE | '(MM/DD/YYYY)' | (no ATTRB specified, inherits default) |
| 14 | 15 | 12 | TURQUOISE | '  End Date :' | ASKIP,NORM |
| 14 | 32 | 1 | BLUE | '/' | ASKIP,NORM (date separator) |
| 14 | 37 | 1 | BLUE | '/' | ASKIP,NORM (date separator) |
| 14 | 46 | 12 | BLUE | '(MM/DD/YYYY)' | (no ATTRB specified) |
| 19 | 6 | 59 | TURQUOISE | 'The Report will be submitted for printing. Please confirm: ' | ASKIP,NORM |
| 19 | 69 | 5 | NEUTRAL | '(Y/N)' | ASKIP,NORM |
| 24 | 1 | 23 | YELLOW | 'ENTER=Continue  F3=Back' | ASKIP,NORM |

### 6.2 Named Symbolic Fields — Header Area

Output-only (ASKIP, FSET) set by CORPT00C POPULATE-HEADER-INFO paragraph.

| BMS Name | Symbolic Name | Row | Col | Length | Color | Purpose |
|---|---|---|---|---|---|---|
| TRNNAME | TRNNAMEI/O | 1 | 7 | 4 | BLUE | Transaction ID (CR00) |
| TITLE01 | TITLE01I/O | 1 | 21 | 40 | YELLOW | Application title line 1 |
| CURDATE | CURDATEI/O | 1 | 71 | 8 | BLUE | Current date (mm/dd/yy) |
| PGMNAME | PGMNAMEI/O | 2 | 7 | 8 | BLUE | Program name (CORPT00C) |
| TITLE02 | TITLE02I/O | 2 | 21 | 40 | YELLOW | Application title line 2 |
| CURTIME | CURTIMEI/O | 2 | 71 | 8 | BLUE | Current time (hh:mm:ss) |

### 6.3 Named Symbolic Fields — Report Selection Area

| BMS Name | Symbolic Name | Row | Col | Length | Color | Attr | HILIGHT | Purpose |
|---|---|---|---|---|---|---|---|---|
| MONTHLY | MONTHLYI/O | 7 | 10 | 1 | GREEN | FSET,IC,NORM,UNPROT | UNDERLINE | Monthly report selector; IC = initial cursor |
| YEARLY | YEARLYI/O | 9 | 10 | 1 | GREEN | FSET,NORM,UNPROT | UNDERLINE | Yearly report selector |
| CUSTOM | CUSTOMI/O | 11 | 10 | 1 | GREEN | FSET,NORM,UNPROT | UNDERLINE | Custom date range selector |

**Design note**: These three selector fields are single-character, unprotected. The program treats any non-blank, non-LOW-VALUES value as a selection. There is no radio-button enforcement at the BMS level; the program logic evaluates them in MONTHLY > YEARLY > CUSTOM priority order (EVALUATE TRUE with WHEN order).

### 6.4 Named Symbolic Fields — Custom Date Range Area

| BMS Name | Symbolic Name | Row | Col | Length | Color | Attr | HILIGHT | Purpose |
|---|---|---|---|---|---|---|---|---|
| SDTMM | SDTMMI/O | 13 | 29 | 2 | GREEN | FSET,NORM,NUM,UNPROT | UNDERLINE | Start date month (2 digits) |
| SDTDD | SDTDDI/O | 13 | 34 | 2 | GREEN | FSET,NORM,NUM,UNPROT | UNDERLINE | Start date day (2 digits) |
| SDTYYYY | SDTYYYYI/O | 13 | 39 | 4 | GREEN | FSET,NORM,NUM,UNPROT | UNDERLINE | Start date year (4 digits) |
| EDTMM | EDTMMI/O | 14 | 29 | 2 | GREEN | FSET,NORM,NUM,UNPROT | UNDERLINE | End date month (2 digits) |
| EDTDD | EDTDDI/O | 14 | 34 | 2 | GREEN | FSET,NORM,NUM,UNPROT | UNDERLINE | End date day (2 digits) |
| EDTYYYY | EDTYYYYI/O | 14 | 39 | 4 | GREEN | FSET,NORM,NUM,UNPROT | UNDERLINE | End date year (4 digits) |

**Design note**: All six date sub-fields have the NUM attribute, meaning the terminal will enforce numeric-only keystrokes. The separating '/' characters between month, day, and year are static ASKIP fields — users tab between the three sub-fields.

### 6.5 Named Symbolic Fields — Confirmation and Messaging

| BMS Name | Symbolic Name | Row | Col | Length | Color | Attr | HILIGHT | Purpose |
|---|---|---|---|---|---|---|---|---|
| CONFIRM | CONFIRMI/O | 19 | 66 | 1 | GREEN | FSET,NORM,UNPROT | UNDERLINE | Y/N confirmation entry |
| ERRMSG | ERRMSGI/O | 23 | 1 | 78 | RED | ASKIP,BRT,FSET | — | Error / status message line |

### 6.6 Stopper Fields (LENGTH=0)

| After Field | Row | Col | Source |
|---|---|---|---|
| After MONTHLY | 7 | 12 | CORPT00.bms line 87 |
| After YEARLY | 9 | 12 | CORPT00.bms line 100 |
| After CUSTOM | 11 | 12 | CORPT00.bms line 114 |
| After SDTYYYY | 13 | 44 | CORPT00.bms line 155 |
| After EDTYYYY | 14 | 44 | CORPT00.bms line 194 |
| After CONFIRM | 19 | 68 | CORPT00.bms line 211 |

---

## 7. Symbolic Map Structures (from CORPT00.CPY)

Source: app/cpy-bms/CORPT00.CPY

### 7.1 Input Structure: CORPT0AI (lines 17–120)

Standard BMS symbolic map pattern with 12-byte TIOA prefix, followed by each named field's L (length), F (flag), A (attribute REDEFINES), 4-byte reserved FILLER, and I (data) sub-fields.

Key input fields used by CORPT00C:

| Field Name | PIC | Length | Usage in CORPT00C |
|---|---|---|---|
| MONTHLYI | PIC X(1) | 1 | Checked at line 213 |
| YEARLYI | PIC X(1) | 1 | Checked at line 239 |
| CUSTOMI | PIC X(1) | 1 | Checked at line 256 |
| SDTMMI | PIC X(2) | 2 | Start month; checked at lines 259, 329 |
| SDTDDI | PIC X(2) | 2 | Start day; checked at lines 266, 338 |
| SDTYYYYI | PIC X(4) | 4 | Start year; checked at lines 273, 347 |
| EDTMMI | PIC X(2) | 2 | End month; checked at lines 280, 355 |
| EDTDDI | PIC X(2) | 2 | End day; checked at lines 287, 364 |
| EDTYYYYI | PIC X(4) | 4 | End year; checked at lines 294, 373 |
| CONFIRMI | PIC X(1) | 1 | Checked at lines 464, 478 |
| ERRMSGI | PIC X(78) | 78 | Not read from user in normal flow |
| MONTHLYL | COMP PIC S9(4) | — | Cursor control (-1 = set cursor here) |
| CONFIRML | COMP PIC S9(4) | — | Cursor control for CONFIRM field |
| (all other L fields) | COMP PIC S9(4) | — | Used for cursor positioning on errors |

### 7.2 Output Structure: CORPT0AO (lines 121–224)

CORPT0AO REDEFINES CORPT0AI. Follows the same extended attribute pattern as COBIL0AO. CORPT00C sets ERRMSGC to DFHGREEN on successful job submission (line 448).

---

## 8. Attribute Byte Reference

| Attribute | Meaning | Applied to |
|---|---|---|
| ASKIP | Protected / auto-skip | All label and output-only fields |
| UNPROT | User-enterable | MONTHLY, YEARLY, CUSTOM, SDTMM, SDTDD, SDTYYYY, EDTMM, EDTDD, EDTYYYY, CONFIRM |
| NUM | Numeric only (terminal enforces digits) | All six date sub-fields (SDTMM, SDTDD, SDTYYYY, EDTMM, EDTDD, EDTYYYY) |
| NORM | Normal intensity | Most input fields |
| BRT | Bright | ERRMSG, screen title 'Transaction Reports', option labels |
| FSET | Always transmit | All named fields |
| IC | Initial cursor | MONTHLY (first cursor position on screen entry) |
| HILIGHT=UNDERLINE | Underline display | MONTHLY, YEARLY, CUSTOM, all date fields, CONFIRM |

---

## 9. Screen Navigation

| Key | Action in CORPT00C |
|---|---|
| ENTER | Validate selection, compute dates, submit job, or prompt for confirmation |
| PF3 | XCTL to COMEN01C (return to menu) |
| Any other key | Display 'Invalid key pressed...' in ERRMSG |

Note: PF4 (Clear) is NOT defined in this mapset's key legend (row 24 shows only ENTER and F3). COBIL00C supports PF4 but CORPT00C does not.

---

## 10. Screen Interaction Sequence

1. First display: cursor on MONTHLY (IC). All input fields blank.
2. User marks one selector field (MONTHLY, YEARLY, or CUSTOM) with any character (typically 'X' or ' ') and presses ENTER.
   - For CUSTOM: also fills in the 6 date sub-fields.
3. If CONFIRM was blank (expected on first pass): program prompts "Please confirm to print the [name] report..." and moves cursor to CONFIRM.
4. User enters 'Y' or 'N' in CONFIRM and presses ENTER.
5. On 'Y': JCL submitted, success message in green at row 23, all fields cleared.
6. On 'N': screen cleared, cursor returns to MONTHLY.
7. Error conditions display red message at row 23 with cursor on offending field.

---

## 11. Mapset Termination

Source: CORPT00.bms line 227
```
DFHMSD TYPE=FINAL
END
```

---

## 12. Open Questions and Gaps

1. **Selector field ambiguity**: If a user enters a value in both MONTHLY (row 7) and YEARLY (row 9), the EVALUATE TRUE in CORPT00C.cbl processes MONTHLY first (line 213), ignoring YEARLY. The BMS has no mechanism to enforce mutual exclusivity between the three selector fields.
2. **SDTMM, SDTDD, SDTYYYY always visible**: The custom date sub-fields (rows 13–14) are visible regardless of whether CUSTOM is selected. They are simply ignored by the program logic if CUSTOM is not selected. There is no dynamic attribute manipulation to show/hide them.
3. **CONFIRM field always visible**: Like the date fields, the CONFIRM prompt at row 19 is permanently visible even on first entry before a report type is selected. Users could fill it in on the first pass, which the program handles correctly (jumping straight to submission).
4. **No PF4 key defined**: Unlike COBIL00, this screen has no clear/reset function. The only way to start over is PF3 (exit) or let the program clear the screen after a successful submission or cancellation.
