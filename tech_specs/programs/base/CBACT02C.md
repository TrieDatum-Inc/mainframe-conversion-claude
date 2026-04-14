# Technical Specification: CBACT02C

## 1. Program Overview

| Attribute        | Value                                       |
|------------------|---------------------------------------------|
| Program ID       | CBACT02C                                    |
| Source File      | app/cbl/CBACT02C.cbl                        |
| Application      | CardDemo                                    |
| Type             | Batch COBOL Program                         |
| Transaction ID   | N/A (batch)                                 |
| Function         | Read the Credit Card VSAM KSDS file sequentially and print (DISPLAY) each card record to SYSOUT |

---

## 2. Program Flow

### High-Level Flow

```
START
  OPEN CARDFILE (INPUT KSDS, sequential)
  PERFORM UNTIL END-OF-FILE = 'Y'
      READ next CARD-RECORD from CARDFILE
      IF successful: DISPLAY CARD-RECORD to SYSOUT
      IF EOF (status '10'): set END-OF-FILE = 'Y'
      IF error: display status, ABEND
  CLOSE CARDFILE
STOP
```

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| PROCEDURE DIVISION     | 70–87     | Main driver: opens CARDFILE, runs read loop, closes, GOBACK |
| 1000-CARDFILE-GET-NEXT | 92–116    | Reads one record into CARD-RECORD; maps file status to APPL-RESULT; handles EOF (sets END-OF-FILE='Y') and non-zero errors (ABEND) |
| 0000-CARDFILE-OPEN     | 118–134   | Opens CARDFILE INPUT; abends on non-zero status |
| 9000-CARDFILE-CLOSE    | 136–152   | Closes CARDFILE; abends on non-zero status |
| 9999-ABEND-PROGRAM     | 154–158   | Calls LE CEE3ABD with ABCODE=999, TIMING=0 |
| 9910-DISPLAY-IO-STATUS | 161–174   | Formats and displays 4-character I/O status code; handles VSAM physical error (IO-STAT1='9') |

Note: The DISPLAY CARD-RECORD statement inside `1000-CARDFILE-GET-NEXT` is commented out (line 96). The active display is at line 78 in the main loop body (DISPLAY CARD-RECORD after the GET-NEXT call when END-OF-FILE is still 'N').

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Contents | Used For |
|----------|----------|----------|
| CVACT02Y | `CARD-RECORD` (01 level, RECLN 150): CARD-NUM PIC X(16), CARD-ACCT-ID PIC 9(11), CARD-CVV-CD PIC 9(3), CARD-EMBOSSED-NAME PIC X(50), CARD-EXPIRAION-DATE PIC X(10), CARD-ACTIVE-STATUS PIC X(1), FILLER PIC X(59) | Source record layout for CARDFILE reads |

### File Description Records

| FD Name       | Record Name        | Key Field              | Layout |
|---------------|--------------------|------------------------|--------|
| CARDFILE-FILE | FD-CARDFILE-REC    | FD-CARD-NUM PIC X(16)  | FD-CARD-NUM X(16) + FD-CARD-DATA X(134) |

### Key Working Storage Variables

| Variable          | PIC         | Purpose |
|-------------------|-------------|---------|
| CARDFILE-STATUS   | X(2)        | Two-byte file status for CARDFILE |
| IO-STATUS         | X(2)        | Work area for status display routine |
| APPL-RESULT       | S9(9) COMP  | Result code: 0=AOK, 16=EOF, 12=error |
| END-OF-FILE       | X(1)        | Loop control: 'N'=continue, 'Y'=stop |
| ABCODE            | S9(9) BINARY | Abend code (999) |
| TIMING            | S9(9) BINARY | Timing for CEE3ABD (0) |
| TWO-BYTES-BINARY  | 9(4) BINARY  | Used to decode physical VSAM status byte |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name  | File Object    | Org  | Access     | Open Mode | Purpose |
|----------|----------------|------|------------|-----------|---------|
| CARDFILE | CARDFILE-FILE  | KSDS | Sequential | INPUT     | Credit card master records read sequentially |

---

## 6. Screen Interaction

None. Output is DISPLAY to SYSOUT only.

---

## 7. Called Programs / Transfers

| Called Program | Type   | Call Point           | Purpose |
|----------------|--------|----------------------|---------|
| CEE3ABD        | Static CALL | 9999-ABEND-PROGRAM | LE forced abnormal termination |

---

## 8. Error Handling

| Condition                    | Action |
|------------------------------|--------|
| CARDFILE status '00'         | Normal; APPL-RESULT = 0 |
| CARDFILE status '10' (EOF)   | APPL-RESULT = 16; END-OF-FILE = 'Y'; exit loop |
| CARDFILE any other status    | DISPLAY error message, call 9910-DISPLAY-IO-STATUS, call 9999-ABEND-PROGRAM |
| CARDFILE OPEN failure        | DISPLAY error, call 9910, call 9999 |
| CARDFILE CLOSE failure       | DISPLAY error, call 9910, call 9999 |

---

## 9. Business Rules

1. **Read-only reporting program**: CBACT02C is a diagnostic/listing utility. It performs no writes to any dataset other than SYSOUT.
2. **Sequential full scan**: All card records in CARDFILE are read and printed; no filtering is applied.
3. **Record display**: The entire CARD-RECORD (150 bytes including all fields) is passed to DISPLAY, which outputs the packed/binary representation as-is to SYSOUT.

---

## 10. Inputs and Outputs

### Inputs

| Source   | Description |
|----------|-------------|
| CARDFILE | KSDS VSAM credit card file read sequentially |

### Outputs

| Destination | Description |
|-------------|-------------|
| SYSOUT      | DISPLAY of each CARD-RECORD plus start/end execution messages and any error messages |

---

## 11. Key Variables and Their Purpose

| Variable    | Purpose |
|-------------|---------|
| CARD-RECORD | Working area (from CVACT02Y) populated by READ CARDFILE-FILE INTO; contains all card master fields |
| END-OF-FILE | Controls the main read loop; set to 'Y' on EOF |
| APPL-RESULT | Intermediate result indicator used to map file status to application-level result codes |
