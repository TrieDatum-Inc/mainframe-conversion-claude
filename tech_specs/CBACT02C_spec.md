# Technical Specification: CBACT02C

## 1. Executive Summary

CBACT02C is a batch COBOL program in the CardDemo application that sequentially reads the card master VSAM KSDS file and displays each card record to SYSOUT. It is a diagnostic/reporting utility with no output file — its sole function is to read and display card data for verification or auditing purposes.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBACT02C.cbl` | COBOL Batch Program | Main program |
| `CVACT02Y.cpy` | Copybook | Card record layout (`CARD-RECORD`) |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBACT02C` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Read and print card data file |
| Source Version | CardDemo_v2.0-25-gdb72e6b-235, 2025-04-29 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field |
|---|---|---|---|---|
| `CARDFILE-FILE` | `CARDFILE` | INDEXED (KSDS) | Sequential | `FD-CARD-NUM` PIC X(16) |

---

## 5. File Section — Record Layout

### 5.1 CARDFILE-FILE (Input)
Defined at lines 37–40:
```
01 FD-CARDFILE-REC.
   05 FD-CARD-NUM    PIC X(16)
   05 FD-CARD-DATA   PIC X(134)
```
Total record length: 150 bytes. Read INTO `CARD-RECORD` (from copybook CVACT02Y).

---

## 6. Copybooks Referenced

| Copybook | Location in Source | Purpose |
|---|---|---|
| `CVACT02Y` | Line 45 (WORKING-STORAGE) | Defines `CARD-RECORD` (150-byte card layout) |

### CVACT02Y — CARD-RECORD Layout
```
01 CARD-RECORD.
   05 CARD-NUM             PIC X(16)
   05 CARD-ACCT-ID         PIC 9(11)
   05 CARD-CVV-CD          PIC 9(03)
   05 CARD-EMBOSSED-NAME   PIC X(50)
   05 CARD-EXPIRAION-DATE  PIC X(10)
   05 CARD-ACTIVE-STATUS   PIC X(01)
   05 FILLER               PIC X(59)
```
Total record length: 150 bytes.

---

## 7. Working-Storage Data Structures

| Field | PIC | Purpose |
|---|---|---|
| `CARDFILE-STATUS` | 2 x PIC X | VSAM file status for CARDFILE |
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
DISPLAY 'START OF EXECUTION OF PROGRAM CBACT02C'
PERFORM 0000-CARDFILE-OPEN

PERFORM UNTIL END-OF-FILE = 'Y'
    IF END-OF-FILE = 'N'
        PERFORM 1000-CARDFILE-GET-NEXT
        IF END-OF-FILE = 'N'
            DISPLAY CARD-RECORD
        END-IF
    END-IF
END-PERFORM

PERFORM 9000-CARDFILE-CLOSE
DISPLAY 'END OF EXECUTION OF PROGRAM CBACT02C'
GOBACK
```

### 8.2 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `0000-CARDFILE-OPEN` | 118–134 | Opens CARDFILE-FILE for INPUT. Sets APPL-RESULT to 8 before open; sets to 0 on success or 12 on failure. Abends on failure via 9910 + 9999. |
| `1000-CARDFILE-GET-NEXT` | 92–116 | Reads next card record sequentially into CARD-RECORD. On status '00': sets APPL-RESULT=0. On status '10': sets APPL-RESULT=16 (EOF). On other: sets APPL-RESULT=12 (error). Evaluates result: if EOF sets END-OF-FILE='Y'; if error abends. Note: the DISPLAY at line 96 is commented out; the main loop DISPLAY at line 78 handles the output. |
| `9000-CARDFILE-CLOSE` | 136–152 | Closes CARDFILE-FILE. Uses arithmetic idiom `ADD 8 TO ZERO GIVING APPL-RESULT` to set initial value, then `SUBTRACT APPL-RESULT FROM APPL-RESULT` on success. Abends on failure. |
| `9999-ABEND-PROGRAM` | 154–158 | Calls `CEE3ABD` with ABCODE=999, TIMING=0. |
| `9910-DISPLAY-IO-STATUS` | 161–174 | Formats and displays the 2-byte file status as a 4-digit value, handling both standard numeric and VSAM extended (stat1='9') codes. |

---

## 9. External Program Calls

| Called Program | Mechanism | Purpose |
|---|---|---|
| `CEE3ABD` | CALL ... USING ABCODE, TIMING | LE abnormal termination. Called in 9999-ABEND-PROGRAM (line 158). |

---

## 10. Business Logic and Processing Rules

1. **Sequential Read of CARDFILE:** The program reads CARDFILE-FILE from first record to EOF. Every record is processed — there is no filtering or selection.

2. **DISPLAY-Only Output:** The only output of this program is DISPLAY statements written to SYSOUT (DD SYSOUT in JCL). No physical output file is written.

3. **Diagnostic Purpose:** The program serves as a data validation/verification tool to confirm the contents of the CARDFILE KSDS. There is no record transformation or update operation.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| File open failure | Status != '00' (after initial APPL-RESULT=8 sentinel) | DISPLAY error, 9910-DISPLAY-IO-STATUS, 9999-ABEND-PROGRAM |
| Read error (not EOF) | APPL-RESULT = 12 (status not '00' or '10') | DISPLAY 'ERROR READING CARDFILE', abend |
| File close failure | Status != '00' | DISPLAY error, abend |

**Abend mechanism:** `CEE3ABD` called with ABCODE=999, TIMING=0. Produces user abend U0999.

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion | 0 (implicit GOBACK) |
| Any file I/O error | U0999 abend via CEE3ABD |

---

## 13. Observations

- This program is structurally identical to CBACT03C (which reads XREFFILE) and CBCUS01C (which reads CUSTFILE). All three follow the same read-display-close pattern with no output file.
- The DISPLAY at line 96 inside `1000-CARDFILE-GET-NEXT` is commented out (`* DISPLAY CARD-RECORD`), while the DISPLAY at line 78 in the main loop remains active. This redundancy indicates iterative development.
- No record count is maintained. There is no summary report at end of run.
