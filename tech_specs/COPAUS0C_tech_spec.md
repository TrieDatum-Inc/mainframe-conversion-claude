# Technical Specification: COPAUS0C — Authorization Summary View

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COPAUS0C |
| Source File | `app/app-authorization-ims-db2-mq/cbl/COPAUS0C.cbl` |
| Type | CICS Online (IMS BMS) |
| Transaction ID | CPVS |
| BMS Mapset | COPAU00 |
| BMS Map | COPAU0A |

## 2. Purpose

COPAUS0C displays a **paged list of pending authorizations** for a given account. It shows account summary information (name, address, credit limits, balances, approval/decline counts) at the top, then up to 5 authorization transactions per page.

## 3. Data Access

### IMS Database (DBPAUTP0 via PSB PSBPAUTB, PCB +1)
| Segment | Operation | Description |
|---------|-----------|-------------|
| PAUTSUM0 | GU, GN | Read account summary |
| PAUTDTL1 | GN | Read authorization details (5 per page) |

### VSAM Files
| File DD | Purpose |
|---------|---------|
| ACCTDAT | Account data |
| CUSTDAT | Customer data |
| CARDDAT | Card data |
| CXACAIX | Card-xref alternate index |
| CCXREF | Card-to-account cross reference |

## 4. Screen Layout

- Rows 1–2: Standard header
- Row 3: Title "View Authorizations"
- Rows 5–12: Account summary (name, address, limits, balances, approve/decline counts)
- Rows 14–15: Column headers
- Rows 16–20: Authorization list (5 rows: Sel, Transaction ID, Date, Time, Type, A/D, Status, Amount)
- Row 22: "Type 'S' to View Authorization details from the list"

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Search/navigate |
| PF3 | Back to menu |
| PF7 | Page backward |
| PF8 | Page forward |

## 5. Navigation

- Selecting a row with 'S' → XCTL to COPAUS1C (detail view)
- PF3 → XCTL to COMEN01C

### COMMAREA Extension (CDEMO-CPVS-INFO)
- Page number, auth key list (5 per page), prev-page key stack (20 deep), next-page flag

## 6. Copybooks Used

COPAU00, COCOM01Y, COTTL01Y, CSDAT01Y, CSMSG01Y, CSMSG02Y, CVACT01Y, CVACT02Y, CVACT03Y, CIPAUSMY, CIPAUDTY
