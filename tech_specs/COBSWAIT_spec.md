# Technical Specification: COBSWAIT — Batch Wait Utility Program

## 1. Executive Summary

COBSWAIT is a batch COBOL utility program in the CardDemo application whose sole function is to introduce a controlled pause (sleep/wait) during batch job execution. The program reads a wait duration value in centiseconds from the SYSIN DD stream, converts it to a binary numeric field, and passes it to the IBM z/OS service program MVSWAIT via a static COBOL CALL. The program is useful in batch job streams where a delay between steps is required — for example, to allow a prior step's output to be committed to disk before the next step reads it, or to pace job execution in test environments.

Source file: `app/cbl/COBSWAIT.cbl`
Version stamp: Not present (no version stamp in source; file header at line 22 shows sequence numbers)

---

## 2. Artifact Inventory

| Artifact | Type | Location | Role |
|---|---|---|---|
| COBSWAIT.cbl | Batch COBOL Program | app/cbl/ | Wait utility |
| MVSWAIT | IBM z/OS System Service | System load library | External wait routine (not available for inspection) |

No copybooks are referenced. No COPY statements appear in the source.

---

## 3. Program Identity

| Attribute | Value | Source Reference |
|---|---|---|
| PROGRAM-ID | COBSWAIT | COBSWAIT.cbl line 23 |
| Type | Batch COBOL Program | COBSWAIT.cbl line 4 |
| Function | Timed wait (pause) in centiseconds | COBSWAIT.cbl line 5 |
| CICS | None — no CICS commands | Entire source |
| Called By | JCL job steps (EXEC PGM=COBSWAIT) | Inferred from batch type |

---

## 4. Data Division

### 4.1 Working-Storage Section (lines 28–32)

| Field | PIC | Purpose |
|---|---|---|
| MVSWAIT-TIME | PIC 9(8) COMP | Binary wait duration in centiseconds; passed to MVSWAIT |
| PARM-VALUE | PIC X(8) | Character string read from SYSIN; holds wait value |

**Key constraint**: PARM-VALUE is PIC X(8) — the input must be 8 characters or fewer. MVSWAIT-TIME is PIC 9(8) COMP (a 4-byte binary field), capable of holding values 0 through 99,999,999 centiseconds.

No ENVIRONMENT DIVISION / INPUT-OUTPUT SECTION is populated beyond the declaration at line 25. No SELECT/ASSIGN statements are present — SYSIN is accessed via the ACCEPT verb, not a COBOL file.

### 4.2 Linkage Section

None. COBSWAIT is a main program (STOP RUN at line 40), not a subprogram.

---

## 5. PROCEDURE DIVISION (lines 34–40)

```cobol
PROCEDURE DIVISION.

    ACCEPT PARM-VALUE      FROM SYSIN.
    MOVE  PARM-VALUE       TO MVSWAIT-TIME.
    CALL 'MVSWAIT'       USING MVSWAIT-TIME.

    STOP RUN.
```

The entire program logic is four statements:

### Statement 1: ACCEPT PARM-VALUE FROM SYSIN (line 36)

Reads the first 80-byte record from the SYSIN DD stream into PARM-VALUE (first 8 characters used; remainder of the 80-byte input record is ignored because PARM-VALUE is only 8 bytes). The SYSIN DD must be supplied in the executing JCL as an inline data stream or a dataset.

### Statement 2: MOVE PARM-VALUE TO MVSWAIT-TIME (line 37)

Moves the 8-character alphanumeric field PARM-VALUE to the binary numeric MVSWAIT-TIME (PIC 9(8) COMP). This is an alphanumeric-to-numeric MOVE. In COBOL, moving an alphanumeric field to a numeric field performs a de-editing / conversion. If PARM-VALUE contains a numeric string (e.g., '00006000'), the binary integer 6000 (60 seconds) is placed in MVSWAIT-TIME. If PARM-VALUE contains non-numeric characters, the result is implementation-defined and may cause an abnormal termination.

### Statement 3: CALL 'MVSWAIT' USING MVSWAIT-TIME (line 38)

Static CALL to IBM z/OS load module MVSWAIT, passing MVSWAIT-TIME BY REFERENCE (default). MVSWAIT is an IBM-supplied utility that suspends the calling task for the specified number of centiseconds. MVSWAIT must be available in the job's STEPLIB, JOBLIB, or link pack area.

[ARTIFACT NOT AVAILABLE FOR INSPECTION: MVSWAIT]. This is an IBM system-supplied routine; its source is not part of the CardDemo codebase.

### Statement 4: STOP RUN (line 40)

Terminates the program and returns control to the operating system with return code 0 (normal completion, assuming MVSWAIT does not alter RETURN-CODE).

---

## 6. Program Flow Diagram

```
JCL: EXEC PGM=COBSWAIT
     //SYSIN DD *
     00006000
     /*
           |
           v
     ACCEPT PARM-VALUE FROM SYSIN
     (reads '00006000' into PARM-VALUE)
           |
           v
     MOVE PARM-VALUE TO MVSWAIT-TIME
     (MVSWAIT-TIME = 6000 binary)
           |
           v
     CALL 'MVSWAIT' USING MVSWAIT-TIME
     (program suspends for 6000 centiseconds = 60 seconds)
           |
           v
     STOP RUN
     (return code 0 to JCL)
```

---

## 7. Time Unit Reference

| SYSIN Value | Centiseconds | Duration |
|---|---|---|
| 00000100 | 100 | 1 second |
| 00000500 | 500 | 5 seconds |
| 00006000 | 6000 | 60 seconds (1 minute) |
| 00060000 | 60000 | 600 seconds (10 minutes) |
| 99999999 | 99,999,999 | ~277.8 hours (maximum) |

---

## 8. JCL Usage Pattern

Typical usage within a batch job stream:

```jcl
//WAITSTEP EXEC PGM=COBSWAIT
//STEPLIB  DD DSN=AWS.M2.CARDDEMO.LOAD,DISP=SHR
//SYSOUT   DD SYSOUT=*
//SYSIN    DD *
00000500
/*
```

This example waits 5 seconds before the next job step executes.

No other DD statements are required for COBSWAIT to function. The SYSOUT DD is for diagnostic/message output if MVSWAIT writes any.

---

## 9. Inter-Program Interactions

| Direction | Mechanism | Target | Condition | Source Reference |
|---|---|---|---|---|
| Calls | COBOL CALL (static) | MVSWAIT (IBM z/OS) | Always | COBSWAIT.cbl line 38 |
| Called by | JCL EXEC PGM= | COBSWAIT | Any batch job requiring a delay | Inferred from batch type |

---

## 10. Error Handling

COBSWAIT performs no error handling whatsoever. There are no EVALUATE, IF, or CICS error-handling constructs. Possible failure scenarios:

| Failure Mode | Behavior |
|---|---|
| SYSIN not available | ACCEPT FROM SYSIN fails; system abend (typically S001 or S013 depending on JCL error) |
| PARM-VALUE non-numeric | MOVE to MVSWAIT-TIME results in unpredictable binary value; MVSWAIT may wait for an unintended duration or abend |
| MVSWAIT not found in load library | Dynamic loader fails; S806 program not found abend |
| MVSWAIT returns non-zero | RETURN-CODE may be set non-zero; no COBOL handling present |

---

## 11. Business Rules

There are no business rules per se in this utility program. The single operational rule is:

| Rule | Implementation | Source Reference |
|---|---|---|
| Wait duration in centiseconds is supplied via SYSIN | ACCEPT FROM SYSIN reads the first 8 characters | Line 36 |
| Duration is passed directly to MVSWAIT without validation | No range checks or numeric validation | Lines 37–38 |

---

## 12. Relationship to Other CardDemo Programs

COBSWAIT is a standalone batch utility. It has no relationship to the CICS online programs (COBIL00C, CORPT00C, etc.) at the source level. Its presence in the CardDemo codebase suggests it is used in batch job streams that process transaction data — for example:

- After a VSAM file update job, before a job that reads those updates.
- Between job steps in environments where file system delays occur.
- In test/simulation scenarios requiring paced execution.

No direct evidence of COBSWAIT invocation is present in the analyzed JCL or other program sources within the codebase. [ARTIFACT NOT AVAILABLE FOR INSPECTION: Any JCL referencing COBSWAIT as EXEC PGM=COBSWAIT].

---

## 13. Open Questions and Gaps

1. **MVSWAIT not available for inspection**: [ARTIFACT NOT AVAILABLE FOR INSPECTION: MVSWAIT]. Its exact behavior, return codes, and centisecond resolution are assumed from IBM documentation. The actual load module must be available in the production STEPLIB/LPALST for COBSWAIT to function.
2. **No numeric validation**: The MOVE PARM-VALUE TO MVSWAIT-TIME will silently corrupt the wait duration if SYSIN contains non-numeric data. Adding an IF PARM-VALUE IS NUMERIC guard would improve robustness.
3. **ACCEPT FROM SYSIN reads exactly one record**: If the SYSIN DD contains multiple records, only the first is read. Subsequent records are ignored.
4. **Return code not set explicitly**: COBSWAIT does not set RETURN-CODE. If MVSWAIT alters RETURN-CODE or if COBSWAIT abends, the JCL COND= parameter on subsequent steps must account for this.
5. **Sequence numbers in source**: Lines 22, 23, 25, 34, 40 contain trailing sequence numbers (e.g., `00010000`, `0002000`, `00030000`), which is a legacy IBM source management artifact. This is informational only.
