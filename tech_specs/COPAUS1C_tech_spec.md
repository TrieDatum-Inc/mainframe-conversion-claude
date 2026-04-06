# Technical Specification: COPAUS1C — Authorization Detail View

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COPAUS1C |
| Source File | `app/app-authorization-ims-db2-mq/cbl/COPAUS1C.cbl` |
| Type | CICS Online (IMS BMS) |
| Transaction ID | CPVD |
| BMS Mapset | COPAU01 |
| BMS Map | COPAU1A |

## 2. Purpose

COPAUS1C displays the **full detail of a single pending authorization record** and allows the operator to mark or remove fraud flags.

## 3. Data Access

### IMS Database (DBPAUTP0 via PSB PSBPAUTB, PCB +1)
| Segment | Operation | Description |
|---------|-----------|-------------|
| PAUTSUM0 | GU | Read parent summary by account key |
| PAUTDTL1 | GU (qualified SSA) | Read specific detail by timestamp key |

## 4. Screen Fields (Output)

| Field | Description |
|-------|-------------|
| CARDNUM | Card number |
| AUTHDT / AUTHTM | Authorization date / time |
| AUTHRSP | Response (A=Approved, D=Declined) |
| AUTHRSN | Response reason text |
| AUTHCD | Authorization code |
| AUTHAMT | Amount |
| POSEMD | POS entry mode |
| AUTHSRC | Authorization source |
| MCCCD | MCC code |
| CRDEXP | Card expiry |
| AUTHTYP | Auth type |
| TRNID | Transaction ID |
| AUTHMTC | Match status (P/D/E/M) |
| AUTHFRD | Fraud status (highlighted RED) |
| Merchant | Name, ID, City, State, Zip |

## 5. Decline Reason Lookup Table

10-entry binary search table (SEARCH ALL):
| Code | Description |
|------|-------------|
| 0000 | APPROVED |
| 3100 | INVALID CARD |
| 4100 | INSUFFICNT FUND |
| 4200 | CARD NOT ACTIVE |
| 4300 | ACCOUNT CLOSED |
| 4400 | EXCED DAILY LMT |
| 5100 | CARD FRAUD |
| 5200 | MERCHANT FRAUD |
| 5300 | LOST CARD |
| 9000 | UNKNOWN |

## 6. Fraud Action

On PF5 (Mark/Remove Fraud):
- Sets WS-REPORT-FRAUD ('F') or WS-REMOVE-FRAUD ('R')
- EXEC CICS LINK PROGRAM(COPAUS2C) COMMAREA(WS-FRAUD-DATA)
- COMMAREA: ACCT-ID (9(11)), CUST-ID (9(9)), WS-FRAUD-AUTH-RECORD (CIPAUDTY, 200 bytes), WS-FRAUD-STATUS-RECORD (action + status + message)

### Function Keys
| Key | Action |
|-----|--------|
| F3 | Back to COPAUS0C |
| F5 | Mark/Remove fraud flag |
| F8 | Next authorization record |

## 7. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COPAUS0C | XCTL | PF3 |
| COPAUS2C | LINK | PF5 (fraud action) |
