# Technical Specification: CBTRN03C

## 1. Executive Summary

CBTRN03C is the daily transaction detail report batch COBOL program in the CardDemo application. It reads a date parameter file to establish a reporting window, then reads the transaction file sequentially and filters transactions by processing timestamp within the window. For each qualifying transaction, it performs keyed lookups of the card cross-reference, transaction type, and transaction category files to build descriptive report lines. The program produces a formatted 133-character-wide report file with transaction details, page totals, account totals, and a grand total. The report is paginated at 20 lines per page.

---

## 2. Artifact Inventory

| Artifact | Type | Role |
|---|---|---|
| `CBTRN03C.cbl` | COBOL Batch Program | Main program |
| `CVTRA05Y.cpy` | Copybook | Transaction record (`TRAN-RECORD`) |
| `CVACT03Y.cpy` | Copybook | Card cross-reference record (`CARD-XREF-RECORD`) |
| `CVTRA03Y.cpy` | Copybook | Transaction type record (`TRAN-TYPE-RECORD`) |
| `CVTRA04Y.cpy` | Copybook | Transaction category record (`TRAN-CAT-RECORD`) |
| `CVTRA07Y.cpy` | Copybook | Report layout structures (headers, detail line, totals) |

---

## 3. Program Identification

| Attribute | Value |
|---|---|
| Program ID | `CBTRN03C` |
| Author | AWS |
| Application | CardDemo |
| Type | Batch COBOL Program |
| Function | Print the transaction detail report |
| Source Version | CardDemo_v2.0-25-gdb72e6b-235, 2025-04-29 |

---

## 4. Environment Division — File Assignments

| Logical Name | DD Name | Organization | Access | Key Field | Mode |
|---|---|---|---|---|---|
| `TRANSACT-FILE` | `TRANFILE` | Sequential | Sequential | N/A | INPUT |
| `XREF-FILE` | `CARDXREF` | INDEXED (KSDS) | Random | `FD-XREF-CARD-NUM` PIC X(16) | INPUT |
| `TRANTYPE-FILE` | `TRANTYPE` | INDEXED (KSDS) | Random | `FD-TRAN-TYPE` PIC X(02) | INPUT |
| `TRANCATG-FILE` | `TRANCATG` | INDEXED (KSDS) | Random | `FD-TRAN-CAT-KEY` (composite: TYPE X(02) + CAT 9(04)) | INPUT |
| `REPORT-FILE` | `TRANREPT` | Sequential | Sequential | N/A | OUTPUT |
| `DATE-PARMS-FILE` | `DATEPARM` | Sequential | Sequential | N/A | INPUT |

---

## 5. File Section — Record Layouts

### 5.1 TRANSACT-FILE (Input)
```
FD TRANSACT-FILE.
01 FD-TRANFILE-REC.
   05 FD-TRANS-DATA    PIC X(304)   [Transaction fields except proc timestamp]
   05 FD-TRAN-PROC-TS  PIC X(26)    [Processing timestamp — used for date filter]
   05 FD-FILLER        PIC X(20)
```
Total: 350 bytes. Read INTO `TRAN-RECORD` (CVTRA05Y). Note: The FD layout overlays the record to expose `FD-TRAN-PROC-TS` at position 305 for filtering without fully parsing the record.

### 5.2 XREF-FILE (Input)
```
FD XREF-FILE.
01 FD-CARDXREF-REC.
   05 FD-XREF-CARD-NUM    PIC X(16)
   05 FD-XREF-DATA        PIC X(34)
```
Total: 50 bytes.

### 5.3 TRANTYPE-FILE (Input)
```
FD TRANTYPE-FILE.
01 FD-TRANTYPE-REC.
   05 FD-TRAN-TYPE    PIC X(02)
   05 FD-TRAN-DATA    PIC X(58)
```
Total: 60 bytes. Read INTO `TRAN-TYPE-RECORD` (CVTRA03Y).

### 5.4 TRANCATG-FILE (Input)
```
FD TRANCATG-FILE.
01 FD-TRAN-CAT-RECORD.
   05 FD-TRAN-CAT-KEY.
      10 FD-TRAN-TYPE-CD    PIC X(02)
      10 FD-TRAN-CAT-CD     PIC 9(04)
   05 FD-TRAN-CAT-DATA      PIC X(54)
```
Total: 60 bytes. Read INTO `TRAN-CAT-RECORD` (CVTRA04Y).

### 5.5 REPORT-FILE (Output)
```
FD REPORT-FILE.
01 FD-REPTFILE-REC    PIC X(133).
```
133-byte report lines.

### 5.6 DATE-PARMS-FILE (Input)
```
FD DATE-PARMS-FILE.
01 FD-DATEPARM-REC    PIC X(80).
```
Read INTO `WS-DATEPARM-RECORD`:
```
01 WS-DATEPARM-RECORD.
   05 WS-START-DATE    PIC X(10)   [First 10 bytes: YYYY-MM-DD start date]
   05 FILLER           PIC X(01)   [Separator (space or slash)]
   05 WS-END-DATE      PIC X(10)   [Bytes 12-21: YYYY-MM-DD end date]
```

---

## 6. Copybooks Referenced

| Copybook | Working-Storage Record | Key Fields |
|---|---|---|
| `CVTRA05Y` | `TRAN-RECORD` | `TRAN-ID`, `TRAN-TYPE-CD`, `TRAN-CAT-CD`, `TRAN-AMT`, `TRAN-CARD-NUM`, `TRAN-PROC-TS` |
| `CVACT03Y` | `CARD-XREF-RECORD` | `XREF-CARD-NUM`, `XREF-ACCT-ID` |
| `CVTRA03Y` | `TRAN-TYPE-RECORD` | `TRAN-TYPE` X(02), `TRAN-TYPE-DESC` X(50) |
| `CVTRA04Y` | `TRAN-CAT-RECORD` | `TRAN-TYPE-CD` X(02), `TRAN-CAT-CD` 9(04), `TRAN-CAT-TYPE-DESC` X(50) |
| `CVTRA07Y` | Multiple report structures | See below |

### CVTRA07Y — Report Layout Structures
```
01 REPORT-NAME-HEADER.
   05 REPT-SHORT-NAME     PIC X(38) VALUE 'DALYREPT'
   05 REPT-LONG-NAME      PIC X(41) VALUE 'Daily Transaction Report'
   05 REPT-DATE-HEADER    PIC X(12) VALUE 'Date Range: '
   05 REPT-START-DATE     PIC X(10) VALUE SPACES   [Set at runtime]
   05 FILLER              PIC X(04) VALUE ' to '
   05 REPT-END-DATE       PIC X(10) VALUE SPACES   [Set at runtime]

01 TRANSACTION-DETAIL-REPORT.
   05 TRAN-REPORT-TRANS-ID      PIC X(16)
   05 FILLER                    PIC X(01) SPACES
   05 TRAN-REPORT-ACCOUNT-ID    PIC X(11)
   05 FILLER                    PIC X(01) SPACES
   05 TRAN-REPORT-TYPE-CD       PIC X(02)
   05 FILLER                    PIC X(01) '-'
   05 TRAN-REPORT-TYPE-DESC     PIC X(15)
   05 FILLER                    PIC X(01) SPACES
   05 TRAN-REPORT-CAT-CD        PIC 9(04)
   05 FILLER                    PIC X(01) '-'
   05 TRAN-REPORT-CAT-DESC      PIC X(29)
   05 FILLER                    PIC X(01) SPACES
   05 TRAN-REPORT-SOURCE        PIC X(10)
   05 FILLER                    PIC X(04) SPACES
   05 TRAN-REPORT-AMT           PIC -ZZZ,ZZZ,ZZZ.ZZ

01 TRANSACTION-HEADER-1    [Column headers: Trans ID, Account ID, Tran Type, Category, Source, Amount]
01 TRANSACTION-HEADER-2    PIC X(133) VALUE ALL '-'
01 REPORT-PAGE-TOTALS      [Page Total: ... +ZZZ,ZZZ,ZZZ.ZZ]
01 REPORT-ACCOUNT-TOTALS   [Account Total: ... +ZZZ,ZZZ,ZZZ.ZZ]
01 REPORT-GRAND-TOTALS     [Grand Total: ... +ZZZ,ZZZ,ZZZ.ZZ]
```

---

## 7. Working-Storage Data Structures

| Field | PIC | Purpose |
|---|---|---|
| `WS-DATEPARM-RECORD` | Group | Holds start and end dates from parameter file |
| `WS-FIRST-TIME` | PIC X VALUE 'Y' | Flag to write headers on first qualifying record |
| `WS-LINE-COUNTER` | PIC 9(09) COMP-3 VALUE 0 | Lines written since last header |
| `WS-PAGE-SIZE` | PIC 9(03) COMP-3 VALUE 20 | Lines per page before new header |
| `WS-BLANK-LINE` | PIC X(133) VALUE SPACES | Blank line for spacing |
| `WS-PAGE-TOTAL` | PIC S9(09)V99 VALUE 0 | Running total for current page |
| `WS-ACCOUNT-TOTAL` | PIC S9(09)V99 VALUE 0 | Running total for current account/card |
| `WS-GRAND-TOTAL` | PIC S9(09)V99 VALUE 0 | Running total for entire report |
| `WS-CURR-CARD-NUM` | PIC X(16) VALUE SPACES | Tracks current card for account break detection |
| `APPL-RESULT` | PIC S9(9) COMP | 88 levels: APPL-AOK (0), APPL-EOF (16) |
| `END-OF-FILE` | PIC X(01) VALUE 'N' | EOF flag |
| `ABCODE`/`TIMING` | PIC S9(9) BINARY | Abend parameters |

---

## 8. Procedure Division — Program Flow

### 8.1 Main Control (lines 159–217)
```
DISPLAY 'START OF EXECUTION OF PROGRAM CBTRN03C'
PERFORM 0000-TRANFILE-OPEN
PERFORM 0100-REPTFILE-OPEN
PERFORM 0200-CARDXREF-OPEN
PERFORM 0300-TRANTYPE-OPEN
PERFORM 0400-TRANCATG-OPEN
PERFORM 0500-DATEPARM-OPEN

PERFORM 0550-DATEPARM-READ   [Read start/end dates]

PERFORM UNTIL END-OF-FILE = 'Y'
    IF END-OF-FILE = 'N'
        PERFORM 1000-TRANFILE-GET-NEXT
        IF TRAN-PROC-TS(1:10) >= WS-START-DATE
           AND TRAN-PROC-TS(1:10) <= WS-END-DATE
            CONTINUE   [within date range — falls through to report write]
        ELSE
            NEXT SENTENCE   [outside range — skip this record]
        END-IF
        IF END-OF-FILE = 'N'
            DISPLAY TRAN-RECORD
            [Account break detection]
            IF WS-CURR-CARD-NUM NOT= TRAN-CARD-NUM
                IF WS-FIRST-TIME = 'N'
                    PERFORM 1120-WRITE-ACCOUNT-TOTALS
                END-IF
                MOVE TRAN-CARD-NUM TO WS-CURR-CARD-NUM, FD-XREF-CARD-NUM
                PERFORM 1500-A-LOOKUP-XREF
            END-IF
            [Type and category lookups]
            MOVE TRAN-TYPE-CD TO FD-TRAN-TYPE
            PERFORM 1500-B-LOOKUP-TRANTYPE
            MOVE TRAN-TYPE-CD/TRAN-CAT-CD to FD-TRAN-CAT-KEY
            PERFORM 1500-C-LOOKUP-TRANCATG
            PERFORM 1100-WRITE-TRANSACTION-REPORT
        ELSE
            [EOF branch — write final totals]
            ADD TRAN-AMT TO WS-PAGE-TOTAL WS-ACCOUNT-TOTAL
            PERFORM 1110-WRITE-PAGE-TOTALS
            PERFORM 1110-WRITE-GRAND-TOTALS
        END-IF
    END-IF
END-PERFORM

PERFORM 9000-9500 (close all files)
DISPLAY 'END OF EXECUTION OF PROGRAM CBTRN03C'
GOBACK
```

**Structural note on date filter (lines 173–178):** The date range filter uses `CONTINUE` when in range and `NEXT SENTENCE` when out of range. In modern COBOL, `NEXT SENTENCE` jumps to the period after the IF, which in this structure means bypassing the report write and proceeding to the PERFORM UNTIL check. However, the report detail paragraphs at lines 179–205 are inside the `IF END-OF-FILE = 'N'` block that follows — this means out-of-range records still reach the EOF/totals logic in the ELSE branch if END-OF-FILE happens to be 'Y' at that point. The logic is convoluted and likely a defect — transactions read after EOF sets END-OF-FILE='Y' (which cannot happen) would be processed differently. In practice, when END-OF-FILE='N' and the record is out of range, NEXT SENTENCE skips to the END-IF at line 205 and loops. This is functionally correct but the CONTINUE/NEXT SENTENCE pattern is confusing.

### 8.2 Paragraph-by-Paragraph Description

| Paragraph | Lines | Action |
|---|---|---|
| `0550-DATEPARM-READ` | 220–243 | Reads one record from DATE-PARMS-FILE into WS-DATEPARM-RECORD. Sets WS-START-DATE and WS-END-DATE. Abends on error; sets EOF and exits on status '10'. DISPLAYs 'Reporting from [start] to [end]'. |
| `1000-TRANFILE-GET-NEXT` | 248–272 | Sequential READ of TRANSACT-FILE into TRAN-RECORD. EVALUATE status: '00'->continue, '10'->EOF, other->abend. |
| `1100-WRITE-TRANSACTION-REPORT` | 274–290 | First-time: sets WS-FIRST-TIME='N', copies dates to REPT-START/END-DATE, calls 1120-WRITE-HEADERS. On page boundary (WS-LINE-COUNTER MOD WS-PAGE-SIZE = 0): calls 1110-WRITE-PAGE-TOTALS and 1120-WRITE-HEADERS. Adds TRAN-AMT to WS-PAGE-TOTAL and WS-ACCOUNT-TOTAL. Calls 1120-WRITE-DETAIL. |
| `1110-WRITE-PAGE-TOTALS` | 293–304 | Moves WS-PAGE-TOTAL to REPT-PAGE-TOTAL. Writes REPORT-PAGE-TOTALS record. Adds WS-PAGE-TOTAL to WS-GRAND-TOTAL. Resets WS-PAGE-TOTAL=0. Writes TRANSACTION-HEADER-2. Increments WS-LINE-COUNTER. |
| `1120-WRITE-ACCOUNT-TOTALS` | 306–316 | Moves WS-ACCOUNT-TOTAL to REPT-ACCOUNT-TOTAL. Writes REPORT-ACCOUNT-TOTALS. Resets WS-ACCOUNT-TOTAL=0. Writes header-2. |
| `1110-WRITE-GRAND-TOTALS` | 318–322 | Moves WS-GRAND-TOTAL to REPT-GRAND-TOTAL. Writes REPORT-GRAND-TOTALS. |
| `1120-WRITE-HEADERS` | 324–341 | Writes REPORT-NAME-HEADER, blank line, TRANSACTION-HEADER-1, TRANSACTION-HEADER-2. Increments WS-LINE-COUNTER for each. |
| `1111-WRITE-REPORT-REC` | 343–359 | Physical WRITE of FD-REPTFILE-REC. Checks TRANREPT-STATUS for '00'. Abends on non-zero status. |
| `1120-WRITE-DETAIL` | 361–374 | INITIALIZEs TRANSACTION-DETAIL-REPORT. Populates: TRAN-ID, XREF-ACCT-ID (from XREF lookup), TRAN-TYPE-CD + TRAN-TYPE-DESC (from TRANTYPE lookup), TRAN-CAT-CD + TRAN-CAT-TYPE-DESC (from TRANCATG lookup), TRAN-SOURCE, TRAN-AMT. Writes to REPORT-FILE. Increments WS-LINE-COUNTER. |
| `1500-A-LOOKUP-XREF` | 484–492 | Keyed READ of XREF-FILE by FD-XREF-CARD-NUM. INVALID KEY: DISPLAY invalid card, move '23' to IO-STATUS, 9910-DISPLAY-IO-STATUS, **9999-ABEND-PROGRAM**. |
| `1500-B-LOOKUP-TRANTYPE` | 494–502 | Keyed READ of TRANTYPE-FILE by FD-TRAN-TYPE. INVALID KEY: DISPLAY invalid type, abend. |
| `1500-C-LOOKUP-TRANCATG` | 504–512 | Keyed READ of TRANCATG-FILE by FD-TRAN-CAT-KEY. INVALID KEY: DISPLAY invalid key, abend. |

---

## 9. Report Structure

The REPORT-FILE produces lines of exactly 133 characters in the following pattern:

```
DALYREPT          Daily Transaction Report          Date Range: YYYY-MM-DD to YYYY-MM-DD
[blank line]
Transaction ID   Account ID   Transaction Type        Tran Category                     Tran Source    Amount
---[133 dashes]---
[detail line: trans-id acct-id type-cd-type-desc cat-cd-cat-desc source amount]
[detail line: ...]
...
Page Total....................................................................+ZZZ,ZZZ,ZZZ.ZZ
---[133 dashes]---
[headers repeat]
...
Account Total................................................................+ZZZ,ZZZ,ZZZ.ZZ
[blank]
Grand Total...................................................................+ZZZ,ZZZ,ZZZ.ZZ
```

---

## 10. Business Logic and Processing Rules

1. **Date Range Filter:** Only transactions with `TRAN-PROC-TS(1:10)` (first 10 characters = YYYY-MM-DD) between WS-START-DATE and WS-END-DATE inclusive are included in the report. Out-of-range transactions are silently skipped.

2. **Account Break Detection:** When TRAN-CARD-NUM changes, account totals for the previous card are written (if not first record). Account total accumulates all qualifying transactions for the same card number.

3. **Page Break at 20 Lines:** When `WS-LINE-COUNTER MOD WS-PAGE-SIZE = 0` (every 20 lines), the current page total is written and headers are reprinted. WS-PAGE-SIZE is set to 20 (COMP-3).

4. **Reference Data Lookups:** For each transaction, three keyed lookups are performed — XREF (on card-number change only), TRANTYPE (every record), and TRANCATG (every record). Any lookup failure causes an immediate abend.

5. **Grand Total:** Accumulated via WS-GRAND-TOTAL; WS-PAGE-TOTAL is added to WS-GRAND-TOTAL when each page total is written.

---

## 11. Error Handling

| Error Condition | Detection | Action |
|---|---|---|
| File open failure | Status != '00' | DISPLAY error, 9910-DISPLAY-IO-STATUS, 9999-ABEND-PROGRAM |
| Date parm read error | Status not '00' or '10' | DISPLAY error, abend |
| Transaction read error | APPL-RESULT = 12 | DISPLAY error, abend |
| XREF key not found | INVALID KEY | DISPLAY error, abend (fatal — unlike CBTRN01C) |
| TRANTYPE key not found | INVALID KEY | DISPLAY error, abend |
| TRANCATG key not found | INVALID KEY | DISPLAY error, abend |
| Report write failure | Status != '00' | DISPLAY error, abend |
| File close failures | Status != '00' | DISPLAY error, abend |

---

## 12. Return Codes

| Condition | Return Code |
|---|---|
| Normal completion | 0 (implicit GOBACK) |
| Any I/O error or reference data not found | U0999 abend via CEE3ABD |

---

## 13. EOF Totals Defect

The EOF branch of the main loop (lines 197–204, the `ELSE` when `END-OF-FILE = 'N'` is false) contains:
```
ADD TRAN-AMT TO WS-PAGE-TOTAL WS-ACCOUNT-TOTAL
PERFORM 1110-WRITE-PAGE-TOTALS
PERFORM 1110-WRITE-GRAND-TOTALS
```
This branch executes when `END-OF-FILE = 'Y'` — meaning after the last successful read, the next read sets EOF and control reaches the ELSE. At this point `TRAN-AMT` holds the amount from the LAST RECORD SUCCESSFULLY READ (not a new record). This causes the last record's amount to be double-counted: once in `1100-WRITE-TRANSACTION-REPORT` during its normal processing, and once again in this EOF branch. This is a defect that inflates both the page total and the grand total by the last transaction's amount.

Additionally, `1110-WRITE-GRAND-TOTALS` is called here but `1120-WRITE-ACCOUNT-TOTALS` is never called for the final account group at EOF — the last account's account-total is never written to the report.

---

## 14. Observations

- CBTRN03C is the reporting counterpart to CBTRN02C (posting). It reads the TRANSACT-FILE that CBTRN02C writes, plus the DALYREPT parameter file for date range filtering.
- The program reads TRANSACT-FILE as a SEQUENTIAL (not INDEXED) file, declared with `ORGANIZATION IS SEQUENTIAL`. This means any TRANSACT-FILE must be in sequential format for this program, not the KSDS format used by CBTRN02C. This may imply a sort/copy step between CBTRN02C and CBTRN03C in the JCL stream.
- Three reference lookups per transaction (XREF, TRANTYPE, TRANCATG) are all keyed random reads and all are fatal if not found. The transaction data quality must be perfect for this program to complete.
