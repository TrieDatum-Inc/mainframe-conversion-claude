# CardDemo Application — Overall System Technical Specification

## 1. Executive Summary

**CardDemo** is an AWS Mainframe Modernization reference implementation simulating a complete **credit card management system**. It is built on Enterprise COBOL and spans five middleware technologies: CICS, VSAM, IMS DL/I, DB2, and IBM MQ. The application contains **45+ COBOL programs**, **21 BMS screens**, **40+ copybooks**, **35+ JCL jobs**, and supporting assembler, macro, and scheduler artifacts.

The system is organized into three sub-applications:
1. **Core Application** (CICS/VSAM) — Account, card, transaction, user, and billing management
2. **Authorization Sub-Application** (CICS/IMS/DB2/MQ) — Real-time card authorization processing
3. **Transaction Type Sub-Application** (CICS/DB2) — Reference data maintenance

---

## 2. Architecture Overview

### 2.1 Technology Stack

| Layer | Technology |
|-------|-----------|
| Online Transaction Processing | CICS TS |
| Screen Presentation | BMS (Basic Mapping Support) |
| Primary Data Storage | VSAM KSDS (8 master files + alternate indexes) |
| Hierarchical Database | IMS DL/I (authorization data) |
| Relational Database | DB2 (reference data, fraud records) |
| Message Queuing | IBM MQ (authorization requests, account/date services) |
| Batch Processing | JCL, SORT, IDCAMS, cataloged procedures |
| Job Scheduling | Control-M, CA7 |

### 2.2 Module Structure

```
CardDemo Application
├── Core Application (app/)
│   ├── 17 CICS online programs
│   ├── 15 batch programs
│   ├── 17 BMS screens
│   └── 8 VSAM master files
├── Authorization Sub-App (app/app-authorization-ims-db2-mq/)
│   ├── 3 CICS online programs
│   ├── 5 batch programs
│   ├── 2 BMS screens
│   ├── 1 IMS database (DBPAUTP0)
│   └── 1 DB2 table (AUTHFRDS)
├── Transaction Type Sub-App (app/app-transaction-type-db2/)
│   ├── 2 CICS online programs
│   ├── 1 batch program
│   ├── 2 BMS screens
│   └── 2 DB2 tables (TRANSACTION_TYPE, TRANSACTION_TYPE_CATEGORY)
└── VSAM/MQ Services (app/app-vsam-mq/)
    └── 2 CICS MQ service programs
```

---

## 3. Application Navigation Flow

```
COSGN00C (CC00) — Sign-On Screen
   |
   ├── [Admin User] → COADM01C (CA00) — Admin Menu
   │                    ├── 01: COUSR00C (CU00) — User List
   │                    │       ├── 'U' → COUSR02C (CU02) — Update User
   │                    │       └── 'D' → COUSR03C (CU03) — Delete User
   │                    ├── 02: COUSR01C (CU01) — Add User
   │                    ├── 03: COUSR02C (CU02) — Update User
   │                    ├── 04: COUSR03C (CU03) — Delete User
   │                    ├── 05: COTRTLIC (CTLI) — Transaction Type List
   │                    │       └── → COTRTUPC (CTTU) — Transaction Type Add/Update
   │                    └── 06: COTRTUPC (CTTU) — Transaction Type Maintenance
   │
   └── [Regular User] → COMEN01C (CM00) — Main Menu
                          ├── 01: COACTVWC (CAVW) — Account View
                          ├── 02: COACTUPC (CAUP) — Account Update
                          ├── 03: COCRDLIC (CCLI) — Credit Card List
                          │       ├── 'S' → COCRDSLC (CCDL) — Card Detail
                          │       └── 'U' → COCRDUPC (CCUP) — Card Update
                          ├── 04: COCRDSLC (CCDL) — Credit Card View
                          ├── 05: COCRDUPC (CCUP) — Credit Card Update
                          ├── 06: COTRN00C (CT00) — Transaction List
                          │       └── 'S' → COTRN01C (CT01) — View Transaction
                          ├── 07: COTRN01C (CT01) — Transaction View
                          ├── 08: COTRN02C (CT02) — Add Transaction
                          ├── 09: CORPT00C (CR00) — Transaction Reports
                          ├── 10: COBIL00C (CB00) — Bill Payment
                          └── 11: COPAUS0C (CPVS) — Pending Authorization View
                                  └── 'S' → COPAUS1C (CPVD) — Authorization Detail
                                            └── F5 → COPAUS2C (LINK) — Fraud Action
```

---

## 4. CICS Transaction-to-Program Mapping

| Trans ID | Program | BMS Mapset | Description |
|----------|---------|------------|-------------|
| CC00 | COSGN00C | COSGN00 | Sign-on |
| CM00 | COMEN01C | COMEN01 | Regular user menu |
| CA00 | COADM01C | COADM01 | Admin menu |
| CU00 | COUSR00C | COUSR00 | User list |
| CU01 | COUSR01C | COUSR01 | Add user |
| CU02 | COUSR02C | COUSR02 | Update user |
| CU03 | COUSR03C | COUSR03 | Delete user |
| CT00 | COTRN00C | COTRN00 | Transaction list |
| CT01 | COTRN01C | COTRN01 | View transaction |
| CT02 | COTRN02C | COTRN02 | Add transaction |
| CB00 | COBIL00C | COBIL00 | Bill payment |
| CR00 | CORPT00C | CORPT00 | Report request |
| CAVW | COACTVWC | COACTVW | Account view |
| CAUP | COACTUPC | COACTUP | Account update |
| CCLI | COCRDLIC | COCRDLI | Card list |
| CCDL | COCRDSLC | COCRDSL | Card detail |
| CCUP | COCRDUPC | COCRDUP | Card update |
| CTLI | COTRTLIC | COTRTLI | Transaction type list (DB2) |
| CTTU | COTRTUPC | COTRTUP | Transaction type update (DB2) |
| CP00 | COPAUA0C | — | Authorization engine (MQ-driven) |
| CPVS | COPAUS0C | COPAU00 | Authorization summary view |
| CPVD | COPAUS1C | COPAU01 | Authorization detail view |

---

## 5. Data Model

### 5.1 VSAM Master Files

| Dataset | DD Name | Key | LRECL | Description |
|---------|---------|-----|-------|-------------|
| USRSEC | USRSEC | SEC-USR-ID X(8) | 80 | User security records |
| ACCTDATA | ACCTDAT | ACCT-ID 9(11) | 300 | Account master |
| CARDDATA | CARDDAT | CARD-NUM X(16) | 150 | Credit card records |
| CARDXREF | CCXREF | XREF-CARD-NUM X(16) | 50 | Card-to-account cross-reference |
| CUSTDATA | CUSTDAT | CUST-ID 9(9) | 500 | Customer demographics |
| TRANSACT | TRANSACT | TRAN-ID X(16) | 350 | Transaction records |
| TCATBALF | TCATBALF | Composite 17-byte | 50 | Transaction category balances |
| DISCGRP | DISCGRP | Composite 16-byte | 50 | Discount/interest group rates |

### 5.2 Alternate Indexes

| AIX Path | Base File | AIX Key | Purpose |
|----------|-----------|---------|---------|
| CARDAIX | CARDDATA | CARD-ACCT-ID 9(11) | Browse cards by account |
| CXACAIX | CARDXREF | XREF-ACCT-ID 9(11) | Look up xref by account |

### 5.3 Entity Relationship Diagram

```
CUSTOMER (CUST-ID 9(9))
    |
    | 1:N
    v
CARD-XREF (XREF-CARD-NUM X(16))
    |-- XREF-CUST-ID → CUSTOMER
    |-- XREF-ACCT-ID → ACCOUNT
    |
    v
ACCOUNT (ACCT-ID 9(11))           CARD (CARD-NUM X(16))
    |-- ACCT-GROUP-ID → DISCGRP       |-- CARD-ACCT-ID → ACCOUNT
    |
    | 1:N (via TRAN-CARD-NUM)
    v
TRANSACTION (TRAN-ID X(16))
    |-- TRAN-TYPE-CD → TRAN-TYPE (CVTRA03Y)
    |-- TRAN-CAT-CD → TRAN-CAT (CVTRA04Y)
    |
    v
TRAN-CAT-BAL (ACCT-ID + TYPE-CD + CAT-CD)
    |
    v
DIS-GROUP (GROUP-ID + TYPE-CD + CAT-CD)
    |-- DIS-INT-RATE → interest rate for this group/type/category
```

### 5.4 IMS Database (Authorization)

```
DBPAUTP0 (HIDAM/VSAM)
└── PAUTSUM0 (Root, 100 bytes)
    Key: ACCNTID (packed decimal 6 bytes)
    Fields: credit limits, balances, auth counts/amounts
    │
    └── PAUTDTL1 (Child, 200 bytes)
        Key: PAUT9CTS (date+time as 9-complement COMP-3)
        Fields: card, auth type, amounts, merchant, response, fraud status
```

### 5.5 DB2 Tables

| Table | Primary Key | Module |
|-------|------------|--------|
| CARDDEMO.TRANSACTION_TYPE | TR_TYPE CHAR(2) | Transaction Type Sub-App |
| CARDDEMO.TRANSACTION_TYPE_CATEGORY | TR_TYPE + TR_CAT | Transaction Type Sub-App |
| CARDDEMO.AUTHFRDS | CARD_NUM CHAR(16) + AUTH_TS TIMESTAMP | Authorization Sub-App |

---

## 6. Inter-Program Communication

### 6.1 COMMAREA (COCOM01Y)

All CICS programs share a common CARDDEMO-COMMAREA containing:

| Section | Key Fields |
|---------|------------|
| General Info | FROM-TRANID, FROM-PROGRAM, TO-TRANID, TO-PROGRAM, USER-ID, USER-TYPE, PGM-CONTEXT |
| Customer Info | CUST-ID, CUST-FNAME/MNAME/LNAME |
| Account Info | ACCT-ID, ACCT-STATUS |
| Card Info | CARD-NUM |
| Navigation | LAST-MAP, LAST-MAPSET |

### 6.2 Program Interaction Patterns

| Pattern | Programs Using | Description |
|---------|---------------|-------------|
| Menu Dispatch | COMEN01C, COADM01C | Data-driven XCTL from menu arrays |
| Paginated Browse | COUSR00C, COTRN00C, COCRDLIC, COTRTLIC, COPAUS0C | 7-10 rows per page, F7/F8 paging |
| Two-Phase Fetch-Edit | COUSR02C, COUSR03C, COBIL00C, COTRN02C | ENTER fetches, PF5 commits |
| CALL Subroutine | CSUTLDTC, CBSTM03B, COBSWAIT | CALL/USING for shared utilities |
| LINK (Return) | COPAUS2C | LINK from COPAUS1C, returns with status |
| MQ Request/Reply | COPAUA0C, COACCT01, CODATE01 | MQGET/MQPUT messaging pattern |
| TDQ Job Submit | CORPT00C | Write JCL to TDQ JOBS for batch submission |

---

## 7. Batch Processing

### 7.1 Daily Transaction Processing Chain

```
Step 1: CLOSEFIL    — Close CICS files for batch access
Step 2: POSTTRAN    — CBTRN02C: Validate and post daily transactions
                      Input: DALYTRAN.PS → Output: TRANSACT, ACCTDATA, TCATBALF, DALYREJS(+1)
Step 3: WAITSTEP    — COBSWAIT: Controlled delay
Step 4: OPENFIL     — Reopen CICS files
```

### 7.2 Monthly Processing Chain

```
Step 1: CLOSEFIL    — Close CICS files
Step 2: INTCALC     — CBACT04C: Compute interest/fees
                      Input: TCATBALF, DISCGRP → Output: SYSTRAN(+1), updated ACCTDATA
Step 3: COMBTRAN    — SORT merge TRANSACT.BKUP + SYSTRAN → TRANSACT.COMBINED
                      IDCAMS REPRO COMBINED → TRANSACT.VSAM.KSDS
Step 4: WAITSTEP    — Controlled delay
Step 5: OPENFIL     — Reopen CICS files
```

### 7.3 Report Generation

```
TRANREPT Procedure (3 steps):
  1. REPROC: Backup TRANSACT → TRANSACT.BKUP(+1)
  2. SORT: Filter by date range, sort by card number → TRANSACT.DALY(+1)
  3. CBTRN03C: Generate 133-byte report → TRANREPT(+1)
```

### 7.4 Statement Generation

```
CREASTMT Job:
  1. SORT: Rekey TRANSACT by card number → TRXFL.SEQ
  2. REPRO → TRXFL.VSAM.KSDS
  3. CBSTM03A (calls CBSTM03B): Generate statements
     → STATEMNT.PS (text) + STATEMNT.HTML
```

### 7.5 Reference Data Refresh (Weekly)

```
TRANEXTR Job:
  1. Backup current TRANTYPE.PS and TRANCATG.PS
  2. DSNTIAUL: Extract DB2 TRANSACTION_TYPE → TRANTYPE.PS
  3. DSNTIAUL: Extract DB2 TRANSACTION_TYPE_CATEGORY → TRANCATG.PS
  4. Reload into VSAM (via separate jobs)
```

### 7.6 Data Migration

```
CBEXPORT: Read 5 VSAM files → 500-byte multi-type EXPFILE KSDS
CBIMPORT: Read EXPFILE → 5 normalized output files + ERROUT
```

### 7.7 Job Scheduling (Control-M)

| Schedule | Frequency | Job Chain |
|----------|-----------|-----------|
| DAILY-TransactionBackup | Daily | CLOSEFIL → TRANBKP → WAITSTEP → OPENFIL |
| WEEKLY-DisclosureGroups | Saturday | CLOSEFIL → DISCGRP → WAITSTEP → OPENFIL |
| WEEKLY-TransactionTypes | Saturday | TRANEXTR |
| MONTHLY-InterestCalc | Monthly | CLOSEFIL → INTCALC → COMBTRAN → WAITSTEP → OPENFIL |

---

## 8. BMS Screen Architecture

### 8.1 Design Patterns

| Pattern | Description |
|---------|-------------|
| Universal Header | Rows 1-2: Tran ID, Program, Title, Date, Time (all screens) |
| Error Message | Row 23, col 1, 78 chars, ASKIP,BRT,FSET,RED (all screens) |
| Function Key Legend | Row 24, initially NORM or DRK (revealed dynamically) |
| Y/N Confirmation | Single-char CONFIRM field + "(Y/N)" hint |
| Paginated List | PAGENUM field, per-row SEL fields, F7/F8 navigation |
| Two-Phase Fetch-Edit | ENTER=Fetch, F5=Save/Delete |
| Dynamic Function Keys | DRK fields revealed programmatically based on context |

### 8.2 Screen Inventory

| # | Mapset | Title | Domain | Input Fields | Output Fields |
|---|--------|-------|--------|--------------|---------------|
| 1 | COSGN00 | Sign-On | Auth | USERID, PASSWD | Header, ERRMSG |
| 2 | COMEN01 | Main Menu | Nav | OPTION(2) | 12 menu options |
| 3 | COADM01 | Admin Menu | Nav | OPTION(2) | 12 menu options |
| 4 | COTRN00 | List Transactions | Txn | TRNIDIN, 10×SEL | 10 rows×4 cols |
| 5 | COTRN01 | View Transaction | Txn | TRNIDIN | 13 detail fields |
| 6 | COTRN02 | Add Transaction | Txn | 14 fields + CONFIRM | — |
| 7 | COBIL00 | Bill Payment | Billing | ACTIDIN, CONFIRM | CURBAL |
| 8 | CORPT00 | Transaction Reports | Reporting | 10 fields + CONFIRM | — |
| 9 | COACTVW | View Account | Acct | ACCTSID | 23 detail fields |
| 10 | COACTUP | Update Account | Acct | 30+ editable fields | — |
| 11 | COCRDSL | View Card Detail | Cards | ACCTSID, CARDSID | Card info |
| 12 | COCRDLI | List Credit Cards | Cards | ACCTSID, CARDSID, 7×SEL | 7 rows |
| 13 | COCRDUP | Update Card | Cards | 5 editable fields | ACCTSID (prot) |
| 14 | COUSR00 | List Users | Users | USRIDIN, 10×SEL | 10 rows×4 cols |
| 15 | COUSR01 | Add User | Users | 5 fields | — |
| 16 | COUSR02 | Update User | Users | 5 fields | — |
| 17 | COUSR03 | Delete User | Users | USRIDIN | 3 read-only fields |
| 18 | COTRTLI | Tran Type List | Ref Data | TRTYPE, TRDESC, 7×SEL | 7 rows |
| 19 | COTRTUP | Tran Type Update | Ref Data | TRTYPCD, TRTYDSC | Dynamic FK |
| 20 | COPAU00 | Auth Summary | Auth | ACCTID, 4×SEL | Summary + 5 rows |
| 21 | COPAU01 | Auth Detail | Auth | — | 20 detail fields |

---

## 9. Shared Copybook Summary

### 9.1 Entity Record Layouts

| Copybook | Structure | Size | Key | Used By |
|----------|-----------|------|-----|---------|
| CVACT01Y | ACCOUNT-RECORD | 300 | ACCT-ID 9(11) | 16+ programs |
| CVACT02Y | CARD-RECORD | 150 | CARD-NUM X(16) | 12+ programs |
| CVACT03Y | CARD-XREF-RECORD | 50 | XREF-CARD-NUM X(16) | Most programs |
| CVCUS01Y | CUSTOMER-RECORD | 500 | CUST-ID 9(9) | 10+ programs |
| CVTRA05Y | TRAN-RECORD | 350 | TRAN-ID X(16) | 11+ programs |
| CVTRA06Y | DALYTRAN-RECORD | 350 | DALYTRAN-ID X(16) | CBTRN01C, CBTRN02C |
| CVTRA01Y | TRAN-CAT-BAL-RECORD | 50 | Composite 17-byte | Batch programs |
| CVTRA02Y | DIS-GROUP-RECORD | 50 | Composite 16-byte | CBACT04C |
| CVTRA03Y | TRAN-TYPE-RECORD | 60 | TRAN-TYPE X(2) | CBTRN03C, COTRTLIC |
| CVTRA04Y | TRAN-CAT-RECORD | 60 | TYPE-CD + CAT-CD | CBTRN03C |
| CSUSR01Y | SEC-USER-DATA | 80 | SEC-USR-ID X(8) | Auth programs |
| CVEXPORT | EXPORT-RECORD | 500 | Sequence# | CBEXPORT, CBIMPORT |

### 9.2 Infrastructure Copybooks

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA (all CICS programs) |
| CVCRD01Y | Screen navigation state (AID keys, next program/map) |
| COMEN02Y | Regular user menu options (11 entries) |
| COADM02Y | Admin menu options (6 entries) |
| CSDAT01Y | Date/time working storage |
| COTTL01Y | Application title strings |
| CSMSG01Y | Common screen messages |
| CSMSG02Y | Abend/error diagnostic data |
| CSSTRPFY | PF-key mapping paragraph |
| CSSETATY | Field error highlighting (COPY REPLACING) |
| CSUTLDWY | Date validation working storage |
| CSUTLDPY | Date validation procedure paragraphs |
| CSLKPCDY | Lookup tables (phone area codes, states, zip codes) |
| CODATECN | Date conversion interface for COBDATFT assembler |

### 9.3 IMS/MQ Copybooks

| Copybook | Purpose |
|----------|---------|
| CIPAUSMY | IMS summary segment (PAUTSUM0) |
| CIPAUDTY | IMS detail segment (PAUTDTL1) |
| CCPAURQY | MQ authorization request message |
| CCPAURLY | MQ authorization response message |
| CCPAUERY | Error log record |
| IMSFUNCS | IMS DL/I function code constants |
| CSDB2RWY | DB2 common working storage |
| CSDB2RPY | DB2 common procedure paragraphs |

---

## 10. End-to-End Transaction Flows

### 10.1 User Login Flow

```
Terminal → CC00 → COSGN00C
  → READ USRSEC (user/password validation)
  → If Admin: XCTL → COADM01C (CA00)
  → If User: XCTL → COMEN01C (CM00)
```

### 10.2 Account Inquiry Flow

```
COMEN01C → Option 01 → XCTL → COACTVWC (CAVW)
  → READ ACCTDAT (account data)
  → READ CUSTDAT (customer data by ACCT-CUSTID)
  → Browse CARDAIX (cards for account)
  → Display 23 fields on screen
  → F3: XCTL → COMEN01C
```

### 10.3 Credit Card Update Flow

```
COMEN01C → Option 05 → XCTL → COCRDUPC (CCUP)
  → ENTER: READ CARDDAT with UPDATE
  → Display card fields (name, status, expiry)
  → User edits fields
  → F5: Validate (month 1-12, year 1950-2099, status Y/N)
  → REWRITE CARDDAT
  → F3: XCTL → COCRDLIC or COMEN01C
```

### 10.4 Add Transaction Flow

```
COMEN01C → Option 08 → XCTL → COTRN02C (CT02)
  → User enters Account# or Card# + transaction details
  → READ CXACAIX/CCXREF (resolve account↔card)
  → CALL CSUTLDTC (validate dates)
  → Validate amount format, merchant ID
  → CONFIRM='Y': 
    → STARTBR HIGH-VALUES → READPREV → max TRAN-ID + 1
    → WRITE to TRANSACT
  → Display success message
```

### 10.5 Bill Payment Flow

```
COMEN01C → Option 10 → XCTL → COBIL00C (CB00)
  → Enter Account ID
  → READ ACCTDAT with UPDATE (get balance)
  → Display balance, prompt Y/N
  → CONFIRM='Y':
    → READ CXACAIX (get card for account)
    → Generate new TRAN-ID (max+1)
    → Build payment transaction (type='02', cat=2, full balance)
    → WRITE to TRANSACT
    → COMPUTE balance = 0
    → REWRITE ACCTDAT
```

### 10.6 Authorization Processing Flow

```
POS Terminal → MQ Request Queue → COPAUA0C (CP00)
  → MQGET request message
  → READ VSAM: ACCTDAT, CUSTDAT, CARDDAT, CCXREF
  → Evaluate: funds, card active, account open, fraud flags
  → Calculate: available = credit_limit - balance - pending_approved
  → IMS ISRT: PAUTSUM0 (summary) + PAUTDTL1 (detail)
  → Build response: auth code, approved/declined, amount
  → MQPUT reply message
  
Operator → COPAUS0C (CPVS) — Browse authorizations by account
  → IMS GN PAUTSUM0 + GNP PAUTDTL1
  → Select record → XCTL → COPAUS1C (CPVD) — Detail view
  → F5: LINK → COPAUS2C — DB2 INSERT/UPDATE AUTHFRDS (fraud)
  
Nightly → CBPAUP0C (BMP) — Purge expired records
  → IMS GN/GNP → DLET expired details → DLET empty summaries
```

### 10.7 Daily Batch Processing Flow

```
DALYTRAN.PS (raw daily feed)
    ↓
CBTRN02C — Post transactions
    → Validate: XREFFILE lookup, ACCTFILE lookup, dup check
    → Valid: WRITE TRANSACT, REWRITE ACCTDAT (balance), REWRITE/WRITE TCATBALF
    → Invalid: WRITE DALYREJS(+1)
    ↓
CBACT04C — Compute interest (monthly)
    → READ TCATBALF, DISCGRP (lookup rate), ACCTFILE
    → Compute interest per category
    → WRITE system transactions → SYSTRAN(+1)
    ↓
COMBTRAN — Merge
    → SORT TRANSACT.BKUP + SYSTRAN → COMBINED
    → REPRO COMBINED → TRANSACT.VSAM.KSDS
    ↓
CBTRN03C — Report (via TRANREPT procedure)
    → Read sorted/filtered transactions
    → Join TRANTYPE, TRANCATG descriptions
    → Write 133-byte report → TRANREPT(+1) GDG
    ↓
CBSTM03A — Statements (via CREASTMT job)
    → Read transactions by card (via CBSTM03B)
    → Join customer, account data
    → Write STATEMNT.PS (text) + STATEMNT.HTML
```

### 10.8 Report Submission Flow (Online → Batch)

```
COMEN01C → Option 09 → XCTL → CORPT00C (CR00)
  → User selects Monthly/Yearly/Custom + date range
  → CALL CSUTLDTC (validate dates if custom)
  → CONFIRM='Y':
    → SUBMIT-JOB-TO-INTRDR:
      → Loop through JOB-DATA (WS literal JCL array)
      → EXEC CICS WRITEQ TD('JOBS') each 80-byte line
      → JCL runs TRANREPT procedure in batch
```

---

## 11. File Access Matrix

| Program | USRSEC | ACCTDAT | CARDDAT | CCXREF | CXACAIX | CARDAIX | CUSTDAT | TRANSACT | TCATBALF | DISCGRP |
|---------|--------|---------|---------|--------|---------|---------|---------|----------|----------|---------|
| COSGN00C | R | | | | | | | | | |
| COUSR00C | R | | | | | | | | | |
| COUSR01C | W | | | | | | | | | |
| COUSR02C | RW | | | | | | | | | |
| COUSR03C | RD | | | | | | | | | |
| COTRN00C | | | | | | | | R(browse) | | |
| COTRN01C | | | | | | | | R | | |
| COTRN02C | | | | R | R | | | W | | |
| COBIL00C | | RW | | | R | | | W | | |
| COACTVWC | | R | R | | R | R(browse) | R | | | |
| COACTUPC | | RW | | | R | R(browse) | RW | | | |
| COCRDLIC | | | R(browse) | | | R(browse) | | | | |
| COCRDSLC | | | R | | | | | | | |
| COCRDUPC | | | RW | | | | | | | |
| CBTRN02C | | RW | | R | | | | W | RW | |
| CBACT04C | | RW | | | | | | W | R | R |
| CBTRN03C | | | | R | | | | R | | |

*R=Read, W=Write, RW=Read+Write, RD=Read+Delete*

---

## 12. Known Issues and Observations

| Issue | Program | Description |
|-------|---------|-------------|
| Unnecessary UPDATE lock | COTRN01C | Reads TRANSACT with UPDATE flag but never REWRITE/DELETE — view-only screen holds VSAM lock |
| Race condition | COTRN02C, COBIL00C | Transaction ID generation (max+1) has no locking — concurrent tasks could generate duplicate IDs |
| Hardcoded test data | CBACT01C | When ACCT-CURR-CYC-DEBIT=0, substitutes 2525.00 — test default |
| Incomplete program | DBUNLDGS | PSB-NAME and PCB-OFFSET are commented out; FILE-CONTROL section is commented out; not production-ready |
| Spelling typo | CVACT01Y, CVACT02Y | Field name `ACCT-EXPIRAION-DATE` and `CARD-EXPIRAION-DATE` — "EXPIRATION" misspelled |

---

## 13. Document Index

### Program Technical Specifications
| Document | Program |
|----------|---------|
| [COSGN00C_tech_spec.md](COSGN00C_tech_spec.md) | Sign-On Screen |
| [COMEN01C_tech_spec.md](COMEN01C_tech_spec.md) | Regular User Main Menu |
| [COADM01C_tech_spec.md](COADM01C_tech_spec.md) | Admin Menu |
| [COUSR00C_tech_spec.md](COUSR00C_tech_spec.md) | User List (Browse) |
| [COUSR01C_tech_spec.md](COUSR01C_tech_spec.md) | Add User |
| [COUSR02C_tech_spec.md](COUSR02C_tech_spec.md) | Update User |
| [COUSR03C_tech_spec.md](COUSR03C_tech_spec.md) | Delete User |
| [COTRN00C_tech_spec.md](COTRN00C_tech_spec.md) | Transaction List |
| [COTRN01C_tech_spec.md](COTRN01C_tech_spec.md) | View Transaction |
| [COTRN02C_tech_spec.md](COTRN02C_tech_spec.md) | Add Transaction |
| [COBIL00C_tech_spec.md](COBIL00C_tech_spec.md) | Bill Payment |
| [CORPT00C_tech_spec.md](CORPT00C_tech_spec.md) | Transaction Reports |
| [COACTVWC_tech_spec.md](COACTVWC_tech_spec.md) | View Account |
| [COACTUPC_tech_spec.md](COACTUPC_tech_spec.md) | Update Account |
| [COCRDLIC_tech_spec.md](COCRDLIC_tech_spec.md) | Credit Card List |
| [COCRDSLC_tech_spec.md](COCRDSLC_tech_spec.md) | Credit Card Detail |
| [COCRDUPC_tech_spec.md](COCRDUPC_tech_spec.md) | Update Credit Card |
| [COPAUA0C_tech_spec.md](COPAUA0C_tech_spec.md) | Authorization Engine |
| [COPAUS0C_tech_spec.md](COPAUS0C_tech_spec.md) | Authorization Summary View |
| [COPAUS1C_tech_spec.md](COPAUS1C_tech_spec.md) | Authorization Detail View |
| [COPAUS2C_tech_spec.md](COPAUS2C_tech_spec.md) | Fraud Mark/Remove |
| [CBPAUP0C_tech_spec.md](CBPAUP0C_tech_spec.md) | Expired Auth Purge |
| [COTRTLIC_tech_spec.md](COTRTLIC_tech_spec.md) | Transaction Type List (DB2) |
| [COTRTUPC_tech_spec.md](COTRTUPC_tech_spec.md) | Transaction Type Update (DB2) |
| [COBTUPDT_tech_spec.md](COBTUPDT_tech_spec.md) | Batch Tran Type Maintenance |
| [COACCT01_tech_spec.md](COACCT01_tech_spec.md) | Account MQ Service |
| [CODATE01_tech_spec.md](CODATE01_tech_spec.md) | Date MQ Service |
| [CBACT01C_tech_spec.md](CBACT01C_tech_spec.md) | Account File Extract |
| [CBACT02C_tech_spec.md](CBACT02C_tech_spec.md) | Card File Dump |
| [CBACT03C_tech_spec.md](CBACT03C_tech_spec.md) | Card Xref Dump |
| [CBACT04C_tech_spec.md](CBACT04C_tech_spec.md) | Interest Calculator |
| [CBCUS01C_tech_spec.md](CBCUS01C_tech_spec.md) | Customer File Dump |
| [CBTRN01C_tech_spec.md](CBTRN01C_tech_spec.md) | Transaction Validation |
| [CBTRN02C_tech_spec.md](CBTRN02C_tech_spec.md) | Transaction Posting |
| [CBTRN03C_tech_spec.md](CBTRN03C_tech_spec.md) | Transaction Report |
| [CBSTM03A_tech_spec.md](CBSTM03A_tech_spec.md) | Statement Generator |
| [CBSTM03B_tech_spec.md](CBSTM03B_tech_spec.md) | Statement File I/O |
| [CBEXPORT_tech_spec.md](CBEXPORT_tech_spec.md) | Data Export |
| [CBIMPORT_tech_spec.md](CBIMPORT_tech_spec.md) | Data Import |
| [CSUTLDTC_tech_spec.md](CSUTLDTC_tech_spec.md) | Date Validation |
| [COBSWAIT_tech_spec.md](COBSWAIT_tech_spec.md) | Wait Utility |
| [PAUDBUNL_tech_spec.md](PAUDBUNL_tech_spec.md) | IMS Database Unload |
| [PAUDBLOD_tech_spec.md](PAUDBLOD_tech_spec.md) | IMS Database Load |
| [DBUNLDGS_tech_spec.md](DBUNLDGS_tech_spec.md) | IMS Unload Template |

### BMS Screen Technical Specifications
| Document | Screen |
|----------|--------|
| [BMS_COSGN00_tech_spec.md](BMS_COSGN00_tech_spec.md) | Login |
| [BMS_COMEN01_tech_spec.md](BMS_COMEN01_tech_spec.md) | Main Menu |
| [BMS_COADM01_tech_spec.md](BMS_COADM01_tech_spec.md) | Admin Menu |
| [BMS_COTRN00_tech_spec.md](BMS_COTRN00_tech_spec.md) | List Transactions |
| [BMS_COTRN01_tech_spec.md](BMS_COTRN01_tech_spec.md) | View Transaction |
| [BMS_COTRN02_tech_spec.md](BMS_COTRN02_tech_spec.md) | Add Transaction |
| [BMS_COBIL00_tech_spec.md](BMS_COBIL00_tech_spec.md) | Bill Payment |
| [BMS_CORPT00_tech_spec.md](BMS_CORPT00_tech_spec.md) | Transaction Reports |
| [BMS_COACTVW_tech_spec.md](BMS_COACTVW_tech_spec.md) | View Account |
| [BMS_COACTUP_tech_spec.md](BMS_COACTUP_tech_spec.md) | Update Account |
| [BMS_COCRDSL_tech_spec.md](BMS_COCRDSL_tech_spec.md) | View Card Detail |
| [BMS_COCRDLI_tech_spec.md](BMS_COCRDLI_tech_spec.md) | List Credit Cards |
| [BMS_COCRDUP_tech_spec.md](BMS_COCRDUP_tech_spec.md) | Update Credit Card |
| [BMS_COUSR00_tech_spec.md](BMS_COUSR00_tech_spec.md) | List Users |
| [BMS_COUSR01_tech_spec.md](BMS_COUSR01_tech_spec.md) | Add User |
| [BMS_COUSR02_tech_spec.md](BMS_COUSR02_tech_spec.md) | Update User |
| [BMS_COUSR03_tech_spec.md](BMS_COUSR03_tech_spec.md) | Delete User |
| [BMS_COTRTLI_tech_spec.md](BMS_COTRTLI_tech_spec.md) | Transaction Type List |
| [BMS_COTRTUP_tech_spec.md](BMS_COTRTUP_tech_spec.md) | Transaction Type Update |
| [BMS_COPAU00_tech_spec.md](BMS_COPAU00_tech_spec.md) | Authorization Summary |
| [BMS_COPAU01_tech_spec.md](BMS_COPAU01_tech_spec.md) | Authorization Detail |
