# CORPT00 — Transaction Reports Screen Technical Specification

## 1. Screen Overview

**Purpose:** Provides a report generation request form. The operator selects a report type (Monthly, Yearly, or Custom date range) and optionally specifies start/end dates for the custom range. A confirmation field (Y/N) prevents accidental report submission. Reports are submitted for batch printing.

**Driving Program:** CORPT00C (Transaction Reports program)

**Source File:** `/app/bms/CORPT00.bms`
**Copybook:** `/app/cpy-bms/CORPT00.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | CORPT00           |
| MAP name     | CORPT0A           |
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
Row4:                                  Transaction Reports
Row5:
Row6:
Row7:          [M]    Monthly (Current Month)
Row8:
Row9:          [Y]    Yearly (Current Year)
Row10:
Row11:         [C]    Custom (Date Range)
Row12:
Row13:               Start Date : [MM]/[DD]/[YYYY] (MM/DD/YYYY)
Row14:                 End Date : [MM]/[DD]/[YYYY] (MM/DD/YYYY)
Row15:
Row16:
Row17:
Row18:
Row19:      The Report will be submitted for printing. Please confirm:  [C] (Y/N)
Row20:
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Continue  F3=Back
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

| Row | Col | Length | Content                 | ATTRB     | Color   |
|-----|-----|--------|-------------------------|-----------|---------|
| 4   | 30  | 19     | `Transaction Reports`   | ASKIP,BRT | NEUTRAL |

### Report Type Selection Fields (rows 7–11)

Each report type has a 1-character checkbox-style input field and a label:

| Field Name | Row | Col | Length | ATTRB               | Color | Hilight   | I/O   | Notes                                         |
|------------|-----|-----|--------|---------------------|-------|-----------|-------|-----------------------------------------------|
| MONTHLY    | 7   | 10  | 1      | FSET,IC,NORM,UNPROT | GREEN | UNDERLINE | Input | Monthly report selector; IC — cursor starts here; init space |
| (stopper)  | 7   | 12  | 0      | ASKIP,NORM          | —     | —         | —     | Tab stop                                      |
| (label)    | 7   | 15  | 23     | ASKIP,BRT           | TURQUOISE | —     | O     | `Monthly (Current Month)`                     |
| YEARLY     | 9   | 10  | 1      | FSET,NORM,UNPROT    | GREEN | UNDERLINE | Input | Yearly report selector; init space            |
| (stopper)  | 9   | 12  | 0      | ASKIP,NORM          | —     | —         | —     | Tab stop                                      |
| (label)    | 9   | 15  | 23     | ASKIP,BRT           | TURQUOISE | —     | O     | `Yearly (Current Year)`                       |
| CUSTOM     | 11  | 10  | 1      | FSET,NORM,UNPROT    | GREEN | UNDERLINE | Input | Custom date range selector; init space        |
| (stopper)  | 11  | 12  | 0      | ASKIP,NORM          | —     | —         | —     | Tab stop                                      |
| (label)    | 11  | 15  | 23     | ASKIP,BRT           | TURQUOISE | —     | O     | `Custom (Date Range)`                         |

**Usage pattern:** The operator types a non-blank character (e.g., `X` or `Y`) in one of the three checkbox fields. The program reads back all three selectors and determines which report type was chosen. Only one should be set; the program enforces mutual exclusivity.

### Custom Date Range (rows 13–14)

#### Start Date (row 13)

| Field Name | Row | Col | Length | ATTRB                    | Color | Hilight   | I/O   | Notes                    |
|------------|-----|-----|--------|--------------------------|-------|-----------|-------|--------------------------|
| (label)    | 13  | 15  | 12     | ASKIP,NORM               | TURQUOISE| —      | O     | `Start Date :`           |
| SDTMM      | 13  | 29  | 2      | FSET,NORM,NUM,UNPROT     | GREEN | UNDERLINE | Input | Start month (MM); NUM    |
| (sep)      | 13  | 32  | 1      | ASKIP,NORM               | BLUE  | —         | O     | `/`                      |
| SDTDD      | 13  | 34  | 2      | FSET,NORM,NUM,UNPROT     | GREEN | UNDERLINE | Input | Start day (DD); NUM      |
| (sep)      | 13  | 37  | 1      | ASKIP,NORM               | BLUE  | —         | O     | `/`                      |
| SDTYYYY    | 13  | 39  | 4      | FSET,NORM,NUM,UNPROT     | GREEN | UNDERLINE | Input | Start year (YYYY); NUM   |
| (stopper)  | 13  | 44  | 0      | —                        | —     | —         | —     |                          |
| (hint)     | 13  | 46  | 12     | (default)                | BLUE  | —         | O     | `(MM/DD/YYYY)`           |

#### End Date (row 14)

| Field Name | Row | Col | Length | ATTRB                    | Color | Hilight   | I/O   | Notes                    |
|------------|-----|-----|--------|--------------------------|-------|-----------|-------|--------------------------|
| (label)    | 14  | 15  | 12     | ASKIP,NORM               | TURQUOISE| —      | O     | `  End Date :`           |
| EDTMM      | 14  | 29  | 2      | FSET,NORM,NUM,UNPROT     | GREEN | UNDERLINE | Input | End month (MM); NUM      |
| (sep)      | 14  | 32  | 1      | ASKIP,NORM               | BLUE  | —         | O     | `/`                      |
| EDTDD      | 14  | 34  | 2      | FSET,NORM,NUM,UNPROT     | GREEN | UNDERLINE | Input | End day (DD); NUM        |
| (sep)      | 14  | 37  | 1      | ASKIP,NORM               | BLUE  | —         | O     | `/`                      |
| EDTYYYY    | 14  | 39  | 4      | FSET,NORM,NUM,UNPROT     | GREEN | UNDERLINE | Input | End year (YYYY); NUM     |
| (stopper)  | 14  | 44  | 0      | —                        | —     | —         | —     |                          |
| (hint)     | 14  | 46  | 12     | (default)                | BLUE  | —         | O     | `(MM/DD/YYYY)`           |

**NUM attribute on date sub-fields:** Restricts input to numeric digits at the terminal hardware level.

### Confirmation Field (row 19)

| Field Name | Row | Col | Length | ATTRB          | Color | Hilight   | I/O   | Notes                                            |
|------------|-----|-----|--------|----------------|-------|-----------|-------|--------------------------------------------------|
| (prompt)   | 19  | 6   | 59     | ASKIP,NORM     | TURQUOISE | —     | O     | `The Report will be submitted for printing. Please confirm: ` |
| CONFIRM    | 19  | 66  | 1      | FSET,NORM,UNPROT | GREEN | UNDERLINE | Input | Y to submit; N to cancel                        |
| (stopper)  | 19  | 68  | 0      | —              | —     | —         | —     |                                                  |
| (hint)     | 19  | 69  | 5      | ASKIP,NORM     | NEUTRAL | —       | O     | `(Y/N)`                                          |

### Message and Navigation (rows 23–24)

| Field Name | Row | Col | Length | ATTRB          | Color  | I/O | Notes                   |
|------------|-----|-----|--------|----------------|--------|-----|-------------------------|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED    | O   | Error message           |
| (fkeys)    | 24  | 1   | 23     | ASKIP,NORM     | YELLOW | O   | `ENTER=Continue  F3=Back` |

---

## 5. Generated Copybook Structure (CORPT00.CPY)

### Input Structure: CORPT0AI

| Input Field | COBOL Name  | PIC       | Notes                                    |
|-------------|-------------|-----------|------------------------------------------|
| TRNNAME     | TRNNAMEI    | PIC X(4)  | Transaction ID                           |
| TITLE01     | TITLE01I    | PIC X(40) | Title line 1                             |
| CURDATE     | CURDATEI    | PIC X(8)  | Date                                     |
| PGMNAME     | PGMNAMEI    | PIC X(8)  | Program name                             |
| TITLE02     | TITLE02I    | PIC X(40) | Title line 2                             |
| CURTIME     | CURTIMEI    | PIC X(8)  | Time                                     |
| MONTHLY     | MONTHLYI    | PIC X(1)  | Monthly selector (space = not selected)  |
| YEARLY      | YEARLYI     | PIC X(1)  | Yearly selector                          |
| CUSTOM      | CUSTOMI     | PIC X(1)  | Custom selector                          |
| SDTMM       | SDTMMI      | PIC X(2)  | Start month                              |
| SDTDD       | SDTDDI      | PIC X(2)  | Start day                                |
| SDTYYYY     | SDTYYYYI    | PIC X(4)  | Start year                               |
| EDTMM       | EDTMMI      | PIC X(2)  | End month                                |
| EDTDD       | EDTDDI      | PIC X(2)  | End day                                  |
| EDTYYYY     | EDTYYYYI    | PIC X(4)  | End year                                 |
| CONFIRM     | CONFIRMI    | PIC X(1)  | Submission confirmation                  |
| ERRMSG      | ERRMSGI     | PIC X(78) | Error message                            |

---

## 6. Screen Navigation

| Key   | Action                                                                         |
|-------|--------------------------------------------------------------------------------|
| ENTER | Validates selections and submits report if CONFIRM=Y                           |
| PF3   | Returns to previous screen (main menu)                                         |

---

## 7. Validation Rules

| Field                  | BMS Constraint            | Program-Level Validation                               |
|------------------------|---------------------------|--------------------------------------------------------|
| MONTHLY/YEARLY/CUSTOM  | Length=1, UNPROT, FSET    | Exactly one must be non-blank; CUSTOM requires dates   |
| SDTMM                  | Length=2, NUM, UNPROT     | Required if CUSTOM; 01–12                              |
| SDTDD                  | Length=2, NUM, UNPROT     | Required if CUSTOM; 01–31; calendar-valid              |
| SDTYYYY                | Length=4, NUM, UNPROT     | Required if CUSTOM; 4-digit year                       |
| EDTMM/EDTDD/EDTYYYY    | As above                  | Required if CUSTOM; must be >= start date              |
| CONFIRM                | Length=1, UNPROT, FSET    | Must be Y to submit; N cancels                         |

---

## 8. Related Screens

| Screen  | Mapset  | Relationship                                    |
|---------|---------|-------------------------------------------------|
| COMEN01 | COMEN01 | Navigate FROM (transaction reports menu option) |
