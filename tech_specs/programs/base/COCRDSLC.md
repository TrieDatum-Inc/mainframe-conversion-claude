# Technical Specification: COCRDSLC

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COCRDSLC                                             |
| Source File      | app/cbl/COCRDSLC.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CCDL (LIT-THISTRANID, line 166)                      |
| Function         | Displays credit card detail for a selected card. Accepts an account ID (required) and card number (required) as search criteria, reads the CARDDAT VSAM file by card number key, and displays card embossed name, expiry month/year, and active status. When invoked from COCRDLIC (card list), the search keys are pre-populated from COMMAREA and the card lookup proceeds immediately without user input. PF3 returns to the calling program (CDEMO-FROM-PROGRAM) or COMEN01C if no prior program. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CCDL and COMMAREA)

EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE)

INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA
SET WS-RETURN-MSG-OFF

IF EIBCALEN = 0 OR (FROM-PROGRAM = COMEN01C AND NOT CDEMO-PGM-REENTER):
    INITIALIZE CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA
ELSE:
    MOVE DFHCOMMAREA to CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA

PERFORM YYYY-STORE-PFKEY

Validate AID: ENTER and PF03 are valid; others treated as ENTER

EVALUATE TRUE:
    WHEN CCARD-AID-PFK03:
        CDEMO-TO-PROGRAM = CDEMO-FROM-PROGRAM (or COMEN01C if blank)
        EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM)

    WHEN CDEMO-PGM-ENTER AND CDEMO-FROM-PROGRAM = COCRDLIC:
        INPUT-OK; move CDEMO-ACCT-ID/CARD-NUM to CC-ACCT-ID-N/CARD-NUM-N
        PERFORM 9000-READ-DATA
        PERFORM 1000-SEND-MAP; GO TO COMMON-RETURN

    WHEN CDEMO-PGM-ENTER (from any other program):
        PERFORM 1000-SEND-MAP (display blank form); GO TO COMMON-RETURN

    WHEN CDEMO-PGM-REENTER:
        PERFORM 2000-PROCESS-INPUTS (receive map, validate)
        IF INPUT-ERROR: PERFORM 1000-SEND-MAP; GO TO COMMON-RETURN
        ELSE: PERFORM 9000-READ-DATA; 1000-SEND-MAP; GO TO COMMON-RETURN

    WHEN OTHER:
        ABEND-CULPRIT/CODE set; PERFORM SEND-PLAIN-TEXT

COMMON-RETURN:
    CICS RETURN TRANSID('CCDL') COMMAREA(WS-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph               | Lines      | Description |
|-------------------------|------------|-------------|
| 0000-MAIN               | 248–392    | Entry: HANDLE ABEND; INITIALIZE; commarea load; YYYY-STORE-PFKEY; AID validate; EVALUATE dispatch; post-evaluate INPUT-ERROR check |
| COMMON-RETURN           | 394–407    | Set CCARD-ERROR-MSG; serialize COMMAREA; CICS RETURN TRANSID('CCDL') |
| 1000-SEND-MAP           | 412–425    | Calls 1100 → 1200 → 1300 → 1400 |
| 1100-SCREEN-INIT        | 427–455    | LOW-VALUES to CCRDSLAO; fill title, tran, pgm, date, time fields |
| 1200-SETUP-SCREEN-VARS  | 457–497    | Populate account/card filter fields on screen from CDEMO-ACCT-ID/CARD-NUM; if FOUND-CARDS-FOR-ACCOUNT: fill card name, expiry month/year, status; set info message |
| 1300-SETUP-SCREEN-ATTRS | 502–560    | Protect/unprotect ACCTSIDA/CARDSIDA based on origin (from COCRDLIC = protected); highlight invalid/blank filters red; put '*' in blank fields on reenter; set color for INFOMSGC |
| 1400-SEND-SCREEN        | 563–579    | SET CDEMO-PGM-REENTER; CICS SEND MAP(CCRDSLA) MAPSET(COCRDSL) FROM(CCRDSLAO) CURSOR ERASE FREEKB |
| 2000-PROCESS-INPUTS     | 582–595    | Calls 2100-RECEIVE-MAP, 2200-EDIT-MAP-INPUTS; sets CCARD-ERROR-MSG/NEXT-PROG/MAPSET/MAP |
| 2100-RECEIVE-MAP        | 596–607    | CICS RECEIVE MAP(CCRDSLA) INTO(CCRDSLAI); note: fields read by caller |
| 2200-EDIT-MAP-INPUTS    | 608–644    | SET INPUT-OK; cleanse '*' → LOW-VALUES; PERFORM 2210, 2220; cross-field check both-blank = NO-SEARCH-CRITERIA-RECEIVED |
| 2210-EDIT-ACCOUNT       | 647–681    | Account required: blank/zero = INPUT-ERROR + FLG-ACCTFILTER-BLANK; non-numeric = INPUT-ERROR; else FLG-ACCTFILTER-ISVALID |
| 2220-EDIT-CARD          | 685–723    | Card required: blank/zero = INPUT-ERROR + FLG-CARDFILTER-BLANK; non-numeric = INPUT-ERROR; else FLG-CARDFILTER-ISVALID |
| 9000-READ-DATA          | 726–734    | Delegates to 9100-GETCARD-BYACCTCARD |
| 9100-GETCARD-BYACCTCARD | 736–776    | READ CARDDAT by WS-CARD-RID-CARDNUM; NORMAL: SET FOUND-CARDS-FOR-ACCOUNT; NOTFND: INPUT-ERROR + both filters not-ok + DID-NOT-FIND-ACCTCARD-COMBO; OTHER: error message |
| 9150-GETCARD-BYACCT     | 779–811    | READ CARDAIX by WS-CARD-RID-ACCT-ID (alternate path — **not called** by 9000-READ-DATA; dead code in current program flow) |
| YYYY-STORE-PFKEY        | (COPY 'CSSTRPFY', line 855) | Common PF key mapping |
| ABEND-ROUTINE           | 857–878    | CICS SEND FROM(ABEND-DATA); CICS HANDLE ABEND CANCEL; EXEC CICS ABEND ABCODE('9999') |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook   | Used In              | Contents |
|------------|----------------------|----------|
| CVCRD01Y   | WORKING-STORAGE (line 194) | CC-WORK-AREA: CC-ACCT-ID X(11)/N, CC-CARD-NUM X(16)/N, FOUND-CARDS-FOR-ACCOUNT flag |
| COCOM01Y   | WORKING-STORAGE (line 198) | CARDDEMO-COMMAREA: CDEMO-FROM-PROGRAM, CDEMO-FROM-TRANID, CDEMO-ACCT-ID, CDEMO-CARD-NUM, CDEMO-PGM-ENTER/REENTER, CDEMO-TO-PROGRAM, CDEMO-TO-TRANID |
| DFHBMSCA   | WORKING-STORAGE (line 208) | BMS attribute byte constants: DFHBMPRF, DFHBMFSE, DFHRED, DFHDFCOL, DFHBMDAR, DFHNEUTR |
| DFHAID     | WORKING-STORAGE (line 209) | EIBAID constants |
| COTTL01Y   | WORKING-STORAGE (line 213) | CCDA-TITLE01, CCDA-TITLE02 title constants |
| COCRDSL    | WORKING-STORAGE (line 215) | BMS mapset: CCRDSLAI (input), CCRDSLAO (output); contains ACCTSIDI/O/A/C/L, CARDSIDI/O/A/C/L, CRDNAMEO, EXPMONO, EXPYEARO, CRDSTCDO, ERRMSGO, INFOMSGO/C, TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO |
| CSDAT01Y   | WORKING-STORAGE (line 217) | Current date/time working variables |
| CSMSG01Y   | WORKING-STORAGE (line 221) | Common message literals |
| CSMSG02Y   | WORKING-STORAGE (line 224) | ABEND-DATA structure: ABEND-CULPRIT, ABEND-CODE, ABEND-REASON, ABEND-MSG |
| CSUSR01Y   | WORKING-STORAGE (line 227) | Signed-on user data |
| CVACT02Y   | WORKING-STORAGE (line 234) | CARD-RECORD: CARD-NUM, CARD-ACCT-ID, CARD-CVV-CD, CARD-EMBOSSED-NAME, CARD-EXPIRAION-DATE, CARD-ACTIVE-STATUS |
| CVCUS01Y   | WORKING-STORAGE (line 240) | Customer record layout (copied but not directly used in PROCEDURE DIVISION) |

### Key Working Storage Variables

| Variable                      | PIC / Structure | Purpose |
|-------------------------------|-----------------|---------|
| LIT-THISTRANID                | X(4) = 'CCDL'   | Transaction ID for CICS RETURN |
| LIT-THISPGM                   | X(8) = 'COCRDSLC' | Program name constant |
| LIT-CARDFILENAME              | X(8) = 'CARDDAT ' | Primary card file name |
| LIT-CARDFILENAME-ACCT-PATH    | X(8) = 'CARDAIX ' | Alternate index path (account-keyed) |
| LIT-CCLISTPGM                 | X(8) = 'COCRDLIC' | Known caller from list screen |
| LIT-MENUPGM                   | X(8) = 'COMEN01C' | Default return target |
| WS-CARD-RID                   | X(27)           | Composite key: CARDNUM X(16) + ACCT-ID 9(11) |
| WS-INPUT-FLAG                 | PIC X(1)        | 88 INPUT-OK='0'/' '/LOW-VALUES, INPUT-ERROR='1', INPUT-PENDING=LOW-VALUES |
| WS-RETURN-MSG                 | PIC X(75)       | Error/return message; 88 levels for all error conditions |
| WS-INFO-MSG                   | PIC X(40)       | Info message; 88 FOUND-CARDS-FOR-ACCOUNT, WS-PROMPT-FOR-INPUT |
| CARD-EXPIRAION-DATE-X         | PIC X(10)       | Expiry date string YYYY-MM-DD; decomposed into CARD-EXPIRY-YEAR/MONTH/DAY |
| WS-THIS-PROGCOMMAREA          | Group 12 bytes  | CA-FROM-PROGRAM X(8) + CA-FROM-TRANID X(4) |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE) | 0000-MAIN (line 250) | Install abend handler |
| EXEC CICS RETURN TRANSID('CCDL') COMMAREA(WS-COMMAREA) | COMMON-RETURN (line 402) | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | 0000-MAIN (line 331) | PF3 exit to calling program or COMEN01C |
| EXEC CICS SEND MAP(CCRDSLA) MAPSET(COCRDSL) FROM(CCRDSLAO) CURSOR ERASE FREEKB | 1400-SEND-SCREEN (line 569) | Send card detail screen |
| EXEC CICS RECEIVE MAP(CCRDSLA) MAPSET(COCRDSL) INTO(CCRDSLAI) | 2100-RECEIVE-MAP (line 597) | Receive user-entered search keys |
| EXEC CICS READ FILE(CARDDAT) RIDFLD KEYLENGTH INTO RESP RESP2 | 9100-GETCARD-BYACCTCARD (line 742) | Read card by primary key (card number) |
| EXEC CICS READ FILE(CARDAIX) RIDFLD KEYLENGTH INTO RESP RESP2 | 9150-GETCARD-BYACCT (line 783) | Read card by alternate index (account ID) — dead code, not called |
| EXEC CICS SEND FROM(ABEND-DATA) NOHANDLE | ABEND-ROUTINE (line 865) | Display abend info before terminating |
| EXEC CICS HANDLE ABEND CANCEL | ABEND-ROUTINE (line 871) | Cancel abend handler before ABEND |
| EXEC CICS ABEND ABCODE('9999') | ABEND-ROUTINE (line 875) | Forced abend with code 9999 |

---

## 5. File/Dataset Access

| CICS File Name | Access Type | Purpose |
|----------------|-------------|---------|
| CARDDAT        | READ (non-update) by card number key | Read single card record for display |
| CARDAIX        | READ by account ID (alternate index) | **Dead code** — 9150-GETCARD-BYACCT is defined but never called from 9000-READ-DATA |

The primary read key (9100-GETCARD-BYACCTCARD) uses WS-CARD-RID-CARDNUM (16 bytes) as the RIDFLD with KEYLENGTH of 16. The ACCT-ID portion of WS-CARD-RID is not used in the active read path.

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COCRDSL    | CCRDSLA | CCDL        |

**Key Screen Fields:**

| Field     | Direction | Description |
|-----------|-----------|-------------|
| ACCTSIDI/O | I/O      | Account ID (required, 11 digits; protected when arriving from COCRDLIC) |
| CARDSIDI/O | I/O      | Card number (required, 16 digits; protected when arriving from COCRDLIC) |
| CRDNAMEO  | Output    | Card embossed name (CARD-EMBOSSED-NAME) |
| EXPMONO   | Output    | Expiry month (CARD-EXPIRY-MONTH from CARD-EXPIRAION-DATE positions 6-7) |
| EXPYEARO  | Output    | Expiry year (CARD-EXPIRY-YEAR from CARD-EXPIRAION-DATE positions 1-4) |
| CRDSTCDO  | Output    | Card active status (CARD-ACTIVE-STATUS Y/N) |
| ERRMSGO   | Output    | WS-RETURN-MSG error/validation message |
| INFOMSGO/C | Output   | WS-INFO-MSG informational text + color (DFHNEUTR when found, DFHBMDAR when not) |
| TITLE01O/TITLE02O | Output | Application titles from CCDA-TITLE01/CCDA-TITLE02 |
| TRNNAMEO  | Output    | Transaction ID (CCDL) |
| PGMNAMEO  | Output    | Program name (COCRDSLC) |
| CURDATEO  | Output    | Current date MM/DD/YY |
| CURTIMEO  | Output    | Current time HH:MM:SS |

**Field Protection Logic:**
- When CDEMO-LAST-MAPSET = COCRDLI AND CDEMO-FROM-PROGRAM = COCRDLIC: ACCTSIDA and CARDSIDA are DFHBMPRF (protected), and DFHDFCOL applied to both colors.
- Otherwise: both fields DFHBMFSE (unprotected/editable).

**Navigation:**
- ENTER: validate inputs, read card, display detail
- PF3: return to calling program
- Other keys: treated as ENTER

---

## 7. Called Programs / Transfers

| Program   | Method       | Condition |
|-----------|--------------|-----------|
| CDEMO-FROM-PROGRAM (or COMEN01C) | CICS XCTL | PF3 pressed; defaults to COMEN01C if CDEMO-FROM-PROGRAM is blank/LOW-VALUES |

No other programs are called. COCRDSLC only reads data and displays it; it does not navigate to further programs.

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 OR from COMEN01C fresh | INITIALIZE commarea; first-entry display |
| Account not supplied (blank/zero) | INPUT-ERROR; FLG-ACCTFILTER-BLANK; WS-PROMPT-FOR-ACCT; highlight red with '*' on reenter |
| Account non-numeric | INPUT-ERROR; FLG-ACCTFILTER-NOT-OK; error message |
| Card not supplied (blank/zero) | INPUT-ERROR; FLG-CARDFILTER-BLANK; WS-PROMPT-FOR-CARD; highlight red with '*' on reenter |
| Card non-numeric | INPUT-ERROR; FLG-CARDFILTER-NOT-OK; 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER' |
| Both fields blank | NO-SEARCH-CRITERIA-RECEIVED; INPUT-ERROR implicit |
| CARDDAT NOTFND | INPUT-ERROR; both filter flags NOT-OK; DID-NOT-FIND-ACCTCARD-COMBO message |
| CARDDAT other RESP | INPUT-ERROR; WS-FILE-ERROR-MESSAGE with OPNAME/FILE/RESP/RESP2 |
| WHEN OTHER in EVALUATE | ABEND-CULPRIT='COCRDSLC', ABEND-CODE='0001'; SEND-PLAIN-TEXT |
| Any unhandled abend | ABEND-ROUTINE: display ABEND-DATA; CICS ABEND('9999') |

---

## 9. Business Rules

1. **Both fields required**: Unlike COCRDLIC (where account and card are optional filters), COCRDSLC requires both account ID and card number. A blank account causes INPUT-ERROR regardless of card value.
2. **Pre-populated from list screen**: When CDEMO-FROM-PROGRAM = COCRDLIC and CDEMO-PGM-ENTER, the program skips user input and directly reads the card using CDEMO-ACCT-ID and CDEMO-CARD-NUM from COMMAREA. The user sees the result immediately.
3. **Read by card number only**: The active read path (9100-GETCARD-BYACCTCARD) reads CARDDAT using card number as the key (WS-CARD-RID-CARDNUM, 16 bytes). The account ID is passed in COMMAREA and displayed on screen but is not used to key the VSAM read.
4. **Dead code — 9150-GETCARD-BYACCT**: The alternate index path reading CARDAIX by account ID is defined but never called by 9000-READ-DATA. It would only be reachable if 9000-READ-DATA were modified to call it.
5. **Expiry date decomposition**: CARD-EXPIRAION-DATE (X(10), format YYYY-MM-DD) is overlaid by a REDEFINES at lines 86-90 splitting into CARD-EXPIRY-YEAR(4), separator, CARD-EXPIRY-MONTH(2), separator, CARD-EXPIRY-DAY(2). Only month and year are shown on screen; day is not displayed.
6. **Protection from list caller**: When arriving from COCRDLIC, the account and card fields are made uneditable (DFHBMPRF) and displayed in default color. The user cannot change the search criteria until they press PF3 to return.
7. **Pseudo-conversational**: CICS RETURN TRANSID('CCDL') on every cycle. CDEMO-PGM-REENTER is set to TRUE inside 1400-SEND-SCREEN (line 567) so the next entry processes user input.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (CCRDSLA) | ACCTSIDI — account ID; CARDSIDI — card number |
| COMMAREA  | CDEMO-FROM-PROGRAM, CDEMO-FROM-TRANID (for PF3 navigation); CDEMO-ACCT-ID, CDEMO-CARD-NUM (pre-populated when from COCRDLIC) |
| CARDDAT   | Card record read by card number key |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (CCRDSLA) | Card name, expiry month/year, status; filter echo; error/info messages |
| COMMAREA  | CDEMO-FROM-PROGRAM=COCRDSLC, CDEMO-FROM-TRANID=CCDL set before XCTL on PF3 |

---

## 11. Key Variables and Their Purpose

| Variable               | Purpose |
|------------------------|---------|
| CDEMO-FROM-PROGRAM     | Identifies calling program; drives PF3 return target and field protection logic |
| FOUND-CARDS-FOR-ACCOUNT (from CVCRD01Y) | 88-level flag set when CARDDAT read succeeds; controls whether card detail fields are populated on screen |
| WS-RETURN-MSG          | Primary error message; 88 levels cover all validation and lookup error cases |
| WS-INFO-MSG            | Informational message: 'Displaying requested details' or 'Please enter Account and Card Number' |
| CARD-EXPIRAION-DATE-X  | Work area for expiry date; REDEFINES decompose YYYY-MM-DD into year/month/day components for screen output |
| WS-THIS-PROGCOMMAREA   | Local context (CA-FROM-PROGRAM + CA-FROM-TRANID) carried across pseudo-conversational cycles |
