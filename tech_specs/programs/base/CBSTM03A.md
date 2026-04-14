# Technical Specification: CBSTM03A

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | CBSTM03A                                             |
| Source File      | app/cbl/CBSTM03A.CBL                                 |
| Application      | CardDemo                                             |
| Type             | Batch COBOL Program                                  |
| Transaction ID   | N/A (batch)                                          |
| Function         | Generate account statements from transaction data in two output formats: (1) plain text (STMTFILE, 80 bytes/line) and (2) HTML (HTMLFILE, 100 bytes/line). Drives from XREFFILE sequentially; for each cross-reference fetches the customer, account, and associated transactions, then formats and writes one statement per account to both output files. Calls CBSTM03B for all file I/O operations via a generic area interface. |

**Design Note**: This program intentionally exercises five mainframe-specific features for modernization tooling validation: (1) mainframe control block addressing (PSA/TCB/TIOT), (2) ALTER/GO TO statements, (3) COMP and COMP-3 variables, (4) two-dimensional arrays, and (5) calls to a subroutine (CBSTM03B).

---

## 2. Program Flow

### High-Level Flow

```
START
  Address PSA, TCB, TIOT via POINTER (LINKAGE SECTION)
  DISPLAY JCL job name, step name from TIOT
  Walk TIOT entries and DISPLAY all DD names

  OPEN OUTPUT STMT-FILE HTML-FILE
  INITIALIZE WS-TRNX-TABLE WS-TRN-TBL-CNTR

  0000-START:
      EVALUATE WS-FL-DD ('TRNXFILE' / 'XREFFILE' etc.)
          ALTER 8100-FILE-OPEN (not shown in read excerpt — file open via ALTER/GO TO)
      [Opens XREFFILE, TRNXFILE, CUSTFILE, ACCTFILE via CBSTM03B]

  1000-MAINLINE:
  PERFORM UNTIL END-OF-FILE = 'Y':
      1000-XREFFILE-GET-NEXT (CALL CBSTM03B READ XREFFILE)
      IF not EOF:
          2000-CUSTFILE-GET (CALL CBSTM03B READ-K CUSTFILE by XREF-CUST-ID)
          3000-ACCTFILE-GET (CALL CBSTM03B READ-K ACCTFILE by XREF-ACCT-ID)
          5000-CREATE-STATEMENT
              Write plain text header lines to STMTFILE
              Write HTML header via 5100-WRITE-HTML-HEADER
              Fill name/address/account details
              Write HTML name/address/basic details via 5200-WRITE-HTML-NMADBS
          4000-TRNXFILE-GET
              Search WS-TRNX-TABLE for matching card number
              For each matching transaction:
                  6000-WRITE-TRANS (write one line to STMTFILE + HTML row)
                  ADD TRNX-AMT to WS-TOTAL-AMT
              Write total-expense line (ST-LINE14A) to STMTFILE
              Write HTML end-of-statement rows
  END-PERFORM

  9100-TRNXFILE-CLOSE, 9200-XREFFILE-CLOSE, 9300-CUSTFILE-CLOSE, 9400-ACCTFILE-CLOSE
  CLOSE STMT-FILE HTML-FILE
  GOBACK
```

### Paragraph-Level Detail

| Paragraph                  | Lines     | Description |
|----------------------------|-----------|-------------|
| PROCEDURE DIVISION (init)  | 262–293   | PSA/TCB/TIOT addressing; DISPLAY job/step/DD names; OPEN STMT-FILE HTML-FILE; INITIALIZE tables |
| 0000-START                 | 296–314   | EVALUATE WS-FL-DD; ALTER 8100-FILE-OPEN and GO TO for file opens; falls through to 1000-MAINLINE |
| 1000-MAINLINE              | 316–342   | Main loop: calls GET-NEXT, then CUSTFILE/ACCTFILE/TRNXFILE gets and statement creation |
| 1000-XREFFILE-GET-NEXT     | 345–366   | Sets WS-M03B-DD='XREFFILE', M03B-READ; CALL CBSTM03B; EVALUATE return code; MOVE WS-M03B-FLDT TO CARD-XREF-RECORD |
| 2000-CUSTFILE-GET          | 368–390   | Sets WS-M03B-DD='CUSTFILE', M03B-READ-K; key=XREF-CUST-ID, length from LENGTH OF; CALL CBSTM03B; MOVE result to CUSTOMER-RECORD |
| 3000-ACCTFILE-GET          | 392–414   | Sets WS-M03B-DD='ACCTFILE', M03B-READ-K; key=XREF-ACCT-ID; CALL CBSTM03B; MOVE result to ACCOUNT-RECORD |
| 4000-TRNXFILE-GET          | 416–456   | PERFORM VARYING CR-JMP searching WS-TRNX-TABLE for XREF-CARD-NUM match; inner loop over transactions; calls 6000-WRITE-TRANS; accumulates WS-TOTAL-AMT; writes totals/end-of-statement to both files |
| 5000-CREATE-STATEMENT      | 458–503   | INITIALIZE STATEMENT-LINES; writes ST-LINE0 through ST-LINE13 to STMTFILE; calls 5100 and 5200 for HTML |
| 5100-WRITE-HTML-HEADER     | 506–554   | Writes HTML boilerplate (DOCTYPE through table header) and bank address to HTMLFILE |
| 5100-EXIT                  | 554–555   | EXIT |
| 5200-WRITE-HTML-NMADBS     | 558–672   | Writes customer name, address, basic account details, and transaction summary headers to HTMLFILE via STRING into work areas |
| 5200-EXIT                  | 671–672   | EXIT |
| 6000-WRITE-TRANS           | 675–~740  | Formats one transaction line to STMTFILE (ST-LINE14); writes HTML table row with TRAN-ID, description, amount |
| 8100-FILE-OPEN / 8100-TRNXFILE-OPEN etc. | ~740+ | ALTER targets for file open via CBSTM03B (not fully captured in read) |
| 9100–9400-*-CLOSE          | ~800+     | Close each file via CBSTM03B (WS-M03B-OPER='C') |
| 9999-ABEND-PROGRAM         | ~850      | DISPLAY error; CALL 'CEE3ABD' |
| 9999-GOBACK                | 341       | GOBACK (alternate exit from 0000-START WHEN OTHER) |

**Note**: Lines beyond 698 were not read in their entirety. The 8100-FILE-OPEN ALTER targets, close paragraphs, and abend paragraph exist but line numbers cannot be confirmed precisely.

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Used In              | Contents |
|----------|----------------------|----------|
| COSTM01  | WORKING-STORAGE (line 51) | Transaction record layout for TRNXFILE (TRNX-CARD-NUM X(16), TRNX-ID X(16), TRNX-DESC, TRNX-AMT, TRNX-REST X(318)) — **[UNRESOLVED]** exact field layout requires reading app/cpy/COSTM01.cpy |
| CVACT03Y | WORKING-STORAGE (line 53) | CARD-XREF-RECORD: XREF-CARD-NUM X(16), XREF-CUST-ID 9(9), XREF-ACCT-ID 9(11), FILLER X(14) |
| CUSTREC  | WORKING-STORAGE (line 55) | Customer record layout — **[UNRESOLVED]** exact field layout requires reading app/cpy/CUSTREC.cpy; fields CUST-FIRST-NAME, CUST-MIDDLE-NAME, CUST-LAST-NAME, CUST-ADDR-LINE-1 through -3, CUST-ADDR-STATE-CD, CUST-ADDR-COUNTRY-CD, CUST-ADDR-ZIP, CUST-FICO-CREDIT-SCORE are referenced in PROCEDURE DIVISION |
| CVACT01Y | WORKING-STORAGE (line 57) | ACCOUNT-RECORD (300 bytes): ACCT-ID 9(11), ACCT-CURR-BAL, ACCT-CREDIT-LIMIT, etc. |

### File Description Records

| FD Name       | DD Name   | Org  | RECLN | Notes |
|---------------|-----------|------|-------|-------|
| STMT-FILE     | STMTFILE  | Sequential | 80 | Plain text statement output |
| HTML-FILE     | HTMLFILE  | Sequential | 100 | HTML statement output |

Note: XREFFILE, CUSTFILE, ACCTFILE, and TRNXFILE are all opened and read exclusively through the CBSTM03B subroutine interface. They have no FD in CBSTM03A's FILE SECTION.

### Key Working Storage Variables

| Variable               | PIC / Type   | Purpose |
|------------------------|--------------|---------|
| WS-FL-DD               | X(8) = 'TRNXFILE' | Initial value; used in 0000-START EVALUATE to select first file to open via ALTER |
| WS-M03B-AREA           | Group (1040 bytes) | Interface area passed to CBSTM03B: DD name X(8), operation X(1), return code X(2), key X(25), key length S9(4), data area X(1000) |
| WS-M03B-DD             | X(08)        | DD name for CBSTM03B dispatch |
| WS-M03B-OPER           | X(01)        | Operation: O=open, C=close, R=read-seq, K=read-by-key, W=write, Z=rewrite |
| WS-M03B-RC             | X(02)        | Return code from CBSTM03B (VSAM file status) |
| WS-M03B-KEY            | X(25)        | Key value for random reads |
| WS-M03B-KEY-LN         | S9(4)        | Length of key (computed from LENGTH OF key field) |
| WS-M03B-FLDT           | X(1000)      | Data payload passed to/from CBSTM03B |
| WS-TRNX-TABLE          | Group        | Two-dimensional: WS-CARD-TBL OCCURS 51 TIMES; each entry has WS-CARD-NUM X(16) + WS-TRAN-TBL OCCURS 10 TIMES (WS-TRAN-NUM X(16) + WS-TRAN-REST X(318)) |
| WS-TRN-TBL-CNTR        | Group        | WS-TRN-TBL-CTR OCCURS 51 TIMES, each WS-TRCT PIC S9(4) COMP; tracks transaction count per card |
| CR-CNT                 | S9(4) COMP   | Card count (number of card entries in WS-TRNX-TABLE) |
| TR-CNT                 | S9(4) COMP   | Transaction count (within a card) |
| CR-JMP                 | S9(4) COMP   | Loop index for card table search |
| TR-JMP                 | S9(4) COMP   | Loop index for transaction table |
| WS-TOTAL-AMT           | S9(9)V99 COMP-3 | Running total transaction amount for one account statement |
| WS-TRN-AMT             | S9(9)V99     | Copy of WS-TOTAL-AMT moved to display area |
| END-OF-FILE            | X(01)        | Loop control for XREFFILE sequential read |
| PSAPTR                 | POINTER      | Hardcoded pointer to address 0 (PSA base); used to address control blocks |
| BUMP-TIOT              | S9(08) BINARY | Arithmetic displacement through TIOT entries |
| TIOT-INDEX             | POINTER REDEFINES BUMP-TIOT | Current address of TIOT entry being examined |
| STATEMENT-LINES        | Group (ST-LINE0 through ST-LINE15) | 80-byte formatted output lines for STMTFILE |
| HTML-LINES             | Group        | 100-byte HTML line buffer; 88-level values define literal HTML tags |

### LINKAGE SECTION Control Block Layout

| 01-Level  | Contents |
|-----------|----------|
| ALIGN-PSA     | PIC 9(16) BINARY — used to establish PSA address |
| PSA-BLOCK     | 536 bytes filler + TCB-POINT POINTER (at offset 536) |
| TCB-BLOCK     | 12 bytes filler + TIOT-POINT POINTER (at offset 12) |
| TIOT-BLOCK    | TIOTNJOB X(8) + TIOTJSTP X(8) + TIOTPSTP X(8) |
| TIOT-ENTRY    | TIO-LEN X(1) + FILLER X(3) + TIOCDDNM X(8) + FILLER X(5) + UCB-ADDR X(3); 88 NULL-UCB=LOW-VALUES; 88 END-OF-TIOT=LOW-VALUES on following FILLER X(4) |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name   | Accessed Via | Org  | Mode   | Purpose |
|-----------|--------------|------|--------|---------|
| STMTFILE  | Direct FD    | Sequential | OUTPUT | Plain text statement output (80 bytes) |
| HTMLFILE  | Direct FD    | Sequential | OUTPUT | HTML statement output (100 bytes) |
| XREFFILE  | CBSTM03B (R) | KSDS Sequential | INPUT | Drives main loop; provides card-to-customer/account mapping |
| CUSTFILE  | CBSTM03B (K) | KSDS Random | INPUT | Random read by CUST-ID to get customer name and address |
| ACCTFILE  | CBSTM03B (K) | KSDS Random | INPUT | Random read by ACCT-ID to get account balance and details |
| TRNXFILE  | CBSTM03B (R) | KSDS Sequential | INPUT | Sequential read; records loaded into WS-TRNX-TABLE |

---

## 6. Screen Interaction

None. Batch program.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Call Points | Purpose |
|----------------|-------------|-------------|---------|
| CBSTM03B       | Static CALL | 1000-XREFFILE-GET-NEXT, 2000-CUSTFILE-GET, 3000-ACCTFILE-GET, and file open/close paragraphs | All file I/O operations: open, sequential read, keyed read, close |
| CEE3ABD        | Static CALL | 9999-ABEND-PROGRAM | LE forced abend |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| XREFFILE read error (RC not '00'/'10') | DISPLAY 'ERROR READING XREFFILE', RC; PERFORM 9999-ABEND-PROGRAM |
| CUSTFILE read error (RC not '00') | DISPLAY 'ERROR READING CUSTFILE', RC; PERFORM 9999-ABEND-PROGRAM |
| ACCTFILE read error (RC not '00') | DISPLAY 'ERROR READING ACCTFILE', RC; PERFORM 9999-ABEND-PROGRAM |
| XREFFILE EOF (RC='10') | MOVE 'Y' TO END-OF-FILE; exit loop normally |
| TRNXFILE errors | Propagated via WS-M03B-RC but specific handling not captured in available source |

---

## 9. Business Rules

1. **Two output formats**: One execution produces both a plain text statement (STMTFILE) and an HTML statement (HTMLFILE) for each account found in XREFFILE.
2. **Transaction pre-loading**: Transactions are pre-loaded from TRNXFILE into the two-dimensional WS-TRNX-TABLE (51 cards × 10 transactions each) before statement generation. The table is searched by card number for each XREF record. Note: the pre-load mechanism uses ALTER/GO TO to open TRNXFILE before the main loop — the exact pre-load flow requires examining lines beyond 698.
3. **ALTER/GO TO**: The 0000-START paragraph uses ALTER statements to dynamically redirect GO TO destinations (8100-FILE-OPEN altered to proceed to 8100-TRNXFILE-OPEN, 8200-XREFFILE-OPEN, etc.). This is an intentional exercise of an obsolete COBOL feature.
4. **Mainframe control block walk**: At program start, PSAPTR (set to NULL POINTER = address 0) chains PSA → TCB → TIOT; DD names are read from TIOT and displayed to SYSOUT.
5. **HTML hardcoded bank identity**: HTML output embeds hardcoded strings: bank name 'Bank of XYZ', address '410 Terry Ave N', city/state 'Seattle WA 99999' (lines 540–542 area).
6. **Transaction total**: For each account, WS-TOTAL-AMT accumulates all TRNX-AMT values and is written as a "Total EXP:" line (ST-LINE14A) in the plain text statement.
7. **Table capacity**: WS-TRNX-TABLE holds a maximum of 51 card entries and 10 transactions per card. Overflow handling is not visible in the read source.

---

## 10. Inputs and Outputs

### Inputs

| Source   | Description |
|----------|-------------|
| XREFFILE | KSDS; drives main loop sequentially; provides XREF-CARD-NUM, XREF-CUST-ID, XREF-ACCT-ID |
| CUSTFILE | KSDS; random read by CUST-ID for customer name and address |
| ACCTFILE | KSDS; random read by ACCT-ID for account balance and FICO score |
| TRNXFILE | KSDS; read into in-memory WS-TRNX-TABLE; provides transaction details for statement body |

### Outputs

| Destination | RECLN | Description |
|-------------|-------|-------------|
| STMTFILE    | 80    | Plain text account statements with header, basic details, transaction listing, total |
| HTMLFILE    | 100   | HTML account statements with identical content in table layout |
| SYSOUT      | N/A   | JCL job/step name, DD name list from TIOT, error messages |

---

## 11. Key Variables and Their Purpose

| Variable           | Purpose |
|--------------------|---------|
| WS-M03B-AREA       | Generic call interface to CBSTM03B; single structure passed for all file operations |
| WS-TRNX-TABLE      | In-memory two-dimensional transaction table (51×10); loaded from TRNXFILE before statements are generated |
| WS-TRN-TBL-CNTR    | Parallel counter array (OCCURS 51); tracks how many transactions are loaded per card |
| CR-CNT / CR-JMP    | COMP variables: card table boundary and search index |
| TR-CNT / TR-JMP    | COMP variables: transaction sub-table boundary and search index |
| WS-TOTAL-AMT       | COMP-3 accumulator for per-account total transaction amount |
| PSAPTR             | POINTER at value zero; chains to TCB and TIOT for control block walk |
| TIOT-INDEX         | POINTER redefining BUMP-TIOT; stepped through TIOT entries by adding TIO-LEN |
| END-OF-FILE        | XREFFILE EOF flag; drives main loop termination |
| HTML-FIXED-LN / 88 levels | Single 100-byte area with 88-level values holding HTML tag strings; SET to TRUE then WRITE |
