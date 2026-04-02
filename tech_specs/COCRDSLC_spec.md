# Technical Specification: COCRDSLC.CBL

## 1. Program Overview

| Attribute        | Value                              |
|------------------|------------------------------------|
| Program Name     | COCRDSLC                           |
| Source File      | app/cbl/COCRDSLC.cbl               |
| Layer            | Business Logic (Online / CICS)     |
| Function         | View Credit Card Detail            |
| Transaction ID   | CCDL                               |
| Mapset           | COCRDSL                            |
| Map              | CCRDSLA                            |
| Date Written     | April 2022                         |
| Version Tag      | CardDemo_v1.0-15-g27d6c6f-68       |

### Purpose

COCRDSLC accepts a credit card account number (11 digits) and card number (16 digits), reads the corresponding record from the CARDDAT VSAM file, and displays the card details in read-only form on the CCRDSLA screen (mapset COCRDSL). It can be reached two ways:

1. **From COCRDLIC** (card list): Account and card numbers are pre-populated in COMMAREA; the program reads the record immediately and displays it.
2. **Directly** (fresh entry or re-entry from other context): The user must type the account and card numbers into the entry fields.

The screen is read-only — no updates are performed. PF3 exits back to the calling program.

---

## 2. Artifact Inventory

| Artifact           | Type              | Location                          |
|--------------------|-------------------|-----------------------------------|
| COCRDSLC.CBL       | COBOL source      | app/cbl/COCRDSLC.cbl              |
| COCRDSL.BMS        | BMS mapset source | app/bms/COCRDSL.bms               |
| COCRDSL.CPY        | BMS map copybook  | app/cpy-bms/COCRDSL.CPY           |
| CVCRD01Y.CPY       | Working storage   | app/cpy/CVCRD01Y.cpy              |
| COCOM01Y.CPY       | COMMAREA layout   | app/cpy/COCOM01Y.cpy              |
| CVACT02Y.CPY       | Card record layout| app/cpy/CVACT02Y.cpy              |
| CVCUS01Y.CPY       | Customer record   | app/cpy/CVCUS01Y.cpy              |
| COTTL01Y.CPY       | Screen titles     | app/cpy/COTTL01Y.cpy              |
| CSDAT01Y.CPY       | Date formatting   | app/cpy/CSDAT01Y.cpy              |
| CSMSG01Y.CPY       | Common messages   | app/cpy/CSMSG01Y.cpy              |
| CSMSG02Y.CPY       | Abend variables   | app/cpy/CSMSG02Y.cpy              |
| CSUSR01Y.CPY       | Signed-on user    | app/cpy/CSUSR01Y.cpy              |
| DFHBMSCA           | IBM BMS attribute | System copybook                   |
| DFHAID             | IBM AID keys      | System copybook                   |
| CSSTRPFY           | PFKey store logic | Inline COPY at line 855           |

---

## 3. CICS Commands Used

| Command               | Paragraph / Location        | Purpose                                              |
|-----------------------|-----------------------------|------------------------------------------------------|
| EXEC CICS HANDLE ABEND| 0000-MAIN (~249)            | Route abends to ABEND-ROUTINE label                  |
| EXEC CICS RETURN      | COMMON-RETURN (~402)        | Return with TRANSID=CCDL and COMMAREA                |
| EXEC CICS XCTL        | ~331                        | Transfer to calling program or COMEN01C on PF3       |
| EXEC CICS SEND MAP    | 1400-SEND-SCREEN (~569)     | Send CCRDSLA from CCRDSLAO with CURSOR/ERASE/FREEKB  |
| EXEC CICS RECEIVE MAP | 2100-RECEIVE-MAP (~597)     | Receive CCRDSLA into CCRDSLAI                        |
| EXEC CICS READ        | 9100-GETCARD-BYACCTCARD (~742) | Direct read of CARDDAT by card number (primary key) |
| EXEC CICS READ        | 9150-GETCARD-BYACCT (~783)  | Read CARDAIX by account ID (alt index path) — defined but not called from main flow |
| EXEC CICS SEND TEXT   | SEND-LONG-TEXT (~821)       | Debug long-text send (not for production)            |
| EXEC CICS SEND TEXT   | SEND-PLAIN-TEXT (~838)      | Debug plain-text send; used in WHEN OTHER abend path |

---

## 4. Copybooks Referenced

| Copybook      | Usage in COCRDSLC                                                                     |
|---------------|---------------------------------------------------------------------------------------|
| CVCRD01Y      | CC-WORK-AREAS: CC-ACCT-ID, CC-CARD-NUM, CCARD-AID-xxx, CCARD-NEXT-PROG, CCARD-ERROR-MSG |
| COCOM01Y      | CARDDEMO-COMMAREA: CDEMO-FROM-PROGRAM, CDEMO-PGM-CONTEXT, CDEMO-ACCT-ID, CDEMO-CARD-NUM, etc. |
| COCRDSL       | BMS symbolic map CCRDSLAI / CCRDSLAO                                                  |
| CVACT02Y      | CARD-RECORD (CARD-NUM, CARD-ACCT-ID, CARD-CVV-CD, CARD-EMBOSSED-NAME, CARD-EXPIRAION-DATE, CARD-ACTIVE-STATUS) |
| CVCUS01Y      | CUSTOMER-RECORD (included but customer data not directly displayed on this screen)    |
| COTTL01Y      | CCDA-TITLE01, CCDA-TITLE02                                                            |
| CSDAT01Y      | Date/time formatting                                                                  |
| CSMSG01Y      | Common message literals                                                               |
| CSMSG02Y      | ABEND-DATA, ABEND-CULPRIT, ABEND-CODE, ABEND-REASON, ABEND-MSG                       |
| CSUSR01Y      | Signed-on user data                                                                   |
| DFHBMSCA      | BMS attribute constants (DFHBMPRF, DFHBMFSE, DFHDFCOL, DFHRED, DFHBMDAR, DFHNEUTR)  |
| DFHAID        | AID constants                                                                         |
| CSSTRPFY      | Maps EIBAID to CCARD-AID value                                                        |

---

## 5. Data Structures

### 5.1 Program-Specific COMMAREA Extension (WS-THIS-PROGCOMMAREA)

Defined at lines 199–203. Only contains:

| Field              | PIC    | Description                            |
|--------------------|--------|----------------------------------------|
| CA-FROM-PROGRAM    | X(08)  | Program that called this program       |
| CA-FROM-TRANID     | X(04)  | Transaction ID of calling program      |

### 5.2 Output Edit Variables (CICS-OUTPUT-EDIT-VARS)

| Field                    | PIC        | Description                           |
|--------------------------|------------|---------------------------------------|
| CARD-ACCT-ID-X           | X(11)      | Account ID alphanumeric view          |
| CARD-ACCT-ID-N (REDEFINES)| 9(11)     | Account ID numeric view               |
| CARD-CVV-CD-X            | X(03)      | CVV alphanumeric                      |
| CARD-CVV-CD-N (REDEFINES)| 9(03)      | CVV numeric                           |
| CARD-CARD-NUM-X          | X(16)      | Card number alphanumeric              |
| CARD-CARD-NUM-N (REDEFINES)| 9(16)    | Card number numeric                   |
| CARD-NAME-EMBOSSED-X     | X(50)      | Embossed name                         |
| CARD-STATUS-X            | X(1)       | Active status                         |
| CARD-EXPIRAION-DATE-X    | X(10)      | Full expiry date YYYY-MM-DD           |
| CARD-EXPIRY-YEAR (REDEFINES) | X(4)   | Positions 1-4                         |
| CARD-EXPIRY-MONTH (REDEFINES)| X(2)   | Positions 6-7                         |
| CARD-EXPIRY-DAY (REDEFINES)  | X(2)   | Positions 9-10                        |
| CARD-EXPIRAION-DATE-N (REDEFINES)| 9(10)| Numeric view of full date           |

### 5.3 CARD-RECORD (from CVACT02Y) — see COCRDLIC_spec.md section 5.3.

### 5.4 CARDDEMO-COMMAREA (from COCOM01Y) — see COCRDLIC_spec.md section 5.4.

---

## 6. File Access

### CARDDAT (LIT-CARDFILENAME = 'CARDDAT ')
- **Type**: VSAM KSDS
- **Primary key**: CARD-NUM X(16)
- **Operation**: Direct READ by primary key
- **Paragraph**: 9100-GETCARD-BYACCTCARD (line 736)
- **Key built**: WS-CARD-RID-CARDNUM ← CC-CARD-NUM

### CARDAIX (LIT-CARDFILENAME-ACCT-PATH = 'CARDAIX ')
- **Type**: VSAM Alternate Index path on CARDDAT keyed by CARD-ACCT-ID
- **Operation**: READ by alternate key (paragraph 9150-GETCARD-BYACCT, line 779)
- **Note**: Paragraph 9150 is defined but is NOT called from the main 9000-READ-DATA driver in COCRDSLC. It is dead code in the current version.

---

## 7. Program Flow — Paragraph-by-Paragraph

### 0000-MAIN (Entry Point, lines 247–408)

1. EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE).
2. INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA.
3. SET WS-RETURN-MSG-OFF.
4. **COMMAREA load**: If EIBCALEN=0 OR (FROM-PROGRAM=COMEN01C AND NOT REENTER), initialize CARDDEMO-COMMAREA and WS-THIS-PROGCOMMAREA; else load both from DFHCOMMAREA.
5. PERFORM YYYY-STORE-PFKEY.
6. **PFKey validation**: Accepts ENTER, PFK03 only. Any other key is coerced to ENTER.
7. **Main dispatch EVALUATE** (lines 304–381):

| Condition                                              | Action                                                          |
|--------------------------------------------------------|-----------------------------------------------------------------|
| CCARD-AID-PFK03                                        | Determine return program (FROM-PROGRAM or COMEN01C), XCTL back |
| CDEMO-PGM-ENTER AND FROM-PROGRAM = COCRDLIC            | Set INPUT-OK, move COMMAREA keys to CC fields, 9000-READ-DATA, 1000-SEND-MAP, COMMON-RETURN |
| CDEMO-PGM-ENTER (other context)                        | 1000-SEND-MAP (show blank entry form), COMMON-RETURN            |
| CDEMO-PGM-REENTER                                      | 2000-PROCESS-INPUTS; if INPUT-ERROR send map, else 9000-READ-DATA then send map |
| OTHER                                                  | Set ABEND-CULPRIT/CODE, SEND-PLAIN-TEXT and return              |

8. Post-EVALUATE: if INPUT-ERROR still set, send map and COMMON-RETURN.

### COMMON-RETURN (lines 394–407)
- Moves WS-RETURN-MSG to CCARD-ERROR-MSG.
- Packs CARDDEMO-COMMAREA and WS-THIS-PROGCOMMAREA into WS-COMMAREA.
- EXEC CICS RETURN TRANSID(CCDL) COMMAREA(WS-COMMAREA).

### 1000-SEND-MAP (lines 412–424)
Driver for screen output. Calls in sequence:
- 1100-SCREEN-INIT
- 1200-SETUP-SCREEN-VARS
- 1300-SETUP-SCREEN-ATTRS
- 1400-SEND-SCREEN

### 1100-SCREEN-INIT (lines 427–454)
- Clears CCRDSLAO to LOW-VALUES.
- Sets TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO from literals.
- Sets CURDATEO (MM/DD/YY format) and CURTIMEO (HH:MM:SS) from FUNCTION CURRENT-DATE.

### 1200-SETUP-SCREEN-VARS (lines 457–497)
- If EIBCALEN=0: set WS-PROMPT-FOR-INPUT message.
- Else: if CDEMO-ACCT-ID=0 send LOW-VALUES to ACCTSIDO else send CC-ACCT-ID.
- Same logic for CDEMO-CARD-NUM → CARDSIDO.
- If FOUND-CARDS-FOR-ACCOUNT: populate CRDNAMEO, EXPMONO, EXPYEARO, CRDSTCDO from CARD-RECORD fields.
- If WS-NO-INFO-MESSAGE: default to WS-PROMPT-FOR-INPUT.
- Move WS-RETURN-MSG to ERRMSGO, WS-INFO-MSG to INFOMSGO.

### 1300-SETUP-SCREEN-ATTRS (lines 502–558)
- **Protect/unprotect ACCTSID and CARDSID**:
  - If CDEMO-LAST-MAPSET = COCRDLI (came from card list): protect both fields (DFHBMPRF).
  - Else: unprotect both (DFHBMFSE).
- **Cursor positioning** (EVALUATE):
  - FLG-ACCTFILTER-NOT-OK or BLANK → cursor to ACCTSID (length=-1).
  - FLG-CARDFILTER-NOT-OK or BLANK → cursor to CARDSID.
  - OTHER → cursor to ACCTSID.
- **Color**: If came from card list, set fields to DFHDFCOL (default). If filter errors, set to DFHRED. If blank field on REENTER, place '*' and set RED.
- INFOMSGO: if no message, DFHBMDAR (dark); else DFHNEUTR (neutral).

### 1400-SEND-SCREEN (lines 563–578)
- Sets CCARD-NEXT-MAPSET and CCARD-NEXT-MAP.
- Sets CDEMO-PGM-REENTER.
- EXEC CICS SEND MAP(CCRDSLA) MAPSET(COCRDSL) FROM(CCRDSLAO) CURSOR ERASE FREEKB.

### 2000-PROCESS-INPUTS (lines 582–592)
- PERFORM 2100-RECEIVE-MAP.
- PERFORM 2200-EDIT-MAP-INPUTS.
- Sets CCARD-ERROR-MSG, CCARD-NEXT-PROG/MAPSET/MAP to this program.

### 2100-RECEIVE-MAP (lines 596–606)
- EXEC CICS RECEIVE MAP(CCRDSLA) MAPSET(COCRDSL) INTO(CCRDSLAI).

### 2200-EDIT-MAP-INPUTS (lines 608–641)
- Set INPUT-OK, FLG-CARDFILTER-ISVALID, FLG-ACCTFILTER-ISVALID.
- Replace '*' or SPACES in ACCTSIDI with LOW-VALUES in CC-ACCT-ID.
- Replace '*' or SPACES in CARDSIDI with LOW-VALUES in CC-CARD-NUM.
- PERFORM 2210-EDIT-ACCOUNT.
- PERFORM 2220-EDIT-CARD.
- Cross-field edit: if both blank, set NO-SEARCH-CRITERIA-RECEIVED.

### 2210-EDIT-ACCOUNT (lines 647–681)
- If CC-ACCT-ID blank/zero: INPUT-ERROR, FLG-ACCTFILTER-BLANK, message 'Account number not provided'.
- If not numeric: INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, message 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER'.
- Else: move to CDEMO-ACCT-ID, FLG-ACCTFILTER-ISVALID.

### 2220-EDIT-CARD (lines 685–722)
- If CC-CARD-NUM blank/zero: INPUT-ERROR, FLG-CARDFILTER-BLANK, message 'Card number not provided'.
- If not numeric: INPUT-ERROR, FLG-CARDFILTER-NOT-OK, message 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER'.
- Else: move to CDEMO-CARD-NUM, FLG-CARDFILTER-ISVALID.

### 9000-READ-DATA (lines 726–733)
- Calls 9100-GETCARD-BYACCTCARD.

### 9100-GETCARD-BYACCTCARD (lines 736–775)
- Sets WS-CARD-RID-CARDNUM ← CC-CARD-NUM.
- EXEC CICS READ FILE(CARDDAT) RIDFLD(WS-CARD-RID-CARDNUM) INTO(CARD-RECORD).
- EVALUATE WS-RESP-CD:
  - NORMAL: SET FOUND-CARDS-FOR-ACCOUNT.
  - NOTFND: INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, FLG-CARDFILTER-NOT-OK, message 'Did not find cards for this search condition'.
  - OTHER: INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, build WS-FILE-ERROR-MESSAGE, move to WS-RETURN-MSG.

### 9150-GETCARD-BYACCT (lines 779–811)
- Reads CARDAIX by WS-CARD-RID-ACCT-ID.
- NOTFND: message 'Did not find this account in cards database'.
- **NOTE**: This paragraph is defined but never called by 9000-READ-DATA. It is unreachable dead code in the current implementation.

---

## 8. Inter-Program Interactions

| Direction | Target Program | Mechanism          | Trigger                                          | Data Passed                               |
|-----------|----------------|--------------------|--------------------------------------------------|-------------------------------------------|
| Outbound  | COMEN01C or caller | EXEC CICS XCTL | PFK03 — return to CDEMO-FROM-PROGRAM or menu     | CARDDEMO-COMMAREA                         |
| Self-loop | COCRDSLC       | EXEC CICS RETURN TRANSID(CCDL) | Normal screen re-display after input | WS-COMMAREA = CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA |
| Inbound   | COCRDLIC       | XCTL              | Row selected with 'S' from card list             | CARDDEMO-COMMAREA with CDEMO-ACCT-ID, CDEMO-CARD-NUM |
| Inbound   | COMEN01C       | XCTL              | Direct transaction CCDL from menu (less common)  | CARDDEMO-COMMAREA                         |

### PF3 Return Logic
On PF3, COCRDSLC routes back as follows:
- If CDEMO-FROM-TRANID is blank: use COMEN01C / CM00.
- Else: use CDEMO-FROM-PROGRAM / CDEMO-FROM-TRANID.

This allows the program to generically return to whoever called it.

---

## 9. Key Function Keys

| Key    | Action                                                       |
|--------|--------------------------------------------------------------|
| ENTER  | Search for card (if manual entry) or re-display              |
| PF3    | Exit to calling program or main menu                         |
| Other  | Coerced to ENTER                                             |

---

## 10. Error Handling

| Condition                          | Message                                                     | Behavior                                |
|------------------------------------|-------------------------------------------------------------|-----------------------------------------|
| Account not provided               | 'Account number not provided'                               | INPUT-ERROR, cursor to ACCTSID, RED     |
| Account not numeric                | 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER'      | INPUT-ERROR, RED on ACCTSID             |
| Card not provided                  | 'Card number not provided'                                  | INPUT-ERROR, cursor to CARDSID, RED     |
| Card not numeric                   | 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER'      | INPUT-ERROR, RED on CARDSID             |
| Both blank                         | 'No input received'                                         | INPUT-ERROR                             |
| Card not found in CARDDAT          | 'Did not find cards for this search condition'              | INPUT-ERROR, RED on both fields         |
| Account not in alt index           | 'Did not find this account in cards database'               | (set in 9150, but 9150 not called)      |
| File I/O error (other RESP)        | 'File Error: READ on CARDDAT returned RESP x,RESP2 y'       | INPUT-ERROR                             |
| Unexpected EVALUATE fall-through   | 'UNEXPECTED DATA SCENARIO' via SEND-PLAIN-TEXT              | Plain text display and RETURN           |
| CICS ABEND                         | EXEC CICS SEND ABEND-DATA; EXEC CICS ABEND ABCODE('9999')   | Abend with code 9999                    |

---

## 11. Transaction Flow Context

```
COCRDLIC (list)
    |-- XCTL ('S') --> COCRDSLC (CCDL) -- CICS RETURN(CCDL) loop
                          |-- XCTL PF3 --> COCRDLIC (or COMEN01C)
```

---

## 12. Screen Display Logic Summary

When FOUND-CARDS-FOR-ACCOUNT is set after a successful READ:
- CRDNAMEO ← CARD-EMBOSSED-NAME
- EXPMONO ← CARD-EXPIRY-MONTH (positions 6-7 of CARD-EXPIRAION-DATE)
- EXPYEARO ← CARD-EXPIRY-YEAR (positions 1-4 of CARD-EXPIRAION-DATE)
- CRDSTCDO ← CARD-ACTIVE-STATUS

All card detail fields on screen CCRDSLA are ASKIP (protected) — the user cannot modify them. This is a strict read-only display screen.

The ACCTSID and CARDSID entry fields are conditionally protected:
- Protected (DFHBMPRF) when coming from COCRDLIC (CDEMO-LAST-MAPSET = COCRDLI).
- Unprotected (DFHBMFSE) when the user enters the program directly.
