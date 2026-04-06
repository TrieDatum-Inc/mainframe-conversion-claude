# Technical Specification: BMS Screen — CORPT00 (Transaction Reports)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | CORPT00 |
| Map | CORPT0A |
| Source File | `app/bms/CORPT00.bms` |
| Copybook | `app/cpy-bms/CORPT00.CPY` |
| COBOL Program | CORPT00C |
| Domain | Reporting |

## 2. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "Transaction Reports" (centered)
Row 7:    [_] Monthly (Current Month)
Row 9:    [_] Yearly (Current Year)
Row 11:   [_] Custom (Date Range)
Row 13:   Start Date: [__]/[__]/[____] (MM/DD/YYYY)
Row 14:     End Date: [__]/[__]/[____] (MM/DD/YYYY)
Row 19:   "The Report will be submitted for printing. Please confirm:" [_] (Y/N)
Row 23:   [Error message]
Row 24:   ENTER=Continue  F3=Back
```

## 3. Input Fields

| Field | Length | Description |
|-------|--------|-------------|
| MONTHLY | 1 | Select monthly (cursor initial) |
| YEARLY | 1 | Select yearly |
| CUSTOM | 1 | Select custom range |
| SDTMM/SDTDD/SDTYYYY | 2/2/4 | Start date |
| EDTMM/EDTDD/EDTYYYY | 2/2/4 | End date |
| CONFIRM | 1 | Y/N confirmation |

## 4. Function Keys

ENTER=Submit report, F3=Back to menu
