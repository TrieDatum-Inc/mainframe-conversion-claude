# COTRN01 — Transaction View Screen Technical Specification

## 1. Screen Overview

**Purpose:** Displays the full detail of a single credit card transaction. The operator can enter a Transaction ID and press ENTER to fetch and display the record. Alternatively, a transaction can be pre-loaded from the Transaction List (COTRN00) via a `S` selection. Supports browsing to the Transaction Add screen (COTRN02) and clearing the form. All detail fields are output-only (protected).

**Driving Program:** COTRN01C (Transaction View program)

**Source File:** `/app/bms/COTRN01.bms`
**Copybook:** `/app/cpy-bms/COTRN01.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value             |
|--------------|-------------------|
| MAPSET name  | COTRN01           |
| MAP name     | COTRN1A           |
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
Row4:                                 View Transaction
Row5:
Row6:      Enter Tran ID:[TRNIDIN-----------]
Row7:
Row8:      -----------------------------------------------------------------------
Row9:
Row10:     Transaction ID:[TRNID-----------]    Card Number:[CARDNUM-----------]
Row11:
Row12:     Type CD:[TT]     Category CD:[CCCC]   Source:[TRNSRC----]
Row13:
Row14:     Description:[TDESC------------------------------------------------------]
Row15:
Row16:     Amount:[TRNAMT-----]  Orig Date:[TORIGDT--]  Proc Date:[TPROCDT--]
Row17:
Row18:     Merchant ID:[MID-----]   Merchant Name:[MNAME--------------------------]
Row19:
Row20:     Merchant City:[MCITY-------------------]  Merchant Zip:[MZIP------]
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Fetch  F3=Back  F4=Clear  F5=Browse Tran.
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

| Row | Col | Length | Content            | ATTRB     | Color   |
|-----|-----|--------|--------------------|-----------|---------|
| 4   | 30  | 16     | `View Transaction` | ASKIP,BRT | NEUTRAL |

### Transaction ID Input (row 6)

| Field Name | Row | Col | Length | ATTRB               | Color     | Hilight   | I/O   | Notes                                  |
|------------|-----|-----|--------|---------------------|-----------|-----------|-------|----------------------------------------|
| (label)    | 6   | 6   | 14     | ASKIP,NORM          | TURQUOISE | —         | O     | `Enter Tran ID:`                       |
| TRNIDIN    | 6   | 21  | 16     | FSET,IC,NORM,UNPROT | GREEN     | UNDERLINE | Input | Transaction ID search key; IC here; init space |
| (stopper)  | 6   | 38  | 0      | ASKIP,NORM          | —         | —         | —     | Tab stop                               |

### Separator (row 8)

| Row | Col | Length | Content       | Color   |
|-----|-----|--------|---------------|---------|
| 8   | 6   | 70     | 70 dashes     | NEUTRAL |

### Transaction Detail Display Fields (rows 10–20)

All detail display fields are ATTRB=(ASKIP,NORM) — protected, cannot be modified by the operator. Initial values are single spaces (populated by the program after fetch).

#### Row 10 — Transaction ID and Card Number

| Field Name | Row | Col | Length | ATTRB      | Color     | I/O | Notes                   |
|------------|-----|-----|--------|------------|-----------|-----|-------------------------|
| (label)    | 10  | 6   | 15     | ASKIP,NORM | TURQUOISE | O   | `Transaction ID:`       |
| TRNID      | 10  | 22  | 16     | ASKIP,NORM | BLUE      | O   | Transaction ID display  |
| (stopper)  | 10  | 39  | 0      | —          | —         | —   |                         |
| (label)    | 10  | 45  | 12     | ASKIP,NORM | TURQUOISE | O   | `Card Number:`          |
| CARDNUM    | 10  | 58  | 16     | ASKIP,NORM | BLUE      | O   | Card number display     |
| (stopper)  | 10  | 75  | 0      | GREEN      | —         | —   |                         |

#### Row 12 — Type, Category, Source

| Field Name | Row | Col | Length | ATTRB      | Color     | I/O | Notes                      |
|------------|-----|-----|--------|------------|-----------|-----|----------------------------|
| (label)    | 12  | 6   | 8      | ASKIP,NORM | TURQUOISE | O   | `Type CD:`                 |
| TTYPCD     | 12  | 15  | 2      | ASKIP,NORM | BLUE      | O   | Transaction type code      |
| (stopper)  | 12  | 18  | 0      | —          | —         | —   |                            |
| (label)    | 12  | 23  | 12     | ASKIP,NORM | TURQUOISE | O   | `Category CD:`             |
| TCATCD     | 12  | 36  | 4      | ASKIP,NORM | BLUE      | O   | Category code              |
| (stopper)  | 12  | 41  | 0      | —          | —         | —   |                            |
| (label)    | 12  | 46  | 7      | ASKIP,NORM | TURQUOISE | O   | `Source:`                  |
| TRNSRC     | 12  | 54  | 10     | ASKIP,NORM | BLUE      | O   | Transaction source         |
| (stopper)  | 12  | 65  | 0      | —          | —         | —   |                            |

#### Row 14 — Description

| Field Name | Row | Col | Length | ATTRB      | Color     | I/O | Notes                          |
|------------|-----|-----|--------|------------|-----------|-----|--------------------------------|
| (label)    | 14  | 6   | 12     | ASKIP,NORM | TURQUOISE | O   | `Description:`                 |
| TDESC      | 14  | 19  | 60     | ASKIP,NORM | BLUE      | O   | Full transaction description   |
| (stopper)  | 14  | 80  | 0      | —          | —         | —   |                                |

#### Row 16 — Amount, Orig Date, Proc Date

| Field Name | Row | Col | Length | ATTRB      | Color     | I/O | Notes                          |
|------------|-----|-----|--------|------------|-----------|-----|--------------------------------|
| (label)    | 16  | 6   | 7      | ASKIP,NORM | TURQUOISE | O   | `Amount:`                      |
| TRNAMT     | 16  | 14  | 12     | ASKIP,NORM | BLUE      | O   | Transaction amount             |
| (stopper)  | 16  | 27  | 0      | —          | —         | —   |                                |
| (label)    | 16  | 31  | 10     | ASKIP,NORM | TURQUOISE | O   | `Orig Date:`                   |
| TORIGDT    | 16  | 42  | 10     | ASKIP,NORM | BLUE      | O   | Original transaction date      |
| (stopper)  | 16  | 53  | 0      | —          | —         | —   |                                |
| (label)    | 16  | 57  | 10     | ASKIP,NORM | TURQUOISE | O   | `Proc Date:`                   |
| TPROCDT    | 16  | 68  | 10     | ASKIP,NORM | BLUE      | O   | Processing date                |
| (stopper)  | 16  | 79  | 0      | —          | —         | —   |                                |

#### Row 18 — Merchant ID and Name

| Field Name | Row | Col | Length | ATTRB      | Color     | I/O | Notes                    |
|------------|-----|-----|--------|------------|-----------|-----|--------------------------|
| (label)    | 18  | 6   | 12     | ASKIP,NORM | TURQUOISE | O   | `Merchant ID:`           |
| MID        | 18  | 19  | 9      | ASKIP,NORM | BLUE      | O   | Merchant ID              |
| (stopper)  | 18  | 29  | 0      | —          | —         | —   |                          |
| (label)    | 18  | 33  | 14     | ASKIP,NORM | TURQUOISE | O   | `Merchant Name:`         |
| MNAME      | 18  | 48  | 30     | ASKIP,NORM | BLUE      | O   | Merchant name            |
| (stopper)  | 18  | 79  | 0      | —          | —         | —   |                          |

#### Row 20 — Merchant City and ZIP

| Field Name | Row | Col | Length | ATTRB      | Color     | I/O | Notes                    |
|------------|-----|-----|--------|------------|-----------|-----|--------------------------|
| (label)    | 20  | 6   | 14     | ASKIP,NORM | TURQUOISE | O   | `Merchant City:`         |
| MCITY      | 20  | 21  | 25     | ASKIP,NORM | BLUE      | O   | Merchant city            |
| (stopper)  | 20  | 47  | 0      | —          | —         | —   |                          |
| (label)    | 20  | 53  | 13     | ASKIP,NORM | TURQUOISE | O   | `Merchant Zip:`          |
| MZIP       | 20  | 67  | 10     | ASKIP,NORM | BLUE      | O   | Merchant ZIP code        |
| (stopper)  | 20  | 78  | 0      | —          | —         | —   |                          |

### Message and Navigation (rows 23–24)

| Field Name | Row | Col | Length | ATTRB          | Color  | I/O | Notes                                          |
|------------|-----|-----|--------|----------------|--------|-----|------------------------------------------------|
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED    | O   | Error message                                  |
| (fkeys)    | 24  | 1   | 47     | ASKIP,NORM     | YELLOW | O   | `ENTER=Fetch  F3=Back  F4=Clear  F5=Browse Tran.` |

---

## 5. Screen Navigation

| Key  | Action                                                                         |
|------|--------------------------------------------------------------------------------|
| ENTER| Fetches transaction for the entered TRNIDIN and displays all detail fields     |
| PF3  | Returns to previous screen (transaction list or main menu)                     |
| PF4  | Clears TRNIDIN and all displayed detail fields                                 |
| PF5  | Navigates to COTRN02 (Add Transaction) — `Browse Tran.`                        |

---

## 6. Validation Rules

| Field   | BMS Constraint           | Program-Level Validation                                |
|---------|--------------------------|---------------------------------------------------------|
| TRNIDIN | Length=16, UNPROT, FSET  | Must not be blank; must match existing transaction record|

All display fields are ASKIP — no input validation applies.

---

## 7. Related Screens

| Screen  | Mapset  | Relationship                                           |
|---------|---------|--------------------------------------------------------|
| COTRN00 | COTRN00 | Navigate FROM (list screen; `S` selection leads here)  |
| COTRN02 | COTRN02 | Navigate TO via PF5 (add a new transaction)            |
| COMEN01 | COMEN01 | Navigate FROM/TO (main menu)                           |
