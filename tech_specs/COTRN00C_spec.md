# Technical Specification: COTRN00C — Transaction List Program

## 1. Executive Summary

COTRN00C is an online CICS COBOL program in the CardDemo application that presents a paginated list of transactions read from the TRANSACT VSAM file. The operator may optionally filter from a starting Transaction ID, page forward and backward through the result set (10 rows per page), and select a single transaction for detailed view by typing `S` in the selection field beside it. Selection transfers control to COTRN01C via CICS XCTL.

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COTRN00C.CBL | CICS COBOL program | app/cbl/COTRN00C.cbl |
| COTRN00.BMS | BMS mapset | app/bms/COTRN00.bms |
| COTRN00.CPY | BMS-generated copybook | app/cpy-bms/COTRN00.CPY |
| COCOM01Y.CPY | Common COMMAREA copybook | app/cpy/COCOM01Y.cpy |
| CVTRA05Y.CPY | Transaction record layout | app/cpy/CVTRA05Y.cpy |
| COTTL01Y.CPY | Screen title constants | app/cpy/COTTL01Y.cpy |
| CSDAT01Y.CPY | Date/time working storage | app/cpy/CSDAT01Y.cpy |
| CSMSG01Y.CPY | Common message constants | app/cpy/CSMSG01Y.cpy |
| DFHAID | CICS-supplied AID key constants | system |
| DFHBMSCA | CICS-supplied BMS attribute constants | system |

---

## 3. Program Identity

| Attribute | Value |
|---|---|
| Program name | COTRN00C |
| CICS Transaction ID | CT00 |
| Source file | COTRN00C.CBL |
| Version stamp | CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19 |
| BMS Mapset | COTRN00 |
| BMS Map | COTRN0A |

---

## 4. CICS Commands Used

| Command | Purpose | Paragraph |
|---|---|---|
| `EXEC CICS RETURN TRANSID(CT00) COMMAREA(CARDDEMO-COMMAREA)` | Pseudo-conversational return, re-arms CT00 | MAIN-PARA (line 138) |
| `EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)` | Transfer control to COTRN01C (selection) or back (F3) | PROCESS-ENTER-KEY (line 192), RETURN-TO-PREV-SCREEN (line 518) |
| `EXEC CICS SEND MAP('COTRN0A') MAPSET('COTRN00') FROM(COTRN0AO) ERASE CURSOR` | Send list screen with erase | SEND-TRNLST-SCREEN (line 534) |
| `EXEC CICS SEND MAP('COTRN0A') MAPSET('COTRN00') FROM(COTRN0AO) CURSOR` | Send list screen without erase | SEND-TRNLST-SCREEN (line 544) |
| `EXEC CICS RECEIVE MAP('COTRN0A') MAPSET('COTRN00') INTO(COTRN0AI)` | Receive operator input | RECEIVE-TRNLST-SCREEN (line 556) |
| `EXEC CICS STARTBR DATASET('TRANSACT') RIDFLD(TRAN-ID)` | Begin VSAM browse | STARTBR-TRANSACT-FILE (line 593) |
| `EXEC CICS READNEXT DATASET('TRANSACT') INTO(TRAN-RECORD) RIDFLD(TRAN-ID)` | Forward browse read | READNEXT-TRANSACT-FILE (line 626) |
| `EXEC CICS READPREV DATASET('TRANSACT') INTO(TRAN-RECORD) RIDFLD(TRAN-ID)` | Backward browse read | READPREV-TRANSACT-FILE (line 660) |
| `EXEC CICS ENDBR DATASET('TRANSACT')` | End VSAM browse | ENDBR-TRANSACT-FILE (line 694) |

---

## 5. Copybooks Referenced

### COCOM01Y.CPY — CARDDEMO-COMMAREA
The global pseudo-conversational COMMAREA shared by all CardDemo online programs.

| Field | PIC | Description |
|---|---|---|
| CDEMO-FROM-TRANID | X(04) | Transaction ID of calling program |
| CDEMO-FROM-PROGRAM | X(08) | Name of calling program |
| CDEMO-TO-TRANID | X(04) | Target transaction ID |
| CDEMO-TO-PROGRAM | X(08) | Target program name |
| CDEMO-USER-ID | X(08) | Signed-on user ID |
| CDEMO-USER-TYPE | X(01) | 'A'=Admin, 'U'=User |
| CDEMO-PGM-CONTEXT | 9(01) | 0=first entry, 1=re-enter |
| CDEMO-CUST-ID | 9(09) | Customer ID (context) |
| CDEMO-ACCT-ID | 9(11) | Account ID (context) |
| CDEMO-CARD-NUM | 9(16) | Card number (context) |

Additionally, COTRN00C defines a program-local extension to the COMMAREA immediately after the COPY COCOM01Y statement (lines 62–70):

```
05 CDEMO-CT00-INFO.
   10 CDEMO-CT00-TRNID-FIRST     PIC X(16)   -- first tran ID on current page
   10 CDEMO-CT00-TRNID-LAST      PIC X(16)   -- last tran ID on current page
   10 CDEMO-CT00-PAGE-NUM        PIC 9(08)   -- current page number
   10 CDEMO-CT00-NEXT-PAGE-FLG   PIC X(01)   -- 'Y' if next page exists
   10 CDEMO-CT00-TRN-SEL-FLG     PIC X(01)   -- selection flag typed by user
   10 CDEMO-CT00-TRN-SELECTED    PIC X(16)   -- transaction ID of selected row
```

### CVTRA05Y.CPY — TRAN-RECORD
Transaction file record layout (350-byte record). Source: app/cpy/CVTRA05Y.cpy.

| Field | PIC | Description |
|---|---|---|
| TRAN-ID | X(16) | Transaction identifier (KSDS key) |
| TRAN-TYPE-CD | X(02) | Transaction type code |
| TRAN-CAT-CD | 9(04) | Transaction category code |
| TRAN-SOURCE | X(10) | Source of transaction |
| TRAN-DESC | X(100) | Description |
| TRAN-AMT | S9(09)V99 | Amount (signed packed) |
| TRAN-MERCHANT-ID | 9(09) | Merchant identifier |
| TRAN-MERCHANT-NAME | X(50) | Merchant name |
| TRAN-MERCHANT-CITY | X(50) | Merchant city |
| TRAN-MERCHANT-ZIP | X(10) | Merchant ZIP |
| TRAN-CARD-NUM | X(16) | Card number |
| TRAN-ORIG-TS | X(26) | Origination timestamp |
| TRAN-PROC-TS | X(26) | Processing timestamp |
| FILLER | X(20) | Reserved |

### COTRN00.CPY — BMS-Generated Map Symbolic Description
Generated from COTRN00.BMS. Defines two 01-level structures:
- `COTRN0AI` — input map (fields suffixed with `I`, lengths with `L`, attributes with `A/F`)
- `COTRN0AO` — output map, REDEFINES COTRN0AI (fields suffixed with `O`, color/highlight bytes)

Key fields in COTRN0AI/COTRN0AO (source: app/cpy-bms/COTRN00.CPY):

| Symbolic Name | PIC | Direction | Purpose |
|---|---|---|---|
| PAGENUMI / PAGENUMIO | X(8) | Out | Page number display |
| TRNIDINI / TRNIDINO | X(16) | In/Out | Search Transaction ID filter |
| TRNIDINL | S9(4) COMP | In | Cursor length control |
| SEL0001I..SEL0010I | X(1) each | In | Row selection flag (1–10) |
| TRNID01I..TRNID10I | X(16) each | In/Out | Transaction ID per row |
| TDATE01I..TDATE10I | X(8) each | In/Out | Date per row (MM/DD/YY) |
| TDESC01I..TDESC10I | X(26) each | In/Out | Description per row |
| TAMT001I..TAMT010I | X(12) each | In/Out | Amount per row |
| ERRMSGI / ERRMSGO | X(78) | Out | Error/status message |
| TRNNAMEO | X(4) | Out | Transaction name (CT00) |
| PGMNAMEO | X(8) | Out | Program name |
| CURDATEO | X(8) | Out | Current date MM/DD/YY |
| CURTIMEO | X(8) | Out | Current time HH:MM:SS |
| TITLE01O / TITLE02O | X(40) each | Out | Application title lines |

### COTTL01Y.CPY — CCDA-SCREEN-TITLE
Provides `CCDA-TITLE01` ('AWS Mainframe Modernization') and `CCDA-TITLE02` ('CardDemo') for header population.

### CSDAT01Y.CPY — WS-DATE-TIME
Provides the date/time working-storage structure used to format current date and time into the screen header.

### CSMSG01Y.CPY — CCDA-COMMON-MESSAGES
Provides `CCDA-MSG-INVALID-KEY` used when an unrecognized attention key is pressed.

---

## 6. Working Storage Variables

| Field | PIC | Value | Purpose |
|---|---|---|---|
| WS-PGMNAME | X(08) | 'COTRN00C' | Self-identifying program name |
| WS-TRANID | X(04) | 'CT00' | Self-identifying transaction ID |
| WS-MESSAGE | X(80) | SPACES | Current message to display in ERRMSG |
| WS-TRANSACT-FILE | X(08) | 'TRANSACT' | CICS DATASET name for VSAM file |
| WS-ERR-FLG | X(01) | 'N' | Error flag; 88 ERR-FLG-ON='Y', ERR-FLG-OFF='N' |
| WS-TRANSACT-EOF | X(01) | 'N' | EOF flag; 88 TRANSACT-EOF='Y' |
| WS-SEND-ERASE-FLG | X(01) | 'Y' | Controls ERASE on SEND MAP |
| WS-RESP-CD | S9(09) COMP | 0 | CICS RESP primary return code |
| WS-REAS-CD | S9(09) COMP | 0 | CICS RESP2 secondary return code |
| WS-REC-COUNT | S9(04) COMP | 0 | Record counter (informational) |
| WS-IDX | S9(04) COMP | 0 | Loop index (1–10) for populating rows |
| WS-PAGE-NUM | S9(04) COMP | 0 | Page number (local, not persisted) |
| WS-TRAN-AMT | PIC +99999999.99 | — | Formatted transaction amount |
| WS-TRAN-DATE | X(08) | '00/00/00' | Formatted date MM/DD/YY |

---

## 7. Program Flow — Paragraph-by-Paragraph

### MAIN-PARA (entry point, line 94)

```
Initialize flags: ERR-FLG-OFF, TRANSACT-NOT-EOF, NEXT-PAGE-NO, SEND-ERASE-YES
Clear WS-MESSAGE and ERRMSGO
Set cursor to TRNIDINL = -1

IF EIBCALEN = 0
    → no COMMAREA, redirect to COSGN00C via RETURN-TO-PREV-SCREEN
ELSE
    Move DFHCOMMAREA into CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER (first entry, context=0)
        Set CDEMO-PGM-REENTER = 1
        Initialize COTRN0AO to LOW-VALUES
        PERFORM PROCESS-ENTER-KEY     -- load first page
        PERFORM SEND-TRNLST-SCREEN
    ELSE (re-entry, context=1)
        PERFORM RECEIVE-TRNLST-SCREEN
        EVALUATE EIBAID
            DFHENTER → PERFORM PROCESS-ENTER-KEY
            DFHPF3   → XCTL to COMEN01C
            DFHPF7   → PERFORM PROCESS-PF7-KEY
            DFHPF8   → PERFORM PROCESS-PF8-KEY
            OTHER    → set error message, PERFORM SEND-TRNLST-SCREEN
        END-EVALUATE
    END-IF
END-IF

EXEC CICS RETURN TRANSID(CT00) COMMAREA(CARDDEMO-COMMAREA)
```

### PROCESS-ENTER-KEY (line 146)

1. Examines SEL0001I through SEL0010I (EVALUATE TRUE chain) for the first non-space/non-low-values selection field. When found, captures the selection flag into `CDEMO-CT00-TRN-SEL-FLG` and the corresponding `TRNIDxxI` value into `CDEMO-CT00-TRN-SELECTED`.
2. If a selection was found and the flag is `S` or `s`, sets CDEMO-TO-PROGRAM to `COTRN01C` and issues `EXEC CICS XCTL`.
3. If the selection flag is not `S`, sets error message "Invalid selection. Valid value is S".
4. Validates the search filter field TRNIDINI: if blank, moves LOW-VALUES to TRAN-ID; if non-blank but non-numeric, sets error; if numeric, moves value to TRAN-ID.
5. Resets CDEMO-CT00-PAGE-NUM to 0 and calls PROCESS-PAGE-FORWARD.
6. On success, blanks the TRNIDINO output field.

### PROCESS-PF7-KEY (line 234)

Backward page. Uses `CDEMO-CT00-TRNID-FIRST` as the starting browse key. If page is already 1, displays "You are already at the top of the page..." and sets SEND-ERASE-NO. Otherwise calls PROCESS-PAGE-BACKWARD.

### PROCESS-PF8-KEY (line 257)

Forward page. Uses `CDEMO-CT00-TRNID-LAST` as the browse start key. If `NEXT-PAGE-YES` is not set, displays "You are already at the bottom of the page..." and sets SEND-ERASE-NO. Otherwise calls PROCESS-PAGE-FORWARD.

### PROCESS-PAGE-FORWARD (line 279)

1. STARTBR-TRANSACT-FILE — positions browse at TRAN-ID.
2. If first entry (EIBAID is not ENTER, PF7, or PF3), reads one record past the start with READNEXT to skip the boundary record.
3. Clears all 10 row slots (INITIALIZE-TRAN-DATA loop WS-IDX 1–10).
4. Reads up to 10 records forward with READNEXT and calls POPULATE-TRAN-DATA for each.
5. Reads one more record to determine if a next page exists; sets NEXT-PAGE-YES/NO accordingly.
6. Increments CDEMO-CT00-PAGE-NUM by 1.
7. ENDBR-TRANSACT-FILE.
8. Moves page number to PAGENUMI and calls SEND-TRNLST-SCREEN.

### PROCESS-PAGE-BACKWARD (line 333)

1. STARTBR-TRANSACT-FILE — positions at CDEMO-CT00-TRNID-FIRST.
2. If EIBAID is not ENTER or PF8, reads one record backward with READPREV to skip the boundary.
3. Clears all 10 row slots.
4. Reads up to 10 records backward with READPREV and calls POPULATE-TRAN-DATA for each (filling slots 10 down to 1).
5. Reads one more backward to determine whether a previous page exists; decrements CDEMO-CT00-PAGE-NUM.
6. ENDBR-TRANSACT-FILE.
7. Calls SEND-TRNLST-SCREEN.

### POPULATE-TRAN-DATA (line 381)

Converts TRAN-AMT to display format (WS-TRAN-AMT via `PIC +99999999.99`). Extracts date from TRAN-ORIG-TS using WS-TIMESTAMP redefinitions (year-3:2 / month / day) into WS-TRAN-DATE MM/DD/YY. Uses EVALUATE WS-IDX (1–10) to move TRAN-ID, WS-TRAN-DATE, TRAN-DESC, and WS-TRAN-AMT into the corresponding row fields of COTRN0AI. Row 1 also sets CDEMO-CT00-TRNID-FIRST; row 10 also sets CDEMO-CT00-TRNID-LAST.

### INITIALIZE-TRAN-DATA (line 450)

Moves SPACES to TRNID/TDATE/TDESC/TAMT fields for the row index WS-IDX (1–10). Called before each page-load to clear stale data.

### RETURN-TO-PREV-SCREEN (line 510)

Sets CDEMO-FROM-TRANID = WS-TRANID ('CT00'), CDEMO-FROM-PROGRAM = WS-PGMNAME ('COTRN00C'), CDEMO-PGM-CONTEXT = 0, then issues XCTL to CDEMO-TO-PROGRAM. Default target when CDEMO-TO-PROGRAM is empty is 'COSGN00C'.

### SEND-TRNLST-SCREEN (line 527)

Calls POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO. If SEND-ERASE-YES, issues SEND with ERASE; otherwise sends without ERASE (used when preserving screen state for in-place messages at top/bottom of page).

### RECEIVE-TRNLST-SCREEN (line 554)

Issues `EXEC CICS RECEIVE MAP INTO(COTRN0AI)` capturing RESP and RESP2 into WS-RESP-CD / WS-REAS-CD.

### POPULATE-HEADER-INFO (line 567)

Gets FUNCTION CURRENT-DATE into WS-CURDATE-DATA, formats into MM/DD/YY for CURDATEO and HH:MM:SS for CURTIMEO. Moves CCDA-TITLE01/02 to TITLE01O/TITLE02O, WS-TRANID to TRNNAMEO, WS-PGMNAME to PGMNAMEO.

### STARTBR-TRANSACT-FILE (line 591)

`EXEC CICS STARTBR DATASET('TRANSACT') RIDFLD(TRAN-ID) KEYLENGTH(16)`.
- DFHRESP(NORMAL): continue.
- DFHRESP(NOTFND): sets TRANSACT-EOF, message "You are at the top of the page...", sends screen.
- OTHER: sets ERR-FLG-ON, message "Unable to lookup transaction...", sends screen.

### READNEXT-TRANSACT-FILE (line 624)

`EXEC CICS READNEXT DATASET('TRANSACT') INTO(TRAN-RECORD) RIDFLD(TRAN-ID)`.
- DFHRESP(NORMAL): continue.
- DFHRESP(ENDFILE): sets TRANSACT-EOF, message "You have reached the bottom of the page...", sends screen.
- OTHER: sets ERR-FLG-ON, sends screen.

### READPREV-TRANSACT-FILE (line 658)

`EXEC CICS READPREV DATASET('TRANSACT') INTO(TRAN-RECORD) RIDFLD(TRAN-ID)`.
- DFHRESP(NORMAL): continue.
- DFHRESP(ENDFILE): sets TRANSACT-EOF, message "You have reached the top of the page...".
- OTHER: sets ERR-FLG-ON, sends screen.

### ENDBR-TRANSACT-FILE (line 692)

`EXEC CICS ENDBR DATASET('TRANSACT')` — unconditional browse termination.

---

## 8. Inter-Program Interactions

| Interaction | Target | Mechanism | Condition |
|---|---|---|---|
| Called by | COMEN01C | XCTL (inbound) | User selects transaction list from menu |
| Transfer to | COTRN01C | XCTL with COMMAREA | User enters 'S' on a row |
| Transfer to | COMEN01C | XCTL with COMMAREA | F3 pressed |
| Transfer to | COSGN00C | XCTL with COMMAREA | EIBCALEN=0 or CDEMO-TO-PROGRAM empty |

COMMAREA fields used for handoff to COTRN01C (set in PROCESS-ENTER-KEY, lines 188–194):
- `CDEMO-TO-PROGRAM` = 'COTRN01C'
- `CDEMO-FROM-TRANID` = 'CT00'
- `CDEMO-FROM-PROGRAM` = 'COTRN00C'
- `CDEMO-PGM-CONTEXT` = 0
- `CDEMO-CT00-TRN-SEL-FLG` = 'S'
- `CDEMO-CT00-TRN-SELECTED` = 16-character transaction ID

---

## 9. Files Accessed

| CICS Dataset Name | Access Mode | Operations | Record Structure |
|---|---|---|---|
| TRANSACT | Browse (read-only) | STARTBR, READNEXT, READPREV, ENDBR | TRAN-RECORD (CVTRA05Y.CPY), 350 bytes, KSDS key=TRAN-ID X(16) |

---

## 10. Error Handling

| Condition | ERR-FLG | Message | Action |
|---|---|---|---|
| EIBCALEN = 0 | — | — | XCTL to COSGN00C |
| Invalid AID key | Y | "Invalid key pressed. Please see below..." | Re-send screen |
| TRNIDINI non-numeric | Y | "Tran ID must be Numeric ..." | Re-send, cursor on TRNIDIN |
| Selection not 'S' | — | "Invalid selection. Valid value is S" | Re-send |
| STARTBR NOTFND | — (EOF set) | "You are at the top of the page..." | Send screen |
| STARTBR OTHER | Y | "Unable to lookup transaction..." | Send screen |
| READNEXT ENDFILE | — (EOF set) | "You have reached the bottom of the page..." | Send screen |
| READNEXT OTHER | Y | "Unable to lookup transaction..." | Send screen |
| READPREV ENDFILE | — (EOF set) | "You have reached the top of the page..." | Send screen |
| PF7 at page 1 | — | "You are already at the top of the page..." | Send without ERASE |
| PF8 at last page | — | "You are already at the bottom of the page..." | Send without ERASE |

---

## 11. Transaction Flow Context

```
COSGN00C (signon)
    --> COMEN01C (main menu)
        --> COTRN00C [CT00] (transaction list)    <-- this program
                Browse TRANSACT VSAM (READNEXT/READPREV, 10 per page)
                F7=page backward, F8=page forward
                S=select --> XCTL to COTRN01C [CT01] (transaction view)
            F3 --> XCTL back to COMEN01C
```

---

## 12. Pagination Design Notes

- The program uses a true VSAM browse with STARTBR/READNEXT/READPREV; there is no in-memory caching.
- The COMMAREA fields `CDEMO-CT00-TRNID-FIRST` and `CDEMO-CT00-TRNID-LAST` serve as browse anchors between pseudo-conversational invocations. TRNID-FIRST is used by PF7 (backward), TRNID-LAST by PF8 (forward).
- The `WS-SEND-ERASE-FLG` flag is set to NO only for informational boundary messages (top/bottom of file), preserving screen content while posting the message.
- The program issues an extra READNEXT/READPREV beyond the 10-row limit to set NEXT-PAGE-YES/NO, which governs PF8 availability.
- `CDEMO-CT00-PAGE-NUM` is incremented on each forward load and decremented on backward; the displayed page number is informational only and driven from COMMAREA.

---

## 13. Open Questions and Gaps

- The GTEQ keyword is commented out on the STARTBR (line 597); the browse therefore starts at or after the key using the default (GTEQ) positioning. This is as intended but should be verified against CICS resource definition for the TRANSACT file.
- `WS-REC-COUNT` (line 52) is declared but never incremented in the source; it appears to be vestigial.
- COTRN00C issues `READ UPDATE` is not used here (browse only); concurrent updates to the TRANSACT file during browse are not protected.
