# Technical Specification: COTRN01C — Transaction View (Detail) Program

## 1. Executive Summary

COTRN01C is an online CICS COBOL program in the CardDemo application that displays the complete detail of a single transaction record from the TRANSACT VSAM file. The operator can enter a Transaction ID directly into the screen, or arrive from COTRN00C with a pre-selected ID. The program reads the record with `READ UPDATE` (acquiring an exclusive lock) and populates all transaction fields in read-only display format. Navigation returns to COTRN00C (F5), the previous program (F3), or the main menu (COMEN01C default).

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COTRN01C.CBL | CICS COBOL program | app/cbl/COTRN01C.cbl |
| COTRN01.BMS | BMS mapset | app/bms/COTRN01.bms |
| COTRN01.CPY | BMS-generated copybook | app/cpy-bms/COTRN01.CPY |
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
| Program name | COTRN01C |
| CICS Transaction ID | CT01 |
| Source file | COTRN01C.CBL |
| Version stamp | CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19 |
| BMS Mapset | COTRN01 |
| BMS Map | COTRN1A |

---

## 4. CICS Commands Used

| Command | Purpose | Paragraph |
|---|---|---|
| `EXEC CICS RETURN TRANSID(CT01) COMMAREA(CARDDEMO-COMMAREA)` | Pseudo-conversational return | MAIN-PARA (line 136) |
| `EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)` | Transfer to previous program or target | RETURN-TO-PREV-SCREEN (line 205) |
| `EXEC CICS SEND MAP('COTRN1A') MAPSET('COTRN01') FROM(COTRN1AO) ERASE CURSOR` | Send detail screen | SEND-TRNVIEW-SCREEN (line 219) |
| `EXEC CICS RECEIVE MAP('COTRN1A') MAPSET('COTRN01') INTO(COTRN1AI)` | Receive operator input | RECEIVE-TRNVIEW-SCREEN (line 232) |
| `EXEC CICS READ DATASET('TRANSACT') INTO(TRAN-RECORD) RIDFLD(TRAN-ID) UPDATE` | Read transaction record with exclusive lock | READ-TRANSACT-FILE (line 269) |

---

## 5. Copybooks Referenced

### COCOM01Y.CPY — CARDDEMO-COMMAREA
The global COMMAREA. See COTRN00C_spec.md Section 5 for full field listing.

Additional program-local COMMAREA extension defined immediately after COPY COCOM01Y (lines 53–61):

```
05 CDEMO-CT01-INFO.
   10 CDEMO-CT01-TRNID-FIRST     PIC X(16)   -- not used for view functionality
   10 CDEMO-CT01-TRNID-LAST      PIC X(16)   -- not used for view functionality
   10 CDEMO-CT01-PAGE-NUM        PIC 9(08)   -- not actively used
   10 CDEMO-CT01-NEXT-PAGE-FLG   PIC X(01)   -- 'Y'=next page exists
   10 CDEMO-CT01-TRN-SEL-FLG     PIC X(01)   -- selection flag from list screen
   10 CDEMO-CT01-TRN-SELECTED    PIC X(16)   -- transaction ID passed from COTRN00C
```

Note: The field name prefix `CDEMO-CT01-` mirrors the COTRN00C convention with `CDEMO-CT00-`. When COTRN00C XCTLs to COTRN01C, the values written into the `CDEMO-CT00-` fields of the COMMAREA are read as `CDEMO-CT01-` fields here because the COMMAREA is a flat structure with positional mapping.

### CVTRA05Y.CPY — TRAN-RECORD (350 bytes)
Full transaction record layout. Source: app/cpy/CVTRA05Y.cpy.

| Field | PIC | Description |
|---|---|---|
| TRAN-ID | X(16) | Transaction identifier (key) |
| TRAN-TYPE-CD | X(02) | Transaction type code |
| TRAN-CAT-CD | 9(04) | Category code |
| TRAN-SOURCE | X(10) | Source |
| TRAN-DESC | X(100) | Description |
| TRAN-AMT | S9(09)V99 | Signed amount |
| TRAN-MERCHANT-ID | 9(09) | Merchant ID |
| TRAN-MERCHANT-NAME | X(50) | Merchant name |
| TRAN-MERCHANT-CITY | X(50) | Merchant city |
| TRAN-MERCHANT-ZIP | X(10) | Merchant ZIP |
| TRAN-CARD-NUM | X(16) | Card number |
| TRAN-ORIG-TS | X(26) | Origination timestamp |
| TRAN-PROC-TS | X(26) | Processing timestamp |
| FILLER | X(20) | Reserved |

### COTRN01.CPY — BMS-Generated Map Symbolic Description
Generated from COTRN01.BMS. Defines:
- `COTRN1AI` — input symbolic map
- `COTRN1AO` — output symbolic map (REDEFINES COTRN1AI)

Key map fields (source: app/cpy-bms/COTRN01.CPY):

| Symbolic Name | PIC | Direction | Purpose |
|---|---|---|---|
| TRNIDINI / TRNIDINO | X(16) | In/Out | Transaction ID entered by user |
| TRNIDINL | S9(4) COMP | In | Cursor position control |
| TRNIDI / TRNIDO | X(16) | Out | Transaction ID display field |
| CARDNUMI / CARDNUMO | X(16) | Out | Card number display |
| TTYPCDI / TTYPCDO | X(2) | Out | Type code display |
| TCATCDI / TCATCDO | X(4) | Out | Category code display |
| TRNSRCI / TRNSRCO | X(10) | Out | Source display |
| TDESCI / TDESCO | X(60) | Out | Description display |
| TRNAMTI / TRNAMTO | X(12) | Out | Amount display |
| TORIGDTI / TORIGDTO | X(10) | Out | Original date display |
| TPROCDTI / TPROCDTO | X(10) | Out | Processing date display |
| MIDI / MIDO | X(9) | Out | Merchant ID display |
| MNAMEI / MNAMEO | X(30) | Out | Merchant name display |
| MCITYI / MCITYO | X(25) | Out | Merchant city display |
| MZIPI / MZIPO | X(10) | Out | Merchant ZIP display |
| ERRMSGI / ERRMSGO | X(78) | Out | Error/status message |
| TRNNAMEO | X(4) | Out | Transaction name (CT01) |
| PGMNAMEO | X(8) | Out | Program name |
| CURDATEO | X(8) | Out | Current date |
| CURTIMEO | X(8) | Out | Current time |
| TITLE01O / TITLE02O | X(40) each | Out | Application title |

### COTTL01Y.CPY, CSDAT01Y.CPY, CSMSG01Y.CPY
See COTRN00C_spec.md Section 5 for descriptions. Same usage pattern.

---

## 6. Working Storage Variables

| Field | PIC | Value | Purpose |
|---|---|---|---|
| WS-PGMNAME | X(08) | 'COTRN01C' | Program name |
| WS-TRANID | X(04) | 'CT01' | Transaction ID |
| WS-MESSAGE | X(80) | SPACES | Message buffer |
| WS-TRANSACT-FILE | X(08) | 'TRANSACT' | VSAM dataset name |
| WS-ERR-FLG | X(01) | 'N' | Error flag |
| WS-RESP-CD | S9(09) COMP | 0 | CICS RESP |
| WS-REAS-CD | S9(09) COMP | 0 | CICS RESP2 |
| WS-USR-MODIFIED | X(01) | 'N' | User modified flag (declared but not used in this program) |
| WS-TRAN-AMT | PIC +99999999.99 | — | Formatted display amount |
| WS-TRAN-DATE | X(08) | '00/00/00' | Formatted date (not used in display here) |

---

## 7. Program Flow — Paragraph-by-Paragraph

### MAIN-PARA (entry point, line 85)

```
Set ERR-FLG-OFF, USR-MODIFIED-NO
Clear WS-MESSAGE and ERRMSGO

IF EIBCALEN = 0
    CDEMO-TO-PROGRAM = 'COSGN00C'
    PERFORM RETURN-TO-PREV-SCREEN
ELSE
    Move DFHCOMMAREA into CARDDEMO-COMMAREA
    IF NOT CDEMO-PGM-REENTER (first entry)
        Set CDEMO-PGM-REENTER = 1
        Move LOW-VALUES to COTRN1AO
        Move -1 to TRNIDINL
        IF CDEMO-CT01-TRN-SELECTED not spaces/low-values
            Move CDEMO-CT01-TRN-SELECTED to TRNIDINI  (pre-load from list screen)
            PERFORM PROCESS-ENTER-KEY
        END-IF
        PERFORM SEND-TRNVIEW-SCREEN
    ELSE (re-entry)
        PERFORM RECEIVE-TRNVIEW-SCREEN
        EVALUATE EIBAID
            DFHENTER → PERFORM PROCESS-ENTER-KEY
            DFHPF3   → CDEMO-TO-PROGRAM = CDEMO-FROM-PROGRAM (or 'COMEN01C')
                       PERFORM RETURN-TO-PREV-SCREEN
            DFHPF4   → PERFORM CLEAR-CURRENT-SCREEN
            DFHPF5   → CDEMO-TO-PROGRAM = 'COTRN00C'
                       PERFORM RETURN-TO-PREV-SCREEN
            OTHER    → set ERR-FLG, message CCDA-MSG-INVALID-KEY
                       PERFORM SEND-TRNVIEW-SCREEN
        END-EVALUATE
    END-IF
END-IF

EXEC CICS RETURN TRANSID(CT01) COMMAREA(CARDDEMO-COMMAREA)
```

### PROCESS-ENTER-KEY (line 144)

1. Validates TRNIDINI: if blank, sets error "Tran ID can NOT be empty..." and sends screen with cursor on TRNIDINL.
2. If valid, clears all display fields (TRNIDI, CARDNUMI, TTYPCDI, TCATCDI, TRNSRCI, TRNAMTI, TDESCI, TORIGDTI, TPROCDTI, MIDI, MNAMEI, MCITYI, MZIPI) to SPACES.
3. Moves TRNIDINI to TRAN-ID and calls READ-TRANSACT-FILE.
4. If no error, populates all display fields from TRAN-RECORD:
   - TRAN-AMT → WS-TRAN-AMT (formatted `PIC +99999999.99`) → TRNAMTI
   - TRAN-ID → TRNIDI
   - TRAN-CARD-NUM → CARDNUMI
   - TRAN-TYPE-CD → TTYPCDI
   - TRAN-CAT-CD → TCATCDI
   - TRAN-SOURCE → TRNSRCI
   - TRAN-DESC → TDESCI
   - TRAN-ORIG-TS → TORIGDTI
   - TRAN-PROC-TS → TPROCDTI
   - TRAN-MERCHANT-ID → MIDI
   - TRAN-MERCHANT-NAME → MNAMEI
   - TRAN-MERCHANT-CITY → MCITYI
   - TRAN-MERCHANT-ZIP → MZIPI
5. Calls SEND-TRNVIEW-SCREEN.

### RETURN-TO-PREV-SCREEN (line 197)

Sets CDEMO-FROM-TRANID = 'CT01', CDEMO-FROM-PROGRAM = 'COTRN01C', CDEMO-PGM-CONTEXT = 0, then XCTLs to CDEMO-TO-PROGRAM. Default fallback is 'COSGN00C'.

### SEND-TRNVIEW-SCREEN (line 213)

Calls POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO, and issues `EXEC CICS SEND MAP ERASE CURSOR`. Always sends with ERASE (no conditional erase in this program unlike COTRN00C).

### RECEIVE-TRNVIEW-SCREEN (line 230)

`EXEC CICS RECEIVE MAP('COTRN1A') MAPSET('COTRN01') INTO(COTRN1AI)` with RESP/RESP2.

### POPULATE-HEADER-INFO (line 243)

Identical pattern to COTRN00C. Formats current date/time into screen header fields.

### READ-TRANSACT-FILE (line 267)

```
EXEC CICS READ
    DATASET('TRANSACT')
    INTO(TRAN-RECORD)
    LENGTH(LENGTH OF TRAN-RECORD)
    RIDFLD(TRAN-ID)
    KEYLENGTH(16)
    UPDATE
    RESP(WS-RESP-CD) RESP2(WS-REAS-CD)
```

- DFHRESP(NORMAL): continue (record populated in TRAN-RECORD).
- DFHRESP(NOTFND): sets ERR-FLG-ON, message "Transaction ID NOT found...", cursor on TRNIDINL, sends screen.
- OTHER: DISPLAY resp codes to SYSOUT, sets ERR-FLG-ON, message "Unable to lookup Transaction...", sends screen.

**Important design note:** The READ uses the UPDATE option, acquiring an exclusive VSAM lock on the record. However, COTRN01C never issues a REWRITE or UNLOCK. The lock is released only when the CICS task ends (at EXEC CICS RETURN). This means that while the operator views the detail, the record is held locked — a design characteristic to flag for modernization.

### CLEAR-CURRENT-SCREEN (line 301)

Calls INITIALIZE-ALL-FIELDS then SEND-TRNVIEW-SCREEN.

### INITIALIZE-ALL-FIELDS (line 309)

Moves SPACES to: TRNIDINI, TRNIDI, CARDNUMI, TTYPCDI, TCATCDI, TRNSRCI, TRNAMTI, TDESCI, TORIGDTI, TPROCDTI, MIDI, MNAMEI, MCITYI, MZIPI, WS-MESSAGE. Sets TRNIDINL = -1.

---

## 8. Inter-Program Interactions

| Interaction | Target | Mechanism | Condition |
|---|---|---|---|
| Called by | COTRN00C | XCTL (inbound, CT00→CT01) | User types 'S' on list screen |
| Called by | COMEN01C | XCTL (direct navigation) | Admin/user navigates directly |
| Transfer to | CDEMO-FROM-PROGRAM (COTRN00C) | XCTL | F3 pressed; returns to calling program |
| Transfer to | COMEN01C | XCTL | F3 when CDEMO-FROM-PROGRAM is empty |
| Transfer to | COTRN00C | XCTL | F5 Browse Tran |
| Transfer to | COSGN00C | XCTL | EIBCALEN=0 or CDEMO-TO-PROGRAM empty |

COMMAREA fields read on entry (set by COTRN00C):
- `CDEMO-CT01-TRN-SELECTED` (= CDEMO-CT00-TRN-SELECTED): 16-character transaction ID
- `CDEMO-FROM-PROGRAM`: used by F3 to return to caller

---

## 9. Files Accessed

| CICS Dataset Name | Access Mode | Operations | Record Structure |
|---|---|---|---|
| TRANSACT | Random read with UPDATE | READ UPDATE | TRAN-RECORD (CVTRA05Y.CPY), 350 bytes, KSDS key=TRAN-ID X(16) |

---

## 10. Error Handling

| Condition | ERR-FLG | Message | Action |
|---|---|---|---|
| EIBCALEN = 0 | — | — | XCTL to COSGN00C |
| TRNIDINI blank | Y | "Tran ID can NOT be empty..." | Re-send, cursor on TRNIDIN |
| READ NOTFND | Y | "Transaction ID NOT found..." | Re-send, cursor on TRNIDIN |
| READ OTHER | Y | "Unable to lookup Transaction..." | DISPLAY resp, re-send |
| Invalid AID key | Y | CCDA-MSG-INVALID-KEY | Re-send screen |

---

## 11. Transaction Flow Context

```
COTRN00C [CT00]
    -- XCTL with CDEMO-CT01-TRN-SELECTED -->
        COTRN01C [CT01]   <-- this program
            READ UPDATE TRANSACT (by TRAN-ID)
            Display all transaction fields (read-only)
            F3 --> XCTL back to COTRN00C (or COMEN01C)
            F4 --> Clear screen
            F5 --> XCTL to COTRN00C (browse list)
```

---

## 12. Design Notes for Modernization

1. **READ UPDATE without REWRITE**: The transaction record is locked for the entire operator interaction. In a high-volume environment this could cause contention. The modern equivalent should use an optimistic locking pattern or READ without UPDATE for display-only screens.
2. **Dual-use of COMMAREA fields**: `CDEMO-CT01-TRN-SELECTED` at the physical COMMAREA position corresponds to `CDEMO-CT00-TRN-SELECTED` in the COTRN00C layout. The programs share the same COMMAREA structure but interpret fields using their own COPY statements. This is a common CardDemo pattern and requires careful positional alignment during migration.
3. **WS-USR-MODIFIED** is declared (line 46) but never set to 'Y' — it appears to be scaffolding for a future update capability in this view screen.
4. **Amount display**: TRAN-AMT (S9(09)V99 packed) is moved to WS-TRAN-AMT (PIC +99999999.99 edited) to produce signed display with decimal point and sign prefix.

---

## 13. Open Questions and Gaps

- The `CDEMO-CT01-TRNID-FIRST`, `CDEMO-CT01-TRNID-LAST`, and `CDEMO-CT01-PAGE-NUM` fields in the COMMAREA extension are declared but never written by COTRN01C. They are vestigial from the copy of the CT00 pattern.
- The `READ UPDATE` lock behavior under CICS pseudo-conversational design: the lock is released at RETURN, not at screen read. This is confirmed but the intended behavior (whether it was meant to be a read-with-intent-to-update for COTRN02C) is unclear from this source alone.
