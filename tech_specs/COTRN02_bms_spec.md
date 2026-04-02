# Technical Specification: COTRN02 BMS Mapset — Transaction Add Screen

## 1. Executive Summary

COTRN02 is a BMS mapset definition for the CardDemo Transaction Add screen. It defines a single physical map (COTRN2A) that presents a fully editable form for adding a new transaction record. The operator supplies account or card number to identify the cardholder, then fills all transaction fields. A confirmation field (Y/N) prevents accidental submission. The screen is used exclusively by program COTRN02C (transaction CT02).

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COTRN02.BMS | BMS macro source | app/bms/COTRN02.bms |
| COTRN02.CPY | Generated symbolic description copybook | app/cpy-bms/COTRN02.CPY |
| COTRN02C.CBL | Owning CICS program | app/cbl/COTRN02C.cbl |

---

## 3. Mapset Definition

| Parameter | Value | Meaning |
|---|---|---|
| Mapset name | COTRN02 | CICS resource definition name |
| CTRL | (ALARM,FREEKB) | Sound alarm on send; free keyboard |
| EXTATT | YES | Extended attributes (color, highlight) enabled |
| LANG | COBOL | Generated COBOL copybook |
| MODE | INOUT | Both input and output maps generated |
| STORAGE | AUTO | Separate storage per map |
| TIOAPFX | YES | 12-byte TIOA prefix |
| TYPE | &&SYSPARM | Assembly type from SYSPARM |

---

## 4. Map Definition

| Parameter | Value |
|---|---|
| Map name | COTRN2A |
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
R04:                               Add Transaction
R05:  (blank)
R06:       Enter Acct #: [ACTIDIN____] (or)  Card #: [CARDNIN_____________]
R07:  (blank)
R08:       -----------------------------------------------------------------------
R09:  (blank)
R10:       Type CD: [TT]   Category CD: [CCCC]   Source: [SSSSSSSSSS]
R11:  (blank)
R12:       Description: [TDESCI______________________________________________ (60)]
R13:  (blank)
R14:       Amount: [TRNAMTI__]   Orig Date: [TORIGDTI_]   Proc Date: [TPROCDTI_]
R15:              (-99999999.99)            (YYYY-MM-DD)              (YYYY-MM-DD)
R16:       Merchant ID: [MIDI_____]   Merchant Name: [MNAMEI___________________]
R17:  (blank)
R18:       Merchant City: [MCITYI___________________]   Merchant Zip: [MZIPI___]
R19:  (blank)
R20:  (blank)
R21:       You are about to add this transaction. Please confirm : [C] (Y/N)
R22:  (blank)
R23:  [ERRMSG__________________________________________________________________]
R24:  ENTER=Continue  F3=Back  F4=Clear  F5=Copy Last Tran.
```

---

## 6. Field Definitions

### Header Fields (Row 1)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Tran:') | (1,1) | 5 | ASKIP,NORM | BLUE | Label |
| TRNNAME | (1,7) | 4 | ASKIP,FSET,NORM | BLUE | Transaction ID ('CT02') |
| TITLE01 | (1,21) | 40 | ASKIP,FSET,NORM | YELLOW | App title line 1 |
| (literal 'Date:') | (1,65) | 5 | ASKIP,NORM | BLUE | Label |
| CURDATE | (1,71) | 8 | ASKIP,FSET,NORM | BLUE | Current date MM/DD/YY, initial='mm/dd/yy' |

### Header Fields (Row 2)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| (literal 'Prog:') | (2,1) | 5 | ASKIP,NORM | BLUE | Label |
| PGMNAME | (2,7) | 8 | ASKIP,FSET,NORM | BLUE | Program name ('COTRN02C') |
| TITLE02 | (2,21) | 40 | ASKIP,FSET,NORM | YELLOW | App title line 2 |
| (literal 'Time:') | (2,65) | 5 | ASKIP,NORM | BLUE | Label |
| CURTIME | (2,71) | 8 | ASKIP,FSET,NORM | BLUE | Current time HH:MM:SS, initial='hh:mm:ss' |

### Screen Title (Row 4)

| Literal | POS | Length | ATTRB | Color |
|---|---|---|---|---|
| 'Add Transaction' | (4,30) | 15 | ASKIP,BRT | NEUTRAL |

### Account/Card Entry (Row 6)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Highlight | IC | Description |
|---|---|---|---|---|---|---|---|
| (literal 'Enter Acct #:') | (6,6) | 13 | ASKIP,NORM | TURQUOISE | — | — | Label |
| ACTIDIN | (6,21) | 11 | FSET,IC,NORM,UNPROT | GREEN | UNDERLINE | YES | Account ID input (11 digits) |
| (stopper) | (6,33) | 0 | ASKIP,NORM | — | — | — | Field terminator |
| (literal '(or)') | (6,37) | 4 | ASKIP,NORM | NEUTRAL | — | — | Separator label |
| (literal 'Card #:') | (6,46) | 7 | ASKIP,NORM | TURQUOISE | — | — | Label |
| CARDNIN | (6,55) | 16 | FSET,NORM,UNPROT | GREEN | UNDERLINE | — | Card number input (16 digits) |
| (stopper) | (6,72) | 0 | — | — | — | — | Field terminator |

Note: ACTIDIN has IC (Initial Cursor); CARDNIN does not. The cursor starts at ACTIDIN. The program uses whichever field is populated for cross-reference lookup.

### Separator Line (Row 8)

| Literal | POS | Length | ATTRB | Color |
|---|---|---|---|---|
| (70 dashes) | (8,6) | 70 | ASKIP,NORM | NEUTRAL |

### Type Code, Category, Source (Row 10)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Highlight | Description |
|---|---|---|---|---|---|---|
| (literal 'Type CD:') | (10,6) | 8 | ASKIP,NORM | TURQUOISE | — | Label |
| TTYPCD | (10,15) | 2 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Type code input; initial=' ' |
| (stopper) | (10,18) | 0 | — | — | — | Field terminator |
| (literal 'Category CD:') | (10,23) | 12 | ASKIP,NORM | TURQUOISE | — | Label |
| TCATCD | (10,36) | 4 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Category code input; initial=' ' |
| (stopper) | (10,41) | 0 | — | — | — | Field terminator |
| (literal 'Source:') | (10,46) | 7 | ASKIP,NORM | TURQUOISE | — | Label |
| TRNSRC | (10,54) | 10 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Source input; initial=' ' |
| (stopper) | (10,65) | 0 | — | — | — | Field terminator |

### Description (Row 12)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Highlight | Description |
|---|---|---|---|---|---|---|
| (literal 'Description:') | (12,6) | 12 | ASKIP,NORM | TURQUOISE | — | Label |
| TDESC | (12,19) | 60 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Description input; initial=' ' |
| (stopper) | (12,80) | 0 | — | — | — | Field terminator |

### Amount and Dates (Row 14) with Format Hints (Row 15)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Highlight | Description |
|---|---|---|---|---|---|---|
| (literal 'Amount:') | (14,6) | 7 | ASKIP,NORM | TURQUOISE | — | Label |
| TRNAMT | (14,14) | 12 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Amount input; format +/-99999999.99 |
| (stopper) | (14,27) | 0 | — | — | — | Field terminator |
| (literal 'Orig Date:') | (14,31) | 10 | ASKIP,NORM | TURQUOISE | — | Label |
| TORIGDT | (14,42) | 10 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Original date input YYYY-MM-DD |
| (stopper) | (14,53) | 0 | — | — | — | Field terminator |
| (literal 'Proc Date:') | (14,57) | 10 | ASKIP,NORM | TURQUOISE | — | Label |
| TPROCDT | (14,68) | 10 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Processing date input YYYY-MM-DD |
| (stopper) | (14,79) | 0 | — | — | — | Field terminator |

**Row 15 — Format hint labels (display-only):**

| Literal | POS | Length | ATTRB | Color | Purpose |
|---|---|---|---|---|---|
| '(-99999999.99)' | (15,13) | 14 | ASKIP,NORM | BLUE | Amount format guide |
| '(YYYY-MM-DD)' | (15,41) | 12 | ASKIP,NORM | BLUE | Orig Date format guide |
| '(YYYY-MM-DD)' | (15,67) | 12 | ASKIP,NORM | BLUE | Proc Date format guide |

### Merchant Information (Rows 16 and 18)

**Row 16 — Merchant ID and Name:**

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Highlight | Description |
|---|---|---|---|---|---|---|
| (literal 'Merchant ID:') | (16,6) | 12 | ASKIP,NORM | TURQUOISE | — | Label |
| MID | (16,19) | 9 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Merchant ID (numeric); initial=' ' |
| (stopper) | (16,29) | 0 | — | — | — | Field terminator |
| (literal 'Merchant Name:') | (16,33) | 14 | ASKIP,NORM | TURQUOISE | — | Label |
| MNAME | (16,48) | 30 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Merchant name; initial=' ' |
| (stopper) | (16,79) | 0 | — | — | — | Field terminator |

**Row 18 — Merchant City and ZIP:**

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Highlight | Description |
|---|---|---|---|---|---|---|
| (literal 'Merchant City:') | (18,6) | 14 | ASKIP,NORM | TURQUOISE | — | Label |
| MCITY | (18,21) | 25 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Merchant city; initial=' ' |
| (stopper) | (18,47) | 0 | — | — | — | Field terminator |
| (literal 'Merchant Zip:') | (18,53) | 13 | ASKIP,NORM | TURQUOISE | — | Label |
| MZIP | (18,67) | 10 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Merchant ZIP; initial=' ' |
| (stopper) | (18,78) | 0 | — | — | — | Field terminator |

### Confirmation Prompt (Row 21)

| Field Name | POS (Row,Col) | Length | ATTRB | Color | Highlight | Description |
|---|---|---|---|---|---|---|
| (literal 'You are about to add this transaction. Please confirm :') | (21,6) | 55 | ASKIP,NORM | TURQUOISE | — | Confirmation prompt |
| CONFIRM | (21,63) | 1 | FSET,NORM,UNPROT | GREEN | UNDERLINE | Y/N confirmation; single character |
| (stopper) | (21,65) | 0 | — | — | — | Field terminator |
| (literal '(Y/N)') | (21,66) | 5 | ASKIP,NORM | NEUTRAL | — | Valid value guide |

### Error/Message Line (Row 23)

| Field Name | POS | Length | ATTRB | Color | Description |
|---|---|---|---|---|---|
| ERRMSG | (23,1) | 78 | ASKIP,BRT,FSET | RED | Error or status message |

### Function Key Legend (Row 24)

| Literal | POS | Length | ATTRB | Color |
|---|---|---|---|---|
| 'ENTER=Continue  F3=Back  F4=Clear  F5=Copy Last Tran.' | (24,1) | 53 | ASKIP,NORM | YELLOW |

---

## 7. Input Fields Summary

| Field | Row,Col | Len | Attributes | IC | Required | Description |
|---|---|---|---|---|---|---|
| ACTIDIN | 6,21 | 11 | FSET,NORM,UNPROT,UNDERLINE | YES | One of these | Account ID (11 numeric digits) |
| CARDNIN | 6,55 | 16 | FSET,NORM,UNPROT,UNDERLINE | No | One of these | Card number (16 numeric digits) |
| TTYPCD | 10,15 | 2 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Transaction type code (numeric) |
| TCATCD | 10,36 | 4 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Category code (numeric) |
| TRNSRC | 10,54 | 10 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Transaction source |
| TDESC | 12,19 | 60 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Description |
| TRNAMT | 14,14 | 12 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Amount in format +/-99999999.99 |
| TORIGDT | 14,42 | 10 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Original date YYYY-MM-DD |
| TPROCDT | 14,68 | 10 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Processing date YYYY-MM-DD |
| MID | 16,19 | 9 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Merchant ID (numeric) |
| MNAME | 16,48 | 30 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Merchant name |
| MCITY | 18,21 | 25 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Merchant city |
| MZIP | 18,67 | 10 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Merchant ZIP |
| CONFIRM | 21,63 | 1 | FSET,NORM,UNPROT,UNDERLINE | No | Yes | Y to confirm add, N to cancel |

---

## 8. Output-Only Fields Summary

| Field | Row,Col | Len | Contents |
|---|---|---|---|
| TRNNAME | 1,7 | 4 | 'CT02' |
| TITLE01 | 1,21 | 40 | 'AWS Mainframe Modernization' |
| CURDATE | 1,71 | 8 | MM/DD/YY |
| PGMNAME | 2,7 | 8 | 'COTRN02C' |
| TITLE02 | 2,21 | 40 | 'CardDemo' |
| CURTIME | 2,71 | 8 | HH:MM:SS |
| ERRMSG | 23,1 | 78 | Error/status message (color-changeable by program) |

---

## 9. Symbolic Map Fields in COTRN02.CPY

The generated copybook (app/cpy-bms/COTRN02.CPY) creates:

**Input map COTRN2AI:**
- Header fields: TRNNAMEL/F/I, TITLE01L/F/I, CURDATEL/F/I, PGMNAMEL/F/I, TITLE02L/F/I, CURTIMEL/F/I
- Key entry: ACTIDINL/F/I (X(11)), CARDNINL/F/I (X(16))
- Transaction data: TTYPCDL/F/I (X(2)), TCATCDL/F/I (X(4)), TRNSRCL/F/I (X(10)), TDESCL/F/I (X(60))
- Financial: TRNAMTL/F/I (X(12)), TORIGDTL/F/I (X(10)), TPROCDTL/F/I (X(10))
- Merchant: MIDL/F/I (X(9)), MNAMEL/F/I (X(30)), MCITYL/F/I (X(25)), MZIPL/F/I (X(10))
- Confirmation: CONFIRML/F/I (X(1))
- Message: ERRMSGL/F/I (X(78))

**Output map COTRN2AO** REDEFINES COTRN2AI with `O` suffix fields and `C/P/H/V` attribute bytes. The `ERRMSGC` field (color byte for ERRMSG) is set to DFHGREEN by COTRN02C on successful write (line 727 of COTRN02C.cbl) to display the success message in green instead of the default red.

---

## 10. Comparison with COTRN01 (View) Screen

| Aspect | COTRN02 (Add) | COTRN01 (View) |
|---|---|---|
| Key field | ACTIDIN (account) + CARDNIN (card) | TRNIDIN (transaction ID) |
| Data fields | All UNPROT (editable) | All ASKIP (protected/display) |
| Confirmation | CONFIRM Y/N field present | No confirmation field |
| Format hints | Amount, Orig Date, Proc Date hints on row 15 | No format hints |
| Description length | 60 chars (same display length 60) | 60 chars |
| Merchant section | Row 16 + 18 (editable) | Row 18 + 20 (display only) |
| F5 function | 'Copy Last Tran.' | 'Browse Tran.' |
| Success message | Green ERRMSG with new Tran ID | N/A |

---

## 11. Program Usage

COTRN02C uses this mapset as follows:

| Operation | CICS Command |
|---|---|
| Display add screen | `EXEC CICS SEND MAP('COTRN2A') MAPSET('COTRN02') FROM(COTRN2AO) ERASE CURSOR` |
| Read operator input | `EXEC CICS RECEIVE MAP('COTRN2A') MAPSET('COTRN02') INTO(COTRN2AI)` |

Note: `SEND-TRNADD-SCREEN` in COTRN02C includes an embedded `EXEC CICS RETURN` immediately after the SEND, making the send-and-return a single operation.

---

## 12. Screen Navigation

```
Function Key  Action
-----------   ------
ENTER         Validate and attempt to add transaction (requires CONFIRM=Y)
F3            Return to calling program (or COMEN01C)
F4            Clear all fields
F5            Copy last transaction's data into fields (for quick duplicate entry)
```

---

## 13. Data Entry Sequence

The intended entry sequence enforced by program validation:

1. Enter Account ID (11 digits) OR Card Number (16 digits) — program resolves the other via XREF lookup.
2. Fill all transaction detail fields: Type CD, Category CD, Source, Description, Amount, Orig Date, Proc Date, Merchant ID, Name, City, ZIP.
3. Enter 'Y' in CONFIRM field.
4. Press ENTER — program writes new record and displays success message with generated Transaction ID.

---

## 14. Version and Change History

Source version stamp: `CardDemo_v1.0-70-g193b394-123  Date: 2022-08-22 17:02:43 CDT`
