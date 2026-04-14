# COCRDUP — Credit Card Update Screen Technical Specification

## 1. Screen Overview

**Purpose:** Provides an edit form for updating an existing credit card record. The Account Number is display-only (protected); the Card Number, Name on Card, Active status, and Expiry Date are editable. A hidden EXPDAY field carries an internal day component not shown to the user. Function keys F5=Save and F12=Cancel are initially hidden (DRK) and revealed when appropriate.

**Driving Program:** COCRDUPD (Credit Card Update program)

**Source File:** `/app/bms/COCRDUP.bms`
**Copybook:** `/app/cpy-bms/COCRDUP.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value                          |
|--------------|--------------------------------|
| MAPSET name  | COCRDUP                        |
| MAP name     | CCRDUPA                        |
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
Row4:                               Update Credit Card Details
Row5:
Row6:
Row7:                       Account Number    :[ACCTSID---]  (PROT)
Row8:                       Card Number       :[CARDSID-----------]
Row9:
Row10:
Row11:    Name on card      :[CRDNAME-----------------------------------------]
Row12:
Row13:    Card Active Y/N   : [A]
Row14:
Row15:    Expiry Date       : [MM]/[YYYY][ED](hidden)
Row16:
Row17:
Row18:
Row19:
Row20:                         [INFOMSG-----------------------------]
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Process F3=Exit        F5=Save F12=Cancel (initially hidden)
```

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

### Screen Title (row 4)

| Row | Col | Length | Content                      | Color   |
|-----|-----|--------|------------------------------|---------|
| 4   | 30  | 26     | `Update Credit Card Details` | NEUTRAL |

### Key Fields (rows 7–8)

| Field Name | Row | Col | Length | ATTRB               | Color   | Hilight   | I/O   | Notes                                              |
|------------|-----|-----|--------|---------------------|---------|-----------|-------|----------------------------------------------------|
| (label)    | 7   | 23  | 19     | ASKIP,NORM          | TURQUOISE| —        | O     | `Account Number    :`                              |
| ACCTSID    | 7   | 45  | 11     | FSET,IC,NORM,PROT   | DEFAULT | UNDERLINE | O     | **PROT** — account number is display-only; IC sets cursor to CARDSID on first tab |
| (stopper)  | 7   | 57  | 0      | —                   | —       | —         | —     | Tab stop                                           |
| (label)    | 8   | 23  | 19     | ASKIP,NORM          | TURQUOISE| —        | O     | `Card Number       :`                              |
| CARDSID    | 8   | 45  | 16     | FSET,NORM,UNPROT    | DEFAULT | UNDERLINE | Input | Card number — editable                             |
| (stopper)  | 8   | 62  | 0      | —                   | —       | —         | —     |                                                    |

**ACCTSID PROT:** Unlike COCRDSL where ACCTSID is UNPROT for searching, on this update screen the account is already resolved and the field is locked to prevent accidental change.

### Editable Card Detail Fields (rows 11–15)

| Field Name | Row | Col | Length | ATTRB    | Color     | Hilight   | I/O   | Notes                             |
|------------|-----|-----|--------|----------|-----------|-----------|-------|-----------------------------------|
| (label)    | 11  | 4   | 20     | —        | TURQUOISE | —         | O     | `Name on card      :`             |
| CRDNAME    | 11  | 25  | 50     | UNPROT   | —         | UNDERLINE | Input | Cardholder name — **editable**    |
| (stopper)  | 11  | 76  | 0      | —        | —         | —         | —     |                                   |
| (label)    | 13  | 4   | 20     | —        | TURQUOISE | —         | O     | `Card Active Y/N   : `            |
| CRDSTCD    | 13  | 25  | 1      | UNPROT   | —         | UNDERLINE | Input | Active status — **editable**      |
| (stopper)  | 13  | 27  | 0      | —        | —         | —         | —     |                                   |
| (label)    | 15  | 4   | 20     | —        | TURQUOISE | —         | O     | `Expiry Date       : `            |
| EXPMON     | 15  | 25  | 2      | UNPROT   | —         | UNDERLINE | Input | Expiry month (MM); JUSTIFY=(RIGHT)|
| (sep)      | 15  | 28  | 1      | —        | —         | —         | O     | `/` separator                     |
| EXPYEAR    | 15  | 30  | 4      | UNPROT   | —         | UNDERLINE | Input | Expiry year (YYYY); JUSTIFY=(RIGHT)|
| (stopper)  | 15  | 35  | 0      | —        | —         | —         | —     |                                   |
| EXPDAY     | 15  | 36  | 2      | DRK,FSET,PROT | —  | OFF       | I/O   | **Hidden** expiry day — DRK; carries internal day value; FSET retransmits |
| (stopper)  | 15  | 39  | 0      | —        | —         | —         | —     |                                   |

**EXPDAY note:** This hidden field (DRK=dark, PROT=protected) stores the day component of the expiry date. It is not visible to the operator. The program reads it on RECEIVE MAP and maintains the day value across screen sends. This pattern preserves data that cannot be derived from the visible MM/YYYY fields alone.

### Status and Navigation (rows 20–24)

| Field Name | Row | Col | Length | ATTRB          | Color   | I/O | Notes                                   |
|------------|-----|-----|--------|----------------|---------|-----|-----------------------------------------|
| INFOMSG    | 20  | 25  | 40     | PROT           | NEUTRAL | O   | Informational message                   |
| ERRMSG     | 23  | 1   | 80     | ASKIP,BRT,FSET | RED     | O   | Error message (80 chars)                |
| FKEYS      | 24  | 1   | 21     | ASKIP,NORM     | YELLOW  | O   | `ENTER=Process F3=Exit` — always visible|
| FKEYSC     | 24  | 23  | 18     | ASKIP,DRK      | YELLOW  | O   | `F5=Save F12=Cancel` — **initially hidden (DRK)**; program reveals when data is loaded |

---

## 5. Screen Navigation

| Key   | Action                                                                         |
|-------|--------------------------------------------------------------------------------|
| ENTER | Submits editable fields; program validates and processes update                |
| PF3   | Exits without saving                                                           |
| PF5   | Save — saves changes (only visible once card data is loaded)                   |
| PF12  | Cancel — abandons changes (only visible once card data is loaded)              |

---

## 6. Validation Rules

| Field   | BMS Constraint                | Program-Level Validation                        |
|---------|-------------------------------|-------------------------------------------------|
| CARDSID | Length=16, UNPROT, FSET       | Must be a valid card number; format validated   |
| CRDNAME | Length=50, UNPROT             | Must not be blank                               |
| CRDSTCD | Length=1, UNPROT              | Must be Y or N                                  |
| EXPMON  | Length=2, UNPROT              | Must be 01–12                                   |
| EXPYEAR | Length=4, UNPROT              | Must be a 4-digit year >= current year          |

---

## 7. Related Screens

| Screen  | Mapset  | Relationship                                           |
|---------|---------|--------------------------------------------------------|
| COCRDSL | COCRDSL | Navigate FROM (view screen leads to update)            |
| COCRDLI | COCRDLI | Navigate FROM (list screen; selecting a card leads here)|
| COMEN01 | COMEN01 | Navigate TO/FROM (main menu)                           |
