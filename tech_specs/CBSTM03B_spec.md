# Technical Specification: CBSTM03B

## 1. Executive Summary

CBSTM03B is a batch COBOL subroutine in the CardDemo application. It is not a standalone program — it is called exclusively by CBSTM03A. Its purpose is to centralize all file I/O operations for the four VSAM files used during statement generation: TRNXFILE, XREFFILE, CUSTFILE, and ACCTFILE. It receives a generic operation descriptor (DD name, operation code, key, and data area) through its LINKAGE SECTION and dispatches to the appropriate file operation. This design decouples the statement logic in CBSTM03A from the physical file I/O, allowing the file handling to be modified independently.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBSTM03B.CBL` | COBOL Batch Subroutine | File I/O delegate for CBSTM03A |

No copybooks are referenced. All file record layouts are defined inline within the FD entries.

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBSTM03B` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Subroutine |
| Function | File processing related to Transact Report (called by CBSTM03A) |
| Invocation | CALL 'CBSTM03B' USING LK-M03B-AREA |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field |
|---|---|---|---|---|
| `TRNX-FILE` | `TRNXFILE` | INDEXED (KSDS) | Sequential | `FD-TRNXS-ID` (composite: TRNX-CARD X(16) + TRNX-ID X(16)) |
| `XREF-FILE` | `XREFFILE` | INDEXED (KSDS) | Sequential | `FD-XREF-CARD-NUM` PIC X(16) |
| `CUST-FILE` | `CUSTFILE` | INDEXED (KSDS) | Random | `FD-CUST-ID` PIC X(09) |
| `ACCT-FILE` | `ACCTFILE` | INDEXED (KSDS) | Random | `FD-ACCT-ID` PIC 9(11) |

**Note on FD-CUST-ID declaration:** In CBSTM03B, `FD-CUST-ID` is declared `PIC X(09)` (alphanumeric), whereas in CVACT01Y-based programs it is `PIC 9(09)` (numeric). This is a type inconsistency in the record key declarations across programs.

---

## 5. File Section — Record Layouts

All record layouts are defined inline (no copybooks):

### 5.1 TRNX-FILE (Transactions)
```
FD TRNX-FILE.
01 FD-TRNXFILE-REC.
   05 FD-TRNXS-ID.
      10 FD-TRNX-CARD    PIC X(16)   [Part 1 of composite key: card number]
      10 FD-TRNX-ID      PIC X(16)   [Part 2 of composite key: transaction ID]
   05 FD-ACCT-DATA        PIC X(318)
```
Total record length: 350 bytes. This file is the transaction file keyed by (card_num, tran_id) — note the composite key structure differs from the TRANSACT file used by CBTRN02C and CBTRN03C, which use TRAN-ID alone as the key.

### 5.2 XREF-FILE (Card Cross-Reference)
```
FD XREF-FILE.
01 FD-XREFFILE-REC.
   05 FD-XREF-CARD-NUM    PIC X(16)
   05 FD-XREF-DATA        PIC X(34)
```
Total: 50 bytes.

### 5.3 CUST-FILE (Customer)
```
FD CUST-FILE.
01 FD-CUSTFILE-REC.
   05 FD-CUST-ID      PIC X(09)
   05 FD-CUST-DATA    PIC X(491)
```
Total: 500 bytes.

### 5.4 ACCT-FILE (Account)
```
FD ACCT-FILE.
01 FD-ACCTFILE-REC.
   05 FD-ACCT-ID      PIC 9(11)
   05 FD-ACCT-DATA    PIC X(289)
```
Total: 300 bytes.

---

## 6. Linkage Section — Call Interface

```
01 LK-M03B-AREA.
   05 LK-M03B-DD      PIC X(08)    [Target DD name: 'TRNXFILE','XREFFILE','CUSTFILE','ACCTFILE']
   05 LK-M03B-OPER    PIC X(01)    [Operation code]
     88 M03B-OPEN     VALUE 'O'    [Open file]
     88 M03B-CLOSE    VALUE 'C'    [Close file]
     88 M03B-READ     VALUE 'R'    [Sequential read]
     88 M03B-READ-K   VALUE 'K'    [Keyed (random) read]
     88 M03B-WRITE    VALUE 'W'    [Write record]
     88 M03B-REWRITE  VALUE 'Z'    [Rewrite record]
   05 LK-M03B-RC      PIC X(02)    [Return code: file status from the operation]
   05 LK-M03B-KEY     PIC X(25)    [Key value for keyed reads]
   05 LK-M03B-KEY-LN  PIC S9(4)    [Key length in bytes]
   05 LK-M03B-FLDT    PIC X(1000)  [Data area: record read INTO or written FROM]
```

This interface matches the `WS-M03B-AREA` working-storage structure in CBSTM03A.

---

## 7. Working-Storage Data Structures

Only four 2-byte file status fields are declared:

```
01 TRNXFILE-STATUS.   05 TRNXFILE-STAT1 PIC X.  05 TRNXFILE-STAT2 PIC X.
01 XREFFILE-STATUS.   05 XREFFILE-STAT1 PIC X.  05 XREFFILE-STAT2 PIC X.
01 CUSTFILE-STATUS.   05 CUSTFILE-STAT1 PIC X.  05 CUSTFILE-STAT2 PIC X.
01 ACCTFILE-STATUS.   05 ACCTFILE-STAT1 PIC X.  05 ACCTFILE-STAT2 PIC X.
```

No complex working-storage is required because all data exchange occurs through the LINKAGE SECTION.

---

## 8. Procedure Division — Program Flow

### 8.1 Entry Point and Dispatch (lines 114–131)

```
PROCEDURE DIVISION USING LK-M03B-AREA.

0000-START.
    EVALUATE LK-M03B-DD
        WHEN 'TRNXFILE'  PERFORM 1000-TRNXFILE-PROC THRU 1999-EXIT
        WHEN 'XREFFILE'  PERFORM 2000-XREFFILE-PROC THRU 2999-EXIT
        WHEN 'CUSTFILE'  PERFORM 3000-CUSTFILE-PROC THRU 3999-EXIT
        WHEN 'ACCTFILE'  PERFORM 4000-ACCTFILE-PROC THRU 4999-EXIT
        WHEN OTHER       GO TO 9999-GOBACK
    END-EVALUATE.

9999-GOBACK.
    GOBACK.
```

**Note the use of `PERFORM ... THRU ...`:** Each file processing section spans from its start paragraph to its exit paragraph (e.g., `1000-TRNXFILE-PROC THRU 1999-EXIT`). This pattern uses sequential paragraph fall-through within a range rather than nested PERFORM calls.

### 8.2 File Processing Sections

Each of the four file sections follows the same conditional operation pattern. After the operation completes, the file status is moved to `LK-M03B-RC`, which is returned to the caller.

#### TRNXFILE Section (paragraphs 1000–1999)
```
1000-TRNXFILE-PROC:
    IF M03B-OPEN   -> OPEN INPUT TRNX-FILE    -> GO TO 1900-EXIT
    IF M03B-READ   -> READ TRNX-FILE INTO LK-M03B-FLDT -> GO TO 1900-EXIT
    IF M03B-CLOSE  -> CLOSE TRNX-FILE         -> GO TO 1900-EXIT
1900-EXIT:
    MOVE TRNXFILE-STATUS TO LK-M03B-RC
1999-EXIT:  EXIT.
```

#### XREFFILE Section (paragraphs 2000–2999)
```
2000-XREFFILE-PROC:
    IF M03B-OPEN   -> OPEN INPUT XREF-FILE
    IF M03B-READ   -> READ XREF-FILE INTO LK-M03B-FLDT
    IF M03B-CLOSE  -> CLOSE XREF-FILE
2900-EXIT:
    MOVE XREFFILE-STATUS TO LK-M03B-RC
2999-EXIT:  EXIT.
```

#### CUSTFILE Section (paragraphs 3000–3999)
```
3000-CUSTFILE-PROC:
    IF M03B-OPEN    -> OPEN INPUT CUST-FILE
    IF M03B-READ-K  -> MOVE LK-M03B-KEY(1:LK-M03B-KEY-LN) TO FD-CUST-ID
                       READ CUST-FILE INTO LK-M03B-FLDT
    IF M03B-CLOSE   -> CLOSE CUST-FILE
3900-EXIT:
    MOVE CUSTFILE-STATUS TO LK-M03B-RC
3999-EXIT:  EXIT.
```

#### ACCTFILE Section (paragraphs 4000–4999)
```
4000-ACCTFILE-PROC:
    IF M03B-OPEN    -> OPEN INPUT ACCT-FILE
    IF M03B-READ-K  -> MOVE LK-M03B-KEY(1:LK-M03B-KEY-LN) TO FD-ACCT-ID
                       READ ACCT-FILE INTO LK-M03B-FLDT
    IF M03B-CLOSE   -> CLOSE ACCT-FILE
4900-EXIT:
    MOVE ACCTFILE-STATUS TO LK-M03B-RC
4999-EXIT:  EXIT.
```

---

## 9. Supported Operations by File

| DD Name | Open ('O') | Sequential Read ('R') | Keyed Read ('K') | Close ('C') | Write ('W') | Rewrite ('Z') |
|---|---|---|---|---|---|---|
| TRNXFILE | Yes | Yes | No | Yes | No | No |
| XREFFILE | Yes | Yes | No | Yes | No | No |
| CUSTFILE | Yes | No | Yes | Yes | No | No |
| ACCTFILE | Yes | No | Yes | Yes | No | No |

Write ('W') and Rewrite ('Z') are defined as 88-level values in the operation code field but are not implemented for any file. If either is passed, the program will fall through all IF conditions without taking any action and return the current (unchanged) file status code.

---

## 10. Return Code Behavior

The return code `LK-M03B-RC` is always set to the file status from the most recently executed operation for that file (moved from the file-specific status variable at the 9X00-EXIT paragraph). This is the standard 2-character VSAM/QSAM file status code:
- `'00'` — Operation successful
- `'10'` — End of file (sequential read)
- Any other value — Error condition

The caller (CBSTM03A) is responsible for interpreting the return code and taking action.

---

## 11. Error Handling

CBSTM03B performs no error handling itself. It executes the requested operation and returns the file status to the caller in `LK-M03B-RC`. Error detection and response is entirely the responsibility of CBSTM03A.

There is no ABEND paragraph in CBSTM03B.

---

## 12. Data Flow

```
CBSTM03A
    |
    | CALL 'CBSTM03B' USING WS-M03B-AREA
    |   LK-M03B-DD = 'TRNXFILE'/'XREFFILE'/'CUSTFILE'/'ACCTFILE'
    |   LK-M03B-OPER = 'O'/'R'/'K'/'C'
    |   LK-M03B-KEY = key value (for 'K' only)
    |   LK-M03B-KEY-LN = key length (for 'K' only)
    |
    v
CBSTM03B
    | Dispatches by LK-M03B-DD
    | Executes file operation
    | Moves record to LK-M03B-FLDT (for read operations)
    | Sets LK-M03B-RC = file status
    |
    GOBACK
    |
    v
CBSTM03A
    | Reads LK-M03B-RC to check success/EOF/error
    | Reads LK-M03B-FLDT to get record data (after read operations)
```

---

## 13. Observations

- CBSTM03B is the only program in this batch suite that uses the `PERFORM ... THRU ...` construct. The THRU pattern (1000-TRNXFILE-PROC THRU 1999-EXIT) relies on sequential paragraph fall-through, which can be fragile if paragraphs are reordered.
- The WRITE ('W') and REWRITE ('Z') operation codes are defined but not implemented for any file — they are dead code.
- CUSTFILE is opened with sequential key declaration (`ACCESS MODE IS RANDOM`) but only keyed reads ('K') are supported. Sequential reads would require re-opening with sequential access.
- The composite key of TRNX-FILE (card number + transaction ID) is a significant architectural note: the transaction file used by CBSTM03B/CBSTM03A uses a different key structure than the TRANSACT file used by CBTRN01C/CBTRN02C/CBTRN03C (which use transaction ID alone as key). These may be different physical files or different KSDS definitions of the same data.
- No bounds checking is performed on `LK-M03B-KEY-LN` before using it as a reference modification length. A negative or excessively large key length from the caller would produce a runtime error.
