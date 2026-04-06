# Technical Specification: BMS Screen — COCRDLI (List Credit Cards)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COCRDLI |
| Map | CCRDLIA |
| Source File | `app/bms/COCRDLI.bms` |
| Copybook | `app/cpy-bms/COCRDLI.CPY` |
| COBOL Program | COCRDLIC |
| Domain | Cards |

## 2. Purpose

Paginated list of credit cards (7 per page). Search filter for Account Number and Card Number.

## 3. Screen Layout

```
Row 1-2:  [Standard header]      PAGENO at row 4,76
Row 6:    Account Number    : [___________]
Row 7:    Credit Card Number: [________________]
Row 9:    Column headers: Select | Account Number | Card Number | Active
Row 11-17: [7 data rows]
Row 20:   [Informational message]
Row 23:   [Error message]
Row 24:   F3=Exit F7=Backward  F8=Forward
```

## 4. Fields (7 rows)

### Input
ACCTSID(11), CARDSID(16), CRDSEL1–CRDSEL7(1 each)

### Output per row
ACCTNO(11), CRDNUM(16), CRDSTS(1)

## 5. Technical Notes

Uses CRDSTP fields (DRK, FSET) as hidden sentinel/stop bytes between rows 2–7. CRDSEL1 on row 1 is PROT — selection mechanism uses the CRDSTP sentinels.

## 6. Function Keys

F3=Exit, F7=Page backward, F8=Page forward
