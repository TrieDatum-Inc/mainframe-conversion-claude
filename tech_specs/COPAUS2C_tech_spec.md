# Technical Specification: COPAUS2C — Fraud Mark/Remove

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COPAUS2C |
| Source File | `app/app-authorization-ims-db2-mq/cbl/COPAUS2C.cbl` |
| Type | CICS Online (DB2) |
| Invocation | EXEC CICS LINK from COPAUS1C only |

## 2. Purpose

COPAUS2C **inserts or updates a fraud record in the DB2 AUTHFRDS table**. It is invoked as a LINK (not XCTL) and returns control to COPAUS1C.

## 3. Data Access

### DB2 Table: CARDDEMO.AUTHFRDS
| Column | Type | Description |
|--------|------|-------------|
| CARD_NUM | CHAR(16) | Primary key part 1 |
| AUTH_TS | TIMESTAMP | Primary key part 2 |
| FRAUD_RPT_DATE | DATE | Date fraud reported |
| AUTH_FRAUD | CHAR(1) | Fraud flag (F/R) |
| MATCH_STATUS | CHAR(1) | Match status |
| ACCT_ID | DECIMAL(11) | Account ID |
| CUST_ID | DECIMAL(9) | Customer ID |
| + 20 more columns | — | Full authorization details |

### DB2 Operations
- On fraud report: INSERT INTO AUTHFRDS (new fraud record)
- On fraud update: UPDATE AUTHFRDS SET AUTH_FRAUD, FRAUD_RPT_DATE

## 4. Time Reversal Formula

The IMS detail segment stores time as a 9-complement:
```
COMPUTE WS-AUTH-TIME = 999999999 - PA-AUTH-TIME-9C
```
This reverses the encoding to reconstruct the actual timestamp for DB2 storage.

## 5. LINKAGE Section

Receives from COPAUS1C via DFHCOMMAREA:
- Full CIPAUDTY record (authorization detail, 200 bytes)
- Fraud action record: action flag ('F'=report, 'R'=remove), status ('S'=success, 'F'=failed), message

## 6. Return Values

| Status | Meaning |
|--------|---------|
| WS-FRD-UPDT-SUCCESS ('S') | DB2 operation succeeded |
| WS-FRD-UPDT-FAILED ('F') | DB2 operation failed |
