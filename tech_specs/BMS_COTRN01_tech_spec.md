# Technical Specification: BMS Screen — COTRN01 (View Transaction)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COTRN01 |
| Map | COTRN1A |
| Source File | `app/bms/COTRN01.bms` |
| Copybook | `app/cpy-bms/COTRN01.CPY` |
| COBOL Program | COTRN01C |
| Domain | Transactions |

## 2. Purpose

Displays complete detail of a single transaction. User can fetch by typing a Transaction ID or navigate here from COTRN00.

## 3. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "View Transaction" (centered)
Row 6:    "Enter Tran ID:" [________________]
Row 8:    [Separator line]
Row 10:   Transaction ID: XXXXXXXXXXXXXXXX    Card Number: XXXXXXXXXXXXXXXX
Row 12:   Type: XX    Category: XXXX    Source: XXXXXXXXXX
Row 14:   Description: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Row 16:   Amount: XXXXXXXXXXXX    Orig Date: XXXXXXXXXX    Proc Date: XXXXXXXXXX
Row 18:   Merchant ID: XXXXXXXXX    Name: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Row 20:   City: XXXXXXXXXXXXXXXXXXXXXXXXX    Zip: XXXXXXXXXX
Row 23:   [Error message]
Row 24:   ENTER=Fetch  F3=Back  F4=Clear  F5=Browse Tran.
```

## 4. Field Definitions

### Input
| Field | Length | Description |
|-------|--------|-------------|
| TRNIDIN | 16 | Transaction ID to fetch |

### Output (all ASKIP,NORM,BLUE)
TRNID(16), CARDNUM(16), TTYPCD(2), TCATCD(4), TRNSRC(10), TDESC(60), TRNAMT(12), TORIGDT(10), TPROCDT(10), MID(9), MNAME(30), MCITY(25), MZIP(10)

## 5. Function Keys

| Key | Action |
|-----|--------|
| ENTER | Fetch transaction |
| F3 | Back to COTRN00 |
| F4 | Clear input |
| F5 | Browse transactions |
