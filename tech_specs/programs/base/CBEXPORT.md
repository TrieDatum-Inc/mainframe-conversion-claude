# Technical Specification: CBEXPORT

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | CBEXPORT                                             |
| Source File      | app/cbl/CBEXPORT.cbl                                 |
| Application      | CardDemo                                             |
| Type             | Batch COBOL Program                                  |
| Transaction ID   | N/A (batch)                                          |
| Function         | Export all CardDemo entity data (customers, accounts, cross-references, transactions, cards) into a single multi-record-type VSAM KSDS export file for branch migration purposes |

---

## 2. Program Flow

### High-Level Flow

```
START
  PERFORM 1000-INITIALIZE
      Generate timestamp (WS-FORMATTED-TIMESTAMP)
      OPEN all 5 input files (CUSTFILE, ACCTFILE, XREFFILE, TRANSACT, CARDFILE)
      OPEN EXPFILE (OUTPUT)

  PERFORM 2000-EXPORT-CUSTOMERS
      Read each customer record sequentially
      For each: CREATE EXPORT-RECORD with type='C', write to EXPFILE
      Count exported records

  PERFORM 3000-EXPORT-ACCOUNTS
      Read each account record sequentially
      For each: CREATE EXPORT-RECORD with type='A', write to EXPFILE

  PERFORM 4000-EXPORT-XREFS
      Read each cross-reference record sequentially
      For each: CREATE EXPORT-RECORD with type='X', write to EXPFILE

  PERFORM 5000-EXPORT-TRANSACTIONS
      Read each transaction record sequentially
      For each: CREATE EXPORT-RECORD with type='T', write to EXPFILE

  PERFORM 5500-EXPORT-CARDS
      Read each card record sequentially
      For each: CREATE EXPORT-RECORD with type='D', write to EXPFILE

  PERFORM 6000-FINALIZE
      CLOSE all files
      DISPLAY export statistics
STOP
```

### Paragraph-Level Detail

| Paragraph                  | Lines     | Description |
|----------------------------|-----------|-------------|
| 0000-MAIN-PROCESSING       | 149–158   | Top-level: calls all phases in sequence; GOBACK |
| 1000-INITIALIZE            | 161–169   | Display start message; call 1050-GENERATE-TIMESTAMP; call 1100-OPEN-FILES |
| 1050-GENERATE-TIMESTAMP    | 172–195   | ACCEPT date/time from DATE YYYYMMDD and TIME; formats WS-EXPORT-DATE (YYYY-MM-DD), WS-EXPORT-TIME (HH:MM:SS), WS-FORMATTED-TIMESTAMP (26 chars) |
| 1100-OPEN-FILES            | 198–240   | Opens all 6 files (5 input + 1 output); abends on any failure |
| 2000-EXPORT-CUSTOMERS      | 243–255   | Read-write loop for customer records |
| 2100-READ-CUSTOMER-RECORD  | 258–266   | READ CUSTOMER-INPUT; abends on non-OK/non-EOF |
| 2200-CREATE-CUSTOMER-EXP-REC | 269–310 | INITIALIZE EXPORT-RECORD; set EXPORT-REC-TYPE='C'; fill common header; map CVCUS01Y fields to EXP-CUST-* fields; WRITE to EXPFILE |
| 3000-EXPORT-ACCOUNTS       | 312–324   | Read-write loop for account records |
| 3100-READ-ACCOUNT-RECORD   | 327–335   | READ ACCOUNT-INPUT |
| 3200-CREATE-ACCOUNT-EXP-REC | 338–373  | Type='A'; maps CVACT01Y fields to EXP-ACCT-* fields |
| 4000-EXPORT-XREFS          | 376–388   | Read-write loop for xref records |
| 4100-READ-XREF-RECORD      | 391–399   | READ XREF-INPUT |
| 4200-CREATE-XREF-EXPORT-RECORD | 402–428 | Type='X'; maps CVACT03Y fields |
| 5000-EXPORT-TRANSACTIONS   | 431–443   | Read-write loop for transactions |
| 5100-READ-TRANSACTION-RECORD | 446–454 | READ TRANSACTION-INPUT |
| 5200-CREATE-TRAN-EXP-REC   | 457–493   | Type='T'; maps CVTRA05Y fields |
| 5500-EXPORT-CARDS          | 496–508   | Read-write loop for card records |
| 5600-READ-CARD-RECORD      | 511–519   | READ CARD-INPUT |
| 5700-CREATE-CARD-EXPORT-RECORD | 522–551 | Type='D'; maps CVACT02Y fields |
| 6000-FINALIZE              | 554–573   | CLOSE all files; DISPLAY statistics |
| 9999-ABEND-PROGRAM         | 576–579   | CALL 'CEE3ABD' (no parameters) |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Used In         | Contents |
|----------|-----------------|----------|
| CVCUS01Y | FD CUSTOMER-INPUT (line 75) | CUSTOMER-RECORD (500 bytes) |
| CVACT01Y | FD ACCOUNT-INPUT (line 78)  | ACCOUNT-RECORD (300 bytes) |
| CVACT03Y | FD XREF-INPUT (line 81)     | CARD-XREF-RECORD (50 bytes) |
| CVTRA05Y | FD TRANSACTION-INPUT (line 84) | TRAN-RECORD (350 bytes) |
| CVACT02Y | FD CARD-INPUT (line 87)     | CARD-RECORD (150 bytes) |
| CVEXPORT | WORKING-STORAGE (line 96)   | EXPORT-RECORD layout (500 bytes): EXPORT-SEQUENCE-NUM 9(9), EXPORT-REC-TYPE X(1), EXPORT-TIMESTAMP X(26), EXPORT-BRANCH-ID X(4), EXPORT-REGION-CODE X(5), then entity-specific fields via REDEFINES or continuation |

### File Description Records

| FD Name            | DD Name   | Org  | RECLN | Access     |
|--------------------|-----------|------|-------|------------|
| CUSTOMER-INPUT     | CUSTFILE  | KSDS | varies | Sequential |
| ACCOUNT-INPUT      | ACCTFILE  | KSDS | varies | Sequential |
| XREF-INPUT         | XREFFILE  | KSDS | varies | Sequential |
| TRANSACTION-INPUT  | TRANSACT  | KSDS | varies | Sequential |
| CARD-INPUT         | CARDFILE  | KSDS | varies | Sequential |
| EXPORT-OUTPUT      | EXPFILE   | KSDS | 500F  | Sequential (OUTPUT) |

Note: EXPORT-OUTPUT is declared as KSDS (`ORGANIZATION IS INDEXED`, `RECORD KEY IS EXPORT-SEQUENCE-NUM`), making it an indexed output file keyed on sequence number.

### Key Working Storage Variables

| Variable                      | PIC       | Purpose |
|-------------------------------|-----------|---------|
| WS-SEQUENCE-COUNTER           | 9(9)      | Monotonically incremented; used as EXPORT-SEQUENCE-NUM (KSDS key) |
| WS-FORMATTED-TIMESTAMP        | X(26)     | Timestamp embedded in every export record |
| WS-EXPORT-DATE / WS-EXPORT-TIME | X(10)/X(8) | Components of formatted timestamp |
| WS-CUSTOMER-RECORDS-EXPORTED  | 9(9)      | Statistics counter |
| WS-ACCOUNT-RECORDS-EXPORTED   | 9(9)      | Statistics counter |
| WS-XREF-RECORDS-EXPORTED      | 9(9)      | Statistics counter |
| WS-TRAN-RECORDS-EXPORTED      | 9(9)      | Statistics counter |
| WS-CARD-RECORDS-EXPORTED      | 9(9)      | Statistics counter |
| WS-TOTAL-RECORDS-EXPORTED     | 9(9)      | Grand total counter |
| WS-*-STATUS (6 fields)        | X(2) each | File status variables with 88-level CONDITIONS (OK='00', EOF='10') |
| EXPORT-RECORD                 | From CVEXPORT | 500-byte export record built before WRITE |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name  | File    | Org  | Access     | Mode     | Purpose |
|----------|---------|------|------------|----------|---------|
| CUSTFILE | CUSTOMER-INPUT | KSDS | Sequential | INPUT | All customer records |
| ACCTFILE | ACCOUNT-INPUT  | KSDS | Sequential | INPUT | All account records |
| XREFFILE | XREF-INPUT     | KSDS | Sequential | INPUT | All cross-reference records |
| TRANSACT | TRANSACTION-INPUT | KSDS | Sequential | INPUT | All transaction records |
| CARDFILE | CARD-INPUT     | KSDS | Sequential | INPUT | All card records |
| EXPFILE  | EXPORT-OUTPUT  | KSDS | Sequential | OUTPUT | Consolidated export file (500-byte fixed records) |

---

## 6. Screen Interaction

None. Batch program.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| CEE3ABD        | Static CALL | Abend on fatal error (no parameters passed, unlike other programs) |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| Any input file OPEN failure | DISPLAY error with status; PERFORM 9999-ABEND-PROGRAM |
| EXPORT-OUTPUT OPEN failure  | DISPLAY error with status; PERFORM 9999-ABEND-PROGRAM |
| Any READ error (non-OK, non-EOF) | DISPLAY error with status; PERFORM 9999-ABEND-PROGRAM |
| EXPORT WRITE error | DISPLAY 'ERROR: Writing export record, Status:' + status; PERFORM 9999-ABEND-PROGRAM |

---

## 9. Business Rules

1. **Record type codes**: C=Customer, A=Account, X=Cross-reference, T=Transaction, D=card (D presumably from "Debit/Credit card").
2. **Hardcoded branch metadata**: EXPORT-BRANCH-ID='0001', EXPORT-REGION-CODE='NORTH' are hardcoded in all record types. These would need parameterization for production use.
3. **Sequence key**: Each export record receives a unique monotonically increasing EXPORT-SEQUENCE-NUM starting at 1. This serves as the KSDS primary key.
4. **Ordering of entity types**: The export writes entities in order C → A → X → T → D. The import program (CBIMPORT) must handle interleaved types since it dispatches by type code.
5. **Timestamp**: A single timestamp is generated once at initialization and embedded in every export record, providing a consistent export-time marker.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| CUSTFILE  | All customer master records |
| ACCTFILE  | All account master records |
| XREFFILE  | All card-to-account cross-reference records |
| TRANSACT  | All transaction records |
| CARDFILE  | All credit card records |
| System clock | Date and time for export timestamp |

### Outputs

| Destination | Description |
|-------------|-------------|
| EXPFILE     | Multi-type indexed export file; 500-byte fixed records; keyed by sequence number |
| SYSOUT      | Export progress and statistics |

---

## 11. Key Variables and Their Purpose

| Variable              | Purpose |
|-----------------------|---------|
| EXPORT-RECORD         | 500-byte working area built before each WRITE; contains type code, sequence, timestamp, branch, and entity fields |
| WS-SEQUENCE-COUNTER   | Primary key for EXPFILE; ensures uniqueness |
| WS-FORMATTED-TIMESTAMP | 26-char timestamp string stamped on each record |
| WS-*-STATUS fields    | Per-file status; 88 conditions simplify EOF and OK checks |
