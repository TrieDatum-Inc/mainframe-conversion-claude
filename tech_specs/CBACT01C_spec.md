# Technical Specification: CBACT01C

## 1. Executive Summary

CBACT01C is a batch COBOL program in the CardDemo application that sequentially reads the account master VSAM KSDS file and writes the data to three different output files: a flat sequential file, a fixed-format array file, and a variable-length record file. Its primary purpose is to demonstrate and test multi-format output writing from an account file, including a date-format conversion call to an assembler program.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBACT01C.cbl` | COBOL Batch Program | Main program |
| `CVACT01Y.cpy` | Copybook | Account master record layout (`ACCOUNT-RECORD`) |
| `CODATECN.cpy` | Copybook | Date conversion interface record (`CODATECN-REC`) |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBACT01C` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Source Version | CardDemo_v2.0-25-gdb72e6b-235, 2025-04-29 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field |
|---|---|---|---|---|
| `ACCTFILE-FILE` | `ACCTFILE` | INDEXED (KSDS) | Sequential | `FD-ACCT-ID` PIC 9(11) |
| `OUT-FILE` | `OUTFILE` | Sequential | Sequential | N/A |
| `ARRY-FILE` | `ARRYFILE` | Sequential | Sequential | N/A |
| `VBRC-FILE` | `VBRCFILE` | Sequential (Variable) | Sequential | N/A |

**Note on VBRC-FILE:** Declared with `RECORDING MODE IS V`, `RECORD IS VARYING IN SIZE FROM 10 TO 80 DEPENDING ON WS-RECD-LEN`. This is a variable-length record output file.

---

## 5. File Section — Record Layouts

### 5.1 ACCTFILE-FILE (Input)
Defined at lines 52–55:
```
01 FD-ACCTFILE-REC.
   05 FD-ACCT-ID     PIC 9(11)
   05 FD-ACCT-DATA   PIC X(289)
```
Total record length: 300 bytes. Read INTO `ACCOUNT-RECORD` (from copybook CVACT01Y).

### 5.2 OUT-FILE (Output)
Defined at lines 57–69. A flattened sequential representation:
```
01 OUT-ACCT-REC.
   05 OUT-ACCT-ID                PIC 9(11)
   05 OUT-ACCT-ACTIVE-STATUS     PIC X(01)
   05 OUT-ACCT-CURR-BAL          PIC S9(10)V99
   05 OUT-ACCT-CREDIT-LIMIT      PIC S9(10)V99
   05 OUT-ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99
   05 OUT-ACCT-OPEN-DATE         PIC X(10)
   05 OUT-ACCT-EXPIRAION-DATE    PIC X(10)
   05 OUT-ACCT-REISSUE-DATE      PIC X(10)
   05 OUT-ACCT-CURR-CYC-CREDIT   PIC S9(10)V99
   05 OUT-ACCT-CURR-CYC-DEBIT    PIC S9(10)V99 USAGE IS COMP-3
   05 OUT-ACCT-GROUP-ID          PIC X(10)
```

### 5.3 ARRY-FILE (Output)
Defined at lines 71–78. Array record with 5 occurrences:
```
01 ARR-ARRAY-REC.
   05 ARR-ACCT-ID              PIC 9(11)
   05 ARR-ACCT-BAL OCCURS 5 TIMES.
      10 ARR-ACCT-CURR-BAL       PIC S9(10)V99
      10 ARR-ACCT-CURR-CYC-DEBIT PIC S9(10)V99 USAGE IS COMP-3
   05 ARR-FILLER                 PIC X(04)
```

### 5.4 VBRC-FILE (Output, Variable-Length)
Declared at lines 80–85. Uses `WS-RECD-LEN` (PIC 9(04)) as the DEPENDING ON variable. Two working-storage record layouts are written:
- `VBRC-REC1` (12 bytes): Account ID (9(11)) + Active Status (X(01))
- `VBRC-REC2` (39 bytes): Account ID (9(11)) + Current Balance (S9(10)V99) + Credit Limit (S9(10)V99) + Reissue Year (X(04))

---

## 6. Copybooks Referenced

| Copybook | Location in Source | Purpose |
|---|---|---|
| `CVACT01Y` | Line 89 (WORKING-STORAGE) | Defines `ACCOUNT-RECORD` (300-byte account layout) |
| `CODATECN` | Line 90 (WORKING-STORAGE) | Defines `CODATECN-REC` for date format conversion interface |

### CVACT01Y — ACCOUNT-RECORD Layout
```
01 ACCOUNT-RECORD.
   05 ACCT-ID                 PIC 9(11)
   05 ACCT-ACTIVE-STATUS      PIC X(01)
   05 ACCT-CURR-BAL           PIC S9(10)V99
   05 ACCT-CREDIT-LIMIT       PIC S9(10)V99
   05 ACCT-CASH-CREDIT-LIMIT  PIC S9(10)V99
   05 ACCT-OPEN-DATE          PIC X(10)
   05 ACCT-EXPIRAION-DATE     PIC X(10)
   05 ACCT-REISSUE-DATE       PIC X(10)
   05 ACCT-CURR-CYC-CREDIT    PIC S9(10)V99
   05 ACCT-CURR-CYC-DEBIT     PIC S9(10)V99
   05 ACCT-ADDR-ZIP           PIC X(10)
   05 ACCT-GROUP-ID           PIC X(10)
   05 FILLER                  PIC X(178)
```
Total record length: 300 bytes.

### CODATECN — Date Conversion Record
Provides an interface to the `COBDATFT` assembler program. Fields include `CODATECN-TYPE` (input format indicator), `CODATECN-INP-DATE` (20-byte input), `CODATECN-OUTTYPE` (output format indicator), and `CODATECN-0UT-DATE` (20-byte output).

---

## 7. Working-Storage Data Structures

| Field | PIC | Purpose |
|---|---|---|
| `ACCTFILE-STATUS` | 2 x PIC X | VSAM file status for ACCTFILE |
| `OUTFILE-STATUS` | 2 x PIC X | File status for OUTFILE |
| `ARRYFILE-STATUS` | 2 x PIC X | File status for ARRYFILE |
| `VBRCFILE-STATUS` | 2 x PIC X | File status for VBRCFILE |
| `IO-STATUS` | 2 x PIC X | Scratch area for displaying I/O errors |
| `TWO-BYTES-BINARY` / `TWO-BYTES-ALPHA` | PIC 9(4) BINARY / REDEFINES | Binary/character overlay for extended file status display |
| `IO-STATUS-04` | PIC 9 + PIC 999 | Formatted 4-digit I/O status display |
| `APPL-RESULT` | PIC S9(9) COMP | Internal result code; 88 levels: `APPL-AOK` (0), `APPL-EOF` (16) |
| `END-OF-FILE` | PIC X(01) VALUE 'N' | EOF flag; set to 'Y' on file status '10' |
| `ABCODE` | PIC S9(9) BINARY | Abend code passed to CEE3ABD (value 999) |
| `TIMING` | PIC S9(9) BINARY | Timing parameter passed to CEE3ABD (value 0) |
| `WS-RECD-LEN` | PIC 9(04) | Determines length of variable record written to VBRC-FILE |
| `VBRC-REC1` | 12 bytes | Variable record type 1: Account ID + Active Status |
| `VBRC-REC2` | 39 bytes | Variable record type 2: Account ID + Balance + Credit Limit + Reissue Year |
| `WS-ACCT-REISSUE-DATE` | PIC X(10) | Reissue date parsed as YYYY-MM-DD |
| `WS-REISSUE-DATE` REDEFINES | PIC X(10) | Character overlay of WS-ACCT-REISSUE-DATE |

---

## 8. Procedure Division — Program Flow

### 8.1 Main Control (lines 141–160)
```
DISPLAY 'START OF EXECUTION OF PROGRAM CBACT01C'
PERFORM 0000-ACCTFILE-OPEN
PERFORM 2000-OUTFILE-OPEN
PERFORM 3000-ARRFILE-OPEN
PERFORM 4000-VBRFILE-OPEN

PERFORM UNTIL END-OF-FILE = 'Y'
    IF END-OF-FILE = 'N'
        PERFORM 1000-ACCTFILE-GET-NEXT
        IF END-OF-FILE = 'N'
            DISPLAY ACCOUNT-RECORD
        END-IF
    END-IF
END-PERFORM

PERFORM 9000-ACCTFILE-CLOSE
DISPLAY 'END OF EXECUTION OF PROGRAM CBACT01C'
GOBACK
```
**Note:** Only ACCTFILE is explicitly closed in the main flow at line 156. The output files (OUTFILE, ARRYFILE, VBRCFILE) are opened but never explicitly closed by a CLOSE statement. This is a defect — output files are left open at program termination.

### 8.2 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `0000-ACCTFILE-OPEN` | 317–333 | Opens ACCTFILE-FILE for INPUT. Abends on failure. |
| `2000-OUTFILE-OPEN` | 334–350 | Opens OUT-FILE for OUTPUT. Abends on failure. |
| `3000-ARRFILE-OPEN` | 352–368 | Opens ARRY-FILE for OUTPUT. Abends on failure. |
| `4000-VBRFILE-OPEN` | 370–386 | Opens VBRC-FILE for OUTPUT. Abends on failure. |
| `1000-ACCTFILE-GET-NEXT` | 165–198 | Reads next account record sequentially. On status '00': calls 1100, 1300, 1350, 1400, 1450, 1500, 1550, 1575. On status '10': sets EOF. On other: abends. |
| `1100-DISPLAY-ACCT-RECORD` | 200–213 | Displays all account fields to SYSOUT for diagnostic purposes. |
| `1300-POPUL-ACCT-RECORD` | 215–240 | Populates OUT-ACCT-REC from ACCOUNT-RECORD. Calls assembler `COBDATFT` to convert ACCT-REISSUE-DATE to formatted output date. If ACCT-CURR-CYC-DEBIT = 0, sets OUT-ACCT-CURR-CYC-DEBIT to 2525.00 (hardcoded default). |
| `1350-WRITE-ACCT-RECORD` | 242–251 | WRITEs OUT-ACCT-REC to OUT-FILE. Abends if status not '00' or '10'. |
| `1400-POPUL-ARRAY-RECORD` | 253–261 | Populates ARR-ARRAY-REC: sets occurrences (1) and (2) with ACCT-CURR-BAL and hardcoded debit amounts (1005.00 and 1525.00); occurrence (3) has hardcoded values (-1025.00 balance, -2500.00 debit). |
| `1450-WRITE-ARRY-RECORD` | 263–274 | WRITEs ARR-ARRAY-REC to ARRY-FILE. Abends if status not '00' or '10'. |
| `1500-POPUL-VBRC-RECORD` | 276–285 | Populates VBRC-REC1 and VBRC-REC2 from ACCOUNT-RECORD fields. |
| `1550-WRITE-VB1-RECORD` | 287–300 | Sets WS-RECD-LEN = 12, moves VBRC-REC1 to VBR-REC, WRITEs to VBRC-FILE. Abends on error. |
| `1575-WRITE-VB2-RECORD` | 302–315 | Sets WS-RECD-LEN = 39, moves VBRC-REC2 to VBR-REC, WRITEs to VBRC-FILE. Abends on error. |
| `9000-ACCTFILE-CLOSE` | 388–404 | Closes ACCTFILE-FILE. Abends on failure. |
| `9910-DISPLAY-IO-STATUS` | 413–426 | Formats and displays the 2-byte file status code as a 4-digit value. Handles both numeric and non-numeric (VSAM extended) status codes. |
| `9999-ABEND-PROGRAM` | 406–410 | Calls `CEE3ABD` Language Environment service with ABCODE=999, TIMING=0 to force an abend. |

---

## 9. External Program Calls

| Called Program | Mechanism | Purpose |
|---|---|---|
| `COBDATFT` | CALL ... USING CODATECN-REC | Assembler date formatting routine. Converts ACCT-REISSUE-DATE from one format to another. Called in paragraph 1300-POPUL-ACCT-RECORD (line 231). Input type '2' (YYYY-MM-DD), output type '2'. |
| `CEE3ABD` | CALL ... USING ABCODE, TIMING | LE (Language Environment) abnormal termination service. Called in 9999-ABEND-PROGRAM (line 410). |

---

## 10. Business Logic and Processing Rules

1. **Sequential Account File Read:** The program reads ACCTFILE sequentially from beginning to end. Every record is processed.

2. **Date Conversion (line 231):** ACCT-REISSUE-DATE is passed to the external assembler routine `COBDATFT` (via CODATECN-REC) for format conversion. The converted date is placed in OUT-ACCT-REISSUE-DATE.

3. **Default Debit Injection (lines 236–238):** If `ACCT-CURR-CYC-DEBIT` equals zero, OUT-ACCT-CURR-CYC-DEBIT is set to the hardcoded value 2525.00. This is a data transformation rule — zero debit accounts receive a synthetic default value in the output.

4. **Array Population with Hardcoded Values (lines 254–261):** The array record contains only partial live data. Occurrences (1) and (2) receive the live `ACCT-CURR-BAL` but hardcoded debit values (1005.00 and 1525.00). Occurrence (3) has entirely hardcoded values (-1025.00 and -2500.00). This appears to be test/demonstration data rather than production logic.

5. **Variable-Length Record Output:** Two variable-length records are produced per account: a short 12-byte record containing ID and status, and a longer 39-byte record containing ID, balance, credit limit, and reissue year.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| File open failure | Status != '00' | DISPLAY error message, call 9910-DISPLAY-IO-STATUS, call 9999-ABEND-PROGRAM |
| Read error (not EOF) | Status not '00' or '10' | DISPLAY 'ERROR READING ACCOUNT FILE', abend |
| Write error (OUT-FILE) | Status not '00' or '10' | DISPLAY write status, abend |
| Write error (ARRY-FILE) | Status not '00' or '10' | DISPLAY write status, abend |
| Write error (VBRC-FILE) | Status not '00' or '10' | DISPLAY write status, abend |
| Close failure (ACCTFILE) | Status != '00' | DISPLAY error, abend |

**Abend mechanism:** All fatal errors call `9999-ABEND-PROGRAM`, which invokes `CEE3ABD` with ABCODE=999. This produces a user abend U0999 in the z/OS environment.

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion | 0 (implicit GOBACK) |
| Any file I/O error | U0999 abend via CEE3ABD |

---

## 13. Known Issues and Observations

- **Output files not closed:** OUT-FILE, ARRY-FILE, and VBRC-FILE are opened but there is no CLOSE statement for them in the main flow. Only ACCTFILE-FILE is closed (paragraph 9000-ACCTFILE-CLOSE). On z/OS, the runtime will implicitly close these on GOBACK, but this is non-standard practice and may cause issues with buffer flush in some environments.
- **Hardcoded test data:** The array population logic (paragraph 1400-POPUL-ARRAY-RECORD) uses hardcoded debit amounts and negative balance values, suggesting this program is a VSAM feature demonstration rather than a production batch job.
- **Diagnostic DISPLAY statements:** Paragraph 1100-DISPLAY-ACCT-RECORD displays every account record field to SYSOUT, which would produce very large output in a production run.
