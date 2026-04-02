# CardDemo Copybook Catalog - Technical Specification

**Document:** COPYBOOKS_spec.md  
**Project:** AWS Mainframe Modernization - CardDemo  
**Date:** 2026-04-02  
**Analyst:** Mainframe Codebase Analyst  
**Source Directories Analyzed:**
- `app/cpy/` — Main application copybooks
- `app/cpy-bms/` — BMS-generated screen copybooks
- `app/app-authorization-ims-db2-mq/cpy/` — Authorization subsystem copybooks
- `app/app-authorization-ims-db2-mq/cpy-bms/` — Authorization BMS copybooks
- `app/app-transaction-type-db2/cpy/` — Transaction type DB2 copybooks
- `app/app-transaction-type-db2/cpy-bms/` — Transaction type BMS copybooks

---

## 1. Executive Summary

The CardDemo application contains **57 copybooks** across six directories. These fall into four functional categories: (1) core entity data structures (VSAM record layouts for Account, Customer, Card, Transaction), (2) inter-program communication structures (COMMAREA, work areas), (3) BMS-generated screen maps (one copybook per screen in paired input/output layout), and (4) subsystem-specific structures (IMS PCBs, MQ message layouts, DB2 utilities, authorization request/response). The most widely shared copybook is `CSSETATY` (39 inline COPY REPLACING usages in `COACTUPC` alone), followed by `COCOM01Y` (used by 14 programs), `DFHBMSCA` and `DFHAID` (15 programs each), `CSMSG01Y` (15 programs), `CSDAT01Y` (15 programs), and `COTTL01Y` (15 programs). These six copybooks form the universal infrastructure layer present in virtually every online CICS program.

---

## 2. Artifact Inventory

### 2.1 Main Copybooks (app/cpy/)

| Copybook | Type | Record Length | Primary Purpose |
|---|---|---|---|
| COCOM01Y | COMMAREA | ~164 bytes | Inter-program communication area (CARDDEMO-COMMAREA) |
| CVACT01Y | Entity | 300 bytes | Account VSAM record layout |
| CVACT02Y | Entity | 150 bytes | Card (credit card) VSAM record layout |
| CVACT03Y | Entity | 50 bytes | Card-to-Account cross-reference VSAM record layout |
| CVCUS01Y | Entity | 500 bytes | Customer VSAM record layout |
| CVCRD01Y | Work Area | Variable | Credit card AID key work area with REDEFINES |
| CVTRA01Y | Entity | 50 bytes | Transaction category balance record (TRAN-CAT-BAL-RECORD) |
| CVTRA02Y | Entity | 50 bytes | Disclosure group record (DIS-GROUP-RECORD) |
| CVTRA03Y | Entity | 60 bytes | Transaction type record (TRAN-TYPE-RECORD) |
| CVTRA04Y | Entity | 60 bytes | Transaction category record (TRAN-CAT-RECORD) |
| CVTRA05Y | Entity | 350 bytes | Transaction VSAM record layout (TRAN-RECORD) |
| CVTRA06Y | Entity | 350 bytes | Daily transaction record layout (DALYTRAN-RECORD) |
| CVTRA07Y | Report | Variable | Daily transaction report header/detail/total structures |
| CVEXPORT | Export | 500 bytes | Multi-entity sequential export record with REDEFINES |
| CSDAT01Y | Utility | ~56 bytes | Current date/time working storage structure |
| CSMSG01Y | Utility | ~100 bytes | Common screen messages (Thank-you, Invalid-key) |
| CSMSG02Y | Utility | ~134 bytes | Abend work area (ABEND-DATA) |
| CSUSR01Y | Security | 80 bytes | User security data (SEC-USER-DATA) |
| CSSETATY | Inline Logic | N/A | Procedure division: BMS field attribute setting snippet |
| CSSTRPFY | Inline Logic | N/A | Procedure division: string processing (not available in cpy/) |
| CSUTLDWY | Work Area | Variable | Date validation working storage (CSUTLDWY) |
| CSUTLDPY | Procedure | N/A | Date validation paragraphs (EDIT-DATE-CCYYMMDD, EDIT-DATE-LE, etc.) |
| COTTL01Y | UI | 120 bytes | Screen title constants (AWS Mainframe Modernization / CardDemo) |
| COADM02Y | Navigation | Variable | Admin menu option table (6 options, program names embedded) |
| COMEN02Y | Navigation | Variable | Main user menu option table (11 options, program names embedded) |
| CSLKPCDY | Validation | Variable | US phone area code, state code, and state+ZIP lookup tables |
| CODATECN | Utility | ~42 bytes | Date conversion interface record (CODATECN-REC) |
| COSTM01 | Batch | 350 bytes | Statement transaction record (TRNX-RECORD) with composite KSDS key |
| CUSTREC | Batch | 500 bytes | Customer record (duplicate of CVCUS01Y with YYYYMMDD date field) |
| UNUSED1Y | Unused | 80 bytes | Unused user data structure (mirrors CSUSR01Y) |

### 2.2 BMS-Generated Screen Copybooks (app/cpy-bms/)

Each BMS copybook defines a paired input map (suffix `I`) and output map (suffix `O`, implemented as REDEFINES of the input map). All maps share a standard header section: TRNNAME, TITLE01, CURDATE, PGMNAME, TITLE02, CURTIME fields.

| Copybook | Map Name (Input/Output) | Associated Program | Screen Function |
|---|---|---|---|
| COSGN00.CPY | COSGN0AI / COSGN0AO | COSGN00C | Sign-on (USERID, PASSWD, ERRMSG) |
| COMEN01.CPY | COMEN1AI / COMEN1AO | COMEN01C | User main menu (12 option lines, OPTION selector, ERRMSG) |
| COADM01.CPY | COADM1AI / COADM1AO | COADM01C | Admin menu (12 option lines, OPTION selector, ERRMSG) |
| COACTUP.CPY | CACTUPAI / CACTUPAO | COACTUPC | Account update form (full account fields) |
| COACTVW.CPY | CACTVWAI / CACTVWAO | COACTVWC | Account view (read-only account fields) |
| COBIL00.CPY | CBIL0AI / CBIL0AO | COBIL00C | Bill payment screen |
| COCRDSL.CPY | CCRDSLAI / CCRDSLA0 | COCRDSLC | Credit card selection/view screen |
| COCRDLI.CPY | CCRDLIAI / CCRDLIAO | COCRDLIC | Credit card list screen (7 rows: CRDSEL, ACCTNO, CRDNUM, CRDNAME, CRDSTCD, EXPMON, EXPYEAR) |
| COCRDUP.CPY | CCRDUAI / CCRDUAO | COCRDUPC | Credit card update form |
| CORPT00.CPY | CRPT00AI / CRPT00AO | CORPT00C | Transaction report generation screen |
| COTRN00.CPY | COTRN0AI / COTRN0AO | COTRN00C | Transaction list screen (10 rows with TRNID selectors) |
| COTRN01.CPY | COTRN1AI / COTRN1AO | COTRN01C | Transaction detail view |
| COTRN02.CPY | COTRN2AI / COTRN2AO | COTRN02C | Transaction add screen |
| COUSR00.CPY | COUSR0AI / COUSR0AO | COUSR00C | User list screen (10 rows with USRID selectors) |
| COUSR01.CPY | COUSR1AI / COUSR1AO | COUSR01C | User add screen |
| COUSR02.CPY | COUSR2AI / COUSR2AO | COUSR02C | User update screen |
| COUSR03.CPY | COUSR3AI / COUSR3AO | COUSR03C | User delete screen |

### 2.3 Authorization Subsystem Copybooks (app/app-authorization-ims-db2-mq/cpy/)

| Copybook | Type | Purpose |
|---|---|---|
| CCPAUERY.cpy | IMS Log | ERROR-LOG-RECORD — authorization error log (date, time, app, program, level, subsystem, codes, message, event key) |
| CCPAURLY.cpy | IMS Segment | Authorization response fields (card number, transaction ID, auth ID code, response code, reason, approved amount) |
| CCPAURQY.cpy | IMS Segment | Authorization request fields (date, time, card number, auth type, expiry, message type/source, processing code, amount, merchant data, transaction ID) |
| CIPAUDTY.cpy | IMS Segment | Pending Authorization Details segment (full auth detail including key PA-AUTH-DATE-9C/PA-AUTH-TIME-9C, match status, fraud flags) |
| CIPAUSMY.cpy | IMS Segment | Pending Authorization Summary segment (account ID, customer ID, auth status, credit/cash limits and balances, approved/declined counts and amounts) |
| IMSFUNCS.cpy | IMS Utility | DL/I function code constants (GU, GHU, GN, GHN, GNP, GHNP, REPL, ISRT, DLET) plus PARMCOUNT |
| PADFLPCB.CPY | IMS PCB | PCB definition for PADFL (Authorization Details) IMS database |
| PASFLPCB.CPY | IMS PCB | PCB definition for PASFL (Authorization Summary) IMS database (keyfb 100 bytes) |
| PAUTBPCB.CPY | IMS PCB | PCB definition for PAUT (Authorization table) IMS database (keyfb 255 bytes) |

### 2.4 Authorization BMS Copybooks (app/app-authorization-ims-db2-mq/cpy-bms/)

| Copybook | Map Name | Associated Program | Screen Function |
|---|---|---|---|
| COPAU00.cpy | COPAU0AI / COPAU0AO | COPAUS0C | Pending Authorization list (account ID input, list of authorizations) |
| COPAU01.cpy | COPAU1AI / COPAU1AO | COPAUS1C | Pending Authorization detail view (card number as key input) |

### 2.5 Transaction Type DB2 Copybooks (app/app-transaction-type-db2/cpy/)

| Copybook | Type | Purpose |
|---|---|---|
| CSDB2RPY.cpy | DB2 Procedure | Procedure division: DB2 priming query (SELECT 1 FROM SYSIBM.SYSDUMMY1) and DSNTIAC message formatting paragraph |
| CSDB2RWY.cpy | DB2 Work Area | Working storage for DB2: SQLCODE display field, dummy int, processing flag, current action message, DSNTIAC formatted message buffer (10x72-char lines) |

### 2.6 Transaction Type BMS Copybooks (app/app-transaction-type-db2/cpy-bms/)

| Copybook | Map Name | Associated Program | Screen Function |
|---|---|---|---|
| COTRTLI.cpy | CTRTLIAI / CTRTLIAO | COTRTLIC | Transaction type list screen (PAGENO field, list rows with type code and description) |
| COTRTUP.cpy | CTRTUPAI / CTRTUPAO | COTRTUPC | Transaction type update/add screen (TRTYPCD field) |

---

## 3. Detailed Copybook Analysis

### 3.1 COCOM01Y — Application COMMAREA

**File:** `app/cpy/COCOM01Y.cpy`  
**Root Record:** `CARDDEMO-COMMAREA`  
**Version:** CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19

This is the single most critical shared structure in the CardDemo system. It is passed as the COMMAREA in every CICS XCTL and LINK call, enabling state continuity across screen transitions.

```
01 CARDDEMO-COMMAREA.
   05 CDEMO-GENERAL-INFO.
      10 CDEMO-FROM-TRANID       PIC X(04)   -- Originating transaction ID
      10 CDEMO-FROM-PROGRAM      PIC X(08)   -- Originating program name
      10 CDEMO-TO-TRANID         PIC X(04)   -- Destination transaction ID
      10 CDEMO-TO-PROGRAM        PIC X(08)   -- Destination program name
      10 CDEMO-USER-ID           PIC X(08)   -- Authenticated user ID
      10 CDEMO-USER-TYPE         PIC X(01)   -- 'A'=Admin, 'U'=User
         88 CDEMO-USRTYP-ADMIN   VALUE 'A'
         88 CDEMO-USRTYP-USER    VALUE 'U'
      10 CDEMO-PGM-CONTEXT       PIC 9(01)   -- 0=First entry, 1=Re-entry
         88 CDEMO-PGM-ENTER      VALUE 0
         88 CDEMO-PGM-REENTER    VALUE 1
   05 CDEMO-CUSTOMER-INFO.
      10 CDEMO-CUST-ID           PIC 9(09)
      10 CDEMO-CUST-FNAME        PIC X(25)
      10 CDEMO-CUST-MNAME        PIC X(25)
      10 CDEMO-CUST-LNAME        PIC X(25)
   05 CDEMO-ACCOUNT-INFO.
      10 CDEMO-ACCT-ID           PIC 9(11)
      10 CDEMO-ACCT-STATUS       PIC X(01)
   05 CDEMO-CARD-INFO.
      10 CDEMO-CARD-NUM          PIC 9(16)
   05 CDEMO-MORE-INFO.
      10 CDEMO-LAST-MAP          PIC X(7)    -- Last BMS map name
      10 CDEMO-LAST-MAPSET       PIC X(7)    -- Last BMS mapset name
```

**Programs Referencing COCOM01Y:** COSGN00C, COMEN01C, COADM01C, COACTVWC, COACTUPC, COCRDSLC, COCRDLIC, COCRDUPC, COBIL00C, COTRN00C, COTRN01C, COTRN02C, CORPT00C, COUSR00C, COUSR01C, COUSR02C, COUSR03C, COPAUS0C, COPAUS1C, COTRTLIC, COTRTUPC (14 programs from main cbl/, plus authorization and transaction-type subsystems)

**Confidence:** HIGH — directly observed in `app/cpy/COCOM01Y.cpy` lines 19-47.

---

### 3.2 CVACT01Y — Account Record

**File:** `app/cpy/CVACT01Y.cpy`  
**Root Record:** `ACCOUNT-RECORD`  
**Record Length:** 300 bytes  
**Version:** CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19

This is the VSAM KSDS account record layout (file logical name: ACCTFILE).

```
01 ACCOUNT-RECORD.
   05 ACCT-ID                PIC 9(11)         -- Primary key, 11-digit account number
   05 ACCT-ACTIVE-STATUS     PIC X(01)         -- Account status flag
   05 ACCT-CURR-BAL          PIC S9(10)V99     -- Current balance (signed, 2 decimal)
   05 ACCT-CREDIT-LIMIT      PIC S9(10)V99     -- Credit limit
   05 ACCT-CASH-CREDIT-LIMIT PIC S9(10)V99     -- Cash credit limit
   05 ACCT-OPEN-DATE         PIC X(10)         -- Open date (YYYY-MM-DD)
   05 ACCT-EXPIRAION-DATE    PIC X(10)         -- Expiration date (note: typo in original)
   05 ACCT-REISSUE-DATE      PIC X(10)         -- Reissue date
   05 ACCT-CURR-CYC-CREDIT   PIC S9(10)V99     -- Current cycle credits
   05 ACCT-CURR-CYC-DEBIT    PIC S9(10)V99     -- Current cycle debits
   05 ACCT-ADDR-ZIP          PIC X(10)         -- ZIP code for billing address
   05 ACCT-GROUP-ID          PIC X(10)         -- Account group (used for disclosure rate lookup)
   05 FILLER                 PIC X(178)
```

**Programs Referencing CVACT01Y:** CBACT01C (batch - account KSDS I/O), CBTRN01C (batch), CBTRN02C (batch), CBEXPORT (batch), CBIMPORT (batch), CBSTM03A (batch), COACTUPC (online), COACTVWC (online), COBIL00C (online), COTRN02C (online), COPAUS0C (auth subsystem), COPAUA0C (auth subsystem), COACCT01 (MQ service)

**Confidence:** HIGH — directly observed in `app/cpy/CVACT01Y.cpy` lines 4-17.

---

### 3.3 CVACT02Y — Card Record

**File:** `app/cpy/CVACT02Y.cpy`  
**Root Record:** `CARD-RECORD`  
**Record Length:** 150 bytes  
**Version:** CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19

VSAM KSDS card (credit card) record layout (file logical name: CARDFILE). Primary key is CARD-NUM.

```
01 CARD-RECORD.
   05 CARD-NUM               PIC X(16)    -- 16-character card number (primary key)
   05 CARD-ACCT-ID           PIC 9(11)    -- Associated account ID
   05 CARD-CVV-CD            PIC 9(03)    -- CVV security code (3-digit)
   05 CARD-EMBOSSED-NAME     PIC X(50)    -- Name as embossed on card
   05 CARD-EXPIRAION-DATE    PIC X(10)    -- Expiration date (note: typo in original)
   05 CARD-ACTIVE-STATUS     PIC X(01)    -- Active status flag
   05 FILLER                 PIC X(59)
```

**Programs Referencing CVACT02Y:** CBACT02C (batch - card KSDS I/O), CBEXPORT (batch), CBIMPORT (batch), COACTUPC (online), COACTVWC (online), COCRDUPC (online), COCRDSLC (online), COCRDLIC (online), COTRTLIC (DB2 subsystem)

**Confidence:** HIGH — directly observed in `app/cpy/CVACT02Y.cpy` lines 4-11.

---

### 3.4 CVACT03Y — Card-to-Account Cross-Reference Record

**File:** `app/cpy/CVACT03Y.cpy`  
**Root Record:** `CARD-XREF-RECORD`  
**Record Length:** 50 bytes  
**Version:** CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19

VSAM KSDS cross-reference record (file logical name: XREFFILE). Links card number to customer and account.

```
01 CARD-XREF-RECORD.
   05 XREF-CARD-NUM          PIC X(16)    -- Card number (primary key)
   05 XREF-CUST-ID           PIC 9(09)    -- Associated customer ID
   05 XREF-ACCT-ID           PIC 9(11)    -- Associated account ID
   05 FILLER                 PIC X(14)
```

**Programs Referencing CVACT03Y:** CBACT03C (batch - xref KSDS I/O), CBTRN01C (batch), CBTRN02C (batch), CBEXPORT (batch), CBIMPORT (batch), CBSTM03A (batch), COACTUPC (online), COACTVWC (online), COTRN02C (online), COBIL00C (online), COPAUS0C (auth subsystem), COPAUA0C (auth subsystem), CBTRN03C (batch)

**Confidence:** HIGH — directly observed in `app/cpy/CVACT03Y.cpy` lines 4-8.

---

### 3.5 CVCUS01Y — Customer Record

**File:** `app/cpy/CVCUS01Y.cpy`  
**Root Record:** `CUSTOMER-RECORD`  
**Record Length:** 500 bytes  
**Version:** CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19

VSAM KSDS customer record layout (file logical name: CUSTFILE). Primary key is CUST-ID.

```
01 CUSTOMER-RECORD.
   05 CUST-ID                  PIC 9(09)    -- 9-digit customer ID (primary key)
   05 CUST-FIRST-NAME          PIC X(25)
   05 CUST-MIDDLE-NAME         PIC X(25)
   05 CUST-LAST-NAME           PIC X(25)
   05 CUST-ADDR-LINE-1         PIC X(50)
   05 CUST-ADDR-LINE-2         PIC X(50)
   05 CUST-ADDR-LINE-3         PIC X(50)
   05 CUST-ADDR-STATE-CD       PIC X(02)    -- 2-char US state code
   05 CUST-ADDR-COUNTRY-CD     PIC X(03)    -- 3-char country code
   05 CUST-ADDR-ZIP            PIC X(10)    -- ZIP code
   05 CUST-PHONE-NUM-1         PIC X(15)
   05 CUST-PHONE-NUM-2         PIC X(15)
   05 CUST-SSN                 PIC 9(09)    -- Social Security Number
   05 CUST-GOVT-ISSUED-ID      PIC X(20)    -- Government-issued ID
   05 CUST-DOB-YYYY-MM-DD      PIC X(10)    -- Date of birth
   05 CUST-EFT-ACCOUNT-ID      PIC X(10)    -- EFT account identifier
   05 CUST-PRI-CARD-HOLDER-IND PIC X(01)    -- Primary cardholder indicator
   05 CUST-FICO-CREDIT-SCORE   PIC 9(03)    -- FICO score (3-digit)
   05 FILLER                   PIC X(168)
```

**Note:** A near-duplicate, `CUSTREC.cpy`, exists in `app/cpy/` with an identical structure but uses field `CUST-DOB-YYYYMMDD` (no hyphens), used exclusively in batch programs CBSTM03A.

**Programs Referencing CVCUS01Y:** CBCUS01C (batch - customer KSDS I/O), CBEXPORT, CBIMPORT, CBTRN01C, COACTUPC, COACTVWC, COCRDUPC, COCRDSLC, COPAUS0C, COPAUA0C

**Confidence:** HIGH — directly observed in `app/cpy/CVCUS01Y.cpy` lines 4-23.

---

### 3.6 CVCRD01Y — Credit Card Work Area

**File:** `app/cpy/CVCRD01Y.cpy`  
**Root Record:** `CC-WORK-AREAS`  
**Version:** CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19

Working storage for credit card screen programs. Contains AID (attention identifier) parsing constants, navigation fields, and key-passing fields for account/card/customer IDs. Note the commented-out fields (CCARD-LAST-PROG, CCARD-RETURN-TO-PROG, CCARD-RETURN-FLAG, CCARD-FUNCTION), indicating design simplification.

```
01 CC-WORK-AREAS.
   05 CC-WORK-AREA.
      10 CCARD-AID            PIC X(5)     -- AID value: ENTER, CLEAR, PA1, PA2, PFK01-PFK12
         88 CCARD-AID-ENTER   VALUE 'ENTER'
         ... (12 PFK conditions)
      10 CCARD-NEXT-PROG      PIC X(8)     -- Program to XCTL to next
      10 CCARD-NEXT-MAPSET    PIC X(7)     -- Next map set name
      10 CCARD-NEXT-MAP       PIC X(7)     -- Next map name
      10 CCARD-ERROR-MSG      PIC X(75)    -- Error message buffer
      10 CCARD-RETURN-MSG     PIC X(75)    -- Return/informational message
         88 CCARD-RETURN-MSG-OFF  VALUE LOW-VALUES
      10 CC-ACCT-ID           PIC X(11)    -- Account ID (alpha)
         10 CC-ACCT-ID-N REDEFINES CC-ACCT-ID  PIC 9(11)
      10 CC-CARD-NUM          PIC X(16)    -- Card number (alpha)
         10 CC-CARD-NUM-N REDEFINES CC-CARD-NUM PIC 9(16)
      10 CC-CUST-ID           PIC X(09)    -- Customer ID (alpha)
         10 CC-CUST-ID-N REDEFINES CC-CUST-ID   PIC 9(9)
```

**Programs Referencing CVCRD01Y:** COCRDLIC, COCRDSLC, COCRDUPC, COACTUPC, COACTVWC, COTRTLIC, COTRTUPC

**Confidence:** HIGH — directly observed in `app/cpy/CVCRD01Y.cpy` lines 1-43.

---

### 3.7 CVTRA05Y — Transaction Record (Primary)

**File:** `app/cpy/CVTRA05Y.cpy`  
**Root Record:** `TRAN-RECORD`  
**Record Length:** 350 bytes  
**Version:** CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19

Primary transaction VSAM KSDS record layout (file logical name: TRANFILE). Key is TRAN-ID.

```
01 TRAN-RECORD.
   05 TRAN-ID              PIC X(16)         -- Transaction ID (primary key)
   05 TRAN-TYPE-CD         PIC X(02)         -- Transaction type code
   05 TRAN-CAT-CD          PIC 9(04)         -- Transaction category code
   05 TRAN-SOURCE          PIC X(10)         -- Source system/channel
   05 TRAN-DESC            PIC X(100)        -- Transaction description
   05 TRAN-AMT             PIC S9(09)V99     -- Transaction amount (signed)
   05 TRAN-MERCHANT-ID     PIC 9(09)         -- Merchant identifier
   05 TRAN-MERCHANT-NAME   PIC X(50)
   05 TRAN-MERCHANT-CITY   PIC X(50)
   05 TRAN-MERCHANT-ZIP    PIC X(10)
   05 TRAN-CARD-NUM        PIC X(16)         -- Card number for this transaction
   05 TRAN-ORIG-TS         PIC X(26)         -- Original timestamp
   05 TRAN-PROC-TS         PIC X(26)         -- Processing timestamp
   05 FILLER               PIC X(20)
```

**Programs Referencing CVTRA05Y:** CBTRN01C, CBTRN02C, CBTRN03C, CBEXPORT, CBIMPORT, CBSTM03A (batch programs reading/writing transaction file), COBIL00C, COTRN00C, COTRN01C, COTRN02C, CORPT00C (online programs), COTRTLIC (DB2 subsystem)

**Confidence:** HIGH — directly observed in `app/cpy/CVTRA05Y.cpy` lines 4-18.

---

### 3.8 CVTRA06Y — Daily Transaction Record

**File:** `app/cpy/CVTRA06Y.cpy`  
**Root Record:** `DALYTRAN-RECORD`  
**Record Length:** 350 bytes  
**Version:** CardDemo_v1.0-15-g27d6c6f-68, 2022-07-19

Daily transaction input file record (file logical name: DALYTRAN). Structurally identical to CVTRA05Y/TRAN-RECORD but prefixed with DALYTRAN- to distinguish batch input from the master transaction file.

```
01 DALYTRAN-RECORD.
   05 DALYTRAN-ID           PIC X(16)
   05 DALYTRAN-TYPE-CD      PIC X(02)
   05 DALYTRAN-CAT-CD       PIC 9(04)
   05 DALYTRAN-SOURCE       PIC X(10)
   05 DALYTRAN-DESC         PIC X(100)
   05 DALYTRAN-AMT          PIC S9(09)V99
   05 DALYTRAN-MERCHANT-ID  PIC 9(09)
   05 DALYTRAN-MERCHANT-NAME PIC X(50)
   05 DALYTRAN-MERCHANT-CITY PIC X(50)
   05 DALYTRAN-MERCHANT-ZIP  PIC X(10)
   05 DALYTRAN-CARD-NUM     PIC X(16)
   05 DALYTRAN-ORIG-TS      PIC X(26)
   05 DALYTRAN-PROC-TS      PIC X(26)
   05 FILLER                PIC X(20)
```

**Programs Referencing CVTRA06Y:** CBTRN01C, CBTRN02C (batch transaction processing programs)

**Confidence:** HIGH — directly observed in `app/cpy/CVTRA06Y.cpy` lines 4-18.

---

### 3.9 CVTRA01Y — Transaction Category Balance Record

**File:** `app/cpy/CVTRA01Y.cpy`  
**Root Record:** `TRAN-CAT-BAL-RECORD`  
**Record Length:** 50 bytes

Secondary index/summary VSAM record. Composite key: account ID + type code + category code. Used in batch statement processing and account update.

```
01 TRAN-CAT-BAL-RECORD.
   05 TRAN-CAT-KEY.
      10 TRANCAT-ACCT-ID    PIC 9(11)    -- Account ID (key component)
      10 TRANCAT-TYPE-CD    PIC X(02)    -- Transaction type code (key component)
      10 TRANCAT-CD         PIC 9(04)    -- Category code (key component)
   05 TRAN-CAT-BAL          PIC S9(09)V99  -- Running balance for this category
   05 FILLER                PIC X(22)
```

**Programs Referencing CVTRA01Y:** CBACT04C (batch), CBTRN02C (batch)

**Confidence:** HIGH — directly observed in `app/cpy/CVTRA01Y.cpy` lines 4-10.

---

### 3.10 CVTRA02Y — Disclosure Group Record

**File:** `app/cpy/CVTRA02Y.cpy`  
**Root Record:** `DIS-GROUP-RECORD`  
**Record Length:** 50 bytes

Interest rate lookup table record. Key: account group ID + transaction type code + transaction category code. Used in batch interest calculation.

```
01 DIS-GROUP-RECORD.
   05 DIS-GROUP-KEY.
      10 DIS-ACCT-GROUP-ID  PIC X(10)    -- Account group ID (from ACCT-GROUP-ID)
      10 DIS-TRAN-TYPE-CD   PIC X(02)    -- Transaction type code
      10 DIS-TRAN-CAT-CD    PIC 9(04)    -- Category code
   05 DIS-INT-RATE          PIC S9(04)V99  -- Interest rate for this group/type/category
   05 FILLER                PIC X(28)
```

**Programs Referencing CVTRA02Y:** CBACT04C (batch interest/disclosure calculation)

**Confidence:** HIGH — directly observed in `app/cpy/CVTRA02Y.cpy` lines 4-10.

---

### 3.11 CVTRA03Y — Transaction Type Record

**File:** `app/cpy/CVTRA03Y.cpy`  
**Root Record:** `TRAN-TYPE-RECORD`  
**Record Length:** 60 bytes

Transaction type lookup table record (VSAM file or DB2 table). Key: TRAN-TYPE (2-char code).

```
01 TRAN-TYPE-RECORD.
   05 TRAN-TYPE             PIC X(02)    -- Transaction type code (key)
   05 TRAN-TYPE-DESC        PIC X(50)    -- Description of transaction type
   05 FILLER                PIC X(08)
```

**Programs Referencing CVTRA03Y:** CBTRN03C (batch)

**Confidence:** HIGH — directly observed in `app/cpy/CVTRA03Y.cpy` lines 4-7.

---

### 3.12 CVTRA04Y — Transaction Category Record

**File:** `app/cpy/CVTRA04Y.cpy`  
**Root Record:** `TRAN-CAT-RECORD`  
**Record Length:** 60 bytes

Transaction category type lookup record. Composite key: type code + category code.

```
01 TRAN-CAT-RECORD.
   05 TRAN-CAT-KEY.
      10 TRAN-TYPE-CD       PIC X(02)    -- Transaction type (key)
      10 TRAN-CAT-CD        PIC 9(04)    -- Category code (key)
   05 TRAN-CAT-TYPE-DESC    PIC X(50)    -- Description
   05 FILLER                PIC X(04)
```

**Programs Referencing CVTRA04Y:** CBTRN03C (batch)

**Confidence:** HIGH — directly observed in `app/cpy/CVTRA04Y.cpy` lines 4-9.

---

### 3.13 CVTRA07Y — Daily Transaction Report Structures

**File:** `app/cpy/CVTRA07Y.cpy`  
**Root Records:** `REPORT-NAME-HEADER`, `TRANSACTION-DETAIL-REPORT`, `TRANSACTION-HEADER-1`, `TRANSACTION-HEADER-2`, `REPORT-PAGE-TOTALS`, `REPORT-ACCOUNT-TOTALS`, `REPORT-GRAND-TOTALS`

Report print-line structures for the batch daily transaction report. Defines literal header labels, formatted detail line, and subtotal/total accumulator lines with edited picture clauses (+ZZZ,ZZZ,ZZZ.ZZ).

**Programs Referencing CVTRA07Y:** CBTRN03C (batch report program)

**Confidence:** HIGH — directly observed in `app/cpy/CVTRA07Y.cpy` lines 4-66.

---

### 3.14 CVEXPORT — Multi-Entity Export Record

**File:** `app/cpy/CVEXPORT.cpy`  
**Root Record:** `EXPORT-RECORD`  
**Record Length:** 500 bytes  
**Version:** CardDemo_v2.0-44-gb6e9c27-254, 2025-10-16

Multi-record-type sequential export file layout. Uses REDEFINES to overlay a 460-byte data area with five entity-specific structures. This is the newer v2.0 copybook, the only one with an October 2025 timestamp.

```
01 EXPORT-RECORD.
   05 EXPORT-REC-TYPE         PIC X(1)      -- Record type discriminator
   05 EXPORT-TIMESTAMP        PIC X(26)     -- ISO timestamp
      05 EXPORT-TIMESTAMP-R REDEFINES ...
         10 EXPORT-DATE       PIC X(10)
         10 EXPORT-DATE-TIME-SEP PIC X(1)
         10 EXPORT-TIME       PIC X(15)
   05 EXPORT-SEQUENCE-NUM     PIC 9(9) COMP
   05 EXPORT-BRANCH-ID        PIC X(4)
   05 EXPORT-REGION-CODE      PIC X(5)
   05 EXPORT-RECORD-DATA      PIC X(460)    -- Overlaid by:
      05 EXPORT-CUSTOMER-DATA REDEFINES...  -- Customer fields (EXP-CUST-*)
      05 EXPORT-ACCOUNT-DATA  REDEFINES...  -- Account fields (EXP-ACCT-*)
      05 EXPORT-TRANSACTION-DATA REDEFINES... -- Transaction fields (EXP-TRAN-*)
      05 EXPORT-CARD-XREF-DATA REDEFINES... -- Card xref fields (EXP-XREF-*)
      05 EXPORT-CARD-DATA     REDEFINES...  -- Card fields (EXP-CARD-*)
```

**Programs Referencing CVEXPORT:** CBEXPORT (batch export), CBIMPORT (batch import)

**Confidence:** HIGH — directly observed in `app/cpy/CVEXPORT.cpy` lines 9-100.

---

### 3.15 COSTM01 — Statement Transaction Record

**File:** `app/cpy/COSTM01.CPY`  
**Root Record:** `TRNX-RECORD`

Batch statement transaction record with a composite KSDS key: card number + transaction ID. Used by the statement generation batch program.

```
01 TRNX-RECORD.
   05 TRNX-KEY.
      10 TRNX-CARD-NUM      PIC X(16)    -- Card number (key component 1)
      10 TRNX-ID            PIC X(16)    -- Transaction ID (key component 2)
   05 TRNX-REST.
      10 TRNX-TYPE-CD       PIC X(02)
      10 TRNX-CAT-CD        PIC 9(04)
      10 TRNX-SOURCE        PIC X(10)
      10 TRNX-DESC          PIC X(100)
      10 TRNX-AMT           PIC S9(09)V99
      10 TRNX-MERCHANT-ID   PIC 9(09)
      10 TRNX-MERCHANT-NAME PIC X(50)
      10 TRNX-MERCHANT-CITY PIC X(50)
      10 TRNX-MERCHANT-ZIP  PIC X(10)
      10 TRNX-ORIG-TS       PIC X(26)
      10 TRNX-PROC-TS       PIC X(26)
      10 FILLER             PIC X(20)
```

**Programs Referencing COSTM01:** CBSTM03A (batch statement program)

**Confidence:** HIGH — directly observed in `app/cpy/COSTM01.CPY` lines 20-37.

---

### 3.16 CUSTREC — Customer Record (Batch Variant)

**File:** `app/cpy/CUSTREC.cpy`  
**Root Record:** `CUSTOMER-RECORD`  
**Record Length:** 500 bytes

Near-duplicate of CVCUS01Y with one difference: the date-of-birth field is `CUST-DOB-YYYYMMDD` (8 characters, no hyphens) versus `CUST-DOB-YYYY-MM-DD` (10 characters with hyphens) in CVCUS01Y. Used exclusively by batch program CBSTM03A.

**Programs Referencing CUSTREC:** CBSTM03A

**Confidence:** HIGH — directly observed in `app/cpy/CUSTREC.cpy` lines 4-24.

---

### 3.17 CSDAT01Y — Date/Time Working Storage

**File:** `app/cpy/CSDAT01Y.cpy`  
**Root Record:** `WS-DATE-TIME`

Universal date/time working storage used by every online CICS program and some batch programs. Provides current date in multiple formats, current time, and a full ISO timestamp.

```
01 WS-DATE-TIME.
   05 WS-CURDATE-DATA.
      10 WS-CURDATE.
         15 WS-CURDATE-YEAR    PIC 9(04)
         15 WS-CURDATE-MONTH   PIC 9(02)
         15 WS-CURDATE-DAY     PIC 9(02)
      10 WS-CURDATE-N REDEFINES WS-CURDATE  PIC 9(08)
      10 WS-CURTIME.
         15 WS-CURTIME-HOURS   PIC 9(02)
         15 WS-CURTIME-MINUTE  PIC 9(02)
         15 WS-CURTIME-SECOND  PIC 9(02)
         15 WS-CURTIME-MILSEC  PIC 9(02)
      10 WS-CURTIME-N REDEFINES WS-CURTIME  PIC 9(08)
   05 WS-CURDATE-MM-DD-YY.  -- Formatted MM/DD/YY for screen display
   05 WS-CURTIME-HH-MM-SS.  -- Formatted HH:MM:SS for screen display
   05 WS-TIMESTAMP.         -- Full ISO-style YYYY-MM-DD HH:MM:SS.microseconds
```

**Programs Referencing CSDAT01Y:** COSGN00C, COMEN01C, COADM01C, COACTVWC, COACTUPC, COBIL00C, COCRDLIC, COCRDSLC, COCRDUPC, COTRN00C, COTRN01C, COTRN02C, CORPT00C, COUSR00C, COUSR01C, COUSR02C, COUSR03C, COPAUS0C, COPAUS1C, COTRTLIC, COTRTUPC (all online programs)

**Confidence:** HIGH — directly observed in `app/cpy/CSDAT01Y.cpy` lines 17-55.

---

### 3.18 CSMSG01Y — Common Screen Messages

**File:** `app/cpy/CSMSG01Y.cpy`  
**Root Record:** `CCDA-COMMON-MESSAGES`

Two-message structure providing standard screen messages used across all online programs.

```
01 CCDA-COMMON-MESSAGES.
   05 CCDA-MSG-THANK-YOU    PIC X(50) VALUE 'Thank you for using CardDemo application...'
   05 CCDA-MSG-INVALID-KEY  PIC X(50) VALUE 'Invalid key pressed. Please see below...'
```

**Programs Referencing CSMSG01Y:** All 17 online CICS programs (same list as CSDAT01Y)

**Confidence:** HIGH — directly observed in `app/cpy/CSMSG01Y.cpy` lines 17-23.

---

### 3.19 CSMSG02Y — Abend Work Area

**File:** `app/cpy/CSMSG02Y.cpy`  
**Root Record:** `ABEND-DATA`

Abend handling work area referenced in screen programs that detect unrecoverable conditions.

```
01 ABEND-DATA.
   05 ABEND-CODE     PIC X(4)   -- 4-char CICS abend code
   05 ABEND-CULPRIT  PIC X(8)   -- Program that caused the abend
   05 ABEND-REASON   PIC X(50)  -- Textual reason
   05 ABEND-MSG      PIC X(72)  -- Full formatted abend message
```

**Programs Referencing CSMSG02Y:** COACTUPC, COACTVWC, COCRDSLC, COCRDUPC, COPAUS0C, COPAUS1C, COTRTLIC, COTRTUPC

**Confidence:** HIGH — directly observed in `app/cpy/CSMSG02Y.cpy` lines 21-29.

---

### 3.20 CSUSR01Y — User Security Data

**File:** `app/cpy/CSUSR01Y.cpy`  
**Root Record:** `SEC-USER-DATA`  
**Record Length:** 80 bytes

User security record layout. This structure matches the VSAM security file record for user authentication.

```
01 SEC-USER-DATA.
   05 SEC-USR-ID      PIC X(08)    -- User ID (primary key, 8 characters)
   05 SEC-USR-FNAME   PIC X(20)    -- First name
   05 SEC-USR-LNAME   PIC X(20)    -- Last name
   05 SEC-USR-PWD     PIC X(08)    -- Password (8 characters, stored in clear)
   05 SEC-USR-TYPE    PIC X(01)    -- User type: 'A'=Admin, 'U'=User
   05 SEC-USR-FILLER  PIC X(23)
```

**Programs Referencing CSUSR01Y:** COSGN00C (auth), COADM01C, COMEN01C, COACTUPC, COACTVWC, COBIL00C, COCRDLIC, COCRDSLC, COCRDUPC, COUSR00C, COUSR01C, COUSR02C, COUSR03C, COPAUS0C, COTRN00C, COTRN01C, COTRN02C (virtually all online programs)

**Confidence:** HIGH — directly observed in `app/cpy/CSUSR01Y.cpy` lines 17-23.

---

### 3.21 COTTL01Y — Screen Title Constants

**File:** `app/cpy/COTTL01Y.cpy`  
**Root Record:** `CCDA-SCREEN-TITLE`

Screen title constants used in the header row of all BMS screens.

```
01 CCDA-SCREEN-TITLE.
   05 CCDA-TITLE01  PIC X(40) VALUE '      AWS Mainframe Modernization       '
   05 CCDA-TITLE02  PIC X(40) VALUE '              CardDemo                  '
   05 CCDA-THANK-YOU PIC X(40) VALUE 'Thank you for using CCDA application... '
```

**Programs Referencing COTTL01Y:** All online CICS programs (same list as CSDAT01Y)

**Confidence:** HIGH — directly observed in `app/cpy/COTTL01Y.cpy` lines 17-25.

---

### 3.22 CSSETATY — BMS Field Attribute Setting Snippet

**File:** `app/cpy/CSSETATY.cpy`

This is a PROCEDURE DIVISION inline code snippet, not a DATA DIVISION copybook. It is always used with COPY ... REPLACING to parameterize field names. The snippet sets a BMS field to red color if a validation flag indicates error or blank, and inserts an asterisk '*' if the field is blank.

```
(Parameterized snippet — with REPLACING TESTVAR1/SCRNVAR2/MAPNAME3)
IF (FLG-(TESTVAR1)-NOT-OK OR FLG-(TESTVAR1)-BLANK) AND CDEMO-PGM-REENTER
    MOVE DFHRED TO (SCRNVAR2)C OF (MAPNAME3)O
    IF FLG-(TESTVAR1)-BLANK
        MOVE '*' TO (SCRNVAR2)O OF (MAPNAME3)O
    END-IF
END-IF
```

**Programs Referencing CSSETATY:** COACTUPC (39 occurrences — one per validated field), COTRTUPC (1 occurrence), COPAUS0C (1 occurrence — via `CSSETATY REPLACING` at line 13580000)

**Confidence:** HIGH — directly observed in `app/cpy/CSSETATY.cpy` lines 17-27.

---

### 3.23 CSUTLDWY — Date Validation Working Storage

**File:** `app/cpy/CSUTLDWY.cpy` (also referenced as `'CSUTLDWY'` with quotes)

Working storage used in conjunction with the CSUTLDPY procedure copybook. Provides all date component fields, validation flags, and the date-validation-result structure for the CSUTLDTC utility call.

Key fields: `WS-EDIT-DATE-CCYYMMDD` (date input decomposed into CC/YY/MM/DD), validation flag fields (FLG-YEAR-*, FLG-MONTH-*, FLG-DAY-*), date format `WS-DATE-FORMAT`, and result structure `WS-DATE-VALIDATION-RESULT`.

**Programs Referencing CSUTLDWY:** COACTUPC (line 166), COTRTUPC (line 76)

**Confidence:** HIGH — directly observed in `app/cpy/CSUTLDWY.cpy` lines 4-86.

---

### 3.24 CSUTLDPY — Date Validation Paragraphs

**File:** `app/cpy/CSUTLDPY.cpy`

Procedure division copybook providing reusable date validation paragraphs. Paragraphs defined:
- `EDIT-DATE-CCYYMMDD` — Entry point, sets invalid state
- `EDIT-YEAR-CCYY` — Validates 4-digit year (century must be 19 or 20)
- `EDIT-MONTH` — Validates month (1-12)
- `EDIT-DAY` — Validates day (1-31)
- `EDIT-DAY-MONTH-YEAR` — Validates cross-field (31 days in correct months, leap year for Feb 29)
- `EDIT-DATE-LE` — Calls CSUTLDTC for final verification
- `EDIT-DATE-OF-BIRTH` — Validates DOB is not in the future

Note: The `EDIT-DATE-LE` paragraph performs `CALL 'CSUTLDTC'` (the date conversion utility program).

**Programs Referencing CSUTLDPY:** COACTUPC (line 4232)

**Confidence:** HIGH — directly observed in `app/cpy/CSUTLDPY.cpy` lines 18-371.

---

### 3.25 CSSTRPFY — String Processing Snippet

Referenced in: COCRDLIC (line 855), COACTVWC (line 913), COCRDUPC (line 1528), COACTUPC (line 4199), COTRTLIC (line 2060), COTRTUPC (line 1671)

**[ARTIFACT NOT AVAILABLE FOR INSPECTION: CSSTRPFY in app/cpy/]** This copybook is referenced with quoted syntax (`COPY 'CSSTRPFY'`) in procedure division sections of multiple online programs. It is a procedure division snippet, likely containing string manipulation or error-message formatting logic. The physical copybook was not found in any of the six analyzed directories.

**Confidence:** LOW — referenced 6 times across programs but source file not found in any analyzed directory.

---

### 3.26 COADM02Y — Admin Menu Option Table

**File:** `app/cpy/COADM02Y.cpy`  
**Root Record:** `CARDDEMO-ADMIN-MENU-OPTIONS`

Hardcoded admin menu option table with 6 options (expandable to 9 via OCCURS). Each option carries a number, display name, and target program name.

| Option | Description | Target Program |
|---|---|---|
| 1 | User List (Security) | COUSR00C |
| 2 | User Add (Security) | COUSR01C |
| 3 | User Update (Security) | COUSR02C |
| 4 | User Delete (Security) | COUSR03C |
| 5 | Transaction Type List/Update (Db2) | COTRTLIC |
| 6 | Transaction Type Maintenance (Db2) | COTRTUPC |

**Programs Referencing COADM02Y:** COADM01C

**Confidence:** HIGH — directly observed in `app/cpy/COADM02Y.cpy` lines 19-57.

---

### 3.27 COMEN02Y — Main User Menu Option Table

**File:** `app/cpy/COMEN02Y.cpy`  
**Root Record:** `CARDDEMO-MAIN-MENU-OPTIONS`

Hardcoded user menu option table with 11 options. Each option also carries a user-type indicator ('U' = regular user access).

| Option | Description | Target Program | User Type |
|---|---|---|---|
| 1 | Account View | COACTVWC | U |
| 2 | Account Update | COACTUPC | U |
| 3 | Credit Card List | COCRDLIC | U |
| 4 | Credit Card View | COCRDSLC | U |
| 5 | Credit Card Update | COCRDUPC | U |
| 6 | Transaction List | COTRN00C | U |
| 7 | Transaction View | COTRN01C | U |
| 8 | Transaction Add | COTRN02C | U |
| 9 | Transaction Reports | CORPT00C | U |
| 10 | Bill Payment | COBIL00C | U |
| 11 | Pending Authorization View | COPAUS0C | U |

**Programs Referencing COMEN02Y:** COMEN01C

**Confidence:** HIGH — directly observed in `app/cpy/COMEN02Y.cpy` lines 19-100.

---

### 3.28 CSLKPCDY — Phone/State/ZIP Lookup Tables

**File:** `app/cpy/CSLKPCDY.cpy`

Large validation table copybook (1319 lines) containing three lookup structures:
1. `WS-US-PHONE-AREA-CODE-TO-EDIT` — 88-level conditions for approximately 750 valid North American phone area codes, subdivided into `VALID-PHONE-AREA-CODE`, `VALID-GENERAL-PURP-CODE`, and `VALID-EASY-RECOG-AREA-CODE`.
2. `US-STATE-CODE-TO-EDIT` — 88-level condition `VALID-US-STATE-CODE` with all 50 US states + DC + territories (AS, GU, MP, PR, VI).
3. `US-STATE-ZIPCODE-TO-EDIT` — 88-level condition `VALID-US-STATE-ZIP-CD2-COMBO` matching state codes to first 2 ZIP digits.

**Programs Referencing CSLKPCDY:** COACTUPC (account update program uses all three validations)

**Confidence:** HIGH — directly observed in `app/cpy/CSLKPCDY.cpy` lines 23-1313.

---

### 3.29 CODATECN — Date Conversion Interface Record

**File:** `app/cpy/CODATECN.cpy`  
**Root Record:** `CODATECN-REC`

Interface record for the CODATECN date conversion utility. Supports two input formats (YYYYMMDD type=1, YYYY-MM-DD type=2) and two output formats.

```
01 CODATECN-REC.
   05 CODATECN-IN-REC.
      10 CODATECN-TYPE         PIC X     -- '1'=YYYYMMDD, '2'=YYYY-MM-DD
      10 CODATECN-INP-DATE     PIC X(20)
         REDEFINES for each format
   05 CODATECN-OUT-REC.
      10 CODATECN-OUTTYPE      PIC X     -- '1'=YYYY-MM-DD, '2'=YYYYMMDD
      10 CODATECN-0UT-DATE     PIC X(20)
         REDEFINES for each format
   05 CODATECN-ERROR-MSG       PIC X(38)
```

**Programs Referencing CODATECN:** CBACT01C (batch account file utility)

**Confidence:** HIGH — directly observed in `app/cpy/CODATECN.cpy` lines 17-52.

---

### 3.30 UNUSED1Y — Unused User Structure

**File:** `app/cpy/UNUSED1Y.cpy`  
**Root Record:** `UNUSED-DATA`

Mirrors the structure of CSUSR01Y exactly (ID 8, FNAME 20, LNAME 20, PWD 8, TYPE 1, FILLER 23). Version CardDemo_v1.0-56-gd8e5ebf-109 (2022-08-19). No program currently contains a `COPY UNUSED1Y` statement — this copybook is orphaned.

**Programs Referencing UNUSED1Y:** None found in any .cbl or .CBL file.

**Confidence:** HIGH (no references confirmed) — grep scan of all COBOL source files found zero matches.

---

### 3.31 BMS Screen Copybook Pattern

All BMS screen copybooks follow an identical structural pattern. Each defines:
- `xxxxAI` — Input map record (fields end in `L` for length, `F` for flag/attribute, `A` for attribute redefine, then `I` for input data)
- `xxxxAO REDEFINES xxxxAI` — Output map (same layout, fields end in `C` for color, `P` for print, `H` for hidden, `V` for value, then `O` for output data)

Standard header fields present in every map: TRNNAME (4), TITLE01 (40), CURDATE (8), PGMNAME (8), TITLE02 (40), CURTIME (8 or 9), then screen-specific fields.

The paired `L` (length COMP S9(4)) + `F`/`A` (attribute) + data pattern is the standard BMS symbolic map generated by assembler macros. The input/output overlay via REDEFINES is the canonical CICS BMS technique.

---

### 3.32 Authorization Subsystem IMS Copybooks

#### CIPAUDTY — Authorization Details IMS Segment

**File:** `app/app-authorization-ims-db2-mq/cpy/CIPAUDTY.cpy`

The primary IMS segment for pending authorization records. Key is composite: `PA-AUTH-DATE-9C` (COMP-3 5-digit) + `PA-AUTH-TIME-9C` (COMP-3 9-digit). Status field `PA-MATCH-STATUS` drives the authorization lifecycle (Pending, Declined, Expired, Matched). Fraud field `PA-AUTH-FRAUD` tracks fraud disposition.

**Programs Referencing CIPAUDTY:** COPAUS0C, COPAUS1C, COPAUA0C (CICS programs), CBPAUP0C (batch), PAUDBLOD.CBL, PAUDBUNL.CBL, DBUNLDGS.CBL (IMS batch programs), COPAUS2C

**Confidence:** HIGH — directly observed in `app/app-authorization-ims-db2-mq/cpy/CIPAUDTY.cpy` lines 19-55.

#### CIPAUSMY — Authorization Summary IMS Segment

**File:** `app/app-authorization-ims-db2-mq/cpy/CIPAUSMY.cpy`

Parent IMS segment (summary level) containing account-level authorization totals. Contains `PA-ACCT-ID` (COMP-3 S9(11)) and `PA-CUST-ID` as linkage to core entities, plus approved/declined counts and amounts.

**Programs Referencing CIPAUSMY:** COPAUS0C, COPAUS1C, COPAUA0C, CBPAUP0C, PAUDBLOD.CBL, PAUDBUNL.CBL, DBUNLDGS.CBL, COPAUS2C

**Confidence:** HIGH — directly observed in `app/app-authorization-ims-db2-mq/cpy/CIPAUSMY.cpy` lines 19-31.

#### IMS PCB Copybooks (PADFLPCB, PASFLPCB, PAUTBPCB)

Three PCB (Program Communication Block) structures for IMS DL/I access:
- `PADFLPCB.CPY` — PADFL PCB for authorization details (keyfb 255 bytes): PADFL-DBDNAME, PADFL-SEG-LEVEL, PADFL-PCB-STATUS, PADFL-PCB-PROCOPT, PADFL-SEG-NAME, PADFL-KEYFB-NAME, PADFL-NUM-SENSEGS, PADFL-KEYFB
- `PASFLPCB.CPY` — PASFL PCB for authorization summary (keyfb 100 bytes), same field pattern with PASFL- prefix
- `PAUTBPCB.CPY` — PAUT PCB for authorization table (keyfb 255 bytes), same field pattern with PAUT- prefix

**Programs Referencing PADFLPCB:** DBUNLDGS.CBL only  
**Programs Referencing PASFLPCB:** DBUNLDGS.CBL only  
**Programs Referencing PAUTBPCB:** PAUDBLOD.CBL, PAUDBUNL.CBL, DBUNLDGS.CBL

**Confidence:** HIGH — directly observed in respective .CPY files.

#### IMSFUNCS — IMS DL/I Function Code Constants

**File:** `app/app-authorization-ims-db2-mq/cpy/IMSFUNCS.cpy`

DL/I function code table. Defines constants for all standard IMS call functions: GU (Get Unique), GHU (Get Hold Unique), GN (Get Next), GHN (Get Hold Next), GNP (Get Next in Parent), GHNP (Get Hold Next in Parent), REPL (Replace), ISRT (Insert), DLET (Delete). Also defines `PARMCOUNT PIC S9(05) VALUE +4 COMP-5`.

**Programs Referencing IMSFUNCS:** PAUDBLOD.CBL, PAUDBUNL.CBL, DBUNLDGS.CBL

**Confidence:** HIGH — directly observed in `app/app-authorization-ims-db2-mq/cpy/IMSFUNCS.cpy` lines 17-27.

---

### 3.33 MQ Copybooks (External — Not In Analyzed Directories)

Programs COACCT01, CODATE01, COPAUA0C reference: CMQGMOV, CMQPMOV, CMQMDV, CMQODV, CMQV, CMQTML.

**[ARTIFACTS NOT AVAILABLE FOR INSPECTION: CMQGMOV, CMQPMOV, CMQMDV, CMQODV, CMQV, CMQTML]** These are IBM MQ API copybooks defining MQ message headers (MQMD = Message Descriptor), put/get message options (MQPMO, MQGMO), object descriptors (MQOD), and topic/message list structures. They are system-provided IBM MQ copybooks, not application-written. They are not present in any of the six analyzed directories.

**Confidence for identification:** MEDIUM — names are standard IBM MQ library copybook names (CMQV = constants, CMQMD = message descriptor, CMQPMO = put message options, etc.).

---

### 3.34 DB2 Utility Copybooks

#### CSDB2RWY — DB2 Working Storage

**File:** `app/app-transaction-type-db2/cpy/CSDB2RWY.cpy`

Working storage for DB2 operations. Provides: `WS-DISP-SQLCODE` (formatted SQLCODE display), `WS-DUMMY-DB2-INT` (COMP-3, used in connectivity check), `WS-DB2-PROCESSING-FLAG` (OK/ERROR indicator), `WS-DB2-CURRENT-ACTION` (72-char action description), DSNTIAC message buffer (10 lines × 72 chars), DSNTIAC error fields.

**Programs Referencing CSDB2RWY:** COTRTLIC (referenced as `COPY 'CSUTLDWY'.` at line 76 — note this appears to be a copy statement referencing this file by name), COTRTUPC

**Confidence:** HIGH — directly observed in `app/app-transaction-type-db2/cpy/CSDB2RWY.cpy` lines 37-47.

#### CSDB2RPY — DB2 Common Procedures

**File:** `app/app-transaction-type-db2/cpy/CSDB2RPY.cpy`

Procedure division copybook providing two paragraphs:
- `9998-PRIMING-QUERY` — Issues `SELECT 1 FROM SYSIBM.SYSDUMMY1` to verify DB2 connectivity
- `9999-FORMAT-DB2-MESSAGE` — Calls `DSNTIAC` utility to format SQLCA error messages into human-readable form

**Programs Referencing CSDB2RPY:** COTRTLIC, COTRTUPC

**Confidence:** HIGH — directly observed in `app/app-transaction-type-db2/cpy/CSDB2RPY.cpy` lines 177-208.

---

## 4. Copybook Usage Cross-Reference Matrix

### 4.1 Programs by Copybook (Most Shared First)

| Copybook | Programs (Count) |
|---|---|
| CSSETATY | COACTUPC(39), COTRTUPC(1), COPAUS0C(1) — 3 programs, 41 total usages |
| DFHBMSCA | All 17 online CICS programs (15 counts in grep), plus authorization/db2 subsystem programs |
| DFHAID | Same as DFHBMSCA |
| CSMSG01Y | COSGN00C, COMEN01C, COADM01C, COACTVWC, COACTUPC, COBIL00C, COCRDLIC, COCRDSLC, COCRDUPC, COTRN00C, COTRN01C, COTRN02C, CORPT00C, COUSR00C, COUSR01C, COUSR02C, COUSR03C, COPAUS0C, COPAUS1C, COTRTLIC, COTRTUPC — 21 programs |
| CSDAT01Y | Same 21 programs as CSMSG01Y |
| COTTL01Y | Same 21 programs |
| COCOM01Y | Same 21 programs |
| CSUSR01Y | COSGN00C + all 16 remaining online programs + COPAUS0C, COPAUS2C |
| CVACT01Y | CBACT01C, CBTRN01C, CBTRN02C, CBEXPORT, CBIMPORT, CBSTM03A, COACTUPC, COACTVWC, COBIL00C, COTRN02C, COPAUS0C, COPAUA0C, COACCT01 — 13 programs |
| CVACT03Y | CBACT03C, CBTRN01C, CBTRN02C, CBTRN03C, CBEXPORT, CBIMPORT, CBSTM03A, COACTUPC, COACTVWC, COTRN02C, COBIL00C, COPAUS0C, COPAUA0C — 13 programs |
| CVTRA05Y | CBTRN01C, CBTRN02C, CBTRN03C, CBEXPORT, CBIMPORT, CBSTM03A, COBIL00C, COTRN00C, COTRN01C, COTRN02C, CORPT00C, COTRTLIC — 12 programs |
| CVCUS01Y | CBCUS01C, CBEXPORT, CBIMPORT, CBTRN01C, COACTUPC, COACTVWC, COCRDUPC, COCRDSLC, COPAUS0C, COPAUA0C — 10 programs |
| CVCRD01Y | COCRDLIC, COCRDSLC, COCRDUPC, COACTUPC, COACTVWC, COTRTLIC, COTRTUPC — 7 programs |
| CVACT02Y | CBACT02C, CBEXPORT, CBIMPORT, COCRDSLC, COCRDLIC, COCRDUPC, COACTUPC, COACTVWC — 8 programs |
| CSMSG02Y | COACTUPC, COACTVWC, COCRDSLC, COCRDUPC, COPAUS0C, COPAUS1C, COTRTLIC, COTRTUPC — 8 programs |
| CIPAUDTY | COPAUS0C, COPAUS1C, COPAUA0C, CBPAUP0C, PAUDBLOD, PAUDBUNL, DBUNLDGS, COPAUS2C — 8 programs |
| CIPAUSMY | Same 8 programs as CIPAUDTY |
| CVTRA06Y | CBTRN01C, CBTRN02C — 2 programs |
| CVTRA01Y | CBACT04C, CBTRN02C — 2 programs |
| CVEXPORT | CBEXPORT, CBIMPORT — 2 programs |
| IMSFUNCS | PAUDBLOD, PAUDBUNL, DBUNLDGS — 3 programs |
| PAUTBPCB | PAUDBLOD, PAUDBUNL, DBUNLDGS — 3 programs |
| CSUTLDPY | COACTUPC — 1 program |
| CSUTLDWY | COACTUPC, COTRTUPC — 2 programs |
| CSLKPCDY | COACTUPC — 1 program |
| COADM02Y | COADM01C — 1 program |
| COMEN02Y | COMEN01C — 1 program |
| CODATECN | CBACT01C — 1 program |
| COSTM01 | CBSTM03A — 1 program |
| CUSTREC | CBSTM03A — 1 program |
| CVTRA02Y | CBACT04C — 1 program |
| CVTRA03Y | CBTRN03C — 1 program |
| CVTRA04Y | CBTRN03C — 1 program |
| CVTRA07Y | CBTRN03C — 1 program |
| UNUSED1Y | None — 0 programs |

---

## 5. Sharing Patterns Across Subsystems

### 5.1 Universal Infrastructure Layer (All Subsystems)

The following copybooks are used across the main online subsystem, the authorization subsystem, and the transaction-type DB2 subsystem:
- **COCOM01Y** — COMMAREA (cross-subsystem CICS state carrier)
- **CSDAT01Y** — Date/time WS
- **CSMSG01Y** — Common messages
- **COTTL01Y** — Screen titles
- **DFHAID** and **DFHBMSCA** — IBM CICS-provided AID and BMS attribute copybooks

### 5.2 Core Entity Layer (Batch + Online Shared)

The five entity copybooks (CVACT01Y, CVACT02Y, CVACT03Y, CVCUS01Y, CVTRA05Y) are shared between online CICS programs and batch programs, confirming that batch and online programs access the same VSAM files with the same record definitions.

### 5.3 Authorization Subsystem Isolation

The IMS-specific copybooks (CIPAUDTY, CIPAUSMY, IMSFUNCS, PADFLPCB, PASFLPCB, PAUTBPCB, CCPAUERY, CCPAURLY, CCPAURQY) are exclusively used within the `app/app-authorization-ims-db2-mq/` subsystem. They do not appear in any main `app/cbl/` program, confirming a clean subsystem boundary at the IMS/MQ layer.

### 5.4 DB2 Subsystem Isolation

The DB2 utility copybooks (CSDB2RWY, CSDB2RPY) and the transaction-type BMS maps (COTRTLI, COTRTUP) are exclusively used by programs in `app/app-transaction-type-db2/`. The entity copybooks CVCRD01Y and CVTRA05Y cross this boundary (referenced by COTRTLIC).

### 5.5 Batch-Exclusive Copybooks

COSTM01, CUSTREC, CVTRA02Y, CVTRA03Y, CVTRA04Y, CVTRA07Y, and CODATECN are used exclusively by batch programs.

---

## 6. Open Questions and Gaps

1. **CSSTRPFY not found** — Referenced by 6 programs but not present in any analyzed directory. This is likely a utility string-processing procedure stored in a different library path or a system-provided copybook.

2. **CMQ* MQ copybooks not found** — CMQGMOV, CMQPMOV, CMQMDV, CMQODV, CMQV, CMQTML are IBM MQ system copybooks referenced by COPAUA0C, COACCT01, and CODATE01. Expected to reside in IBM MQ installation libraries, not application PDS.

3. **DFHBMSCA and DFHAID** — IBM CICS system copybooks referenced by all online programs. Not present in application directories; expected in CICS MACLIB or SDFHCOB.

4. **CBSTM03B** — Listed in the cbl/ directory but no COPY statements were captured in grep output. Its copybook dependencies are unknown.

5. **COBSWAIT** — Similarly no COPY statements captured. Likely uses no application copybooks (pure CICS DELAY program).

6. **COBTUPDT** — Batch program in app-transaction-type-db2/cbl/ with no COPY statements captured. May use CSDB2RWY/CSDB2RPY or system-only copybooks.

7. **app-vsam-mq/cbl/** — Programs COACCT01 and CODATE01 reference only MQ system copybooks plus CVACT01Y. No application cpy/ directory exists for this subsystem — all other copybooks come from the main app/cpy/ directory.
