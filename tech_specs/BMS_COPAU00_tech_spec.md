# Technical Specification: BMS Screen — COPAU00 (View Authorizations List)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COPAU00 |
| Map | COPAU0A |
| Source File | `app/app-authorization-ims-db2-mq/bms/COPAU00.bms` |
| COBOL Program | COPAUS0C |
| Domain | Authorization |

## 2. Purpose

Lists pending authorization records for a given account. Shows account summary at top, then up to 5 authorization transactions per page.

## 3. Screen Layout

```
Row 1-2:  [Standard header]
Row 3:    "View Authorizations" (title at row 3, not row 4)
Row 5:    Account ID: [___________]
Row 6-9:  Customer name, address, phone, approval/decline counts
Row 11-12: Credit/cash limits, balances, approved/declined amounts
Row 14-15: Column headers
Row 16-20: [5 authorization rows: Sel|Tran ID|Date|Time|Type|A/D|STS|Amount]
Row 22:   "Type 'S' to View Authorization details from the list"
Row 23:   [Error message]
Row 24:   ENTER=Continue  F3=Back  F7=Backward  F8=Forward
```

## 4. Fields

### Input
ACCTID(11), SEL0001–SEL0004(1 each, 'S' to select)

### Account Summary Output
CNAME(25), CUSTID(9), ADDR001/002(25), ACCSTAT(1), PHONE1(13), APPRCNT/DECLCNT(3), CREDLIM/CASHLIM(12/9), APPRAMT/DECLAMT(10), CREDBAL/CASHBAL(12/9)

### Authorization List (5 rows)
TRNID01–05(16), PDATE01–05(8), PTIME01–05(8), PTYPE01–05(4), PAPRV01–05(1), PSTAT01–05(1), PAMT001–005(12)

## 5. Function Keys

ENTER=Search, F3=Back, F7=Backward, F8=Forward

## 6. Navigation

Selecting with 'S' → COPAU01 (detail view)
