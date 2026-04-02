# Technical Specification: COACTUPC.CBL

## 1. Executive Summary

COACTUPC is a CICS online COBOL program that implements the Account Update function of the CardDemo application. It operates as a multi-pass, pseudo-conversational transaction (transaction ID: CAUP) that allows an operator to look up an account by account number, review and edit both account master and associated customer master data on a single screen (map CACTUPA in mapset COACTUP), validate all changes through an extensive set of field-level and cross-field edits, present a confirmation step, and commit the updates atomically to two VSAM KSDS files (ACCTDAT and CUSTDAT). The program is entirely read-only on the first pass; it only issues CICS REWRITE commands after the operator explicitly presses F5 to confirm validated changes.

---

## 2. Artifact Inventory

| Artifact | Type | Location |
|---|---|---|
| COACTUPC.CBL | CICS COBOL Program | `app/cbl/COACTUPC.cbl` |
| COACTUP.BMS | BMS Mapset | `app/bms/COACTUP.bms` |
| COACTUP (copybook) | BMS-generated copybook | Resolved via COPY COACTUP at line 623 |
| CVACT01Y.CPY | Account record layout | `app/cpy/CVACT01Y.cpy` |
| CVACT03Y.CPY | Card xref record layout | `app/cpy/CVACT03Y.cpy` |
| CVCUS01Y.CPY | Customer record layout | `app/cpy/CVCUS01Y.cpy` |
| CVCRD01Y.CPY | Card working storage | `app/cpy/CVCRD01Y.cpy` |
| COCOM01Y.CPY | Application COMMAREA | `app/cpy/COCOM01Y.cpy` |
| COTTL01Y.CPY | Screen titles | `app/cpy/COTTL01Y.cpy` |
| CSDAT01Y.CPY | Current date variables | `app/cpy/CSDAT01Y.cpy` |
| CSMSG01Y.CPY | Common messages | `app/cpy/CSMSG01Y.cpy` |
| CSMSG02Y.CPY | Abend variables | `app/cpy/CSMSG02Y.cpy` |
| CSUSR01Y.CPY | Signed-on user data | `app/cpy/CSUSR01Y.cpy` |
| CSSETATY.CPY | Screen attribute setter macro | `app/cpy/CSSETATY.cpy` |
| CSUTLDWY.CPY | Generic date edit variables | `app/cpy/CSUTLDWY.cpy` |
| CSUTLDPY.CPY | Common date routines | `app/cpy/CSUTLDPY.cpy` |
| CSLKPCDY.CPY | Phone area code lookup table | `app/cpy/CSLKPCDY.cpy` |
| CSSTRPFY.CPY | PF key store routine | `app/cpy/CSSTRPFY.cpy` |
| DFHBMSCA | IBM BMS attribute constants | System copybook |
| DFHAID | IBM AID key definitions | System copybook |

---

## 3. Program Identity

| Property | Value | Source |
|---|---|---|
| Program ID | COACTUPC | Line 23 |
| Transaction ID | CAUP | Line 536, `LIT-THISTRANID` |
| Mapset | COACTUP | Line 538, `LIT-THISMAPSET` |
| Map | CACTUPA | Line 540, `LIT-THISMAP` |
| Layer | Business logic | Line 3 |
| Function | Accept and process ACCOUNT UPDATE | Line 4 |
| Date written | July 2022 | Line 25 |

---

## 4. COMMAREA Structure

COACTUPC uses a composite COMMAREA that combines two copybooks laid end-to-end. The total working area `WS-COMMAREA` is declared as PIC X(2000) at line 850.

### 4.1 Segment 1: CARDDEMO-COMMAREA (from COCOM01Y.CPY)

| Field | PIC | Purpose |
|---|---|---|
| CDEMO-FROM-TRANID | X(04) | Calling transaction ID |
| CDEMO-FROM-PROGRAM | X(08) | Calling program name |
| CDEMO-TO-TRANID | X(04) | Target transaction ID for XCTL |
| CDEMO-TO-PROGRAM | X(08) | Target program name for XCTL |
| CDEMO-USER-ID | X(08) | Signed-on user identifier |
| CDEMO-USER-TYPE | X(01) | 'A'=Admin, 'U'=User |
| CDEMO-PGM-CONTEXT | 9(01) | 0=First entry, 1=Re-entry |
| CDEMO-CUST-ID | 9(09) | Customer ID in context |
| CDEMO-CUST-FNAME/MNAME/LNAME | X(25) each | Customer name in context |
| CDEMO-ACCT-ID | 9(11) | Account ID in context |
| CDEMO-ACCT-STATUS | X(01) | Account status in context |
| CDEMO-CARD-NUM | 9(16) | Card number in context |
| CDEMO-LAST-MAP | X(07) | Last map displayed |
| CDEMO-LAST-MAPSET | X(07) | Last mapset used |

### 4.2 Segment 2: WS-THIS-PROGCOMMAREA (lines 652-849)

This private commarea carries the program state across pseudo-conversational returns.

| Field | PIC | Values / Meaning |
|---|---|---|
| ACUP-CHANGE-ACTION | X(1) | State machine flag (see below) |
| ACUP-OLD-DETAILS | Group | Snapshot of data as fetched from files |
| ACUP-OLD-ACCT-DATA | Group | Account fields at fetch time |
| ACUP-OLD-CUST-DATA | Group | Customer fields at fetch time |
| ACUP-NEW-DETAILS | Group | Data as entered by operator this pass |
| ACUP-NEW-ACCT-DATA | Group | New account field values |
| ACUP-NEW-CUST-DATA | Group | New customer field values |

**ACUP-CHANGE-ACTION 88-level state codes (lines 656-668):**

| 88-Level Name | Value | Meaning |
|---|---|---|
| ACUP-DETAILS-NOT-FETCHED | LOW-VALUES / SPACES | Initial state; no data retrieved yet |
| ACUP-SHOW-DETAILS | 'S' | Data fetched; showing for edit |
| ACUP-CHANGES-NOT-OK | 'E' | Changes entered but validation failed |
| ACUP-CHANGES-OK-NOT-CONFIRMED | 'N' | Changes validated; awaiting F5 |
| ACUP-CHANGES-OKAYED-AND-DONE | 'C' | Changes saved successfully |
| ACUP-CHANGES-OKAYED-LOCK-ERROR | 'L' | Save attempted; record lock failed |
| ACUP-CHANGES-OKAYED-BUT-FAILED | 'F' | Save attempted; REWRITE failed |

---

## 5. Program Flow (PROCEDURE DIVISION)

### 5.1 Entry Point: 0000-MAIN (lines 859-1023)

```
0000-MAIN
  |
  +-- EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE)
  |
  +-- INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA
  |
  +-- If EIBCALEN = 0 OR (from menu AND NOT re-enter):
  |     INITIALIZE CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA
  |     SET CDEMO-PGM-ENTER, ACUP-DETAILS-NOT-FETCHED
  |   Else:
  |     MOVE DFHCOMMAREA -> CARDDEMO-COMMAREA
  |     MOVE DFHCOMMAREA(offset) -> WS-THIS-PROGCOMMAREA
  |
  +-- PERFORM YYYY-STORE-PFKEY
  |
  +-- Validate AID key (ENTER, PFK03, PFK05 if confirmed, PFK12 if data shown)
  |   If invalid AID: SET CCARD-AID-ENTER
  |
  +-- EVALUATE TRUE
        WHEN CCARD-AID-PFK03  -> exit via XCTL (with SYNCPOINT first)
        WHEN ACUP-DETAILS-NOT-FETCHED AND CDEMO-PGM-ENTER
        WHEN from menu AND not re-enter -> PERFORM 3000-SEND-MAP, RETURN
        WHEN ACUP-CHANGES-OKAYED-AND-DONE
        WHEN ACUP-CHANGES-FAILED -> reinitialize, PERFORM 3000-SEND-MAP, RETURN
        WHEN OTHER -> PERFORM 1000-PROCESS-INPUTS
                      PERFORM 2000-DECIDE-ACTION
                      PERFORM 3000-SEND-MAP
                      GO TO COMMON-RETURN
```

### 5.2 COMMON-RETURN (lines 1007-1019)

Assembles the composite COMMAREA and issues:
```
EXEC CICS RETURN
     TRANSID(CAUP)
     COMMAREA(WS-COMMAREA)
     LENGTH(LENGTH OF WS-COMMAREA)
```

### 5.3 PF03 Exit Logic (lines 927-959)

When F3 is pressed, the program:
1. Sets `CDEMO-TO-TRANID`/`CDEMO-TO-PROGRAM` to the caller's values (from COMMAREA), defaulting to menu (COMEN01C / CM00)
2. Issues `EXEC CICS SYNCPOINT` (line 953) before transfer
3. Issues `EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)`

---

## 6. Paragraph-by-Paragraph Logic

### 6.1 1000-PROCESS-INPUTS (lines 1025-1038)

Orchestrates input processing:
1. PERFORM 1100-RECEIVE-MAP
2. PERFORM 1200-EDIT-MAP-INPUTS

### 6.2 1100-RECEIVE-MAP (lines 1039-1426)

Issues `EXEC CICS RECEIVE MAP(CACTUPA) MAPSET(COACTUP) INTO(CACTUPAI)`.

Then extracts every field from the map's input area (CACTUPAI) into `ACUP-NEW-*` fields. Fields containing '*' or SPACES are treated as blank (set to LOW-VALUES). Key mappings:

- ACCTSIDI -> CC-ACCT-ID and ACUP-NEW-ACCT-ID-X (line 1051-1058)
- ACSTTUSI -> ACUP-NEW-ACTIVE-STATUS (line 1065-1070)
- ACRDLIMI -> ACUP-NEW-CREDIT-LIMIT-X, converted to packed via NUMVAL-C (lines 1073-1084)
- ACSHLIMI -> ACUP-NEW-CASH-CREDIT-LIMIT-X (lines 1087-1098)
- ACURBALI -> ACUP-NEW-CURR-BAL-X (lines 1101-1112)
- ACRCYCRI -> ACUP-NEW-CURR-CYC-CREDIT-X (lines 1115-1126)
- ACRCYDBI -> ACUP-NEW-CURR-CYC-DEBIT-X (lines 1129-1140)
- OPNYEARI/OPNMONI/OPNDAYI -> ACUP-NEW-OPEN-YEAR/MON/DAY (lines 1144-1163)
- EXPYEARI/EXPMONI/EXPDAYI -> ACUP-NEW-EXP-YEAR/MON/DAY (lines 1166-1186)
- RISYEARI/RISMONI/RISDAYI -> ACUP-NEW-REISSUE-YEAR/MON/DAY (lines 1190-1209)
- AADDGRPI -> ACUP-NEW-GROUP-ID (lines 1213-1218)
- ACSTNUMI -> ACUP-NEW-CUST-ID-X (lines 1224-1229)
- ACTSSN1I/ACTSSN2I/ACTSSN3I -> ACUP-NEW-CUST-SSN-1/2/3 (lines 1233-1252)
- DOBYEARI/DOBMONI/DOBDAYI -> ACUP-NEW-CUST-DOB-YEAR/MON/DAY (lines 1256-1275)
- ACSTFCOI -> ACUP-NEW-CUST-FICO-SCORE-X (lines 1279-1284)
- ACSFNAMI/ACSMNAMI/ACSLNAMI -> first/middle/last names (lines 1288-1311)
- ACSADL1I/ACSADL2I/ACSCITYI -> address lines 1/2/city (lines 1315-1334)
- ACSSTTEI -> ACUP-NEW-CUST-ADDR-STATE-CD (lines 1336-1341)
- ACSCTRYI -> ACUP-NEW-CUST-ADDR-COUNTRY-CD (lines 1343-1348)
- ACSZIPCI -> ACUP-NEW-CUST-ADDR-ZIP (lines 1350-1355)
- ACSPH1AI/BI/CI -> phone 1 area/prefix/line (lines 1357-1376)
- ACSPH2AI/BI/CI -> phone 2 area/prefix/line (lines 1378-1397)
- ACSGOVTI -> ACUP-NEW-CUST-GOVT-ISSUED-ID (lines 1401-1406)
- ACSEFTCI -> ACUP-NEW-CUST-EFT-ACCOUNT-ID (lines 1410-1415)
- ACSPFLGI -> ACUP-NEW-CUST-PRI-HOLDER-IND (lines 1419-1424)

**Note:** If `ACUP-DETAILS-NOT-FETCHED` is true (line 1060), map receive exits early - only the account number field is extracted.

### 6.3 1200-EDIT-MAP-INPUTS (lines 1429-1680)

The main validation dispatcher. Two execution paths:

**Path A - Details not yet fetched (lines 1433-1446):**
Calls 1210-EDIT-ACCOUNT only. No further edits.

**Path B - Data already shown (lines 1447-1676):**
1. PERFORM 1205-COMPARE-OLD-NEW — detects if any field changed
2. If no changes or already confirmed/done: skip to exit
3. SET ACUP-CHANGES-NOT-OK
4. Validates all non-key fields sequentially (see Section 7 for business rules)
5. If all edits pass: SET ACUP-CHANGES-OK-NOT-CONFIRMED

### 6.4 1205-COMPARE-OLD-NEW (lines 1681-1779)

Performs a field-by-field comparison of all ACUP-NEW-* fields against ACUP-OLD-* fields using FUNCTION UPPER-CASE and FUNCTION TRIM for text fields, and direct numeric comparison for packed fields. If every field matches: SET NO-CHANGES-DETECTED. If any field differs: SET CHANGE-HAS-OCCURRED and exits immediately.

### 6.5 2000-DECIDE-ACTION (lines 2562-2645)

State machine dispatcher controlling what happens after validation:

| State / AID | Action |
|---|---|
| ACUP-DETAILS-NOT-FETCHED | Read account data (9000-READ-ACCT) |
| CCARD-AID-PFK12 (cancel) | If acct valid, re-read and show original data |
| ACUP-SHOW-DETAILS and INPUT-OK and changes exist | SET ACUP-CHANGES-OK-NOT-CONFIRMED |
| ACUP-CHANGES-NOT-OK | Continue (redisplay with errors) |
| ACUP-CHANGES-OK-NOT-CONFIRMED AND CCARD-AID-PFK05 | PERFORM 9600-WRITE-PROCESSING; set result state |
| ACUP-CHANGES-OK-NOT-CONFIRMED (Enter only) | Continue (show confirmation prompt) |
| ACUP-CHANGES-OKAYED-AND-DONE | SET ACUP-SHOW-DETAILS; reset IDs if no caller context |
| OTHER | PERFORM ABEND-ROUTINE |

### 6.6 3000-SEND-MAP (lines 2649-2665)

Orchestrates screen output in five steps:
1. 3100-SCREEN-INIT — clear CACTUPAO, move date/time/title/tranid/pgm
2. 3200-SETUP-SCREEN-VARS — populate all data fields based on current state
3. 3250-SETUP-INFOMSG — determine informational message for line 22
4. 3300-SETUP-SCREEN-ATTRS — protect/unprotect fields, set colors, position cursor
5. 3400-SEND-SCREEN — issue EXEC CICS SEND MAP ... ERASE FREEKB CURSOR

### 6.7 3200-SETUP-SCREEN-VARS (lines 2698-2726)

Selects display data based on state:
- ACUP-DETAILS-NOT-FETCHED or zero acct: call 3201-SHOW-INITIAL-VALUES (clears all fields)
- ACUP-SHOW-DETAILS: call 3202-SHOW-ORIGINAL-VALUES (shows ACUP-OLD-* fields)
- ACUP-CHANGES-MADE: call 3203-SHOW-UPDATED-VALUES (shows ACUP-NEW-* fields)

**3202-SHOW-ORIGINAL-VALUES (lines 2787-2864):** Maps ACUP-OLD-* fields to screen output. Numeric currency fields are formatted through `WS-EDIT-CURRENCY-9-2-F` (PIC +ZZZ,ZZZ,ZZZ.99). Dates are split into YEAR/MON/DAY parts. Phone number parts are extracted by byte offsets from the stored (999)999-9999 format.

**3203-SHOW-UPDATED-VALUES (lines 2870-2950):** Maps ACUP-NEW-* fields to screen output with same formatting logic.

### 6.8 3300-SETUP-SCREEN-ATTRS (lines 2986-3437)

Manages field protection and color:

**3310-PROTECT-ALL-ATTRS (lines 3441-3495):** Sets DFHBMPRF on all editable fields — the screen is fully protected by default.

**3320-UNPROTECT-FEW-ATTRS (lines 3500-3561):** When data is shown for editing, sets DFHBMFSE on all editable fields. Exceptions:
- ACSTNUMA (Customer ID): remains protected (DFHBMPRF at line 3531) — Customer ID is display-only
- ACSCTRYA (Country): protected (line 3547) — country edits are US-specific only

**Color / error highlighting (lines 3170-3436):** Uses the CSSETATY.CPY macro (via COPY REPLACING) to set field color to DFHRED and content to '*' for any field flagged as NOT-OK or BLANK, when CDEMO-PGM-REENTER is true.

**Cursor positioning (lines 3008-3167):** EVALUATE TRUE selects the first errored field in screen-top-to-bottom order and positions the cursor there (-1 to the length field).

### 6.9 9000-READ-ACCT (lines 3608-3648)

Orchestrates the three-step read sequence:
1. PERFORM 9200-GETCARDXREF-BYACCT
2. If not found: exit
3. PERFORM 9300-GETACCTDATA-BYACCT
4. If not found: exit
5. PERFORM 9400-GETCUSTDATA-BYCUST
6. If not found: exit
7. PERFORM 9500-STORE-FETCHED-DATA

### 6.10 9200-GETCARDXREF-BYACCT (lines 3650-3698)

```
EXEC CICS READ
     DATASET(CXACAIX)          -- alternate index path on CARDXREF
     RIDFLD(WS-CARD-RID-ACCT-ID-X)
     KEYLENGTH(11)
     INTO(CARD-XREF-RECORD)
```
On NORMAL: extracts XREF-CUST-ID -> CDEMO-CUST-ID, XREF-CARD-NUM -> CDEMO-CARD-NUM.
On NOTFND: sets INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, constructs error message.
On OTHER: sets INPUT-ERROR, formats WS-FILE-ERROR-MESSAGE.

### 6.11 9300-GETACCTDATA-BYACCT (lines 3701-3748)

```
EXEC CICS READ
     DATASET(ACCTDAT)
     RIDFLD(WS-CARD-RID-ACCT-ID-X)
     KEYLENGTH(11)
     INTO(ACCOUNT-RECORD)
```
On NORMAL: sets FOUND-ACCT-IN-MASTER.
On NOTFND / OTHER: sets INPUT-ERROR, FLG-ACCTFILTER-NOT-OK.

### 6.12 9400-GETCUSTDATA-BYCUST (lines 3752-3797)

```
EXEC CICS READ
     DATASET(CUSTDAT)
     RIDFLD(WS-CARD-RID-CUST-ID-X)
     KEYLENGTH(9)
     INTO(CUSTOMER-RECORD)
```
On NORMAL: sets FOUND-CUST-IN-MASTER.
On NOTFND / OTHER: sets INPUT-ERROR, FLG-CUSTFILTER-NOT-OK.

### 6.13 9500-STORE-FETCHED-DATA (lines 3801-3884)

Copies all fields from ACCOUNT-RECORD and CUSTOMER-RECORD into ACUP-OLD-* and also populates CARDDEMO-COMMAREA context fields (CDEMO-ACCT-ID, CDEMO-CUST-ID, CDEMO-CUST-FNAME/MNAME/LNAME, CDEMO-ACCT-STATUS, CDEMO-CARD-NUM).

Dates are split from the stored YYYY-MM-DD format into separate YEAR/MON/DAY components:
- `ACCT-OPEN-DATE(1:4)` -> ACUP-OLD-OPEN-YEAR (line 3832)
- `ACCT-OPEN-DATE(6:2)` -> ACUP-OLD-OPEN-MON (line 3833)
- `ACCT-OPEN-DATE(9:2)` -> ACUP-OLD-OPEN-DAY (line 3834)

### 6.14 9600-WRITE-PROCESSING (lines 3888-4107)

The atomic write sequence:

**Step 1 - Lock account (lines 3894-3915):**
```
EXEC CICS READ FILE(ACCTDAT) UPDATE
     RIDFLD(WS-CARD-RID-ACCT-ID-X)
     INTO(ACCOUNT-RECORD)
```
Failure: SET COULD-NOT-LOCK-ACCT-FOR-UPDATE, exit.

**Step 2 - Lock customer (lines 3921-3942):**
```
EXEC CICS READ FILE(CUSTDAT) UPDATE
     RIDFLD(WS-CARD-RID-CUST-ID-X)
     INTO(CUSTOMER-RECORD)
```
Failure: SET COULD-NOT-LOCK-CUST-FOR-UPDATE, exit.

**Step 3 - Concurrent modification check (lines 3947-3952):**
PERFORM 9700-CHECK-CHANGE-IN-REC. If DATA-WAS-CHANGED-BEFORE-UPDATE: exit without writing.

**Step 4 - Prepare ACCT-UPDATE-RECORD (lines 3956-4002):**
Populates the local update record from ACUP-NEW-* fields. Dates are reassembled into YYYY-MM-DD format using STRING statements. Phone numbers are formatted as (NNN)NNN-NNNN.

**Step 5 - REWRITE account (lines 4065-4081):**
```
EXEC CICS REWRITE FILE(ACCTDAT)
     FROM(ACCT-UPDATE-RECORD)
     LENGTH(LENGTH OF ACCT-UPDATE-RECORD)
```
Failure: SET LOCKED-BUT-UPDATE-FAILED, exit.

**Step 6 - Prepare CUST-UPDATE-RECORD (lines 4007-4058).**

**Step 7 - REWRITE customer (lines 4085-4103):**
```
EXEC CICS REWRITE FILE(CUSTDAT)
     FROM(CUST-UPDATE-RECORD)
     LENGTH(LENGTH OF CUST-UPDATE-RECORD)
```
Failure: SET LOCKED-BUT-UPDATE-FAILED, issue `EXEC CICS SYNCPOINT ROLLBACK` (line 4100), exit.

**Note:** SYNCPOINT ROLLBACK is issued ONLY if the customer REWRITE fails after a successful account REWRITE, ensuring the two updates remain atomic.

### 6.15 9700-CHECK-CHANGE-IN-REC (lines 4109-4193)

Compares every field of the freshly-locked ACCOUNT-RECORD and CUSTOMER-RECORD against the ACUP-OLD-* snapshot taken at initial fetch time. If any field differs: SET DATA-WAS-CHANGED-BEFORE-UPDATE. This is an optimistic concurrency check implemented without database timestamps — it compares all payload fields.

---

## 7. Business Rules Catalog

| Rule | Location | Description |
|---|---|---|
| Account number required | 1210-EDIT-ACCOUNT, line 1787 | Must not be blank/LOW-VALUES |
| Account number numeric and non-zero | 1210-EDIT-ACCOUNT, line 1802 | Must be numeric 11 digits, non-zero |
| Account status Y/N | 1220-EDIT-YESNO, line 1856 | Must be 'Y' or 'N' |
| Credit limit required | 1250-EDIT-SIGNED-9V2, line 1484 | Must be supplied and parseable as signed number |
| Cash credit limit required | 1250-EDIT-SIGNED-9V2, line 1496 | Must be supplied and parseable |
| Current balance required | 1250-EDIT-SIGNED-9V2, line 1509 | Must be supplied and parseable |
| Current cycle credit required | 1250-EDIT-SIGNED-9V2, line 1515 | Must be supplied and parseable |
| Current cycle debit required | 1250-EDIT-SIGNED-9V2, line 1522 | Must be supplied and parseable |
| Open date valid | EDIT-DATE-CCYYMMDD, line 1480 | Must be a valid calendar date |
| Expiry date valid | EDIT-DATE-CCYYMMDD, line 1491 | Must be a valid calendar date |
| Reissue date valid | EDIT-DATE-CCYYMMDD, line 1504 | Must be a valid calendar date |
| SSN Part 1 not 000/666/900-999 | 1265-EDIT-US-SSN, line 2450 | IRS SSN rules for first 3 digits |
| SSN Part 1/2/3 all numeric non-zero | 1265-EDIT-US-SSN, lines 2442-2487 | All three parts required and numeric |
| Date of birth valid | EDIT-DATE-CCYYMMDD + EDIT-DATE-OF-BIRTH, line 1534 | Date must be valid AND in past |
| FICO score 300-850 | 1275-EDIT-FICO-SCORE, line 2515 | 88-level FICO-RANGE-IS-VALID at line 848 |
| First name required alpha | 1225-EDIT-ALPHA-REQD, line 1563 | Required, alphabetic characters and spaces only |
| Middle name optional alpha | 1235-EDIT-ALPHA-OPT, line 1571 | Optional; if supplied, alphabetic only |
| Last name required alpha | 1225-EDIT-ALPHA-REQD, line 1579 | Required, alphabetic only |
| Address line 1 required | 1215-EDIT-MANDATORY, line 1587 | Must be supplied (any printable content) |
| State code valid | 1270-EDIT-US-STATE-CD, line 2494 | Must match VALID-US-STATE-CODE lookup (CSLKPCDY) |
| Zip code numeric required | 1245-EDIT-NUM-REQD, line 1608 | 5-digit numeric, non-zero |
| State/Zip cross-check | 1280-EDIT-US-STATE-ZIP-CD, line 2536 | First 2 digits of zip must match state (USPS rules) |
| City required alpha | 1225-EDIT-ALPHA-REQD, line 1618 | Required, alphabetic only |
| Country required alpha | 1225-EDIT-ALPHA-REQD, line 1627 | Required, 3-char alphabetic |
| Phone 1 area code valid | 1260-EDIT-US-PHONE-NUM, line 2296 | Must be valid NANP general-purpose area code (CSLKPCDY) |
| Phone 2 area code valid | 1260-EDIT-US-PHONE-NUM, line 1643 | Same rules as Phone 1 |
| EFT Account ID numeric | 1245-EDIT-NUM-REQD, line 1652 | Required, 10-digit numeric, non-zero |
| Primary card holder Y/N | 1220-EDIT-YESNO, line 1660 | Must be 'Y' or 'N' |
| No-change detection | 1205-COMPARE-OLD-NEW, line 1682 | All 40+ field pairs must match to trigger NO-CHANGES-DETECTED |
| Concurrent modification detection | 9700-CHECK-CHANGE-IN-REC, line 4109 | Re-reads locked records and compares all fields to old snapshot |
| Atomic account+customer update | 9600-WRITE-PROCESSING, line 4100 | SYNCPOINT ROLLBACK issued if customer REWRITE fails after account REWRITE succeeds |

---

## 8. CICS Commands Used

| CICS Command | Location | Purpose |
|---|---|---|
| HANDLE ABEND LABEL | Line 862 | Register abend handler |
| RECEIVE MAP | Line 1040-1045 | Read operator input from map CACTUPA |
| SEND MAP ... ERASE FREEKB CURSOR | Line 3594-3601 | Display screen to operator |
| READ DATASET (CXACAIX) | Line 3654-3662 | Read card xref via alternate index |
| READ DATASET (ACCTDAT) | Line 3703-3711 | Read account master |
| READ DATASET (CUSTDAT) | Line 3753-3761 | Read customer master |
| READ FILE UPDATE (ACCTDAT) | Line 3894-3903 | Lock account for update |
| READ FILE UPDATE (CUSTDAT) | Line 3921-3930 | Lock customer for update |
| REWRITE FILE (ACCTDAT) | Line 4065-4071 | Write updated account record |
| REWRITE FILE (CUSTDAT) | Line 4085-4091 | Write updated customer record |
| SYNCPOINT | Line 953 | Issue sync before F3 XCTL |
| SYNCPOINT ROLLBACK | Line 4099-4101 | Roll back on customer write failure |
| XCTL PROGRAM | Line 956-958 | Transfer control to caller (F3) |
| RETURN TRANSID COMMAREA | Line 1015-1018 | Pseudo-conversational return |
| SEND TEXT ERASE FREEKB | Lines 878-882 | Diagnostic plain-text output |
| HANDLE ABEND CANCEL | Line 4218-4220 | Cancel abend handler in abend routine |
| ABEND ABCODE('9999') | Line 4222-4224 | Force abend with code 9999 |

---

## 9. Data Structures

### 9.1 ACCOUNT-RECORD (CVACT01Y.CPY)

| Field | PIC | Length |
|---|---|---|
| ACCT-ID | 9(11) | 11 |
| ACCT-ACTIVE-STATUS | X(01) | 1 |
| ACCT-CURR-BAL | S9(10)V99 | 12 |
| ACCT-CREDIT-LIMIT | S9(10)V99 | 12 |
| ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | 12 |
| ACCT-OPEN-DATE | X(10) | 10 (YYYY-MM-DD) |
| ACCT-EXPIRAION-DATE | X(10) | 10 (YYYY-MM-DD) |
| ACCT-REISSUE-DATE | X(10) | 10 (YYYY-MM-DD) |
| ACCT-CURR-CYC-CREDIT | S9(10)V99 | 12 |
| ACCT-CURR-CYC-DEBIT | S9(10)V99 | 12 |
| ACCT-ADDR-ZIP | X(10) | 10 |
| ACCT-GROUP-ID | X(10) | 10 |
| FILLER | X(178) | 178 |

Total record length: 300 bytes.

### 9.2 CUSTOMER-RECORD (CVCUS01Y.CPY)

| Field | PIC | Length |
|---|---|---|
| CUST-ID | 9(09) | 9 |
| CUST-FIRST-NAME | X(25) | 25 |
| CUST-MIDDLE-NAME | X(25) | 25 |
| CUST-LAST-NAME | X(25) | 25 |
| CUST-ADDR-LINE-1 | X(50) | 50 |
| CUST-ADDR-LINE-2 | X(50) | 50 |
| CUST-ADDR-LINE-3 | X(50) | 50 (City) |
| CUST-ADDR-STATE-CD | X(02) | 2 |
| CUST-ADDR-COUNTRY-CD | X(03) | 3 |
| CUST-ADDR-ZIP | X(10) | 10 |
| CUST-PHONE-NUM-1 | X(15) | 15 (NNN)NNN-NNNN |
| CUST-PHONE-NUM-2 | X(15) | 15 |
| CUST-SSN | 9(09) | 9 |
| CUST-GOVT-ISSUED-ID | X(20) | 20 |
| CUST-DOB-YYYY-MM-DD | X(10) | 10 |
| CUST-EFT-ACCOUNT-ID | X(10) | 10 |
| CUST-PRI-CARD-HOLDER-IND | X(01) | 1 |
| CUST-FICO-CREDIT-SCORE | 9(03) | 3 |
| FILLER | X(168) | 168 |

Total record length: 500 bytes.

### 9.3 CARD-XREF-RECORD (CVACT03Y.CPY)

| Field | PIC | Length |
|---|---|---|
| XREF-CARD-NUM | X(16) | 16 |
| XREF-CUST-ID | 9(09) | 9 |
| XREF-ACCT-ID | 9(11) | 11 |
| FILLER | X(14) | 14 |

Total record length: 50 bytes.

---

## 10. VSAM Files Referenced

| Logical Name | Physical Name | Access Mode | Key |
|---|---|---|---|
| ACCTDAT | ACCTDAT | KSDS, keyed by account ID (11 bytes) | ACCT-ID 9(11) |
| CUSTDAT | CUSTDAT | KSDS, keyed by customer ID (9 bytes) | CUST-ID 9(09) |
| CXACAIX | CXACAIX | Alternate index on card xref by account ID | XREF-ACCT-ID 9(11) |

---

## 11. Inter-Program Interactions

| Direction | Program | Transaction | Mechanism | Condition |
|---|---|---|---|---|
| Exit to (default) | COMEN01C | CM00 | XCTL + SYNCPOINT | F3 with no CDEMO-FROM-PROGRAM |
| Exit to (caller) | (from COMMAREA) | (from COMMAREA) | XCTL + SYNCPOINT | F3 with CDEMO-FROM-PROGRAM set |
| Called by | COMEN01C | CM00 | XCTL | Standard menu flow |
| Called by | COCRDLIC | CCLI | XCTL | Card list -> account update |
| Pseudo-return | COACTUPC | CAUP | CICS RETURN | Every non-exit path |

Note: `LIT-CCLISTPGM = 'COCRDLIC'` (line 550) and `LIT-CARDUPDATE-PGM = 'COCRDUPC'` (line 541) are referenced as literals for context tracking but COACTUPC does not directly XCTL or LINK to them.

---

## 12. Screen Attribute Management

The program uses the CSSETATY.CPY copybook (via COPY REPLACING at lines 3208-3435) as a macro to set field color and content for each editable field. The expanded pattern for each field is:

```cobol
IF (FLG-(TESTVAR1)-NOT-OK OR FLG-(TESTVAR1)-BLANK)
AND CDEMO-PGM-REENTER
    MOVE DFHRED TO (SCRNVAR2)C OF (MAPNAME3)O
    IF FLG-(TESTVAR1)-BLANK
        MOVE '*' TO (SCRNVAR2)O OF (MAPNAME3)O
    END-IF
END-IF
```

This pattern is applied to every validated field (approximately 35 fields), producing consistent red highlighting and asterisk replacement for all error conditions.

---

## 13. Error Handling

| Error Condition | Response | Source |
|---|---|---|
| No account number entered | WS-PROMPT-FOR-ACCT set, INPUT-ERROR, cursor to ACCTSID | 1210-EDIT-ACCOUNT |
| Account number not numeric/zero | WS-RETURN-MSG set, INPUT-ERROR | 1210-EDIT-ACCOUNT |
| Account not found in CXACAIX | INPUT-ERROR, account filter flagged NOT-OK | 9200-GETCARDXREF-BYACCT |
| Account not found in ACCTDAT | INPUT-ERROR, account filter flagged NOT-OK | 9300-GETACCTDATA-BYACCT |
| Customer not found in CUSTDAT | INPUT-ERROR, customer filter flagged NOT-OK | 9400-GETCUSTDATA-BYCUST |
| VSAM read error (OTHER) | WS-FILE-ERROR-MESSAGE with RESP/RESP2, INPUT-ERROR | All 9xxx paragraphs |
| Validation failure | Field flag set NOT-OK, WS-RETURN-MSG set, field highlighted red | 1200-EDIT-MAP-INPUTS |
| Cannot lock account for update | COULD-NOT-LOCK-ACCT-FOR-UPDATE, INFORM-FAILURE message | 9600-WRITE-PROCESSING |
| Cannot lock customer for update | COULD-NOT-LOCK-CUST-FOR-UPDATE, INFORM-FAILURE message | 9600-WRITE-PROCESSING |
| Record changed concurrently | DATA-WAS-CHANGED-BEFORE-UPDATE, re-shows data | 9700-CHECK-CHANGE-IN-REC |
| Account REWRITE failure | LOCKED-BUT-UPDATE-FAILED, INFORM-FAILURE message | 9600-WRITE-PROCESSING |
| Customer REWRITE failure | LOCKED-BUT-UPDATE-FAILED, SYNCPOINT ROLLBACK, INFORM-FAILURE | 9600-WRITE-PROCESSING |
| Invalid AID key | Treated as ENTER (line 916) | 0000-MAIN |
| Unexpected state | ABEND-ROUTINE called, ABEND code 9999 | 2000-DECIDE-ACTION |
| Any CICS abend | HANDLE ABEND -> ABEND-ROUTINE -> sends ABEND-DATA, abends with 9999 | Lines 862-864, 4203-4225 |

---

## 14. Transaction Flow

```
User presses CAUP (or arrives via XCTL from menu/card-list)
        |
        v
COACTUPC Pass 1: ACUP-DETAILS-NOT-FETCHED
  - Sends blank CACTUPA screen
  - Operator enters 11-digit account number
  - CICS RETURN TRANSID(CAUP)
        |
        v
COACTUPC Pass 2: CDEMO-PGM-REENTER
  1000-PROCESS-INPUTS:
    - RECEIVE MAP: capture account number
    - 1210-EDIT-ACCOUNT: validate account number
  2000-DECIDE-ACTION:
    - ACUP-DETAILS-NOT-FETCHED -> 9000-READ-ACCT
      - Read CXACAIX (alternate index), get customer ID
      - Read ACCTDAT, get account record
      - Read CUSTDAT, get customer record
      - Store in ACUP-OLD-* and CDEMO-* context
      - SET ACUP-SHOW-DETAILS
  3000-SEND-MAP:
    - Shows full account + customer data (editable)
    - Info msg: "Update account details presented above."
  CICS RETURN TRANSID(CAUP)
        |
        v
COACTUPC Pass 3: Operator edits fields, presses ENTER
  1000-PROCESS-INPUTS:
    - RECEIVE MAP: capture all field values
    - 1205-COMPARE-OLD-NEW: detect changes
    - 1200-EDIT-MAP-INPUTS: validate all changed fields
  2000-DECIDE-ACTION:
    - If INPUT-ERROR: redisplay with errors (ACUP-CHANGES-NOT-OK)
    - If no changes: redisplay unchanged
    - If all OK: SET ACUP-CHANGES-OK-NOT-CONFIRMED
  3000-SEND-MAP:
    - Shows data with edited values
    - Info msg: "Changes validated.Press F5 to save"
    - F5 key enabled
  CICS RETURN TRANSID(CAUP)
        |
        v
COACTUPC Pass 4: Operator presses F5 to confirm
  2000-DECIDE-ACTION:
    - ACUP-CHANGES-OK-NOT-CONFIRMED AND PFK05:
      - 9600-WRITE-PROCESSING:
        - READ UPDATE ACCTDAT (locks record)
        - READ UPDATE CUSTDAT (locks record)
        - 9700-CHECK-CHANGE-IN-REC (concurrent mod check)
        - REWRITE ACCTDAT
        - REWRITE CUSTDAT
        - On failure: SYNCPOINT ROLLBACK
      - SET ACUP-CHANGES-OKAYED-AND-DONE
  3000-SEND-MAP:
    - Shows saved data
    - Info msg: "Changes committed to database"
  CICS RETURN TRANSID(CAUP)
        |
        v
COACTUPC Pass 5: ACUP-CHANGES-OKAYED-AND-DONE / FAILED
  - Reinitialize state
  - Show blank search screen
  - Ready for new account number
```

---

## 15. Open Questions and Gaps

| Item | Status |
|---|---|
| CVCRD01Y.CPY content | [ARTIFACT READ AT LINE 597 but not read in detail] — contains `CC-WORK-AREA` and `CC-ACCT-ID` referenced throughout |
| COTTL01Y.CPY content | Not fully read — provides CCDA-TITLE01 and CCDA-TITLE02 screen title literals |
| CSUTLDPY.CPY content | Not fully read — provides EDIT-DATE-CCYYMMDD and EDIT-DATE-OF-BIRTH paragraphs (COPYed at line 4232) |
| CSUTLDWY.CPY content | Not fully read — provides WS-EDIT-DATE-CCYYMMDD and WS-EDIT-DATE-FLGS variables (COPYed at line 166) |
| CSLKPCDY.CPY content | Not fully read — provides VALID-GENERAL-PURP-CODE and VALID-US-STATE-CODE and VALID-US-STATE-ZIP-CD2-COMBO condition-names |
| CSMSG01Y.CPY / CSMSG02Y.CPY | Not read — ABEND-DATA, ABEND-CULPRIT, ABEND-CODE, ABEND-REASON, ABEND-MSG, CCARD-ERROR-MSG, CCARD-AID-* flags are defined here |
| CSUSR01Y.CPY | Not read — user session data |
| COACTUP (BMS copybook) | Not read directly — generated from COACTUP.BMS and copied at line 623; provides CACTUPAI/CACTUPAO structures |
| Country code validation | ACSCTRYA is protected (line 3547) with comment "Since most of the edits are USA specific" — country is not validated |
| Address Line 2 | Labeled "NO EDITS CODED AS YET" (line 3369) — field is editable but no validation |
| Account Group ID | No validation rules coded — field is editable but only a mandatory-presence check is absent |
