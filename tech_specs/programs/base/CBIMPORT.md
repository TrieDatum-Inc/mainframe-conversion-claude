# Technical Specification: CBIMPORT

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | CBIMPORT                                             |
| Source File      | app/cbl/CBIMPORT.cbl                                 |
| Application      | CardDemo                                             |
| Type             | Batch COBOL Program                                  |
| Transaction ID   | N/A (batch)                                          |
| Function         | Import branch migration data from a consolidated multi-record-type VSAM KSDS export file (EXPFILE) and split it into five separate normalized sequential output files (customer, account, xref, transaction, card). Unknown record types are written to an error file. Reverse operation of CBEXPORT. |

---

## 2. Program Flow

### High-Level Flow

```
START
  PERFORM 1000-INITIALIZE
      Format WS-IMPORT-DATE and WS-IMPORT-TIME from FUNCTION CURRENT-DATE
      OPEN EXPORT-INPUT (INPUT KSDS sequential)
      OPEN CUSTOMER-OUTPUT, ACCOUNT-OUTPUT, XREF-OUTPUT,
           TRANSACTION-OUTPUT, CARD-OUTPUT, ERROR-OUTPUT (all OUTPUT sequential)

  PERFORM 2000-PROCESS-EXPORT-FILE
      Priming read (2100-READ-EXPORT-RECORD)
      PERFORM UNTIL WS-EXPORT-EOF:
          ADD 1 TO WS-TOTAL-RECORDS-READ
          PERFORM 2200-PROCESS-RECORD-BY-TYPE (EVALUATE on EXPORT-REC-TYPE)
          PERFORM 2100-READ-EXPORT-RECORD (next read)

  PERFORM 3000-VALIDATE-IMPORT (stub — DISPLAY "No validation errors")

  PERFORM 4000-FINALIZE
      CLOSE all 7 files
      DISPLAY import statistics
STOP
```

### Paragraph-Level Detail

| Paragraph                    | Lines     | Description |
|------------------------------|-----------|-------------|
| 0000-MAIN-PROCESSING         | 165–171   | Top-level: calls all phases in sequence; GOBACK |
| 1000-INITIALIZE              | 174–193   | Display start; build WS-IMPORT-DATE / WS-IMPORT-TIME from FUNCTION CURRENT-DATE; PERFORM 1100-OPEN-FILES |
| 1100-OPEN-FILES              | 196–245   | Opens all 7 files (1 input + 5 output + 1 error); abends on any failure |
| 2000-PROCESS-EXPORT-FILE     | 248–256   | Priming read loop; increments WS-TOTAL-RECORDS-READ per record |
| 2100-READ-EXPORT-RECORD      | 259–267   | READ EXPORT-INPUT INTO EXPORT-RECORD; abends on non-OK/non-EOF |
| 2200-PROCESS-RECORD-BY-TYPE  | 270–285   | EVALUATE EXPORT-REC-TYPE: dispatches C/A/X/T/D/OTHER |
| 2300-PROCESS-CUSTOMER-RECORD | 288–320   | Maps EXP-CUST-* fields to CUSTOMER-RECORD fields; WRITE to CUSTOMER-OUTPUT; increments counter |
| 2400-PROCESS-ACCOUNT-RECORD  | 323–349   | Maps EXP-ACCT-* fields to ACCOUNT-RECORD; WRITE to ACCOUNT-OUTPUT |
| 2500-PROCESS-XREF-RECORD     | 352–369   | Maps EXP-XREF-* fields to CARD-XREF-RECORD; WRITE to XREF-OUTPUT |
| 2600-PROCESS-TRAN-RECORD     | 372–399   | Maps EXP-TRAN-* fields to TRAN-RECORD; WRITE to TRANSACTION-OUTPUT |
| 2650-PROCESS-CARD-RECORD     | 402–422   | Maps EXP-CARD-* fields to CARD-RECORD; WRITE to CARD-OUTPUT |
| 2700-PROCESS-UNKNOWN-RECORD  | 425–434   | Increments WS-UNKNOWN-RECORD-TYPE-COUNT; builds WS-ERROR-RECORD; PERFORM 2750-WRITE-ERROR |
| 2750-WRITE-ERROR             | 437–446   | WRITE ERROR-OUTPUT-RECORD FROM WS-ERROR-RECORD; increments WS-ERROR-RECORDS-WRITTEN |
| 3000-VALIDATE-IMPORT         | 449–452   | Stub — two DISPLAY statements only; no actual validation performed |
| 4000-FINALIZE                | 455–478   | CLOSE all 7 files; DISPLAY summary statistics |
| 9999-ABEND-PROGRAM           | 481–484   | DISPLAY 'CBIMPORT: ABENDING PROGRAM'; CALL 'CEE3ABD' |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Used In         | Contents |
|----------|-----------------|----------|
| CVEXPORT | WORKING-STORAGE (line 113) | EXPORT-RECORD layout (500 bytes): EXPORT-SEQUENCE-NUM 9(9), EXPORT-REC-TYPE X(1), EXPORT-TIMESTAMP X(26), EXPORT-BRANCH-ID X(4), EXPORT-REGION-CODE X(5), then entity-specific EXP-CUST-*, EXP-ACCT-*, EXP-XREF-*, EXP-TRAN-*, EXP-CARD-* fields |
| CVCUS01Y | FD CUSTOMER-OUTPUT (line 84) | CUSTOMER-RECORD (500 bytes): CUST-ID 9(9), name fields, address fields, CUST-SSN, CUST-DOB, CUST-EFT-ACCOUNT-ID, CUST-PRI-CARD-HOLDER-IND, CUST-FICO-CREDIT-SCORE |
| CVACT01Y | FD ACCOUNT-OUTPUT (line 89)  | ACCOUNT-RECORD (300 bytes): ACCT-ID 9(11), ACCT-ACTIVE-STATUS, balance/limit fields, dates, ACCT-GROUP-ID |
| CVACT03Y | FD XREF-OUTPUT (line 94)     | CARD-XREF-RECORD (50 bytes): XREF-CARD-NUM X(16), XREF-CUST-ID 9(9), XREF-ACCT-ID 9(11) |
| CVTRA05Y | FD TRANSACTION-OUTPUT (line 99) | TRAN-RECORD (350 bytes): TRAN-ID, type/cat codes, amounts, merchant fields, card number, timestamps |
| CVACT02Y | FD CARD-OUTPUT (line 104)    | CARD-RECORD (150 bytes): CARD-NUM X(16), CARD-ACCT-ID 9(11), CARD-CVV-CD, CARD-EMBOSSED-NAME, CARD-EXPIRAION-DATE, CARD-ACTIVE-STATUS |

### File Description Records

| FD Name             | DD Name   | Org       | RECLN | Access              |
|---------------------|-----------|-----------|-------|---------------------|
| EXPORT-INPUT        | EXPFILE   | KSDS      | 500F  | Sequential INPUT    |
| CUSTOMER-OUTPUT     | CUSTOUT   | Sequential | 500F  | Sequential OUTPUT  |
| ACCOUNT-OUTPUT      | ACCTOUT   | Sequential | 300F  | Sequential OUTPUT  |
| XREF-OUTPUT         | XREFOUT   | Sequential | 50F   | Sequential OUTPUT  |
| TRANSACTION-OUTPUT  | TRNXOUT   | Sequential | 350F  | Sequential OUTPUT  |
| CARD-OUTPUT         | CARDOUT   | Sequential | 150F  | Sequential OUTPUT  |
| ERROR-OUTPUT        | ERROUT    | Sequential | 132F  | Sequential OUTPUT  |

### Key Working Storage Variables

| Variable                         | PIC       | Purpose |
|----------------------------------|-----------|---------|
| EXPORT-RECORD (from CVEXPORT)    | 500 bytes | Target of READ INTO; EXPORT-REC-TYPE drives dispatch |
| WS-IMPORT-DATE                   | X(10)     | Current date formatted YYYY-MM-DD |
| WS-IMPORT-TIME                   | X(08)     | Current time formatted HH:MM:SS |
| WS-TOTAL-RECORDS-READ            | 9(09)     | Grand total records read from EXPFILE |
| WS-CUSTOMER-RECORDS-IMPORTED     | 9(09)     | Count of type 'C' records written |
| WS-ACCOUNT-RECORDS-IMPORTED      | 9(09)     | Count of type 'A' records written |
| WS-XREF-RECORDS-IMPORTED         | 9(09)     | Count of type 'X' records written |
| WS-TRAN-RECORDS-IMPORTED         | 9(09)     | Count of type 'T' records written |
| WS-CARD-RECORDS-IMPORTED         | 9(09)     | Count of type 'D' records written |
| WS-ERROR-RECORDS-WRITTEN         | 9(09)     | Count of error records written |
| WS-UNKNOWN-RECORD-TYPE-COUNT     | 9(09)     | Count of unrecognized type codes |
| WS-ERROR-RECORD                  | 132 bytes | ERR-TIMESTAMP X(26) + ERR-RECORD-TYPE X(1) + ERR-SEQUENCE 9(7) + ERR-MESSAGE X(50) + FILLER X(43) |
| WS-*-STATUS (7 fields)           | X(2) each | File status variables with 88-level conditions (OK='00', EOF='10') |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name  | File Object         | Org       | Access     | Mode     | Purpose |
|----------|---------------------|-----------|------------|----------|---------|
| EXPFILE  | EXPORT-INPUT        | KSDS      | Sequential | INPUT    | Consolidated multi-type export file from CBEXPORT |
| CUSTOUT  | CUSTOMER-OUTPUT     | Sequential | Sequential | OUTPUT   | Extracted customer records |
| ACCTOUT  | ACCOUNT-OUTPUT      | Sequential | Sequential | OUTPUT   | Extracted account records |
| XREFOUT  | XREF-OUTPUT         | Sequential | Sequential | OUTPUT   | Extracted cross-reference records |
| TRNXOUT  | TRANSACTION-OUTPUT  | Sequential | Sequential | OUTPUT   | Extracted transaction records |
| CARDOUT  | CARD-OUTPUT         | Sequential | Sequential | OUTPUT   | Extracted card records |
| ERROUT   | ERROR-OUTPUT        | Sequential | Sequential | OUTPUT   | 132-byte error records for unknown type codes |

---

## 6. Screen Interaction

None. Batch program.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| CEE3ABD        | Static CALL | LE forced abend on fatal error |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| Any file OPEN failure | DISPLAY error + status; PERFORM 9999-ABEND-PROGRAM |
| READ error (non-OK, non-EOF) | DISPLAY 'ERROR: Reading EXPORT-INPUT, Status:' + status; abend |
| CUSTOMER-OUTPUT WRITE error | DISPLAY error + WS-CUSTOMER-STATUS; abend |
| ACCOUNT-OUTPUT WRITE error  | DISPLAY error + WS-ACCOUNT-STATUS; abend |
| XREF-OUTPUT WRITE error     | DISPLAY error + WS-XREF-STATUS; abend |
| TRANSACTION-OUTPUT WRITE error | DISPLAY error + WS-TRANSACTION-STATUS; abend |
| CARD-OUTPUT WRITE error     | DISPLAY error + WS-CARD-STATUS; abend |
| ERROR-OUTPUT WRITE error    | DISPLAY 'ERROR: Writing error record, Status:' (no abend — program continues) |
| Unknown EXPORT-REC-TYPE     | Write to ERROUT; increment WS-UNKNOWN-RECORD-TYPE-COUNT; no abend |

---

## 9. Business Rules

1. **Record type dispatch**: EXPORT-REC-TYPE values C=Customer, A=Account, X=Cross-reference, T=Transaction, D=Card. Any other value triggers error record.
2. **Output files are sequential**: Unlike the input KSDS, all five entity output files are sequential (ORGANIZATION IS SEQUENTIAL). These are not VSAM KSDS files; they are flat sequential datasets suitable for downstream VSAM load jobs.
3. **Validation stub**: Paragraph 3000-VALIDATE-IMPORT contains only two DISPLAY statements. No data integrity, referential integrity, or checksum validation is implemented despite the program header commenting "validate data integrity using checksums."
4. **Error record format**: 132-byte pipe-delimited error record contains timestamp (26), record type (1), sequence number (7), and message (50). The ERROR-OUTPUT WRITE failure does not cause an abend — the program continues processing.
5. **Field mapping is 1-to-1**: Each entity mapping paragraph (2300–2650) performs INITIALIZE on the target record, then moves each EXP-* field from the export record to the corresponding entity record field. No transformation or conversion is applied.
6. **Symmetric with CBEXPORT**: The field mappings in CBIMPORT are the inverse of CBIMPORT's export mappings. The same 5 entity types are handled in both programs with matching field names.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| EXPFILE   | KSDS export file written by CBEXPORT; 500-byte fixed records; keyed by EXPORT-SEQUENCE-NUM |

### Outputs

| Destination | Record Layout  | Description |
|-------------|----------------|-------------|
| CUSTOUT     | CUSTOMER-RECORD (CVCUS01Y) | Sequential flat file of extracted customer records |
| ACCTOUT     | ACCOUNT-RECORD (CVACT01Y)  | Sequential flat file of extracted account records |
| XREFOUT     | CARD-XREF-RECORD (CVACT03Y) | Sequential flat file of extracted cross-reference records |
| TRNXOUT     | TRAN-RECORD (CVTRA05Y)     | Sequential flat file of extracted transaction records |
| CARDOUT     | CARD-RECORD (CVACT02Y)     | Sequential flat file of extracted card records |
| ERROUT      | WS-ERROR-RECORD (132 bytes) | Error records for unrecognized type codes |
| SYSOUT      | DISPLAY                     | Import start/end messages and statistics |

---

## 11. Key Variables and Their Purpose

| Variable              | Purpose |
|-----------------------|---------|
| EXPORT-RECORD         | 500-byte area populated by READ EXPORT-INPUT INTO; EXPORT-REC-TYPE field (offset 10 of CVEXPORT) drives type dispatch |
| WS-EXPORT-STATUS      | File status for EXPFILE; 88 WS-EXPORT-EOF='10', WS-EXPORT-OK='00' |
| WS-ERROR-RECORD       | 132-byte error record assembled for unknown type codes written to ERROUT |
| WS-TOTAL-RECORDS-READ | Grand total counter incremented once per record regardless of type |
| WS-UNKNOWN-RECORD-TYPE-COUNT | Tracks frequency of unrecognized type codes; reported in statistics |
