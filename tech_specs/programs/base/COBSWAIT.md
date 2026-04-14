# Technical Specification: COBSWAIT

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COBSWAIT                                             |
| Source File      | app/cbl/COBSWAIT.cbl                                 |
| Application      | CardDemo                                             |
| Type             | Batch COBOL Program                                  |
| Transaction ID   | N/A (batch)                                          |
| Function         | Utility wait program. ACCEPTs a wait duration value (in centiseconds) from SYSIN, moves it to MVSWAIT-TIME, and calls the 'MVSWAIT' assembler routine to suspend execution for the specified duration. Used in JCL job streams where a timed delay is needed. |

---

## 2. Program Flow

### High-Level Flow

```
START
  ACCEPT PARM-VALUE FROM SYSIN
  MOVE PARM-VALUE TO MVSWAIT-TIME
  CALL 'MVSWAIT' USING MVSWAIT-TIME
STOP RUN
```

### Paragraph-Level Detail

| Paragraph       | Lines | Description |
|-----------------|-------|-------------|
| PROCEDURE DIVISION | 34–40 | Single inline procedure: ACCEPT, MOVE, CALL, STOP RUN |

No paragraph names are defined. The entire PROCEDURE DIVISION is a single sequential block.

---

## 3. Data Structures

### Copybooks Referenced

None.

### Key Working Storage Variables

| Variable      | PIC          | Purpose |
|---------------|--------------|---------|
| MVSWAIT-TIME  | 9(8) COMP    | Binary 8-digit integer; centisecond wait duration passed to MVSWAIT |
| PARM-VALUE    | X(8)         | Raw character value read from SYSIN; moved to MVSWAIT-TIME |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name | Access | Purpose |
|---------|--------|---------|
| SYSIN   | ACCEPT | Single 8-byte value: wait duration in centiseconds |

---

## 6. Screen Interaction

None. Batch program.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| MVSWAIT        | Static CALL | IBM MVS/z/OS wait routine; suspends execution for MVSWAIT-TIME centiseconds |

**Note**: MVSWAIT is an IBM-provided routine that causes an SVC WAIT for the specified number of centiseconds. It is not a COBOL program; it is an assembler or system service routine. **[UNRESOLVED]** — MVSWAIT availability depends on z/OS system level and site-specific modules; confirm presence in the STEPLIB concatenation.

---

## 8. Error Handling

None. The program has no error checking. If SYSIN is empty or MVSWAIT-TIME is zero, MVSWAIT will be called with zero (immediate return). If MVSWAIT is not available (not in load library), the CALL will abend with S806.

---

## 9. Business Rules

1. **Centisecond units**: The wait duration is in centiseconds (1/100 of a second). For example, PARM-VALUE='00000100' waits 1 second; '00006000' waits 60 seconds.
2. **SYSIN input**: The program reads exactly one record from SYSIN (ACCEPT reads until end of record). The first 8 bytes are treated as the wait time.
3. **Single purpose**: COBSWAIT has no application logic. It exists solely to inject a timed delay in JCL job streams, typically between steps that require serialization or a settling period.

---

## 10. Inputs and Outputs

### Inputs

| Source  | Description |
|---------|-------------|
| SYSIN   | 8-byte wait duration value in centiseconds |

### Outputs

None (wait is transparent; program terminates normally after the wait).

---

## 11. Key Variables and Their Purpose

| Variable     | Purpose |
|--------------|---------|
| PARM-VALUE   | Raw input from SYSIN; character representation of centisecond wait duration |
| MVSWAIT-TIME | Binary integer form of wait duration; passed by reference to MVSWAIT |
