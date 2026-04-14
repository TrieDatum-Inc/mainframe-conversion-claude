# Technical Specification: COCRDLIC

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COCRDLIC                                             |
| Source File      | app/cbl/COCRDLIC.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CCLI (LIT-THISTRANID, line 182)                      |
| Function         | Lists credit cards for browsing and selection. Displays up to 7 card records per page (CARD-NUM, ACCT-ID, ACTIVE-STATUS) from the CARDDAT VSAM file via sequential browse (STARTBR/READNEXT for forward, STARTBR/READPREV for backward). Supports optional account ID and card number filter criteria. User can select a row with 'S' (view detail via COCRDSLC) or 'U' (update via COCRDUPC). PF3 returns to main menu (COMEN01C). PF7 pages backward, PF8 pages forward. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CCLI and COMMAREA)

INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA

IF EIBCALEN = 0:
    INITIALIZE CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA
    Set defaults: CDEMO-USRTYP-USER, CDEMO-PGM-ENTER, CA-FIRST-PAGE, CA-LAST-PAGE-NOT-SHOWN

ELSE:
    MOVE DFHCOMMAREA(1:LEN) TO CARDDEMO-COMMAREA
    MOVE DFHCOMMAREA(LEN+1:LEN2) TO WS-THIS-PROGCOMMAREA

IF CDEMO-PGM-ENTER AND CDEMO-FROM-PROGRAM NOT = COCRDLIC:
    INITIALIZE WS-THIS-PROGCOMMAREA (fresh start from other program)
    SET CA-FIRST-PAGE, CA-LAST-PAGE-NOT-SHOWN

PERFORM YYYY-STORE-PFKEY

IF EIBCALEN > 0 AND CDEMO-FROM-PROGRAM = COCRDLIC:
    PERFORM 2000-RECEIVE-MAP (receive and edit screen inputs)

Validate AID: ENTER/PF03/PF07/PF08 = valid; else treat as ENTER

IF PF03 AND CDEMO-FROM-PROGRAM = COCRDLIC:
    XCTL to COMEN01C

IF PF08: preserve CA-LAST-PAGE flags; else reset CA-LAST-PAGE-NOT-SHOWN

EVALUATE TRUE:
    WHEN INPUT-ERROR:
        If no filter errors: PERFORM 9000-READ-FORWARD
        PERFORM 1000-SEND-MAP
    WHEN PF07 AND CA-FIRST-PAGE: (read first page again)
        PERFORM 9000-READ-FORWARD; SEND
    WHEN PF03 OR CDEMO-PGM-REENTER from non-COCRDLIC:
        Reinitialize; 9000-READ-FORWARD; SEND
    WHEN PF08 AND CA-NEXT-PAGE-EXISTS:
        ADD 1 TO WS-CA-SCREEN-NUM; 9000-READ-FORWARD; SEND
    WHEN PF07 AND NOT CA-FIRST-PAGE:
        SUBTRACT 1 FROM WS-CA-SCREEN-NUM; 9100-READ-BACKWARDS; SEND
    WHEN ENTER AND VIEW-REQUESTED-ON(I-SELECTED):
        MOVE row data to CDEMO-ACCT-ID / CDEMO-CARD-NUM
        XCTL to COCRDSLC
    WHEN ENTER AND UPDATE-REQUESTED-ON(I-SELECTED):
        MOVE row data to CDEMO-ACCT-ID / CDEMO-CARD-NUM
        XCTL to COCRDUPC
    WHEN OTHER:
        9000-READ-FORWARD; SEND

COMMON-RETURN:
    CICS RETURN TRANSID('CCLI') COMMAREA(WS-COMMAREA)
    WS-COMMAREA = CARDDEMO-COMMAREA || WS-THIS-PROGCOMMAREA
```

### Paragraph-Level Detail

| Paragraph             | Lines      | Description |
|-----------------------|------------|-------------|
| 0000-MAIN             | 298–602    | Entry point: initialize, commarea load, PF key dispatch, AID routing, EVALUATE for all cases, GO TO COMMON-RETURN |
| COMMON-RETURN         | 604–620    | Serialize COMMAREA + WS-THIS-PROGCOMMAREA into WS-COMMAREA; CICS RETURN TRANSID('CCLI') |
| 1000-SEND-MAP         | 624–641    | Orchestrates 1100 → 1200 → 1250 → 1300 → 1400 → 1500 |
| 1100-SCREEN-INIT      | 642–676    | LOW-VALUES to CCRDLIAO; fill title, tran, pgm, date, time, page number; set WS-NO-INFO-MESSAGE |
| 1200-SCREEN-ARRAY-INIT | 678–747   | Move WS-SCREEN-ROWS(1-7) ACCTNO/CARD-NUM/STATUS fields to CCRDLIAO output map fields; skip LOW-VALUES rows |
| 1250-SETUP-ARRAY-ATTRIBS | 748–834 | For each row: if empty or FLG-PROTECT-SELECT-ROWS-YES then DFHBMPRF; else DFHBMFSE; if select error then DFHRED |
| 1300-SETUP-SCREEN-ATTRS | 837–892  | Restore account/card filter fields to output; highlight invalid filters red; position cursor |
| 1400-SETUP-MESSAGE    | 895–935    | Determine info/error message: PF7-at-first, PF8-at-last, PF8-last-page-now-shown, inform-rec-actions |
| 1500-SEND-SCREEN      | 938–950    | CICS SEND MAP(CCRDLIA) MAPSET(COCRDLI) FROM(CCRDLIAO) CURSOR ERASE FREEKB |
| 2000-RECEIVE-MAP      | 951–961    | Calls 2100-RECEIVE-SCREEN, 2200-EDIT-INPUTS |
| 2100-RECEIVE-SCREEN   | 962–983    | CICS RECEIVE MAP INTO(CCRDLIAI); move ACCTSIDI/CARDSIDI/CRDSEL1-7I to work vars |
| 2200-EDIT-INPUTS      | 985–1001   | SET INPUT-OK; PERFORM 2210, 2220, 2250 |
| 2210-EDIT-ACCOUNT     | 1003–1034  | Validate account filter: blank/zero=blank flag; non-numeric=error; else valid; move to CDEMO-ACCT-ID |
| 2220-EDIT-CARD        | 1036–1071  | Validate card filter: blank/zero=blank flag; non-numeric=error; else valid; move CC-CARD-NUM-N to CDEMO-CARD-NUM |
| 2250-EDIT-ARRAY       | 1073–1121  | INSPECT WS-EDIT-SELECT-FLAGS tally S/U count; if >1: error WS-MORE-THAN-1-ACTION; scan rows for invalid chars; set I-SELECTED |
| 9000-READ-FORWARD     | 1123–1263  | STARTBR CARDDAT GTEQ WS-CARD-RID-CARDNUM; READNEXT loop up to 7 records; apply 9500-FILTER; capture first/last card key; peek extra record for CA-NEXT-PAGE-EXISTS; ENDBR |
| 9100-READ-BACKWARDS   | 1264–1380  | STARTBR from first-key; one READPREV to skip; READPREV loop filling rows in reverse order (counts down from 7); ENDBR |
| 9500-FILTER-RECORDS   | 1382–1411  | If FLG-ACCTFILTER-ISVALID: exclude if CARD-ACCT-ID != CC-ACCT-ID; if FLG-CARDFILTER-ISVALID: exclude if CARD-NUM != CC-CARD-NUM-N |
| YYYY-STORE-PFKEY      | (COPY 'CSSTRPFY', line 1416) | Common PF key mapping copybook; sets CCARD-AID-* flags |
| SEND-PLAIN-TEXT       | 1422–1435  | Debug utility: CICS SEND TEXT from WS-ERROR-MSG; CICS RETURN |
| SEND-LONG-TEXT        | 1441–1454  | Debug utility: CICS SEND TEXT from WS-LONG-MSG; CICS RETURN |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook   | Used In              | Contents |
|------------|----------------------|----------|
| CVCRD01Y   | WORKING-STORAGE (line 221) | CC-WORK-AREA: CC-ACCT-ID X(11)/N redefine 9(11), CC-CARD-NUM X(16)/N redefine 9(16), FOUND-CARDS-FOR-ACCOUNT flag |
| COCOM01Y   | WORKING-STORAGE (line 227) | CARDDEMO-COMMAREA: CDEMO-ACCT-ID, CDEMO-CARD-NUM, CDEMO-FROM-PROGRAM, CDEMO-FROM-TRANID, CDEMO-PGM-ENTER/REENTER, CDEMO-USRTYP-*, CDEMO-LAST-MAP/MAPSET |
| DFHBMSCA   | WORKING-STORAGE (line 267) | BMS attribute byte constants: DFHBMPRF, DFHBMFSE, DFHBMPRO, DFHBMDAR, DFHRED, DFHGREEN, DFHNEUTR |
| DFHAID     | WORKING-STORAGE (line 268) | EIBAID key constants; CCARD-AID-* defined via CSSTRPFY copybook logic |
| COTTL01Y   | WORKING-STORAGE (line 272) | CCDA-TITLE01, CCDA-TITLE02 screen title constants |
| COCRDLI    | WORKING-STORAGE (line 276) | BMS mapset copybook: CCRDLIAI (input) and CCRDLIAO (output); contains ACCTSIDI/O, CARDSIDI/O, CRDSEL1-7 I/O/A/C/L, ACCTNO1-7 O, CRDNUM1-7 O, CRDSTS1-7 O, ERRMSGO, INFOMSGO/C, TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO, PAGENOO |
| CSDAT01Y   | WORKING-STORAGE (line 279) | WS-CURDATE-DATA, WS-CURDATE-MONTH, WS-CURDATE-DAY, WS-CURDATE-YEAR, WS-CURDATE-MM-DD-YY, WS-CURTIME-* |
| CSMSG01Y   | WORKING-STORAGE (line 281) | Common message literals (e.g., CCDA-MSG-INVALID-KEY) |
| CSUSR01Y   | WORKING-STORAGE (line 285) | Signed-on user data |
| CVACT02Y   | WORKING-STORAGE (line 290) | CARD-RECORD layout: CARD-NUM X(16), CARD-ACCT-ID 9(11), CARD-CVV-CD 9(3), CARD-EMBOSSED-NAME X(50), CARD-EXPIRAION-DATE X(10), CARD-ACTIVE-STATUS X(1) |

### Key Working Storage Variables

| Variable                    | PIC / Structure | Purpose |
|-----------------------------|-----------------|---------|
| LIT-THISTRANID              | X(4) = 'CCLI'   | Transaction ID for CICS RETURN |
| LIT-THISPGM                 | X(8) = 'COCRDLIC' | Program name constant |
| LIT-CARD-FILE               | X(8) = 'CARDDAT ' | CICS file name for primary browse |
| LIT-CARDDTLPGM              | X(8) = 'COCRDSLC' | Target for 'S' selection |
| LIT-CARDUPDPGM              | X(8) = 'COCRDUPC' | Target for 'U' selection |
| LIT-MENUPGM                 | X(8) = 'COMEN01C' | Return target on PF3 |
| WS-MAX-SCREEN-LINES         | S9(4) COMP = 7  | Maximum rows per page |
| WS-EDIT-SELECT-FLAGS        | X(7)            | 7-byte array overlaid by WS-EDIT-SELECT-ARRAY (1 char per row) |
| WS-EDIT-SELECT(I)           | PIC X(1) OCCURS 7 | 88 SELECT-OK ('S','U'), VIEW-REQUESTED-ON ('S'), UPDATE-REQUESTED-ON ('U'), SELECT-BLANK (' '/LOW-VALUES) |
| WS-SCREEN-DATA              | X(196)          | 7-row × 28-byte array: ACCTNO X(11) + CARD-NUM X(16) + STATUS X(1) |
| WS-CA-LAST-CARDKEY          | X(27)           | Last card key seen this page (for PF8 next-page start) |
| WS-CA-FIRST-CARDKEY         | X(27)           | First card key seen this page (for PF7 prev-page start) |
| WS-CA-SCREEN-NUM            | PIC 9(1)        | Current page number; 88 CA-FIRST-PAGE = 1 |
| WS-CA-LAST-PAGE-DISPLAYED   | PIC 9(1)        | 88 CA-LAST-PAGE-SHOWN=0, CA-LAST-PAGE-NOT-SHOWN=9 |
| WS-CA-NEXT-PAGE-IND         | PIC X(1)        | 88 CA-NEXT-PAGE-NOT-EXISTS=LOW-VALUES, CA-NEXT-PAGE-EXISTS='Y' |
| WS-FILTER-RECORD-FLAG       | PIC X(1)        | 88 WS-EXCLUDE-THIS-RECORD='0', WS-DONOT-EXCLUDE-THIS-RECORD='1' |
| I                           | S9(4) COMP      | Subscript for edit-array loop |
| I-SELECTED                  | S9(4) COMP      | Index of the selected row; 88 DETAIL-WAS-REQUESTED = 1 THRU 7 |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS HANDLE ABEND | 0000-MAIN (none present — COCRDLIC does NOT set HANDLE ABEND) | No abend handler installed |
| EXEC CICS RETURN TRANSID('CCLI') COMMAREA(WS-COMMAREA) | COMMON-RETURN (line 615) | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM(LIT-MENUPGM) COMMAREA | 0000-MAIN (line 402) | PF3 exit to COMEN01C |
| EXEC CICS XCTL PROGRAM(CCARD-NEXT-PROG) COMMAREA | 0000-MAIN (line 538, line 566) | 'S' selection → COCRDSLC; 'U' selection → COCRDUPC |
| EXEC CICS SEND MAP(CCRDLIA) MAPSET(COCRDLI) FROM(CCRDLIAO) CURSOR ERASE FREEKB | 1500-SEND-SCREEN (line 939) | Display card list screen |
| EXEC CICS RECEIVE MAP(CCRDLIA) MAPSET(COCRDLI) INTO(CCRDLIAI) | 2100-RECEIVE-SCREEN (line 963) | Receive user inputs |
| EXEC CICS STARTBR DATASET(CARDDAT) RIDFLD GTEQ | 9000-READ-FORWARD (line 1129), 9100-READ-BACKWARDS (line 1273) | Begin forward/backward browse of CARDDAT |
| EXEC CICS READNEXT DATASET(CARDDAT) INTO(CARD-RECORD) | 9000-READ-FORWARD (line 1146, 1197) | Forward browse loop; extra read to detect next page |
| EXEC CICS READPREV DATASET(CARDDAT) INTO(CARD-RECORD) | 9100-READ-BACKWARDS (line 1294, 1322) | Backward browse loop |
| EXEC CICS ENDBR FILE(CARDDAT) | 9000-READ-FORWARD (line 1258), 9100-READ-BACKWARDS (line 1375) | End browse |

---

## 5. File/Dataset Access

| CICS File Name | Access Type | Purpose |
|----------------|-------------|---------|
| CARDDAT        | STARTBR/READNEXT/READPREV/ENDBR | Sequential browse of card file for pagination display |

The browse key is WS-CARD-RID-CARDNUM (16 bytes, CARD-NUM only). The ACCT-ID portion of WS-CARD-RID is not used in keyed operations (the ACCT-ID key components are commented out in lines 449, 475, 490, 506).

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COCRDLI    | CCRDLIA | CCLI        |

**Key Screen Fields:**

| Field         | Direction | Description |
|---------------|-----------|-------------|
| ACCTSIDI/O    | I/O       | Account ID filter (optional, 11 digits) |
| CARDSIDI/O    | I/O       | Card number filter (optional, 16 digits) |
| CRDSEL1-7 I/O | I/O       | Selection code per row: 'S'=view, 'U'=update, blank=none |
| ACCTNO1-7 O   | Output    | Account ID for each displayed row |
| CRDNUM1-7 O   | Output    | Card number for each displayed row |
| CRDSTS1-7 O   | Output    | Card active status for each displayed row |
| PAGENOO       | Output    | Current page number (WS-CA-SCREEN-NUM) |
| INFOMSGO/C    | Output    | Informational message and color attribute |
| ERRMSGO       | Output    | Error message |
| TITLE01O/TITLE02O | Output | Application title lines |
| TRNNAMEO      | Output    | Transaction ID (CCLI) |
| PGMNAMEO      | Output    | Program name (COCRDLIC) |
| CURDATEO      | Output    | Current date MM/DD/YY |
| CURTIMEO      | Output    | Current time HH:MM:SS |

**Navigation:**
- ENTER: process selection (view or update selected row)
- PF3: return to COMEN01C (main menu)
- PF7: page backward
- PF8: page forward
- Other keys: treated as ENTER

---

## 7. Called Programs / Transfers

| Program   | Method       | Condition |
|-----------|--------------|-----------|
| COMEN01C  | CICS XCTL    | PF3 pressed while CDEMO-FROM-PROGRAM = COCRDLIC |
| COCRDSLC  | CICS XCTL    | ENTER with SELECT-OK and VIEW-REQUESTED-ON(I-SELECTED) |
| COCRDUPC  | CICS XCTL    | ENTER with SELECT-OK and UPDATE-REQUESTED-ON(I-SELECTED) |

When transferring to COCRDSLC or COCRDUPC, the selected row's account and card number are placed in CDEMO-ACCT-ID and CDEMO-CARD-NUM of CARDDEMO-COMMAREA before XCTL.

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| Account filter non-numeric | FLG-ACCTFILTER-NOT-OK; INPUT-ERROR; FLG-PROTECT-SELECT-ROWS-YES; error message 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER' |
| Card filter non-numeric | FLG-CARDFILTER-NOT-OK; INPUT-ERROR; FLG-PROTECT-SELECT-ROWS-YES; 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER' |
| More than one row selected (I > 1) | INPUT-ERROR; WS-MORE-THAN-1-ACTION; highlight all selected rows red |
| Invalid selection code (not S/U/blank) | INPUT-ERROR; highlight offending row red; 'INVALID ACTION CODE' |
| PF7 already on first page | Message 'NO PREVIOUS PAGES TO DISPLAY'; re-read first page |
| PF8 with no more records | CA-NEXT-PAGE-NOT-EXISTS set; 'NO MORE PAGES TO DISPLAY' or 'NO MORE RECORDS TO SHOW' |
| READNEXT/READPREV RESP not NORMAL/ENDFILE | WS-FILE-ERROR-MESSAGE built with OPNAME/FILE/RESP/RESP2; set as WS-ERROR-MSG |
| EIBCALEN = 0 | Initialize commarea and reinitialize WS-THIS-PROGCOMMAREA |

No CICS HANDLE ABEND is installed. No PGMIDERR handler. Unexpected CICS responses produce a formatted error message displayed on screen.

---

## 9. Business Rules

1. **Dual browse mode**: Forward paging (PF8) uses STARTBR/READNEXT from WS-CA-LAST-CARD-NUM. Backward paging (PF7) uses STARTBR/READPREV from WS-CA-FIRST-CARD-NUM, reading backwards to fill the page from position 7 down to 1.
2. **Look-ahead for next-page detection**: After filling 7 rows, a one additional READNEXT is executed to peek whether more records exist (sets CA-NEXT-PAGE-EXISTS or CA-NEXT-PAGE-NOT-EXISTS). The look-ahead record also updates WS-CA-LAST-CARD-NUM for the next forward-page start key.
3. **Client-side filter applied post-read**: 9500-FILTER-RECORDS applies account and card number filters after each READNEXT/READPREV. Records not matching are excluded without stopping the browse. This means more than 7 reads may be needed to fill one page.
4. **Single selection rule**: Only one row may be selected per screen refresh. Multiple S/U entries trigger an INPUT-ERROR.
5. **ACCT-ID key not used in RIDFLD**: The browse key is 16-byte CARD-NUM only. The ACCT-ID portion of WS-CARD-RID (commented out at lines 449, 475, etc.) is not transmitted to CICS. This means all browse operations use the primary key path only.
6. **Fresh start on entry from other program**: When CDEMO-FROM-PROGRAM != COCRDLIC and CDEMO-PGM-ENTER, WS-THIS-PROGCOMMAREA is reinitialized. Page state from a previous visit is not preserved across round trips via other programs.
7. **COMMAREA extension**: WS-THIS-PROGCOMMAREA is appended to CARDDEMO-COMMAREA within WS-COMMAREA (2000 bytes total) passed in CICS RETURN. WS-THIS-PROGCOMMAREA starts at offset LENGTH(CARDDEMO-COMMAREA)+1.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (CCRDLIA) | ACCTSIDI — optional account filter; CARDSIDI — optional card filter; CRDSEL1-7I — row selection codes |
| COMMAREA  | CARDDEMO-COMMAREA (CDEMO-FROM-PROGRAM, CDEMO-PGM-ENTER/REENTER, CDEMO-ACCT-ID) + WS-THIS-PROGCOMMAREA (page tracking: first/last keys, screen num, next-page indicator) |
| CARDDAT   | Card records read via STARTBR/READNEXT/READPREV for display |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (CCRDLIA) | 7-row card list with select fields, account numbers, card numbers, statuses; filter echo; page number; info and error messages |
| COMMAREA  | WS-THIS-PROGCOMMAREA updated with current page keys and indicators; CDEMO-ACCT-ID/CDEMO-CARD-NUM set on row selection before XCTL |
| COCRDSLC or COCRDUPC | CDEMO-ACCT-ID + CDEMO-CARD-NUM of selected row passed via COMMAREA on XCTL |

---

## 11. Key Variables and Their Purpose

| Variable                  | Purpose |
|---------------------------|---------|
| WS-CA-FIRST-CARDKEY       | First card number on current page; used as start key for PF7 backward browse |
| WS-CA-LAST-CARDKEY        | Last card number on current page (or the look-ahead record); used as start key for PF8 forward browse |
| WS-CA-SCREEN-NUM          | Page counter; incremented on PF8, decremented on PF7 |
| WS-CA-NEXT-PAGE-IND       | Indicates whether a next page exists; controls PF8 message and action |
| WS-EDIT-SELECT-FLAGS       | 7-byte flat array of selection codes; tallied by INSPECT for multi-select detection |
| I-SELECTED                | Row subscript of the one selected row; used to index WS-SCREEN-DATA for CDEMO-ACCT-ID/CDEMO-CARD-NUM |
| WS-FILTER-RECORD-FLAG     | Controls whether current READNEXT/READPREV record is added to the display array |
