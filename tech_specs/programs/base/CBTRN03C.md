# Technical Specification: CBTRN03C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | CBTRN03C                                             |
| Source File      | app/cbl/CBTRN03C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | Batch COBOL Program                                  |
| Transaction ID   | N/A (batch)                                          |
| Function         | Transaction detail report. Reads TRANSACT-FILE (sequential) and filters records by a date range read from DATE-PARMS-FILE. For each transaction in range: looks up account via XREF, transaction type description via TRANTYPE-FILE, and transaction category description via TRANCATG-FILE. Writes formatted 133-byte detail report records to REPORT-FILE. Handles page breaks every 20 lines, account totals on card-number change, and grand totals at end of run. |

---

## 2. Program Flow

### High-Level Flow

```
START
  OPEN INPUT: TRANSACT-FILE, XREF-FILE, TRANTYPE-FILE, TRANCATG-FILE, DATE-PARMS-FILE
  OPEN OUTPUT: REPORT-FILE

  0550-DATEPARM-READ
      Read WS-DATEPARM-RECORD: WS-START-DATE X(10), WS-END-DATE X(10)

  PERFORM UNTIL END-OF-FILE = 'Y':
      1000-TRANFILE-GET-NEXT (READ TRANSACT-FILE INTO TRAN-RECORD)
      IF TRAN-PROC-TS(1:10) within WS-START-DATE..WS-END-DATE:
          IF not EOF:
              DISPLAY TRAN-RECORD
              IF card changed (TRAN-CARD-NUM != WS-CURR-CARD-NUM):
                  IF not first time: 1120-WRITE-ACCOUNT-TOTALS
                  MOVE new card num; 1500-A-LOOKUP-XREF
              1500-B-LOOKUP-TRANTYPE (READ TRANTYPE-FILE)
              1500-C-LOOKUP-TRANCATG (READ TRANCATG-FILE)
              1100-WRITE-TRANSACTION-REPORT
                  IF WS-FIRST-TIME='Y': write headers (1120-WRITE-HEADERS)
                  IF line count % 20 = 0: write page totals + headers
                  ADD TRAN-AMT to WS-PAGE-TOTAL + WS-ACCOUNT-TOTAL
                  1120-WRITE-DETAIL (write formatted 133-byte detail line)
      ELSE (at EOF):
          ADD TRAN-AMT to WS-PAGE-TOTAL + WS-ACCOUNT-TOTAL
          1110-WRITE-PAGE-TOTALS
          1110-WRITE-GRAND-TOTALS

  CLOSE all 6 files
STOP
```

**Note on EOF handling**: The PROCEDURE DIVISION loop structure (lines 170–206) has the transaction filter check and DISPLAY outside the IF END-OF-FILE='N' check (lines 173–178 are outside). On EOF, the branch at line 197–204 (`ELSE ... ADD TRAN-AMT ... PERFORM 1110-WRITE-PAGE-TOTALS ... PERFORM 1110-WRITE-GRAND-TOTALS`) handles final totals.

### Paragraph-Level Detail

| Paragraph                | Lines     | Description |
|--------------------------|-----------|-------------|
| PROCEDURE DIVISION       | 159–217   | Opens 6 files; reads date parms; main loop; closes; GOBACK |
| 0550-DATEPARM-READ       | 220–243   | READ DATE-PARMS-FILE INTO WS-DATEPARM-RECORD; EVALUATE status; abend on error |
| 1000-TRANFILE-GET-NEXT   | 248–272   | READ TRANSACT-FILE INTO TRAN-RECORD; EOF sets END-OF-FILE='Y'; abend on error |
| 1100-WRITE-TRANSACTION-REPORT | 274–290 | First-time header write; page-break check (MOD function); ADD to totals; call 1120-WRITE-DETAIL |
| 1110-WRITE-PAGE-TOTALS   | 292–304   | MOVE WS-PAGE-TOTAL to REPT-PAGE-TOTAL; write REPORT-PAGE-TOTALS; ADD to WS-GRAND-TOTAL; reset WS-PAGE-TOTAL=0; write sub-header |
| 1120-WRITE-ACCOUNT-TOTALS | 306–316  | MOVE WS-ACCOUNT-TOTAL to REPT-ACCOUNT-TOTAL; write REPORT-ACCOUNT-TOTALS; reset WS-ACCOUNT-TOTAL=0 |
| 1110-WRITE-GRAND-TOTALS  | 318–322   | MOVE WS-GRAND-TOTAL to REPT-GRAND-TOTAL; write REPORT-GRAND-TOTALS |
| 1120-WRITE-HEADERS       | 324–341   | Write REPORT-NAME-HEADER, blank line, TRANSACTION-HEADER-1, TRANSACTION-HEADER-2 |
| 1111-WRITE-REPORT-REC    | 343–359   | WRITE FD-REPTFILE-REC; abend on failure |
| 1120-WRITE-DETAIL        | 361–374   | INITIALIZE TRANSACTION-DETAIL-REPORT; MOVE all fields; WRITE via 1111-WRITE-REPORT-REC; ADD 1 TO WS-LINE-COUNTER |
| 0000-TRANFILE-OPEN       | 376–392   | OPEN INPUT TRANSACT-FILE |
| 0100-REPTFILE-OPEN       | 394–410   | OPEN OUTPUT REPORT-FILE |
| 0200-CARDXREF-OPEN       | 412–428   | OPEN INPUT XREF-FILE (DD=CARDXREF) |
| 0300-TRANTYPE-OPEN       | 430–446   | OPEN INPUT TRANTYPE-FILE (DD=TRANTYPE) |
| 0400-TRANCATG-OPEN       | 448–464   | OPEN INPUT TRANCATG-FILE (DD=TRANCATG) |
| 0500-DATEPARM-OPEN       | 466–482   | OPEN INPUT DATE-PARMS-FILE (DD=DATEPARM) |
| 1500-A-LOOKUP-XREF       | 484–492   | READ XREF-FILE by FD-XREF-CARD-NUM; INVALID KEY: DISPLAY, abend |
| 1500-B-LOOKUP-TRANTYPE   | 494–502   | READ TRANTYPE-FILE by FD-TRAN-TYPE; INVALID KEY: DISPLAY, abend |
| 1500-C-LOOKUP-TRANCATG   | 504–512   | READ TRANCATG-FILE by FD-TRAN-CAT-KEY; INVALID KEY: DISPLAY, abend |
| 9000–9500-*-CLOSE        | 514–~620  | Close all 6 files |
| 9910-DISPLAY-IO-STATUS   | ~620+     | Standard I/O status formatter |
| 9999-ABEND-PROGRAM       | ~640+     | CALL 'CEE3ABD' |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook | Used In              | Contents |
|----------|----------------------|----------|
| CVTRA05Y | WORKING-STORAGE (line 93) | TRAN-RECORD (350 bytes): TRAN-ID X(16), TRAN-TYPE-CD X(2), TRAN-CAT-CD 9(4), TRAN-SOURCE X(10), TRAN-DESC X(100), TRAN-AMT S9(9)V99, TRAN-MERCHANT-* fields, TRAN-CARD-NUM X(16), TRAN-ORIG-TS X(26), TRAN-PROC-TS X(26) |
| CVACT03Y | WORKING-STORAGE (line 98) | CARD-XREF-RECORD (50 bytes): XREF-CARD-NUM X(16), XREF-CUST-ID, XREF-ACCT-ID |
| CVTRA03Y | WORKING-STORAGE (line 103) | TRAN-TYPE-RECORD: FD-TRAN-TYPE X(2) + TRAN-TYPE-DESC — **[UNRESOLVED]** complete layout requires app/cpy/CVTRA03Y.cpy |
| CVTRA04Y | WORKING-STORAGE (line 108) | TRAN-CAT-RECORD: FD-TRAN-CAT-KEY (TYPE-CD + CAT-CD) + TRAN-CAT-TYPE-DESC — **[UNRESOLVED]** complete layout requires app/cpy/CVTRA04Y.cpy |
| CVTRA07Y | WORKING-STORAGE (line 113) | Report line layouts: REPORT-NAME-HEADER, TRANSACTION-HEADER-1, TRANSACTION-HEADER-2, TRANSACTION-DETAIL-REPORT (133 bytes with fields: TRAN-REPORT-TRANS-ID, TRAN-REPORT-ACCOUNT-ID, TRAN-REPORT-TYPE-CD, TRAN-REPORT-TYPE-DESC, TRAN-REPORT-CAT-CD, TRAN-REPORT-CAT-DESC, TRAN-REPORT-SOURCE, TRAN-REPORT-AMT), REPORT-PAGE-TOTALS (REPT-PAGE-TOTAL), REPORT-ACCOUNT-TOTALS (REPT-ACCOUNT-TOTAL), REPORT-GRAND-TOTALS (REPT-GRAND-TOTAL), REPT-START-DATE, REPT-END-DATE — **[UNRESOLVED]** complete layout requires app/cpy/CVTRA07Y.cpy |

### File Description Records

| FD Name          | DD Name   | Key                                     | RECLN |
|------------------|-----------|-----------------------------------------|-------|
| TRANSACT-FILE    | TRANFILE  | Sequential (no key in FD)               | 350 (FD-TRANS-DATA X(304) + FD-TRAN-PROC-TS X(26) + FD-FILLER X(20)) |
| XREF-FILE        | CARDXREF  | FD-XREF-CARD-NUM X(16)                  | 50    |
| TRANTYPE-FILE    | TRANTYPE  | FD-TRAN-TYPE X(02)                      | 60 (FD-TRAN-TYPE X(2) + FD-TRAN-DATA X(58)) |
| TRANCATG-FILE    | TRANCATG  | FD-TRAN-CAT-KEY (FD-TRAN-TYPE-CD X(2) + FD-TRAN-CAT-CD 9(4)) | 60 (key 6 + FD-TRAN-CAT-DATA X(54)) |
| REPORT-FILE      | TRANREPT  | Sequential                              | 133   |
| DATE-PARMS-FILE  | DATEPARM  | Sequential                              | 80    |

### Key Working Storage Variables

| Variable          | PIC           | Purpose |
|-------------------|---------------|---------|
| WS-START-DATE     | X(10)         | Report start date (YYYY-MM-DD) from DATEPARM |
| WS-END-DATE       | X(10)         | Report end date (YYYY-MM-DD) from DATEPARM |
| WS-FIRST-TIME     | X VALUE 'Y'   | Flag; 'N' after first report header is written |
| WS-LINE-COUNTER   | 9(09) COMP-3  | Lines written since last page break; triggers headers every 20 lines (WS-PAGE-SIZE=20) |
| WS-PAGE-SIZE      | 9(03) COMP-3 = 20 | Lines per page |
| WS-PAGE-TOTAL     | S9(09)V99     | Accumulated transaction amounts for current page |
| WS-ACCOUNT-TOTAL  | S9(09)V99     | Accumulated transaction amounts for current card/account |
| WS-GRAND-TOTAL    | S9(09)V99     | Grand total across all pages |
| WS-CURR-CARD-NUM  | X(16)         | Current card number; used to detect account change |
| END-OF-FILE       | X(01)         | Loop control; 'Y' on TRANSACT EOF |
| APPL-RESULT       | S9(9) COMP    | Result code: 0=AOK, 16=EOF |

---

## 4. CICS Commands Used

None. Batch program.

---

## 5. File/Dataset Access

| DD Name   | File Object      | Org        | Access     | Open Mode | Purpose |
|-----------|------------------|------------|------------|-----------|---------|
| TRANFILE  | TRANSACT-FILE    | Sequential | Sequential | INPUT     | Driving file: all transaction records |
| TRANREPT  | REPORT-FILE      | Sequential | Sequential | OUTPUT    | Formatted 133-byte report lines |
| CARDXREF  | XREF-FILE        | KSDS       | Random     | INPUT     | Card-to-account lookup; provides XREF-ACCT-ID for report |
| TRANTYPE  | TRANTYPE-FILE    | KSDS       | Random     | INPUT     | Transaction type code to description lookup |
| TRANCATG  | TRANCATG-FILE    | KSDS       | Random     | INPUT     | Transaction category code to description lookup |
| DATEPARM  | DATE-PARMS-FILE  | Sequential | Sequential | INPUT     | Single-record date range file: start date + end date |

---

## 6. Screen Interaction

None. Batch program.

---

## 7. Called Programs / Transfers

| Called Program | Type        | Purpose |
|----------------|-------------|---------|
| CEE3ABD        | Static CALL | LE forced abend |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| Any OPEN failure | DISPLAY error; 9910; 9999 abend |
| DATEPARM read error (non-00/10) | DISPLAY 'ERROR READING DATEPARM FILE'; 9910; abend |
| DATEPARM EOF | MOVE 'Y' TO END-OF-FILE (skip entire report) |
| TRANSACT read error | DISPLAY 'ERROR READING TRANSACTION FILE'; 9910; abend |
| XREF INVALID KEY | DISPLAY 'INVALID CARD NUMBER: ' + card num; MOVE 23 TO IO-STATUS; 9910; abend |
| TRANTYPE INVALID KEY | DISPLAY 'INVALID TRANSACTION TYPE: ' + type; abend |
| TRANCATG INVALID KEY | DISPLAY 'INVALID TRAN CATG KEY: ' + key; abend |
| REPORT-FILE write failure | DISPLAY 'ERROR WRITING REPTFILE'; 9910; abend |
| Any CLOSE failure | DISPLAY error; 9910; abend |

**Note**: XREF, TRANTYPE, and TRANCATG lookup failures all cause program abend rather than soft-error handling. This means every transaction in the date range must have resolvable cross-references.

---

## 9. Business Rules

1. **Date filter**: Only transactions where TRAN-PROC-TS(1:10) falls between WS-START-DATE and WS-END-DATE (inclusive, string comparison on YYYY-MM-DD format) are reported. Out-of-range records are silently skipped.
2. **Page break at 20 lines**: FUNCTION MOD(WS-LINE-COUNTER, WS-PAGE-SIZE) = 0 triggers page totals and new headers. WS-PAGE-SIZE is hardcoded at 20.
3. **Account grouping by card number**: When TRAN-CARD-NUM changes, account totals for the previous card are written before processing the new card's XREF lookup. WS-FIRST-TIME prevents spurious totals on the very first record.
4. **Lookup keys for TRANCATG**: The composite key FD-TRAN-CAT-KEY is populated by moving TRAN-TYPE-CD to FD-TRAN-TYPE-CD (within FD-TRAN-CAT-KEY) and TRAN-CAT-CD to FD-TRAN-CAT-CD. Both must match for a successful read.
5. **DATEPARM format**: Single 80-byte record with WS-START-DATE at bytes 1-10, a filler byte at byte 11, and WS-END-DATE at bytes 12-21.
6. **Grand total timing**: WS-GRAND-TOTAL is accumulated inside 1110-WRITE-PAGE-TOTALS (ADD WS-PAGE-TOTAL TO WS-GRAND-TOTAL), not directly from TRAN-AMT. So the grand total is the sum of page totals, which should equal the sum of all transaction amounts in the date range.

---

## 10. Inputs and Outputs

### Inputs

| Source     | Description |
|------------|-------------|
| TRANFILE   | TRANSACT-FILE sequential — all transaction records |
| DATEPARM   | Single-record file: report start date + end date |
| CARDXREF   | KSDS cross-reference: card-to-account mapping |
| TRANTYPE   | KSDS transaction type description lookup |
| TRANCATG   | KSDS transaction category description lookup |

### Outputs

| Destination | RECLN | Description |
|-------------|-------|-------------|
| TRANREPT    | 133   | Formatted transaction detail report: headers, detail lines, page totals, account totals, grand total |
| SYSOUT      | N/A   | Start/end execution messages; TRAN-AMT display at EOF; page total display at EOF; DISPLAY TRAN-RECORD per processed transaction |

---

## 11. Key Variables and Their Purpose

| Variable          | Purpose |
|-------------------|---------|
| TRAN-RECORD       | Working area from CVTRA05Y; used for date filter, card-number change detection, and all report fields |
| WS-START-DATE / WS-END-DATE | Date range from DATEPARM; compared to TRAN-PROC-TS(1:10) |
| WS-CURR-CARD-NUM  | Previous card number; change detection triggers account total write |
| WS-LINE-COUNTER   | COMP-3 counter driving 20-line page breaks via FUNCTION MOD |
| WS-PAGE-TOTAL / WS-ACCOUNT-TOTAL / WS-GRAND-TOTAL | Three-level accumulator hierarchy for report totals |
| XREF-ACCT-ID      | Account ID obtained from XREF lookup; moved to TRAN-REPORT-ACCOUNT-ID in report |
| TRAN-TYPE-DESC    | Transaction type description from TRANTYPE lookup; placed in report detail line |
| TRAN-CAT-TYPE-DESC | Category description from TRANCATG lookup; placed in report detail line |
