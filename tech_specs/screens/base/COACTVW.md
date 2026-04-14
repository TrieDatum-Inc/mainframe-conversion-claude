# COACTVW — Account View Screen Technical Specification

## 1. Screen Overview

**Purpose:** Presents a read-only display of a complete credit card account record including financial parameters and linked customer details. The operator enters an Account Number and presses ENTER to retrieve and display the record. Navigation to the Account Update screen is available from this screen.

**Driving Program:** COACTVWC (Account View program)

**Source File:** `/app/bms/COACTVW.bms`
**Copybook:** `/app/cpy-bms/COACTVW.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value                          |
|--------------|--------------------------------|
| MAPSET name  | COACTVW                        |
| MAP name     | CACTVWA                        |
| SIZE         | (24, 80)                       |
| CTRL         | FREEKB                         |
| DSATTS       | COLOR, HILIGHT, PS, VALIDN     |
| MAPATTS      | COLOR, HILIGHT, PS, VALIDN     |
| LANG         | COBOL                          |
| MODE         | INOUT                          |
| STORAGE      | AUTO                           |
| TIOAPFX      | YES                            |
| TYPE         | &&SYSPARM                      |

**Key design difference from COACTUP:** Most data display fields use ASKIP (auto-skip/protected) attribute, making them output-only. Only the ACCTSID search field is UNPROT/FSET with IC to accept operator input.

---

## 3. Screen Layout (ASCII Representation)

```
Col:  1         2         3         4         5         6         7         8
      12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row1: Tran:[TRNM]          [----------TITLE01----------]     Date:[CURDATE-]
Row2: Prog:[PGMNAME]       [----------TITLE02----------]     Time:[CURTIME-]
Row3:
Row4:                                 View Account
Row5:   Account Number :[ACCTSID---]          Active Y/N: [A]
Row6: Opened:[ADTOPEN--]                Credit Limit        :[ACRDLIM-------]
Row7: Expiry:[AEXPDT---]                Cash credit Limit   :[ACSHLIM-------]
Row8: Reissue:[AREISDT--]               Current Balance     :[ACURBAL-------]
Row9:                                   Current Cycle Credit:[ACRCYCR-------]
Row10:   Account Group:[AADDGRP--]      Current Cycle Debit :[ACRCYDB-------]
Row11:                               Customer Details
Row12:   Customer id  :[ACSTNUM-]       SSN:[ACSTSSN--------]
Row13:   Date of birth:[ACSTDOB--]      FICO Score:[FCO]
Row14: First Name           Middle Name:         Last Name :
Row15: [ACSFNAM-----------------][ACSMNAM-----------------][ACSLNAM-----------------]
Row16: Address:[ACSADL1------------------------------------------]  State [ST]
Row17:         [ACSADL2------------------------------------------]  Zip[ACSZIPC]
Row18: City   [ACSCITY------------------------------------------]  Country[CTR]
Row19: Phone 1:[ACSPHN1-----]    Government Issued Id Ref    : [ACSGOVT-----------]
Row20: Phone 2:[ACSPHN2-----]    EFT Account Id: [ACSEFTC--]  Primary Card Holder Y/N:[P]
Row21:
Row22:                       [INFOMSG----------------------------------]
Row23: [---------------------------ERRMSG------------------------------------]
Row24:   F3=Exit
```

---

## 4. Field Definitions

### Header Fields (rows 1–2)

| Field Name | Row | Col | Length | ATTRB      | Color  | I/O | Notes                        |
|------------|-----|-----|--------|------------|--------|-----|------------------------------|
| (label)    | 1   | 1   | 5      | ASKIP,NORM | BLUE   | O   | `Tran:`                      |
| TRNNAME    | 1   | 7   | 4      | ASKIP,FSET,NORM | BLUE | O   | Transaction name          |
| TITLE01    | 1   | 21  | 40     | ASKIP,NORM | YELLOW | O   | Title line 1                 |
| (label)    | 1   | 65  | 5      | ASKIP,NORM | BLUE   | O   | `Date:`                      |
| CURDATE    | 1   | 71  | 8      | ASKIP,NORM | BLUE   | O   | Current date; init `mm/dd/yy`|
| (label)    | 2   | 1   | 5      | ASKIP,NORM | BLUE   | O   | `Prog:`                      |
| PGMNAME    | 2   | 7   | 8      | ASKIP,NORM | BLUE   | O   | Program name                 |
| TITLE02    | 2   | 21  | 40     | ASKIP,NORM | YELLOW | O   | Title line 2                 |
| (label)    | 2   | 65  | 5      | ASKIP,NORM | BLUE   | O   | `Time:`                      |
| CURTIME    | 2   | 71  | 8      | ASKIP,NORM | BLUE   | O   | Current time; init `hh:mm:ss`|

### Account Input and Summary (rows 4–10)

| Field Name | Row | Col | Length | ATTRB              | Color     | Hilight   | Other          | I/O    | Notes                                              |
|------------|-----|-----|--------|--------------------|-----------|-----------|----------------|--------|----------------------------------------------------|
| (title)    | 4   | 33  | 12     | (default)          | NEUTRAL   | —         | —              | O      | `View Account`                                     |
| (label)    | 5   | 19  | 16     | ASKIP,NORM         | TURQUOISE | —         | —              | O      | `Account Number :`                                 |
| ACCTSID    | 5   | 38  | 11     | FSET,IC,NORM,UNPROT| GREEN     | UNDERLINE | PICIN=99999999999, VALIDN=(MUSTFILL) | Input | Account number entry; MUSTFILL enforces non-blank at terminal level |
| (stopper)  | 5   | 50  | 0      | —                  | —         | —         | —              | —      |                                                    |
| (label)    | 5   | 57  | 12     | (default)          | TURQUOISE | —         | —              | O      | `Active Y/N: `                                     |
| ACSTTUS    | 5   | 70  | 1      | ASKIP              | —         | UNDERLINE | —              | O      | Account status — display only (ASKIP=protected)    |
| (stopper)  | 5   | 72  | 0      | —                  | —         | —         | —              | —      |                                                    |

#### Date Fields — Opened, Expiry, Reissue (rows 6–8)

Unlike COACTUP which splits dates into three separate year/month/day fields, COACTVW uses single consolidated date display fields:

| Field Name | Row | Col | Length | ATTRB    | Hilight   | I/O | Notes                              |
|------------|-----|-----|--------|----------|-----------|-----|------------------------------------|
| (label)    | 6   | 8   | 7      | —        | —         | O   | `Opened:`                          |
| ADTOPEN    | 6   | 17  | 10     | (default)| UNDERLINE | O   | Opened date; single 10-char field  |
| (stopper)  | 6   | 28  | 0      | —        | —         | —   |                                    |
| (label)    | 7   | 8   | 7      | —        | —         | O   | `Expiry:`                          |
| AEXPDT     | 7   | 17  | 10     | (default)| UNDERLINE | O   | Expiry date                        |
| (stopper)  | 7   | 28  | 0      | —        | —         | —   |                                    |
| (label)    | 8   | 8   | 8      | —        | —         | O   | `Reissue:`                         |
| AREISDT    | 8   | 17  | 10     | (default)| UNDERLINE | O   | Reissue date                       |
| (stopper)  | 8   | 28  | 0      | —        | —         | —   |                                    |

#### Financial Display Fields (rows 6–10, right column)

All financial fields use PICOUT='+ZZZ,ZZZ,ZZZ.99' for formatted numeric display:

| Field Name | Row | Col | Length | ATTRB    | Hilight   | I/O | PICOUT                 | Notes                  |
|------------|-----|-----|--------|----------|-----------|-----|------------------------|------------------------|
| ACRDLIM    | 6   | 61  | 15     | (default)| UNDERLINE | O   | `+ZZZ,ZZZ,ZZZ.99`     | Credit limit           |
| ACSHLIM    | 7   | 61  | 15     | (default)| UNDERLINE | O   | `+ZZZ,ZZZ,ZZZ.99`     | Cash advance limit     |
| ACURBAL    | 8   | 61  | 15     | (default)| UNDERLINE | O   | `+ZZZ,ZZZ,ZZZ.99`     | Current balance        |
| ACRCYCR    | 9   | 61  | 15     | (default)| UNDERLINE | O   | `+ZZZ,ZZZ,ZZZ.99`     | Cycle credit           |
| ACRCYDB    | 10  | 61  | 15     | (default)| UNDERLINE | O   | `+ZZZ,ZZZ,ZZZ.99`     | Cycle debit            |

**PICOUT note:** The `+ZZZ,ZZZ,ZZZ.99` picture string produces a signed, comma-formatted decimal output. A leading `+` or `-` sign indicates credit or debit balances.

#### Account Group (row 10)

| Field Name | Row | Col | Length | ATTRB    | Hilight   | I/O |
|------------|-----|-----|--------|----------|-----------|-----|
| AADDGRP    | 10  | 23  | 10     | (default)| UNDERLINE | O   |

### Customer Details Section (rows 11–20)

#### Customer ID and SSN (row 12)

| Field Name | Row | Col | Length | ATTRB    | Hilight   | I/O | Notes                                          |
|------------|-----|-----|--------|----------|-----------|-----|------------------------------------------------|
| ACSTNUM    | 12  | 23  | 9      | (default)| UNDERLINE | O   | Customer ID — display only                     |
| (label)    | 12  | 49  | 4      | —        | —         | O   | `SSN:`                                         |
| ACSTSSN    | 12  | 54  | 12     | (default)| UNDERLINE | O   | Full SSN as single 12-char field (vs. 3 fields in COACTUP) |
| (stopper)  | 12  | 67  | 0      | —        | —         | —   |                                                |

#### Date of Birth and FICO (row 13)

| Field Name | Row | Col | Length | ATTRB    | Hilight   | I/O | Notes                  |
|------------|-----|-----|--------|----------|-----------|-----|------------------------|
| ACSTDOB    | 13  | 23  | 10     | (default)| UNDERLINE | O   | Date of birth — single 10-char field |
| (stopper)  | 13  | 34  | 0      | —        | —         | —   |                        |
| ACSTFCO    | 13  | 61  | 3      | (default)| UNDERLINE | O   | FICO score             |
| (stopper)  | 13  | 65  | 0      | —        | —         | —   |                        |

#### Name Fields (rows 14–15)

| Field Name | Row | Col | Length | ATTRB    | Hilight   | I/O |
|------------|-----|-----|--------|----------|-----------|-----|
| ACSFNAM    | 15  | 1   | 25     | (default)| UNDERLINE | O   |
| ACSMNAM    | 15  | 28  | 25     | (default)| UNDERLINE | O   |
| ACSLNAM    | 15  | 55  | 25     | (default)| UNDERLINE | O   |

#### Address (rows 16–18)

| Field Name | Row | Col | Length | ATTRB    | Hilight   | I/O |
|------------|-----|-----|--------|----------|-----------|-----|
| ACSADL1    | 16  | 10  | 50     | (default)| UNDERLINE | O   |
| ACSSTTE    | 16  | 73  | 2      | (default)| UNDERLINE | O   |
| ACSADL2    | 17  | 10  | 50     | (default)| UNDERLINE | O   |
| ACSZIPC    | 17  | 73  | 5      | (default)| UNDERLINE | O   |
| ACSCITY    | 18  | 10  | 50     | (default)| UNDERLINE | O   |
| ACSCTRY    | 18  | 73  | 3      | (default)| UNDERLINE | O   |

#### Phone and Other (rows 19–20)

Unlike COACTUP which splits phone into 3 sub-fields, COACTVW uses single 13-char consolidated phone fields:

| Field Name | Row | Col | Length | ATTRB    | Hilight   | I/O | Notes              |
|------------|-----|-----|--------|----------|-----------|-----|--------------------|
| ACSPHN1    | 19  | 10  | 13     | (default)| UNDERLINE | O   | Phone 1 — single field |
| ACSGOVT    | 19  | 58  | 20     | (default)| UNDERLINE | O   | Govt ID reference  |
| ACSPHN2    | 20  | 10  | 13     | (default)| UNDERLINE | O   | Phone 2 — single field |
| ACSEFTC    | 20  | 41  | 10     | (default)| UNDERLINE | O   | EFT account ID     |
| ACSPFLG    | 20  | 78  | 1      | (default)| UNDERLINE | O   | Primary holder flag|

### System/Status Fields (rows 22–24)

| Field Name | Row | Col | Length | ATTRB          | Color   | I/O | Notes                          |
|------------|-----|-----|--------|----------------|---------|-----|--------------------------------|
| INFOMSG    | 22  | 23  | 45     | PROT           | NEUTRAL | O   | Info message; HILIGHT=OFF; PROT (no cursor) |
| (stopper)  | 22  | 69  | 0      | —              | —       | —   |                                |
| (filler)   | 1   | 1   | 9      | —              | —       | —   | Internal 9-byte unnamed field  |
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED     | O   | Error message                  |
| (fkeys)    | 24  | 1   | 60     | ASKIP,NORM     | TURQUOISE| O  | `  F3=Exit ` (note leading spaces; padded to 60) |

---

## 5. ACCTSID Field — Special Attributes

ACCTSID is the only interactive input field. Its BMS definition includes:
- `VALIDN=(MUSTFILL)` — the terminal's hardware validation requires the field to be non-blank before the AID key transmission is accepted
- `PICIN='99999999999'` — restricts terminal-side input to 11 numeric digits
- `FSET` — retransmits the current value on the next RECEIVE even if unchanged
- `IC` — cursor defaults here

---

## 6. Screen Navigation

| Key  | Action                                                                         |
|------|--------------------------------------------------------------------------------|
| ENTER| Fetches and displays account for the entered Account Number                    |
| PF3  | Returns to previous screen (main menu)                                         |

---

## 7. Validation Rules

| Field   | BMS Constraint                                 | Program-Level Validation                     |
|---------|------------------------------------------------|----------------------------------------------|
| ACCTSID | Length=11, UNPROT, MUSTFILL, PICIN=99999999999 | Must exist in the account file/table         |

All other fields are output-only (ASKIP or default-protected); no input validation applies to them.

---

## 8. Key Structural Differences: COACTVW vs COACTUP

| Aspect                | COACTVW (View)                    | COACTUP (Update)                    |
|-----------------------|-----------------------------------|-------------------------------------|
| Date display          | Single 10-char fields (ADTOPEN, AEXPDT, AREISDT) | Split year/month/day fields |
| SSN display           | Single ACSTSSN (12 chars)         | Split ACTSSN1/2/3 (3/2/4)           |
| Phone display         | Single ACSPHN1/2 (13 chars each)  | Split ACSPH1A/B/C, ACSPH2A/B/C      |
| DOB display           | Single ACSTDOB (10 chars)         | Split DOBYEAR/DOBMON/DOBDAY         |
| Financial PICOUT      | +ZZZ,ZZZ,ZZZ.99 formatted output | Free-form alphanumeric              |
| Data field protection | Nearly all ASKIP/default-PROT     | Nearly all UNPROT for editing       |
| ACCTSID               | FSET,IC,NORM,UNPROT + MUSTFILL    | IC,UNPROT (no MUSTFILL, no FSET)    |

---

## 9. Related Screens

| Screen  | Mapset  | Relationship                                              |
|---------|---------|-----------------------------------------------------------|
| COMEN01 | COMEN01 | Navigate FROM (regular user account view option)          |
| COACTUP | COACTUP | Navigate TO (update the currently viewed account)         |
