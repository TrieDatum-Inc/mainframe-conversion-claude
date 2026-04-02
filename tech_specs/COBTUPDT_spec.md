# Technical Specification: COBTUPDT

## 1. Executive Summary

COBTUPDT is a **batch COBOL program** in the Transaction Type DB2 subsystem of the CardDemo application. It reads a sequential flat file of transaction-type maintenance records and applies insert, update, or delete operations to the `CARDDEMO.TRANSACTION_TYPE` DB2 table. Each record in the input file carries a single-character operation code (`A`, `U`, `D`, or `*`) that determines the SQL action taken. The program is entirely non-interactive (no CICS, no BMS), operating as a pure batch utility for bulk maintenance of the transaction-type reference table.

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COBTUPDT.cbl | COBOL batch program | `app/app-transaction-type-db2/cbl/COBTUPDT.cbl` |
| DCLTRTYP | DB2 DCLGEN table declaration | Included via `EXEC SQL INCLUDE DCLTRTYP` (not available for inspection) |
| SQLCA | DB2 SQL Communications Area | Included via `EXEC SQL INCLUDE SQLCA` |

> [ARTIFACT NOT AVAILABLE FOR INSPECTION: DCLTRTYP]. The DCLGEN-generated host-variable declarations for `CARDDEMO.TRANSACTION_TYPE` are referenced at line 54 but the source member was not provided. Analysis of the exact column names and host-variable PIC clauses declared therein is incomplete.

---

## 3. Program Identity

| Attribute | Value | Source |
|---|---|---|
| Program-ID | COBTUPDT | Line 23 |
| Layer | Business logic | Line 3 |
| Function | Update Transaction Type based on user input | Line 4 |
| Invocation type | Batch (STOP RUN at line 99) | Lines 97-99 |
| Transaction ID | None — batch only | N/A |
| CICS commands | None | N/A |

---

## 4. ENVIRONMENT DIVISION — File Assignments

| Logical File | DD Name | Organization | Access | Status Field |
|---|---|---|---|---|
| TR-RECORD | INPFILE | Sequential | Sequential | WS-INF-STATUS (PIC XX) |

Source: lines 31-34 (`SELECT TR-RECORD ASSIGN TO INPFILE`).

---

## 5. DATA DIVISION

### 5.1 FILE SECTION — Input Record (FD TR-RECORD, lines 39-47)

| Field | PIC | Offset | Description |
|---|---|---|---|
| INPUT-TYPE | X(1) | 1 | Operation code (defined in FD but superseded by WS-INPUT-REC) |
| INPUT-TR-NUMBER | X(2) | 2 | Transaction type code (2-digit) |
| INPUT-TR-DESC | X(50) | 4 | Transaction description (50 chars) |

Note: The FD record is 53 bytes. The program reads INTO `WS-INPUT-REC` (lines 71-77), which redefines the same layout under working-storage names.

### 5.2 WORKING-STORAGE SECTION

| Group | Field | PIC | Purpose |
|---|---|---|---|
| WS-INPUT-REC | INPUT-REC-TYPE | X(1) | Target area for READ INTO — operation code |
| WS-INPUT-REC | INPUT-REC-NUMBER | X(2) | Target area — transaction type code |
| WS-INPUT-REC | INPUT-REC-DESC | X(50) | Target area — transaction description |
| FLAGS | LASTREC | X(1) | End-of-file flag; 'Y' = EOF |
| WORKING-VARIABLES | WS-RETURN-MSG | X(80) | Error message accumulation |
| WS-MISC-VARS | WS-VAR-SQLCODE | PIC ----9 | Signed display SQLCODE for messages |
| WS-INF-STATUS | WS-INF-STAT1 | X(1) | First byte of file status |
| WS-INF-STATUS | WS-INF-STAT2 | X(1) | Second byte of file status |
| SQLCA | (DB2 supplied) | — | SQLCODE, SQLERRM, etc. |
| DCLTRTYP | (DB2 DCLGEN) | — | Host variables for TRANSACTION_TYPE columns |

---

## 6. DB2 SQL Statements

### 6.1 Table Operated Upon

| Table | Schema | Operations |
|---|---|---|
| TRANSACTION_TYPE | CARDDEMO | INSERT, UPDATE, DELETE |

### 6.2 INSERT (paragraph 10031-INSERT-DB, lines 132-164)

```sql
INSERT INTO CARDDEMO.TRANSACTION_TYPE
  ( TR_TYPE, TR_DESCRIPTION )
  VALUES
  ( :INPUT-REC-NUMBER, :INPUT-REC-DESC )
```

Host variables: `:INPUT-REC-NUMBER` (PIC X(2)), `:INPUT-REC-DESC` (PIC X(50)).

SQLCODE handling:
- `= 0`: Displays "RECORD INSERTED SUCCESSFULLY"
- `< 0`: Formats error message and PERFORMs `9999-ABEND`

### 6.3 UPDATE (paragraph 10032-UPDATE-DB, lines 166-195)

```sql
UPDATE CARDDEMO.TRANSACTION_TYPE
   SET TR_DESCRIPTION = :INPUT-REC-DESC
 WHERE TR_TYPE        = :INPUT-REC-NUMBER
```

SQLCODE handling:
- `= 0`: Displays "RECORD UPDATED SUCCESSFULLY"
- `= +100`: Sets "No records found." in WS-RETURN-MSG, PERFORMs `9999-ABEND`
- `< 0`: Formats error message, PERFORMs `9999-ABEND`

### 6.4 DELETE (paragraph 10033-DELETE-DB, lines 196-226)

```sql
DELETE FROM CARDDEMO.TRANSACTION_TYPE
 WHERE TR_TYPE = :INPUT-REC-NUMBER
```

SQLCODE handling:
- `= 0`: Displays "RECORD DELETED SUCCESSFULLY"
- `= +100`: Sets "No records found." in WS-RETURN-MSG, PERFORMs `9999-ABEND`
- `< 0`: Formats error message, PERFORMs `9999-ABEND`

> No COMMIT or ROLLBACK logic is present in this program. DB2 unit-of-work management is delegated to the JCL step or the DB2 subsystem default.

---

## 7. PROCEDURE DIVISION — Paragraph-by-Paragraph Logic

### Control Flow Diagram

```
0001-OPEN-FILES
       |
       v
1001-READ-NEXT-RECORDS  <--- entry point
       |
       v
  1002-READ-RECORDS (prime read)
       |
       v
  [PERFORM UNTIL LASTREC = 'Y']
       |
       +---> 1003-TREAT-RECORD
       |           |
       |           +--[A]--> 10031-INSERT-DB
       |           +--[U]--> 10032-UPDATE-DB
       |           +--[D]--> 10033-DELETE-DB
       |           +--[*]--> DISPLAY 'IGNORING COMMENTED LINE'
       |           +--[OTHER]--> 9999-ABEND
       |
       +---> 1002-READ-RECORDS (next read)
       |
  [END-PERFORM]
       |
       v
  2001-CLOSE-STOP
       |
       v
  EXIT / STOP RUN
```

### Paragraph Descriptions

**0001-OPEN-FILES** (lines 82-89)
- Issues `OPEN INPUT TR-RECORD`
- Checks `WS-INF-STATUS`; displays "OPEN FILE OK" or "OPEN FILE NOT OK"
- Does not abend on open failure — processing continues regardless

**1001-READ-NEXT-RECORDS** (lines 91-98)
- Issues a priming call to `1002-READ-RECORDS`
- Loops UNTIL `LASTREC = 'Y'`, calling `1003-TREAT-RECORD` then `1002-READ-RECORDS` each iteration
- PERFORMs `2001-CLOSE-STOP` when loop exits
- The `STOP RUN` at line 99 is unreachable (after `2001-CLOSE-STOP` EXIT)

**1002-READ-RECORDS** (lines 100-107)
- Issues `READ TR-RECORD NEXT RECORD INTO WS-INPUT-REC`
- AT END: moves 'Y' to LASTREC
- If not at EOF, displays WS-INPUT-REC content via DISPLAY

**1003-TREAT-RECORD** (lines 109-130)
- EVALUATE on INPUT-REC-TYPE:
  - `'A'` — PERFORMs `10031-INSERT-DB`
  - `'U'` — PERFORMs `10032-UPDATE-DB`
  - `'D'` — PERFORMs `10033-DELETE-DB`
  - `'*'` — displays "IGNORING COMMENTED LINE" (comment line support)
  - OTHER — STRINGs "ERROR: TYPE NOT VALID" into WS-RETURN-MSG, PERFORMs `9999-ABEND`

**10031-INSERT-DB** (lines 132-164) — see SQL section 6.2

**10032-UPDATE-DB** (lines 166-195) — see SQL section 6.3

**10033-DELETE-DB** (lines 196-226) — see SQL section 6.4

**9999-ABEND** (lines 230-233)
- DISPLAYs WS-RETURN-MSG
- MOVEs 4 to RETURN-CODE (sets batch step condition code to 4)
- Does NOT issue STOP RUN or ABEND — returns to caller
- This means processing continues after an error record; subsequent records are still processed

**2001-CLOSE-STOP** (lines 234-236)
- `CLOSE TR-RECORD`

---

## 8. Input File Format

The input file (DD INPFILE) is a fixed-format sequential file. Each record is 53 bytes:

| Position | Length | Field | Values |
|---|---|---|---|
| 1 | 1 | Operation Code | `A`=Add, `U`=Update, `D`=Delete, `*`=Comment |
| 2-3 | 2 | Transaction Type Code | 2-character alphanumeric |
| 4-53 | 50 | Transaction Description | Free-text description |

---

## 9. Error Handling

| Condition | Action | Return Code |
|---|---|---|
| File open failure | Displays message, continues processing | None set |
| Invalid record type | Formats "ERROR: TYPE NOT VALID", calls 9999-ABEND | RC=4 |
| INSERT SQLCODE < 0 | Formats DB2 error message, calls 9999-ABEND | RC=4 |
| UPDATE SQLCODE = +100 | Sets "No records found.", calls 9999-ABEND | RC=4 |
| UPDATE SQLCODE < 0 | Formats DB2 error message, calls 9999-ABEND | RC=4 |
| DELETE SQLCODE = +100 | Sets "No records found.", calls 9999-ABEND | RC=4 |
| DELETE SQLCODE < 0 | Formats DB2 error message, calls 9999-ABEND | RC=4 |

Key design note: `9999-ABEND` only sets RETURN-CODE to 4 and exits to caller. It does NOT stop the program. After an error record, the next record in the input file will still be processed.

---

## 10. VSAM File Operations

None. This program does not access any VSAM files.

---

## 11. CICS Commands

None. This is a pure batch program.

---

## 12. MQ Operations

None.

---

## 13. Copybooks Referenced

| Copybook | INCLUDE Type | Purpose | Available? |
|---|---|---|---|
| SQLCA | `EXEC SQL INCLUDE SQLCA` | DB2 SQL Communications Area | Standard IBM-supplied |
| DCLTRTYP | `EXEC SQL INCLUDE DCLTRTYP` | DCLGEN host variables for TRANSACTION_TYPE | NOT AVAILABLE FOR INSPECTION |

---

## 14. Inter-Program Interactions

None. COBTUPDT does not CALL, LINK, or XCTL to any other program. It is a self-contained batch utility.

---

## 15. Transaction Flows It Participates In

COBTUPDT participates only in batch job flows. It is the batch counterpart to the online programs COTRTLIC and COTRTUPC, which maintain the same `CARDDEMO.TRANSACTION_TYPE` table interactively via CICS. The expected JCL invocation would be:

```
//STEP1   EXEC PGM=COBTUPDT
//STEPLIB  DD  DSN=...load library...
//INPFILE  DD  DSN=...input dataset...,DISP=SHR
//SYSOUT   DD  SYSOUT=*
```

[ARTIFACT NOT AVAILABLE FOR INSPECTION: JCL invoking COBTUPDT]. No JCL member was provided in the analyzed artifacts.

---

## 16. Open Questions and Gaps

1. **DCLTRTYP copybook**: The DCLGEN member is not available. The exact host-variable names used in SQL statements (`:INPUT-REC-NUMBER`, `:INPUT-REC-DESC`) appear to be the WS-INPUT-REC fields used directly as host variables without DCLGEN renaming. This is unusual and may indicate the host variables in the SQL are the WS variables themselves — verification requires the compiler output.

2. **No COMMIT logic**: The program performs no explicit DB2 COMMIT. Whether changes are committed depends entirely on the JCL step end or an external RRS/DB2 subsystem configuration. This is a risk for large input files.

3. **File open failure does not abort**: If OPEN INPUT fails (WS-INF-STATUS != '00'), the program displays a message but continues into the READ loop, which will immediately fail with a file-not-open condition. This is a latent defect.

4. **STOP RUN at line 99**: The `STOP RUN` after `2001-CLOSE-STOP` EXIT is unreachable code. Normal termination is via EXIT from `1001-READ-NEXT-RECORDS` back to the implicit end of PROCEDURE DIVISION.
