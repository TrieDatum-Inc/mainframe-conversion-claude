# Technical Specification: CBIMPORT

## 1. Executive Summary

CBIMPORT is a batch COBOL program in the CardDemo application that performs the inverse operation of CBEXPORT. It reads a multi-record-type consolidated export file (produced by CBEXPORT) and splits each record into its appropriate normalized output file based on the one-character record type code. It writes separate sequential output files for customers, accounts, cross-references, transactions, and cards. Unknown record types are routed to an error output file. The program is designed for branch migration data import.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBIMPORT.cbl` | COBOL Batch Program | Main program |
| `CVCUS01Y.cpy` | Copybook | Customer record layout (FD CUSTOMER-OUTPUT) |
| `CVACT01Y.cpy` | Copybook | Account record layout (FD ACCOUNT-OUTPUT) |
| `CVACT03Y.cpy` | Copybook | Card XREF record layout (FD XREF-OUTPUT) |
| `CVTRA05Y.cpy` | Copybook | Transaction record layout (FD TRANSACTION-OUTPUT) |
| `CVACT02Y.cpy` | Copybook | Card record layout (FD CARD-OUTPUT) |
| `CVEXPORT.cpy` | Copybook | Export record layout (`EXPORT-RECORD`) with REDEFINES sections |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBIMPORT` |
| Author | CARDDEMO TEAM |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Import Customer Data from Branch Migration Export |
| Source Version | CardDemo_v2.0-44-gb6e9c27-254, 2025-10-16 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field | Mode |
|---|---|---|---|---|---|
| `EXPORT-INPUT` | `EXPFILE` | INDEXED (KSDS) | Sequential | `EXPORT-SEQUENCE-NUM` | INPUT |
| `CUSTOMER-OUTPUT` | `CUSTOUT` | Sequential | Sequential | N/A | OUTPUT |
| `ACCOUNT-OUTPUT` | `ACCTOUT` | Sequential | Sequential | N/A | OUTPUT |
| `XREF-OUTPUT` | `XREFOUT` | Sequential | Sequential | N/A | OUTPUT |
| `TRANSACTION-OUTPUT` | `TRNXOUT` | Sequential | Sequential | N/A | OUTPUT |
| `CARD-OUTPUT` | `CARDOUT` | Sequential | Sequential | N/A | OUTPUT |
| `ERROR-OUTPUT` | `ERROUT` | Sequential | Sequential | N/A | OUTPUT |

**Key architectural difference from CBEXPORT:** The output files in CBIMPORT are all SEQUENTIAL (not INDEXED). They produce flat sequential files suitable for downstream VSAM load utilities or direct use in batch processing.

---

## 5. File Section — Record Layouts

### 5.1 EXPORT-INPUT (Input)
```
FD EXPORT-INPUT
   RECORDING MODE IS F
   RECORD CONTAINS 500 CHARACTERS.
01 EXPORT-INPUT-RECORD    PIC X(500).
```
Read INTO `EXPORT-RECORD` (from CVEXPORT).

### 5.2 Output Files (FDs with Copybook COPY)
| File | DD | Copybook | Record | Record Length |
|---|---|---|---|---|
| `CUSTOMER-OUTPUT` | `CUSTOUT` | `CVCUS01Y` | `CUSTOMER-RECORD` | 500 bytes |
| `ACCOUNT-OUTPUT` | `ACCTOUT` | `CVACT01Y` | `ACCOUNT-RECORD` | 300 bytes |
| `XREF-OUTPUT` | `XREFOUT` | `CVACT03Y` | `CARD-XREF-RECORD` | 50 bytes |
| `TRANSACTION-OUTPUT` | `TRNXOUT` | `CVTRA05Y` | `TRAN-RECORD` | 350 bytes |
| `CARD-OUTPUT` | `CARDOUT` | `CVACT02Y` | `CARD-RECORD` | 150 bytes |

### 5.3 ERROR-OUTPUT
```
FD ERROR-OUTPUT
   RECORDING MODE IS F
   RECORD CONTAINS 132 CHARACTERS.
01 ERROR-OUTPUT-RECORD    PIC X(132).
```
Written FROM `WS-ERROR-RECORD`.

---

## 6. Copybooks Referenced

| Copybook | Purpose |
|---|---|
| `CVCUS01Y` | Customer record (FD + `CUSTOMER-RECORD` working data) |
| `CVACT01Y` | Account record (FD + `ACCOUNT-RECORD`) |
| `CVACT03Y` | Card XREF record (FD + `CARD-XREF-RECORD`) |
| `CVTRA05Y` | Transaction record (FD + `TRAN-RECORD`) |
| `CVACT02Y` | Card record (FD + `CARD-RECORD`) |
| `CVEXPORT` | Export record with REDEFINES (shared with CBEXPORT) |

---

## 7. Working-Storage Data Structures

### 7.1 File Status Area
```
01 WS-FILE-STATUS-AREA.
   05 WS-EXPORT-STATUS      PIC X(02)  88 WS-EXPORT-EOF='10', WS-EXPORT-OK='00'
   05 WS-CUSTOMER-STATUS    PIC X(02)  88 WS-CUSTOMER-OK='00'
   05 WS-ACCOUNT-STATUS     PIC X(02)  88 WS-ACCOUNT-OK='00'
   05 WS-XREF-STATUS        PIC X(02)  88 WS-XREF-OK='00'
   05 WS-TRANSACTION-STATUS PIC X(02)  88 WS-TRANSACTION-OK='00'
   05 WS-CARD-STATUS        PIC X(02)  88 WS-CARD-OK='00'
   05 WS-ERROR-STATUS       PIC X(02)  88 WS-ERROR-OK='00'
```

### 7.2 Import Control Variables
```
01 WS-IMPORT-CONTROL.
   05 WS-IMPORT-DATE    PIC X(10)   [YYYY-MM-DD, built from FUNCTION CURRENT-DATE]
   05 WS-IMPORT-TIME    PIC X(08)   [HH:MM:SS]
```

### 7.3 Statistics Counters
```
01 WS-IMPORT-STATISTICS.
   05 WS-TOTAL-RECORDS-READ           PIC 9(09) VALUE 0
   05 WS-CUSTOMER-RECORDS-IMPORTED    PIC 9(09) VALUE 0
   05 WS-ACCOUNT-RECORDS-IMPORTED     PIC 9(09) VALUE 0
   05 WS-XREF-RECORDS-IMPORTED        PIC 9(09) VALUE 0
   05 WS-TRAN-RECORDS-IMPORTED        PIC 9(09) VALUE 0
   05 WS-CARD-RECORDS-IMPORTED        PIC 9(09) VALUE 0
   05 WS-ERROR-RECORDS-WRITTEN        PIC 9(09) VALUE 0
   05 WS-UNKNOWN-RECORD-TYPE-COUNT    PIC 9(09) VALUE 0
```

### 7.4 Error Record Layout
```
01 WS-ERROR-RECORD.
   05 ERR-TIMESTAMP    PIC X(26)
   05 FILLER           PIC X(01) VALUE '|'
   05 ERR-RECORD-TYPE  PIC X(01)
   05 FILLER           PIC X(01) VALUE '|'
   05 ERR-SEQUENCE     PIC 9(07)
   05 FILLER           PIC X(01) VALUE '|'
   05 ERR-MESSAGE      PIC X(50)
   05 FILLER           PIC X(43) VALUE SPACES
```
Total: 132 bytes, pipe-delimited.

---

## 8. Procedure Division — Program Flow

### 8.1 Main Control (lines 165–171)
```
0000-MAIN-PROCESSING:
    PERFORM 1000-INITIALIZE
    PERFORM 2000-PROCESS-EXPORT-FILE
    PERFORM 3000-VALIDATE-IMPORT
    PERFORM 4000-FINALIZE
    GOBACK
```

### 8.2 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `1000-INITIALIZE` | 174–193 | Builds WS-IMPORT-DATE and WS-IMPORT-TIME using FUNCTION CURRENT-DATE (substring extraction with hard-coded position/length references). Calls 1100-OPEN-FILES. DISPLAYs start message, import date and time. |
| `1100-OPEN-FILES` | 196–245 | Opens EXPORT-INPUT for INPUT; opens all 6 output files for OUTPUT. Abends on any open failure. |
| `2000-PROCESS-EXPORT-FILE` | 248–256 | Calls 2100-READ-EXPORT-RECORD then loops: ADD 1 to WS-TOTAL-RECORDS-READ, calls 2200-PROCESS-RECORD-BY-TYPE, reads next record. Repeats until WS-EXPORT-EOF. |
| `2100-READ-EXPORT-RECORD` | 259–267 | READ EXPORT-INPUT INTO EXPORT-RECORD. Abends if status is not OK and not EOF. |
| `2200-PROCESS-RECORD-BY-TYPE` | 270–285 | EVALUATE EXPORT-REC-TYPE: routes 'C' to 2300, 'A' to 2400, 'X' to 2500, 'T' to 2600, 'D' to 2650, WHEN OTHER to 2700. |
| `2300-PROCESS-CUSTOMER-RECORD` | 288–320 | INITIALIZE CUSTOMER-RECORD. Maps all EXP-CUST-* fields to CUST-* fields. WRITE CUSTOMER-RECORD to CUSTOMER-OUTPUT. Increments counter. Abends on write failure. |
| `2400-PROCESS-ACCOUNT-RECORD` | 322–349 | INITIALIZE ACCOUNT-RECORD. Maps all EXP-ACCT-* fields to ACCT-* fields. WRITE ACCOUNT-RECORD to ACCOUNT-OUTPUT. Increments counter. Abends on write failure. |
| `2500-PROCESS-XREF-RECORD` | 352–369 | INITIALIZE CARD-XREF-RECORD. Maps EXP-XREF-* to XREF-* fields. WRITE CARD-XREF-RECORD to XREF-OUTPUT. Increments counter. |
| `2600-PROCESS-TRAN-RECORD` | 371–399 | INITIALIZE TRAN-RECORD. Maps all EXP-TRAN-* to TRAN-* fields. WRITE TRAN-RECORD to TRANSACTION-OUTPUT. Increments counter. |
| `2650-PROCESS-CARD-RECORD` | 401–422 | INITIALIZE CARD-RECORD. Maps all EXP-CARD-* to CARD-* fields. WRITE CARD-RECORD to CARD-OUTPUT. Increments counter. |
| `2700-PROCESS-UNKNOWN-RECORD` | 425–434 | Increments WS-UNKNOWN-RECORD-TYPE-COUNT. Builds WS-ERROR-RECORD using FUNCTION CURRENT-DATE, EXPORT-REC-TYPE, EXPORT-SEQUENCE-NUM, and message 'Unknown record type encountered'. Calls 2750-WRITE-ERROR. |
| `2750-WRITE-ERROR` | 437–446 | WRITE ERROR-OUTPUT-RECORD FROM WS-ERROR-RECORD. If status not OK, DISPLAYs error (but does NOT abend). Increments WS-ERROR-RECORDS-WRITTEN. |
| `3000-VALIDATE-IMPORT` | 449–452 | Stub — DISPLAYs 'Import validation completed' and 'No validation errors detected'. No actual validation logic is implemented. |
| `4000-FINALIZE` | 455–478 | CLOSE all 7 files. DISPLAYs summary statistics: total records read, per-type counts, error count, unknown type count. |
| `9999-ABEND-PROGRAM` | 481–484 | `CALL 'CEE3ABD'` — simplified call, no USING. |

---

## 9. Record Type Routing — EVALUATE Logic

```
EVALUATE EXPORT-REC-TYPE
    WHEN 'C'   -> 2300-PROCESS-CUSTOMER-RECORD  -> CUSTOMER-OUTPUT
    WHEN 'A'   -> 2400-PROCESS-ACCOUNT-RECORD   -> ACCOUNT-OUTPUT
    WHEN 'X'   -> 2500-PROCESS-XREF-RECORD      -> XREF-OUTPUT
    WHEN 'T'   -> 2600-PROCESS-TRAN-RECORD       -> TRANSACTION-OUTPUT
    WHEN 'D'   -> 2650-PROCESS-CARD-RECORD       -> CARD-OUTPUT
    WHEN OTHER -> 2700-PROCESS-UNKNOWN-RECORD    -> ERROR-OUTPUT
```

---

## 10. Business Logic and Processing Rules

1. **Single-Pass Split:** The export file is read once, and each record is dispatched by type code. All output files are populated in a single sequential pass.

2. **Field Mapping (Export -> Target):** Each processing paragraph initializes the target record to spaces/zeros, then maps from the CVEXPORT REDEFINES sections to the standard copybook fields. The mapping is a direct field-by-field MOVE — no transformation, calculation, or validation of field values is performed.

3. **Error Handling for Unknown Types:** Unknown record types are not abend conditions — they produce error records in the pipe-delimited ERROR-OUTPUT file and increment WS-UNKNOWN-RECORD-TYPE-COUNT. The program continues processing. The error WRITE failure (if ERROR-OUTPUT write fails) is also non-fatal — only a DISPLAY is issued.

4. **Validation Stub:** `3000-VALIDATE-IMPORT` is declared but contains no validation logic. The comment 'No validation errors detected' is hardcoded, not the result of any check. Data integrity validation was planned but not implemented.

5. **Date/Time Construction (lines 178–188):** The initialization of WS-IMPORT-DATE and WS-IMPORT-TIME uses hard-coded substring positions against `FUNCTION CURRENT-DATE`. Note a discrepancy: the time field extracts positions 9:2 (hour), 11:2 (minute), and 13:2 (second) from CURRENT-DATE, but positions 9-14 of FUNCTION CURRENT-DATE represent time in HHMMSS format — the hour is at position 9, not the date. The date extraction (positions 1:4, 5:2, 7:2) is correct.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| Any file open failure | NOT WS-*-OK | DISPLAY error, 9999-ABEND-PROGRAM |
| Export read error (not EOF) | NOT WS-EXPORT-OK AND NOT WS-EXPORT-EOF | DISPLAY error, 9999-ABEND-PROGRAM |
| Customer write failure | NOT WS-CUSTOMER-OK | DISPLAY error, 9999-ABEND-PROGRAM |
| Account write failure | NOT WS-ACCOUNT-OK | DISPLAY error, 9999-ABEND-PROGRAM |
| XREF write failure | NOT WS-XREF-OK | DISPLAY error, 9999-ABEND-PROGRAM |
| Transaction write failure | NOT WS-TRANSACTION-OK | DISPLAY error, 9999-ABEND-PROGRAM |
| Card write failure | NOT WS-CARD-OK | DISPLAY error, 9999-ABEND-PROGRAM |
| Error record write failure | NOT WS-ERROR-OK | DISPLAY only — no abend |
| Unknown record type | EXPORT-REC-TYPE not in {'C','A','X','T','D'} | Route to error file, continue |

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion (no unknown types) | 0 (implicit GOBACK) |
| Normal completion with unknown types | 0 (GOBACK, error records written to ERROUT) |
| Fatal I/O error | Abend via CEE3ABD |

---

## 13. Data Flow Diagram

```
EXPFILE (INDEXED, 500-byte) -->  2200-PROCESS-RECORD-BY-TYPE
                                     |
                    +----------------+-------------------+
                    |         |         |        |       |
                    v         v         v        v       v
                CUSTOUT   ACCTOUT   XREFOUT  TRNXOUT  CARDOUT
               (500-byte) (300-byte) (50-byte) (350-byte) (150-byte)
                    |
                  WHEN OTHER
                    v
                 ERROUT (132-byte, pipe-delimited error records)
```

---

## 14. Observations

- The output files (CUSTOUT, ACCTOUT, etc.) are SEQUENTIAL, not INDEXED. They cannot be directly used as VSAM KSDS replacements for the CardDemo system without a subsequent IDCAMS REPRO or VSAM load step.
- The `3000-VALIDATE-IMPORT` stub is a significant gap. No referential integrity checks (e.g., does each XREF record's ACCT-ID correspond to an exported account?) are performed.
- The error write in `2750-WRITE-ERROR` does not abend on failure, allowing the import to complete even if the error file is unavailable. This means unknown records may be silently lost if ERROUT cannot be written.
- The CBEXPORT/CBIMPORT pair uses COMP and COMP-3 fields within the 460-byte EXPORT-RECORD-DATA payload. This creates a binary dependency — the export file is not a plain text/character format.
