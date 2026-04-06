# Technical Specification: BMS Screen — COCRDSL (View Credit Card Detail)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COCRDSL |
| Map | CCRDSLA |
| Source File | `app/bms/COCRDSL.bms` |
| Copybook | `app/cpy-bms/COCRDSL.CPY` |
| COBOL Program | COCRDSLC |
| Domain | Cards |

## 2. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "View Credit Card Detail"
Row 7:    Account Number    : [___________]
Row 8:    Card Number       : [________________]
Row 11:   Name on Card: __________________________________________________ (output)
Row 13:   Card Active: _ (output)
Row 15:   Expiry: __/____ (month/year, output)
Row 20:   [Informational message]
Row 23:   [Error message - 80 chars]
Row 24:   ENTER=Search Cards  F3=Exit
```

## 3. Fields

### Input
ACCTSID(11, cursor initial), CARDSID(16)

### Output
CRDNAME(50), CRDSTCD(1), EXPMON(2), EXPYEAR(4), INFOMSG(40)

## 4. Function Keys

ENTER=Search and display card, F3=Exit

## 5. Technical Notes

Uses DSATTS=(COLOR,HILIGHT,PS,VALIDN) and MAPATTS=(COLOR,HILIGHT,PS,VALIDN). ERRMSG is 80 chars (vs 78 in other screens).
