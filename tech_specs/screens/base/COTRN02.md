# COTRN02 — Transaction Add Screen Technical Specification

## 1. Screen Overview

**Purpose:** Provides a full data-entry form for adding a new credit card transaction record. The operator enters an Account Number or Card Number to identify the account, then fills in transaction details (type, category, source, description, amount, dates, merchant information). A Y/N confirmation field prevents accidental submission. PF5 copies the last transaction to pre-fill fields.

**Driving Program:** COTRN02C (Transaction Add program)

**Source File:** `/app/bms/COTRN02.bms`
**Copybook:** `/app/cpy-bms/COTRN02.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COTRN02           |
| MAP name     | COTRN2A           |
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
Row4:                                  Add Transaction
Row5:
Row6:      Enter Acct #:[ACTIDIN---]    (or)    Card #:[CARDNIN-----------]
Row7:
Row8:      -----------------------------------------------------------------------
Row9:
Row10:     Type CD:[TT]     Category CD:[CCCC]   Source:[TRNSRC----]
Row11:
Row12:     Description:[TDESC------------------------------------------------------]
Row13:
Row14:     Amount:[TRNAMT-----]  Orig Date:[TORIGDT--]  Proc Date:[TPROCDT--]
Row15:     (-99999999.99)        (YYYY-MM-DD)           (YYYY-MM-DD)
Row16:     Merchant ID:[MID-----]   Merchant Name:[MNAME--------------------------]
Row17:
Row18:     Merchant City:[MCITY-------------------]  Merchant Zip:[MZIP------]
Row19:
Row20:
Row21:     You are about to add this transaction. Please confirm : [C] (Y/N)
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Continue  F3=Back  F4=Clear  F5=Copy Last Tran.
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
| CURDATE    | 1   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current date                   |
| (label)    | 2   | 1   | 5      | ASKIP,NORM      | BLUE   | O   | `Prog:`                        |
| PGMNAME    | 2   | 7   | 8      | ASKIP,FSET,NORM | BLUE   | O   | Program name                   |
| TITLE02    | 2   | 21  | 40     | ASKIP,FSET,NORM | YELLOW | O   | Title line 2                   |
| (label)    | 2   | 65  | 5      | ASKIP,NORM      | BLUE   | O   | `Time:`                        |
| CURTIME    | 2   | 71  | 8      | ASKIP,FSET,NORM | BLUE   | O   | Current time                   |

### Screen Title (row 4)

| Row | Col | Length | Content           | ATTRB     | Color   |
|-----|-----|--------|-------------------|-----------|---------|
| 4   | 30  | 15     | `Add Transaction` | ASKIP,BRT | NEUTRAL |

### Account/Card Identification (row 6)

| Field Name | Row | Col | Length | ATTRB               | Color     | Hilight   | I/O   | Notes                                      |
|------------|-----|-----|--------|---------------------|-----------|-----------|-------|--------------------------------------------|
| (label)    | 6   | 6   | 13     | ASKIP,NORM          | TURQUOISE | —         | O     | `Enter Acct #:`                            |
| ACTIDIN    | 6   | 21  | 11     | FSET,IC,NORM,UNPROT | GREEN     | UNDERLINE | Input | Account ID — mutually exclusive with CARDNIN; IC |
| (stopper)  | 6   | 33  | 0      | ASKIP,NORM          | —         | —         | —     | Tab stop                                   |
| (label)    | 6   | 37  | 4      | ASKIP,NORM          | NEUTRAL   | —         | O     | `(or)`                                     |
| (label)    | 6   | 46  | 7      | ASKIP,NORM          | TURQUOISE | —         | O     | `Card #:`                                  |
| CARDNIN    | 6   | 55  | 16     | FSET,NORM,UNPROT    | GREEN     | UNDERLINE | Input | Card number — mutually exclusive with ACTIDIN |
| (stopper)  | 6   | 72  | 0      | —                   | —         | —         | —     | Tab stop                                   |

### Separator (row 8)

| Row | Col | Length | Content   | Color   |
|-----|-----|--------|-----------|---------|
| 8   | 6   | 70     | 70 dashes | NEUTRAL |

### Transaction Classification (row 10)

| Field Name | Row | Col | Length | ATTRB               | Color     | Hilight   | I/O   | Notes                   |
|------------|-----|-----|--------|---------------------|-----------|-----------|-------|-------------------------|
| (label)    | 10  | 6   | 8      | ASKIP,NORM          | TURQUOISE | —         | O     | `Type CD:`              |
| TTYPCD     | 10  | 15  | 2      | FSET,NORM,UNPROT    | GREEN     | UNDERLINE | Input | Transaction type code; init space |
| (stopper)  | 10  | 18  | 0      | —                   | —         | —         | —     |                         |
| (label)    | 10  | 23  | 12     | ASKIP,NORM          | TURQUOISE | —         | O     | `Category CD:`          |
| TCATCD     | 10  | 36  | 4      | FSET,NORM,UNPROT    | GREEN     | UNDERLINE | Input | Category code; init space |
| (stopper)  | 10  | 41  | 0      | —                   | —         | —         | —     |                         |
| (label)    | 10  | 46  | 7      | ASKIP,NORM          | TURQUOISE | —         | O     | `Source:`               |
| TRNSRC     | 10  | 54  | 10     | FSET,NORM,UNPROT    | GREEN     | UNDERLINE | Input | Source system code; init space |
| (stopper)  | 10  | 65  | 0      | —                   | —         | —         | —     |                         |

### Description (row 12)

| Field Name | Row | Col | Length | ATTRB            | Color | Hilight   | I/O   | Notes                         |
|------------|-----|-----|--------|------------------|-------|-----------|-------|-------------------------------|
| (label)    | 12  | 6   | 12     | ASKIP,NORM       | TURQUOISE| —      | O     | `Description:`                |
| TDESC      | 12  | 19  | 60     | FSET,NORM,UNPROT | GREEN | UNDERLINE | Input | Free-text description; init space |
| (stopper)  | 12  | 80  | 0      | —                | —     | —         | —     |                               |

### Financial and Date Fields (rows 14–15)

| Field Name | Row | Col | Length | ATTRB            | Color | Hilight   | I/O   | Notes                                    |
|------------|-----|-----|--------|------------------|-------|-----------|-------|------------------------------------------|
| (label)    | 14  | 6   | 7      | ASKIP,NORM       | TURQUOISE| —      | O     | `Amount:`                                |
| TRNAMT     | 14  | 14  | 12     | FSET,NORM,UNPROT | GREEN | UNDERLINE | Input | Amount; init space; hint `(-99999999.99)` on row 15 |
| (stopper)  | 14  | 27  | 0      | —                | —     | —         | —     |                                          |
| (label)    | 14  | 31  | 10     | ASKIP,NORM       | TURQUOISE| —      | O     | `Orig Date:`                             |
| TORIGDT    | 14  | 42  | 10     | FSET,NORM,UNPROT | GREEN | UNDERLINE | Input | Original date; hint `(YYYY-MM-DD)` row 15|
| (stopper)  | 14  | 53  | 0      | —                | —     | —         | —     |                                          |
| (label)    | 14  | 57  | 10     | ASKIP,NORM       | TURQUOISE| —      | O     | `Proc Date:`                             |
| TPROCDT    | 14  | 68  | 10     | FSET,NORM,UNPROT | GREEN | UNDERLINE | Input | Processing date; hint `(YYYY-MM-DD)` row 15 |
| (stopper)  | 14  | 79  | 0      | —                | —     | —         | —     |                                          |

#### Format Hint Line (row 15)

| Row | Col | Length | Content            | Color |
|-----|-----|--------|--------------------|-------|
| 15  | 13  | 14     | `(-99999999.99)`   | BLUE  |
| 15  | 41  | 12     | `(YYYY-MM-DD)`     | BLUE  |
| 15  | 67  | 12     | `(YYYY-MM-DD)`     | BLUE  |

### Merchant Fields (rows 16–18)

| Field Name | Row | Col | Length | ATTRB            | Color     | Hilight   | I/O   | Notes                   |
|------------|-----|-----|--------|------------------|-----------|-----------|-------|-------------------------|
| (label)    | 16  | 6   | 12     | ASKIP,NORM       | TURQUOISE | —         | O     | `Merchant ID:`          |
| MID        | 16  | 19  | 9      | FSET,NORM,UNPROT | GREEN     | UNDERLINE | Input | Merchant ID; init space |
| (stopper)  | 16  | 29  | 0      | —                | —         | —         | —     |                         |
| (label)    | 16  | 33  | 14     | ASKIP,NORM       | TURQUOISE | —         | O     | `Merchant Name:`        |
| MNAME      | 16  | 48  | 30     | FSET,NORM,UNPROT | GREEN     | UNDERLINE | Input | Merchant name; init space |
| (stopper)  | 16  | 79  | 0      | —                | —         | —         | —     |                         |
| (label)    | 18  | 6   | 14     | ASKIP,NORM       | TURQUOISE | —         | O     | `Merchant City:`        |
| MCITY      | 18  | 21  | 25     | FSET,NORM,UNPROT | GREEN     | UNDERLINE | Input | Merchant city; init space |
| (stopper)  | 18  | 47  | 0      | —                | —         | —         | —     |                         |
| (label)    | 18  | 53  | 13     | ASKIP,NORM       | TURQUOISE | —         | O     | `Merchant Zip:`         |
| MZIP       | 18  | 67  | 10     | FSET,NORM,UNPROT | GREEN     | UNDERLINE | Input | Merchant ZIP; init space |
| (stopper)  | 18  | 78  | 0      | —                | —         | —         | —     |                         |

### Confirmation (row 21)

| Field Name | Row | Col | Length | ATTRB            | Color     | Hilight   | I/O   | Notes                                         |
|------------|-----|-----|--------|------------------|-----------|-----------|-------|-----------------------------------------------|
| (prompt)   | 21  | 6   | 55     | ASKIP,NORM       | TURQUOISE | —         | O     | `You are about to add this transaction. Please confirm :` |
| CONFIRM    | 21  | 63  | 1      | FSET,NORM,UNPROT | GREEN     | UNDERLINE | Input | Y to add; N to cancel                         |
| (stopper)  | 21  | 65  | 0      | —                | —         | —         | —     |                                               |
| (hint)     | 21  | 66  | 5      | ASKIP,NORM       | NEUTRAL   | —         | O     | `(Y/N)`                                       |

### Message and Navigation (rows 23–24)

| Field Name | Row | Col | Length | ATTRB          | Color  | I/O | Notes                                             |
|------------|-----|-----|--------|----------------|--------|-----|---------------------------------------------------|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED    | O   | Error message                                     |
| (fkeys)    | 24  | 1   | 53     | ASKIP,NORM     | YELLOW | O   | `ENTER=Continue  F3=Back  F4=Clear  F5=Copy Last Tran.` |

---

## 5. Screen Navigation

| Key  | Action                                                                            |
|------|-----------------------------------------------------------------------------------|
| ENTER| Validates all input fields; if CONFIRM=Y, inserts the new transaction record     |
| PF3  | Returns to previous screen (transaction view or main menu)                        |
| PF4  | Clears all input fields                                                           |
| PF5  | Copies the most recently added transaction into all fields to facilitate re-entry |

---

## 6. Validation Rules

| Field      | BMS Constraint              | Program-Level Validation                                       |
|------------|-----------------------------|----------------------------------------------------------------|
| ACTIDIN    | Length=11, UNPROT, FSET     | Optional if CARDNIN provided; must match existing account      |
| CARDNIN    | Length=16, UNPROT, FSET     | Optional if ACTIDIN provided; at least one must be non-blank   |
| TTYPCD     | Length=2, UNPROT, FSET      | Must be a valid transaction type code                          |
| TCATCD     | Length=4, UNPROT, FSET      | Must be a valid category code                                  |
| TRNSRC     | Length=10, UNPROT, FSET     | Must be a valid source code                                    |
| TDESC      | Length=60, UNPROT, FSET     | Must not be blank                                              |
| TRNAMT     | Length=12, UNPROT, FSET     | Numeric; format -99999999.99; must not be zero                 |
| TORIGDT    | Length=10, UNPROT, FSET     | Format YYYY-MM-DD; must be a valid date                        |
| TPROCDT    | Length=10, UNPROT, FSET     | Format YYYY-MM-DD; must be >= TORIGDT                          |
| MID        | Length=9, UNPROT, FSET      | Required; must be a valid merchant ID                          |
| MNAME      | Length=30, UNPROT, FSET     | Required; must not be blank                                    |
| CONFIRM    | Length=1, UNPROT, FSET      | Must be Y or N to act; Y triggers record insertion             |

---

## 7. Related Screens

| Screen  | Mapset  | Relationship                                           |
|---------|---------|--------------------------------------------------------|
| COTRN01 | COTRN01 | Navigate FROM via PF5 (browse/add flow)                |
| COMEN01 | COMEN01 | Navigate FROM (add transaction menu option)            |
