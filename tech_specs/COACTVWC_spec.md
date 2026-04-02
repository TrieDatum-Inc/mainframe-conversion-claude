# Technical Specification: COACTVWC.CBL

## 1. Executive Summary

COACTVWC is a CICS online COBOL program that implements the Account View function of the CardDemo application. It operates as a pseudo-conversational transaction (transaction ID: CAVW) allowing an operator to enter an 11-digit account number on the COACTVW mapset (map CACTVWA), retrieve and display all corresponding account and customer data in read-only mode, and then navigate to the main menu or other programs. Unlike its sibling COACTUPC, this program performs no updates; all VSAM file accesses are read-only. The program is simpler in structure, with a single two-pass flow: first to collect the account number, and second to read and display the data.

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COACTVWC.CBL | CICS COBOL Program | `app/cbl/COACTVWC.cbl` |
| COACTVW.BMS | BMS Mapset | `app/bms/COACTVW.bms` |
| COACTVW (copybook) | BMS-generated copybook | Resolved via COPY COACTVW at line 229 |
| CVACT01Y.CPY | Account record layout | `app/cpy/CVACT01Y.cpy` |
| CVACT02Y.CPY | Card record layout | `app/cpy/CVACT02Y.cpy` |
| CVACT03Y.CPY | Card xref record layout | `app/cpy/CVACT03Y.cpy` |
| CVCUS01Y.CPY | Customer record layout | `app/cpy/CVCUS01Y.cpy` |
| CVCRD01Y.CPY | Card working storage | `app/cpy/CVCRD01Y.cpy` |
| COCOM01Y.CPY | Application COMMAREA | `app/cpy/COCOM01Y.cpy` |
| COTTL01Y.CPY | Screen titles | `app/cpy/COTTL01Y.cpy` |
| CSDAT01Y.CPY | Current date variables | `app/cpy/CSDAT01Y.cpy` |
| CSMSG01Y.CPY | Common messages | `app/cpy/CSMSG01Y.cpy` |
| CSMSG02Y.CPY | Abend variables | `app/cpy/CSMSG02Y.cpy` |
| CSUSR01Y.CPY | Signed-on user data | `app/cpy/CSUSR01Y.cpy` |
| CSSTRPFY.CPY | PF key store routine | `app/cpy/CSSTRPFY.cpy` |
| DFHBMSCA | IBM BMS attribute constants | System copybook |
| DFHAID | IBM AID key definitions | System copybook |

---

## 3. Program Identity

| Property | Value | Source |
|---|---|---|
| Program ID | COACTVWC | Line 23 |
| Transaction ID | CAVW | Line 146, `LIT-THISTRANID` |
| Mapset | COACTVW | Line 148, `LIT-THISMAPSET` |
| Map | CACTVWA | Line 150, `LIT-THISMAP` |
| Layer | Business logic | Line 3 |
| Function | Accept and process Account View request | Line 4 |
| Date written | May 2022 | Line 25 |

---

## 4. Constants and Program References

All literals are defined in the WS-LITERALS group (lines 142-200):

| Constant | Value | Purpose |
|---|---|---|
| LIT-THISPGM | COACTVWC | This program name |
| LIT-THISTRANID | CAVW | This transaction ID |
| LIT-THISMAPSET | COACTVW | This mapset |
| LIT-THISMAP | CACTVWA | This map |
| LIT-CCLISTPGM | COCRDLIC | Card list program |
| LIT-CCLISTTRANID | CCLI | Card list transaction |
| LIT-CARDUPDATEPGM | COCRDUPC | Card update program |
| LIT-CARDUDPATETRANID | CCUP | Card update transaction |
| LIT-MENUPGM | COMEN01C | Main menu program |
| LIT-MENUTRANID | CM00 | Main menu transaction |
| LIT-CARDDTLPGM | COCRDSLC | Card detail program |
| LIT-CARDDTLTRANID | CCDL | Card detail transaction |
| LIT-ACCTFILENAME | ACCTDAT | Account VSAM file |
| LIT-CARDFILENAME | CARDDAT | Card VSAM file |
| LIT-CUSTFILENAME | CUSTDAT | Customer VSAM file |
| LIT-CARDFILENAME-ACCT-PATH | CARDAIX | Card file alternate index |
| LIT-CARDXREFNAME-ACCT-PATH | CXACAIX | Card xref alternate index |

---

## 5. WORKING-STORAGE Structure

### 5.1 Input Flag Variables (lines 50-65)

| Field | PIC | 88-level values |
|---|---|---|
| WS-INPUT-FLAG | X(1) | INPUT-OK='0', INPUT-ERROR='1', INPUT-PENDING=LOW-VALUES |
| WS-PFK-FLAG | X(1) | PFK-VALID='0', PFK-INVALID='1' |
| WS-EDIT-ACCT-FLAG | X(1) | FLG-ACCTFILTER-NOT-OK='0', FLG-ACCTFILTER-ISVALID='1', FLG-ACCTFILTER-BLANK=' ' |
| WS-EDIT-CUST-FLAG | X(1) | FLG-CUSTFILTER-NOT-OK='0', FLG-CUSTFILTER-ISVALID='1', FLG-CUSTFILTER-BLANK=' ' |

### 5.2 File RID and Read Flag (lines 73-85)

| Field | PIC | Purpose |
|---|---|---|
| WS-CARD-RID-CARDNUM | X(16) | Card number for RIDFLD |
| WS-CARD-RID-CUST-ID | 9(09) | Customer ID for RIDFLD |
| WS-CARD-RID-CUST-ID-X | X(09) | Redefines above |
| WS-CARD-RID-ACCT-ID | 9(11) | Account ID for RIDFLD |
| WS-CARD-RID-ACCT-ID-X | X(11) | Redefines above |
| WS-ACCOUNT-MASTER-READ-FLAG | X(1) | FOUND-ACCT-IN-MASTER='1' |
| WS-CUST-MASTER-READ-FLAG | X(1) | FOUND-CUST-IN-MASTER='1' |

### 5.3 Error Message Construction (lines 86-105)

`WS-FILE-ERROR-MESSAGE` is a formatted 80-byte string: `'File Error: ' + operation + ' on ' + filename + ' returned RESP ' + resp + ',RESP2 ' + resp2`.

### 5.4 Info and Return Messages (lines 109-138)

| 88-Level | Value | Used when |
|---|---|---|
| WS-NO-INFO-MESSAGE | SPACES / LOW-VALUES | No info to display |
| WS-PROMPT-FOR-INPUT | 'Enter or update id of account to display' | Initial entry |
| WS-INFORM-OUTPUT | 'Displaying details of given Account' | Data shown |
| WS-EXIT-MESSAGE | 'PF03 pressed.Exiting' | F3 pressed (return msg) |
| WS-PROMPT-FOR-ACCT | 'Account number not provided' | Blank account entry |
| NO-SEARCH-CRITERIA-RECEIVED | 'No input received' | All input blank |
| SEARCHED-ACCT-ZEROES | 'Account number must be a non zero 11 digit number' | Zero account |
| SEARCHED-ACCT-NOT-NUMERIC | 'Account number must be a non zero 11 digit number' | Non-numeric |
| DID-NOT-FIND-ACCT-IN-CARDXREF | 'Did not find this account in account card xref file' | XREF miss |
| DID-NOT-FIND-ACCT-IN-ACCTDAT | 'Did not find this account in account master file' | ACCTDAT miss |
| DID-NOT-FIND-CUST-IN-CUSTDAT | 'Did not find associated customer in master file' | CUSTDAT miss |
| XREF-READ-ERROR | 'Error reading account card xref File' | XREF read error |

### 5.5 Program-Specific COMMAREA (lines 213-218)

```cobol
01 WS-THIS-PROGCOMMAREA.
   05 CA-CALL-CONTEXT.
      10 CA-FROM-PROGRAM    PIC X(08).
      10 CA-FROM-TRANID     PIC X(04).
```

This is a minimal private context — only the caller's program name and transaction ID are stored.

---

## 6. COMMAREA Structure

COACTVWC uses the same composite COMMAREA pattern as COACTUPC (see COACTUPC_spec.md Section 4.1 for CARDDEMO-COMMAREA layout from COCOM01Y.CPY). The composite `WS-COMMAREA` is PIC X(2000) (line 218).

---

## 7. Program Flow (PROCEDURE DIVISION)

### 7.1 Entry Point: 0000-MAIN (lines 262-413)

```
0000-MAIN
  |
  +-- EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE)
  |
  +-- INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA
  |
  +-- MOVE LIT-THISTRANID -> WS-TRANID
  +-- SET WS-RETURN-MSG-OFF
  |
  +-- If EIBCALEN = 0 OR (from menu AND NOT re-enter):
  |     INITIALIZE CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA
  |   Else:
  |     MOVE DFHCOMMAREA(1:len) -> CARDDEMO-COMMAREA
  |     MOVE DFHCOMMAREA(offset:len) -> WS-THIS-PROGCOMMAREA
  |
  +-- PERFORM YYYY-STORE-PFKEY
  |
  +-- AID validation:
  |   Only ENTER and PFK03 are valid
  |   If invalid AID: SET CCARD-AID-ENTER
  |
  +-- EVALUATE TRUE
        WHEN CCARD-AID-PFK03
          -> XCTL to caller or menu
        WHEN CDEMO-PGM-ENTER
          -> PERFORM 1000-SEND-MAP, GO TO COMMON-RETURN
        WHEN CDEMO-PGM-REENTER
          -> PERFORM 2000-PROCESS-INPUTS
             IF INPUT-ERROR: PERFORM 1000-SEND-MAP, GO TO COMMON-RETURN
             ELSE: PERFORM 9000-READ-ACCT
                   PERFORM 1000-SEND-MAP
                   GO TO COMMON-RETURN
        WHEN OTHER
          -> SET ABEND conditions, PERFORM SEND-PLAIN-TEXT
```

### 7.2 COMMON-RETURN (lines 394-407)

```
MOVE WS-RETURN-MSG -> CCARD-ERROR-MSG
Assemble composite WS-COMMAREA
EXEC CICS RETURN
     TRANSID(CAVW)
     COMMAREA(WS-COMMAREA)
     LENGTH(LENGTH OF WS-COMMAREA)
```

### 7.3 F3 Exit Logic (lines 324-352)

Sets CDEMO-TO-TRANID/CDEMO-TO-PROGRAM from COMMAREA, defaulting to COMEN01C/CM00. Then:
```
EXEC CICS XCTL
     PROGRAM(CDEMO-TO-PROGRAM)
     COMMAREA(CARDDEMO-COMMAREA)
```
Note: COACTVWC does NOT issue SYNCPOINT before XCTL (unlike COACTUPC).

---

## 8. Paragraph-by-Paragraph Logic

### 8.1 1000-SEND-MAP (lines 416-428)

Orchestrates screen output:
1. PERFORM 1100-SCREEN-INIT
2. PERFORM 1200-SETUP-SCREEN-VARS
3. PERFORM 1300-SETUP-SCREEN-ATTRS
4. PERFORM 1400-SEND-SCREEN

### 8.2 1100-SCREEN-INIT (lines 431-458)

Initializes the output map CACTVWAO (LOW-VALUES), then populates the header fields:
- FUNCTION CURRENT-DATE -> WS-CURDATE-DATA
- CCDA-TITLE01 -> TITLE01O of CACTVWAO
- CCDA-TITLE02 -> TITLE02O of CACTVWAO
- LIT-THISTRANID -> TRNNAMEO of CACTVWAO
- LIT-THISPGM -> PGMNAMEO of CACTVWAO
- Formatted MM/DD/YY -> CURDATEO of CACTVWAO
- Formatted HH:MM:SS -> CURTIMEO of CACTVWAO

### 8.3 1200-SETUP-SCREEN-VARS (lines 460-535)

Populates all data fields on the output map based on context:

**If EIBCALEN = 0 (fresh start):**
Sets WS-PROMPT-FOR-INPUT.

**If EIBCALEN > 0:**

Account number field:
- If FLG-ACCTFILTER-BLANK: set ACCTSIDO to LOW-VALUES
- Else: move CC-ACCT-ID to ACCTSIDO

Account data (if FOUND-ACCT-IN-MASTER or FOUND-CUST-IN-MASTER):
- ACCT-ACTIVE-STATUS -> ACSTTUSO
- ACCT-CURR-BAL -> ACURBALO (displayed via PICOUT format in BMS)
- ACCT-CREDIT-LIMIT -> ACRDLIMO
- ACCT-CASH-CREDIT-LIMIT -> ACSHLIMO
- ACCT-CURR-CYC-CREDIT -> ACRCYCRO
- ACCT-CURR-CYC-DEBIT -> ACRCYDBO
- ACCT-OPEN-DATE -> ADTOPENO (full 10-char date string)
- ACCT-EXPIRAION-DATE -> AEXPDTO
- ACCT-REISSUE-DATE -> AREISDTO
- ACCT-GROUP-ID -> AADDGRPO

Customer data (if FOUND-CUST-IN-MASTER):
- CUST-ID -> ACSTNUMO
- SSN formatted as NNN-NN-NNNN using STRING statement (lines 496-504):
  `CUST-SSN(1:3) + '-' + CUST-SSN(4:2) + '-' + CUST-SSN(6:4)` -> ACSTSSNO
- CUST-FICO-CREDIT-SCORE -> ACSTFCOO
- CUST-DOB-YYYY-MM-DD -> ACSTDOBO (full date string)
- CUST-FIRST-NAME -> ACSFNAMO
- CUST-MIDDLE-NAME -> ACSMNAMO
- CUST-LAST-NAME -> ACSLNAMO
- CUST-ADDR-LINE-1 -> ACSADL1O
- CUST-ADDR-LINE-2 -> ACSADL2O
- CUST-ADDR-LINE-3 (city) -> ACSCITYO
- CUST-ADDR-STATE-CD -> ACSSTTEO
- CUST-ADDR-ZIP -> ACSZIPCO
- CUST-ADDR-COUNTRY-CD -> ACSCTRYO
- CUST-PHONE-NUM-1 -> ACSPHN1O (full formatted string)
- CUST-PHONE-NUM-2 -> ACSPHN2O
- CUST-GOVT-ISSUED-ID -> ACSGOVTO
- CUST-EFT-ACCOUNT-ID -> ACSEFTCO
- CUST-PRI-CARD-HOLDER-IND -> ACSPFLGO

Message line:
- If WS-NO-INFO-MESSAGE: SET WS-PROMPT-FOR-INPUT
- WS-RETURN-MSG -> ERRMSGO of CACTVWAO (line 22 error area)
- WS-INFO-MSG -> INFOMSGO of CACTVWAO (line 22 info area)

### 8.4 1300-SETUP-SCREEN-ATTRS (lines 541-572)

**Field protection:** Sets DFHBMFSE on ACCTSIDA (line 543) — the account number field is always unprotected for entry.

**Cursor positioning:** EVALUATE TRUE over flag states:
- FLG-ACCTFILTER-NOT-OK or FLG-ACCTFILTER-BLANK: cursor to ACCTSIDL
- OTHER: cursor to ACCTSIDL (always positions at account number field)

**Color:**
- Default color (DFHDFCOL) -> ACCTSIDC
- If FLG-ACCTFILTER-NOT-OK: DFHRED -> ACCTSIDC
- If FLG-ACCTFILTER-BLANK AND CDEMO-PGM-REENTER: '*' -> ACCTSIDO, DFHRED -> ACCTSIDC

**Info message color:**
- If WS-NO-INFO-MESSAGE: DFHBMDAR (dark) -> INFOMSGC
- Else: DFHNEUTR (neutral) -> INFOMSGC

### 8.5 1400-SEND-SCREEN (lines 577-591)

```
MOVE LIT-THISMAPSET -> CCARD-NEXT-MAPSET
MOVE LIT-THISMAP    -> CCARD-NEXT-MAP
SET CDEMO-PGM-REENTER TO TRUE

EXEC CICS SEND MAP(CACTVWA)
               MAPSET(COACTVW)
               FROM(CACTVWAO)
               CURSOR
               ERASE
               FREEKB
               RESP(WS-RESP-CD)
```

### 8.6 2000-PROCESS-INPUTS (lines 596-608)

Orchestrates input handling:
1. PERFORM 2100-RECEIVE-MAP
2. PERFORM 2200-EDIT-MAP-INPUTS
3. Moves context fields (WS-RETURN-MSG, program name, mapset, map) to CCARD-* fields

### 8.7 2100-RECEIVE-MAP (lines 610-620)

```
EXEC CICS RECEIVE MAP(CACTVWA)
               MAPSET(COACTVW)
               INTO(CACTVWAI)
               RESP(WS-RESP-CD)
               RESP2(WS-REAS-CD)
```

### 8.8 2200-EDIT-MAP-INPUTS (lines 622-643)

1. SET INPUT-OK, SET FLG-ACCTFILTER-ISVALID
2. If ACCTSIDI = '*' or SPACES: MOVE LOW-VALUES -> CC-ACCT-ID
   Else: MOVE ACCTSIDI -> CC-ACCT-ID
3. PERFORM 2210-EDIT-ACCOUNT
4. If FLG-ACCTFILTER-BLANK: SET NO-SEARCH-CRITERIA-RECEIVED

### 8.9 2210-EDIT-ACCOUNT (lines 649-683)

| Check | Condition | Result |
|---|---|---|
| Not supplied | CC-ACCT-ID = LOW-VALUES or SPACES | INPUT-ERROR, FLG-ACCTFILTER-BLANK, WS-PROMPT-FOR-ACCT |
| Not numeric | CC-ACCT-ID IS NOT NUMERIC | INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, error message |
| Zero value | CC-ACCT-ID = ZEROES | INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, error message |
| Valid | Otherwise | MOVE CC-ACCT-ID -> CDEMO-ACCT-ID, FLG-ACCTFILTER-ISVALID |

Error message for non-numeric/zero: `'Account Filter must  be a non-zero 11 digit number'` (line 672).

### 8.10 9000-READ-ACCT (lines 687-720)

The data retrieval orchestrator (read-only):

1. SET WS-NO-INFO-MESSAGE
2. MOVE CDEMO-ACCT-ID -> WS-CARD-RID-ACCT-ID
3. PERFORM 9200-GETCARDXREF-BYACCT
4. If FLG-ACCTFILTER-NOT-OK: exit
5. PERFORM 9300-GETACCTDATA-BYACCT
6. If DID-NOT-FIND-ACCT-IN-ACCTDAT: exit
7. MOVE CDEMO-CUST-ID -> WS-CARD-RID-CUST-ID
8. PERFORM 9400-GETCUSTDATA-BYCUST
9. If DID-NOT-FIND-CUST-IN-CUSTDAT: exit

Data is left in ACCOUNT-RECORD and CUSTOMER-RECORD (from their respective copybooks) and the CCARD-* context fields for display in 1200-SETUP-SCREEN-VARS.

### 8.11 9200-GETCARDXREF-BYACCT (lines 723-771)

```
EXEC CICS READ
     DATASET(CXACAIX)
     RIDFLD(WS-CARD-RID-ACCT-ID-X)
     KEYLENGTH(LENGTH OF WS-CARD-RID-ACCT-ID-X)
     INTO(CARD-XREF-RECORD)
     LENGTH(LENGTH OF CARD-XREF-RECORD)
     RESP(WS-RESP-CD)
     RESP2(WS-REAS-CD)
```

EVALUATE WS-RESP-CD:
- DFHRESP(NORMAL): XREF-CUST-ID -> CDEMO-CUST-ID; XREF-CARD-NUM -> CDEMO-CARD-NUM
- DFHRESP(NOTFND): INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, detailed STRING error message
- OTHER: INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, WS-FILE-ERROR-MESSAGE

### 8.12 9300-GETACCTDATA-BYACCT (lines 774-822)

```
EXEC CICS READ
     DATASET(ACCTDAT)
     RIDFLD(WS-CARD-RID-ACCT-ID-X)
     KEYLENGTH(LENGTH OF WS-CARD-RID-ACCT-ID-X)
     INTO(ACCOUNT-RECORD)
     LENGTH(LENGTH OF ACCOUNT-RECORD)
     RESP(WS-RESP-CD)
     RESP2(WS-REAS-CD)
```

EVALUATE WS-RESP-CD:
- DFHRESP(NORMAL): SET FOUND-ACCT-IN-MASTER
- DFHRESP(NOTFND): INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, STRING error message
- OTHER: INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, WS-FILE-ERROR-MESSAGE

### 8.13 9400-GETCUSTDATA-BYCUST (lines 825-869)

```
EXEC CICS READ
     DATASET(CUSTDAT)
     RIDFLD(WS-CARD-RID-CUST-ID-X)
     KEYLENGTH(LENGTH OF WS-CARD-RID-CUST-ID-X)
     INTO(CUSTOMER-RECORD)
     LENGTH(LENGTH OF CUSTOMER-RECORD)
     RESP(WS-RESP-CD)
     RESP2(WS-REAS-CD)
```

EVALUATE WS-RESP-CD:
- DFHRESP(NORMAL): SET FOUND-CUST-IN-MASTER
- DFHRESP(NOTFND): INPUT-ERROR, FLG-CUSTFILTER-NOT-OK, STRING error message
- OTHER: INPUT-ERROR, FLG-CUSTFILTER-NOT-OK, WS-FILE-ERROR-MESSAGE

---

## 9. CICS Commands Used

| CICS Command | Location | Purpose |
|---|---|---|
| HANDLE ABEND LABEL | Line 264 | Register abend handler |
| RECEIVE MAP | Line 611-615 | Read operator input (account number) |
| SEND MAP ... ERASE FREEKB CURSOR | Lines 583-589 | Display screen to operator |
| READ DATASET (CXACAIX) | Lines 727-734 | Read card xref via alternate index by account ID |
| READ DATASET (ACCTDAT) | Lines 776-783 | Read account master record |
| READ DATASET (CUSTDAT) | Lines 826-833 | Read customer master record |
| XCTL PROGRAM | Lines 349-351 | Transfer control to caller/menu on F3 |
| RETURN TRANSID COMMAREA | Lines 402-405 | Pseudo-conversational return |
| SEND TEXT ERASE FREEKB | Lines 878-882 | Diagnostic/unexpected-path text output |
| HANDLE ABEND CANCEL | Lines 930-932 | Cancel abend handler in abend routine |
| ABEND ABCODE('9999') | Lines 934-935 | Force abend in error handler |

---

## 10. VSAM Files Referenced

| Logical Name | Physical Name | Access | Key Field |
|---|---|---|---|
| ACCTDAT | ACCTDAT | Read-only | ACCT-ID 9(11) |
| CUSTDAT | CUSTDAT | Read-only | CUST-ID 9(09) |
| CXACAIX | CXACAIX | Read-only (alternate index) | XREF-ACCT-ID 9(11) |

No REWRITE, WRITE, or DELETE commands are issued. All access is read-only.

---

## 11. Data Structures

All shared record structures are identical to those used in COACTUPC. See COACTUPC_spec.md Sections 9.1-9.3 for field-level definitions of ACCOUNT-RECORD (CVACT01Y), CUSTOMER-RECORD (CVCUS01Y), and CARD-XREF-RECORD (CVACT03Y).

COACTVWC additionally COPYs CVACT02Y (CARD-RECORD), though the CARD-RECORD structure is not directly populated in the procedure division — it is available if needed but not used in the current display logic.

---

## 12. Inter-Program Interactions

| Direction | Program | Transaction | Mechanism | Condition |
|---|---|---|---|---|
| Exit to (default) | COMEN01C | CM00 | XCTL | F3 with no CDEMO-FROM-PROGRAM |
| Exit to (caller) | (from COMMAREA) | (from COMMAREA) | XCTL | F3 with CDEMO-FROM-PROGRAM set |
| Called by | COMEN01C | CM00 | XCTL | Standard menu navigation |
| Called by | Other programs | Various | XCTL | Via CDEMO-FROM-PROGRAM |
| Pseudo-return | COACTVWC | CAVW | CICS RETURN | Every non-exit path |

Referenced but not XCTLed to within this program:
- COCRDLIC (CCLI) — card list program
- COCRDUPC (CCUP) — card update program
- COCRDSLC (CCDL) — card detail program

---

## 13. SSN Display Formatting

COACTVWC uses a STRING statement (lines 496-504) to format the SSN for display, which differs from COACTUPC's approach (which splits the SSN into three separate input fields):

```cobol
STRING
    CUST-SSN(1:3)
    '-'
    CUST-SSN(4:2)
    '-'
    CUST-SSN(6:4)
    DELIMITED BY SIZE
    INTO ACSTSSNO OF CACTVWAO
```

Note: `CUST-SSN` is defined as PIC 9(09) in CVCUS01Y. The reference string offset starts at 1 which is standard COBOL 1-based referencing — the 9-digit numeric SSN is treated as a character string for display purposes.

---

## 14. Error Handling

| Error Condition | Response | Source |
|---|---|---|
| No account number entered | WS-PROMPT-FOR-ACCT, INPUT-ERROR, cursor to ACCTSID, field turns red | 2210-EDIT-ACCOUNT |
| Account number not numeric or zero | Error message in WS-RETURN-MSG, INPUT-ERROR, field red | 2210-EDIT-ACCOUNT |
| Account not found in CXACAIX (NOTFND) | Detailed error with account number and RESP/RESP2, INPUT-ERROR | 9200-GETCARDXREF-BYACCT |
| Account not found in ACCTDAT (NOTFND) | Detailed error with account number and RESP/RESP2, INPUT-ERROR | 9300-GETACCTDATA-BYACCT |
| Customer not found in CUSTDAT (NOTFND) | Detailed error with customer ID and RESP/RESP2, INPUT-ERROR | 9400-GETCUSTDATA-BYCUST |
| VSAM file error (OTHER response) | WS-FILE-ERROR-MESSAGE with operation+file+RESP+RESP2 | All 9xxx paragraphs |
| Unexpected evaluation path | Abend code set, PERFORM SEND-PLAIN-TEXT (diagnostic), not ABEND | 0000-MAIN WHEN OTHER |
| CICS-raised abend | HANDLE ABEND -> ABEND-ROUTINE -> SEND data, ABEND 9999 | Lines 264, 916-937 |

Error messages are placed in WS-RETURN-MSG and moved to ERRMSGO of CACTVWAO (line 22, row 23 on screen).

---

## 15. Transaction Flow

```
User starts transaction CAVW (or arrives via XCTL from menu)
        |
        v
COACTVWC Pass 1: CDEMO-PGM-ENTER (EIBCALEN=0 or from menu)
  - 1000-SEND-MAP:
    - Clears screen
    - Sets info message: "Enter or update id of account to display"
    - Account number field unprotected, cursor positioned there
  - CICS RETURN TRANSID(CAVW) COMMAREA
        |
        v
Operator enters 11-digit account number, presses ENTER
        |
        v
COACTVWC Pass 2: CDEMO-PGM-REENTER
  - 2000-PROCESS-INPUTS:
    - RECEIVE MAP: capture ACCTSIDI
    - 2200-EDIT-MAP-INPUTS:
      - 2210-EDIT-ACCOUNT: validate account number
  - If INPUT-ERROR:
      - 1000-SEND-MAP (with error highlighted)
      - CICS RETURN
  - If INPUT-OK:
      - 9000-READ-ACCT:
        - READ CXACAIX (alternate index) -> get CDEMO-CUST-ID, CDEMO-CARD-NUM
        - READ ACCTDAT -> populate ACCOUNT-RECORD; SET FOUND-ACCT-IN-MASTER
        - READ CUSTDAT -> populate CUSTOMER-RECORD; SET FOUND-CUST-IN-MASTER
      - 1000-SEND-MAP:
        - 1200-SETUP-SCREEN-VARS: maps all account + customer fields to output map
        - Account data: status, balance, limits, dates, group ID
        - Customer data: SSN (formatted), DOB, FICO, name, address, phones
        - Info message: "Enter or update id of account to display"
        - All data fields are ASKIP (read-only in COACTVW mapset)
      - CICS RETURN TRANSID(CAVW) COMMAREA
        |
        v
Operator reviews data, presses F3 to exit
        |
        v
COACTVWC: CCARD-AID-PFK03
  - XCTL to CDEMO-FROM-PROGRAM (or COMEN01C if none)
```

---

## 16. Differences from COACTUPC

| Aspect | COACTVWC | COACTUPC |
|---|---|---|
| Purpose | Display only | Display and update |
| Transaction ID | CAVW | CAUP |
| Map | CACTVWA | CACTUPA |
| Write operations | None | REWRITE ACCTDAT, REWRITE CUSTDAT |
| State machine | Simple enter/reenter | 6-state ACUP-CHANGE-ACTION |
| SYNCPOINT before F3 XCTL | No | Yes |
| Date field handling | Full date strings (ADTOPENO, AEXPDTO, AREISDTO) | Split year/month/day fields |
| SSN display | Single formatted field ACSTSSNO | Three separate fields ACTSSN1/2/3 |
| Phone display | Single field ACSPHN1O, ACSPHN2O | Three-part fields PH1A/B/C, PH2A/B/C |
| COMMAREA private state | 12 bytes (just caller context) | ~800+ bytes (old+new data snapshots) |
| Validation | Account number only | 35+ fields, cross-field edits |
| Field protection | All output fields ASKIP in BMS | Dynamically set PROT/UNPROT per state |
| SYNCPOINT ROLLBACK | Not needed | Line 4100, on customer REWRITE failure |
| CVACT02Y (CARD-RECORD) | Included (line 248) | Not included |

---

## 17. Open Questions and Gaps

| Item | Status |
|---|---|
| CVACT02Y.CPY (CARD-RECORD) | Included via COPY at line 248 but CARD-RECORD is not populated in the procedure division. Purpose unclear — may be remnant from early development. |
| CVCRD01Y.CPY | Not read in detail — provides CC-WORK-AREA containing CC-ACCT-ID referenced throughout |
| COTTL01Y.CPY | Not read — provides CCDA-TITLE01 and CCDA-TITLE02 |
| CSMSG01Y.CPY / CSMSG02Y.CPY | Not read — provides CCARD-* fields, ABEND-DATA structure |
| Customer data display when account found but customer not found | FOUND-ACCT-IN-MASTER and NOT FOUND-CUST-IN-MASTER condition: account fields are shown but all customer fields remain blank (LOW-VALUES) from 1100-SCREEN-INIT |
| CXACAIX alternate index | Assumed to be an alternate index path over the card cross-reference file keyed by account ID. Physical VSAM DDname TBD from CSD/RDO definitions. |
| CARDAIX alternate index | Defined as LIT-CARDFILENAME-ACCT-PATH = 'CARDAIX' but not actually used in any CICS READ in COACTVWC |
