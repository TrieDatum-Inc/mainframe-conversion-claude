# Technical Specification: COTRN00C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COTRN00C                                             |
| Source File      | app/cbl/COTRN00C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CT00 (WS-TRANID, line 37)                            |
| Function         | Transaction list/browse screen. Displays up to 10 transaction records per page from the TRANSACT VSAM KSDS file, using STARTBR/READNEXT/READPREV for forward/backward pagination. An optional transaction ID filter (TRNIDINI) limits results to IDs >= the entered value. Row selection via 'S' or 's' XCTLs to COTRN01C for detailed view. PF7=previous page, PF8=next page, PF3=back to previous menu. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CT00 and COMMAREA)

Clear WS-MESSAGE; SET ERR-FLG-OFF

IF EIBCALEN = 0:
    MOVE 'COSGN00C' TO CDEMO-FROM-PROGRAM
    PERFORM RETURN-TO-PREV-SCREEN

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        MOVE LOW-VALUES TO COTRN0AO
        PERFORM SEND-TRNLST-SCREEN (initial display, no receive)
    ELSE:
        PERFORM RECEIVE-TRNLST-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER:  PERFORM PROCESS-ENTER-KEY
            WHEN DFHPF3:    PERFORM RETURN-TO-PREV-SCREEN
            WHEN DFHPF7:    PERFORM PROCESS-PF7-KEY (previous page)
            WHEN DFHPF8:    PERFORM PROCESS-PF8-KEY (next page)
            WHEN OTHER:     Set ERR-FLG-ON; CCDA-MSG-INVALID-KEY; SEND-TRNLST-SCREEN

EXEC CICS RETURN TRANSID('CT00') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph               | Lines     | Description |
|-------------------------|-----------|-------------|
| MAIN-PARA               | 79–124    | Main entry: EIBCALEN check; first/reenter dispatch; AID evaluate; CICS RETURN |
| PROCESS-ENTER-KEY       | 129–192   | Scan TRNIDINI for new filter; check row selections (SEL-FLAG); XCTL to COTRN01C if selection found; else re-populate and send screen |
| PROCESS-PF7-KEY         | 197–225   | Set direction=backward; call POPULATE-TRAN-DATA reading backward; send screen |
| PROCESS-PF8-KEY         | 230–258   | Set direction=forward; call POPULATE-TRAN-DATA reading forward; send screen |
| RETURN-TO-PREV-SCREEN   | 263–273   | CDEMO-TO-PROGRAM=CDEMO-FROM-PROGRAM default; EXEC CICS XCTL |
| SEND-TRNLST-SCREEN      | 278–293   | POPULATE-HEADER-INFO; POPULATE-TRAN-DATA; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('COTRN0A') MAPSET('COTRN00') FROM(COTRN0AO) ERASE |
| RECEIVE-TRNLST-SCREEN   | 298–308   | CICS RECEIVE MAP('COTRN0A') MAPSET('COTRN00') INTO(COTRN0AI) RESP RESP2 |
| POPULATE-HEADER-INFO    | 313–333   | Fill header screen fields from literals and FUNCTION CURRENT-DATE |
| POPULATE-TRAN-DATA      | 338–490   | STARTBR TRANSACT; loop READNEXT/READPREV to fill 10 rows; look-ahead READNEXT to set NEXT-PAGE-FLG; ENDBR; fill COTRN0AO array fields |
| POPULATE-TRAN-ID        | 495–530   | Convert TRAN-ID from file to display format for screen fields TRNID1O–TRNID10O |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 50) | CARDDEMO-COMMAREA: standard commarea; extended inline with CDEMO-CT00-INFO |
| COTRN00   | WORKING-STORAGE (line 52)  | BMS mapset copybook: COTRN0AI (input map), COTRN0AO (output map); contains TRNIDINI, SEL0001I–SEL0010I (selection flags), TRNID1O–TRNID10O, TRNTP1O–TRNTP10O, TRNAM1O–TRNAM10O, TRNDT1O–TRNDT10O, TRNAM1O–TRNAM10O (amount), ERRMSGO, TITLE01O–CURTIMEO |
| COTRN02Y  | WORKING-STORAGE (line 54)  | TRAN-RECORD layout: TRAN-ID X(16), TRAN-TYPE-CD X(02), TRAN-CAT-CD 9(04), TRAN-SOURCE X(10), TRAN-DESC X(24), TRAN-AMT S9(09)V99, TRAN-MERCHANT-ID 9(09), TRAN-MERCHANT-NAME X(50), TRAN-MERCHANT-CITY X(50), TRAN-MERCHANT-ZIP X(10), TRAN-CARD-NUM X(16), TRAN-ORIG-TS X(26), TRAN-PROC-TS X(26) |
| COTTL01Y  | WORKING-STORAGE (line 56) | Screen title constants |
| CSDAT01Y  | WORKING-STORAGE (line 57) | Current date/time |
| CSMSG01Y  | WORKING-STORAGE (line 58) | Common messages |
| CSUSR01Y  | WORKING-STORAGE (line 59) | Signed-on user data |
| DFHAID    | WORKING-STORAGE (line 61) | EIBAID constants: DFHENTER, DFHPF3, DFHPF7, DFHPF8 |
| DFHBMSCA  | WORKING-STORAGE (line 62) | BMS attribute bytes |

### COMMAREA Extension (inline after COPY COCOM01Y)

| Field              | PIC       | Purpose |
|--------------------|-----------|---------|
| CDEMO-CT00-INFO    | Group     | CT00-specific commarea fields |
| CDEMO-CT00-TRNID-FIRST | X(16) | First transaction ID on current page (for backward browse anchor) |
| CDEMO-CT00-TRNID-LAST  | X(16) | Last transaction ID on current page (for forward browse anchor) |
| CDEMO-CT00-PAGE-NUM    | 9(08)  | Current page number (informational) |
| CDEMO-CT00-NEXT-PAGE-FLG | X(01) | 'Y'=more pages forward; 'N'=no more pages |
| CDEMO-CT00-TRN-SEL-FLG | X(01)  | 'Y'=a row was selected |
| CDEMO-CT00-TRN-SELECTED | X(16) | Transaction ID of selected row; passed to COTRN01C |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| WS-PGMNAME           | X(08) = 'COTRN00C' | Program name for header |
| WS-TRANID            | X(04) = 'CT00' | Transaction ID |
| WS-MESSAGE           | X(80)     | User-visible error/status message |
| WS-ERR-FLG           | X(01)     | Error flag |
| WS-CA-TRAN-ID-FILTER | X(16)     | Current transaction ID filter value (from TRNIDINI) |
| WS-TRAN-SRCH-FLAG    | X(01)     | 'Y'=filter active |
| WS-BROWSE-DIR        | X(01)     | 'F'=forward, 'B'=backward |
| WS-CA-TRAN-ID-N      | 9(16)     | Numeric form of transaction ID for numeric validation |
| WS-TRAN-ORIG-TS      | Group     | Parsed timestamp from TRAN-ORIG-TS for display |
| WS-PAGE-NUM          | 9(08)     | Current page number |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS RETURN TRANSID('CT00') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM('COTRN01C') COMMAREA | PROCESS-ENTER-KEY | Transfer to transaction detail view |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | RETURN-TO-PREV-SCREEN | Return to previous menu |
| EXEC CICS SEND MAP('COTRN0A') MAPSET('COTRN00') FROM(COTRN0AO) ERASE | SEND-TRNLST-SCREEN | Display transaction list |
| EXEC CICS RECEIVE MAP('COTRN0A') MAPSET('COTRN00') INTO(COTRN0AI) RESP RESP2 | RECEIVE-TRNLST-SCREEN | Receive selection and filter input |
| EXEC CICS STARTBR FILE('TRANSACT') RIDFLD(WS-TRAN-ID-SRCH) RESP RESP2 | POPULATE-TRAN-DATA | Begin browse at filter key or HIGH-VALUES |
| EXEC CICS READNEXT FILE('TRANSACT') INTO(TRAN-RECORD) RIDFLD(WS-TRAN-ID) RESP RESP2 | POPULATE-TRAN-DATA | Read forward in transaction file |
| EXEC CICS READPREV FILE('TRANSACT') INTO(TRAN-RECORD) RIDFLD(WS-TRAN-ID) RESP RESP2 | POPULATE-TRAN-DATA (backward) | Read backward in transaction file |
| EXEC CICS ENDBR FILE('TRANSACT') | POPULATE-TRAN-DATA | End browse |

---

## 5. File/Dataset Access

| File Name | CICS File  | Access Type | Key             | Purpose |
|-----------|------------|-------------|-----------------|---------|
| TRANSACT  | TRANSACT   | STARTBR/READNEXT/READPREV/ENDBR | WS-TRAN-ID-SRCH X(16) | Browse transaction records for display |

**Browse pattern:**
- STARTBR key = TRNIDINI filter value (if provided) or LOW-VALUES (start of file) for forward; CDEMO-CT00-TRNID-LAST for next page; CDEMO-CT00-TRNID-FIRST for prior page
- STARTBR does not use GTEQ — positions to exact key or next higher
- Fill up to 10 rows READNEXT (forward) or READPREV (backward)
- After filling 10 rows, perform one extra READNEXT as look-ahead to determine CDEMO-CT00-NEXT-PAGE-FLG
- AT END condition during browse = end of file reached
- ENDBR after each browse session

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COTRN00    | COTRN0A | CT00        |

**Key Screen Fields:**

| Field              | Direction | Description |
|--------------------|-----------|-------------|
| TRNIDINI           | Input     | Optional transaction ID filter (must be numeric if entered) |
| SEL0001I–SEL0010I  | Input     | Row selection flags; 'S' or 's' selects that row |
| TRNID1O–TRNID10O   | Output    | Transaction IDs for displayed rows |
| TRNTP1O–TRNTP10O   | Output    | Transaction type codes |
| TRNAM1O–TRNAM10O   | Output    | Transaction amounts |
| TRNDT1O–TRNDT10O   | Output    | Transaction dates (from TRAN-ORIG-TS, MM/DD/YY format) |
| ERRMSGO            | Output    | WS-MESSAGE: error or status |
| TITLE01O–CURTIMEO  | Output    | Standard header fields |

**Navigation:**
- ENTER: process selection or re-display with new filter
- PF3: return to previous menu
- PF7: previous page (READPREV)
- PF8: next page (READNEXT from last row)
- Other keys: CCDA-MSG-INVALID-KEY

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| COTRN01C   | CICS XCTL   | Row selected with 'S'/'s'; CDEMO-CT00-TRN-SELECTED set to chosen TRAN-ID |
| CDEMO-FROM-PROGRAM (COMEN01C or COADM01C) | CICS XCTL | PF3 pressed or EIBCALEN=0 |

**COMMAREA passed to COTRN01C:**
- CDEMO-CT00-TRN-SELECTED = selected TRAN-ID
- CDEMO-FROM-PROGRAM = 'COTRN00C'
- CDEMO-FROM-TRANID = 'CT00'

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C (no commarea = not from signon) |
| TRNIDINI entered but not numeric | ERR-FLG-ON; 'Invalid transaction ID...' message; re-send map |
| STARTBR RESP = NOTFND | Display 'No transactions found' message; re-send map with empty list |
| STARTBR other RESP | Display error with RESP/RESP2; re-send map |
| READNEXT/READPREV AT END | Normal end of file; stop filling rows; set NEXT-PAGE-FLG accordingly |
| Multiple rows selected | Process first selected row found; [UNRESOLVED] — behavior with multiple selections not explicitly documented in source |
| Invalid AID key | ERR-FLG-ON; CCDA-MSG-INVALID-KEY; re-send map |

---

## 9. Business Rules

1. **10 rows per page**: POPULATE-TRAN-DATA fills exactly 10 screen rows. A look-ahead READNEXT after the 10th row determines whether CDEMO-CT00-NEXT-PAGE-FLG='Y' (more records exist forward).
2. **TRNIDINI filter**: If TRNIDINI is entered, it must be numeric. STARTBR uses it as the starting key for browse, effectively filtering to transactions with ID >= the entered value. Callers cannot filter by partial ID (no wildcard).
3. **Timestamp display**: TRAN-ORIG-TS is a 26-byte timestamp (YYYY-MM-DD-HH.MM.SS.mmmmmm). POPULATE-TRAN-DATA extracts the date portion and reformats to MM/DD/YY for TRNDT display fields.
4. **Pagination state**: CDEMO-CT00-TRNID-FIRST and CDEMO-CT00-TRNID-LAST are stored in the commarea between interactions, enabling STARTBR to be repositioned accurately on PF7/PF8 without re-reading from the beginning.
5. **Selection transfer**: When a row is selected, CDEMO-CT00-TRN-SELECTED receives the TRAN-ID and XCTL transfers to COTRN01C. COTRN01C reads the full transaction record using this ID.
6. **No direct admin/user distinction**: COTRN00C does not check user type; it is accessible from both COMEN01C (regular users) and potentially COTRTLIC (admin transaction list, if applicable).

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COTRN0A) | TRNIDINI (filter), SEL0001I–SEL0010I (row selections) |
| COMMAREA  | CDEMO-CT00-INFO (pagination anchors, page number, next-page flag) |
| TRANSACT VSAM file | Transaction records read via STARTBR/READNEXT/READPREV |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COTRN0A) | Transaction list: up to 10 rows with ID, type, amount, date |
| COMMAREA   | CDEMO-CT00-TRNID-FIRST, CDEMO-CT00-TRNID-LAST (pagination anchors); CDEMO-CT00-TRN-SELECTED (for COTRN01C); CDEMO-CT00-NEXT-PAGE-FLG |

---

## 11. Key Variables and Their Purpose

| Variable                  | Purpose |
|---------------------------|---------|
| WS-CA-TRAN-ID-FILTER      | Active transaction ID filter; used as STARTBR RIDFLD for filtered browse |
| WS-BROWSE-DIR             | Browse direction ('F'=forward, 'B'=backward); controls READNEXT vs. READPREV |
| CDEMO-CT00-TRNID-FIRST    | First transaction ID on current page; STARTBR anchor for PF7 (previous page) |
| CDEMO-CT00-TRNID-LAST     | Last transaction ID on current page; STARTBR anchor for PF8 (next page) |
| CDEMO-CT00-NEXT-PAGE-FLG  | 'Y'/'N'; determined by look-ahead READNEXT after filling 10 rows |
| CDEMO-CT00-TRN-SELECTED   | Transaction ID selected by user; passed to COTRN01C via COMMAREA |
| WS-TRAN-ORIG-TS           | Parsed TRAN-ORIG-TS fields; intermediate for MM/DD/YY display format |
