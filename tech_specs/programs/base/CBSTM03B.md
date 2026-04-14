# Technical Specification: CBSTM03B

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | CBSTM03B                                             |
| Source File      | app/cbl/CBSTM03B.CBL                                 |
| Application      | CardDemo                                             |
| Type             | Batch COBOL Subroutine                               |
| Transaction ID   | N/A (batch)                                          |
| Function         | File I/O subroutine called exclusively by CBSTM03A. Accepts a generic interface area (LK-M03B-AREA) specifying a DD name and operation code, performs the requested file operation (open, sequential read, keyed read, close), and returns the file status in LK-M03B-RC. Handles four files: TRNXFILE, XREFFILE, CUSTFILE, ACCTFILE. |

---

## 2. Program Flow

### High-Level Flow

```
CALLED WITH LK-M03B-AREA (PROCEDURE DIVISION USING LK-M03B-AREA)

0000-START:
    EVALUATE LK-M03B-DD
        WHEN 'TRNXFILE' → PERFORM 1000-TRNXFILE-PROC THRU 1999-EXIT
        WHEN 'XREFFILE' → PERFORM 2000-XREFFILE-PROC THRU 2999-EXIT
        WHEN 'CUSTFILE' → PERFORM 3000-CUSTFILE-PROC THRU 3999-EXIT
        WHEN 'ACCTFILE' → PERFORM 4000-ACCTFILE-PROC THRU 4999-EXIT
        WHEN OTHER     → GO TO 9999-GOBACK
    GOBACK
```

### Paragraph-Level Detail

| Paragraph           | Lines     | Description |
|---------------------|-----------|-------------|
| 0000-START          | 116–131   | EVALUATE on LK-M03B-DD; dispatches to file-specific section; falls through to GOBACK |
| 9999-GOBACK         | 130–131   | GOBACK |
| 1000-TRNXFILE-PROC  | 133–155   | IF M03B-OPEN: OPEN INPUT TRNX-FILE, GO TO 1900-EXIT; IF M03B-READ: READ TRNX-FILE INTO LK-M03B-FLDT, GO TO 1900-EXIT; IF M03B-CLOSE: CLOSE TRNX-FILE, GO TO 1900-EXIT |
| 1900-EXIT           | 151–152   | MOVE TRNXFILE-STATUS TO LK-M03B-RC |
| 1999-EXIT           | 154–155   | EXIT |
| 2000-XREFFILE-PROC  | 157–179   | Same pattern as 1000 but for XREF-FILE; MOVE XREFFILE-STATUS TO LK-M03B-RC at 2900-EXIT |
| 2900-EXIT / 2999-EXIT | 175–179 | Status return and EXIT |
| 3000-CUSTFILE-PROC  | 181–204   | IF M03B-OPEN: OPEN; IF M03B-READ-K: MOVE LK-M03B-KEY(1:LK-M03B-KEY-LN) TO FD-CUST-ID, READ CUST-FILE INTO LK-M03B-FLDT; IF M03B-CLOSE: CLOSE. MOVE CUSTFILE-STATUS TO LK-M03B-RC at 3900-EXIT |
| 3900-EXIT / 3999-EXIT | 200–204 | Status return and EXIT |
| 4000-ACCTFILE-PROC  | 206–229   | IF M03B-OPEN: OPEN; IF M03B-READ-K: MOVE LK-M03B-KEY(1:LK-M03B-KEY-LN) TO FD-ACCT-ID, READ ACCT-FILE INTO LK-M03B-FLDT; IF M03B-CLOSE: CLOSE. MOVE ACCTFILE-STATUS TO LK-M03B-RC at 4900-EXIT |
| 4900-EXIT / 4999-EXIT | 225–229 | Status return and EXIT |

---

## 3. Data Structures

### Copybooks Referenced

None. CBSTM03B uses inline FD definitions with minimal field layouts.

### File Description Records

| FD Name     | DD Name   | Key Field                              | Layout |
|-------------|-----------|----------------------------------------|--------|
| TRNX-FILE   | TRNXFILE  | FD-TRNXS-ID (composite): FD-TRNX-CARD X(16) + FD-TRNX-ID X(16) | FD-TRNXS-ID X(32) + FD-ACCT-DATA X(318); total 350 bytes |
| XREF-FILE   | XREFFILE  | FD-XREF-CARD-NUM X(16)                 | FD-XREF-CARD-NUM X(16) + FD-XREF-DATA X(34); total 50 bytes |
| CUST-FILE   | CUSTFILE  | FD-CUST-ID X(09)                       | FD-CUST-ID X(9) + FD-CUST-DATA X(491); total 500 bytes |
| ACCT-FILE   | ACCTFILE  | FD-ACCT-ID 9(11)                       | FD-ACCT-ID 9(11) + FD-ACCT-DATA X(289); total 300 bytes |

### File Organization

| DD Name   | Organization | ACCESS MODE  | Notes |
|-----------|--------------|--------------|-------|
| TRNXFILE  | INDEXED      | SEQUENTIAL   | Record key FD-TRNXS-ID (composite card+transaction ID) |
| XREFFILE  | INDEXED      | SEQUENTIAL   | Record key FD-XREF-CARD-NUM |
| CUSTFILE  | INDEXED      | RANDOM       | Record key FD-CUST-ID; read by key only |
| ACCTFILE  | INDEXED      | RANDOM       | Record key FD-ACCT-ID; read by key only |

### Working Storage

| Variable          | PIC       | Purpose |
|-------------------|-----------|---------|
| TRNXFILE-STATUS   | X(2) (TRNXFILE-STAT1 X + TRNXFILE-STAT2 X) | File status for TRNX-FILE |
| XREFFILE-STATUS   | X(2)      | File status for XREF-FILE |
| CUSTFILE-STATUS   | X(2)      | File status for CUST-FILE |
| ACCTFILE-STATUS   | X(2)      | File status for ACCT-FILE |

### Linkage Section

| Field           | PIC     | Purpose |
|-----------------|---------|---------|
| LK-M03B-DD      | X(08)   | DD name identifying which file to operate on: 'TRNXFILE', 'XREFFILE', 'CUSTFILE', 'ACCTFILE' |
| LK-M03B-OPER    | X(01)   | Operation: O=open, C=close, R=sequential read, K=keyed read, W=write (no-op for these files), Z=rewrite (no-op) |
| LK-M03B-RC      | X(02)   | Output: file status after operation; set at *900-EXIT label of each section |
| LK-M03B-KEY     | X(25)   | Key value for keyed read (K operation); used as LK-M03B-KEY(1:LK-M03B-KEY-LN) |
| LK-M03B-KEY-LN  | S9(4)   | Length of the key in LK-M03B-KEY |
| LK-M03B-FLDT    | X(1000) | Data payload: READ INTO this area; caller reads from here after return |

88-level condition names on LK-M03B-OPER (mirroring WS-M03B-AREA in CBSTM03A):

| 88-Name    | Value |
|------------|-------|
| M03B-OPEN  | 'O'   |
| M03B-CLOSE | 'C'   |
| M03B-READ  | 'R'   |
| M03B-READ-K | 'K'  |
| M03B-WRITE | 'W'   |
| M03B-REWRITE | 'Z' |

---

## 4. CICS Commands Used

None. Batch subroutine.

---

## 5. File/Dataset Access

| DD Name   | File Object | Org      | Access     | Mode  | Operations Supported |
|-----------|-------------|----------|------------|-------|----------------------|
| TRNXFILE  | TRNX-FILE   | KSDS     | Sequential | INPUT | Open (O), Sequential Read (R), Close (C) |
| XREFFILE  | XREF-FILE   | KSDS     | Sequential | INPUT | Open (O), Sequential Read (R), Close (C) |
| CUSTFILE  | CUST-FILE   | KSDS     | Random     | INPUT | Open (O), Keyed Read (K), Close (C) |
| ACCTFILE  | ACCT-FILE   | KSDS     | Random     | INPUT | Open (O), Keyed Read (K), Close (C) |

Note: Operation codes W (write) and Z (rewrite) are defined in the 88-level conditions but no corresponding IF branches exist in the current source for any of the four files. These operations are effectively not implemented.

---

## 6. Screen Interaction

None. Batch subroutine.

---

## 7. Called Programs / Transfers

None. CBSTM03B is a leaf subroutine and calls no other programs.

---

## 8. Error Handling

CBSTM03B performs no error checking. It executes the requested file operation and returns the file status to the caller in LK-M03B-RC. All error handling decisions are made by the caller (CBSTM03A) based on the returned status code.

| Condition | Handling |
|-----------|----------|
| Any file status | Copied to LK-M03B-RC at *900-EXIT; no check performed in this program |
| Unknown LK-M03B-DD | GO TO 9999-GOBACK; LK-M03B-RC is not set (retains whatever value caller placed in it) |

---

## 9. Business Rules

1. **Generic dispatch interface**: One subroutine handles four different files via a single calling convention. The caller sets LK-M03B-DD and LK-M03B-OPER before each CALL; the subroutine sets LK-M03B-RC and LK-M03B-FLDT on return.
2. **Key-length-trimmed read**: For CUSTFILE and ACCTFILE keyed reads, the key is moved as `LK-M03B-KEY(1:LK-M03B-KEY-LN)` — only the first LK-M03B-KEY-LN bytes of the 25-byte key area are copied to the FD key field. The caller must set LK-M03B-KEY-LN correctly.
3. **No write or rewrite implementation**: Although M03B-WRITE ('W') and M03B-REWRITE ('Z') are defined as 88-level conditions, no corresponding IF branches exist in 1000-TRNXFILE-PROC, 2000-XREFFILE-PROC, 3000-CUSTFILE-PROC, or 4000-ACCTFILE-PROC. Calling CBSTM03B with these operations will fall through to the EXIT paragraph without performing any I/O.
4. **State is preserved across calls**: TRNX-FILE and XREF-FILE are opened in SEQUENTIAL access mode. Successive READ calls advance through the file. The file must be explicitly opened (O) before reading and closed (C) after use.
5. **PERFORM THRU pattern**: The main 0000-START uses `PERFORM 1000-TRNXFILE-PROC THRU 1999-EXIT` (not THRU 1900-EXIT). This ensures the EXIT statement at 1999-EXIT terminates the PERFORM scope regardless of which GO TO was taken within the section.

---

## 10. Inputs and Outputs

### Inputs

| Source          | Description |
|-----------------|-------------|
| LK-M03B-AREA (CALL argument) | DD name, operation code, key, and key length passed by CBSTM03A |
| TRNXFILE / XREFFILE / CUSTFILE / ACCTFILE | KSDS VSAM files read per operation request |

### Outputs

| Destination     | Description |
|-----------------|-------------|
| LK-M03B-RC      | Two-byte file status returned to caller after each operation |
| LK-M03B-FLDT    | 1000-byte data area populated with record contents on READ or READ-K |

---

## 11. Key Variables and Their Purpose

| Variable         | Purpose |
|------------------|---------|
| LK-M03B-DD       | Identifies which file section (1000/2000/3000/4000) to dispatch to |
| LK-M03B-OPER     | Identifies which file operation to perform within the dispatched section |
| LK-M03B-RC       | Return value: file status code from the just-completed I/O |
| LK-M03B-FLDT     | 1000-byte buffer holding the record read from the file |
| LK-M03B-KEY      | 25-byte key area; first LK-M03B-KEY-LN bytes used for keyed reads |
| LK-M03B-KEY-LN   | Byte count of the meaningful portion of LK-M03B-KEY |
| FD-TRNXS-ID      | Composite primary key for TRNX-FILE (card number X(16) + transaction ID X(16)) |
