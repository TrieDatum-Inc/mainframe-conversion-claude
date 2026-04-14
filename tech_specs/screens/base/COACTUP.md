# COACTUP — Account Update Screen Technical Specification

## 1. Screen Overview

**Purpose:** Provides a full-form edit interface for updating an existing credit card account record and its linked customer details. The operator can modify account financial parameters (credit limit, cash limit, balance), dates (opened, expiry, reissue), customer identity fields (name, SSN, date of birth, FICO score), address, phone numbers, and administrative flags.

**Driving Program:** COACTUPC (Account Update program)

**Source File:** `/app/bms/COACTUP.bms`
**Copybook:** `/app/cpy-bms/COACTUP.CPY`

---

## 2. Map/Mapset Definition

| Attribute    | Value                          |
|--------------|--------------------------------|
| MAPSET name  | COACTUP                        |
| MAP name     | CACTUPA                        |
| SIZE         | (24, 80)                       |
| CTRL         | FREEKB                         |
| DSATTS       | COLOR, HILIGHT, PS, VALIDN     |
| MAPATTS      | COLOR, HILIGHT, PS, VALIDN     |
| LANG         | COBOL                          |
| MODE         | INOUT                          |
| STORAGE      | AUTO                           |
| TIOAPFX      | YES                            |
| TYPE         | &&SYSPARM                      |

**Notable differences from menu maps:**
- No ALARM in CTRL (keyboard unlocks silently)
- No EXTATT=YES at mapset level; instead DSATTS and MAPATTS are explicitly declared on the DFHMDI, enabling dynamic attribute modification per field
- No COLUMN= / LINE= on DFHMDI (defaults to full-screen overlay)

---

## 3. Screen Layout (ASCII Representation)

```
Col:  1         2         3         4         5         6         7         8
      12345678901234567890123456789012345678901234567890123456789012345678901234567890
Row1: Tran:[TRNM]          [----------TITLE01----------]     Date:[CURDATE-]
Row2: Prog:[PGMNAME]       [----------TITLE02----------]     Time:[CURTIME-]
Row3:
Row4:                                Update Account
Row5:   Account Number :[ACCTSID---]          Active Y/N: [A]
Row6: Opened :[YYYY]-[MM]-[DD]                Credit Limit        :[ACRDLIM-------]
Row7: Expiry :[YYYY]-[MM]-[DD]                Cash credit Limit   :[ACSHLIM-------]
Row8: Reissue:[YYYY]-[MM]-[DD]                Current Balance     :[ACURBAL-------]
Row9:                                         Current Cycle Credit:[ACRCYCR-------]
Row10:   Account Group:[AADDGRP--]            Current Cycle Debit :[ACRCYDB-------]
Row11:                               Customer Details
Row12:   Customer id  :[ACSTNUM-]             SSN:[SSN1]-[SS2]-[SSN3]
Row13:   Date of birth:[YYYY]-[MM]-[DD]       FICO Score:[FCO]
Row14: First Name           Middle Name:         Last Name :
Row15: [ACSFNAM-----------------][ACSMNAM-----------------][ACSLNAM-----------------]
Row16: Address:[ACSADL1------------------------------------------]  State [ST]
Row17:         [ACSADL2------------------------------------------]  Zip[ACSZIPC]
Row18: City   [ACSCITY------------------------------------------]  Country[CTR]
Row19: Phone 1:[PH1][PH2][PH3]    Government Issued Id Ref    : [ACSGOVT-----------]
Row20: Phone 2:[PH1][PH2][PH3]    EFT Account Id: [ACSEFTC--]  Primary Card Holder Y/N:[P]
Row21:
Row22:                       [INFOMSG----------------------------------]
Row23: [---------------------------ERRMSG------------------------------------]
Row24: ENTER=Process F3=Exit        F5=Save   F12=Cancel
```

---

## 4. Field Definitions

### Header Fields (rows 1–2)

| Field Name | Row | Col | Length | ATTRB      | Color  | I/O | Notes                        |
|------------|-----|-----|--------|------------|--------|-----|------------------------------|
| (label)    | 1   | 1   | 5      | ASKIP,NORM | BLUE   | O   | `Tran:`                      |
| TRNNAME    | 1   | 7   | 4      | ASKIP,NORM | BLUE   | O   | Transaction ID               |
| TITLE01    | 1   | 21  | 40     | ASKIP,NORM | YELLOW | O   | Title line 1                 |
| (label)    | 1   | 65  | 5      | ASKIP,NORM | BLUE   | O   | `Date:`                      |
| CURDATE    | 1   | 71  | 8      | ASKIP,NORM | BLUE   | O   | Current date; init `mm/dd/yy`|
| (label)    | 2   | 1   | 5      | ASKIP,NORM | BLUE   | O   | `Prog:`                      |
| PGMNAME    | 2   | 7   | 8      | ASKIP,NORM | BLUE   | O   | Program name                 |
| TITLE02    | 2   | 21  | 40     | ASKIP,NORM | YELLOW | O   | Title line 2                 |
| (label)    | 2   | 65  | 5      | ASKIP,NORM | BLUE   | O   | `Time:`                      |
| CURTIME    | 2   | 71  | 8      | ASKIP,NORM | BLUE   | O   | Current time; init `hh:mm:ss`|

**Note:** Header fields on COACTUP use ASKIP,NORM without FSET (unlike the menu maps). This is intentional — the program re-sends the full map on each interaction.

### Account Summary Section (rows 4–10)

| Field Name | Row | Col | Length | ATTRB        | Color     | Hilight   | I/O    | Notes                              |
|------------|-----|-----|--------|--------------|-----------|-----------|--------|------------------------------------|
| (title)    | 4   | 33  | 14     | (default)    | NEUTRAL   | —         | O      | `Update Account`                   |
| (label)    | 5   | 19  | 16     | ASKIP,NORM   | TURQUOISE | —         | O      | `Account Number :`                 |
| ACCTSID    | 5   | 38  | 11     | IC,UNPROT    | —         | UNDERLINE | Input  | Account number; IC sets cursor here|
| (stopper)  | 5   | 50  | 0      | —            | —         | —         | —      | Tab stop after ACCTSID             |
| (label)    | 5   | 57  | 12     | (default)    | TURQUOISE | —         | O      | `Active Y/N: `                     |
| ACSTTUS    | 5   | 70  | 1      | UNPROT       | —         | UNDERLINE | Input  | Account active flag Y/N            |
| (stopper)  | 5   | 72  | 0      | —            | —         | —         | —      | Tab stop                           |

#### Date Fields — Opened (row 6)

| Field Name | Row | Col | Length | ATTRB        | Hilight   | I/O    | Notes                        |
|------------|-----|-----|--------|--------------|-----------|--------|------------------------------|
| (label)    | 6   | 8   | 8      | (default)    | —         | O      | `Opened :`                   |
| OPNYEAR    | 6   | 17  | 4      | FSET,UNPROT  | UNDERLINE | Input  | Open year; JUSTIFY=(RIGHT)   |
| (sep)      | 6   | 22  | 1      | (default)    | —         | O      | `-`                          |
| OPNMON     | 6   | 24  | 2      | UNPROT       | UNDERLINE | Input  | Open month; JUSTIFY=(RIGHT)  |
| (sep)      | 6   | 27  | 1      | (default)    | —         | O      | `-`                          |
| OPNDAY     | 6   | 29  | 2      | UNPROT       | UNDERLINE | Input  | Open day; JUSTIFY=(RIGHT)    |
| (stopper)  | 6   | 32  | 0      | —            | —         | —      | Tab stop                     |

#### Date Fields — Expiry (row 7)

| Field Name | Row | Col | Length | ATTRB        | Hilight   | I/O    |
|------------|-----|-----|--------|--------------|-----------|--------|
| EXPYEAR    | 7   | 17  | 4      | UNPROT       | UNDERLINE | Input  |
| EXPMON     | 7   | 24  | 2      | UNPROT       | UNDERLINE | Input  |
| EXPDAY     | 7   | 29  | 2      | UNPROT       | UNDERLINE | Input  |

#### Date Fields — Reissue (row 8)

| Field Name | Row | Col | Length | ATTRB        | Hilight   | I/O    |
|------------|-----|-----|--------|--------------|-----------|--------|
| RISYEAR    | 8   | 17  | 4      | UNPROT       | UNDERLINE | Input  |
| RISMON     | 8   | 24  | 2      | UNPROT       | UNDERLINE | Input  |
| RISDAY     | 8   | 29  | 2      | UNPROT       | UNDERLINE | Input  |

#### Financial Fields (rows 6–10, right column)

| Field Name | Row | Col | Length | ATTRB        | Color     | Hilight   | I/O    | Notes                         |
|------------|-----|-----|--------|--------------|-----------|-----------|--------|-------------------------------|
| (label)    | 6   | 39  | 21     | ASKIP,NORM   | TURQUOISE | —         | O      | `Credit Limit        :`       |
| ACRDLIM    | 6   | 61  | 15     | FSET,UNPROT  | —         | UNDERLINE | Input  | Credit limit amount           |
| (stopper)  | 6   | 77  | 0      | —            | —         | —         | —      |                               |
| (label)    | 7   | 39  | 21     | ASKIP,NORM   | TURQUOISE | —         | O      | `Cash credit Limit   :`       |
| ACSHLIM    | 7   | 61  | 15     | FSET,UNPROT  | —         | UNDERLINE | Input  | Cash advance limit            |
| (stopper)  | 7   | 77  | 0      | —            | —         | —         | —      |                               |
| (label)    | 8   | 39  | 21     | ASKIP,NORM   | TURQUOISE | —         | O      | `Current Balance     :`       |
| ACURBAL    | 8   | 61  | 15     | FSET,UNPROT  | —         | UNDERLINE | Input  | Current balance               |
| (stopper)  | 8   | 77  | 0      | —            | —         | —         | —      |                               |
| (label)    | 9   | 39  | 21     | ASKIP,NORM   | TURQUOISE | —         | O      | `Current Cycle Credit:`       |
| ACRCYCR    | 9   | 61  | 15     | FSET,UNPROT  | —         | UNDERLINE | Input  | Cycle-to-date credits         |
| (stopper)  | 9   | 77  | 0      | —            | —         | —         | —      |                               |
| (label)    | 10  | 39  | 21     | ASKIP,NORM   | TURQUOISE | —         | O      | `Current Cycle Debit :`       |
| ACRCYDB    | 10  | 61  | 15     | FSET,UNPROT  | —         | UNDERLINE | Input  | Cycle-to-date debits          |
| (stopper)  | 10  | 77  | 0      | —            | —         | —         | —      |                               |

#### Account Group (row 10)

| Field Name | Row | Col | Length | ATTRB   | Color     | Hilight   | I/O   |
|------------|-----|-----|--------|---------|-----------|-----------|-------|
| (label)    | 10  | 8   | 14     | —       | TURQUOISE | —         | O     |
| AADDGRP    | 10  | 23  | 10     | UNPROT  | —         | UNDERLINE | Input |
| (stopper)  | 10  | 34  | 0      | —       | —         | —         | —     |

### Customer Details Section (rows 11–20)

#### Customer ID and SSN (row 12)

| Field Name | Row | Col | Length | ATTRB   | Hilight   | I/O    | Notes                                     |
|------------|-----|-----|--------|---------|-----------|--------|-------------------------------------------|
| (label)    | 12  | 8   | 14     | —       | —         | O      | `Customer id  :`                          |
| ACSTNUM    | 12  | 23  | 9      | UNPROT  | UNDERLINE | Input  | Customer ID number                        |
| (stopper)  | 12  | 33  | 0      | —       | —         | —      |                                           |
| (label)    | 12  | 49  | 4      | —       | —         | O      | `SSN:`                                    |
| ACTSSN1    | 12  | 55  | 3      | UNPROT  | UNDERLINE | Input  | SSN part 1 (3 digits); init `999`         |
| (sep)      | 12  | 59  | 1      | —       | —         | O      | `-`                                       |
| ACTSSN2    | 12  | 61  | 2      | UNPROT  | UNDERLINE | Input  | SSN part 2 (2 digits); init `99`          |
| (sep)      | 12  | 64  | 1      | —       | —         | O      | `-`                                       |
| ACTSSN3    | 12  | 66  | 4      | UNPROT  | UNDERLINE | Input  | SSN part 3 (4 digits); init `9999`        |
| (stopper)  | 12  | 71  | 0      | —       | —         | —      |                                           |

#### Date of Birth (row 13)

| Field Name | Row | Col | Length | ATTRB   | Hilight   | I/O    |
|------------|-----|-----|--------|---------|-----------|--------|
| DOBYEAR    | 13  | 23  | 4      | UNPROT  | UNDERLINE | Input  |
| DOBMON     | 13  | 30  | 2      | UNPROT  | UNDERLINE | Input  |
| DOBDAY     | 13  | 35  | 2      | UNPROT  | UNDERLINE | Input  |

#### FICO Score (row 13)

| Field Name | Row | Col | Length | ATTRB   | Hilight   | I/O    | Notes          |
|------------|-----|-----|--------|---------|-----------|--------|----------------|
| ACSTFCO    | 13  | 62  | 3      | UNPROT  | UNDERLINE | Input  | FICO score 3-digit |

#### Name Fields (rows 14–15)

| Field Name | Row | Col | Length | ATTRB   | Hilight   | I/O    | Notes            |
|------------|-----|-----|--------|---------|-----------|--------|------------------|
| (label)    | 14  | 1   | 10     | —       | —         | O      | `First Name`     |
| (label)    | 14  | 28  | 13     | —       | —         | O      | `Middle Name: `  |
| (label)    | 14  | 55  | 12     | —       | —         | O      | `Last Name : `   |
| ACSFNAM    | 15  | 1   | 25     | UNPROT  | UNDERLINE | Input  | First name       |
| (stopper)  | 15  | 27  | 0      | —       | —         | —      |                  |
| ACSMNAM    | 15  | 28  | 25     | UNPROT  | UNDERLINE | Input  | Middle name      |
| (stopper)  | 15  | 54  | 0      | —       | —         | —      |                  |
| ACSLNAM    | 15  | 55  | 25     | UNPROT  | UNDERLINE | Input  | Last name        |

#### Address Fields (rows 16–18)

| Field Name | Row | Col | Length | ATTRB   | Hilight   | I/O    | Notes                |
|------------|-----|-----|--------|---------|-----------|--------|----------------------|
| (label)    | 16  | 1   | 8      | —       | —         | O      | `Address:`           |
| ACSADL1    | 16  | 10  | 50     | UNPROT  | UNDERLINE | Input  | Address line 1       |
| (stopper)  | 16  | 61  | 0      | —       | —         | —      |                      |
| (label)    | 16  | 63  | 6      | —       | —         | O      | `State `             |
| ACSSTTE    | 16  | 73  | 2      | UNPROT  | UNDERLINE | Input  | State code           |
| (stopper)  | 16  | 76  | 0      | —       | —         | —      |                      |
| ACSADL2    | 17  | 10  | 50     | UNPROT  | UNDERLINE | Input  | Address line 2       |
| (stopper)  | 17  | 61  | 0      | —       | —         | —      |                      |
| (label)    | 17  | 63  | 3      | —       | —         | O      | `Zip`                |
| ACSZIPC    | 17  | 73  | 5      | UNPROT  | UNDERLINE | Input  | ZIP code             |
| (stopper)  | 17  | 79  | 0      | —       | —         | —      |                      |
| (label)    | 18  | 1   | 5      | —       | —         | O      | `City `              |
| ACSCITY    | 18  | 10  | 50     | UNPROT  | UNDERLINE | Input  | City                 |
| (stopper)  | 18  | 61  | 0      | —       | —         | —      |                      |
| (label)    | 18  | 63  | 7      | —       | —         | O      | `Country`            |
| ACSCTRY    | 18  | 73  | 3      | UNPROT  | UNDERLINE | Input  | Country code         |
| (stopper)  | 18  | 77  | 0      | —       | —         | —      |                      |

#### Phone Fields (rows 19–20)

| Field Name | Row | Col | Length | ATTRB                  | Hilight   | I/O    | Notes               |
|------------|-----|-----|--------|------------------------|-----------|--------|---------------------|
| (label)    | 19  | 1   | 8      | —                      | —         | O      | `Phone 1:`          |
| ACSPH1A    | 19  | 10  | 3      | UNPROT, JUSTIFY=(RIGHT)| UNDERLINE | Input  | Area code           |
| ACSPH1B    | 19  | 14  | 3      | UNPROT, JUSTIFY=(RIGHT)| UNDERLINE | Input  | Exchange            |
| ACSPH1C    | 19  | 18  | 4      | UNPROT, JUSTIFY=(RIGHT)| UNDERLINE | Input  | Number              |
| (stopper)  | 19  | 23  | 0      | —                      | —         | —      |                     |
| (label)    | 19  | 24  | 30     | —                      | —         | O      | `Government Issued Id Ref    : ` |
| ACSGOVT    | 19  | 58  | 20     | UNPROT                 | UNDERLINE | Input  | Govt ID reference   |
| (stopper)  | 19  | 79  | 0      | —                      | —         | —      |                     |
| (label)    | 20  | 1   | 8      | —                      | —         | O      | `Phone 2:`          |
| ACSPH2A    | 20  | 10  | 3      | UNPROT, JUSTIFY=(RIGHT)| UNDERLINE | Input  | Area code           |
| ACSPH2B    | 20  | 14  | 3      | UNPROT, JUSTIFY=(RIGHT)| UNDERLINE | Input  | Exchange            |
| ACSPH2C    | 20  | 18  | 4      | UNPROT, JUSTIFY=(RIGHT)| UNDERLINE | Input  | Number              |
| (stopper)  | 20  | 23  | 0      | —                      | —         | —      |                     |
| (label)    | 20  | 24  | 16     | —                      | —         | O      | `EFT Account Id: `  |
| ACSEFTC    | 20  | 41  | 10     | UNPROT                 | UNDERLINE | Input  | EFT/ACH account ID  |
| (stopper)  | 20  | 52  | 0      | —                      | —         | —      |                     |
| (label)    | 20  | 53  | 24     | —                      | —         | O      | `Primary Card Holder Y/N:`|
| ACSPFLG    | 20  | 78  | 1      | UNPROT                 | UNDERLINE | Input  | Primary holder flag Y/N |
| (stopper)  | 20  | 80  | 0      | —                      | —         | —      |                     |

### System/Status Fields (rows 22–24)

| Field Name | Row | Col | Length | ATTRB          | Color   | I/O | Notes                                    |
|------------|-----|-----|--------|----------------|---------|-----|------------------------------------------|
| INFOMSG    | 22  | 23  | 45     | ASKIP           | NEUTRAL | O   | Informational message; HILIGHT=OFF       |
| (stopper)  | 22  | 69  | 0      | —              | —       | —   |                                          |
| (filler)   | 1   | 1   | 9      | —              | —       | —   | 9-byte unnamed field at (1,1) — internal padding |
| ERRMSG     | 23  | 1   | 78     | ASKIP,BRT,FSET | RED     | O   | Error message                            |
| FKEYS      | 24  | 1   | 21     | ASKIP,NORM     | YELLOW  | O   | `ENTER=Process F3=Exit`                  |
| FKEY05     | 24  | 23  | 7      | ASKIP,DRK      | YELLOW  | O   | `F5=Save` — dark (hidden unless activated) |
| FKEY12     | 24  | 31  | 10     | ASKIP,DRK      | YELLOW  | O   | `F12=Cancel` — dark initially            |

**FKEY05 and FKEY12 are DRK (dark/hidden).** The program makes them visible (by changing the attribute byte to NORM or BRT) when the screen is in a state where Save and Cancel are applicable.

---

## 5. Screen Navigation

| Key   | Action                                                                               |
|-------|--------------------------------------------------------------------------------------|
| ENTER | Submits the form; program validates fields and performs account update               |
| PF3   | Exits to previous screen (account inquiry / main menu)                               |
| PF5   | Save — explicitly saves current field values (visible after initial data load)       |
| PF12  | Cancel — abandons changes without saving                                             |

---

## 6. Data Flow

1. Program pre-populates all fields from the account/customer record before SEND MAP (MAPONLY or DATAONLY)
2. Operator modifies desired fields and presses ENTER or PF5
3. Program RECEIVE MAPOs: reads all `I` fields from COACTUPAI structure
4. Program validates (see section 7) and either re-sends with errors or commits update
5. On success, INFOMSG is set to a confirmation message and map is re-sent

---

## 7. Validation Rules

All validation is performed by COACTUPC. BMS structural constraints are:

| Field          | BMS Constraint                        | Implied Validation                                     |
|----------------|---------------------------------------|--------------------------------------------------------|
| ACCTSID        | Length=11, UNPROT, IC                 | Must match an existing account record                  |
| ACSTTUS        | Length=1, UNPROT                      | Must be Y or N                                         |
| OPNYEAR/MON/DAY| Length=4/2/2, UNPROT, JUSTIFY=(RIGHT) | Must form a valid calendar date                        |
| EXPYEAR/MON/DAY| Length=4/2/2, UNPROT                  | Must form a valid future date                          |
| RISYEAR/MON/DAY| Length=4/2/2, UNPROT                  | Must form a valid date                                 |
| ACRDLIM        | Length=15, FSET,UNPROT                | Numeric; must be >= 0                                  |
| ACSHLIM        | Length=15, FSET,UNPROT                | Numeric; must be >= 0 and <= ACRDLIM                   |
| ACURBAL        | Length=15, FSET,UNPROT                | Numeric                                                |
| ACTSSN1/2/3    | Length=3/2/4, UNPROT                  | Numeric SSN components                                 |
| ACSTFCO        | Length=3, UNPROT                      | Numeric 300–850 range (FICO range) — program logic     |
| ACSPFLG        | Length=1, UNPROT                      | Must be Y or N                                         |

---

## 8. Related Screens

| Screen  | Mapset  | Relationship                                            |
|---------|---------|---------------------------------------------------------|
| COACTVW | COACTVW | Navigate FROM (view account before edit)                |
| COMEN01 | COMEN01 | Navigate TO/FROM (main menu)                            |
