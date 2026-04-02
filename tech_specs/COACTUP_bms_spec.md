# Technical Specification: COACTUP.BMS (Account Update Screen)

## 1. Overview

| Property | Value | Source |
|---|---|---|
| BMS Source File | `app/bms/COACTUP.bms` |  |
| Mapset Name | COACTUP | Line 20 |
| Map Name | CACTUPA | Line 25 |
| Screen Title | "Update Account" | Line 78 |
| Screen Size | 24 rows x 80 columns | Line 28 |
| MODE | INOUT | Line 21 |
| LANG | COBOL | Line 20 |
| STORAGE | AUTO | Line 22 |
| TIOAPFX | YES | Line 23 |
| TYPE | &&SYSPARM | Line 24 (resolved at assembly time) |

The mapset is compiled twice using &&SYSPARM — once with TYPE=MAP (physical screen layout) and once with TYPE=DSECT (COBOL copybook for CACTUPAI/CACTUPAO structures).

The map supports extended 3270 attributes via DSATTS and MAPATTS: COLOR, HILIGHT, PS (programmed symbols), VALIDN (validation).

Map CTRL attribute: FREEKB — automatically unlocks keyboard after SEND.

---

## 2. Functional Purpose

COACTUP/CACTUPA is the data entry and update screen for the account management function, used exclusively by COACTUPC (transaction CAUP). The screen serves dual purposes across different passes of the pseudo-conversational transaction:
1. **Pass 1 (search mode):** Only the Account Number field is editable; all other fields are blank and protected.
2. **Pass 2+ (edit mode):** Account number is protected; all account and customer data fields become editable for modification.
3. **Confirmation mode:** All fields become protected; only the informational message confirms pending save.

---

## 3. Screen Layout

```
Col:  1         10        20        30        40        50        60        70        80
Row 1: Tran:XXXX          [TITLE01 - 40 chars          ]     Date:MM/DD/YY
Row 2: Prog:XXXXXXXX      [TITLE02 - 40 chars          ]     Time:HH:MM:SS
Row 3: (blank)
Row 4:                         Update Account
Row 5:          Account Number :[ACCTSID   11]  Active Y/N: [A]
Row 6: Opened :[YYYY]-[MM]-[DD]   Credit Limit        :[  ACRDLIM 15  ]
Row 7: Expiry :[YYYY]-[MM]-[DD]   Cash credit Limit   :[  ACSHLIM 15  ]
Row 8: Reissue:[YYYY]-[MM]-[DD]   Current Balance     :[  ACURBAL 15  ]
Row 9:                            Current Cycle Credit:[  ACRCYCR 15  ]
Row10: Account Group:[AADDGRP 10]  Current Cycle Debit :[  ACRCYDB 15  ]
Row11:                                 Customer Details
Row12: Customer id  :[ACSTNUM 9]   SSN:[ SSN1 3]-[SSN2 2]-[SSN3 4]
Row13: Date of birth:[YYYY]-[MM]-[DD]  FICO Score:[ FCO 3]
Row14: First Name              Middle Name:           Last Name :
Row15: [ACSFNAM 25          ][ACSMNAM 25           ][ACSLNAM 25        ]
Row16: Address:[ACSADL1 50               ]  State [ST]
Row17:         [ACSADL2 50               ]  Zip[ZIPPP]
Row18: City   [ACSCITY 50               ]  Country[CTY]
Row19: Phone 1:[PH1][PH2][PH3]   Government Issued Id Ref    : [ACSGOVT  20  ]
Row20: Phone 2:[PH1][PH2][PH3]   EFT Account Id: [ACSEFTC 10]  Primary Card Holder Y/N:[F]
Row21: (blank)
Row22:                        [INFOMSG 45              ]
Row23: [ERRMSG 78                                                            ]
Row24: ENTER=Process F3=Exit  [F5=Save ] [F12=Cancel]
```

---

## 4. Field Inventory

### 4.1 Header Fields (Rows 1-2)

| Field Name | POS | Length | ATTRB | COLOR | Description |
|---|---|---|---|---|---|
| (literal) | (1,1) | 5 | ASKIP,NORM | BLUE | Static label "Tran:" |
| TRNNAME | (1,7) | 4 | ASKIP,FSET,NORM | BLUE | Current transaction ID (output) |
| TITLE01 | (1,21) | 40 | ASKIP,NORM | YELLOW | Application title line 1 (output) |
| (literal) | (1,65) | 5 | ASKIP,NORM | BLUE | Static label "Date:" |
| CURDATE | (1,71) | 8 | ASKIP,NORM | BLUE | Current date MM/DD/YY, init='mm/dd/yy' |
| (literal) | (2,1) | 5 | ASKIP,NORM | BLUE | Static label "Prog:" |
| PGMNAME | (2,7) | 8 | ASKIP,NORM | BLUE | Current program name (output) |
| TITLE02 | (2,21) | 40 | ASKIP,NORM | YELLOW | Application title line 2 (output) |
| (literal) | (2,65) | 5 | ASKIP,NORM | BLUE | Static label "Time:" |
| CURTIME | (2,71) | 8 | ASKIP,NORM | BLUE | Current time HH:MM:SS, init='hh:mm:ss' |

### 4.2 Screen Title (Row 4)

| Field Name | POS | Length | COLOR | Description |
|---|---|---|---|---|
| (no name) | (4,33) | 14 | NEUTRAL | Static label "Update Account" |

### 4.3 Account Identification and Status (Row 5)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (5,19) | 16 | ASKIP,NORM | — | TURQUOISE "Account Number :" |
| ACCTSID | (5,38) | 11 | IC,UNPROT | UNDERLINE | Account number (key input field, initial cursor) |
| (stopper) | (5,50) | 0 | — | — | Field stopper |
| (literal) | (5,57) | 12 | — | — | TURQUOISE "Active Y/N: " |
| ACSTTUS | (5,70) | 1 | UNPROT | UNDERLINE | Account active status Y or N |
| (stopper) | (5,72) | 0 | — | — | Field stopper |

**ACCTSID notes:**
- IC (Insert Cursor) attribute positions cursor here on initial display
- UNPROT allows operator input
- No FSET in map definition — COACTUPC sets/clears protection dynamically

**ACSTTUS notes:**
- UNPROT (no FSET default from BMS)
- Protected (DFHBMPRF) by 3310-PROTECT-ALL-ATTRS in COACTUPC
- Unprotected (DFHBMFSE) by 3320-UNPROTECT-FEW-ATTRS when account data is shown

### 4.4 Account Open Date (Row 6, left side)

| Field Name | POS | Length | ATTRB | HILIGHT | JUSTIFY | Description |
|---|---|---|---|---|---|---|
| (literal) | (6,8) | 8 | — | — | — | TURQUOISE "Opened :" |
| OPNYEAR | (6,17) | 4 | FSET,UNPROT | UNDERLINE | RIGHT | 4-digit open year |
| (literal) | (6,22) | 1 | — | — | — | '-' separator |
| OPNMON | (6,24) | 2 | UNPROT | UNDERLINE | RIGHT | 2-digit open month |
| (literal) | (6,27) | 1 | — | — | — | '-' separator |
| OPNDAY | (6,29) | 2 | UNPROT | UNDERLINE | RIGHT | 2-digit open day |
| (stopper) | (6,32) | 0 | — | — | — | Field stopper |

### 4.5 Credit Limit (Row 6, right side)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (6,39) | 21 | ASKIP,NORM | — | TURQUOISE "Credit Limit        :" |
| ACRDLIM | (6,61) | 15 | FSET,UNPROT | UNDERLINE | Credit limit (signed currency, e.g. +999,999,999.99) |
| (stopper) | (6,77) | 0 | — | — | Field stopper |

### 4.6 Account Expiry Date (Row 7, left side)

| Field Name | POS | Length | ATTRB | HILIGHT | JUSTIFY | Description |
|---|---|---|---|---|---|---|
| (literal) | (7,8) | 8 | — | — | — | TURQUOISE "Expiry :" |
| EXPYEAR | (7,17) | 4 | UNPROT | UNDERLINE | RIGHT | 4-digit expiry year |
| (literal) | (7,22) | 1 | — | — | — | '-' separator |
| EXPMON | (7,24) | 2 | UNPROT | UNDERLINE | RIGHT | 2-digit expiry month |
| (literal) | (7,27) | 1 | — | — | — | '-' separator |
| EXPDAY | (7,29) | 2 | UNPROT | UNDERLINE | RIGHT | 2-digit expiry day |
| (stopper) | (7,32) | 0 | — | — | — | Field stopper |

### 4.7 Cash Credit Limit (Row 7, right side)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (7,39) | 21 | ASKIP,NORM | — | TURQUOISE "Cash credit Limit   :" |
| ACSHLIM | (7,61) | 15 | FSET,UNPROT | UNDERLINE | Cash credit limit (signed currency) |
| (stopper) | (7,77) | 0 | — | — | Field stopper |

### 4.8 Reissue Date (Row 8, left side)

| Field Name | POS | Length | ATTRB | HILIGHT | JUSTIFY | Description |
|---|---|---|---|---|---|---|
| (literal) | (8,8) | 8 | — | — | — | TURQUOISE "Reissue:" |
| RISYEAR | (8,17) | 4 | UNPROT | UNDERLINE | RIGHT | 4-digit reissue year |
| (literal) | (8,22) | 1 | — | — | — | '-' separator |
| RISMON | (8,24) | 2 | UNPROT | UNDERLINE | RIGHT | 2-digit reissue month |
| (literal) | (8,27) | 1 | — | — | — | '-' separator |
| RISDAY | (8,29) | 2 | UNPROT | UNDERLINE | RIGHT | 2-digit reissue day |
| (stopper) | (8,32) | 0 | — | — | — | Field stopper |

### 4.9 Current Balance (Row 8, right side)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (8,39) | 21 | ASKIP,NORM | — | TURQUOISE "Current Balance     :" |
| ACURBAL | (8,61) | 15 | FSET,UNPROT | UNDERLINE | Current account balance (signed currency) |
| (stopper) | (8,77) | 0 | — | — | Field stopper |

### 4.10 Current Cycle Credit (Row 9, right side)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (9,39) | 21 | ASKIP,NORM | — | TURQUOISE "Current Cycle Credit:" |
| ACRCYCR | (9,61) | 15 | FSET,UNPROT | UNDERLINE | Current cycle credit amount |
| (stopper) | (9,77) | 0 | — | — | Field stopper |

### 4.11 Account Group and Current Cycle Debit (Row 10)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (10,8) | 14 | — | — | TURQUOISE "Account Group:" |
| AADDGRP | (10,23) | 10 | UNPROT | UNDERLINE | Account group ID |
| (stopper) | (10,34) | 0 | — | — | Field stopper |
| (literal) | (10,39) | 21 | ASKIP,NORM | — | TURQUOISE "Current Cycle Debit :" |
| ACRCYDB | (10,61) | 15 | FSET,UNPROT | UNDERLINE | Current cycle debit amount |
| (stopper) | (10,77) | 0 | — | — | Field stopper |

### 4.12 Customer Details Section Header (Row 11)

| Field Name | POS | Length | COLOR | Description |
|---|---|---|---|---|
| (literal) | (11,32) | 16 | NEUTRAL | "Customer Details" section header |

### 4.13 Customer ID and SSN (Row 12)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (12,8) | 14 | — | — | TURQUOISE "Customer id  :" |
| ACSTNUM | (12,23) | 9 | UNPROT | UNDERLINE | Customer ID (display only — protected by COACTUPC) |
| (stopper) | (12,33) | 0 | — | — | Field stopper |
| (literal) | (12,49) | 4 | — | — | TURQUOISE "SSN:" |
| ACTSSN1 | (12,55) | 3 | UNPROT | UNDERLINE | SSN part 1 (3 digits), init='999' |
| (literal) | (12,59) | 1 | — | — | '-' separator |
| ACTSSN2 | (12,61) | 2 | UNPROT | UNDERLINE | SSN part 2 (2 digits), init='99' |
| (literal) | (12,64) | 1 | — | — | '-' separator |
| ACTSSN3 | (12,66) | 4 | UNPROT | UNDERLINE | SSN part 3 (4 digits), init='9999' |
| (stopper) | (12,71) | 0 | — | — | Field stopper |

**Note:** ACTSSN1/2/3 have INITIAL values of '999', '99', '9999' as placeholder indicators. The program overwrites these with actual or blank values on display.

### 4.14 Date of Birth and FICO Score (Row 13)

| Field Name | POS | Length | ATTRB | HILIGHT | JUSTIFY | Description |
|---|---|---|---|---|---|---|
| (literal) | (13,8) | 14 | — | — | — | TURQUOISE "Date of birth:" |
| DOBYEAR | (13,23) | 4 | UNPROT | UNDERLINE | RIGHT | Birth year (4 digits) |
| (literal) | (13,28) | 1 | — | — | — | '-' separator |
| DOBMON | (13,30) | 2 | UNPROT | UNDERLINE | RIGHT | Birth month (2 digits) |
| (literal) | (13,33) | 1 | — | — | — | '-' separator |
| DOBDAY | (13,35) | 2 | UNPROT | UNDERLINE | RIGHT | Birth day (2 digits) |
| (stopper) | (13,38) | 0 | — | — | — | Field stopper |
| (literal) | (13,49) | 11 | — | — | — | TURQUOISE "FICO Score:" |
| ACSTFCO | (13,62) | 3 | UNPROT | UNDERLINE | — | FICO credit score (3 digits, 300-850) |
| (stopper) | (13,66) | 0 | — | — | — | Field stopper |

### 4.15 Name Column Headers (Row 14)

| POS | Length | COLOR | Content |
|---|---|---|---|
| (14,1) | 10 | TURQUOISE | "First Name" |
| (14,28) | 13 | TURQUOISE | "Middle Name: " |
| (14,55) | 12 | TURQUOISE | "Last Name : " |

### 4.16 Name Input Fields (Row 15)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| ACSFNAM | (15,1) | 25 | UNPROT | UNDERLINE | Customer first name |
| (stopper) | (15,27) | 0 | — | — | Field stopper |
| ACSMNAM | (15,28) | 25 | UNPROT | UNDERLINE | Customer middle name (optional) |
| (stopper) | (15,54) | 0 | — | — | Field stopper |
| ACSLNAM | (15,55) | 25 | UNPROT | UNDERLINE | Customer last name |

### 4.17 Address Line 1 and State (Row 16)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (16,1) | 8 | — | — | TURQUOISE "Address:" |
| ACSADL1 | (16,10) | 50 | UNPROT | UNDERLINE | Address line 1 |
| (stopper) | (16,61) | 0 | — | — | Field stopper |
| (literal) | (16,63) | 6 | — | — | TURQUOISE "State " |
| ACSSTTE | (16,73) | 2 | UNPROT | UNDERLINE | State code (2 chars, US state) |
| (stopper) | (16,76) | 0 | — | — | Field stopper |

### 4.18 Address Line 2 and Zip Code (Row 17)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| ACSADL2 | (17,10) | 50 | UNPROT | UNDERLINE | Address line 2 (optional, no edits) |
| (stopper) | (17,61) | 0 | — | — | Field stopper |
| (literal) | (17,63) | 3 | — | — | TURQUOISE "Zip" |
| ACSZIPC | (17,73) | 5 | UNPROT | UNDERLINE | Zip code (5 digits) |
| (stopper) | (17,79) | 0 | — | — | Field stopper |

### 4.19 City and Country (Row 18)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (18,1) | 5 | — | — | TURQUOISE "City " |
| ACSCITY | (18,10) | 50 | UNPROT | UNDERLINE | City (mapped to CUST-ADDR-LINE-3) |
| (stopper) | (18,61) | 0 | — | — | Field stopper |
| (literal) | (18,63) | 7 | — | — | TURQUOISE "Country" |
| ACSCTRY | (18,73) | 3 | UNPROT | UNDERLINE | Country code (3 chars, protected in edit mode by COACTUPC) |
| (stopper) | (18,77) | 0 | — | — | Field stopper |

### 4.20 Phone 1 and Government ID (Row 19)

| Field Name | POS | Length | ATTRB | HILIGHT | JUSTIFY | Description |
|---|---|---|---|---|---|---|
| (literal) | (19,1) | 8 | — | — | — | TURQUOISE "Phone 1:" |
| ACSPH1A | (19,10) | 3 | UNPROT | UNDERLINE | RIGHT | Phone 1 area code (3 digits) |
| ACSPH1B | (19,14) | 3 | UNPROT | UNDERLINE | RIGHT | Phone 1 prefix (3 digits) |
| ACSPH1C | (19,18) | 4 | UNPROT | UNDERLINE | RIGHT | Phone 1 line number (4 digits) |
| (stopper) | (19,23) | 0 | — | — | — | Field stopper |
| (literal) | (19,24) | 30 | — | — | — | TURQUOISE "Government Issued Id Ref    : " |
| ACSGOVT | (19,58) | 20 | UNPROT | UNDERLINE | — | Government-issued ID reference |
| (stopper) | (19,79) | 0 | — | — | — | Field stopper |

### 4.21 Phone 2, EFT Account ID, Primary Card Holder (Row 20)

| Field Name | POS | Length | ATTRB | HILIGHT | JUSTIFY | Description |
|---|---|---|---|---|---|---|
| (literal) | (20,1) | 8 | — | — | — | TURQUOISE "Phone 2:" |
| ACSPH2A | (20,10) | 3 | UNPROT | UNDERLINE | RIGHT | Phone 2 area code (3 digits) |
| ACSPH2B | (20,14) | 3 | UNPROT | UNDERLINE | RIGHT | Phone 2 prefix (3 digits) |
| ACSPH2C | (20,18) | 4 | UNPROT | UNDERLINE | RIGHT | Phone 2 line number (4 digits) |
| (stopper) | (20,23) | 0 | — | — | — | Field stopper |
| (literal) | (20,24) | 16 | — | — | — | TURQUOISE "EFT Account Id: " |
| ACSEFTC | (20,41) | 10 | UNPROT | UNDERLINE | — | EFT account ID (10-digit numeric) |
| (stopper) | (20,52) | 0 | — | — | — | Field stopper |
| (literal) | (20,53) | 24 | — | — | — | TURQUOISE "Primary Card Holder Y/N:" |
| ACSPFLG | (20,78) | 1 | UNPROT | UNDERLINE | — | Primary card holder flag (Y or N) |
| (stopper) | (20,80) | 0 | — | — | — | Field stopper |

### 4.22 Message Fields (Rows 22-24)

| Field Name | POS | Length | ATTRB | COLOR | Description |
|---|---|---|---|---|---|
| INFOMSG | (22,23) | 45 | ASKIP | NEUTRAL, HILIGHT=OFF | Informational message line |
| (stopper) | (22,69) | 0 | — | — | Field stopper |
| (pad) | (1,1) | 9 | — | — | [internal BMS padding field] |
| ERRMSG | (23,1) | 78 | ASKIP,BRT,FSET | RED | Error/return message line |
| FKEYS | (24,1) | 21 | ASKIP,NORM | YELLOW | Static "ENTER=Process F3=Exit" |
| FKEY05 | (24,23) | 7 | ASKIP,DRK | YELLOW | "F5=Save" (initially dark; enabled by COACTUPC when confirmation needed) |
| FKEY12 | (24,31) | 10 | ASKIP,DRK | YELLOW | "F12=Cancel" (initially dark; enabled when changes pending) |

**FKEY05 and FKEY12 notes:**
- Both defined as ASKIP,DRK (dark/invisible) in the BMS source
- COACTUPC paragraph 3390-SETUP-INFOMSG-ATTRS sets DFHBMASB on FKEY05A and FKEY12A when confirmation is required (line 3578-3580) or when changes are made (line 3574-3576) — making them visible to the operator

---

## 5. FSET Usage

Fields with FSET (force-set MDT bit) will always be transmitted back to the host regardless of whether the operator modifies them:
- TRNNAME (row 1) — always sent back
- OPNYEAR (row 6) — open date year
- ACRDLIM (row 6) — credit limit
- ACSHLIM (row 7) — cash credit limit
- ACURBAL (row 8) — current balance
- ACRCYCR (row 9) — current cycle credit
- ACRCYDB (row 10) — current cycle debit
- ERRMSG (row 23) — error message

---

## 6. Field Protection Summary

The BMS source defines most data fields as UNPROT. COACTUPC manages protection dynamically:

| Mode | Account Number | Status/Dates/Limits | Customer Fields | Country |
|---|---|---|---|---|
| Initial (search) | UNPROT (DFHBMFSE) | PROT (DFHBMPRF) | PROT | PROT |
| Show/Edit | PROT (DFHBMPRF) | UNPROT (DFHBMFSE) | UNPROT (except Cust ID) | PROT |
| Confirm/Done | PROT | PROT | PROT | PROT |

---

## 7. BMS-Generated COBOL Structures

The assembly of COACTUP produces two COBOL data structures usable in COACTUPC:

**Input structure (CACTUPAI):** Every named field generates three sub-fields:
- `{name}L OF CACTUPAI` — PIC S9(4) COMP-3 (field length, or -1 to position cursor)
- `{name}A OF CACTUPAI` — PIC X(1) (attribute byte; DFHBMPRF=protected, DFHBMFSE=unprotected, DFHBMDAR=dark)
- `{name}I OF CACTUPAI` — PIC X(n) (input data from terminal)

**Output structure (CACTUPAO):** Every named field generates:
- `{name}L OF CACTUPAO` — PIC S9(4) COMP-3 (length override)
- `{name}A OF CACTUPAO` — PIC X(1) (attribute byte output)
- `{name}C OF CACTUPAO` — PIC X(1) (color extension byte; DFHRED, DFHGRN, DFHNEUTR, etc.)
- `{name}H OF CACTUPAO` — PIC X(1) (highlight extension byte)
- `{name}O OF CACTUPAO` — PIC X(n) (output data to terminal)

---

## 8. Dynamic Attribute Control

COACTUPC exercises extensive dynamic attribute control. Key patterns observed:

| Pattern | Effect | Code |
|---|---|---|
| MOVE DFHBMPRF TO {field}A OF CACTUPAI | Protects field (no input) | 3310-PROTECT-ALL-ATTRS |
| MOVE DFHBMFSE TO {field}A OF CACTUPAI | Unprotects field (allows input) | 3320-UNPROTECT-FEW-ATTRS |
| MOVE DFHRED TO {field}C OF CACTUPAO | Sets field color to red | CSSETATY expand |
| MOVE -1 TO {field}L OF CACTUPAI | Positions cursor to that field | 3300-SETUP-SCREEN-ATTRS |
| MOVE '*' TO {field}O OF CACTUPAO | Places asterisk to indicate blank required field | CSSETATY expand |
| MOVE DFHBMASB TO {field}A OF CACTUPAI | Sets field to bright/unprotected (makes DRK field visible) | 3390-SETUP-INFOMSG-ATTRS |

---

## 9. Key Navigation

| Key | Program Response | Source |
|---|---|---|
| ENTER | Process current screen input | 0000-MAIN EVALUATE |
| F3 (PF3) | Exit — XCTL to calling program or menu | 0000-MAIN WHEN CCARD-AID-PFK03 |
| F5 (PF5) | Confirm and save (only when ACUP-CHANGES-OK-NOT-CONFIRMED) | 0000-MAIN / 2000-DECIDE-ACTION |
| F12 (PF12) | Cancel changes — re-read and show original data (only when data shown) | 0000-MAIN / 2000-DECIDE-ACTION |
| Other keys | Treated as ENTER | 0000-MAIN PFK-INVALID handling |

---

## 10. Design Notes and Observations

1. **Split date entry:** Dates (open, expiry, reissue, date of birth) are entered in three separate fields (YEAR/MON/DAY) rather than a single formatted date field. This differs from the viewer screen (COACTVW) which uses single 10-char date fields. Each component is right-justified.

2. **Split phone entry:** Phone numbers are entered in three separate fields (area/prefix/line) rather than formatted composite. COACTUPC reassembles them as `(NNN)NNN-NNNN` for storage.

3. **Split SSN entry:** SSN uses three fields (ACTSSN1/2/3) with initial placeholder values, allowing separate validation of each component.

4. **Currency input:** Credit limit, cash credit limit, current balance, and cycle amounts use a single 15-character free-form field. COACTUPC uses FUNCTION NUMVAL-C to parse the value and FUNCTION TEST-NUMVAL-C to validate it, supporting both plain numbers and formatted currency strings.

5. **FKEY05 and FKEY12 are invisible by default:** They are defined DRK in the BMS and activated programmatically, providing a progressive disclosure UX where the save/cancel options only appear when relevant.

6. **Customer ID field:** ACSTNUM is defined UNPROT in BMS but COACTUPC explicitly protects it in 3320-UNPROTECT-FEW-ATTRS (line 3531: `MOVE DFHBMPRF TO ACSTNUMA`) — the customer ID is display-only and not editable.

7. **Country field:** ACSCTRY is protected by COACTUPC in edit mode because, as the comment states (line 3547), "most of the edits are USA specific." Country validation is not implemented.

8. **Version:** BMS file trailer states `CardDemo_v1.0-70-g193b394-123, Date: 2022-08-22 17:02:42 CDT`.
