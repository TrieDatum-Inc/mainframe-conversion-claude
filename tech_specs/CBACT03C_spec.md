# Technical Specification: CBACT03C

## 1. Executive Summary

CBACT03C is a batch COBOL program in the CardDemo application that sequentially reads the card cross-reference (XREF) VSAM KSDS file and displays each record to SYSOUT. It is a diagnostic/reporting utility with no output file. Its purpose is to verify or audit the account-to-card cross-reference data.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBACT03C.cbl` | COBOL Batch Program | Main program |
| `CVACT03Y.cpy` | Copybook | Card cross-reference record layout (`CARD-XREF-RECORD`) |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBACT03C` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Read and print account cross-reference data file |
| Source Version | CardDemo_v2.0-25-gdb72e6b-235, 2025-04-29 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field |
|---|---|---|---|---|
| `XREFFILE-FILE` | `XREFFILE` | INDEXED (KSDS) | Sequential | `FD-XREF-CARD-NUM` PIC X(16) |

---

## 5. File Section — Record Layout

### 5.1 XREFFILE-FILE (Input)
Defined at lines 37–40:
```
01 FD-XREFFILE-REC.
   05 FD-XREF-CARD-NUM    PIC X(16)
   05 FD-XREF-DATA        PIC X(34)
```
Total record length: 50 bytes. Read INTO `CARD-XREF-RECORD` (from copybook CVACT03Y).

---

## 6. Copybooks Referenced

| Copybook | Location in Source | Purpose |
|---|---|---|
| `CVACT03Y` | Line 45 (WORKING-STORAGE) | Defines `CARD-XREF-RECORD` (50-byte cross-reference layout) |

### CVACT03Y — CARD-XREF-RECORD Layout
```
01 CARD-XREF-RECORD.
   05 XREF-CARD-NUM    PIC X(16)
   05 XREF-CUST-ID     PIC 9(09)
   05 XREF-ACCT-ID     PIC 9(11)
   05 FILLER           PIC X(14)
```
Total record length: 50 bytes.

The cross-reference file is the linking entity between card numbers, customer IDs, and account IDs in the CardDemo system.

---

## 7. Working-Storage Data Structures

| Field | PIC | Purpose |
|---|---|---|
| `XREFFILE-STATUS` | 2 x PIC X | VSAM file status for XREFFILE |
| `IO-STATUS` | 2 x PIC X | Scratch area for I/O error display |
| `TWO-BYTES-BINARY` / `TWO-BYTES-ALPHA` | PIC 9(4) BINARY / REDEFINES | Binary/character overlay for extended file status |
| `IO-STATUS-04` | PIC 9 + PIC 999 | Formatted 4-digit I/O status for display |
| `APPL-RESULT` | PIC S9(9) COMP | Internal result code; 88 levels: `APPL-AOK` (0), `APPL-EOF` (16) |
| `END-OF-FILE` | PIC X(01) VALUE 'N' | EOF flag; set to 'Y' on file status '10' |
| `ABCODE` | PIC S9(9) BINARY | Abend code (999) passed to CEE3ABD |
| `TIMING` | PIC S9(9) BINARY | Timing parameter (0) passed to CEE3ABD |

---

## 8. Procedure Division — Program Flow

### 8.1 Main Control (lines 70–87)
```
DISPLAY 'START OF EXECUTION OF PROGRAM CBACT03C'
PERFORM 0000-XREFFILE-OPEN

PERFORM UNTIL END-OF-FILE = 'Y'
    IF END-OF-FILE = 'N'
        PERFORM 1000-XREFFILE-GET-NEXT
        IF END-OF-FILE = 'N'
            DISPLAY CARD-XREF-RECORD
        END-IF
    END-IF
END-PERFORM

PERFORM 9000-XREFFILE-CLOSE
DISPLAY 'END OF EXECUTION OF PROGRAM CBACT03C'
GOBACK
```

### 8.2 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `0000-XREFFILE-OPEN` | 118–134 | Opens XREFFILE-FILE for INPUT. Sets APPL-RESULT=8 before open; sets to 0 on success, 12 on failure. Abends on failure. |
| `1000-XREFFILE-GET-NEXT` | 92–116 | Reads next XREF record sequentially into CARD-XREF-RECORD. On status '00': DISPLAY CARD-XREF-RECORD (note: this is a second display — the main loop also displays at line 78; the record is displayed twice per iteration). On status '10': sets APPL-RESULT=16. On other: sets APPL-RESULT=12. EOF sets END-OF-FILE='Y'; error abends. |
| `9000-XREFFILE-CLOSE` | 136–152 | Closes XREFFILE-FILE. Abends on failure. |
| `9999-ABEND-PROGRAM` | 154–158 | Calls `CEE3ABD` with ABCODE=999, TIMING=0. |
| `9910-DISPLAY-IO-STATUS` | 161–174 | Formats and displays the 2-byte file status as a 4-digit value. |

---

## 9. External Program Calls

| Called Program | Mechanism | Purpose |
|---|---|---|
| `CEE3ABD` | CALL ... USING ABCODE, TIMING | LE abnormal termination. Called in 9999-ABEND-PROGRAM (line 158). |

---

## 10. Business Logic and Processing Rules

1. **Sequential Read of XREFFILE:** The program reads XREFFILE-FILE from first record to EOF without any filtering.

2. **Double DISPLAY per Record:** Due to a code anomaly, each XREF record is displayed twice per iteration:
   - First at line 96 inside `1000-XREFFILE-GET-NEXT` on successful read
   - Second at line 78 in the main loop after `1000-XREFFILE-GET-NEXT` returns and `END-OF-FILE = 'N'` check passes
   This is a defect — each record will appear twice in SYSOUT output.

3. **Cross-Reference Data Audit:** The XREF file links CARD-NUM to CUST-ID and ACCT-ID. This program verifies that linkage data is present and readable.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| File open failure | Status != '00' | DISPLAY error, 9910-DISPLAY-IO-STATUS, 9999-ABEND-PROGRAM |
| Read error (not EOF) | APPL-RESULT = 12 | DISPLAY 'ERROR READING XREFFILE', abend |
| File close failure | Status != '00' | DISPLAY error, abend |

**Abend mechanism:** `CEE3ABD` with ABCODE=999. Produces user abend U0999.

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion | 0 (implicit GOBACK) |
| Any file I/O error | U0999 abend via CEE3ABD |

---

## 13. Observations

- **Double DISPLAY defect:** The DISPLAY at line 96 (`DISPLAY CARD-XREF-RECORD` inside `1000-XREFFILE-GET-NEXT`) combined with the DISPLAY at line 78 in the main loop causes each record to be printed twice to SYSOUT. In CBACT02C, the inner DISPLAY is commented out — this suggests CBACT03C was derived from CBACT02C without removing the inner DISPLAY.
- No record count is tracked. No end-of-run summary is produced.
- This program is a read-only diagnostic utility. It makes no updates to any file.
- The XREF record structure it reads is used by many other programs (CBACT04C, CBTRN01C, CBTRN02C, CBTRN03C, CBSTM03A, CBSTM03B) as the key linkage between cards, customers, and accounts.
