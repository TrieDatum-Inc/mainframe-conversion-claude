# COCRDSL — Credit Card Selection/Detail View Screen Technical Specification

## 1. Screen Overview

**Purpose:** Displays the detail of a single credit card record. The operator can enter an Account Number and/or Card Number to search for a card, and the screen displays the card name, active status, and expiry date. This screen is used primarily as a read-only detail view and as the entry point for navigating to the card update screen.

**Driving Program:** COCRDSLIC (Credit Card Select/View program)

**Source File:** `/app/bms/COCRDSL.bms`
**Copybook:** `/app/cpy-bms/COCRDSL.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value                          |
|--------------|--------------------------------|
| MAPSET name  | COCRDSL                        |
| MAP name     | CCRDSLA                        |
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
Row4:                               View Credit Card Detail
Row5:
Row6:
Row7:                       Account Number    :[ACCTSID---]
Row8:                       Card Number       :[CARDSID-----------]
Row9:
Row10:
Row11:    Name on card      :[CRDNAME-----------------------------------------]
Row12:
Row13:    Card Active Y/N   : [A]
Row14:
Row15:    Expiry Date       : [MM]/[YYYY]
Row16:
Row17:
Row18:
Row19:
Row20:                         [INFOMSG-----------------------------]
Row21:
Row22:
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Search Cards  F3=Exit
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

| Row | Col | Length | Content                  | Color   |
|-----|-----|--------|--------------------------|---------|
| 4   | 30  | 23     | `View Credit Card Detail`| NEUTRAL |

### Search Fields (rows 7–8)

| Field Name | Row | Col | Length | ATTRB               | Color   | Hilight   | I/O   | Notes                              |
|------------|-----|-----|--------|---------------------|---------|-----------|-------|------------------------------------|
| (label)    | 7   | 23  | 19     | ASKIP,NORM          | TURQUOISE| —        | O     | `Account Number    :`              |
| ACCTSID    | 7   | 45  | 11     | FSET,IC,NORM,UNPROT | DEFAULT | UNDERLINE | Input | Account number; IC positions cursor here |
| (stopper)  | 7   | 57  | 0      | —                   | —       | —         | —     |                                    |
| (label)    | 8   | 23  | 19     | ASKIP,NORM          | TURQUOISE| —        | O     | `Card Number       :`              |
| CARDSID    | 8   | 45  | 16     | FSET,NORM,UNPROT    | DEFAULT | UNDERLINE | Input | Card number                        |
| (stopper)  | 8   | 62  | 0      | —                   | —       | —         | —     |                                    |

### Card Detail Fields (rows 11–15)

| Field Name | Row | Col | Length | ATTRB  | Color     | Hilight   | I/O | Notes                          |
|------------|-----|-----|--------|--------|-----------|-----------|-----|--------------------------------|
| (label)    | 11  | 4   | 20     | —      | TURQUOISE | —         | O   | `Name on card      :`          |
| CRDNAME    | 11  | 25  | 50     | —      | UNDERLINE | —         | O   | Cardholder name — ASKIP (display only) |
| (stopper)  | 11  | 76  | 0      | —      | —         | —         | —   |                                |
| (label)    | 13  | 4   | 20     | —      | TURQUOISE | —         | O   | `Card Active Y/N   : `         |
| CRDSTCD    | 13  | 25  | 1      | ASKIP  | —         | UNDERLINE | O   | Active status Y/N — protected display |
| (stopper)  | 13  | 27  | 0      | —      | —         | —         | —   |                                |
| (label)    | 15  | 4   | 20     | —      | TURQUOISE | —         | O   | `Expiry Date       : `         |
| EXPMON     | 15  | 25  | 2      | ASKIP  | —         | UNDERLINE | O   | Expiry month — display only    |
| (sep)      | 15  | 28  | 1      | —      | —         | —         | O   | `/` separator                  |
| EXPYEAR    | 15  | 30  | 4      | ASKIP  | —         | UNDERLINE | O   | Expiry year — display only     |
| (stopper)  | 15  | 35  | 0      | —      | —         | —         | —   |                                |

### Status and Navigation (rows 20–24)

| Field Name | Row | Col | Length | ATTRB          | Color   | I/O | Notes                     |
|------------|-----|-----|--------|----------------|---------|-----|---------------------------|
| INFOMSG    | 20  | 25  | 40     | PROT           | NEUTRAL | O   | Informational message     |
| ERRMSG     | 23  | 1   | 80     | ASKIP,BRT,FSET | RED     | O   | Error message (80 chars)  |
| FKEYS      | 24  | 1   | 75     | ASKIP,NORM     | YELLOW  | O   | `ENTER=Search Cards  F3=Exit` |

---

## 5. Screen Navigation

| Key   | Action                                                                       |
|-------|------------------------------------------------------------------------------|
| ENTER | Searches for the card matching ACCTSID/CARDSID and displays detail           |
| PF3   | Returns to previous screen (card list or main menu)                          |

---

## 6. Validation Rules

| Field   | BMS Constraint           | Program-Level Validation                              |
|---------|--------------------------|-------------------------------------------------------|
| ACCTSID | Length=11, UNPROT, FSET  | Optional search key; if provided must match existing account |
| CARDSID | Length=16, UNPROT, FSET  | Optional search key; if provided must be a valid card |

Display fields (CRDNAME, CRDSTCD, EXPMON, EXPYEAR) are all ASKIP — no input validation applies.

---

## 7. Key Difference: COCRDSL vs COCRDUP

| Aspect             | COCRDSL (View)                     | COCRDUP (Update)                    |
|--------------------|------------------------------------|-------------------------------------|
| ACCTSID protection | UNPROT (user can change)           | PROT (fixed; populated by program)  |
| CARDSID protection | UNPROT (user can change)           | UNPROT (user can change)            |
| CRDNAME            | No ATTRB specified (display)       | ATTRB=(UNPROT) — editable           |
| CRDSTCD            | ATTRB=(ASKIP) — protected          | ATTRB=(UNPROT) — editable           |
| EXPMON/EXPYEAR     | ATTRB=(ASKIP) — protected          | ATTRB=(UNPROT) — editable           |
| Screen title       | `View Credit Card Detail`          | `Update Credit Card Details`        |
| Function keys      | ENTER=Search, F3=Exit              | ENTER=Process, F3=Exit, F5=Save, F12=Cancel |

---

## 8. Related Screens

| Screen  | Mapset  | Relationship                                          |
|---------|---------|-------------------------------------------------------|
| COCRDLI | COCRDLI | Navigate FROM (card list; selecting a row leads here) |
| COCRDUP | COCRDUP | Navigate TO (update the currently displayed card)     |
| COMEN01 | COMEN01 | Navigate FROM (direct menu option)                    |
