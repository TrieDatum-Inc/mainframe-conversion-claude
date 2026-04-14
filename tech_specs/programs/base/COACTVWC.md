# Technical Specification: COACTVWC

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COACTVWC                                             |
| Source File      | app/cbl/COACTVWC.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CAVW (LIT-THISTRANID, line 146)                      |
| Function         | Accept and process Account View request. Displays account and associated customer details for a given account ID. Allows navigation to card list (COCRDLIC), card detail (COCRDSLC), card update (COCRDUPC), or main menu (COMEN01C). |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CAVW and COMMAREA)

EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE)
INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA
MOVE LIT-THISTRANID ('CAVW') TO WS-TRANID

IF EIBCALEN = 0 OR (CDEMO-FROM-PROGRAM = 'COMEN01C' AND NOT CDEMO-PGM-REENTER):
    INITIALIZE CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA
ELSE:
    MOVE DFHCOMMAREA(1:LENGTH OF CARDDEMO-COMMAREA) TO CARDDEMO-COMMAREA
    MOVE DFHCOMMAREA(offset) TO WS-THIS-PROGCOMMAREA

PERFORM YYYY-STORE-PFKEY (maps EIBAID to PFK flags)

Check valid AID: ENTER or PF03 accepted; others reset to ENTER

EVALUATE TRUE:
    WHEN CCARD-AID-PFK03:
        Set CDEMO-TO-PROGRAM = CDEMO-FROM-PROGRAM (or LIT-MENUPGM if blank)
        Set navigation fields; EXEC CICS XCTL PROGRAM COMMAREA
    WHEN CDEMO-PGM-ENTER:
        PERFORM 1000-SEND-MAP → COMMON-RETURN
    WHEN CDEMO-PGM-REENTER:
        PERFORM 2000-PROCESS-INPUTS
        IF INPUT-ERROR: PERFORM 1000-SEND-MAP → COMMON-RETURN
        ELSE: PERFORM 9000-READ-ACCT; PERFORM 1000-SEND-MAP → COMMON-RETURN
    WHEN OTHER:
        ABEND-CULPRIT='COACTVWC', ABEND-CODE='0001', SEND-PLAIN-TEXT

COMMON-RETURN:
    MOVE WS-RETURN-MSG TO CCARD-ERROR-MSG
    Build WS-COMMAREA = CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA
    EXEC CICS RETURN TRANSID('CAVW') COMMAREA(WS-COMMAREA) LENGTH(...)
```

### Paragraph-Level Detail

Lines 261–449 capture the full main procedure. Additional paragraphs (1000-SEND-MAP, 2000-PROCESS-INPUTS, 9000-READ-ACCT, etc.) begin at approximately line 400.

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| 0000-MAIN              | 262–393   | Main entry: abend handler setup; COMMAREA load; PFK routing; EVALUATE dispatch |
| COMMON-RETURN          | 394–~410  | Build combined COMMAREA; CICS RETURN TRANSID('CAVW') |
| YYYY-STORE-PFKEY       | ~410+     | Maps EIBAID to CCARD-AID-* conditions |
| 1000-SEND-MAP          | ~420+     | CICS SEND MAP('CACTVWA') MAPSET('COACTVW') FROM(COACTVWA-O) |
| 2000-PROCESS-INPUTS    | ~430+     | Validate account ID from screen; set INPUT-ERROR if invalid |
| 9000-READ-ACCT         | ~450+     | CICS READ ACCTDAT by ACCT-ID; CICS READ CUSTDAT; optional CICS READ CARDAIX or CXACAIX |
| ABEND-ROUTINE          | ~500+     | CICS HANDLE ABEND target |
| SEND-PLAIN-TEXT        | ~500+     | Sends plain text error message to terminal |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook   | Used In              | Contents |
|------------|----------------------|----------|
| COCOM01Y   | WORKING-STORAGE (line 211) | CARDDEMO-COMMAREA: CDEMO-GENERAL-INFO, CDEMO-CUSTOMER-INFO, CDEMO-ACCOUNT-INFO, CDEMO-CARD-INFO, CDEMO-MORE-INFO |
| CVCRD01Y   | WORKING-STORAGE (line 207) | CC-WORK-AREA structure for card display — **[UNRESOLVED]** exact layout requires app/cpy/CVCRD01Y.cpy |
| COACTVW    | WORKING-STORAGE (line 229) | BMS mapset copybook: COACTVWA input/output maps (CACTVWA) |
| COTTL01Y   | WORKING-STORAGE (line 226) | Screen title constants (CCDA-TITLE01, CCDA-TITLE02) |
| CSDAT01Y   | WORKING-STORAGE (line 232) | Current date/time working storage (WS-CURDATE-DATA, etc.) |
| CSMSG01Y   | WORKING-STORAGE (line 235) | Common message literals (CCDA-MSG-*) |
| CSMSG02Y   | WORKING-STORAGE (line 238) | Abend message variables (ABEND-CULPRIT, ABEND-CODE, ABEND-REASON) |
| CSUSR01Y   | WORKING-STORAGE (line 241) | Signed-on user data |
| CVACT01Y   | WORKING-STORAGE (line 244) | ACCOUNT-RECORD (300 bytes) |
| CVACT02Y   | WORKING-STORAGE (line 248) | CARD-RECORD (150 bytes) |
| CVACT03Y   | WORKING-STORAGE (line 251) | CARD-XREF-RECORD (50 bytes): XREF-CARD-NUM, XREF-CUST-ID, XREF-ACCT-ID |
| CVCUS01Y   | WORKING-STORAGE (line 254) | CUSTOMER-RECORD (500 bytes) |
| DFHBMSCA   | WORKING-STORAGE (line 221) | IBM BMS attribute byte constants |
| DFHAID     | WORKING-STORAGE (implicitly included) | EIBAID key constants |

### Key Working Storage Variables

| Variable                       | PIC / Structure | Purpose |
|--------------------------------|-----------------|---------|
| WS-RESP-CD / WS-REAS-CD        | S9(09) COMP     | CICS command response/reason codes |
| WS-TRANID                      | X(4) = 'CAVW'   | Transaction ID |
| LIT-THISPGM                    | X(8) = 'COACTVWC' | Used in COMMAREA navigation fields |
| LIT-THISTRANID                 | X(4) = 'CAVW'   | Transaction ID constant |
| LIT-THISMAPSET                 | X(8) = 'COACTVW' | BMS mapset name |
| LIT-THISMAP                    | X(7) = 'CACTVWA' | BMS map name |
| LIT-CCLISTPGM                  | X(8) = 'COCRDLIC' | Card list program |
| LIT-CARDUPDATEPGM              | X(8) = 'COCRDUPC' | Card update program |
| LIT-MENUPGM                    | X(8) = 'COMEN01C' | Main menu program |
| LIT-CARDDTLPGM                 | X(8) = 'COCRDSLC' | Card detail program |
| LIT-ACCTFILENAME               | X(8) = 'ACCTDAT ' | CICS file name for account |
| LIT-CARDFILENAME               | X(8) = 'CARDDAT ' | CICS file name for cards |
| LIT-CUSTFILENAME               | X(8) = 'CUSTDAT ' | CICS file name for customers |
| LIT-CARDFILENAME-ACCT-PATH     | X(8) = 'CARDAIX ' | Alternate index on CARDDAT by account |
| LIT-CARDXREFNAME-ACCT-PATH     | X(8) = 'CXACAIX ' | Alternate index on XREF by account |
| WS-XREF-RID                    | Group (36 bytes) | CARD-RID-CARDNUM X(16) + CARD-RID-CUST-ID 9(9) + CARD-RID-ACCT-ID 9(11) |
| WS-ACCOUNT-MASTER-READ-FLAG    | X(1)            | '1' = account found in ACCTDAT |
| WS-CUST-MASTER-READ-FLAG       | X(1)            | '1' = customer found in CUSTDAT |
| WS-EDIT-ACCT-FLAG              | X(1)            | '0'=invalid, '1'=valid, ' '=blank |
| WS-INPUT-FLAG                  | X(1)            | LOW-VALUES=pending; '0'=ok; '1'=error |
| WS-PFK-FLAG                    | X(1)            | '0'=valid; '1'=invalid |
| WS-INFO-MSG                    | X(40)           | 88-levels: WS-PROMPT-FOR-INPUT, WS-INFORM-OUTPUT |
| WS-RETURN-MSG                  | X(75)           | 88-levels: WS-EXIT-MESSAGE, error message conditions |
| WS-COMMAREA                    | X(2000)         | Combined commarea (CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA) for CICS RETURN |
| WS-THIS-PROGCOMMAREA           | Group           | CA-FROM-PROGRAM X(8) + CA-FROM-TRANID X(4) |
| SEARCHED-ACCT-ZEROES           | 88 = specific text | Validation: account must be non-zero 11-digit number |
| DID-NOT-FIND-ACCT-IN-CARDXREF  | 88 = specific text | Error message for missing XREF entry |
| DID-NOT-FIND-ACCT-IN-ACCTDAT   | 88 = specific text | Error message for missing account |
| DID-NOT-FIND-CUST-IN-CUSTDAT   | 88 = specific text | Error message for missing customer |

---

## 4. CICS Commands Used

| Command | Purpose |
|---------|---------|
| EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE) | Abend handler registration |
| EXEC CICS RETURN TRANSID('CAVW') COMMAREA LENGTH | Pseudo-conversational return |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | Transfer to previous or menu program |
| EXEC CICS SEND MAP('CACTVWA') MAPSET('COACTVW') FROM ERASE | Send account view screen |
| EXEC CICS RECEIVE MAP MAPSET INTO RESP RESP2 | Receive screen input |
| EXEC CICS READ DATASET INTO LENGTH RIDFLD KEYLENGTH RESP RESP2 | Read ACCTDAT, CUSTDAT |
| EXEC CICS READ DATASET RIDFLD KEYLENGTH GTEQ RESP RESP2 | Read CARDAIX or CXACAIX (alternate index path, inferred) |
| EXEC CICS ASKTIME / FORMATTIME | Date/time for screen header (via CSDAT01Y) |
| EXEC CICS INQUIRE PROGRAM | Not used here (that is COMEN01C); not observed in COACTVWC |

---

## 5. File/Dataset Access

| CICS File Name | Access    | Purpose |
|----------------|-----------|---------|
| ACCTDAT        | READ      | Account master record lookup by ACCT-ID |
| CUSTDAT        | READ      | Customer master record lookup by CUST-ID (from XREF) |
| CARDDAT        | READ      | Card record lookup (for display) |
| CARDAIX        | READ (AIX) | Account-path alternate index on CARDDAT; lookup by account ID |
| CXACAIX        | READ (AIX) | Alternate index on XREF by account ID |

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction ID |
|------------|---------|----------------|
| COACTVW    | CACTVWA | CAVW           |

**Key Screen Fields:**

| Field (Map)    | Direction | Description |
|----------------|-----------|-------------|
| ACTIDINI       | Input     | Account ID to look up |
| CCARD-ERROR-MSG (ERRMSGO equivalent) | Output | Error/info messages |
| Account fields | Output    | ACCT-CURR-BAL, ACCT-CREDIT-LIMIT, ACCT-ACTIVE-STATUS, dates, etc. |
| Customer fields | Output   | Name, address, phone, SSN, DOB, FICO |
| TITLE01O/TITLE02O | Output | Application title from COTTL01Y |
| CURDATEO/CURTIMEO | Output | Current date and time from CSDAT01Y |
| TRNNAMEO/PGMNAMEO | Output | Transaction and program name |

**Navigation:**
- PF3: XCTL to CDEMO-FROM-PROGRAM (or COMEN01C if blank)
- Enter: Process account ID input; display account/customer details
- Navigation to card programs (COCRDLIC, COCRDSLC, COCRDUPC) via COMMAREA context

---

## 7. Called Programs / Transfers

| Program            | Method       | Condition |
|--------------------|--------------|-----------|
| CDEMO-FROM-PROGRAM | CICS XCTL    | PF3 pressed |
| COMEN01C (default) | CICS XCTL    | PF3 when CDEMO-FROM-PROGRAM is blank |
| COCRDLIC           | CICS XCTL    | Navigation to card list (via COMMAREA TO-PROGRAM) |
| COCRDSLC           | CICS XCTL    | Navigation to card detail |
| COCRDUPC           | CICS XCTL    | Navigation to card update |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 (no commarea) | Initialize commarea; send fresh screen |
| Account ID blank/spaces | WS-RETURN-MSG = WS-PROMPT-FOR-ACCT; INPUT-ERROR; re-send map |
| Account ID all zeros | WS-RETURN-MSG = SEARCHED-ACCT-ZEROES; INPUT-ERROR |
| Account ID not numeric | WS-RETURN-MSG = SEARCHED-ACCT-NOT-NUMERIC; INPUT-ERROR |
| ACCTDAT NOTFND | WS-RETURN-MSG = DID-NOT-FIND-ACCT-IN-ACCTDAT; send map |
| CUSTDAT NOTFND | WS-RETURN-MSG = DID-NOT-FIND-CUST-IN-CUSTDAT; send map |
| CARDAIX/CXACAIX error | WS-RETURN-MSG = XREF-READ-ERROR or DID-NOT-FIND-ACCT-IN-CARDXREF |
| Other CICS RESP error | WS-FILE-ERROR-MESSAGE populated with opname/file/RESP/RESP2 |
| Invalid AID (not ENTER/PF03) | Reset to ENTER; re-process |
| Unexpected EVALUATE branch | ABEND-CULPRIT='COACTVWC', ABEND-CODE='0001'; SEND-PLAIN-TEXT |
| CICS HANDLE ABEND | ABEND-ROUTINE (CSMSG02Y abend variables) |

---

## 9. Business Rules

1. **Account ID validation**: Must be a non-zero 11-digit numeric value. Zero and non-numeric inputs are rejected with specific messages.
2. **Account-to-customer chain**: Account is read first (ACCTDAT); then XREF is used to obtain CUST-ID; then customer is read (CUSTDAT). Navigation to CARDAIX/CXACAIX provides card detail links.
3. **Pseudo-conversational design**: CDEMO-PGM-CONTEXT 0 (ENTER) = first time; 1 (REENTER) = returning with data. Commarea is extended to include WS-THIS-PROGCOMMAREA (CA-FROM-PROGRAM + CA-FROM-TRANID).
4. **PF3 returns to caller**: CDEMO-FROM-PROGRAM in the COMMAREA determines where PF3 returns. If blank, defaults to COMEN01C.
5. **Navigation literals**: All target program names and transaction IDs are stored as explicit literals (LIT-CCLISTPGM, LIT-CARDUPDATEPGM, etc.) for maintainability.
6. **Fresh-entry detection**: EIBCALEN=0 OR (calling program is COMEN01C AND NOT CDEMO-PGM-REENTER) both result in a clean initialization.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (CACTVWA) | Account ID entered by user |
| COMMAREA  | CDEMO-FROM-PROGRAM, CDEMO-FROM-TRANID, CDEMO-PGM-CONTEXT |
| ACCTDAT   | Account master record |
| CUSTDAT   | Customer master record |
| CARDAIX / CXACAIX | Card and cross-reference alternate index lookups |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (CACTVWA) | Account and customer details displayed; error/info messages |
| COMMAREA   | CDEMO-FROM-TRANID='CAVW', CDEMO-FROM-PROGRAM='COACTVWC' set for navigation |

---

## 11. Key Variables and Their Purpose

| Variable               | Purpose |
|------------------------|---------|
| WS-XREF-RID            | Composite key (card+cust+acct) for alternate index reads |
| WS-ACCOUNT-MASTER-READ-FLAG | '1' after successful ACCTDAT read; prevents redundant reads |
| WS-CUST-MASTER-READ-FLAG | '1' after successful CUSTDAT read |
| WS-RETURN-MSG          | 88-level value set to specific message based on condition; displayed on screen |
| WS-THIS-PROGCOMMAREA   | Extra commarea area (CA-FROM-PROGRAM + CA-FROM-TRANID) appended beyond CARDDEMO-COMMAREA |
| WS-COMMAREA            | 2000-byte buffer combining CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA for CICS RETURN |
