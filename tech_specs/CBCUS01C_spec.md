# Technical Specification: CBCUS01C

## 1. Executive Summary

CBCUS01C is a batch COBOL program in the CardDemo application that sequentially reads the customer master VSAM KSDS file and displays each customer record to SYSOUT. It is a diagnostic/reporting utility with no output file. Its purpose is to verify or audit the customer data.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBCUS01C.cbl` | COBOL Batch Program | Main program |
| `CVCUS01Y.cpy` | Copybook | Customer record layout (`CUSTOMER-RECORD`) |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBCUS01C` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Read and print customer data file |
| Source Version | CardDemo_v2.0-25-gdb72e6b-235, 2025-04-29 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field |
|---|---|---|---|---|
| `CUSTFILE-FILE` | `CUSTFILE` | INDEXED (KSDS) | Sequential | `FD-CUST-ID` PIC 9(09) |

---

## 5. File Section — Record Layout

### 5.1 CUSTFILE-FILE (Input)
Defined at lines 37–40:
```
01 FD-CUSTFILE-REC.
   05 FD-CUST-ID      PIC 9(09)
   05 FD-CUST-DATA    PIC X(491)
```
Total record length: 500 bytes. Read INTO `CUSTOMER-RECORD` (from copybook CVCUS01Y).

---

## 6. Copybooks Referenced

| Copybook | Location in Source | Purpose |
|---|---|---|
| `CVCUS01Y` | Line 45 (WORKING-STORAGE) | Defines `CUSTOMER-RECORD` (500-byte customer layout) |

### CVCUS01Y — CUSTOMER-RECORD Layout
```
01 CUSTOMER-RECORD.
   05 CUST-ID                  PIC 9(09)
   05 CUST-FIRST-NAME          PIC X(25)
   05 CUST-MIDDLE-NAME         PIC X(25)
   05 CUST-LAST-NAME           PIC X(25)
   05 CUST-ADDR-LINE-1         PIC X(50)
   05 CUST-ADDR-LINE-2         PIC X(50)
   05 CUST-ADDR-LINE-3         PIC X(50)
   05 CUST-ADDR-STATE-CD       PIC X(02)
   05 CUST-ADDR-COUNTRY-CD     PIC X(03)
   05 CUST-ADDR-ZIP            PIC X(10)
   05 CUST-PHONE-NUM-1         PIC X(15)
   05 CUST-PHONE-NUM-2         PIC X(15)
   05 CUST-SSN                 PIC 9(09)
   05 CUST-GOVT-ISSUED-ID      PIC X(20)
   05 CUST-DOB-YYYY-MM-DD      PIC X(10)
   05 CUST-EFT-ACCOUNT-ID      PIC X(10)
   05 CUST-PRI-CARD-HOLDER-IND PIC X(01)
   05 CUST-FICO-CREDIT-SCORE   PIC 9(03)
   05 FILLER                   PIC X(168)
```
Total record length: 500 bytes.

---

## 7. Working-Storage Data Structures

| Field | PIC | Purpose |
|---|---|---|
| `CUSTFILE-STATUS` | 2 x PIC X | VSAM file status for CUSTFILE |
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
DISPLAY 'START OF EXECUTION OF PROGRAM CBCUS01C'
PERFORM 0000-CUSTFILE-OPEN

PERFORM UNTIL END-OF-FILE = 'Y'
    IF END-OF-FILE = 'N'
        PERFORM 1000-CUSTFILE-GET-NEXT
        IF END-OF-FILE = 'N'
            DISPLAY CUSTOMER-RECORD
        END-IF
    END-IF
END-PERFORM

PERFORM 9000-CUSTFILE-CLOSE
DISPLAY 'END OF EXECUTION OF PROGRAM CBCUS01C'
GOBACK
```

### 8.2 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `0000-CUSTFILE-OPEN` | 118–134 | Opens CUSTFILE-FILE for INPUT. Sets APPL-RESULT=8 before open; sets to 0 on success, 12 on failure. Abends via Z-DISPLAY-IO-STATUS and Z-ABEND-PROGRAM on failure. |
| `1000-CUSTFILE-GET-NEXT` | 92–116 | Reads next customer record sequentially into CUSTOMER-RECORD. On status '00': DISPLAY CUSTOMER-RECORD (note: inner DISPLAY at line 96, plus outer DISPLAY at line 78 — double display per record). On status '10': sets APPL-RESULT=16. On other: sets APPL-RESULT=12 and abends. |
| `9000-CUSTFILE-CLOSE` | 136–152 | Closes CUSTFILE-FILE. Abends on failure. |
| `Z-ABEND-PROGRAM` | 154–158 | Calls `CEE3ABD` with ABCODE=999, TIMING=0. |
| `Z-DISPLAY-IO-STATUS` | 161–174 | Formats and displays the 2-byte file status as a 4-digit value. |

**Note on naming:** The abend and I/O-status paragraphs in CBCUS01C use the `Z-` prefix (`Z-ABEND-PROGRAM`, `Z-DISPLAY-IO-STATUS`) rather than the `9999-`/`9910-` prefix used in the CBACT0xC series. The logic is functionally identical.

---

## 9. External Program Calls

| Called Program | Mechanism | Purpose |
|---|---|---|
| `CEE3ABD` | CALL ... USING ABCODE, TIMING | LE abnormal termination. Called in Z-ABEND-PROGRAM (line 158). |

---

## 10. Business Logic and Processing Rules

1. **Sequential Read of CUSTFILE:** The program reads CUSTFILE-FILE from first record to EOF. No filtering, selection, or transformation is applied.

2. **Double DISPLAY per Record:** Each customer record is displayed twice to SYSOUT:
   - First at line 96 inside `1000-CUSTFILE-GET-NEXT` on successful read
   - Second at line 78 in the main loop
   This mirrors the same defect observed in CBACT03C.

3. **Diagnostic Audit Utility:** The program serves only to confirm the customer file is readable and to present its contents for review. It makes no updates.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| File open failure | Status != '00' | DISPLAY 'ERROR OPENING CUSTFILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM |
| Read error (not EOF) | APPL-RESULT = 12 | DISPLAY 'ERROR READING CUSTOMER FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM |
| File close failure | Status != '00' | DISPLAY 'ERROR CLOSING CUSTOMER FILE', abend |

**Abend mechanism:** `CEE3ABD` with ABCODE=999, TIMING=0. Produces user abend U0999.

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion | 0 (implicit GOBACK) |
| Any file I/O error | U0999 abend via CEE3ABD |

---

## 13. Customer Record — Field Reference

| Field | PIC | Notes |
|---|---|---|
| CUST-ID | PIC 9(09) | Primary key — 9-digit customer identifier |
| CUST-FIRST-NAME | PIC X(25) | First name |
| CUST-MIDDLE-NAME | PIC X(25) | Middle name |
| CUST-LAST-NAME | PIC X(25) | Last name |
| CUST-ADDR-LINE-1/2/3 | PIC X(50) each | Three-line street address |
| CUST-ADDR-STATE-CD | PIC X(02) | 2-letter state code |
| CUST-ADDR-COUNTRY-CD | PIC X(03) | 3-letter country code |
| CUST-ADDR-ZIP | PIC X(10) | ZIP/postal code |
| CUST-PHONE-NUM-1/2 | PIC X(15) each | Two phone numbers |
| CUST-SSN | PIC 9(09) | Social Security Number |
| CUST-GOVT-ISSUED-ID | PIC X(20) | Government-issued ID |
| CUST-DOB-YYYY-MM-DD | PIC X(10) | Date of birth in YYYY-MM-DD format |
| CUST-EFT-ACCOUNT-ID | PIC X(10) | EFT bank account identifier |
| CUST-PRI-CARD-HOLDER-IND | PIC X(01) | Primary cardholder indicator |
| CUST-FICO-CREDIT-SCORE | PIC 9(03) | FICO credit score (3-digit) |
| FILLER | PIC X(168) | Reserved |

---

## 14. Observations

- Structurally identical to CBACT02C (reads CARDFILE) and CBACT03C (reads XREFFILE). All three are diagnostic read-and-display programs.
- The double-DISPLAY defect is present here as in CBACT03C. The inner DISPLAY at line 96 should be removed or commented out for clean output.
- CUST-SSN (PIC 9(09)) contains sensitive PII data. This DISPLAY-based program would write raw SSN values to the job log, which is a security consideration in any cloud migration context.
- CUST-FICO-CREDIT-SCORE is also PII. The DISPLAY of CUSTOMER-RECORD exposes all fields without masking.
