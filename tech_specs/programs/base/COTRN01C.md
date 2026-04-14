# Technical Specification: COTRN01C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COTRN01C                                             |
| Source File      | app/cbl/COTRN01C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CT01 (WS-TRANID, line 37)                            |
| Function         | Transaction detail view screen. Displays all fields of a single TRANSACT record selected from COTRN00C. The transaction ID can be entered directly on screen or pre-populated from CDEMO-CT01-TRN-SELECTED in the commarea. PF3 returns to the calling program (CDEMO-FROM-PROGRAM), PF4 clears the screen, PF5 returns to COTRN00C. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CT01 and COMMAREA)

Clear WS-MESSAGE; SET ERR-FLG-OFF

IF EIBCALEN = 0:
    PERFORM RETURN-TO-PREV-SCREEN (XCTL to COSGN00C)

ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER:
        SET CDEMO-PGM-REENTER TO TRUE
        IF CDEMO-CT01-TRN-SELECTED NOT = SPACES:
            MOVE CDEMO-CT01-TRN-SELECTED TO TRNIDINI (pre-populate field)
        MOVE LOW-VALUES TO COTRN1AO
        PERFORM SEND-TRNDET-SCREEN (initial display, no receive)
    ELSE:
        PERFORM RECEIVE-TRNDET-SCREEN
        EVALUATE EIBAID:
            WHEN DFHENTER:  PERFORM PROCESS-ENTER-KEY
            WHEN DFHPF3:    PERFORM RETURN-TO-PREV-SCREEN
            WHEN DFHPF4:    PERFORM CLEAR-CURRENT-SCREEN
            WHEN DFHPF5:    MOVE 'COTRN00C' TO CDEMO-TO-PROGRAM
                            PERFORM RETURN-TO-PREV-SCREEN
            WHEN OTHER:     Set ERR-FLG-ON; CCDA-MSG-INVALID-KEY; SEND-TRNDET-SCREEN

EXEC CICS RETURN TRANSID('CT01') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph               | Lines     | Description |
|-------------------------|-----------|-------------|
| MAIN-PARA               | 79–124    | Main entry: EIBCALEN check; first/reenter dispatch; AID evaluate; CICS RETURN |
| PROCESS-ENTER-KEY       | 129–180   | Validate TRNIDINI (non-blank, numeric); READ TRANSACT with UPDATE; populate screen fields; SEND-TRNDET-SCREEN |
| RETURN-TO-PREV-SCREEN   | 185–198   | Default CDEMO-TO-PROGRAM=CDEMO-FROM-PROGRAM; EXEC CICS XCTL |
| CLEAR-CURRENT-SCREEN    | 203–215   | MOVE LOW-VALUES to COTRN1AO; clear WS-MESSAGE; re-send screen with blank fields |
| SEND-TRNDET-SCREEN      | 220–234   | POPULATE-HEADER-INFO; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('COTRN1A') MAPSET('COTRN01') FROM(COTRN1AO) ERASE |
| RECEIVE-TRNDET-SCREEN   | 239–249   | CICS RECEIVE MAP('COTRN1A') MAPSET('COTRN01') INTO(COTRN1AI) RESP RESP2 |
| POPULATE-HEADER-INFO    | 254–274   | Fill header fields from literals and FUNCTION CURRENT-DATE |
| POPULATE-TRAN-FIELDS    | 279–331   | Map TRAN-RECORD fields to COTRN1AO output fields for display |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 50) | CARDDEMO-COMMAREA: standard commarea; extended inline with CDEMO-CT01-INFO |
| COTRN01  | WORKING-STORAGE (line 52)  | BMS mapset copybook: COTRN1AI (input map), COTRN1AO (output map); contains TRNIDINI, TRNIDO, TRNTPO, TRNAMO, TRNORIGO, TRNPROCO, TRNMRCHO, TRNMRCO, TRNMRCCDO, TRNMRCCTYO, TRNMRCZIPO, TRNDESCO, TRNCARDO, ERRMSGO, header fields |
| COTRN02Y  | WORKING-STORAGE (line 54)  | TRAN-RECORD layout (same as COTRN00C): all transaction fields |
| COTTL01Y  | WORKING-STORAGE (line 56) | Screen title constants |
| CSDAT01Y  | WORKING-STORAGE (line 57) | Current date/time |
| CSMSG01Y  | WORKING-STORAGE (line 58) | Common messages |
| CSUSR01Y  | WORKING-STORAGE (line 59) | Signed-on user data |
| DFHAID    | WORKING-STORAGE (line 61) | EIBAID constants: DFHENTER, DFHPF3, DFHPF4, DFHPF5 |
| DFHBMSCA  | WORKING-STORAGE (line 62) | BMS attribute bytes |

### COMMAREA Extension (inline after COPY COCOM01Y)

| Field              | PIC       | Purpose |
|--------------------|-----------|---------|
| CDEMO-CT01-INFO    | Group     | CT01-specific commarea fields |
| CDEMO-CT01-TRNID-FIRST | X(16) | (Informational; not actively used in CT01) |
| CDEMO-CT01-TRNID-LAST  | X(16) | (Informational) |
| CDEMO-CT01-PAGE-NUM    | 9(08)  | Page number context from CT00 (carried through) |
| CDEMO-CT01-NEXT-PAGE-FLG | X(01) | Carried from CT00 |
| CDEMO-CT01-TRN-SEL-FLG | X(01)  | Carried from CT00 |
| CDEMO-CT01-TRN-SELECTED | X(16) | Transaction ID to display on first entry; pre-populates TRNIDINI |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| WS-PGMNAME           | X(08) = 'COTRN01C' | Program name for header |
| WS-TRANID            | X(04) = 'CT01' | Transaction ID |
| WS-MESSAGE           | X(80)     | User-visible message |
| WS-ERR-FLG           | X(01)     | Error flag |
| WS-TRAN-ID-NUM       | 9(16)     | Numeric validation field for TRNIDINI |
| WS-TRANSACT-FILE     | X(08) = 'TRANSACT' | CICS file name |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS RETURN TRANSID('CT01') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA | Pseudo-conversational return |
| EXEC CICS READ FILE('TRANSACT') INTO(TRAN-RECORD) RIDFLD(WS-TRAN-ID) UPDATE RESP RESP2 | PROCESS-ENTER-KEY | Read transaction record with UPDATE intent |
| EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA | RETURN-TO-PREV-SCREEN | Return to CT00 or prior caller |
| EXEC CICS SEND MAP('COTRN1A') MAPSET('COTRN01') FROM(COTRN1AO) ERASE | SEND-TRNDET-SCREEN | Display transaction detail |
| EXEC CICS RECEIVE MAP('COTRN1A') MAPSET('COTRN01') INTO(COTRN1AI) RESP RESP2 | RECEIVE-TRNDET-SCREEN | Receive transaction ID input |

---

## 5. File/Dataset Access

| File Name | CICS File  | Access Type | Key           | Purpose |
|-----------|------------|-------------|---------------|---------|
| TRANSACT  | TRANSACT   | READ UPDATE | WS-TRAN-ID X(16) | Read transaction record for display |

**Critical observation — READ UPDATE for display-only**: COTRN01C issues `EXEC CICS READ FILE('TRANSACT') ... UPDATE` to retrieve a transaction for display. This acquires an exclusive record lock that is held until the task ends (at CICS RETURN). Since COTRN01C never issues REWRITE or DELETE, the lock is released implicitly at task end. However, concurrent attempts to update the same transaction record (from another task) will be blocked while this display task holds the lock. This is a potential concurrency issue; a plain READ (without UPDATE) would be sufficient for this display-only use case.

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COTRN01    | COTRN1A | CT01        |

**Key Screen Fields:**

| Field      | Direction | Description |
|------------|-----------|-------------|
| TRNIDINI   | Input     | Transaction ID to look up (pre-populated from CDEMO-CT01-TRN-SELECTED on first entry) |
| TRNIDO     | Output    | Transaction ID |
| TRNTPO     | Output    | Transaction type code |
| TRNAMO     | Output    | Transaction amount |
| TRNORIGO   | Output    | Transaction origin date/timestamp |
| TRNPROCO   | Output    | Transaction process date/timestamp |
| TRNMRCHO   | Output    | Merchant ID |
| TRNMRCO    | Output    | Merchant name |
| TRNMRCCDO  | Output    | Merchant city |
| TRNMRCCTY0 | Output    | Merchant state/country |
| TRNMRCZIPO | Output    | Merchant ZIP |
| TRNDESCO   | Output    | Transaction description |
| TRNCARDO   | Output    | Card number |
| ERRMSGO    | Output    | WS-MESSAGE: error or status message |
| TITLE01O–CURTIMEO | Output | Standard header fields |

**Navigation:**
- ENTER: look up transaction by TRNIDINI
- PF3: return to CDEMO-FROM-PROGRAM (typically COMEN01C or COADM01C)
- PF4: clear screen fields, re-send blank map
- PF5: XCTL to COTRN00C (transaction list)
- Other keys: CCDA-MSG-INVALID-KEY

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| CDEMO-FROM-PROGRAM | CICS XCTL | PF3 pressed or EIBCALEN=0 |
| COTRN00C   | CICS XCTL   | PF5 pressed |

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | XCTL to COSGN00C (default CDEMO-TO-PROGRAM when FROM-PROGRAM is blank) |
| TRNIDINI blank | ERR-FLG-ON; 'Please enter a transaction ID'; re-send map |
| TRNIDINI not numeric | ERR-FLG-ON; error message; re-send map |
| READ RESP = NOTFND (13) | 'Transaction not found' message; re-send map |
| READ RESP = other | Generic error with RESP/RESP2 codes; re-send map |
| Invalid AID key | ERR-FLG-ON; CCDA-MSG-INVALID-KEY; re-send map |

---

## 9. Business Rules

1. **Pre-population from CT00**: When arriving from COTRN00C with a selected transaction, CDEMO-CT01-TRN-SELECTED is moved to TRNIDINI on first entry. This causes the transaction to be displayed immediately without requiring the user to re-enter the ID.
2. **Display-only function**: COTRN01C displays transaction data. No updates, deletes, or inserts are performed. The READ UPDATE lock is a defect (see File/Dataset Access note).
3. **PF5 back to list**: PF5 navigates back to COTRN00C, allowing the user to return to the list without entering the CT00 transaction fresh. The COMMAREA carried by XCTL includes pagination state from CT00.
4. **PF4 clear**: PF4 blanks the screen so the user can enter a different transaction ID.
5. **Transaction ID validation**: TRNIDINI must be 1–16 numeric digits. The program converts to WS-TRAN-ID-NUM for numeric validation before use as RIDFLD.

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COTRN1A) | TRNIDINI — transaction ID to look up |
| COMMAREA  | CDEMO-CT01-TRN-SELECTED (pre-selected ID from COTRN00C) |
| TRANSACT VSAM file | Full TRAN-RECORD for the specified transaction ID |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COTRN1A) | All transaction fields displayed: ID, type, amount, dates, merchant info, card number, description |
| COMMAREA   | CDEMO-FROM-PROGRAM='COTRN01C', CDEMO-FROM-TRANID='CT01' |

---

## 11. Key Variables and Their Purpose

| Variable                  | Purpose |
|---------------------------|---------|
| TRNIDINI                  | Transaction ID entered or pre-populated; used as RIDFLD for TRANSACT READ |
| CDEMO-CT01-TRN-SELECTED   | Transaction ID passed from COTRN00C; pre-populates screen on first entry |
| WS-TRAN-ID-NUM            | Numeric version of TRNIDINI; used for validation |
| TRAN-RECORD               | Full transaction record read from TRANSACT; fields mapped to screen output fields |
