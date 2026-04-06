# Technical Specification: COTRN01C — View Transaction Detail

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COTRN01C |
| Source File | `app/cbl/COTRN01C.cbl` |
| Type | CICS Online |
| Transaction ID | CT01 |
| BMS Mapset | COTRN01 |
| BMS Map | COTRN1A |

## 2. Purpose

COTRN01C displays the **complete detail** of a single transaction record from the TRANSACT VSAM file. It can receive a pre-selected transaction ID from COTRN00C via COMMAREA, or accept a typed transaction ID.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA (extended with CDEMO-CT01-INFO) |
| COTRN01 | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y | Standard infrastructure |
| CVTRA05Y | TRAN-RECORD layout |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| TRANSACT | Read | READ (with UPDATE flag — see note) | TRAN-ID X(16) |

**Note**: The program reads TRANSACT with UPDATE flag but never performs REWRITE or DELETE. This is a view-only screen — the UPDATE lock is held until the CICS task ends. This appears to be a code defect.

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| TRNIDIN | 16 | Transaction ID to fetch (cursor initial) |

### Output Fields
| Field | Length | Description |
|-------|--------|-------------|
| TRNID | 16 | Transaction ID |
| CARDNUM | 16 | Card number |
| TTYPCD | 2 | Transaction type code |
| TCATCD | 4 | Category code |
| TRNSRC | 10 | Source |
| TDESC | 60 | Description |
| TRNAMT | 12 | Amount |
| TORIGDT | 10 | Original date |
| TPROCDT | 10 | Processing date |
| MID | 9 | Merchant ID |
| MNAME | 30 | Merchant name |
| MCITY | 25 | Merchant city |
| MZIP | 10 | Merchant zip |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Fetch transaction by ID |
| PF3 | Back to calling program or COMEN01C |
| PF4 | Clear input |
| PF5 | Browse transactions (navigate to COTRN00C) |

## 6. Program Flow

```
1. First entry with CDEMO-CT01-TRN-SELECTED populated (from COTRN00C):
   → Move selected ID to TRNIDIN
   → Auto-fetch and display the record

2. On ENTER:
   → READ TRANSACT by TRNIDIN
   → Populate all output fields
   → Display transaction detail

3. PF5: XCTL to COTRN00C (transaction list)
```

## 7. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| CDEMO-FROM-PROGRAM | XCTL | PF3 |
| COMEN01C | XCTL | PF3 default |
| COTRN00C | XCTL | PF5 |
