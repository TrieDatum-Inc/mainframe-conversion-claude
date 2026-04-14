# Technical Specification: CBACT01C

## 1. Program Overview

| Attribute        | Value                                         |
|------------------|-----------------------------------------------|
| Program ID       | CBACT01C                                      |
| Source File      | app/cbl/CBACT01C.cbl                          |
| Application      | CardDemo                                      |
| Type             | Batch COBOL Program                           |
| Transaction ID   | N/A (batch)                                   |
| Function         | Read the Account VSAM KSDS file sequentially and write records to three output files: a fixed-format sequential file, an array record file, and a variable-length record file |

---

## 2. Program Flow

### High-Level Flow

```
START
  OPEN ACCTFILE (INPUT KSDS)
  OPEN OUTFILE  (OUTPUT sequential)
  OPEN ARRYFILE (OUTPUT sequential)
  OPEN VBRCFILE (OUTPUT variable-length sequential)
  PERFORM UNTIL END-OF-FILE = 'Y'
      READ next ACCOUNT-RECORD sequentially from ACCTFILE
      IF successful:
          DISPLAY account fields to SYSOUT
          POPULATE and WRITE OUT-ACCT-REC to OUTFILE
          POPULATE and WRITE ARR-ARRAY-REC to ARRYFILE
          POPULATE VBRC-REC1 (short: 12 bytes)
          POPULATE VBRC-REC2 (long: 39 bytes)
          WRITE VBR-REC1 to VBRCFILE
          WRITE VBR-REC2 to VBRCFILE
      IF EOF (status '10'): set END-OF-FILE = 'Y'
      IF error: display status, ABEND
  CLOSE ACCTFILE
STOP
```

### Paragraph-Level Detail

| Paragraph            | Lines     | Description |
|----------------------|-----------|-------------|
| PROCEDURE DIVISION   | 140–160   | Main driver: opens files, invokes 1000-ACCTFILE-GET-NEXT loop, closes ACCTFILE |
| 1000-ACCTFILE-GET-NEXT | 165–198 | Reads one ACCOUNT-RECORD into ACCOUNT-RECORD structure; evaluates file status; calls subordinate paragraphs for output; handles EOF and errors |
| 1100-DISPLAY-ACCT-RECORD | 200–213 | Displays all account fields to SYSOUT via DISPLAY |
| 1300-POPUL-ACCT-RECORD | 215–240 | Populates OUT-ACCT-REC; calls external program COBDATFT (assembler date formatter) to reformat ACCT-REISSUE-DATE; applies special rule: if ACCT-CURR-CYC-DEBIT = 0, moves hardcoded value 2525.00 |
| 1350-WRITE-ACCT-RECORD | 242–251 | Writes OUT-ACCT-REC to OUTFILE; abends on non-00/10 status |
| 1400-POPUL-ARRAY-RECORD | 253–261 | Loads ARR-ARRAY-REC with ACCT-ID and hardcoded test values for ARR-ACCT-CURR-BAL and ARR-ACCT-CURR-CYC-DEBIT for occurrences 1–3 |
| 1450-WRITE-ARRY-RECORD | 263–274 | Writes ARR-ARRAY-REC to ARRYFILE |
| 1500-POPUL-VBRC-RECORD | 276–285 | Populates VBRC-REC1 (ACCT-ID + ACCT-ACTIVE-STATUS) and VBRC-REC2 (ACCT-ID + ACCT-CURR-BAL + ACCT-CREDIT-LIMIT + ACCT-REISSUE-YYYY) |
| 1550-WRITE-VB1-RECORD | 287–300 | Moves 12 bytes of VBRC-REC1 into VBR-REC; sets WS-RECD-LEN=12; writes to VBRCFILE |
| 1575-WRITE-VB2-RECORD | 302–315 | Moves 39 bytes of VBRC-REC2 into VBR-REC; sets WS-RECD-LEN=39; writes to VBRCFILE |
| 0000-ACCTFILE-OPEN   | 317–333   | Opens ACCTFILE INPUT; abends on failure |
| 2000-OUTFILE-OPEN    | 334–350   | Opens OUT-FILE OUTPUT; abends on failure |
| 3000-ARRFILE-OPEN    | 352–368   | Opens ARRY-FILE OUTPUT; abends on failure |
| 4000-VBRFILE-OPEN    | 370–386   | Opens VBRC-FILE OUTPUT; abends on failure |
| 9000-ACCTFILE-CLOSE  | 388–404   | Closes ACCTFILE; abends on failure |
| 9999-ABEND-PROGRAM   | 406–410   | Calls LE routine CEE3ABD with code 999 to force abnormal termination |
| 9910-DISPLAY-IO-STATUS | 412–426 | Formats and displays 4-character I/O status code to SYSOUT; handles numeric and non-numeric (VSAM physical error) status |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook    | Contents                                              | Used For |
|-------------|-------------------------------------------------------|----------|
| CVACT01Y    | `ACCOUNT-RECORD` (01 level, RECLN 300): ACCT-ID PIC 9(11), ACCT-ACTIVE-STATUS PIC X(1), ACCT-CURR-BAL S9(10)V99, ACCT-CREDIT-LIMIT S9(10)V99, ACCT-CASH-CREDIT-LIMIT S9(10)V99, ACCT-OPEN-DATE X(10), ACCT-EXPIRAION-DATE X(10), ACCT-REISSUE-DATE X(10), ACCT-CURR-CYC-CREDIT S9(10)V99, ACCT-CURR-CYC-DEBIT S9(10)V99, ACCT-ADDR-ZIP X(10), ACCT-GROUP-ID X(10), FILLER X(178) | Source record layout for ACCTFILE reads |
| CODATECN    | `CODATECN-REC`: CODATECN-INP-DATE X(10), CODATECN-TYPE X(1), CODATECN-OUTTYPE X(1), CODATECN-0UT-DATE X(10) | Parameter area for COBDATFT date formatter call |

### File Description Records

| FD Name        | Record Name        | Key Field       | Layout |
|----------------|--------------------|-----------------|--------|
| ACCTFILE-FILE  | FD-ACCTFILE-REC    | FD-ACCT-ID 9(11) | FD-ACCT-ID 9(11) + FD-ACCT-DATA X(289) |
| OUT-FILE       | OUT-ACCT-REC       | N/A (sequential) | OUT-ACCT-ID 9(11), OUT-ACCT-ACTIVE-STATUS X(1), OUT-ACCT-CURR-BAL S9(10)V99, OUT-ACCT-CREDIT-LIMIT S9(10)V99, OUT-ACCT-CASH-CREDIT-LIMIT S9(10)V99, OUT-ACCT-OPEN-DATE X(10), OUT-ACCT-EXPIRAION-DATE X(10), OUT-ACCT-REISSUE-DATE X(10), OUT-ACCT-CURR-CYC-CREDIT S9(10)V99, OUT-ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3, OUT-ACCT-GROUP-ID X(10) |
| ARRY-FILE      | ARR-ARRAY-REC      | N/A (sequential) | ARR-ACCT-ID 9(11), ARR-ACCT-BAL OCCURS 5: ARR-ACCT-CURR-BAL S9(10)V99 + ARR-ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3, ARR-FILLER X(4) |
| VBRC-FILE      | VBR-REC X(80)      | N/A (sequential) | Variable-length (RECORDING MODE V, 10–80 bytes, DEPENDING ON WS-RECD-LEN) |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| ACCTFILE-STATUS      | X(2)      | Two-byte VSAM file status for ACCTFILE |
| OUTFILE-STATUS       | X(2)      | File status for OUTFILE |
| ARRYFILE-STATUS      | X(2)      | File status for ARRYFILE |
| VBRCFILE-STATUS      | X(2)      | File status for VBRCFILE |
| IO-STATUS            | X(2)      | Temporary work area for status display |
| APPL-RESULT          | S9(9) COMP | Internal result code: 0=AOK, 16=EOF, 12=error |
| END-OF-FILE          | X(1)      | Loop control flag; 'N'=continue, 'Y'=stop |
| ABCODE               | S9(9) BINARY | Abend code passed to CEE3ABD (value 999) |
| TIMING               | S9(9) BINARY | Timing option for CEE3ABD (value 0) |
| WS-RECD-LEN          | 9(4)      | Controls DEPENDING ON clause for VBR variable-length record write |
| VBRC-REC1            | Group     | 12-byte VBR record: VB1-ACCT-ID 9(11) + VB1-ACCT-ACTIVE-STATUS X(1) |
| VBRC-REC2            | Group     | 39-byte VBR record: VB2-ACCT-ID 9(11) + VB2-ACCT-CURR-BAL S9(10)V99 + VB2-ACCT-CREDIT-LIMIT S9(10)V99 + VB2-ACCT-REISSUE-YYYY X(4) |
| TWO-BYTES-BINARY     | 9(4) BINARY | Used in 9910 to decode non-numeric VSAM physical error byte |

---

## 4. CICS Commands Used

None. This is a batch program.

---

## 5. File/Dataset Access

| DD Name    | File Object    | Org       | Access    | Open Mode | Purpose |
|------------|----------------|-----------|-----------|-----------|---------|
| ACCTFILE   | ACCTFILE-FILE  | KSDS      | Sequential | INPUT    | Source account master records |
| OUTFILE    | OUT-FILE       | Sequential | Sequential | OUTPUT   | Fixed-format account output |
| ARRYFILE   | ARRY-FILE      | Sequential | Sequential | OUTPUT   | Array-structured account output |
| VBRCFILE   | VBRC-FILE      | Sequential | Sequential | OUTPUT   | Variable-length record output (2 record types per account) |

---

## 6. Screen Interaction

None. Batch program with DISPLAY output to SYSOUT only.

---

## 7. Called Programs / Transfers

| Called Program | Type   | CALL Point         | Purpose |
|----------------|--------|--------------------|---------|
| COBDATFT       | Static CALL | 1300-POPUL-ACCT-RECORD (line 231) | Assembler date formatting routine; converts ACCT-REISSUE-DATE using CODATECN-REC parameter area; TYPE='2', OUTTYPE='2' |
| CEE3ABD        | Static CALL | 9999-ABEND-PROGRAM (line 410) | LE abnormal termination; ABCODE=999, TIMING=0 |

---

## 8. Error Handling

| Condition                        | Action |
|----------------------------------|--------|
| ACCTFILE status '00'             | Normal; continue processing |
| ACCTFILE status '10' (EOF)       | Set APPL-EOF (value 16); set END-OF-FILE='Y'; terminate loop |
| ACCTFILE any other status        | DISPLAY error, PERFORM 9910-DISPLAY-IO-STATUS, PERFORM 9999-ABEND-PROGRAM |
| OUTFILE write status not '00'/'10' | DISPLAY error, call 9910, call 9999 |
| ARRYFILE write status not '00'/'10' | DISPLAY error, call 9910, call 9999 |
| VBRCFILE write status not '00'/'10' | DISPLAY error, call 9910, call 9999 |
| Any file OPEN failure            | DISPLAY error, call 9910, call 9999 |

The 9910-DISPLAY-IO-STATUS paragraph decodes both standard two-digit file status (numeric) and VSAM physical error codes (IO-STAT1='9', IO-STAT2=binary byte).

---

## 9. Business Rules

1. **Date reformatting**: ACCT-REISSUE-DATE is reformatted from its stored format to an output format via the external assembler program COBDATFT. Input type '2' and output type '2' are used.
2. **Zero debit substitution** (line 236–238): If ACCT-CURR-CYC-DEBIT equals zero, the output record receives a hardcoded value of 2525.00. This appears to be test/demonstration data rather than a live business rule.
3. **Array population with hardcoded values** (lines 255–260): ARR-ACCT-BAL(1) through (3) are populated partly from actual account data and partly from hardcoded test values (1005.00, 1525.00, -1025.00, -2500.00). Occurrences 4 and 5 remain as initialized (zero).
4. **Two VBR record subtypes per account**: Each account produces one short (12-byte) VBR record containing only ID and status, and one long (39-byte) VBR record containing financial fields.

---

## 10. Inputs and Outputs

### Inputs

| Source   | Description |
|----------|-------------|
| ACCTFILE | KSDS VSAM file read sequentially; all account records |

### Outputs

| Destination | Record Type | Description |
|-------------|-------------|-------------|
| OUTFILE     | OUT-ACCT-REC | Fixed-format account record with reformatted reissue date |
| ARRYFILE    | ARR-ARRAY-REC | Account ID plus 5-occurrence balance array (3 populated) |
| VBRCFILE    | VBR-REC      | Two variable-length records per account: short (12B) and long (39B) |
| SYSOUT      | DISPLAY      | Each account's fields printed; file error messages; start/end messages |

---

## 11. Key Variables and Their Purpose

| Variable              | Purpose |
|-----------------------|---------|
| ACCOUNT-RECORD        | Working area (from CVACT01Y) populated by READ ACCTFILE-FILE INTO |
| OUT-ACCT-REC          | Output record for OUTFILE; mirrors ACCOUNT-RECORD with reformatted date |
| ARR-ARRAY-REC         | Output record for ARRYFILE; demonstrates OCCURS array usage |
| VBR-REC               | 80-byte output buffer for VBRCFILE; loaded via reference modification |
| WS-RECD-LEN           | Controls which number of bytes are written in variable-length record |
| CODATECN-REC          | Parameter block for COBDATFT; carries input date, type codes, output date |
| APPL-RESULT / APPL-AOK / APPL-EOF | Standard three-level result indicator used throughout for file operation outcome |
| END-OF-FILE           | Master loop termination flag |
