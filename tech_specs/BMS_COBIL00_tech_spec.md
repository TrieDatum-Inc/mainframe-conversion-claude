# Technical Specification: BMS Screen — COBIL00 (Bill Payment)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COBIL00 |
| Map | COBIL0A |
| Source File | `app/bms/COBIL00.bms` |
| Copybook | `app/cpy-bms/COBIL00.CPY` |
| COBOL Program | COBIL00C |
| Domain | Billing |

## 2. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "Bill Payment" (centered)
Row 6:    "Enter Acct ID:" [___________]
Row 8:    [Separator line]
Row 11:   "Your current balance is:" XXXXXXXXXXXXXX
Row 15:   "Do you want to pay your balance now. Please confirm:" [_] (Y/N)
Row 23:   [Error message]
Row 24:   ENTER=Continue  F3=Back  F4=Clear
```

## 3. Fields

| Field | Type | Length | Description |
|-------|------|--------|-------------|
| ACTIDIN | Input | 11 | Account ID |
| CURBAL | Output | 14 | Current balance display |
| CONFIRM | Input | 1 | Y/N confirmation |

## 4. Function Keys

ENTER=Process, F3=Back, F4=Clear
