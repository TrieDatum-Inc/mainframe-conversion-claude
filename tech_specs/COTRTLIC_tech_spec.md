# Technical Specification: COTRTLIC — Transaction Type List (DB2)

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COTRTLIC |
| Source File | `app/app-transaction-type-db2/cbl/COTRTLIC.cbl` |
| Type | CICS Online (DB2) |
| Transaction ID | CTLI |
| BMS Mapset | COTRTLI |
| BMS Map | CTRTLIA |

## 2. Purpose

COTRTLIC displays a **pageable list of transaction type codes** from the DB2 TRANSACTION_TYPE table, 7 rows per page. Supports filtering by type code and description, inline editing of descriptions, and inline delete of selected rows.

## 3. DB2 Access

| Operation | Table | Description |
|-----------|-------|-------------|
| SELECT (cursor) | CARDDEMO.TRANSACTION_TYPE | Paginated read with optional WHERE filters |
| DELETE | CARDDEMO.TRANSACTION_TYPE | Inline delete of selected rows |
| UPDATE | CARDDEMO.TRANSACTION_TYPE | Inline update of descriptions |

Uses DSNTIAC for DB2 error message formatting.

## 4. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COTRTLI | BMS symbolic map |
| CSDB2RPY | DB2 common procedure paragraphs |
| CSDB2RWY | DB2 common working storage |
| COCOM01Y | CARDDEMO-COMMAREA |
| CSDAT01Y, CSMSG01Y, CSMSG02Y | Standard infrastructure |
| CSUTLDWY | Date validation working storage |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| TRTYPE | 2 | Filter by transaction type code |
| TRDESC | 50 | Filter by description |
| TRTSEL1–TRTSEL7 | 1 each | Row selectors |
| TRTYPD1–TRTYPD7 | 50 each | Description (UNPROT — inline editable) |

### Output Fields (7 rows)
| Field | Length | Description |
|-------|--------|-------------|
| TRTTYP1–TRTTYP7 | 2 each | Type codes (protected) |
| PAGENO | 3 | Page number |

### Function Keys
| Key | Action |
|-----|--------|
| F2 | Add new type (navigate to COTRTUPC) |
| F3 | Exit to admin menu |
| F7 | Page up |
| F8 | Page down |
| F10 | Save inline edits |

## 6. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COTRTUPC | XCTL | F2 or row selection for add/update |
| COADM01C | XCTL | F3 (TRANID CA00) |
