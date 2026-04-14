# Technical Specification: CBACT03C

## 1. Program Overview

| Attribute        | Value                                            |
|------------------|--------------------------------------------------|
| Program ID       | CBACT03C                                         |
| Source File      | app/cbl/CBACT03C.cbl                             |
| Application      | CardDemo                                         |
| Type             | Batch COBOL Program                              |
| Transaction ID   | N/A (batch)                                      |
| Function         | Read the Account/Card Cross-Reference VSAM KSDS file sequentially and print (DISPLAY) each cross-reference record to SYSOUT |

---

## 2. Program Flow

### High-Level Flow

```
START
  OPEN XREFFILE (INPUT KSDS, sequential)
  PERFORM UNTIL END-OF-FILE = 'Y'
      READ next CARD-XREF-RECORD from XREFFILE
      IF successful: DISPLAY CARD-XREF-RECORD (printed twice per record — see note)
      IF EOF (status '10'): set END-OF-FILE = 'Y'
      IF error: display status, ABEND
  CLOSE XREFFILE
STOP
```

**Note on double DISPLAY**: In `1000-XREFFILE-GET-NEXT` (line 96), CARD-XREF-RECORD is displayed when status = '00'. Additionally, the main loop body (line 78) displays CARD-XREF-RECORD again after the paragraph returns if END-OF-FILE is still 'N'. This results in each record being displayed twice per iteration.

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| PROCEDURE DIVISION     | 70–87     | Main driver: opens XREFFILE, runs read loop, closes, GOBACK |
| 1000-XREFFILE-GET-NEXT | 92–116    | Reads CARD-XREF-RECORD; displays it on success (line 96); maps status to APPL-RESULT; sets EOF flag or abends |
| 0000-XREFFILE-OPEN     | 118–134   | Opens XREFFILE INPUT; abends on failure |
| 9000-XREFFILE-CLOSE    | 136–152   | Closes XREFFILE; abends on failure |
| 9999-ABEND-PROGRAM     | 154–158   | LE forced abnormal termination via CEE3ABD |
| 9910-DISPLAY-IO-STATUS | 161–174   | Formats/displays 4-character I/O status; handles VSAM physical error |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Contents | Used For |
|----------|----------|----------|
| CVACT03Y | `CARD-XREF-RECORD` (01 level, RECLN 50): XREF-CARD-NUM PIC X(16), XREF-CUST-ID PIC 9(9), XREF-ACCT-ID PIC 9(11), FILLER PIC X(14) | Source record layout for XREFFILE reads |

### File Description Records

| FD Name       | Record Name        | Key Field                  | Layout |
|---------------|--------------------|----------------------------|--------|
| XREFFILE-FILE | FD-XREFFILE-REC    | FD-XREF-CARD-NUM PIC X(16) | FD-XREF-CARD-NUM X(16) + FD-XREF-DATA X(34) |

### Key Working Storage Variables

| Variable          | PIC         | Purpose |
|-------------------|-------------|---------|
| XREFFILE-STATUS   | X(2)        | Two-byte file status for XREFFILE |
| IO-STATUS         | X(2)        | Work area for 9910 display routine |
| APPL-RESULT       | S9(9) COMP  | Result code: 0=AOK, 16=EOF, 12=error |
| END-OF-FILE       | X(1)        | Loop control flag |
| ABCODE            | S9(9) BINARY | Abend code = 999 |
| TIMING            | S9(9) BINARY | Timing = 0 |
| TWO-BYTES-BINARY  | 9(4) BINARY  | For VSAM physical error decoding |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name  | File Object    | Org  | Access     | Open Mode | Purpose |
|----------|----------------|------|------------|-----------|---------|
| XREFFILE | XREFFILE-FILE  | KSDS | Sequential | INPUT     | Card-to-account cross-reference records |

---

## 6. Screen Interaction

None. Output is DISPLAY to SYSOUT.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| CEE3ABD        | Static CALL | LE forced abend |

---

## 8. Error Handling

| Condition                    | Action |
|------------------------------|--------|
| XREFFILE status '00'         | Normal processing |
| XREFFILE status '10' (EOF)   | END-OF-FILE = 'Y'; exit loop |
| Any other XREFFILE status    | DISPLAY error, 9910, 9999 abend |
| OPEN/CLOSE failure           | DISPLAY error, 9910, 9999 abend |

---

## 9. Business Rules

1. **Read-only diagnostic listing**: No output files are written; purely a sequential scan and print utility.
2. **Cross-reference structure**: Each CARD-XREF-RECORD links one card number (16 chars) to one customer ID (9 digits) and one account ID (11 digits). This is the XREFFILE KSDS with primary key on card number.
3. **Duplicate DISPLAY anomaly**: As noted above, each record is displayed twice due to DISPLAY statements in both the main loop body and inside 1000-XREFFILE-GET-NEXT.

---

## 10. Inputs and Outputs

### Inputs

| Source   | Description |
|----------|-------------|
| XREFFILE | KSDS VSAM card cross-reference file read sequentially |

### Outputs

| Destination | Description |
|-------------|-------------|
| SYSOUT      | DISPLAY of each CARD-XREF-RECORD (twice per record) plus start/end messages |

---

## 11. Key Variables and Their Purpose

| Variable         | Purpose |
|------------------|---------|
| CARD-XREF-RECORD | Working area (from CVACT03Y) containing XREF-CARD-NUM, XREF-CUST-ID, XREF-ACCT-ID |
| END-OF-FILE      | Loop termination flag |
| APPL-RESULT      | Maps file status to application result codes (AOK/EOF/error) |
