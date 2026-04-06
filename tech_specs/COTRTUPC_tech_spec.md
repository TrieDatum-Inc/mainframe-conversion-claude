# Technical Specification: COTRTUPC — Transaction Type Add/Update (DB2)

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COTRTUPC |
| Source File | `app/app-transaction-type-db2/cbl/COTRTUPC.cbl` |
| Type | CICS Online (DB2) |
| Transaction ID | CTTU |
| BMS Mapset | COTRTUP |
| BMS Map | CTRTUPA |

## 2. Purpose

COTRTUPC provides a **single-record form** for adding a new transaction type or updating an existing one. Receives the TR_TYPE key from COTRTLIC via COMMAREA.

## 3. DB2 Access

| Operation | Table | Description |
|-----------|-------|-------------|
| INSERT | CARDDEMO.TRANSACTION_TYPE | Add new type |
| UPDATE | CARDDEMO.TRANSACTION_TYPE | Update description WHERE TR_TYPE = :host-var |

## 4. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| TRTYPCD | 2 | Transaction type code (cursor initial) |
| TRTYDSC | 50 | Description |

### Dynamic Function Keys (initially hidden, revealed based on mode)
| Key | Action |
|-----|--------|
| ENTER | Process/validate |
| F3 | Exit to COTRTLI |
| F4 | Delete (edit mode only) |
| F5 | Save (edit mode only) |
| F6 | Add (add mode only) |
| F12 | Cancel |

## 5. Input Validation

- TR_TYPE: alphanumeric, non-blank, 2 characters
- Description: non-blank
- WS-DATACHANGED-FLAG: detects edits before issuing update

## 6. Copybooks Used

COTRTUP (BMS), CSUTLDWY, COCOM01Y, CSDB2RPY, CSDB2RWY
