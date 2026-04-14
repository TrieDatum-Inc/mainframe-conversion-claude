# COBIL00 — Bill Payment Screen Technical Specification

## 1. Screen Overview

**Purpose:** Allows a cardholder (or operator acting on their behalf) to pay the current balance on a credit card account. The operator enters an Account ID to retrieve the current balance, then confirms or declines the payment. A Y/N confirmation field prevents accidental payments.

**Driving Program:** COBIL00C (Bill Payment program)

**Source File:** `/app/bms/COBIL00.bms`
**Copybook:** `/app/cpy-bms/COBIL00.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COBIL00           |
| MAP name     | COBIL0A           |
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

---

## 3. Screen Layout (ASCII Representation)

```
Col:  1         2         3         4         5         6         7         8
      12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row1: Tran:[TRNM]          [----------TITLE01----------]     Date:[CURDATE-]
Row2: Prog:[PGMNAME]       [----------TITLE02----------]     Time:[CURTIME-]
Row3:
Row4:                                    Bill Payment
Row5:
Row6:      Enter Acct ID:[ACTIDIN---]
Row7:
Row8:      -------------------------------------------------------------------
Row9:
Row10:
Row11:      Your current balance is:  [CURBAL--------]
Row12:
Row13:
Row14:
Row15:      Do you want to pay your balance now. Please confirm:  [C] (Y/N)
Row16:
Row17:
Row18:
Row19:
Row20:
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Continue  F3=Back  F4=Clear
```

---

## 4. Field Definitions

### Header Fields (rows 1–2)

| Field Name | Row | Col | Length | ATTRB           | Color  | I/O | Notes                         |
|------------|-----|-----|--------|-----------------|--------|-----|-------------------------------|
| (label)    | 1   | 1   | 5      | ASKIP,NORM      | BLUE   | O   | `Tran:`                       |
| TRNNAME    | 1   | 7   | 4      | ASKIP,FSET,NORM | BLUE   | O   | Transaction name               |
| TITLE01    | 1   | 21  | 40     | ASKIP,FSET,NORM | YELLOW | O   | Title line 1                   |
| (label)    | 1   | 65  | 5      | ASKIP,NORM      | BLUE   | O   | `Date:`                        |
| CURDATE    | 1   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current date; init `mm/dd/yy`  |
| (label)    | 2   | 1   | 5      | ASKIP,NORM      | BLUE   | O   | `Prog:`                        |
| PGMNAME    | 2   | 7   | 8      | ASKIP,FSET,NORM | BLUE   | O   | Program name                   |
| TITLE02    | 2   | 21  | 40     | ASKIP,FSET,NORM | YELLOW | O   | Title line 2                   |
| (label)    | 2   | 65  | 5      | ASKIP,NORM      | BLUE   | O   | `Time:`                        |
| CURTIME    | 2   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current time; init `hh:mm:ss`  |

### Screen Title (row 4)

| Row | Col | Length | Content        | ATTRB     | Color   |
|-----|-----|--------|----------------|-----------|---------|
| 4   | 35  | 12     | `Bill Payment` | ASKIP,BRT | NEUTRAL |

### Account Entry (row 6)

| Field Name | Row | Col | Length | ATTRB               | Color | Hilight   | I/O   | Notes                               |
|------------|-----|-----|--------|---------------------|-------|-----------|-------|-------------------------------------|
| (label)    | 6   | 6   | 14     | ASKIP,NORM          | GREEN | —         | O     | `Enter Acct ID:`                    |
| ACTIDIN    | 6   | 21  | 11     | FSET,IC,NORM,UNPROT | GREEN | UNDERLINE | Input | Account ID entered by operator; IC  |
| (stopper)  | 6   | 33  | 0      | ASKIP,NORM          | —     | —         | —     | Tab stop                            |

### Separator (row 8)

| Row | Col | Length | Content       | Color  |
|-----|-----|--------|---------------|--------|
| 8   | 6   | 70     | 70 dashes `---...---` | YELLOW |

### Balance Display (row 11)

| Field Name | Row | Col | Length | ATTRB           | Color | I/O | Notes                               |
|------------|-----|-----|--------|-----------------|-------|-----|-------------------------------------|
| (label)    | 11  | 6   | 25     | ASKIP,NORM      | TURQUOISE| O | `Your current balance is: `       |
| CURBAL     | 11  | 32  | 14     | ASKIP,FSET,NORM | BLUE  | O   | Current balance — output only; populated after account lookup |
| (stopper)  | 11  | 47  | 0      | —               | —     | —   |                                     |

### Confirmation Field (row 15)

| Field Name | Row | Col | Length | ATTRB          | Color | Hilight   | I/O   | Notes                                         |
|------------|-----|-----|--------|----------------|-------|-----------|-------|-----------------------------------------------|
| (prompt)   | 15  | 6   | 53     | ASKIP,NORM     | TURQUOISE| —      | O     | `Do you want to pay your balance now. Please confirm: ` |
| CONFIRM    | 15  | 60  | 1      | FSET,NORM,UNPROT | GREEN | UNDERLINE | Input | Y or N; operator confirms payment             |
| (stopper)  | 15  | 62  | 0      | —              | —     | —         | —     | Tab stop                                      |
| (hint)     | 15  | 63  | 5      | ASKIP,NORM     | NEUTRAL| —         | O     | `(Y/N)` hint                                  |

### Message and Navigation (rows 23–24)

| Field Name | Row | Col | Length | ATTRB          | Color  | I/O | Notes                              |
|------------|-----|-----|--------|----------------|--------|-----|------------------------------------|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED    | O   | Error/status message               |
| (fkeys)    | 24  | 1   | 33     | ASKIP,NORM     | YELLOW | O   | `ENTER=Continue  F3=Back  F4=Clear`|

---

## 5. Generated Copybook Structure (COBIL00.CPY)

### Input Structure: COBIL0AI

| Input Field | COBOL Name  | PIC       | Notes                               |
|-------------|-------------|-----------|-------------------------------------|
| TRNNAME     | TRNNAMEI    | PIC X(4)  | Transaction ID                      |
| TITLE01     | TITLE01I    | PIC X(40) | Title line 1                        |
| CURDATE     | CURDATEI    | PIC X(8)  | Date                                |
| PGMNAME     | PGMNAMEI    | PIC X(8)  | Program name                        |
| TITLE02     | TITLE02I    | PIC X(40) | Title line 2                        |
| CURTIME     | CURTIMEI    | PIC X(8)  | Time                                |
| ACTIDIN     | ACTIDINI    | PIC X(11) | Account ID entered by operator      |
| CURBAL      | CURBALI     | PIC X(14) | Current balance (output-retransmit) |
| CONFIRM     | CONFIRMI    | PIC X(1)  | Y/N confirmation                    |
| ERRMSG      | ERRMSGI     | PIC X(78) | Error message                       |

### Output Structure: COBIL0AO (REDEFINES COBIL0AI)

Standard C/P/H/V/O sub-fields per named field.

---

## 6. Two-Phase Interaction Pattern

COBIL00 operates in two phases:

**Phase 1 — Account Lookup:**
1. Operator enters Account ID in ACTIDIN
2. Presses ENTER
3. Program reads ACTIDINI, fetches account record
4. Program populates CURBALO with formatted balance
5. Map re-sent with balance displayed; CONFIRM field becomes active

**Phase 2 — Payment Confirmation:**
1. Operator types Y in CONFIRM and presses ENTER
2. Program reads CONFIRMI
3. If Y: executes payment transaction, updates balance, displays success in ERRMSG
4. If N: clears form and re-displays
5. PF4 clears ACTIDIN and CURBAL, returning to Phase 1

---

## 7. Screen Navigation

| Key   | Action                                                              |
|-------|---------------------------------------------------------------------|
| ENTER | Phase 1: look up account. Phase 2: process payment if CONFIRM=Y    |
| PF3   | Return to previous screen (main menu)                               |
| PF4   | Clear the form (reset ACTIDIN and CURBAL fields)                    |

---

## 8. Validation Rules

| Field   | BMS Constraint          | Program-Level Validation                              |
|---------|-------------------------|-------------------------------------------------------|
| ACTIDIN | Length=11, UNPROT, FSET | Must not be blank; must match existing account record |
| CONFIRM | Length=1, UNPROT, FSET  | Must be Y or N; program rejects other values          |

---

## 9. Related Screens

| Screen  | Mapset  | Relationship                                    |
|---------|---------|-------------------------------------------------|
| COMEN01 | COMEN01 | Navigate FROM (bill payment menu option)        |
