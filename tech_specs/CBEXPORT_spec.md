# Technical Specification: CBEXPORT

## 1. Executive Summary

CBEXPORT is a batch COBOL program in the CardDemo application that exports customer profile data for branch migration. It reads all five core CardDemo VSAM KSDS files — customer, account, cross-reference, transaction, and card — sequentially, and writes every record as a type-tagged, fixed-length 500-byte record into a single consolidated INDEXED export file. Five distinct record types are produced, each identified by a one-character type code ('C', 'A', 'X', 'T', 'D'). The program generates run statistics and a final summary report via DISPLAY. CBIMPORT is the corresponding inverse program.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBEXPORT.cbl` | COBOL Batch Program | Main program |
| `CVCUS01Y.cpy` | Copybook | Customer record layout (used in FD CUSTOMER-INPUT) |
| `CVACT01Y.cpy` | Copybook | Account record layout (used in FD ACCOUNT-INPUT) |
| `CVACT03Y.cpy` | Copybook | Card XREF record layout (used in FD XREF-INPUT) |
| `CVTRA05Y.cpy` | Copybook | Transaction record layout (used in FD TRANSACTION-INPUT) |
| `CVACT02Y.cpy` | Copybook | Card record layout (used in FD CARD-INPUT) |
| `CVEXPORT.cpy` | Copybook | Export record layout (`EXPORT-RECORD`) with REDEFINES sections |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBEXPORT` |
| Author | CARDDEMO TEAM |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Export Customer Data for Branch Migration |
| Source Version | CardDemo_v2.0-44-gb6e9c27-254, 2025-10-16 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field | Mode |
|---|---|---|---|---|---|
| `CUSTOMER-INPUT` | `CUSTFILE` | INDEXED (KSDS) | Sequential | `CUST-ID` | INPUT |
| `ACCOUNT-INPUT` | `ACCTFILE` | INDEXED (KSDS) | Sequential | `ACCT-ID` | INPUT |
| `XREF-INPUT` | `XREFFILE` | INDEXED (KSDS) | Sequential | `XREF-CARD-NUM` | INPUT |
| `TRANSACTION-INPUT` | `TRANSACT` | INDEXED (KSDS) | Sequential | `TRAN-ID` | INPUT |
| `CARD-INPUT` | `CARDFILE` | INDEXED (KSDS) | Sequential | `CARD-NUM` | INPUT |
| `EXPORT-OUTPUT` | `EXPFILE` | INDEXED (KSDS) | Sequential | `EXPORT-SEQUENCE-NUM` | OUTPUT |

---

## 5. File Section — Record Layouts

All input FD entries use `COPY` statements to incorporate the standard record layouts from copybooks. The export output uses a fixed 500-byte record.

### 5.1 Input Files (FDs with Copybook COPY)
| File | Copybook | Record | Length |
|---|---|---|---|
| `CUSTOMER-INPUT` | `CVCUS01Y` | `CUSTOMER-RECORD` | 500 bytes |
| `ACCOUNT-INPUT` | `CVACT01Y` | `ACCOUNT-RECORD` | 300 bytes |
| `XREF-INPUT` | `CVACT03Y` | `CARD-XREF-RECORD` | 50 bytes |
| `TRANSACTION-INPUT` | `CVTRA05Y` | `TRAN-RECORD` | 350 bytes |
| `CARD-INPUT` | `CVACT02Y` | `CARD-RECORD` | 150 bytes |

### 5.2 EXPORT-OUTPUT
```
FD EXPORT-OUTPUT
   RECORDING MODE IS F
   RECORD CONTAINS 500 CHARACTERS.
01 EXPORT-OUTPUT-RECORD    PIC X(500).
```
Records are written FROM `EXPORT-RECORD` (from copybook CVEXPORT).

---

## 6. Copybooks Referenced

| Copybook | Purpose |
|---|---|
| `CVCUS01Y` | Customer record (FD + WORKING-STORAGE reference via `CUSTOMER-RECORD`) |
| `CVACT01Y` | Account record (FD + `ACCOUNT-RECORD`) |
| `CVACT03Y` | Card XREF record (FD + `CARD-XREF-RECORD`) |
| `CVTRA05Y` | Transaction record (FD + `TRAN-RECORD`) |
| `CVACT02Y` | Card record (FD + `CARD-RECORD`) |
| `CVEXPORT` | Export record layout with all record-type REDEFINES sections |

### CVEXPORT — EXPORT-RECORD Layout (500 bytes)
```
01 EXPORT-RECORD.
   05 EXPORT-REC-TYPE              PIC X(1)     [Record type discriminator]
   05 EXPORT-TIMESTAMP             PIC X(26)    [Run timestamp]
   05 EXPORT-TIMESTAMP-R REDEFINES EXPORT-TIMESTAMP.
      10 EXPORT-DATE               PIC X(10)
      10 EXPORT-DATE-TIME-SEP      PIC X(1)
      10 EXPORT-TIME               PIC X(15)
   05 EXPORT-SEQUENCE-NUM          PIC 9(9) COMP  [Primary key, auto-incremented]
   05 EXPORT-BRANCH-ID             PIC X(4)     [Hardcoded '0001']
   05 EXPORT-REGION-CODE           PIC X(5)     [Hardcoded 'NORTH']
   05 EXPORT-RECORD-DATA           PIC X(460)   [Payload, varies by type]
```

The `EXPORT-RECORD-DATA` (460 bytes) is REDEFINEd five ways:
- `EXPORT-CUSTOMER-DATA` — maps EXP-CUST-* fields
- `EXPORT-ACCOUNT-DATA` — maps EXP-ACCT-* fields
- `EXPORT-TRANSACTION-DATA` — maps EXP-TRAN-* fields
- `EXPORT-CARD-XREF-DATA` — maps EXP-XREF-* fields
- `EXPORT-CARD-DATA` — maps EXP-CARD-* fields

Notable: Several export fields use COMP or COMP-3 storage (e.g., `EXP-CUST-ID` 9(09) COMP, `EXP-ACCT-CURR-BAL` S9(10)V99 COMP-3, `EXP-TRAN-AMT` S9(09)V99 COMP-3).

---

## 7. Working-Storage Data Structures

### 7.1 File Status Area
```
01 WS-FILE-STATUS-AREA.
   05 WS-CUSTOMER-STATUS    PIC X(02)  88 WS-CUSTOMER-EOF='10', WS-CUSTOMER-OK='00'
   05 WS-ACCOUNT-STATUS     PIC X(02)  88 WS-ACCOUNT-EOF='10', WS-ACCOUNT-OK='00'
   05 WS-XREF-STATUS        PIC X(02)  88 WS-XREF-EOF='10', WS-XREF-OK='00'
   05 WS-TRANSACTION-STATUS PIC X(02)  88 WS-TRANSACTION-EOF='10', WS-TRANSACTION-OK='00'
   05 WS-CARD-STATUS        PIC X(02)  88 WS-CARD-EOF='10', WS-CARD-OK='00'
   05 WS-EXPORT-STATUS      PIC X(02)  88 WS-EXPORT-OK='00'
```

### 7.2 Export Control Variables
```
01 WS-EXPORT-CONTROL.
   05 WS-EXPORT-DATE          PIC X(10)   [YYYY-MM-DD]
   05 WS-EXPORT-TIME          PIC X(08)   [HH:MM:SS]
   05 WS-FORMATTED-TIMESTAMP  PIC X(26)   [YYYY-MM-DD HH:MM:SS.00]
   05 WS-SEQUENCE-COUNTER     PIC 9(09) VALUE 0  [Auto-incremented key]
```

### 7.3 Statistics Counters
```
01 WS-EXPORT-STATISTICS.
   05 WS-CUSTOMER-RECORDS-EXPORTED    PIC 9(09) VALUE 0
   05 WS-ACCOUNT-RECORDS-EXPORTED     PIC 9(09) VALUE 0
   05 WS-XREF-RECORDS-EXPORTED        PIC 9(09) VALUE 0
   05 WS-TRAN-RECORDS-EXPORTED        PIC 9(09) VALUE 0
   05 WS-CARD-RECORDS-EXPORTED        PIC 9(09) VALUE 0
   05 WS-TOTAL-RECORDS-EXPORTED       PIC 9(09) VALUE 0
```

### 7.4 Timestamp Fields
```
01 WS-TIMESTAMP-FIELDS.
   05 WS-CURRENT-DATE.
      10 WS-CURR-YEAR     PIC 9(04)
      10 WS-CURR-MONTH    PIC 9(02)
      10 WS-CURR-DAY      PIC 9(02)
   05 WS-CURRENT-TIME.
      10 WS-CURR-HOUR     PIC 9(02)
      10 WS-CURR-MINUTE   PIC 9(02)
      10 WS-CURR-SECOND   PIC 9(02)
      10 WS-CURR-HUNDREDTH PIC 9(02)
```

---

## 8. Procedure Division — Program Flow

### 8.1 Main Control (lines 149–158)
```
0000-MAIN-PROCESSING:
    PERFORM 1000-INITIALIZE
    PERFORM 2000-EXPORT-CUSTOMERS
    PERFORM 3000-EXPORT-ACCOUNTS
    PERFORM 4000-EXPORT-XREFS
    PERFORM 5000-EXPORT-TRANSACTIONS
    PERFORM 5500-EXPORT-CARDS
    PERFORM 6000-FINALIZE
    GOBACK
```
All five entity types are exported in separate sequential passes, each reading its respective file from beginning to end.

### 8.2 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `1000-INITIALIZE` | 161–169 | Calls 1050-GENERATE-TIMESTAMP and 1100-OPEN-FILES. DISPLAYs start message and export date/time. |
| `1050-GENERATE-TIMESTAMP` | 172–195 | ACCEPT DATE YYYYMMDD and TIME into WS-TIMESTAMP-FIELDS. Formats WS-EXPORT-DATE (YYYY-MM-DD), WS-EXPORT-TIME (HH:MM:SS), and WS-FORMATTED-TIMESTAMP (YYYY-MM-DD HH:MM:SS.00). |
| `1100-OPEN-FILES` | 198–240 | Opens all 5 input files for INPUT and EXPORT-OUTPUT for OUTPUT. Calls 9999-ABEND-PROGRAM on any open failure (uses 88-level condition names WS-*-OK, no intermediate APPL-RESULT pattern). |
| `2000-EXPORT-CUSTOMERS` | 243–255 | Reads CUSTOMER-INPUT until EOF; for each record calls 2200-CREATE-CUSTOMER-EXP-REC. Reports count. |
| `2100-READ-CUSTOMER-RECORD` | 258–266 | READ CUSTOMER-INPUT. Abends if status is not OK and not EOF. |
| `2200-CREATE-CUSTOMER-EXP-REC` | 269–310 | INITIALIZE EXPORT-RECORD. Sets EXPORT-REC-TYPE='C', EXPORT-TIMESTAMP, increments WS-SEQUENCE-COUNTER. Sets EXPORT-BRANCH-ID='0001', EXPORT-REGION-CODE='NORTH'. Maps all CUST-* fields to EXP-CUST-* fields. WRITEs to EXPORT-OUTPUT. Increments counters. |
| `3000-EXPORT-ACCOUNTS` | 312–324 | Reads ACCOUNT-INPUT until EOF; for each record calls 3200-CREATE-ACCOUNT-EXP-REC. |
| `3200-CREATE-ACCOUNT-EXP-REC` | 338–373 | Sets EXPORT-REC-TYPE='A'. Maps all ACCT-* fields to EXP-ACCT-* fields. Writes and counts. |
| `4000-EXPORT-XREFS` | 376–388 | Reads XREF-INPUT until EOF; for each record calls 4200-CREATE-XREF-EXPORT-RECORD. |
| `4200-CREATE-XREF-EXPORT-RECORD` | 402–428 | Sets EXPORT-REC-TYPE='X'. Maps XREF-CARD-NUM, XREF-CUST-ID, XREF-ACCT-ID to EXP-XREF-* fields. Writes and counts. |
| `5000-EXPORT-TRANSACTIONS` | 431–443 | Reads TRANSACTION-INPUT until EOF; for each record calls 5200-CREATE-TRAN-EXP-REC. |
| `5200-CREATE-TRAN-EXP-REC` | 457–493 | Sets EXPORT-REC-TYPE='T'. Maps all TRAN-* fields to EXP-TRAN-* fields. Writes and counts. |
| `5500-EXPORT-CARDS` | 496–508 | Reads CARD-INPUT until EOF; for each record calls 5700-CREATE-CARD-EXPORT-RECORD. |
| `5700-CREATE-CARD-EXPORT-RECORD` | 522–551 | Sets EXPORT-REC-TYPE='D'. Maps all CARD-* fields to EXP-CARD-* fields. Writes and counts. |
| `6000-FINALIZE` | 554–573 | CLOSE all 6 files. DISPLAYs summary statistics: count per entity type and total. |
| `9999-ABEND-PROGRAM` | 576–579 | Calls `CEE3ABD` (no arguments — simplified call syntax). |

---

## 9. Export Record Type Codes

| Code | Entity | Populated REDEFINES Section |
|---|---|---|
| `'C'` | Customer | `EXPORT-CUSTOMER-DATA` |
| `'A'` | Account | `EXPORT-ACCOUNT-DATA` |
| `'X'` | Card Cross-Reference | `EXPORT-CARD-XREF-DATA` |
| `'T'` | Transaction | `EXPORT-TRANSACTION-DATA` |
| `'D'` | Card (Debit/Credit card) | `EXPORT-CARD-DATA` |

---

## 10. Business Logic and Processing Rules

1. **Sequential Full Export:** Every record from every source file is exported without filtering. The export is a complete snapshot.

2. **Sequence Number as Primary Key:** `EXPORT-SEQUENCE-NUM` (PIC 9(9) COMP) is used as the primary key for the INDEXED output file. It is auto-incremented (starting at 1) across all record types, ensuring uniqueness. This allows CBIMPORT to read the file sequentially by key order.

3. **Fixed Metadata per Record:** Every export record carries:
   - `EXPORT-BRANCH-ID` = hardcoded '0001'
   - `EXPORT-REGION-CODE` = hardcoded 'NORTH'
   - `EXPORT-TIMESTAMP` = formatted run timestamp (not per-record timestamp)
   
   These values are hardcoded constants, not configurable. Any migration to a different branch or region requires code change.

4. **Processing Order:** Records are exported in entity order: Customer -> Account -> XREF -> Transaction -> Card. Within each entity type, records appear in natural KSDS key sequence.

5. **COMP/COMP-3 in Export File:** The CVEXPORT copybook defines several numeric fields with COMP or COMP-3 usage. This means the export file is not human-readable — it contains binary data for numeric fields. CBIMPORT must use the same CVEXPORT copybook to correctly interpret these packed fields.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| Any file open failure | `NOT WS-*-OK` condition | DISPLAY error message, 9999-ABEND-PROGRAM |
| Read error (not EOF) | `NOT WS-*-OK AND NOT WS-*-EOF` | DISPLAY error, 9999-ABEND-PROGRAM |
| Write error | `NOT WS-EXPORT-OK` | DISPLAY error, 9999-ABEND-PROGRAM |

**Abend mechanism:** `CALL 'CEE3ABD'` without USING clause — this is a simplified invocation that produces a runtime abend.

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion | 0 (implicit GOBACK) |
| Any I/O error | Abend via CEE3ABD |

---

## 13. Data Flow Diagram

```
CUSTFILE  -----> CUSTOMER records ('C') ---+
ACCTFILE  -----> ACCOUNT records ('A')  ---|
XREFFILE  -----> XREF records ('X')     ---+--> EXPORT-OUTPUT (EXPFILE)
TRANSACT  -----> TRANSACTION records ('T') |    [INDEXED, 500-byte fixed]
CARDFILE  -----> CARD records ('D')     ---+
```

---

## 14. Observations

- The `EXPORT-SEQUENCE-NUM` field is declared as `PIC 9(9) COMP` in CVEXPORT. Since it is the primary key of an INDEXED file, its binary storage format requires that any program reading EXPFILE must also use the CVEXPORT copybook or know that this field is COMP-encoded.
- The hardcoded branch/region values ('0001', 'NORTH') limit reusability for other migration scenarios without source changes.
- No validation of input data is performed — the program assumes all source records are valid.
- CBIMPORT (the inverse) reads the same EXPFILE using CVEXPORT and routes records by type code. The pair constitutes a complete extract-load pipeline for branch migration.
