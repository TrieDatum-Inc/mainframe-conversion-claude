# Technical Specification: BMS Screen — COCRDUP (Update Credit Card)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COCRDUP |
| Map | CCRDUPA |
| Source File | `app/bms/COCRDUP.bms` |
| Copybook | `app/cpy-bms/COCRDUP.CPY` |
| COBOL Program | COCRDUPC |
| Domain | Cards |

## 2. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "Update Credit Card Details"
Row 7:    Account Number    : XXXXXXXXXXX (PROTECTED)
Row 8:    Card Number       : [________________]
Row 11:   Name on Card: [__________________________________________________]
Row 13:   Card Active: [_] (Y/N)
Row 15:   Expiry: [__]/[____] (month/year)
Row 23:   [Error message - 80 chars]
Row 24:   ENTER=Process F3=Exit  [F5=Save F12=Cancel] (initially hidden)
```

## 3. Fields

### Protected Output
ACCTSID(11) — Account number cannot be changed

### Editable Input
CARDSID(16), CRDNAME(50), CRDSTCD(1), EXPMON(2, JUSTIFY RIGHT), EXPYEAR(4, JUSTIFY RIGHT)

### Hidden
EXPDAY(2, DRK,PROT) — system-maintained
FKEYSC(18, DRK) — "F5=Save F12=Cancel" revealed dynamically

## 4. Function Keys

| Key | Visibility | Action |
|-----|-----------|--------|
| ENTER | Always | Process/validate |
| F3 | Always | Exit |
| F5 | Dynamic | Save |
| F12 | Dynamic | Cancel |
