# Technical Specification: BMS Screen — COTRTUP (Transaction Type Add/Update)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COTRTUP |
| Map | CTRTUPA |
| Source File | `app/app-transaction-type-db2/bms/COTRTUP.bms` |
| Copybook | `app/app-transaction-type-db2/cpy-bms/COTRTUP.cpy` |
| COBOL Program | COTRTUPC |
| Domain | Reference Data |

## 2. Screen Layout

```
Row 1-2:  [Standard header]
Row 7:    "Maintain Transaction Type"
Row 12:   Transaction Type  : [__]
Row 14:   Description       : [__________________________________________________]
Row 22:   [Informational message]
Row 23:   [Error message]
Row 24:   ENTER=Process F3=Exit [F4=Delete] [F5=Save] [F6=Add] [F12=Cancel]
                                 (all initially DRK, revealed dynamically)
```

## 3. Fields

### Input
TRTYPCD(2, cursor initial), TRTYDSC(50)

### Dynamic Function Key Fields
FKEY04(9, DRK→"F4=Delete"), FKEY05(8, DRK→"F5=Save"), FKEY06(6, DRK→"F6=Add"), FKEY12(10, DRK→"F12=Cancel")

## 4. Function Keys

Context-dependent (revealed based on add vs edit mode):
- Add mode: ENTER, F3, F6=Add, F12=Cancel
- Edit mode: ENTER, F3, F4=Delete, F5=Save, F12=Cancel
