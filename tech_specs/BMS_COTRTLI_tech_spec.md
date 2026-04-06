# Technical Specification: BMS Screen — COTRTLI (Transaction Type List)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COTRTLI |
| Map | CTRTLIA |
| Source File | `app/app-transaction-type-db2/bms/COTRTLI.bms` |
| Copybook | `app/app-transaction-type-db2/cpy-bms/COTRTLI.cpy` |
| COBOL Program | COTRTLIC |
| Domain | Reference Data |

## 2. Purpose

Paginated list of transaction type codes with inline editing capability. 7+1 rows per page. Description fields are UNPROT for inline editing.

## 3. Screen Layout

```
Row 1-2:  [Standard header]    PAGENO at row 4,76
Row 6:    Transaction Type: [__]
Row 8:    Description: [__________________________________________________]
Row 10:   Column headers: Select | Type Code | Description
Row 12-18: [7 editable rows + 1 overflow row (protected)]
Row 21:   [Informational message]
Row 23:   [Error message]
Row 24:   F2=Add  F3=Exit  F7=Page Up  F8=Page Dn  F10=Save
```

## 4. Fields

### Filter Input
TRTYPE(2, cursor initial), TRDESC(50)

### List Rows (7 editable + 1 protected)
TRTSEL1–7(1, PROT selectors), TRTTYP1–7(2, PROT type codes), TRTYPD1–7(50, UNPROT descriptions)
Row 8: TRTSELA/TRTTYPA/TRTDSCA all PROT (overflow/spacer row)

## 5. Function Keys

F2=Add new type (→COTRTUP), F3=Exit, F7=Page up, F8=Page down, F10=Save inline edits
