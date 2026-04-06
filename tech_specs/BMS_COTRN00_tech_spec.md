# Technical Specification: BMS Screen — COTRN00 (List Transactions)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COTRN00 |
| Map | COTRN0A |
| Source File | `app/bms/COTRN00.bms` |
| Copybook | `app/cpy-bms/COTRN00.CPY` |
| COBOL Program | COTRN00C |
| Domain | Transactions |

## 2. Purpose

Paginated list of transactions with 10 rows per page. Supports search by Transaction ID, forward/backward paging, and row selection for detail view.

## 3. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    PAGENUM (right side)
Row 6:    "Search Tran ID:" [________________] (16 chars)
Row 8:    Column headers: Sel | Transaction ID | Date | Description | Amount
Row 10-19: [10 data rows with SEL, TRNID, TDATE, TDESC, TAMT]
Row 21:   "Type 'S' to View Transaction details from the list"
Row 23:   [Error message - RED]
Row 24:   ENTER=Continue  F3=Back  F7=Backward  F8=Forward
```

## 4. Field Definitions

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| TRNIDIN | 16 | Search filter by transaction ID |
| SEL0001–SEL0010 | 1 each | Row selection ('S' to view) |

### Output Fields (10 rows)
| Field | Length | Description |
|-------|--------|-------------|
| TRNID01–TRNID10 | 16 | Transaction IDs |
| TDATE01–TDATE10 | 8 | Transaction dates |
| TDESC01–TDESC10 | 26 | Descriptions |
| TAMT001–TAMT010 | 12 | Amounts |

## 5. Function Keys

| Key | Action |
|-----|--------|
| ENTER | Search/refresh |
| F3 | Back to menu |
| F7 | Page backward |
| F8 | Page forward |

## 6. Navigation

Selecting a row with 'S' navigates to COTRN01 (View Transaction).
