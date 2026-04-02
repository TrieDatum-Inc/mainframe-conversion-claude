# Technical Specification: COCRDLIC.CBL

## 1. Program Overview

| Attribute        | Value                              |
|------------------|------------------------------------|
| Program Name     | COCRDLIC                           |
| Source File      | app/cbl/COCRDLIC.cbl               |
| Layer            | Business Logic (Online / CICS)     |
| Function         | List Credit Cards                  |
| Transaction ID   | CCLI                               |
| Mapset           | COCRDLI                            |
| Map              | CCRDLIA                            |
| Date Written     | April 2022                         |
| Version Tag      | CardDemo_v1.0-15-g27d6c6f-68       |

### Purpose

COCRDLIC is the credit card list program. It displays a paginated list of credit card records from the CARDDAT VSAM file. It supports two operating modes:

1. **Admin mode** (no account filter): All cards across all accounts are listed, browseable forward and backward.
2. **Filtered mode** (account or card number filter entered): Only cards matching the supplied account ID and/or card number are displayed.

The user can type `S` against a row to view card details (transfers to COCRDSLC) or `U` to update the card (transfers to COCRDUPC). Only one selection per screen submission is permitted.

---

## 2. Artifact Inventory

| Artifact           | Type              | Location                          |
|--------------------|-------------------|-----------------------------------|
| COCRDLIC.CBL       | COBOL source      | app/cbl/COCRDLIC.cbl              |
| COCRDLI.BMS        | BMS mapset source | app/bms/COCRDLI.bms               |
| COCRDLI.CPY        | BMS map copybook  | app/cpy-bms/COCRDLI.CPY           |
| CVCRD01Y.CPY       | Working storage   | app/cpy/CVCRD01Y.cpy              |
| COCOM01Y.CPY       | COMMAREA layout   | app/cpy/COCOM01Y.cpy              |
| CVACT02Y.CPY       | Card record layout| app/cpy/CVACT02Y.cpy              |
| COTTL01Y.CPY       | Screen titles     | app/cpy/COTTL01Y.cpy              |
| CSDAT01Y.CPY       | Date formatting   | app/cpy/CSDAT01Y.cpy              |
| CSMSG01Y.CPY       | Common messages   | app/cpy/CSMSG01Y.cpy              |
| CSUSR01Y.CPY       | Signed-on user    | app/cpy/CSUSR01Y.cpy              |
| DFHBMSCA           | IBM BMS attribute | System copybook                   |
| DFHAID             | IBM AID keys      | System copybook                   |
| CSSTRPFY           | PFKey store logic | Inline COPY at line 1416          |

---

## 3. CICS Commands Used

| Command              | Location (line approx.) | Purpose                                          |
|----------------------|-------------------------|--------------------------------------------------|
| EXEC CICS RETURN     | COMMON-RETURN (~615)    | Return to CICS with TRANSID=CCLI and COMMAREA    |
| EXEC CICS XCTL       | ~402                    | Transfer control to COMEN01C (menu, on PF3)      |
| EXEC CICS XCTL       | ~538                    | Transfer control to COCRDSLC (card detail, on S) |
| EXEC CICS XCTL       | ~566                    | Transfer control to COCRDUPC (card update, on U) |
| EXEC CICS SEND MAP   | 1500-SEND-SCREEN (~939) | Send CCRDLIA map from CCRDLIAO with ERASE/FREEKB |
| EXEC CICS RECEIVE MAP| 2100-RECEIVE-SCREEN (~963)| Receive CCRDLIA map into CCRDLIAI               |
| EXEC CICS STARTBR    | 9000-READ-FORWARD (~1129)| Start browse of CARDDAT from a key position      |
| EXEC CICS READNEXT   | 9000-READ-FORWARD (~1146)| Read next card record in forward browse          |
| EXEC CICS ENDBR      | ~1258                   | End browse of CARDDAT                            |
| EXEC CICS STARTBR    | 9100-READ-BACKWARDS (~1273)| Start browse for backward page                |
| EXEC CICS READPREV   | 9100-READ-BACKWARDS (~1294, 1322)| Read previous record in backward browse |
| EXEC CICS ENDBR      | 9100-READ-BACKWARDS-EXIT (~1375)| End backward browse                     |
| EXEC CICS SEND TEXT  | SEND-PLAIN-TEXT (~1423) | Debug plain-text send (not for production)       |
| EXEC CICS SEND TEXT  | SEND-LONG-TEXT (~1442)  | Debug long-text send (not for production)        |

---

## 4. Copybooks Referenced

| Copybook      | Usage in COCRDLIC                                                            |
|---------------|-------------------------------------------------------------------------------|
| CVCRD01Y      | Defines CC-WORK-AREAS (CC-ACCT-ID, CC-CARD-NUM, CCARD-AID-xxx, CCARD-NEXT-PROG, etc.) |
| COCOM01Y      | Defines CARDDEMO-COMMAREA (CDEMO-FROM-PROGRAM, CDEMO-PGM-CONTEXT, CDEMO-ACCT-ID, etc.) |
| COCRDLI       | BMS symbolic map CCRDLIAI (input) / CCRDLIAO (output)                        |
| CVACT02Y      | Defines CARD-RECORD (CARD-NUM, CARD-ACCT-ID, CARD-CVV-CD, CARD-EMBOSSED-NAME, CARD-EXPIRAION-DATE, CARD-ACTIVE-STATUS) |
| COTTL01Y      | CCDA-TITLE01, CCDA-TITLE02 screen header title literals                      |
| CSDAT01Y      | WS-CURDATE-DATA, WS-CURDATE-MM, etc. — date/time formatting variables        |
| CSMSG01Y      | Common message literals                                                       |
| CSUSR01Y      | Signed-on user data                                                           |
| DFHBMSCA      | BMS attribute byte constants (DFHBMPRF, DFHBMFSE, DFHBMDAR, DFHRED, etc.)   |
| DFHAID        | AID key constants (DFHENTER, DFHPF3, etc.)                                   |
| CSSTRPFY      | In-line COPY at line 1416 — stores mapped PF key into CCARD-AID              |

---

## 5. Data Structures

### 5.1 Program-Specific COMMAREA Extension (WS-THIS-PROGCOMMAREA)

Defined at line 228. This structure is appended after CARDDEMO-COMMAREA in the full 2000-byte WS-COMMAREA passed on CICS RETURN.

| Field                        | PIC         | Description                                         |
|------------------------------|-------------|-----------------------------------------------------|
| WS-CA-LAST-CARD-NUM          | X(16)       | Card number of the last record on current page      |
| WS-CA-LAST-CARD-ACCT-ID      | 9(11)       | Account ID of the last record on current page       |
| WS-CA-FIRST-CARD-NUM         | X(16)       | Card number of the first record on current page     |
| WS-CA-FIRST-CARD-ACCT-ID     | 9(11)       | Account ID of the first record on current page      |
| WS-CA-SCREEN-NUM             | 9(1)        | Current page number (88 CA-FIRST-PAGE = 1)          |
| WS-CA-LAST-PAGE-DISPLAYED    | 9(1)        | 0=last page shown, 9=not yet shown                  |
| WS-CA-NEXT-PAGE-IND          | X(1)        | LOW-VALUES=no next page, 'Y'=next page exists       |
| WS-RETURN-FLAG               | X(1)        | LOW-VALUES=off, '1'=on                              |

### 5.2 Screen Data Buffer (WS-SCREEN-DATA)

Defined at line 251. Holds up to 7 rows of card data for the current page.

| Field                | PIC    | Description                                  |
|----------------------|--------|----------------------------------------------|
| WS-ROW-ACCTNO(1-7)   | X(11)  | Account number for each displayed row        |
| WS-ROW-CARD-NUM(1-7) | X(16)  | Card number for each displayed row           |
| WS-ROW-CARD-STATUS(1-7)| X(1) | Active status ('Y'/'N') for each row         |

### 5.3 CARD-RECORD (from CVACT02Y)

| Field                  | PIC     | Description                             |
|------------------------|---------|-----------------------------------------|
| CARD-NUM               | X(16)   | Primary key — 16-digit card number      |
| CARD-ACCT-ID           | 9(11)   | Associated account ID                   |
| CARD-CVV-CD            | 9(03)   | CVV security code                       |
| CARD-EMBOSSED-NAME     | X(50)   | Name embossed on card                   |
| CARD-EXPIRAION-DATE    | X(10)   | Expiry date in YYYY-MM-DD format        |
| CARD-ACTIVE-STATUS     | X(01)   | 'Y' = active, 'N' = inactive            |
| FILLER                 | X(59)   | Padding to record length 150            |

### 5.4 CARDDEMO-COMMAREA (from COCOM01Y)

| Field                  | PIC     | Description                                      |
|------------------------|---------|--------------------------------------------------|
| CDEMO-FROM-TRANID      | X(04)   | Transaction that invoked this program            |
| CDEMO-FROM-PROGRAM     | X(08)   | Program that invoked this program                |
| CDEMO-TO-TRANID        | X(04)   | Target transaction for XCTL                      |
| CDEMO-TO-PROGRAM       | X(08)   | Target program for XCTL                          |
| CDEMO-USER-ID          | X(08)   | Signed-on user ID                                |
| CDEMO-USER-TYPE        | X(01)   | 'A'=Admin, 'U'=User                              |
| CDEMO-PGM-CONTEXT      | 9(01)   | 0=ENTER (first time), 1=REENTER (re-display)     |
| CDEMO-ACCT-ID          | 9(11)   | Account ID filter passed between programs        |
| CDEMO-CARD-NUM         | 9(16)   | Card number filter passed between programs       |
| CDEMO-LAST-MAP         | X(7)    | Last map displayed                               |
| CDEMO-LAST-MAPSET      | X(7)    | Last mapset used                                 |

---

## 6. File Access

### CARDDAT (LIT-CARD-FILE = 'CARDDAT ')
- **Type**: VSAM KSDS
- **Primary key**: CARD-NUM X(16)
- **Access mode**: Sequential browse (STARTBR / READNEXT / READPREV / ENDBR)
- **Operations**:
  - STARTBR with GTEQ from WS-CARD-RID-CARDNUM (forward browse)
  - READNEXT to read up to 7 records per page, plus one peek-ahead to detect next page
  - STARTBR + READPREV for backward page navigation (paragraph 9100-READ-BACKWARDS)
  - ENDBR always called after read loop

### CARDAIX (LIT-CARD-FILE-ACCT-PATH = 'CARDAIX ')
- **Type**: VSAM Alternate Index path on CARDDAT, keyed by CARD-ACCT-ID
- **Note**: Defined in WS-CONSTANTS at line 214 but not directly used in the browse loop; the forward/backward browse uses CARDDAT primary key. Filtering by account is done in 9500-FILTER-RECORDS after READNEXT.

---

## 7. Program Flow — Paragraph-by-Paragraph

### 0000-MAIN (Entry Point, lines 297–621)

1. INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA.
2. SET WS-ERROR-MSG-OFF.
3. **COMMAREA load**: If EIBCALEN=0 (fresh start) or coming from menu program without REENTER flag, initialize CARDDEMO-COMMAREA and WS-THIS-PROGCOMMAREA, set CA-FIRST-PAGE and CA-LAST-PAGE-NOT-SHOWN; else move DFHCOMMAREA into both structures.
4. **Fresh-start reset**: If CDEMO-PGM-ENTER and FROM-PROGRAM is not this program, reinitialize WS-THIS-PROGCOMMAREA and set CA-FIRST-PAGE.
5. PERFORM YYYY-STORE-PFKEY — maps raw EIBAID into CCARD-AID value ('ENTER', 'PFK03', etc.).
6. **Receive map gate**: If EIBCALEN > 0 and FROM-PROGRAM = COCRDLIC, PERFORM 2000-RECEIVE-MAP (lines 951–956) to read and edit the screen inputs.
7. **PFKey validation**: Accepts ENTER, PFK03, PFK07, PFK08. Any other key is coerced to ENTER.
8. **PFK03 (Exit)**: If PFK03 and FROM-PROGRAM = this program, set CDEMO-TO-PROGRAM = COMEN01C and EXEC CICS XCTL to menu.
9. **Reset last-page flag**: If not PFK08, set CA-LAST-PAGE-NOT-SHOWN.
10. **Main dispatch EVALUATE** (lines 418–583):

| Condition                                      | Action                                                      |
|------------------------------------------------|-------------------------------------------------------------|
| INPUT-ERROR                                    | Read forward, send map with error message, COMMON-RETURN   |
| PFK07 AND CA-FIRST-PAGE                        | Read forward from first key, send map, COMMON-RETURN        |
| PFK03 or REENTER from different program        | Re-initialize, read forward, send map, COMMON-RETURN        |
| PFK08 AND CA-NEXT-PAGE-EXISTS                  | Advance page: set RID from last key, +1 screen num, read forward, send map |
| PFK07 AND NOT CA-FIRST-PAGE                    | Page back: set RID from first key, -1 screen num, 9100-READ-BACKWARDS |
| ENTER AND VIEW-REQUESTED-ON(I-SELECTED)        | Set CDEMO-ACCT-ID/CARD-NUM from row data, XCTL to COCRDSLC |
| ENTER AND UPDATE-REQUESTED-ON(I-SELECTED)      | Set CDEMO-ACCT-ID/CARD-NUM from row data, XCTL to COCRDUPC |
| OTHER                                          | Read forward from first key, send map, COMMON-RETURN        |

11. **Post-EVALUATE error check**: If INPUT-ERROR still set, set error msg and COMMON-RETURN.

### COMMON-RETURN (lines 604–619)
Sets FROM-TRANID/PROGRAM/MAPSET/MAP fields, packs CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA into WS-COMMAREA, then EXEC CICS RETURN TRANSID(CCLI).

### 1000-SEND-MAP (lines 624–637)
Driver for screen output. Calls in sequence:
- 1100-SCREEN-INIT
- 1200-SCREEN-ARRAY-INIT
- 1250-SETUP-ARRAY-ATTRIBS
- 1300-SETUP-SCREEN-ATTRS
- 1400-SETUP-MESSAGE
- 1500-SEND-SCREEN

### 1100-SCREEN-INIT (lines 642–674)
- Sets CCRDLIAO to LOW-VALUES.
- Populates header fields: TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO, PAGENOO (from WS-CA-SCREEN-NUM).
- Sets INFOMSGO and INFOMSGC to dark/empty.

### 1200-SCREEN-ARRAY-INIT (lines 678–743)
- Iterates rows 1–7.
- For each row: if WS-EACH-CARD(n) is not LOW-VALUES, moves CRDSEL, ACCTNO, CRDNUM, CRDSTS to the corresponding output fields CRDSELnO, ACCTNOnO, CRDNUMnO, CRDSTSnO of CCRDLIAO.

### 1250-SETUP-ARRAY-ATTRIBS (lines 748–832)
- For each row 1–7: if the row is empty (LOW-VALUES) or FLG-PROTECT-SELECT-ROWS-YES, set the selection field attribute to DFHBMPRF (protected).
- If the row has a selection error (WS-ROW-CRDSELECT-ERROR = '1'), set the attribute to RED and place '*' if blank.
- Otherwise set to DFHBMFSE (unprotected).
- Note: Row 1 uses DFHBMPRF on empty; rows 2-7 use DFHBMPRO on empty (minor asymmetry observed in source at lines 753 vs 766).

### 1300-SETUP-SCREEN-ATTRS (lines 837–889)
- If fresh start (EIBCALEN=0) or coming from menu, skips filter field display.
- Otherwise: moves CC-ACCT-ID / CC-CARD-NUM to ACCTSIDO/CARDSIDO based on filter validity flags.
- Positions cursor (length=-1) to ACCTSID if account filter error, to CARDSID if card filter error, to ACCTSID if all OK.
- Sets RED color on filter fields if they failed edit.

### 1400-SETUP-MESSAGE (lines 895–932)
- Evaluates conditions to set the appropriate info/error message:
  - PFK07 on first page: 'NO PREVIOUS PAGES TO DISPLAY'
  - PFK08 at last page: 'NO MORE PAGES TO DISPLAY'
  - PFK08 arriving at last page for first time: set WS-INFORM-REC-ACTIONS, mark CA-LAST-PAGE-SHOWN
  - No info message or next page exists: set WS-INFORM-REC-ACTIONS ('TYPE S FOR DETAIL, U TO UPDATE ANY RECORD')
- Moves WS-ERROR-MSG to ERRMSGO and WS-INFO-MSG to INFOMSGO.

### 1500-SEND-SCREEN (lines 938–948)
- EXEC CICS SEND MAP(CCRDLIA) MAPSET(COCRDLI) FROM(CCRDLIAO) CURSOR ERASE FREEKB.

### 2000-RECEIVE-MAP (lines 951–957)
- Calls 2100-RECEIVE-SCREEN then 2200-EDIT-INPUTS.

### 2100-RECEIVE-SCREEN (lines 962–979)
- EXEC CICS RECEIVE MAP(CCRDLIA) MAPSET(COCRDLI) INTO(CCRDLIAI).
- Moves ACCTSIDI to CC-ACCT-ID.
- Moves CARDSIDI to CC-CARD-NUM.
- Moves CRDSELnI (n=1..7) to WS-EDIT-SELECT(n).

### 2200-EDIT-INPUTS (lines 985–997)
- Sets INPUT-OK, FLG-PROTECT-SELECT-ROWS-NO.
- PERFORM 2210-EDIT-ACCOUNT.
- PERFORM 2220-EDIT-CARD.
- PERFORM 2250-EDIT-ARRAY.

### 2210-EDIT-ACCOUNT (lines 1003–1031)
- If CC-ACCT-ID is blank/zero: set FLG-ACCTFILTER-BLANK, clear CDEMO-ACCT-ID.
- If CC-ACCT-ID is non-numeric: set INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, FLG-PROTECT-SELECT-ROWS-YES, error message 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER'.
- Else: move to CDEMO-ACCT-ID, set FLG-ACCTFILTER-ISVALID.

### 2220-EDIT-CARD (lines 1036–1070)
- Same logic as 2210 for CC-CARD-NUM (16-digit numeric check).
- Error message: 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER'.

### 2250-EDIT-ARRAY (lines 1073–1117)
- If INPUT-ERROR already set, skip.
- Count how many CRDSELn contain 'S' or 'U'. If more than 1, set INPUT-ERROR, WS-MORE-THAN-1-ACTION, mark all selected rows with error flag.
- Loop rows 1–7: if SELECT-OK, save row index in I-SELECTED; if SELECT-BLANK, continue; otherwise set INPUT-ERROR and mark row error.

### 9000-READ-FORWARD (lines 1123–1260)
1. Clear WS-ALL-ROWS.
2. EXEC CICS STARTBR DATASET(CARDDAT) RIDFLD(WS-CARD-RID-CARDNUM) GTEQ.
3. Set WS-SCRN-COUNTER=0, CA-NEXT-PAGE-EXISTS, MORE-RECORDS-TO-READ.
4. PERFORM UNTIL READ-LOOP-EXIT:
   - EXEC CICS READNEXT.
   - On NORMAL/DUPREC: call 9500-FILTER-RECORDS; if not excluded, increment counter, store CARD-NUM/CARD-ACCT-ID/CARD-ACTIVE-STATUS in WS-SCREEN-ROWS.
   - If counter=1 and WS-CA-SCREEN-NUM=0, set WS-CA-SCREEN-NUM=1 and save first-record keys.
   - When counter = WS-MAX-SCREEN-LINES (7): save last-record keys, do one peek-ahead READNEXT to determine if next page exists.
   - On ENDFILE: set READ-LOOP-EXIT, CA-NEXT-PAGE-NOT-EXISTS; if page 1 and zero records, set WS-NO-RECORDS-FOUND.
5. EXEC CICS ENDBR.

### 9100-READ-BACKWARDS (lines 1264–1379)
1. Save WS-CA-FIRST-CARDKEY to WS-CA-LAST-CARDKEY.
2. EXEC CICS STARTBR DATASET(CARDDAT) RIDFLD(WS-CARD-RID-CARDNUM) GTEQ.
3. Set counter = WS-MAX-SCREEN-LINES + 1 (8).
4. Do one READPREV to step back past the start-of-current-page key.
5. PERFORM UNTIL READ-LOOP-EXIT:
   - READPREV.
   - On NORMAL/DUPREC: call 9500-FILTER-RECORDS; if not excluded, store record at WS-SCREEN-ROWS(WS-SCRN-COUNTER), decrement counter.
   - When counter=0: save first-record keys, set READ-LOOP-EXIT.
6. EXEC CICS ENDBR.

### 9500-FILTER-RECORDS (lines 1382–1410)
- If FLG-ACCTFILTER-ISVALID and CARD-ACCT-ID does not match CC-ACCT-ID: set WS-EXCLUDE-THIS-RECORD.
- If FLG-CARDFILTER-ISVALID and CARD-NUM does not match CC-CARD-NUM-N: set WS-EXCLUDE-THIS-RECORD.
- Otherwise set WS-DONOT-EXCLUDE-THIS-RECORD.

---

## 8. Inter-Program Interactions

| Direction  | Target Program | Mechanism       | Trigger Condition                               | Data Passed                              |
|------------|----------------|-----------------|-------------------------------------------------|------------------------------------------|
| Outbound   | COMEN01C       | EXEC CICS XCTL  | PFK03 while FROM-PROGRAM = COCRDLIC             | CARDDEMO-COMMAREA                        |
| Outbound   | COCRDSLC       | EXEC CICS XCTL  | ENTER + 'S' on a row                            | CARDDEMO-COMMAREA with CDEMO-ACCT-ID and CDEMO-CARD-NUM set |
| Outbound   | COCRDUPC       | EXEC CICS XCTL  | ENTER + 'U' on a row                            | CARDDEMO-COMMAREA with CDEMO-ACCT-ID and CDEMO-CARD-NUM set |
| Self-loop  | COCRDLIC       | EXEC CICS RETURN TRANSID(CCLI) | Normal screen re-display       | WS-COMMAREA = CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA |
| Inbound    | COMEN01C       | XCTL into COCRDLIC | Menu selection for card list function          | CARDDEMO-COMMAREA                        |
| Inbound    | COCRDSLC       | XCTL into COCRDLIC | Back navigation from card detail               | CARDDEMO-COMMAREA                        |
| Inbound    | COCRDUPC       | XCTL into COCRDLIC | Back navigation from card update               | CARDDEMO-COMMAREA                        |

---

## 9. Key Function Keys

| Key    | Action                                                    |
|--------|-----------------------------------------------------------|
| ENTER  | Process selection (S=detail, U=update) or refresh list    |
| PF3    | Exit to main menu (COMEN01C) via XCTL                     |
| PF7    | Page backward (READPREV browse)                           |
| PF8    | Page forward (READNEXT browse)                            |
| Other  | Treated as ENTER                                          |

---

## 10. Error Handling

| Condition                              | Error Message Set                                          | Behavior                                   |
|----------------------------------------|------------------------------------------------------------|--------------------------------------------|
| Account filter not numeric             | 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER'     | INPUT-ERROR, protect select rows           |
| Card filter not numeric                | 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER'     | INPUT-ERROR, protect select rows           |
| More than 1 row selected               | 'PLEASE SELECT ONLY ONE RECORD TO VIEW OR UPDATE'          | INPUT-ERROR, highlight all selected rows in RED |
| Invalid selection code (not S/U/blank) | 'INVALID ACTION CODE'                                      | INPUT-ERROR, highlight bad row in RED      |
| READNEXT/READPREV RESP not NORMAL      | WS-FILE-ERROR-MESSAGE (File Error: READ on CARDDAT returned RESP x,RESP2 y) | READ-LOOP-EXIT, display error |
| No records on page 1                   | WS-NO-RECORDS-FOUND ('NO RECORDS FOUND FOR THIS SEARCH CONDITION.') | Send map with no-records message |
| SEND MAP failure                       | WS-RESP-CD checked — no explicit recovery coded            | Implicit CICS default error handling       |
| CICS ABEND                             | SEND ABEND-DATA, EXEC CICS ABEND ABCODE('9999')            | Abend with code 9999                       |

---

## 11. Transaction Flow Context

```
COMEN01C (Menu)
    |-- XCTL --> COCRDLIC (CCLI) -- CICS RETURN(CCLI) loop for pagination
                    |-- XCTL 'S' --> COCRDSLC (CCDL)
                    |-- XCTL 'U' --> COCRDUPC (CCUP)
                    |-- XCTL PF3 --> COMEN01C
```

---

## 12. Business Rules

1. **Single-selection rule** (paragraph 2250-EDIT-ARRAY): Only one row may be marked 'S' or 'U' per submit. Multiple selections are rejected.
2. **Filter precedence**: Account number filter (11-digit) and card number filter (16-digit) are independent; either or both may be blank. If a filter is supplied it must be numeric.
3. **Page size**: Maximum 7 records per page (WS-MAX-SCREEN-LINES = 7, line 177).
4. **Peek-ahead pagination**: After filling a full page of 7, one extra READNEXT is done to test if another record exists. If it does, CA-NEXT-PAGE-EXISTS is set 'Y'; if ENDFILE, CA-NEXT-PAGE-NOT-EXISTS.
5. **Admin vs. non-admin**: The header comment states all cards for admin, filtered by COMMAREA ACCT for non-admin. The filtering is implemented in 9500-FILTER-RECORDS: if FLG-ACCTFILTER-ISVALID, only records matching CC-ACCT-ID pass.
6. **Name on embossed card is passed** through CDEMO-CARD-NUM / CDEMO-ACCT-ID in COMMAREA to child programs; the actual CARD-RECORD fields are not passed directly — they are re-read by COCRDSLC/COCRDUPC.
