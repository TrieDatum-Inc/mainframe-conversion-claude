# Technical Specification: COTRTUP (BMS Mapset)

## 1. Executive Summary

COTRTUP is a **BMS (Basic Mapping Support) mapset** that defines the screen for the Transaction Type Add/Update/Delete detail function of the CardDemo application. It contains a single map, `CTRTUPA`, a 24×80 3270 terminal screen presenting a two-field form (Transaction Type code and Description) with context-sensitive PF key labels. This mapset is used exclusively by program COTRTUPC (transaction `CTTU`). The BMS source file is at `app/app-transaction-type-db2/bms/COTRTUP.bms`; the corresponding COBOL symbolic map copybook is `app/app-transaction-type-db2/cpy-bms/COTRTUP.cpy`.

---

## 2. Mapset Definition

| Attribute | Value | Source |
|---|---|---|
| Mapset name | COTRTUP | BMS `DFHMSD` label, line 20 |
| Language | COBOL | `LANG=COBOL` |
| Mode | Input and Output | `MODE=INOUT` |
| Storage | Automatic | `STORAGE=AUTO` |
| TIOAPFX | YES | `TIOAPFX=YES` |
| Map name | CTRTUPA | BMS `DFHMDI` label, line 25 |
| Screen size | 24 rows × 80 columns | `SIZE=(24,80)` |
| Control | FREEKB | `CTRL=(FREEKB)` — keyboard released on SEND |
| Dynamic attributes | COLOR, HILIGHT, PS, VALIDN | `DSATTS=` and `MAPATTS=` |

---

## 3. Screen Layout (24×80)

```
Row  Col  Content
---  ---  -------
 1    1   'Tran:'  [TRNNAME: 4 chars, blue, ASKIP/FSET]
 1   21   [TITLE01: 40 chars, yellow]
 1   65   'Date:'  [CURDATE: 8 chars, blue, initial='mm/dd/yy']
 2    1   'Prog:'  [PGMNAME: 8 chars, blue]
 2   21   [TITLE02: 40 chars, yellow]
 2   65   'Time:'  [CURTIME: 8 chars, blue, initial='hh:mm:ss']
 7   28   'Maintain Transaction Type'  (neutral, 25 chars)
12    4   'Transaction Type  :'  (turquoise, 19 chars)
12   26   [TRTYPCD: 2 chars, UNPROT, underline, IC]
14    4   'Description       :'  (turquoise, 19 chars)
14   26   [TRTYDSC: 50 chars, UNPROT, underline]
22   23   [INFOMSG: 45 chars, ASKIP, neutral] Informational message
23    1   [ERRMSG: 78 chars, ASKIP/BRT/FSET/red] Error message
24    1   [FKEYS: 21 chars, yellow] 'ENTER=Process F3=Exit'
24   23   [FKEY04: 9 chars, yellow, DRK] 'F4=Delete'
24   33   [FKEY05: 8 chars, yellow, DRK] 'F5=Save'
24   43   [FKEY06: 6 chars, yellow, DRK] 'F6=Add'
24   69   [FKEY12: 10 chars, yellow, DRK] 'F12=Cancel'
```

---

## 4. Field Inventory

### 4.1 Header Fields (rows 1-2)

| BMS Name | Row | Col | Len | ATTRB | Color | Hilight | Description |
|---|---|---|---|---|---|---|---|
| (literal) | 1 | 1 | 5 | ASKIP,NORM | BLUE | — | 'Tran:' |
| TRNNAME | 1 | 7 | 4 | ASKIP,FSET,NORM | BLUE | — | Transaction ID (output: 'CTTU') |
| TITLE01 | 1 | 21 | 40 | ASKIP,NORM | YELLOW | — | Application title line 1 |
| (literal) | 1 | 65 | 5 | ASKIP,NORM | BLUE | — | 'Date:' |
| CURDATE | 1 | 71 | 8 | ASKIP,NORM | BLUE | — | Current date; initial='mm/dd/yy' |
| (literal) | 2 | 1 | 5 | ASKIP,NORM | BLUE | — | 'Prog:' |
| PGMNAME | 2 | 7 | 8 | ASKIP,NORM | BLUE | — | Program name (output: 'COTRTUPC') |
| TITLE02 | 2 | 21 | 40 | ASKIP,NORM | YELLOW | — | Application title line 2 |
| (literal) | 2 | 65 | 5 | ASKIP,NORM | BLUE | — | 'Time:' |
| CURTIME | 2 | 71 | 8 | ASKIP,NORM | BLUE | — | Current time; initial='hh:mm:ss' |

### 4.2 Screen Heading (row 7)

| BMS Name | Row | Col | Len | ATTRB | Color | Description |
|---|---|---|---|---|---|---|
| (literal) | 7 | 28 | 25 | — | NEUTRAL | 'Maintain Transaction Type' |

### 4.3 Data Entry Fields (rows 12, 14)

| BMS Name | Row | Col | Len | ATTRB | Hilight | Initial Cursor | Description |
|---|---|---|---|---|---|---|---|
| (literal) | 12 | 4 | 19 | ASKIP,NORM | — | — | 'Transaction Type  :' label (turquoise) |
| TRTYPCD | 12 | 26 | 2 | IC,UNPROT | UNDERLINE | Yes (IC) | Transaction type code — 2-char alphanumeric |
| (literal) | 14 | 4 | 19 | — | — | — | 'Description       :' label (turquoise) |
| TRTYDSC | 14 | 26 | 50 | UNPROT | UNDERLINE | No | Transaction type description — 50-char |

**Symbolic map field names from COTRTUP.cpy**:

| Symbolic Name | PIC | Description |
|---|---|---|
| TRTYPCDL | PIC S9(4) COMP | Length of TRTYPCD data |
| TRTYPCDF / TRTYPCDA | PIC X | Attribute byte for TRTYPCD |
| TRTYPCDI / TRTYPCDO | PIC X(2) | Transaction type code input/output |
| TRTYDSCL | PIC S9(4) COMP | Length of TRTYDSC data |
| TRTYDSCF / TRTYDSCA | PIC X | Attribute byte for TRTYDSC |
| TRTYDSCI / TRTYDSCO | PIC X(50) | Description input/output |
| INFOMSGL | PIC S9(4) COMP | Length of INFOMSG data |
| INFOMSGF / INFOMSGA | PIC X | Attribute byte |
| INFOMSGI / INFOMSGO | PIC X(45) | Informational message |
| ERRMSGL | PIC S9(4) COMP | Length of ERRMSG data |
| ERRMSGF / ERRMSGA | PIC X | Attribute byte |
| ERRMSGI / ERRMSGO | PIC X(78) | Error message |
| FKEYSL / FKEYSF / FKEYSA | — | FKEYS label attr |
| FKEY04L / FKEY04F / FKEY04A | — | F4 label attr |
| FKEY05L / FKEY05F / FKEY05A | — | F5 label attr |
| FKEY12L / FKEY12F / FKEY12A | — | F12 label attr |

> Note: FKEY06 (F6=Add) is defined in the BMS but no corresponding attribute manipulation was observed in COTRTUPC source. It appears to be a placeholder or legacy label. The add function is triggered by COTRTUPC detecting a not-found key and offering PF05.

### 4.4 Message Fields (rows 22, 23)

| BMS Name | Row | Col | Len | ATTRB | Color | Description |
|---|---|---|---|---|---|---|
| INFOMSG | 22 | 23 | 45 | ASKIP | NEUTRAL | Instructional or status message (center-justified by program) |
| ERRMSG | 23 | 1 | 78 | ASKIP,BRT,FSET | RED | Error message (bright red) |

### 4.5 PF Key Labels (row 24)

| BMS Name | Col | Len | ATTRB | Color | Initial Value | Runtime Behavior |
|---|---|---|---|---|---|---|
| FKEYS | 1 | 21 | ASKIP,NORM | YELLOW | 'ENTER=Process F3=Exit' | Always visible |
| FKEY04 | 23 | 9 | ASKIP,DRK | YELLOW | 'F4=Delete' | Initially dark (hidden); bright when state = TTUP-SHOW-DETAILS or TTUP-CONFIRM-DELETE |
| FKEY05 | 33 | 8 | ASKIP,DRK | YELLOW | 'F5=Save' | Initially dark; bright when TTUP-CHANGES-OK-NOT-CONFIRMED or TTUP-DETAILS-NOT-FOUND |
| FKEY06 | 43 | 6 | ASKIP,DRK | YELLOW | 'F6=Add' | Always dark (no program activation observed) |
| FKEY12 | 69 | 10 | ASKIP,DRK | YELLOW | 'F12=Cancel' | Initially dark; bright when cancel is valid |

The `DRK` attribute makes labels invisible until COTRTUPC dynamically sets their attribute bytes to DFHBMASB (bright) via paragraph `3391-SETUP-PFKEY-ATTRS`.

---

## 5. Symbolic Map Structure (from COTRTUP.cpy)

The copybook defines `CTRTUPAI` (input) and `CTRTUPAO` (output). The full input structure (01 CTRTUPAI) begins at line 17 of COTRTUP.cpy. Key sections:

```
01 CTRTUPAI.
   02 FILLER         PIC X(12).          -- TIOAPFX
   02 TRNNAMEL/F/A/I                     -- Transaction name (4)
   02 TITLE01L/F/A/I                     -- Title 1 (40)
   02 CURDATEL/F/A/I                     -- Date (8)
   02 PGMNAMEL/F/A/I                     -- Program name (8)
   02 TITLE02L/F/A/I                     -- Title 2 (40)
   02 CURTIMEL/F/A/I                     -- Time (8)
   02 TRTYPCDL COMP PIC S9(4)            -- Length for type code
   02 TRTYPCDF PIC X                     -- Attribute byte
   02 FILLER REDEFINES TRTYPCDF
      03 TRTYPCDA PIC X                  -- Attribute byte (settable)
   02 FILLER PIC X(4)                    -- Skip bytes
   02 TRTYPCDI PIC X(2)                  -- Type code input
   02 TRTYDSCL COMP PIC S9(4)            -- Length for description
   02 TRTYDSCF PIC X                     -- Attribute byte
   02 FILLER REDEFINES TRTYDSCF
      03 TRTYDSCA PIC X                  -- Attribute byte (settable)
   02 FILLER PIC X(4)                    -- Skip bytes
   02 TRTYDSCI PIC X(50)                 -- Description input
   02 INFOMSGL/F/A/I (45)               -- Info message
   02 ERRMSGL/F/A/I (78)                -- Error message
   02 FKEYSL/F/A                         -- FKEYS label attr
   02 FKEY04L/F/A                        -- F4 label attr
   02 FKEY05L/F/A                        -- F5 label attr
   02 FKEY06L/F/A                        -- F6 label attr
   02 FKEY12L/F/A                        -- F12 label attr
```

---

## 6. Program That Uses This Mapset

| Program | Transaction | Receives Map | Sends Map |
|---|---|---|---|
| COTRTUPC | CTTU | `EXEC CICS RECEIVE MAP('CTRTUPA') MAPSET('COTRTUP') INTO(CTRTUPAI)` | `EXEC CICS SEND MAP(CCARD-NEXT-MAP) MAPSET(CCARD-NEXT-MAPSET) FROM(CTRTUPAO) CURSOR ERASE FREEKB` |

---

## 7. Dynamic Attribute Behavior at Runtime

COTRTUPC modifies field attributes dynamically based on the program's state machine (TTUP-CHANGE-ACTION). The table below summarizes the key dynamic behaviors:

| Field | State | Applied Attribute | Effect |
|---|---|---|---|
| TRTYPCD (TRTYPCDA) | Search states (NOT-FETCHED, INVALID-KEYS, NOT-FOUND, NOT-SEARCHED) | DFHBMFSE | Editable (unprotected) |
| TRTYPCD (TRTYPCDA) | Edit/Confirm states | DFHBMPRF | Protected (display-only) |
| TRTYPCD | Cursor positioning (TRTYPCDL = -1) | Cursor here | When entering search key |
| TRTYDSC (TRTYDSCA) | TTUP-SHOW-DETAILS, TTUP-CHANGES-NOT-OK, TTUP-CREATE-NEW-RECORD, TTUP-CHANGES-BACKED-OUT | DFHBMFSE | Editable |
| TRTYDSC (TRTYDSCA) | All other states | DFHBMPRF | Protected |
| TRTYDSC | Cursor positioning (TRTYDSCL = -1) | Cursor here | When editing description |
| TRTYPCDC | FLG-TRANFILTER-NOT-OK or TTUP-DELETE-FAILED | DFHRED | Red error color |
| TRTYDSC via CSSETATY | FLG-DESCRIPTION-NOT-OK | (from CSSETATY template) | Red/error color on desc |
| INFOMSGA | WS-NO-INFO-MESSAGE | DFHBMDAR | Dark (info not shown) |
| INFOMSGA | Info message present | DFHBMASB | Bright |
| FKEYS (FKEYSA) | TTUP-CONFIRM-DELETE | DFHBMDAR | ENTER label hidden |
| FKEY04A | TTUP-SHOW-DETAILS or TTUP-CONFIRM-DELETE | DFHBMASB | F4=Delete visible |
| FKEY05A | TTUP-CHANGES-OK-NOT-CONFIRMED or TTUP-DETAILS-NOT-FOUND | DFHBMASB | F5=Save visible |
| FKEY12A | Various cancel-valid states | DFHBMASB | F12=Cancel visible |

---

## 8. Screen Usage Scenarios

### 8.1 Initial Entry (Search Mode)

- TRTYPCD: unprotected, cursor positioned here
- TRTYDSC: protected (blank)
- INFOMSG: 'Enter transaction type to be maintained'
- ERRMSG: blank
- PF labels: only ENTER and F3 visible

### 8.2 Record Found (View/Edit Mode)

- TRTYPCD: protected, shows the fetched type code
- TRTYDSC: unprotected, shows fetched description, cursor positioned here
- INFOMSG: 'Selected transaction type shown above'
- PF labels: ENTER, F3=Exit, F4=Delete, F12=Cancel visible

### 8.3 Delete Confirmation Mode

- TRTYPCD: protected
- TRTYDSC: protected
- INFOMSG: 'Delete this record ? Press F4 to confirm'
- ERRMSG: blank
- PF labels: F4=Delete (confirm), F12=Cancel; ENTER label hidden

### 8.4 Changes Validated, Awaiting Save

- TRTYPCD: protected
- TRTYDSC: protected (showing new value)
- INFOMSG: 'Changes validated.Press F5 to save'
- PF labels: F5=Save, F12=Cancel visible

### 8.5 New Record Entry Mode

- TRTYPCD: protected (showing key not found)
- TRTYDSC: unprotected (blank for input)
- INFOMSG: 'Enter new transaction type details.'
- PF labels: F5=Save, F12=Cancel visible

---

## 9. Navigation Flow

```
[COTRTLI screen (COTRTLIC)]
         |
         | PF02=Add (from list) or selection for edit
         v
  [COTRTUP / CTRTUPA]  <--- COTRTUPC (trans CTTU)
         |
         | PF03=Exit
         v
  [Calling program (COTRTLIC or COADM01C)]
```

---

## 10. Open Questions and Gaps

1. **FKEY06 (F6=Add)**: Defined in the BMS at position (24,43) with initial value 'F6=Add' and attribute DRK. No evidence in COTRTUPC source of this key being activated or handled. It may be a design relic or planned for future use.

2. **Row 7 screen heading placement**: The 'Maintain Transaction Type' heading is at row 7 (center), leaving rows 3-6 and 8-11 entirely empty. The wide vertical spacing is intentional for visual centering of the two-field form between rows 12 and 14.

3. **No NUMERIC attribute on TRTYPCD**: Although the type code is validated as numeric by the program, the BMS field does not have a `NUM` attribute. Numeric validation is entirely software-enforced in COTRTUPC paragraph `1245-EDIT-NUM-REQD`.
