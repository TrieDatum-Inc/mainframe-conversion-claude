# COCRDLI — Credit Card List Screen Technical Specification

## 1. Screen Overview

**Purpose:** Displays a paginated list of credit cards, filtered by an optional Account Number and/or Credit Card Number search criteria. Up to 7 card records are shown per page. The operator can select a card from the list using the selection (CRDSELn) fields. Supports forward/backward paging.

**Driving Program:** COCRDLIC (Credit Card List program)

**Source File:** `/app/bms/COCRDLI.bms`
**Copybook:** `/app/cpy-bms/COCRDLI.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value                          |
|--------------|--------------------------------|
| MAPSET name  | COCRDLI                        |
| MAP name     | CCRDLIA                        |
| SIZE         | (24, 80)                       |
| CTRL         | FREEKB                         |
| DSATTS       | COLOR, HILIGHT, PS, VALIDN     |
| MAPATTS      | COLOR, HILIGHT, PS, VALIDN     |
| LANG         | COBOL                          |
| MODE         | INOUT                          |
| STORAGE      | AUTO                           |
| TIOAPFX      | YES                            |
| TYPE         | &&SYSPARM                      |

---

## 3. Screen Layout (ASCII Representation)

```
Col:  1         2         3         4         5         6         7         8
      12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row1: Tran:[TRNM]          [----------TITLE01----------]     Date:[CURDATE-]
Row2: Prog:[PGMNAME]       [----------TITLE02----------]     Time:[CURTIME-]
Row3:
Row4:                               List Credit Cards            Page [PGN]
Row5:
Row6:                      Account Number    :[ACCTSID---]
Row7:                      Credit Card Number:[CARDSID-----------]
Row8:
Row9:            Select    Account Number    Card Number      Active
Row10:           ------    ---------------  ---------------  --------
Row11:           [S1]      [ACCTNO1---]     [CRDNUM1-------] [CS1]
Row12:           [S2]  [x] [ACCTNO2---]     [CRDNUM2-------] [CS2]
Row13:           [S3]  [x] [ACCTNO3---]     [CRDNUM3-------] [CS3]
Row14:           [S4]  [x] [ACCTNO4---]     [CRDNUM4-------] [CS4]
Row15:           [S5]  [x] [ACCTNO5---]     [CRDNUM5-------] [CS5]
Row16:           [S6]  [x] [ACCTNO6---]     [CRDNUM6-------] [CS6]
Row17:           [S7]  [x] [ACCTNO7---]     [CRDNUM7-------] [CS7]
Row18:
Row19:
Row20:                   [INFOMSG----------------------------------]
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24:   F3=Exit F7=Backward  F8=Forward
```

Note: `[x]` represents the hidden CRDSTP (stop) fields in rows 12–17.

---

## 4. Field Definitions

### Header Fields (rows 1–2)

| Field Name | Row | Col | Length | ATTRB      | Color  | I/O | Notes                        |
|------------|-----|-----|--------|------------|--------|-----|------------------------------|
| (label)    | 1   | 1   | 5      | ASKIP,NORM | BLUE   | O   | `Tran:`                      |
| TRNNAME    | 1   | 7   | 4      | ASKIP,FSET,NORM | BLUE | O  | Transaction name             |
| TITLE01    | 1   | 21  | 40     | ASKIP,NORM | YELLOW | O   | Title line 1                 |
| (label)    | 1   | 65  | 5      | ASKIP,NORM | BLUE   | O   | `Date:`                      |
| CURDATE    | 1   | 71  | 8      | ASKIP,NORM | BLUE   | O   | Current date                 |
| (label)    | 2   | 1   | 5      | ASKIP,NORM | BLUE   | O   | `Prog:`                      |
| PGMNAME    | 2   | 7   | 8      | ASKIP,NORM | BLUE   | O   | Program name                 |
| TITLE02    | 2   | 21  | 40     | ASKIP,NORM | YELLOW | O   | Title line 2                 |
| (label)    | 2   | 65  | 5      | ASKIP,NORM | BLUE   | O   | `Time:`                      |
| CURTIME    | 2   | 71  | 8      | ASKIP,NORM | BLUE   | O   | Current time                 |

### Page Title and Number (row 4)

| Field Name | Row | Col | Length | ATTRB    | Color   | I/O | Notes                  |
|------------|-----|-----|--------|----------|---------|-----|------------------------|
| (title)    | 4   | 31  | 17     | (default)| NEUTRAL | O   | `List Credit Cards`    |
| (label)    | 4   | 70  | 5      | (default)| —       | O   | `Page `                |
| PAGENO     | 4   | 76  | 3      | (default)| —       | O   | Current page number    |

### Search Filter Fields (rows 6–7)

| Field Name | Row | Col | Length | ATTRB               | Color | Hilight   | I/O   | Notes                                  |
|------------|-----|-----|--------|---------------------|-------|-----------|-------|----------------------------------------|
| (label)    | 6   | 22  | 19     | ASKIP,NORM          | TURQUOISE| —      | O     | `Account Number    :`                  |
| ACCTSID    | 6   | 44  | 11     | FSET,IC,NORM,UNPROT | GREEN | UNDERLINE | Input | Account number search key; IC here     |
| (stopper)  | 6   | 56  | 0      | —                   | —     | —         | —     | Tab stop                               |
| (label)    | 7   | 22  | 19     | ASKIP,NORM          | TURQUOISE| —      | O     | `Credit Card Number:`                  |
| CARDSID    | 7   | 44  | 16     | FSET,NORM,UNPROT    | GREEN | UNDERLINE | Input | Card number search key                 |
| (stopper)  | 7   | 61  | 0      | —                   | —     | —         | —     | Tab stop                               |

### Column Headers (rows 9–10)

| Row | Col | Length | Content             | Color   |
|-----|-----|--------|---------------------|---------|
| 9   | 10  | 10     | `Select    `        | NEUTRAL |
| 9   | 21  | 14     | `Account Number`    | NEUTRAL |
| 9   | 45  | 13     | ` Card Number `     | NEUTRAL |
| 9   | 66  | 7      | `Active `           | NEUTRAL |
| 10  | 10  | 6      | `------`            | NEUTRAL |
| 10  | 20  | 15     | `---------------`   | NEUTRAL |
| 10  | 43  | 15     | `---------------`   | NEUTRAL |
| 10  | 65  | 8      | `--------`          | NEUTRAL |

### List Rows (rows 11–17) — 7 card slots

Each row (n = 1–7) has the following fields:

**Row 11 (slot 1 — no stop field):**

| Field Name | Row | Col | Length | ATTRB          | Color   | Hilight   | I/O   | Notes                                        |
|------------|-----|-----|--------|----------------|---------|-----------|-------|----------------------------------------------|
| CRDSEL1    | 11  | 12  | 1      | FSET,NORM,PROT | DEFAULT | UNDERLINE | O     | Selection column; operator overwrites via program; PROT prevents direct cursor entry |
| (stopper)  | 11  | 14  | 0      | —              | —       | —         | —     | Tab stop after selector                      |
| ACCTNO1    | 11  | 22  | 11     | NORM,PROT      | DEFAULT | OFF       | O     | Account number for row 1                     |
| CRDNUM1    | 11  | 43  | 16     | NORM,PROT      | DEFAULT | OFF       | O     | Credit card number for row 1                 |
| CRDSTS1    | 11  | 67  | 1      | NORM,PROT      | DEFAULT | OFF       | O     | Active status for row 1                      |

**Rows 12–17 (slots 2–7 — each has a hidden CRDSTP stop field):**

| Field Name | Row n | Col | Length | ATTRB          | Color   | Hilight   | I/O | Notes                                         |
|------------|-------|-----|--------|----------------|---------|-----------|-----|-----------------------------------------------|
| CRDSELn    | n+10  | 12  | 1      | FSET,NORM,PROT | DEFAULT | UNDERLINE | O   | Selection indicator for row n                 |
| (stopper)  | n+10  | 14  | 0      | —              | —       | —         | —   | Unnamed tab stop                              |
| CRDSTPn    | n+10  | 14  | 1      | ASKIP,DRK,FSET | DEFAULT | OFF       | O   | Hidden stop field — DRK prevents display; used as paging marker |
| ACCTNOn    | n+10  | 22  | 11     | NORM,PROT      | DEFAULT | OFF       | O   | Account number                                |
| CRDNUMn    | n+10  | 43  | 16     | NORM,PROT      | DEFAULT | OFF       | O   | Card number                                   |
| CRDSTSn    | n+10  | 67  | 1      | NORM,PROT      | DEFAULT | OFF       | O   | Active status                                 |

**CRDSTP fields (rows 12–17 only):** These are ASKIP,DRK hidden fields positioned immediately after the selector stop. Their purpose is to provide a programmatic marker that the program can check to determine which rows are populated vs. empty during list processing.

**CRDSEL fields note:** Although defined as PROT in the BMS, the program dynamically modifies the attribute bytes (via the C suffix output fields) to make selector fields UNPROT when a row is populated, allowing the operator to type a selection character.

### Status and Navigation (rows 20–24)

| Field Name | Row | Col | Length | ATTRB          | Color     | I/O | Notes                               |
|------------|-----|-----|--------|----------------|-----------|-----|-------------------------------------|
| INFOMSG    | 20  | 19  | 45     | PROT           | NEUTRAL   | O   | Informational message               |
| (stopper)  | 20  | 65  | 0      | —              | —         | —   |                                     |
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED       | O   | Error message                       |
| (fkeys)    | 24  | 1   | 78     | ASKIP,NORM     | TURQUOISE | O   | `  F3=Exit F7=Backward  F8=Forward` |

---

## 5. Screen Navigation

| Key  | Action                                                                         |
|------|--------------------------------------------------------------------------------|
| ENTER| Submits search criteria (ACCTSID/CARDSID) or processes a selection             |
| PF3  | Returns to previous screen                                                     |
| PF7  | Pages backward through card list                                               |
| PF8  | Pages forward through card list                                                |

**Selection mechanic:** The operator types a selection character (e.g., `S`) into one of the CRDSEL fields and presses ENTER. The program reads back the selector fields and identifies which row was chosen, then navigates to the appropriate detail screen (COCRDSL or COCRDUP).

---

## 6. Validation Rules

| Field   | BMS Constraint          | Program-Level Validation                                   |
|---------|-------------------------|------------------------------------------------------------|
| ACCTSID | Length=11, UNPROT, FSET | Optional; if provided must match existing account          |
| CARDSID | Length=16, UNPROT, FSET | Optional; if provided must be a valid card number format   |
| CRDSELn | Length=1, PROT→UNPROT   | Program validates that at most one selection is made       |

---

## 7. Related Screens

| Screen  | Mapset  | Relationship                                        |
|---------|---------|-----------------------------------------------------|
| COMEN01 | COMEN01 | Navigate FROM (card list menu option)               |
| COCRDSL | COCRDSL | Navigate TO (view card detail for selected card)    |
| COCRDUP | COCRDUP | Navigate TO (update card detail for selected card)  |
