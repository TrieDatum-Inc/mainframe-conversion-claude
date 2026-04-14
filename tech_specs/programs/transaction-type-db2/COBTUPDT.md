# Technical Specification: COBTUPDT

## Program Overview

| Attribute         | Value                                                             |
|-------------------|-------------------------------------------------------------------|
| Program ID        | COBTUPDT                                                          |
| Source File       | app/app-transaction-type-db2/cbl/COBTUPDT.cbl                     |
| Language          | COBOL with embedded static DB2 SQL                                |
| Environment       | Batch (non-CICS)                                                  |
| Function          | Batch maintenance of CARDDEMO.TRANSACTION_TYPE table              |
| Layer             | Business logic — batch DML                                        |
| Associated JCL    | MNTTRDB2.jcl                                                      |
| DB2 Plan          | CARDDEMO (run via DSN RUN PROGRAM command in MNTTRDB2.jcl)        |

### Purpose

COBTUPDT is a batch COBOL program that reads a sequential input file record by record and applies INSERT, UPDATE, or DELETE operations to the `CARDDEMO.TRANSACTION_TYPE` DB2 table based on a transaction-type indicator in column 1 of each input record. It is the batch counterpart to the online CICS programs COTRTLIC and COTRTUPC.

---

## Program Flow

### High-Level Control Flow

```
0001-OPEN-FILES
    |
    +--> OPEN INPUT TR-RECORD
    |
    v
1001-READ-NEXT-RECORDS
    |
    +--> PERFORM 1002-READ-RECORDS        (prime read)
    |
    +--> PERFORM UNTIL LASTREC = 'Y'
    |         PERFORM 1003-TREAT-RECORD
    |         PERFORM 1002-READ-RECORDS
    |    END-PERFORM
    |
    +--> PERFORM 2001-CLOSE-STOP
    |
    v
STOP RUN
```

### Paragraph Reference

| Paragraph             | Line     | Description                                                        |
|-----------------------|----------|--------------------------------------------------------------------|
| 0001-OPEN-FILES       | 82-89    | Opens the sequential input file; checks WS-INF-STATUS = '00'      |
| 1001-READ-NEXT-RECORDS| 91-98    | Main loop controller: primes read, iterates until EOF              |
| 1002-READ-RECORDS     | 100-107  | Reads next record INTO WS-INPUT-REC; sets LASTREC='Y' at AT END   |
| 1003-TREAT-RECORD     | 109-130  | EVALUATE on INPUT-REC-TYPE: routes A/U/D/* or abends on OTHER      |
| 10031-INSERT-DB       | 132-164  | Executes INSERT INTO TRANSACTION_TYPE                              |
| 10032-UPDATE-DB       | 166-195  | Executes UPDATE TRANSACTION_TYPE                                   |
| 10033-DELETE-DB       | 196-226  | Executes DELETE FROM TRANSACTION_TYPE                              |
| 9999-ABEND            | 230-233  | Displays WS-RETURN-MSG; sets RETURN-CODE = 4                       |
| 2001-CLOSE-STOP       | 234-236  | Closes the input file                                              |

### Processing Logic Detail

**1003-TREAT-RECORD (lines 109-130):**
```
EVALUATE INPUT-REC-TYPE (= first byte of WS-INPUT-REC)
    WHEN 'A'  --> PERFORM 10031-INSERT-DB
    WHEN 'U'  --> PERFORM 10032-UPDATE-DB
    WHEN 'D'  --> PERFORM 10033-DELETE-DB
    WHEN '*'  --> DISPLAY 'IGNORING COMMENTED LINE'  (no action)
    WHEN OTHER --> STRING error text INTO WS-RETURN-MSG
                   PERFORM 9999-ABEND
END-EVALUATE
```

---

## Data Structures

### FILE SECTION

| Name           | Level | PIC          | Description                                                       |
|----------------|-------|--------------|-------------------------------------------------------------------|
| TR-RECORD      | FD    | RECORDING F  | Input sequential file (ASSIGN to INPFILE)                         |
| WS-INPUT-VARS  | 01    |              | FD-level record layout (pre-WORKING-STORAGE, lines 40-47)         |
| INPUT-TYPE     | 05    | X(1)         | Record type: A/U/D/*                                              |
| INPUT-TR-NUMBER| 05    | X(2)         | Transaction type code (2-character numeric)                       |
| INPUT-TR-DESC  | 05    | X(50)        | Transaction description (up to 50 characters)                     |

**Note:** The FD record is defined with level-01 name `WS-INPUT-VARS` directly under the FD. This means the READ INTO target `WS-INPUT-REC` (WORKING-STORAGE) receives the data; `WS-INPUT-VARS` is the buffer but `WS-INPUT-REC` is used for all processing (lines 100-101, 110).

### WORKING-STORAGE SECTION

| Name                | Level | PIC       | Description                                              |
|---------------------|-------|-----------|----------------------------------------------------------|
| SQLCA               | EXEC  | SQL INCL  | Standard CICS/DB2 SQL Communication Area                 |
| DCLTRANSACTION-TYPE | EXEC  | SQL INCL  | DCLGEN for CARDDEMO.TRANSACTION_TYPE (from DCLTRTYP.dcl) |
| LASTREC             | 05    | X(1)      | EOF flag; set to 'Y' by AT END on READ                   |
| WS-RETURN-MSG       | 05    | X(80)     | Error message buffer for abend display                   |
| WS-VAR-SQLCODE      | 05    | PIC ----9 | Formatted SQLCODE for display (sign-suppressed)          |
| WS-INF-STATUS       | 01    | XX        | File status: WS-INF-STAT1 (X) + WS-INF-STAT2 (X)        |
| WS-INPUT-REC        | 01    |           | Working copy of input record read from file              |
| INPUT-REC-TYPE      | 05    | X(1)      | Operation code: A, U, D, *                               |
| INPUT-REC-NUMBER    | 05    | X(2)      | Transaction type code (key column)                       |
| INPUT-REC-DESC      | 05    | X(50)     | Transaction description (non-key)                        |

### DB2 Host Variables (from DCLTRTYP.dcl)

| COBOL Name               | DB2 Column       | Type        | Length |
|--------------------------|------------------|-------------|--------|
| DCL-TR-TYPE              | TR_TYPE          | CHAR(2)     | 2      |
| DCL-TR-DESCRIPTION       | TR_DESCRIPTION   | VARCHAR(50) | 50+2   |
| DCL-TR-DESCRIPTION-LEN   | (VARCHAR length) | S9(4) COMP  | 2      |
| DCL-TR-DESCRIPTION-TEXT  | (VARCHAR text)   | X(50)       | 50     |

**Note:** The INSERT and DELETE statements use `:INPUT-REC-NUMBER` and `:INPUT-REC-DESC` as host variables directly (lines 145-146, 173-174, 202-203). This is valid because COBOL working-storage fields can serve as DB2 host variables if declared in WORKING-STORAGE.

---

## CICS/DB2 Commands

### DB2 SQL Operations

**INSERT (paragraph 10031-INSERT-DB, lines 137-148):**
```sql
INSERT INTO CARDDEMO.TRANSACTION_TYPE
    (TR_TYPE, TR_DESCRIPTION)
VALUES (:INPUT-REC-NUMBER, :INPUT-REC-DESC)
```
- Host variable `:INPUT-REC-NUMBER` maps to `WS-INPUT-REC.INPUT-REC-NUMBER` (PIC X(2))
- Host variable `:INPUT-REC-DESC` maps to `WS-INPUT-REC.INPUT-REC-DESC` (PIC X(50))

**UPDATE (paragraph 10032-UPDATE-DB, lines 171-175):**
```sql
UPDATE CARDDEMO.TRANSACTION_TYPE
   SET TR_DESCRIPTION = :INPUT-REC-DESC
 WHERE TR_TYPE = :INPUT-REC-NUMBER
```

**DELETE (paragraph 10033-DELETE-DB, lines 200-204):**
```sql
DELETE FROM CARDDEMO.TRANSACTION_TYPE
 WHERE TR_TYPE = :INPUT-REC-NUMBER
```

### SQLCODE Handling Per Paragraph

| Paragraph      | SQLCODE = 0       | SQLCODE = +100        | SQLCODE < 0            |
|----------------|-------------------|-----------------------|------------------------|
| 10031-INSERT-DB| DISPLAY success   | Not checked           | STRING error, ABEND    |
| 10032-UPDATE-DB| DISPLAY success   | STRING "No records", ABEND | STRING error, ABEND |
| 10033-DELETE-DB| DISPLAY success   | STRING "No records", ABEND | STRING error, ABEND |

---

## File Access

### Input File

| DD Name  | Usage    | Organization | Access | Record Length | Description              |
|----------|----------|--------------|--------|---------------|--------------------------|
| INPFILE  | INPUT    | SEQUENTIAL   | SEQ    | 53 bytes      | Batch transaction maintenance records |

**Record Layout (53 bytes total):**

| Column   | Field Name         | Length | Type    | Values       |
|----------|--------------------|--------|---------|--------------|
| 1        | INPUT-REC-TYPE     | 1      | Alpha   | A, U, D, *   |
| 2-3      | INPUT-REC-NUMBER   | 2      | Numeric | 01-99 (2-digit transaction type code) |
| 4-53     | INPUT-REC-DESC     | 50     | Alpha   | Transaction description text |

Source: MNTTRDB2.jcl comments (lines 8-19) and FD layout (lines 40-47, 71-77).

### No Output Files

The program has no output files. All output is written to DB2 via embedded SQL. Messages are written to SYSOUT via DISPLAY statements.

---

## Screen Interaction

None. COBTUPDT is a batch program with no CICS interaction.

---

## Called Programs

None. COBTUPDT is self-contained; it does not CALL or LINK to any external programs.

---

## Error Handling

### File Open Error
- **Where:** Paragraph 0001-OPEN-FILES (lines 84-89)
- **Detection:** IF WS-INF-STATUS NOT = '00'
- **Action:** DISPLAY 'OPEN FILE NOT OK' — processing continues (no abend on open failure; this is a documentation gap as the program does not terminate here)

### AT END (End of File)
- **Where:** Paragraph 1002-READ-RECORDS (lines 101-103)
- **Detection:** AT END MOVE 'Y' TO LASTREC
- **Action:** Loop terminates; 2001-CLOSE-STOP is performed

### Invalid Record Type
- **Where:** Paragraph 1003-TREAT-RECORD (lines 122-128)
- **Detection:** WHEN OTHER in EVALUATE
- **Action:** STRING error message INTO WS-RETURN-MSG; PERFORM 9999-ABEND

### DB2 SQLCODE < 0 (fatal DB2 error)
- **Where:** Paragraphs 10031, 10032, 10033
- **Detection:** WHEN SQLCODE < 0
- **Action:** STRING error text including table name and WS-VAR-SQLCODE into WS-RETURN-MSG; PERFORM 9999-ABEND

### DB2 SQLCODE = +100 (row not found for UPDATE/DELETE)
- **Where:** Paragraphs 10032 and 10033
- **Detection:** WHEN SQLCODE = +100
- **Action:** STRING 'No records found.' into WS-RETURN-MSG; PERFORM 9999-ABEND

### 9999-ABEND Paragraph (lines 230-233)
- DISPLAY WS-RETURN-MSG to SYSOUT
- MOVE 4 TO RETURN-CODE
- EXIT (program does NOT stop; calling loop continues)

**Critical Note:** The ABEND paragraph does NOT issue STOP RUN. It sets RETURN-CODE=4 and returns. After 9999-ABEND, the EVALUATE falls through to EXIT, and 1001-READ-NEXT-RECORDS continues processing the next record. This means a single bad record does not terminate the job; processing continues. The job step RC will reflect the highest RETURN-CODE set.

---

## Business Rules

1. **Record type 'A':** Unconditional INSERT into TRANSACTION_TYPE. No pre-existence check; a duplicate key will cause SQLCODE < 0 and trigger ABEND with RC=4.

2. **Record type 'U':** UPDATE of TR_DESCRIPTION keyed by TR_TYPE. If the row does not exist (SQLCODE=+100), ABEND with RC=4. No INSERT fallback in batch (unlike the CICS online program COTRTUPC which attempts INSERT on +100).

3. **Record type 'D':** DELETE keyed by TR_TYPE. If the row does not exist (SQLCODE=+100), ABEND with RC=4. Referential integrity violations (SQLCODE=-532 from the FK constraint to TRANSACTION_TYPE_CATEGORY) are caught by the SQLCODE < 0 branch.

4. **Record type '*':** Comment line — ignored with DISPLAY message, no DB2 operation.

5. **Any other value in column 1:** ABEND with RC=4 and error message.

6. **No COMMIT is issued.** The batch program does not issue SQL COMMIT. Under TSO batch execution via DSN RUN PROGRAM, all changes run under a single unit of work. Whether this is committed or rolled back depends on the job step completion code and the DB2 DSN processor behavior on normal/abnormal termination.

---

## Input/Output Specification

### Input Record (INPFILE)

```
Position  Length  Field              Description
1         1       Operation Type     A=Add, U=Update, D=Delete, *=Comment
2-3       2       TR_TYPE            Transaction type code (must be numeric)
4-53      50      TR_DESCRIPTION     Description text
```

### Output

- SYSOUT messages via DISPLAY:
  - 'OPEN FILE OK' or 'OPEN FILE NOT OK' on file open
  - 'PROCESSING   ' + record image for each non-EOF record
  - 'ADDING RECORD', 'UPDATING RECORD', 'DELETING RECORD' per operation
  - 'RECORD INSERTED/UPDATED/DELETED SUCCESSFULLY' on success
  - Error text in WS-RETURN-MSG on failure
- DB2 table CARDDEMO.TRANSACTION_TYPE is updated in place
- RETURN-CODE = 4 on any error

### JCL Execution Context (from MNTTRDB2.jcl)

```
//STEP1   EXEC PGM=IKJEFT01,REGION=0M
//STEPLIB  DD DISP=SHR,DSN=OEM.DB2.DAZ1.SDSNEXIT
//         DD DISP=SHR,DSN=OEMA.DB2.VERSIONA.SDSNLOAD
//         DD DISP=SHR,DSN=AWS.M2.CARDDEMO.LOADLIB
//DBRMLIB  DD DISP=SHR,DSN=AWS.M2.CARDDEMO.DBRMLIB
//SYSTSPRT DD  SYSOUT=*
//INPFILE  DD  DSN=INPFILE,DISP=SHR
//SYSTSIN DD *
     DSN SYSTEM(DAZ1)
          RUN PROGRAM(COBTUPDT) PLAN(CARDDEMO)
```

The program runs under IKJEFT01 (TSO) using the DSN command processor. DB2 subsystem is DAZ1. The DBRM is bound into plan CARDDEMO.

---

## Copybook Dependencies

| Copybook    | Source                                           | Content                                          |
|-------------|--------------------------------------------------|--------------------------------------------------|
| SQLCA       | DB2 system (EXEC SQL INCLUDE SQLCA, line 51-53)  | SQL Communication Area — SQLCODE, SQLERRM, etc.  |
| DCLTRTYP    | dcl/DCLTRTYP.dcl (EXEC SQL INCLUDE, line 54)     | DCLGEN for CARDDEMO.TRANSACTION_TYPE             |

**[UNRESOLVED]** CSUTLDWY is referenced by COPY 'CSUTLDWY' in COTRTUPC (line 76) but NOT in COBTUPDT. COBTUPDT has no COPY for date utilities.

---

## Known Gaps and Anomalies

1. **No COMMIT in batch:** All DB2 changes accumulate in a single UOW. For large input files this risks lock escalation and log full conditions.

2. **Open failure does not terminate:** If INPFILE fails to open, the program displays an error but proceeds to the READ loop, which will immediately fail at the first READ statement.

3. **9999-ABEND does not stop processing:** After setting RETURN-CODE=4 and displaying the error, processing resumes with the next record. This is intentional for "best-effort" batch processing but means subsequent successful records could partially counteract a failed operation.

4. **No rollback on error:** On SQLCODE < 0 errors, the program abends (sets RC=4) but does not issue a SQL ROLLBACK. Prior successful operations in the same job step are not rolled back.

5. **Host variable mismatch:** The DB2 DCL defines `DCL-TR-TYPE PIC X(2)` and `DCL-TR-DESCRIPTION` as VARCHAR(50). The INSERT/DELETE use `:INPUT-REC-NUMBER` (X(2)) and `:INPUT-REC-DESC` (X(50)) as host variables rather than the DCL-prefixed names. This is legal in COBOL DB2 but bypasses the DCLGEN-generated variable layout.
