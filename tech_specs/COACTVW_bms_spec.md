# Technical Specification: COACTVW.BMS (Account Viewer Screen)

## 1. Overview

| Property | Value | Source |
|---|---|---|
| BMS Source File | `app/bms/COACTVW.bms` |  |
| Mapset Name | COACTVW | Line 20 |
| Map Name | CACTVWA | Line 25 |
| Screen Title | "View Account" | Line 78 |
| Screen Size | 24 rows x 80 columns | Line 28 |
| MODE | INOUT | Line 21 |
| LANG | COBOL | Line 20 |
| STORAGE | AUTO | Line 22 |
| TIOAPFX | YES | Line 23 |
| TYPE | &&SYSPARM | Line 24 |

Like COACTUP, this mapset is assembled twice with &&SYSPARM for the physical map (TYPE=MAP) and the COBOL copybook (TYPE=DSECT).

Map CTRL attribute: FREEKB — keyboard automatically unlocked after SEND.

Extended attribute support via DSATTS and MAPATTS: COLOR, HILIGHT, PS, VALIDN.

---

## 2. Functional Purpose

COACTVW/CACTVWA is the read-only account display screen used exclusively by COACTVWC (transaction CAVW). It shows all account and customer information for a given account number. The design intent is:
1. The account number field (ACCTSID) is the only input field — operator enters the account number they want to view.
2. All other data fields are output-only (protected via ASKIP attribute or programmatic PROT in COACTVWC).
3. The screen is single-purpose: display account data. No edit, save, or confirmation workflow.

---

## 3. Screen Layout

```
Col:  1         10        20        30        40        50        60        70        80
Row 1: Tran:XXXX          [TITLE01 - 40 chars          ]     Date:MM/DD/YY
Row 2: Prog:XXXXXXXX      [TITLE02 - 40 chars          ]     Time:HH:MM:SS
Row 3: (blank)
Row 4:                             View Account
Row 5:          Account Number :[ACCTSID 11           ]  Active Y/N: [A]
Row 6: Opened:[ADTOPEN  10      ]   Credit Limit        :[  ACRDLIM 15   ]
Row 7: Expiry:[AEXPDT   10      ]   Cash credit Limit   :[  ACSHLIM 15   ]
Row 8: Reissue:[AREISDT 10      ]   Current Balance     :[  ACURBAL 15   ]
Row 9:                              Current Cycle Credit:[  ACRCYCR 15   ]
Row10: Account Group:[AADDGRP 10]   Current Cycle Debit :[  ACRCYDB 15   ]
Row11:                                  Customer Details
Row12: Customer id  :[ACSTNUM 9]    SSN:[ACSTSSN 12       ]
Row13: Date of birth:[ACSTDOB 10]   FICO Score:[FCO 3]
Row14: First Name              Middle Name:           Last Name :
Row15: [ACSFNAM 25          ][ACSMNAM 25           ][ACSLNAM 25        ]
Row16: Address:[ACSADL1 50               ]  State [ST]
Row17:         [ACSADL2 50               ]  Zip[ZIPPP]
Row18: City   [ACSCITY 50               ]  Country[CTY]
Row19: Phone 1:[ACSPHN1 13    ]   Government Issued Id Ref    : [ACSGOVT  20  ]
Row20: Phone 2:[ACSPHN2 13    ]   EFT Account Id: [ACSEFTC 10]  Primary Card Holder Y/N:[F]
Row21: (blank)
Row22:                        [INFOMSG 45              ]
Row23: [ERRMSG 78                                                            ]
Row24:   F3=Exit
```

---

## 4. Field Inventory

### 4.1 Header Fields (Rows 1-2)

| Field Name | POS | Length | ATTRB | COLOR | Description |
|---|---|---|---|---|---|
| (literal) | (1,1) | 5 | ASKIP,NORM | BLUE | Static "Tran:" |
| TRNNAME | (1,7) | 4 | ASKIP,FSET,NORM | BLUE | Current transaction ID |
| TITLE01 | (1,21) | 40 | ASKIP,NORM | YELLOW | Application title line 1 |
| (literal) | (1,65) | 5 | ASKIP,NORM | BLUE | Static "Date:" |
| CURDATE | (1,71) | 8 | ASKIP,NORM | BLUE | Current date MM/DD/YY, init='mm/dd/yy' |
| (literal) | (2,1) | 5 | ASKIP,NORM | BLUE | Static "Prog:" |
| PGMNAME | (2,7) | 8 | ASKIP,NORM | BLUE | Current program name |
| TITLE02 | (2,21) | 40 | ASKIP,NORM | YELLOW | Application title line 2 |
| (literal) | (2,65) | 5 | ASKIP,NORM | BLUE | Static "Time:" |
| CURTIME | (2,71) | 8 | ASKIP,NORM | BLUE | Current time HH:MM:SS, init='hh:mm:ss' |

### 4.2 Screen Title (Row 4)

| POS | Length | COLOR | Content |
|---|---|---|---|
| (4,33) | 12 | NEUTRAL | "View Account" |

### 4.3 Account Number Input Field (Row 5)

| Field Name | POS | Length | ATTRB | COLOR | HILIGHT | PICIN | VALIDN | Description |
|---|---|---|---|---|---|---|---|---|
| (literal) | (5,19) | 16 | ASKIP,NORM | TURQUOISE | — | — | — | "Account Number :" |
| ACCTSID | (5,38) | 11 | FSET,IC,NORM,UNPROT | GREEN | UNDERLINE | '99999999999' | MUSTFILL | Account number input |
| (stopper) | (5,50) | 0 | — | — | — | — | — | Field stopper |

**ACCTSID detailed attributes:**
- **FSET:** Forces MDT bit — field content always transmitted on SEND/RECEIVE
- **IC (Insert Cursor):** Cursor positioned here when screen is displayed
- **NORM:** Normal intensity
- **UNPROT:** Operator can type in the field
- **COLOR=GREEN:** Distinct from the BLUE header fields and TURQUOISE labels
- **HILIGHT=UNDERLINE:** Underline visible on 3270 color terminals
- **PICIN='99999999999':** Enforces numeric-only input at the terminal hardware level (11 nines)
- **VALIDN=MUSTFILL:** Terminal-level validation requires all 11 positions to be filled before transmission

**MUSTFILL vs. COACTUPC ACCTSID:** The viewer screen uses MUSTFILL validation on ACCTSID, meaning the terminal will refuse to transmit the screen if the account number field is not completely filled. COACTUP.bms does NOT specify VALIDN=MUSTFILL or PICIN on its ACCTSID — all validation is done by COACTUPC in software.

### 4.4 Account Status Display (Row 5)

| Field Name | POS | Length | ATTRB | HILIGHT | Description |
|---|---|---|---|---|---|
| (literal) | (5,57) | 12 | — | — | TURQUOISE "Active Y/N: " |
| ACSTTUS | (5,70) | 1 | ASKIP | UNDERLINE | Account active status (Y/N), output only |
| (stopper) | (5,72) | 0 | — | — | Field stopper |

**Note:** ACSTTUS uses ASKIP (auto-skip / protected) in COACTVW, making it a pure output field — no operator input accepted. This contrasts with COACTUP.bms where ACSTTUS is UNPROT.

### 4.5 Account Dates (Rows 6-8, left side)

Unlike COACTUP which splits dates into year/month/day components, COACTVW uses single 10-character date fields:

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| (literal) | (6,8) | 7 | — | TURQUOISE "Opened:" |
| ADTOPEN | (6,17) | 10 | UNDERLINE | Account open date (YYYY-MM-DD full string) |
| (stopper) | (6,28) | 0 | — | Field stopper |
| (literal) | (7,8) | 7 | — | TURQUOISE "Expiry:" |
| AEXPDT | (7,17) | 10 | UNDERLINE | Account expiry date (YYYY-MM-DD) |
| (stopper) | (7,28) | 0 | — | Field stopper |
| (literal) | (8,8) | 8 | — | TURQUOISE "Reissue:" |
| AREISDT | (8,17) | 10 | UNDERLINE | Account reissue date (YYYY-MM-DD) |
| (stopper) | (8,28) | 0 | — | Field stopper |

**Note:** ADTOPEN, AEXPDT, AREISDT have no explicit ATTRB — they inherit default (ASKIP, output-only). COACTVWC moves the full date string directly from ACCOUNT-RECORD fields.

### 4.6 Financial Data Fields (Rows 6-10, right side)

All financial fields use PICOUT='+ZZZ,ZZZ,ZZZ.99' and JUSTIFY=(RIGHT) for formatted numeric display. They have no explicit ATTRB, making them output-protected by default.

| Field Name | POS | Length | HILIGHT | PICOUT | JUSTIFY | Description |
|---|---|---|---|---|---|---|
| (literal) | (6,39) | 21 | — | — | — | TURQUOISE "Credit Limit        :" |
| ACRDLIM | (6,61) | 15 | UNDERLINE | +ZZZ,ZZZ,ZZZ.99 | RIGHT | Credit limit |
| (stopper) | (6,77) | 0 | — | — | — | Field stopper |
| (literal) | (7,39) | 21 | — | — | — | TURQUOISE "Cash credit Limit   :" |
| ACSHLIM | (7,61) | 15 | UNDERLINE | +ZZZ,ZZZ,ZZZ.99 | RIGHT | Cash credit limit |
| (stopper) | (7,77) | 0 | — | — | Field stopper |
| (literal) | (8,39) | 21 | — | — | — | TURQUOISE "Current Balance     :" |
| ACURBAL | (8,61) | 15 | UNDERLINE | +ZZZ,ZZZ,ZZZ.99 | RIGHT | Current balance |
| (stopper) | (8,77) | 0 | — | — | Field stopper |
| (literal) | (9,39) | 21 | — | — | — | TURQUOISE "Current Cycle Credit:" |
| ACRCYCR | (9,61) | 15 | UNDERLINE | +ZZZ,ZZZ,ZZZ.99 | RIGHT | Current cycle credit |
| (stopper) | (9,77) | 0 | — | — | Field stopper |
| (literal) | (10,39) | 21 | — | — | — | TURQUOISE "Current Cycle Debit :" |
| ACRCYDB | (10,61) | 15 | UNDERLINE | +ZZZ,ZZZ,ZZZ.99 | RIGHT | Current cycle debit |
| (stopper) | (10,77) | 0 | — | — | Field stopper |

**PICOUT='+ZZZ,ZZZ,ZZZ.99' formatting:** The BMS PICOUT clause is applied at the 3270 data stream level. When COACTVWC moves a signed packed numeric (S9(10)V99) to these fields in the output map, the BMS formatter applies the picture to produce a formatted string like `+123,456,789.00` or `-999.99`. This formatting is handled entirely by the BMS runtime — COACTVWC does not need to format these values in COBOL, unlike COACTUPC which must manually format them using WS-EDIT-CURRENCY-9-2-F.

### 4.7 Account Group (Row 10, left side)

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| (literal) | (10,8) | 14 | — | TURQUOISE "Account Group:" |
| AADDGRP | (10,23) | 10 | UNDERLINE | Account group ID (output) |
| (stopper) | (10,34) | 0 | — | Field stopper |

### 4.8 Customer Details Section Header (Row 11)

| POS | Length | COLOR | Content |
|---|---|---|---|
| (11,32) | 16 | NEUTRAL | "Customer Details" |

### 4.9 Customer ID and SSN (Row 12)

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| (literal) | (12,8) | 14 | — | TURQUOISE "Customer id  :" |
| ACSTNUM | (12,23) | 9 | UNDERLINE | Customer ID (output) |
| (stopper) | (12,33) | 0 | — | Field stopper |
| (literal) | (12,49) | 4 | — | TURQUOISE "SSN:" |
| ACSTSSN | (12,54) | 12 | UNDERLINE | SSN formatted as NNN-NN-NNNN (single field, 12 chars) |
| (stopper) | (12,67) | 0 | — | Field stopper |

**ACSTSSN vs. ACTSSN1/2/3 in COACTUP:** COACTVW uses a single 12-character field for the formatted SSN (e.g., "123-45-6789"), while COACTUP splits it into three separate input fields. COACTVWC formats the SSN using a STRING statement before moving it to ACSTSSNO.

### 4.10 Date of Birth and FICO (Row 13)

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| (literal) | (13,8) | 14 | — | TURQUOISE "Date of birth:" |
| ACSTDOB | (13,23) | 10 | UNDERLINE | Date of birth YYYY-MM-DD (single 10-char field) |
| (stopper) | (13,34) | 0 | — | Field stopper |
| (literal) | (13,49) | 11 | — | TURQUOISE "FICO Score:" |
| ACSTFCO | (13,61) | 3 | UNDERLINE | FICO credit score (3 digits) |
| (stopper) | (13,65) | 0 | — | Field stopper |

### 4.11 Name Column Headers (Row 14)

| POS | Length | COLOR | Content |
|---|---|---|---|
| (14,1) | 10 | TURQUOISE | "First Name" |
| (14,28) | 13 | TURQUOISE | "Middle Name: " |
| (14,55) | 12 | TURQUOISE | "Last Name : " |

### 4.12 Name Display Fields (Row 15)

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| ACSFNAM | (15,1) | 25 | UNDERLINE | Customer first name (output) |
| (stopper) | (15,27) | 0 | — | Field stopper |
| ACSMNAM | (15,28) | 25 | UNDERLINE | Customer middle name (output) |
| (stopper) | (15,54) | 0 | — | Field stopper |
| ACSLNAM | (15,55) | 25 | UNDERLINE | Customer last name (output) |

### 4.13 Address Line 1 and State (Row 16)

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| (literal) | (16,1) | 8 | — | TURQUOISE "Address:" |
| ACSADL1 | (16,10) | 50 | UNDERLINE | Address line 1 (output) |
| (stopper) | (16,61) | 0 | — | Field stopper |
| (literal) | (16,63) | 6 | — | TURQUOISE "State " |
| ACSSTTE | (16,73) | 2 | UNDERLINE | State code (output) |
| (stopper) | (16,76) | 0 | — | Field stopper |

### 4.14 Address Line 2 and Zip Code (Row 17)

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| ACSADL2 | (17,10) | 50 | UNDERLINE | Address line 2 (output) |
| (stopper) | (17,61) | 0 | — | Field stopper |
| (literal) | (17,63) | 3 | — | TURQUOISE "Zip" |
| ACSZIPC | (17,73) | 5 | UNDERLINE | Zip code, JUSTIFY=(RIGHT) |
| (stopper) | (17,79) | 0 | — | Field stopper |

### 4.15 City and Country (Row 18)

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| (literal) | (18,1) | 5 | — | TURQUOISE "City " |
| ACSCITY | (18,10) | 50 | UNDERLINE | City (CUST-ADDR-LINE-3) |
| (stopper) | (18,61) | 0 | — | Field stopper |
| (literal) | (18,63) | 7 | — | TURQUOISE "Country" |
| ACSCTRY | (18,73) | 3 | UNDERLINE | Country code (output) |
| (stopper) | (18,77) | 0 | — | Field stopper |

### 4.16 Phone 1 and Government ID (Row 19)

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| (literal) | (19,1) | 8 | — | TURQUOISE "Phone 1:" |
| ACSPHN1 | (19,10) | 13 | UNDERLINE | Phone 1 full formatted string e.g. (NNN)NNN-NNNN |
| (literal) | (19,24) | 30 | — | TURQUOISE "Government Issued Id Ref    : " |
| ACSGOVT | (19,58) | 20 | UNDERLINE | Government-issued ID reference |
| (stopper) | (19,79) | 0 | — | Field stopper |

**ACSPHN1 vs. ACSPH1A/B/C in COACTUP:** COACTVW uses a single 13-character phone field to display the complete stored string `(NNN)NNN-NNNN`. COACTVWC moves CUST-PHONE-NUM-1 directly to ACSPHN1O. The stored format in CUSTDAT is `(NNN)NNN-NNNN` (13 chars with delimiters), matching this field's length exactly.

### 4.17 Phone 2, EFT Account ID, Primary Card Holder (Row 20)

| Field Name | POS | Length | HILIGHT | Description |
|---|---|---|---|---|
| (literal) | (20,1) | 8 | — | TURQUOISE "Phone 2:" |
| ACSPHN2 | (20,10) | 13 | UNDERLINE | Phone 2 full formatted string |
| (literal) | (20,24) | 16 | — | TURQUOISE "EFT Account Id: " |
| ACSEFTC | (20,41) | 10 | UNDERLINE | EFT account ID |
| (stopper) | (20,52) | 0 | — | Field stopper |
| (literal) | (20,53) | 24 | — | TURQUOISE "Primary Card Holder Y/N:" |
| ACSPFLG | (20,78) | 1 | UNDERLINE | Primary card holder flag (Y/N) |
| (stopper) | (20,80) | 0 | — | Field stopper |

### 4.18 Message Fields (Rows 22-24)

| Field Name | POS | Length | ATTRB | COLOR | Description |
|---|---|---|---|---|---|
| INFOMSG | (22,23) | 45 | PROT | NEUTRAL, HILIGHT=OFF | Informational message |
| (stopper) | (22,69) | 0 | — | — | Field stopper |
| (pad) | (1,1) | 9 | — | — | Internal BMS padding |
| ERRMSG | (23,1) | 78 | ASKIP,BRT,FSET | RED | Error/return message |
| (literal) | (24,1) | 60 | ASKIP,NORM | TURQUOISE | "  F3=Exit " (static, full 60-char field) |

**Row 24 note:** COACTVW uses a single static literal "  F3=Exit " in TURQUOISE (60 chars) rather than the COACTUPC approach of separate FKEYS/FKEY05/FKEY12 fields with dynamic visibility. Only F3 is supported as an exit in the viewer.

**INFOMSG attribute difference:** In COACTVW the INFOMSG field uses ATTRB=(PROT) rather than ATTRB=(ASKIP) used in COACTUP. Both prevent input, but PROT is a more explicit protection attribute. COACTVWC dynamically changes INFOMSGC to DFHBMDAR (dark) when no message to display, or DFHNEUTR (neutral) when a message exists.

---

## 5. Complete Field Reference Table

| Field | POS | Len | Input? | Output? | Notes |
|---|---|---|---|---|---|
| TRNNAME | (1,7) | 4 | N | Y | Transaction ID |
| TITLE01 | (1,21) | 40 | N | Y | Screen title 1 |
| CURDATE | (1,71) | 8 | N | Y | Current date |
| PGMNAME | (2,7) | 8 | N | Y | Program name |
| TITLE02 | (2,21) | 40 | N | Y | Screen title 2 |
| CURTIME | (2,71) | 8 | N | Y | Current time |
| ACCTSID | (5,38) | 11 | Y | Y | **Account number input** |
| ACSTTUS | (5,70) | 1 | N | Y | Active status Y/N |
| ADTOPEN | (6,17) | 10 | N | Y | Open date YYYY-MM-DD |
| ACRDLIM | (6,61) | 15 | N | Y | Credit limit (formatted) |
| AEXPDT | (7,17) | 10 | N | Y | Expiry date YYYY-MM-DD |
| ACSHLIM | (7,61) | 15 | N | Y | Cash credit limit (formatted) |
| AREISDT | (8,17) | 10 | N | Y | Reissue date YYYY-MM-DD |
| ACURBAL | (8,61) | 15 | N | Y | Current balance (formatted) |
| ACRCYCR | (9,61) | 15 | N | Y | Current cycle credit (formatted) |
| AADDGRP | (10,23) | 10 | N | Y | Account group ID |
| ACRCYDB | (10,61) | 15 | N | Y | Current cycle debit (formatted) |
| ACSTNUM | (12,23) | 9 | N | Y | Customer ID |
| ACSTSSN | (12,54) | 12 | N | Y | SSN as NNN-NN-NNNN |
| ACSTDOB | (13,23) | 10 | N | Y | Date of birth YYYY-MM-DD |
| ACSTFCO | (13,61) | 3 | N | Y | FICO score |
| ACSFNAM | (15,1) | 25 | N | Y | First name |
| ACSMNAM | (15,28) | 25 | N | Y | Middle name |
| ACSLNAM | (15,55) | 25 | N | Y | Last name |
| ACSADL1 | (16,10) | 50 | N | Y | Address line 1 |
| ACSSTTE | (16,73) | 2 | N | Y | State code |
| ACSADL2 | (17,10) | 50 | N | Y | Address line 2 |
| ACSZIPC | (17,73) | 5 | N | Y | Zip code |
| ACSCITY | (18,10) | 50 | N | Y | City |
| ACSCTRY | (18,73) | 3 | N | Y | Country code |
| ACSPHN1 | (19,10) | 13 | N | Y | Phone 1 formatted |
| ACSGOVT | (19,58) | 20 | N | Y | Government ID |
| ACSPHN2 | (20,10) | 13 | N | Y | Phone 2 formatted |
| ACSEFTC | (20,41) | 10 | N | Y | EFT account ID |
| ACSPFLG | (20,78) | 1 | N | Y | Primary card holder Y/N |
| INFOMSG | (22,23) | 45 | N | Y | Info message |
| ERRMSG | (23,1) | 78 | N | Y | Error message (FSET,BRT,RED) |

Total named fields: 37 (1 input, 36 output).

---

## 6. BMS-Generated COBOL Structures

The COACTVW mapset assembly produces CACTVWAI (input) and CACTVWAO (output) structures. Given MODE=INOUT, both are generated.

**Input structure (CACTVWAI):** Each named field generates:
- `{name}L OF CACTVWAI` — PIC S9(4) COMP-3 (length / cursor position)
- `{name}A OF CACTVWAI` — PIC X(1) (attribute byte)
- `{name}I OF CACTVWAI` — PIC X(n) (input data)

In practice, COACTVWC only reads `ACCTSIDI OF CACTVWAI` from the input structure; all other fields are output-only.

**Output structure (CACTVWAO):** Each named field generates:
- `{name}L OF CACTVWAO` — PIC S9(4) COMP-3
- `{name}A OF CACTVWAO` — PIC X(1) (attribute byte)
- `{name}C OF CACTVWAO` — PIC X(1) (color extension)
- `{name}H OF CACTVWAO` — PIC X(1) (highlight extension)
- `{name}O OF CACTVWAO` — PIC X(n) (output data)

---

## 7. ACCTSID Special Attributes — Terminal-Level Validation

The ACCTSID field in COACTVW has attributes not present in COACTUP:

| Attribute | Value | Effect |
|---|---|---|
| PICIN | '99999999999' | The 3270 terminal enforces numeric-only entry (digits 0-9); letters are rejected at the keyboard |
| VALIDN | MUSTFILL | The terminal will not transmit the AID if any of the 11 positions are blank; the operator must fill all 11 digits |
| COLOR | GREEN | Visual differentiation from other fields |
| FSET | — | MDT bit forced — field transmitted even if not modified by operator |

This means COACTVWC's software validation in 2210-EDIT-ACCOUNT (checking for blank/non-numeric/zero) is essentially belt-and-suspenders protection; the terminal hardware already enforces numeric and non-blank requirements before transmission. The zero check and the 11-digit numeric non-zero check in software catch edge cases.

---

## 8. Key Navigation

| Key | Response | Source |
|---|---|---|
| ENTER | Process account number input (look up and display account) | 0000-MAIN WHEN CDEMO-PGM-REENTER |
| F3 (PF3) | Exit — XCTL to calling program or main menu | 0000-MAIN WHEN CCARD-AID-PFK03 |
| Other keys | Treated as ENTER | AID validation fallback |

Only ENTER and PF3 are recognized valid AIDs (COACTVWC lines 307-309). All other keys default to ENTER behavior.

---

## 9. Comparison: COACTVW vs. COACTUP Field Differences

The two mapsets share the same screen real estate (rows 1-24, 80 columns) and identical label layouts. The key structural differences are:

| Aspect | COACTVW (Viewer) | COACTUP (Updater) |
|---|---|---|
| Screen title | "View Account" (row 4) | "Update Account" (row 4) |
| ACCTSID attributes | FSET,IC,NORM,UNPROT,GREEN,PICIN,MUSTFILL | IC,UNPROT (simpler) |
| ACSTTUS | ASKIP (protected, output only) | UNPROT (editable) |
| Open date | ADTOPEN (single 10-char) | OPNYEAR + OPNMON + OPNDAY (three fields) |
| Expiry date | AEXPDT (single 10-char) | EXPYEAR + EXPMON + EXPDAY (three fields) |
| Reissue date | AREISDT (single 10-char) | RISYEAR + RISMON + RISDAY (three fields) |
| Date of birth | ACSTDOB (single 10-char) | DOBYEAR + DOBMON + DOBDAY (three fields) |
| Financial values | PICOUT=+ZZZ,ZZZ,ZZZ.99 (BMS formatting) | Free text 15-char (COBOL formatting) |
| SSN | ACSTSSN (single 12-char formatted) | ACTSSN1 + ACTSSN2 + ACTSSN3 (three fields) |
| Phone 1 | ACSPHN1 (single 13-char) | ACSPH1A + ACSPH1B + ACSPH1C (three fields) |
| Phone 2 | ACSPHN2 (single 13-char) | ACSPH2A + ACSPH2B + ACSPH2C (three fields) |
| Function key row | Single "  F3=Exit " literal | FKEYS + FKEY05(DRK) + FKEY12(DRK) |
| INFOMSG attribute | PROT | ASKIP |
| Data fields default | No ATTRB (output protected) | UNPROT (dynamically managed) |

---

## 10. Design Notes

1. **Read-only design intent:** With the exception of ACCTSID, all data fields have no ATTRB or have ASKIP. The operator cannot tab to or modify any displayed data. This is appropriate for a view-only function.

2. **BMS-level PICOUT formatting:** The COACTVW screen leverages BMS PICOUT for currency display, offloading the formatting burden from the COBOL program. COACTVWC simply moves the packed decimal value from the account record into the output map field; the BMS runtime applies the format mask. COACTUPC must do this formatting in COBOL because the same fields are used for both input (text entry) and output (formatted display).

3. **Single date fields:** All dates are displayed as the raw stored string (YYYY-MM-DD, 10 chars). COACTVWC moves the ACCOUNT-RECORD and CUSTOMER-RECORD date fields directly without parsing. This is simpler but means the display format is dictated by the storage format.

4. **MUSTFILL on ACCTSID:** This design choice prevents the operator from pressing ENTER with a partial or empty account number — the terminal rejects the transmission. While COACTVWC still validates in software for defense-in-depth, in practice the terminal hardware will enforce this constraint first.

5. **No confirmation flow:** The viewer has no multi-step workflow. One ENTER fetches and displays data. F3 exits. There is no F5 save or F12 cancel because there is nothing to save or cancel.

6. **Version:** BMS file trailer states `CardDemo_v1.0-70-g193b394-123, Date: 2022-08-22 17:02:42 CDT` — same version as COACTUP.BMS.
