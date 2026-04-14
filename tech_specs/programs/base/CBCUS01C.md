# Technical Specification: CBCUS01C

## 1. Program Overview

| Attribute        | Value                                         |
|------------------|-----------------------------------------------|
| Program ID       | CBCUS01C                                      |
| Source File      | app/cbl/CBCUS01C.cbl                          |
| Application      | CardDemo                                      |
| Type             | Batch COBOL Program                           |
| Transaction ID   | N/A (batch)                                   |
| Function         | Read the Customer VSAM KSDS file sequentially and print (DISPLAY) each customer record to SYSOUT |

---

## 2. Program Flow

### High-Level Flow

```
START
  OPEN CUSTFILE (INPUT KSDS, sequential)
  PERFORM UNTIL END-OF-FILE = 'Y'
      READ next CUSTOMER-RECORD from CUSTFILE
      IF successful: DISPLAY CUSTOMER-RECORD (printed twice — see note)
      IF EOF (status '10'): set END-OF-FILE = 'Y'
      IF error: display status, ABEND
  CLOSE CUSTFILE
STOP
```

**Note on double DISPLAY**: DISPLAY CUSTOMER-RECORD appears both inside `1000-CUSTFILE-GET-NEXT` (line 96) and in the main loop body (line 78). Each successful read results in two DISPLAY statements.

### Paragraph-Level Detail

| Paragraph           | Lines     | Description |
|---------------------|-----------|-------------|
| PROCEDURE DIVISION  | 70–87     | Main driver: opens CUSTFILE, loops, closes, GOBACK |
| 1000-CUSTFILE-GET-NEXT | 92–116 | Reads CUSTOMER-RECORD; displays it; evaluates status; handles EOF or calls Z-ABEND-PROGRAM |
| 0000-CUSTFILE-OPEN  | 118–134   | Opens CUSTFILE INPUT; calls Z-DISPLAY-IO-STATUS and Z-ABEND-PROGRAM on failure |
| 9000-CUSTFILE-CLOSE | 136–152   | Closes CUSTFILE; calls Z-DISPLAY-IO-STATUS and Z-ABEND-PROGRAM on failure |
| Z-ABEND-PROGRAM     | 154–158   | Calls CEE3ABD with ABCODE=999, TIMING=0 |
| Z-DISPLAY-IO-STATUS | 161–174   | Formats and displays 4-character I/O status (same logic as 9910 in other programs; renamed Z-prefix in this program) |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Contents | Used For |
|----------|----------|----------|
| CVCUS01Y | `CUSTOMER-RECORD` (01 level, RECLN 500): CUST-ID 9(9), CUST-FIRST-NAME X(25), CUST-MIDDLE-NAME X(25), CUST-LAST-NAME X(25), CUST-ADDR-LINE-1 X(50), CUST-ADDR-LINE-2 X(50), CUST-ADDR-LINE-3 X(50), CUST-ADDR-STATE-CD X(2), CUST-ADDR-COUNTRY-CD X(3), CUST-ADDR-ZIP X(10), CUST-PHONE-NUM-1 X(15), CUST-PHONE-NUM-2 X(15), CUST-SSN 9(9), CUST-GOVT-ISSUED-ID X(20), CUST-DOB-YYYY-MM-DD X(10), CUST-EFT-ACCOUNT-ID X(10), CUST-PRI-CARD-HOLDER-IND X(1), CUST-FICO-CREDIT-SCORE 9(3), FILLER X(168) | Source record layout for CUSTFILE reads |

### File Description Records

| FD Name       | Record Name        | Key Field             | Layout |
|---------------|--------------------|-----------------------|--------|
| CUSTFILE-FILE | FD-CUSTFILE-REC    | FD-CUST-ID PIC 9(9)   | FD-CUST-ID 9(9) + FD-CUST-DATA X(491) |

### Key Working Storage Variables

| Variable         | PIC         | Purpose |
|------------------|-------------|---------|
| CUSTFILE-STATUS  | X(2)        | Two-byte file status |
| IO-STATUS        | X(2)        | Work area for Z-DISPLAY-IO-STATUS |
| APPL-RESULT      | S9(9) COMP  | Result code: 0=AOK, 16=EOF, 12=error |
| END-OF-FILE      | X(1)        | Loop control flag |
| ABCODE           | S9(9) BINARY | Abend code = 999 |
| TIMING           | S9(9) BINARY | Timing = 0 |
| TWO-BYTES-BINARY | 9(4) BINARY  | VSAM physical error decoding |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name  | File Object    | Org  | Access     | Open Mode | Purpose |
|----------|----------------|------|------------|-----------|---------|
| CUSTFILE | CUSTFILE-FILE  | KSDS | Sequential | INPUT     | Customer master records read sequentially |

---

## 6. Screen Interaction

None. Output to SYSOUT via DISPLAY.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| CEE3ABD        | Static CALL | LE forced abend |

---

## 8. Error Handling

| Condition                    | Action |
|------------------------------|--------|
| CUSTFILE status '00'         | Normal; APPL-RESULT = 0 |
| CUSTFILE status '10' (EOF)   | APPL-RESULT = 16; END-OF-FILE = 'Y' |
| CUSTFILE other status        | DISPLAY 'ERROR READING CUSTOMER FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM |
| OPEN failure                 | DISPLAY 'ERROR OPENING CUSTFILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM |
| CLOSE failure                | DISPLAY 'ERROR CLOSING CUSTOMER FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM |

---

## 9. Business Rules

1. **Read-only utility**: No writes to any dataset other than SYSOUT. Diagnostic/listing program.
2. **Full sequential scan**: All customer records are read and displayed; no filtering.
3. **Double display**: Each record is displayed twice (lines 96 and 78) due to DISPLAY statements in both the sub-paragraph and the main loop. This appears to be unintentional.

---

## 10. Inputs and Outputs

### Inputs

| Source   | Description |
|----------|-------------|
| CUSTFILE | KSDS VSAM customer file read sequentially |

### Outputs

| Destination | Description |
|-------------|-------------|
| SYSOUT      | DISPLAY of each CUSTOMER-RECORD (twice) plus execution start/end messages |

---

## 11. Key Variables and Their Purpose

| Variable        | Purpose |
|-----------------|---------|
| CUSTOMER-RECORD | Working area (from CVCUS01Y) populated by READ CUSTFILE-FILE INTO; all customer fields |
| END-OF-FILE     | Loop termination flag |
| APPL-RESULT     | Intermediate result code mapping file status to application outcome |
