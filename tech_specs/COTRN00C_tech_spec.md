# Technical Specification: COTRN00C — Transaction List (Browse)

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COTRN00C |
| Source File | `app/cbl/COTRN00C.cbl` |
| Type | CICS Online |
| Transaction ID | CT00 |
| BMS Mapset | COTRN00 |
| BMS Map | COTRN0A |

## 2. Purpose

COTRN00C provides a **paginated list of transactions** from the TRANSACT VSAM file, displaying 10 transactions per page. Users can search by transaction ID, page forward/backward, and select a row with 'S' to view the transaction detail in COTRN01C.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA (extended with CDEMO-CT00-INFO) |
| COTRN00 | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y | Standard infrastructure |
| CVTRA05Y | TRAN-RECORD layout (350 bytes) |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| TRANSACT | Browse | STARTBR, READNEXT, READPREV, ENDBR | TRAN-ID X(16) |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| TRNIDIN | 16 | Search/filter by starting transaction ID |
| SEL0001–SEL0010 | 1 each | Row selection ('S' to view detail) |

### Output Fields (10 rows)
| Field | Length | Description |
|-------|--------|-------------|
| TRNID01–TRNID10 | 16 each | Transaction IDs |
| TDATE01–TDATE10 | 8 each | Transaction dates (MM/DD/YY) |
| TDESC01–TDESC10 | 26 each | Transaction descriptions |
| TAMT001–TAMT010 | 12 each | Transaction amounts (+99999999.99) |
| PAGENUM | 8 | Current page number |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Search/refresh |
| PF3 | Back to COMEN01C |
| PF7 | Page backward |
| PF8 | Page forward |

## 6. Program Flow

```
1. On ENTER with TRNIDIN:
   a. Validate TRNIDIN is numeric
   b. STARTBR from TRNIDIN key
   c. READNEXT 10 records, format dates and amounts
   d. Track first/last TRAN-ID in COMMAREA

2. Row Selection ('S'):
   → Set CDEMO-CT00-TRNID-SELECTED in COMMAREA
   → XCTL to COTRN01C

3. PF8 (Forward): STARTBR from last key, READNEXT 10
4. PF7 (Backward): STARTBR from first key, READPREV 10
```

## 7. Data Formatting

- **Date**: TRAN-ORIG-TS (26-char timestamp) parsed into MM/DD/YY display format.
- **Amount**: Formatted as +99999999.99 in WS-TRAN-AMT.

## 8. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COTRN01C | XCTL | Row selected with 'S' |
| COMEN01C | XCTL | PF3 |

### COMMAREA Extension (CDEMO-CT00-INFO)
- CDEMO-CT00-TRNID-FIRST / CDEMO-CT00-TRNID-LAST — page boundary keys
- CDEMO-CT00-PAGE-NUM — current page
- CDEMO-CT00-TRNID-SELECTED — selected transaction ID for detail view
