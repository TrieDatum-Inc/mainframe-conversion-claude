# Technical Specification: COTRN01 BMS Mapset — Transaction View Screen

## 1. Executive Summary

COTRN01 is a BMS mapset definition for the CardDemo Transaction View (detail) screen. It defines a single physical map (COTRN1A) that displays all fields of a single transaction record in read-only format. The operator enters a Transaction ID and the program populates all detail fields. The screen is used exclusively by program COTRN01C (transaction CT01).

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COTRN01.BMS | BMS macro source | app/bms/COTRN01.bms |
| COTRN01.CPY | Generated symbolic description copybook | app/cpy-bms/COTRN01.CPY |
| COTRN01C.CBL | Owning CICS program | app/cbl/COTRN01C.cbl |

---

## 3. Mapset Definition

| Parameter | Value | Meaning |
|---|---|---|
| Mapset name | COTRN01 | CICS resource definition name |
| CTRL | (ALARM,FREEKB) | Sound alarm on send; free keyboard |
| EXTATT | YES | Extended attributes enabled |
| LANG | COBOL | Generated COBOL copybook |
| MODE | INOUT | Both input and output maps generated |
| STORAGE | AUTO | Separate storage per map |
| TIOAPFX | YES | 12-byte TIOA prefix |
| TYPE | &&SYSPARM | Assembly type from SYSPARM |

---

## 4. Map Definition

| Parameter | Value |
|---|---|
| Map name | COTRN1A |
| COLUMN | 1 |
| LINE | 1 |
| SIZE | (24, 80) |

---

## 5. Screen Layout

```
Col:  1         10        20        30        40        50        60        70        80
      |---------|---------|---------|---------|---------|---------|---------|---------|
R01:  Tran: TTTT         [      TITLE01 (40)       ]         Date: mm/dd/yy
R02:  Prog: PPPPPPPP     [      TITLE02 (40)       ]         Time: hh:mm:ss
R03:  (blank)
R04:                               View Transaction
R05:  (blank)
R06:       Enter Tran ID: [TRNIDINI________________]
R07:  (blank)
R08:       -----------------------------------------------------------------------
R09:  (blank)
R10:       Transaction ID: [TRNIDI__________]        Card Number: [CARDNUMI______]
R11:  (blank)
R12:       Type CD: [TT]   Category CD: [CCCC]   Source: [SSSSSSSSSS]
R13:  (blank)
R14:       Description: [TDESCI________________________________________________]
R15:  (blank)
R16:       Amount: [TRNAMTI__]   Orig Date: [TORIGDTI_]   Proc Date: [TPROCDTI_]
R17:  (blank)
R18:       Merchant ID: [MIDI____]   Merchant Name: [MNAMEI_____________________]
R19:  (blank)
R20:       Merchant City: [MCITYI___________________]   Merchant Zip: [MZIPI___]
R21:  (blank)
R22:  (blank)
R23:  [ERRMSG__________________________________________________________________]
R24:  ENTER=Fetch  F3=Back  F4=Clear  F5=Browse Tran.
```

---

## 6. Field Definitions

### Header Fields (Row 1)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Tran:') | (1,1) | 5 | ASKIP,NORM | BLUE | Label |
| TRNNAME | (1,7) | 4 | ASKIP,FSET,NORM | BLUE | Transaction ID ('CT01') |
| TITLE01 | (1,21) | 40 | ASKIP,FSET,NORM | YELLOW | App title line 1 |
| (literal 'Date:') | (1,65) | 5 | ASKIP,NORM | BLUE | Label |
| CURDATE | (1,71) | 8 | ASKIP,FSET,NORM | BLUE | Current date MM/DD/YY, initial='mm/dd/yy' |

### Header Fields (Row 2)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Prog:') | (2,1) | 5 | ASKIP,NORM | BLUE | Label |
| PGMNAME | (2,7) | 8 | ASKIP,FSET,NORM | BLUE | Program name ('COTRN01C') |
| TITLE02 | (2,21) | 40 | ASKIP,FSET,NORM | YELLOW | App title line 2 |
| (literal 'Time:') | (2,65) | 5 | ASKIP,NORM | BLUE | Label |
| CURTIME | (2,71) | 8 | ASKIP,FSET,NORM | BLUE | Current time HH:MM:SS, initial='hh:mm:ss' |

### Screen Title (Row 4)

| Literal | POS | Length | ATTRB | Color |
|---|---|---|---|---|
| 'View Transaction' | (4,30) | 16 | ASKIP,BRT | NEUTRAL |

### Transaction ID Entry (Row 6)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Highlight | IC | Description |
|---|---|---|---|---|---|---|---|
| (literal 'Enter Tran ID:') | (6,6) | 14 | ASKIP,NORM | TURQUOISE | — | — | Label |
| TRNIDIN | (6,21) | 16 | FSET,IC,NORM,UNPROT | GREEN | UNDERLINE | YES | Transaction ID entry; initial=' ' |
| (stopper) | (6,38) | 0 | ASKIP,NORM | — | — | — | Field terminator |

Note: TRNIDIN has IC (Initial Cursor) — the cursor is initially positioned here on map display.

### Separator Line (Row 8)

| Literal | POS | Length | ATTRB | Color |
|---|---|---|---|---|
| (70 dashes) | (8,6) | 70 | ASKIP,NORM | NEUTRAL |

### Transaction ID and Card Number (Row 10)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Transaction ID:') | (10,6) | 15 | ASKIP,NORM | TURQUOISE | Label |
| TRNID | (10,22) | 16 | ASKIP,NORM | BLUE | Transaction ID display; initial=' ' |
| (stopper) | (10,39) | 0 | ASKIP,NORM | — | Field terminator |
| (literal 'Card Number:') | (10,45) | 12 | ASKIP,NORM | TURQUOISE | Label |
| CARDNUM | (10,58) | 16 | ASKIP,NORM | BLUE | Card number display; initial=' ' |
| (stopper) | (10,75) | 0 | ASKIP,NORM | GREEN | Field terminator |

### Type Code, Category, Source (Row 12)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Type CD:') | (12,6) | 8 | ASKIP,NORM | TURQUOISE | Label |
| TTYPCD | (12,15) | 2 | ASKIP,NORM | BLUE | Type code display; initial=' ' |
| (stopper) | (12,18) | 0 | — | — | Field terminator |
| (literal 'Category CD:') | (12,23) | 12 | ASKIP,NORM | TURQUOISE | Label |
| TCATCD | (12,36) | 4 | ASKIP,NORM | BLUE | Category code display; initial=' ' |
| (stopper) | (12,41) | 0 | — | — | Field terminator |
| (literal 'Source:') | (12,46) | 7 | ASKIP,NORM | TURQUOISE | Label |
| TRNSRC | (12,54) | 10 | ASKIP,NORM | BLUE | Source display; initial=' ' |
| (stopper) | (12,65) | 0 | — | — | Field terminator |

### Description (Row 14)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Description:') | (14,6) | 12 | ASKIP,NORM | TURQUOISE | Label |
| TDESC | (14,19) | 60 | ASKIP,NORM | BLUE | Full description display; initial=' ' |
| (stopper) | (14,80) | 0 | — | — | Field terminator |

### Amount and Dates (Row 16)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Amount:') | (16,6) | 7 | ASKIP,NORM | TURQUOISE | Label |
| TRNAMT | (16,14) | 12 | ASKIP,NORM | BLUE | Formatted amount; initial=' ' |
| (stopper) | (16,27) | 0 | — | — | Field terminator |
| (literal 'Orig Date:') | (16,31) | 10 | ASKIP,NORM | TURQUOISE | Label |
| TORIGDT | (16,42) | 10 | ASKIP,NORM | BLUE | Origination timestamp; initial=' ' |
| (stopper) | (16,53) | 0 | — | — | Field terminator |
| (literal 'Proc Date:') | (16,57) | 10 | ASKIP,NORM | TURQUOISE | Label |
| TPROCDT | (16,68) | 10 | ASKIP,NORM | BLUE | Processing timestamp; initial=' ' |
| (stopper) | (16,79) | 0 | — | — | Field terminator |

### Merchant Information (Rows 18 and 20)

**Row 18 — Merchant ID and Name:**

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Merchant ID:') | (18,6) | 12 | ASKIP,NORM | TURQUOISE | Label |
| MID | (18,19) | 9 | ASKIP,NORM | BLUE | Merchant ID display; initial=' ' |
| (stopper) | (18,29) | 0 | — | — | Field terminator |
| (literal 'Merchant Name:') | (18,33) | 14 | ASKIP,NORM | TURQUOISE | Label |
| MNAME | (18,48) | 30 | ASKIP,NORM | BLUE | Merchant name; initial=' ' |
| (stopper) | (18,79) | 0 | — | — | Field terminator |

**Row 20 — Merchant City and ZIP:**

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Merchant City:') | (20,6) | 14 | ASKIP,NORM | TURQUOISE | Label |
| MCITY | (20,21) | 25 | ASKIP,NORM | BLUE | Merchant city; initial=' ' |
| (stopper) | (20,47) | 0 | — | — | Field terminator |
| (literal 'Merchant Zip:') | (20,53) | 13 | ASKIP,NORM | TURQUOISE | Label |
| MZIP | (20,67) | 10 | ASKIP,NORM | BLUE | Merchant ZIP; initial=' ' |
| (stopper) | (20,78) | 0 | — | — | Field terminator |

### Error/Message Line (Row 23)

| Field Name | POS | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| ERRMSG | (23,1) | 78 | ASKIP,BRT,FSET | RED | Error or status message |

### Function Key Legend (Row 24)

| Literal | POS | Length | ATTRB | Color |
|---|---|---|---|---|
| 'ENTER=Fetch  F3=Back  F4=Clear  F5=Browse Tran.' | (24,1) | 47 | ASKIP,NORM | YELLOW |

---

## 7. Input Fields Summary

| Field | Row,Col | Len | Attributes | IC | Description |
|---|---|---|---|---|---|
| TRNIDIN | 6,21 | 16 | FSET,NORM,UNPROT,UNDERLINE | YES | Transaction ID to fetch |

Only one user-enterable field exists on this screen. All transaction detail fields are ASKIP (protected display only).

---

## 8. Output-Only Fields Summary

| Field | Row,Col | Len | Contents |
|---|---|---|---|
| TRNNAME | 1,7 | 4 | 'CT01' |
| TITLE01 | 1,21 | 40 | 'AWS Mainframe Modernization' |
| CURDATE | 1,71 | 8 | MM/DD/YY |
| PGMNAME | 2,7 | 8 | 'COTRN01C' |
| TITLE02 | 2,21 | 40 | 'CardDemo' |
| CURTIME | 2,71 | 8 | HH:MM:SS |
| TRNID | 10,22 | 16 | Transaction ID from file |
| CARDNUM | 10,58 | 16 | Card number |
| TTYPCD | 12,15 | 2 | Type code |
| TCATCD | 12,36 | 4 | Category code |
| TRNSRC | 12,54 | 10 | Source |
| TDESC | 14,19 | 60 | Description |
| TRNAMT | 16,14 | 12 | Formatted amount |
| TORIGDT | 16,42 | 10 | Original date/timestamp |
| TPROCDT | 16,68 | 10 | Processing date/timestamp |
| MID | 18,19 | 9 | Merchant ID |
| MNAME | 18,48 | 30 | Merchant name |
| MCITY | 20,21 | 25 | Merchant city |
| MZIP | 20,67 | 10 | Merchant ZIP |
| ERRMSG | 23,1 | 78 | Error/status message |

---

## 9. Symbolic Map Fields in COTRN01.CPY

The generated copybook (app/cpy-bms/COTRN01.CPY) creates:

**Input map COTRN1AI** with fields:
- Header: TRNNAMEL/F/I, TITLE01L/F/I, CURDATEL/F/I, PGMNAMEL/F/I, TITLE02L/F/I, CURTIMEL/F/I
- Entry: TRNIDINL/F/I (X(16)) — editable input
- Display: TRNIDL/F/I (X(16)), CARDNUML/F/I (X(16))
- Type/Cat/Src: TTYPCDL/F/I (X(2)), TCATCDL/F/I (X(4)), TRNSRCL/F/I (X(10))
- Desc: TDESCL/F/I (X(60))
- Financial: TRNAMTL/F/I (X(12)), TORIGDTL/F/I (X(10)), TPROCDTL/F/I (X(10))
- Merchant: MIDL/F/I (X(9)), MNAMEL/F/I (X(30)), MCITYL/F/I (X(25)), MZIPL/F/I (X(10))
- Message: ERRMSGL/F/I (X(78))

**Output map COTRN1AO** REDEFINES COTRN1AI with corresponding `O` suffix fields and `C/P/H/V` color/attribute bytes.

---

## 10. Differences from COTRN02 (Add) Screen

| Aspect | COTRN01 (View) | COTRN02 (Add) |
|---|---|---|
| Entry key field | TRNIDIN — Transaction ID | ACTIDIN / CARDNIN — Account/Card |
| Data fields | All ASKIP (protected) | All UNPROT (editable) |
| Confirmation | None | CONFIRM Y/N field |
| Amount format hint | Not shown | '(-99999999.99)' shown as label |
| Date format hint | Not shown | '(YYYY-MM-DD)' shown as label |
| Amount/date fields | Display (truncated display of TRAN-ORIG-TS and TRAN-PROC-TS) | Full 10-char YYYY-MM-DD input |
| F5 key | 'Browse Tran.' → XCTL to COTRN00C | 'Copy Last Tran.' → copies last record |

---

## 11. Program Usage

COTRN01C uses this mapset as follows:

| Operation | CICS Command |
|---|---|
| Display detail | `EXEC CICS SEND MAP('COTRN1A') MAPSET('COTRN01') FROM(COTRN1AO) ERASE CURSOR` |
| Read operator input | `EXEC CICS RECEIVE MAP('COTRN1A') MAPSET('COTRN01') INTO(COTRN1AI)` |

---

## 12. Screen Navigation

```
Function Key  Action
-----------   ------
ENTER         Fetch transaction by TRNIDIN (or re-display on error)
F3            Return to calling program (COTRN00C) or COMEN01C
F4            Clear all fields
F5            Transfer to COTRN00C (Browse Transaction list)
```

---

## 13. Version and Change History

Source version stamp: `CardDemo_v1.0-70-g193b394-123  Date: 2022-08-22 17:02:43 CDT`
