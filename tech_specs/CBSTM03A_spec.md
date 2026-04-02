# Technical Specification: CBSTM03A

## 1. Executive Summary

CBSTM03A is the primary statement-generation batch COBOL program in the CardDemo application. It reads all card cross-reference records sequentially, and for each card, retrieves the associated customer and account data, then generates account statements in two formats simultaneously: a plain-text statement file and an HTML statement file. Transaction data is pre-loaded into a two-dimensional in-memory array and matched to cards during statement generation. The program delegates all file I/O operations to the subroutine CBSTM03B via a generic CALL interface. CBSTM03A notably exercises several advanced COBOL and mainframe features: control block addressing (PSA/TCB/TIOT), ALTER/GO TO statements, COMP and COMP-3 variables, and a 2-dimensional table structure.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBSTM03A.CBL` | COBOL Batch Program | Main statement generator |
| `CBSTM03B.CBL` | COBOL Batch Subroutine | File I/O delegate (called via CALL) |
| `COSTM01.CPY` | Copybook | Transaction record layout for statement use (`TRNX-RECORD`) |
| `CVACT03Y.cpy` | Copybook | Card cross-reference record (`CARD-XREF-RECORD`) |
| `CUSTREC.cpy` | Copybook | Customer record for statement (`CUSTOMER-RECORD`) |
| `CVACT01Y.cpy` | Copybook | Account record (`ACCOUNT-RECORD`) |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBSTM03A` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Print Account Statements in plain text and HTML formats |
| Source Version | CardDemo_v2.0-25-gdb72e6b-235 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Purpose |
|---|---|---|---|
| `STMT-FILE` | `STMTFILE` | Sequential | Plain-text statement output (80-byte records) |
| `HTML-FILE` | `HTMLFILE` | Sequential | HTML statement output (100-byte records) |

**Note:** CBSTM03A itself does not declare FILE-CONTROL entries for TRNXFILE, XREFFILE, CUSTFILE, or ACCTFILE. All I/O to those files is performed through CBSTM03B, which receives the DD name and operation code via its LINKAGE SECTION interface.

---

## 5. File Section — Record Layouts

### 5.1 STMT-FILE (Output)
```
FD STMT-FILE.
01 FD-STMTFILE-REC    PIC X(80).
```
80-byte plain-text lines.

### 5.2 HTML-FILE (Output)
```
FD HTML-FILE.
01 FD-HTMLFILE-REC    PIC X(100).
```
100-byte HTML tag lines.

---

## 6. Copybooks Referenced

| Copybook | Location | Record/Fields Provided |
|---|---|---|
| `COSTM01` | WORKING-STORAGE (line 51) | `TRNX-RECORD`: TRNX-KEY (TRNX-CARD-NUM X(16), TRNX-ID X(16)), TRNX-REST (TRNX-TYPE-CD, TRNX-CAT-CD, TRNX-SOURCE, TRNX-DESC, TRNX-AMT, TRNX-MERCHANT-*, TRNX-ORIG-TS, TRNX-PROC-TS) |
| `CVACT03Y` | WORKING-STORAGE (line 53) | `CARD-XREF-RECORD`: XREF-CARD-NUM X(16), XREF-CUST-ID 9(09), XREF-ACCT-ID 9(11) |
| `CUSTREC` | WORKING-STORAGE (line 55) | `CUSTOMER-RECORD`: CUST-ID, CUST-FIRST-NAME, CUST-MIDDLE-NAME, CUST-LAST-NAME, CUST-ADDR-LINE-1/2/3, CUST-ADDR-STATE-CD, CUST-ADDR-COUNTRY-CD, CUST-ADDR-ZIP, CUST-FICO-CREDIT-SCORE |
| `CVACT01Y` | WORKING-STORAGE (line 57) | `ACCOUNT-RECORD`: ACCT-ID, ACCT-CURR-BAL, ACCT-GROUP-ID |

**Note on CUSTREC vs CVCUS01Y:** CBSTM03A uses `CUSTREC.cpy`, which differs from `CVCUS01Y.cpy`. The field `CUST-DOB-YYYYMMDD` in CUSTREC has the date in YYYYMMDD format (without separators), while CVCUS01Y uses `CUST-DOB-YYYY-MM-DD`. This is a structural discrepancy between the two customer record definitions.

---

## 7. Working-Storage Data Structures

### 7.1 COMP Variables (binary, halfword)
```
01 COMP-VARIABLES COMP.
   05 CR-CNT    PIC S9(4) VALUE 0   [Card count in WS-TRNX-TABLE]
   05 TR-CNT    PIC S9(4) VALUE 0   [Transaction count per card]
   05 CR-JMP    PIC S9(4) VALUE 0   [Card loop iterator]
   05 TR-JMP    PIC S9(4) VALUE 0   [Transaction loop iterator]
```

### 7.2 COMP-3 Variables (packed decimal)
```
01 COMP3-VARIABLES COMP-3.
   05 WS-TOTAL-AMT    PIC S9(9)V99 VALUE 0   [Running total amount per card]
```

### 7.3 Miscellaneous Variables
```
01 MISC-VARIABLES.
   05 WS-FL-DD      PIC X(8) VALUE 'TRNXFILE'   [DD name for CBSTM03B dispatch]
   05 WS-TRN-AMT    PIC S9(9)V99 VALUE 0
   05 WS-SAVE-CARD  PIC X(16) VALUE SPACES
   05 END-OF-FILE   PIC X(01) VALUE 'N'
```

### 7.4 WS-M03B-AREA — CBSTM03B Call Interface
```
01 WS-M03B-AREA.
   05 WS-M03B-DD     PIC X(08)   [Target DD name: 'TRNXFILE','XREFFILE','CUSTFILE','ACCTFILE']
   05 WS-M03B-OPER   PIC X(01)   [Operation code: 'O'=Open,'C'=Close,'R'=Read,'K'=Read-by-Key]
     88 M03B-OPEN    VALUE 'O'
     88 M03B-CLOSE   VALUE 'C'
     88 M03B-READ    VALUE 'R'
     88 M03B-READ-K  VALUE 'K'
     88 M03B-WRITE   VALUE 'W'
     88 M03B-REWRITE VALUE 'Z'
   05 WS-M03B-RC     PIC X(02)   [Return code: '00'=OK, '10'=EOF, other=error]
   05 WS-M03B-KEY    PIC X(25)   [Key value for keyed reads]
   05 WS-M03B-KEY-LN PIC S9(4)   [Key length]
   05 WS-M03B-FLDT   PIC X(1000) [Data area: record returned or to be written]
```

### 7.5 Statement Line Templates (STATEMENT-LINES)
Predefined output lines for the plain-text statement:
- `ST-LINE0`: Banner line (asterisks + 'START OF STATEMENT')
- `ST-LINE1`: Customer name (75 chars)
- `ST-LINE2/3`: Address lines 1 and 2 (50 chars)
- `ST-LINE4`: Address line 3 (80 chars, includes state, country, zip)
- `ST-LINE5`: Divider (all '-')
- `ST-LINE6`: 'Basic Details' header
- `ST-LINE7`: Account ID display (ST-ACCT-ID PIC X(20))
- `ST-LINE8`: Current Balance (ST-CURR-BAL PIC 9(9).99-)
- `ST-LINE9`: FICO Score (ST-FICO-SCORE PIC X(20))
- `ST-LINE10/12`: More dividers
- `ST-LINE11`: 'TRANSACTION SUMMARY' header
- `ST-LINE13`: Column headers (Tran ID, Tran Details, Tran Amount)
- `ST-LINE14`: Transaction detail line (ST-TRANID X(16), ST-TRANDT X(49), ST-TRANAMT Z(9).99-)
- `ST-LINE14A`: Total expense line (ST-TOTAL-TRAMT Z(9).99-)
- `ST-LINE15`: End-of-statement banner

### 7.6 HTML_LINES — HTML Output Templates
Extensive 88-level VALUE clauses define complete HTML tag strings (100-byte fixed). Includes:
- `HTML-L01` through `HTML-L80`: Standard HTML structural tags
- `HTML-L11`, `HTML-L23`: Variable content lines with embedded data fields (L11-ACCT PIC X(20), L23-NAME PIC X(50))
- `HTML-ADDR-LN`, `HTML-BSIC-LN`, `HTML-TRAN-LN`: Variable HTML body lines

### 7.7 WS-TRNX-TABLE — Two-Dimensional Transaction Array
```
01 WS-TRNX-TABLE.
   05 WS-CARD-TBL OCCURS 51 TIMES.
      10 WS-CARD-NUM              PIC X(16)
      10 WS-TRAN-TBL OCCURS 10 TIMES.
         15 WS-TRAN-NUM           PIC X(16)
         15 WS-TRAN-REST          PIC X(318)
```
This is a fixed-capacity in-memory table: maximum 51 unique card numbers, each with up to 10 transactions. A companion array `WS-TRN-TBL-CNTR` tracks transaction count per card:
```
01 WS-TRN-TBL-CNTR.
   05 WS-TRN-TBL-CTR OCCURS 51 TIMES.
      10 WS-TRCT    PIC S9(4) COMP
```

### 7.8 PSA/TCB/TIOT — Control Block Addressing (Linkage Section)
```
LINKAGE SECTION.
01 ALIGN-PSA         PIC 9(16) BINARY   [Address of PSA]
01 PSA-BLOCK.
   05 FILLER         PIC X(536)
   05 TCB-POINT      POINTER
01 TCB-BLOCK.
   05 FILLER         PIC X(12)
   05 TIOT-POINT     POINTER
01 TIOT-BLOCK.
   05 TIOTNJOB       PIC X(08)   [Job name]
   05 TIOTJSTP       PIC X(08)   [Step name]
   05 TIOTPSTP       PIC X(08)   [Proc step name]
01 TIOT-ENTRY.
   05 TIOT-SEG.
      10 TIO-LEN     PIC X(01)   [Entry length]
      10 FILLER      PIC X(03)
      10 TIOCDDNM    PIC X(08)   [DD name]
      10 FILLER      PIC X(05)
      10 UCB-ADDR    PIC X(03)   [Unit Control Block address]
         88 NULL-UCB VALUES LOW-VALUES
   05 FILLER         PIC X(04)
      88 END-OF-TIOT VALUE LOW-VALUES
```
Used at program startup to display the job step name and enumerate DD allocations.

---

## 8. Procedure Division — Program Flow

### 8.1 Startup — TIOT Traversal (lines 262–291)
```
SET ADDRESS OF PSA-BLOCK TO PSAPTR   [0x00000000 in z/OS]
SET ADDRESS OF TCB-BLOCK TO TCB-POINT
SET ADDRESS OF TIOT-BLOCK TO TIOT-POINT
SET TIOT-INDEX TO TIOT-POINT
DISPLAY 'Running JCL: ' TIOTNJOB ' Step ' TIOTJSTP

[Advance TIOT-INDEX past TIOT-BLOCK header]
[PERFORM UNTIL END-OF-TIOT: display each DD name and UCB status]

OPEN OUTPUT STMT-FILE HTML-FILE
INITIALIZE WS-TRNX-TABLE WS-TRN-TBL-CNTR
```
This section uses raw PSA/TCB/TIOT addressing — a low-level z/OS technique for enumerating JCL DD allocations at runtime.

### 8.2 0000-START — ALTER/GO TO Dispatch (lines 296–314)
```
EVALUATE WS-FL-DD
    WHEN 'TRNXFILE' -> ALTER 8100-FILE-OPEN TO PROCEED TO 8100-TRNXFILE-OPEN
                       GO TO 8100-FILE-OPEN
    WHEN 'XREFFILE' -> ALTER 8100-FILE-OPEN TO PROCEED TO 8200-XREFFILE-OPEN
                       GO TO 8100-FILE-OPEN
    ...
    WHEN 'READTRNX' -> GO TO 8500-READTRNX-READ
    WHEN OTHER      -> GO TO 9999-GOBACK
```
**Note:** The `ALTER` statement modifies the target of a `GO TO` at runtime. `ALTER para-name TO PROCEED TO target` changes the destination of the GO TO in `para-name`. This is an archaic COBOL construct deliberately included to exercise modernization tooling.

WS-FL-DD is initialized to 'TRNXFILE', so at startup `0000-START` opens TRNXFILE first, then the transaction read loop pre-populates WS-TRNX-TABLE before `1000-MAINLINE` processes XREFs.

### 8.3 1000-MAINLINE — Statement Generation Loop (lines 317–342)
```
PERFORM UNTIL END-OF-FILE = 'Y'
    IF END-OF-FILE = 'N'
        PERFORM 1000-XREFFILE-GET-NEXT     [Read next XREF record]
        IF END-OF-FILE = 'N'
            PERFORM 2000-CUSTFILE-GET      [Keyed read of CUSTFILE]
            PERFORM 3000-ACCTFILE-GET      [Keyed read of ACCTFILE]
            PERFORM 5000-CREATE-STATEMENT  [Write statement lines]
            MOVE 1 TO CR-JMP
            MOVE ZERO TO WS-TOTAL-AMT
            PERFORM 4000-TRNXFILE-GET      [Find matching transactions in table]
        END-IF
    END-IF
END-PERFORM

PERFORM 9100-TRNXFILE-CLOSE
PERFORM 9200-XREFFILE-CLOSE
PERFORM 9300-CUSTFILE-CLOSE
PERFORM 9400-ACCTFILE-CLOSE
CLOSE STMT-FILE HTML-FILE
GOBACK
```

### 8.4 File Operation Paragraphs (via CBSTM03B)

All four VSAM file operations follow the same pattern:

| Paragraph | Target DD | Operation | Key Used |
|---|---|---|---|
| `1000-XREFFILE-GET-NEXT` | 'XREFFILE' | 'R' (sequential read) | N/A |
| `2000-CUSTFILE-GET` | 'CUSTFILE' | 'K' (key read) | XREF-CUST-ID |
| `3000-ACCTFILE-GET` | 'ACCTFILE' | 'K' (key read) | XREF-ACCT-ID |
| `4000-TRNXFILE-GET` | Table lookup (in-memory) | N/A — no CBSTM03B call | WS-CARD-NUM array |

**CBSTM03B is called** for operations 1000, 2000, and 3000. The call pattern:
```
MOVE 'XREFFILE' TO WS-M03B-DD
SET M03B-READ TO TRUE
MOVE ZERO TO WS-M03B-RC
MOVE SPACES TO WS-M03B-FLDT
CALL 'CBSTM03B' USING WS-M03B-AREA
EVALUATE WS-M03B-RC
    WHEN '00' CONTINUE
    WHEN '10' MOVE 'Y' TO END-OF-FILE
    WHEN OTHER DISPLAY error, PERFORM 9999-ABEND-PROGRAM
END-EVALUATE
MOVE WS-M03B-FLDT TO CARD-XREF-RECORD  [or CUSTOMER-RECORD / ACCOUNT-RECORD]
```

### 8.5 4000-TRNXFILE-GET — In-Memory Table Lookup (lines 417–456)
Iterates through WS-TRNX-TABLE:
```
PERFORM VARYING CR-JMP FROM 1 BY 1 UNTIL CR-JMP > CR-CNT
                                      OR WS-CARD-NUM(CR-JMP) > XREF-CARD-NUM
    IF XREF-CARD-NUM = WS-CARD-NUM(CR-JMP)
        PERFORM VARYING TR-JMP FROM 1 BY 1 UNTIL TR-JMP > WS-TRCT(CR-JMP)
            MOVE WS-TRAN-NUM(CR-JMP, TR-JMP) TO TRNX-ID
            MOVE WS-TRAN-REST(CR-JMP, TR-JMP) TO TRNX-REST
            PERFORM 6000-WRITE-TRANS
            ADD TRNX-AMT TO WS-TOTAL-AMT
        END-PERFORM
    END-IF
END-PERFORM
```
Then writes total amount and end-of-statement lines to both STMT-FILE and HTML-FILE.

### 8.6 5000-CREATE-STATEMENT — Header and Basic Details (lines 458–499)
- INITIALIZEs STATEMENT-LINES
- Calls 5100-WRITE-HTML-HEADER and 5200-WRITE-HTML-NMADBS
- Builds customer name by STRINGing CUST-FIRST-NAME, CUST-MIDDLE-NAME, CUST-LAST-NAME
- Builds address lines from CUST-ADDR-LINE-1/2/3 + state + country + zip
- Sets ST-ACCT-ID = ACCT-ID, ST-CURR-BAL = ACCT-CURR-BAL, ST-FICO-SCORE = CUST-FICO-CREDIT-SCORE
- WRITEs statement lines ST-LINE0 through ST-LINE15 fragments to STMT-FILE
- WRITEs corresponding HTML tags to HTML-FILE

---

## 9. External Program Calls

| Called Program | Mechanism | Purpose |
|---|---|---|
| `CBSTM03B` | CALL 'CBSTM03B' USING WS-M03B-AREA | File I/O delegate: opens/reads/closes TRNXFILE, XREFFILE, CUSTFILE, ACCTFILE |
| `CEE3ABD` | CALL in 9999-ABEND-PROGRAM | LE abnormal termination |

---

## 10. Business Logic and Processing Rules

1. **Transaction Pre-Loading:** Before the main XREf loop begins (via the `0000-START` ALTER/GO TO mechanism), all transactions are read into the WS-TRNX-TABLE array. The table is indexed by card number. Maximum capacity is 51 cards × 10 transactions = 510 transactions. Records exceeding this capacity would overflow, as there is no bounds check.

2. **Card-to-Statement Mapping:** For each XREF record, the card number (XREF-CARD-NUM) is used as the key to look up transactions in the in-memory array. Only transactions whose card number matches the XREF card number are included in that statement.

3. **Dual-Format Output:** Every statement event writes to both STMT-FILE (plain text, 80 bytes per line) and HTML-FILE (HTML markup, 100 bytes per line) simultaneously.

4. **PSA/TCB/TIOT Enumeration:** At startup, the program walks the z/OS Task I/O Table to enumerate all DD allocations for the current job step. This is diagnostic information written to SYSOUT.

5. **ALTER Statement:** The `ALTER 8100-FILE-OPEN TO PROCEED TO 8100-TRNXFILE-OPEN` construct dynamically modifies the GO TO destination. This is included to challenge modernization tools that may not support ALTER.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| CBSTM03B open/read error | WS-M03B-RC not '00' or '10' | DISPLAY 'ERROR READING [file]' and RETURN CODE, 9999-ABEND-PROGRAM |
| CBSTM03B EOF | WS-M03B-RC = '10' | MOVE 'Y' TO END-OF-FILE |
| Statement or HTML write error | Implicit (no status checked) | No explicit error handling on STMT-FILE/HTML-FILE writes |

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion | 0 (implicit GOBACK) |
| File I/O error | Abend via CEE3ABD (ABCODE=999) |

---

## 13. Table Capacity Limits

| Table | Max Entries | Overflow Behavior |
|---|---|---|
| `WS-CARD-TBL` (card dimension) | 51 | No bounds check — table overflow will corrupt adjacent storage |
| `WS-TRAN-TBL` (transaction dimension per card) | 10 | No bounds check — transaction overflow will corrupt adjacent storage |

These fixed limits are a critical constraint for production use. Any account with more than 10 transactions per statement cycle, or a job with more than 51 unique card numbers, will result in unpredictable behavior.

---

## 14. Observations

- The program is explicitly documented (lines 34–35) as exercising: control block addressing, ALTER/GO TO, COMP/COMP-3 variables, 2-dimensional arrays, and subroutine calls — confirming its role as a modernization tooling test case.
- The PSA address of zero (`SET ADDRESS OF PSA-BLOCK TO PSAPTR` where PSAPTR is a POINTER declared with no initial value) is an absolute z/OS address — this will not work in non-z/OS environments.
- No record count or summary report is produced. The only indication of processing volume is the transaction total per statement.
- The CUSTREC copybook (used here) and CVCUS01Y copybook (used in CBCUS01C, CBEXPORT, CBIMPORT, CBTRN01C) have different date field names (CUST-DOB-YYYYMMDD vs CUST-DOB-YYYY-MM-DD), implying different versions of the customer record layout.
