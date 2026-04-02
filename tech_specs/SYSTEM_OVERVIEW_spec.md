# CardDemo System Architecture - Technical Overview Specification

**Document:** SYSTEM_OVERVIEW_spec.md  
**Project:** AWS Mainframe Modernization - CardDemo  
**Date:** 2026-04-02  
**Analyst:** Mainframe Codebase Analyst  
**Scope:** Complete system-wide architecture derived from source inspection of all 44 COBOL programs and 57 copybooks

---

## 1. Executive Summary

CardDemo is an IBM z/OS mainframe credit card management demonstration application built by Amazon Web Services to illustrate mainframe modernization patterns. The system comprises four distinct processing subsystems: (1) a CICS online application for real-time card/account/transaction management via 3270 BMS screens, (2) a batch subsystem for statement generation, transaction posting, and data export/import, (3) an IMS/DB2/MQ authorization subsystem handling pending card authorization records via both CICS online screens and batch IMS programs, and (4) a DB2-based transaction-type maintenance subsystem. The application stores its primary business data in five VSAM KSDS files (account, customer, card, transaction, cross-reference) and a VSAM user security file, augmented by IMS databases for pending authorizations and DB2 tables for transaction type codes and fraud records. All online programs communicate exclusively via a shared COMMAREA structure (CARDDEMO-COMMAREA defined in COCOM01Y) passed through CICS XCTL transfers.

---

## 2. Artifact Inventory

### 2.1 All Programs by Subsystem

#### 2.1.1 Online CICS Programs (app/cbl/)

| Program | CICS Trans ID | BMS Map | Role |
|---|---|---|---|
| COSGN00C | CC00 | COSGN00 / COSGN0AI | Sign-on screen — user authentication |
| COMEN01C | CM00 | COMEN01 / COMEN1AI | User main menu (11 options) |
| COADM01C | CA00 | COADM01 / COADM1AI | Admin menu (6 options) |
| COACTVWC | (literal, not hardcoded) | COACTVW / CACTVWAI | Account view (read-only) |
| COACTUPC | (literal, not hardcoded) | COACTUP / CACTUPAI | Account update |
| COCRDLIC | (literal, not hardcoded) | COCRDLI / CCRDLIAI | Credit card list (pageable, 7 rows) |
| COCRDSLC | (literal, not hardcoded) | COCRDSL / CCRDSLAI | Credit card selection/view |
| COCRDUPC | (literal, not hardcoded) | COCRDUP / CCRDUAI | Credit card update |
| COTRN00C | CT00 | COTRN00 / COTRN0AI | Transaction list (pageable, 10 rows) |
| COTRN01C | CT01 | COTRN01 / COTRN1AI | Transaction detail view |
| COTRN02C | CT02 | COTRN02 / COTRN2AI | Transaction add |
| CORPT00C | CR00 | CORPT00 / CRPT00AI | Transaction report request |
| COBIL00C | CB00 | COBIL00 / CBIL0AI | Bill payment |
| COUSR00C | CU00 | COUSR00 / COUSR0AI | User list (admin, pageable, 10 rows) |
| COUSR01C | CU01 | COUSR01 / COUSR1AI | User add (admin) |
| COUSR02C | CU02 | COUSR02 / COUSR2AI | User update (admin) |
| COUSR03C | CU03 | COUSR03 / COUSR3AI | User delete (admin) |
| CSUTLDTC | (batch utility) | None | Date validation utility (CALL interface) |
| COBSWAIT | (CICS) | None | CICS DELAY wait utility program |

#### 2.1.2 Batch Programs (app/cbl/)

| Program | Role |
|---|---|
| CBACT01C | Account file utility (date conversion via CODATECN, reads ACCTFILE) |
| CBACT02C | Card file utility (reads CARDFILE KSDS) |
| CBACT03C | Cross-reference file utility (reads XREFFILE KSDS) |
| CBACT04C | Account interest/balance calculation (reads TRANSACT, TRAN-CAT-BAL, DIS-GROUP files; updates ACCTFILE) |
| CBCUS01C | Customer file utility (reads CUSTFILE KSDS) |
| CBTRN01C | Daily transaction posting (reads DALYTRAN, CUSTFILE, XREFFILE, CARDFILE, ACCTFILE; writes TRANFILE) |
| CBTRN02C | Transaction category balance update (reads DALYTRAN, TRANSACT, ACCTFILE; reads/writes TRAN-CAT-BAL-FILE) |
| CBTRN03C | Daily transaction report generation (reads TRANSACT, TRAN-TYPE, TRAN-CAT; writes REPORT file via CVTRA07Y) |
| CBSTM03A | Statement generation driver (reads ACCTFILE, XREFFILE via COSTM01, CUSTREC) |
| CBSTM03B | Statement generation step B [ARTIFACT NOT FULLY ANALYZED — no COPY statements in grep] |
| CBEXPORT | Multi-entity sequential file export (reads CUSTFILE, ACCTFILE, XREFFILE, CARDFILE, TRANFILE; writes EXPFILE via CVEXPORT) |
| CBIMPORT | Multi-entity sequential file import (reads IMPFILE via CVEXPORT; writes CUSTFILE, ACCTFILE, XREFFILE, CARDFILE, TRANFILE) |

#### 2.1.3 Authorization Subsystem Programs (app/app-authorization-ims-db2-mq/cbl/)

| Program | Type | Role |
|---|---|---|
| COPAUS0C | CICS Online | Pending authorization list screen (IMS read, account-level summary) |
| COPAUS1C | CICS Online | Pending authorization detail screen (IMS read + CICS LINK to fraud program) |
| COPAUS2C | CICS Online | Authorization fraud update screen (DB2 INSERT/UPDATE to CARDDEMO.AUTHFRDS) |
| COPAUA0C | CICS Online | MQ-based authorization processor (sends/receives MQ messages, reads IMS) |
| CBPAUP0C | Batch | Batch pending authorization processor (IMS DL/I operations) |
| PAUDBLOD | IMS Batch | IMS database load program (DL/I ISRT using PAUTBPCB) |
| PAUDBUNL | IMS Batch | IMS database unload program (DL/I GN using PAUTBPCB) |
| DBUNLDGS | IMS Batch | IMS full database unload (DL/I using PAUTBPCB + PASFLPCB + PADFLPCB) |

#### 2.1.4 Transaction Type DB2 Programs (app/app-transaction-type-db2/cbl/)

| Program | Type | Role |
|---|---|---|
| COTRTLIC | CICS Online | Transaction type list/view screen (DB2 cursor on CARDDEMO.TRANSACTION_TYPE; XCTL to COTRTUPC) |
| COTRTUPC | CICS Online | Transaction type update/add screen (DB2 SELECT, INSERT, UPDATE, DELETE on CARDDEMO.TRANSACTION_TYPE) |
| COBTUPDT | Batch | Batch transaction type table maintenance (DB2 INSERT/UPDATE/DELETE on CARDDEMO.TRANSACTION_TYPE) |

#### 2.1.5 VSAM/MQ Service Programs (app/app-vsam-mq/cbl/)

| Program | Type | Role |
|---|---|---|
| COACCT01 | Service | MQ account inquiry service (receives MQ request, reads ACCTDAT VSAM, sends MQ reply via CMQGMOV/CMQPMOV) |
| CODATE01 | Service | MQ date service (receives MQ request, returns current date via CMQGMOV/CMQPMOV) |

---

## 3. System Architecture Overview

### 3.1 High-Level Component Architecture

```
+------------------------------------------------------------------+
|                    CICS ONLINE SUBSYSTEM                         |
|  CC00:COSGN00C --> CA00:COADM01C --> Admin functions             |
|                --> CM00:COMEN01C --> User functions               |
|                                                                   |
|  User Functions (all via COMEN01C menu, XCTL):                   |
|    Account:     COACTVWC, COACTUPC                               |
|    Card:        COCRDLIC, COCRDSLC, COCRDUPC                     |
|    Transaction: COTRN00C, COTRN01C, COTRN02C, CORPT00C          |
|    Billing:     COBIL00C                                          |
|    Auth View:   COPAUS0C --> COPAUS1C --> COPAUS2C               |
|                                                                   |
|  Admin Functions (via COADM01C menu, XCTL):                      |
|    User Mgmt:   COUSR00C, COUSR01C, COUSR02C, COUSR03C          |
|    Tran Type:   COTRTLIC --> COTRTUPC                            |
+------------------------------------------------------------------+
         |                    |                    |
    VSAM Files           IMS Database          DB2 Tables
    ---------            ------------          ----------
    ACCTDAT              PAUT DB               TRANSACTION_TYPE
    CUSTDAT              (CIPAUDTY/CIPAUSMY)   AUTHFRDS
    CARDDAT                                    TRANSACTION_CATEGORY
    TRANFILE
    USRSEC
    CXACAIX (AIX)
+------------------------------------------------------------------+
|                    BATCH SUBSYSTEM                               |
|  CBTRN01C  -- Daily transaction posting                         |
|  CBTRN02C  -- Category balance update                           |
|  CBTRN03C  -- Transaction report                                 |
|  CBACT04C  -- Interest calculation                              |
|  CBSTM03A/B -- Statement generation                             |
|  CBEXPORT/CBIMPORT -- Data migration export/import              |
|  PAUDBLOD/PAUDBUNL/DBUNLDGS -- IMS batch utilities             |
|  COBTUPDT  -- DB2 transaction type batch update                 |
+------------------------------------------------------------------+
         |
    Sequential Files:
    DALYTRAN (daily txn input)
    EXPFILE/IMPFILE (export/import)
    REPORT (printed output)
```

---

## 4. Security and Authentication Model

### 4.1 Sign-On Flow

**Source:** `app/cbl/COSGN00C.cbl` lines 211-237

1. Transaction CC00 invokes COSGN00C. The program presents BMS map COSGN00 (mapset COSGN0A) with USERID and PASSWD input fields.
2. COSGN00C issues `EXEC CICS READ DATASET('USRSEC') RIDFLD(userid)` to read a user record matching the entered user ID.
3. The retrieved record is mapped to `SEC-USER-DATA` (from CSUSR01Y copybook): SEC-USR-ID, SEC-USR-FNAME, SEC-USR-LNAME, SEC-USR-PWD, SEC-USR-TYPE.
4. The entered password is compared to SEC-USR-PWD (8-char, stored in clear text in USRSEC VSAM file).
5. If authentication succeeds:
   - SEC-USR-TYPE ('A' or 'U') is moved to `CDEMO-USER-TYPE` in CARDDEMO-COMMAREA (COCOM01Y).
   - `CDEMO-USER-ID` is populated.
   - `CDEMO-PGM-CONTEXT` is set to CDEMO-PGM-ENTER (value 0).
   - If `CDEMO-USRTYP-ADMIN` (type='A'): `EXEC CICS XCTL PROGRAM('COADM01C')` (line 232).
   - If `CDEMO-USRTYP-USER` (type='U'): `EXEC CICS XCTL PROGRAM('COMEN01C')` (line 237).

**Security Note:** Passwords are stored in plain text in USRSEC VSAM. There is no encryption, hashing, or RACF integration evident in source. User type is a single character ('A'/'U') controlling menu routing.

**VSAM File:** USRSEC (dataset name used in CICS FCT). Record layout: `SEC-USER-DATA` from CSUSR01Y (80 bytes). Primary key: SEC-USR-ID (PIC X(08)).

---

## 5. Program Interaction Map (XCTL/LINK Flow)

### 5.1 Online Program Transfer Graph

All online programs transfer control exclusively via `EXEC CICS XCTL` passing the CARDDEMO-COMMAREA. There are no CICS LINK calls within the main online subsystem (LINK is used only in COPAUS1C to COPAUS2C for fraud flagging).

```
COSGN00C (CC00)
   |-- [admin user] --> XCTL --> COADM01C (CA00)
   |                               |-- XCTL[option 1] --> COUSR00C (CU00)
   |                               |-- XCTL[option 2] --> COUSR01C (CU01)
   |                               |-- XCTL[option 3] --> COUSR02C (CU02)
   |                               |-- XCTL[option 4] --> COUSR03C (CU03)
   |                               |-- XCTL[option 5] --> COTRTLIC (CTLI)
   |                               |-- XCTL[option 6] --> COTRTUPC
   |                               |-- XCTL[back]    --> COSGN00C (CC00)
   |
   |-- [user]       --> XCTL --> COMEN01C (CM00)
                                   |-- XCTL[option 1]  --> COACTVWC
                                   |-- XCTL[option 2]  --> COACTUPC
                                   |-- XCTL[option 3]  --> COCRDLIC
                                   |-- XCTL[option 4]  --> COCRDSLC
                                   |-- XCTL[option 5]  --> COCRDUPC
                                   |-- XCTL[option 6]  --> COTRN00C (CT00)
                                   |-- XCTL[option 7]  --> COTRN01C (CT01)
                                   |-- XCTL[option 8]  --> COTRN02C (CT02)
                                   |-- XCTL[option 9]  --> CORPT00C (CR00)
                                   |-- XCTL[option 10] --> COBIL00C (CB00)
                                   |-- XCTL[option 11] --> COPAUS0C
                                   |-- XCTL[back]      --> COSGN00C (CC00)

COCRDLIC --> XCTL[select/view] --> COCRDSLC
COCRDLIC --> XCTL[select/update] --> COCRDUPC
COCRDLIC --> XCTL[back] --> COMEN01C (LIT-MENUPGM = 'CM00')

COTRTLIC --> XCTL[add/update] --> COTRTUPC (LIT-ADDTPGM = 'COTRTUPC', line 50)
COTRTLIC --> XCTL[back] --> COADM01C (via CDEMO-TO-PROGRAM)
COTRTUPC --> XCTL[back] --> COADM01C (via CDEMO-TO-PROGRAM)

COPAUS0C --> XCTL[detail] --> COPAUS1C
COPAUS1C --> LINK[fraud flag] --> COPAUS2C
COPAUS1C --> XCTL[back] --> COPAUS0C
```

**Source citations:**
- COSGN00C XCTL to COADM01C: `app/cbl/COSGN00C.cbl` line 232
- COSGN00C XCTL to COMEN01C: `app/cbl/COSGN00C.cbl` line 237
- COMEN01C option dispatch: `app/cbl/COMEN01C.cbl` line 157 (`XCTL PROGRAM(CDEMO-MENU-OPT-PGMNAME(WS-OPTION))`)
- COADM01C option dispatch: `app/cbl/COADM01C.cbl` line 146 (`XCTL PROGRAM(CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION))`)
- COTRTLIC to COTRTUPC: `app/app-transaction-type-db2/cbl/COTRTLIC.cbl` line 649 (`XCTL PROGRAM (LIT-ADDTPGM)`)
- COPAUS1C LINK to COPAUS2C: `app/app-authorization-ims-db2-mq/cbl/COPAUS1C.cbl` line 248 (`EXEC CICS LINK PROGRAM(WS-PGM-AUTH-FRAUD)`)

### 5.2 COMMAREA Navigation Pattern

Every functional program follows this navigation contract via CARDDEMO-COMMAREA (COCOM01Y):
- `CDEMO-FROM-TRANID` / `CDEMO-FROM-PROGRAM` — Who transferred control here
- `CDEMO-TO-TRANID` / `CDEMO-TO-PROGRAM` — Where to transfer when user presses back/F3
- `CDEMO-PGM-CONTEXT` — 0=first entry (initialize screen), 1=re-entry (process data)
- `CDEMO-USER-ID` / `CDEMO-USER-TYPE` — Authenticated user identity carried throughout the session
- `CDEMO-ACCT-ID`, `CDEMO-CARD-NUM`, `CDEMO-CUST-ID` — Entity keys passed between programs

Programs that return to the menu detect their context using `CDEMO-FROM-PROGRAM` compared against `LIT-MENUPGM` (value 'CM00') to determine whether to refresh from scratch or resume. Source: `app/cbl/COACTVWC.cbl` lines 283, 336; `app/cbl/COCRDLIC.cbl` lines 190, 392.

---

## 6. Data Model

### 6.1 VSAM Files

| CICS Dataset Name | Logical Name (Batch) | Access Type | Primary Key | Record Length | Copybook | Description |
|---|---|---|---|---|---|---|
| ACCTDAT | ACCTFILE | KSDS | ACCT-ID PIC 9(11) | 300 | CVACT01Y | Account records |
| CUSTDAT | CUSTFILE | KSDS | CUST-ID PIC 9(09) | 500 | CVCUS01Y | Customer records |
| CARDDAT | CARDFILE | KSDS | CARD-NUM PIC X(16) | 150 | CVACT02Y | Credit card records |
| TRANFILE / TRANSACT | TRANFILE | KSDS | TRAN-ID PIC X(16) | 350 | CVTRA05Y | Transaction records |
| USRSEC | (USRSEC in batch) | KSDS | SEC-USR-ID PIC X(08) | 80 | CSUSR01Y | User security records |
| CXACAIX | (alternate index) | KSDS AIX | XREF-ACCT-ID (alt. path) | 50 | CVACT03Y | Card-to-account cross-reference (alternate index on CARDDAT/XREFFILE by account ID) |

**Source citations:**
- ACCTDAT value: `app/cbl/COACTVWC.cbl` line 185 (`VALUE 'ACCTDAT '`)
- CUSTDAT value: `app/cbl/COACTVWC.cbl` line 189 (`VALUE 'CUSTDAT '`)
- CARDDAT value: `app/cbl/COCRDSLC.cbl` line 188 (`VALUE 'CARDDAT '`)
- TRANSACT value: `app/cbl/COTRN00C.cbl` line 39 (`VALUE 'TRANSACT'`)
- USRSEC value: `app/cbl/COMEN01C.cbl` line 39 (`VALUE 'USRSEC  '`)
- CXACAIX (AIX): `app/cbl/COACTUPC.cbl` line 582 (`VALUE 'CXACAIX '`); `app/cbl/COBIL00C.cbl` line 42 (`VALUE 'CXACAIX '`)

**Note on CXACAIX:** This is an Alternate Index path over the card cross-reference dataset, keyed by account ID. Programs use it to look up the card number associated with a known account ID. The base dataset appears to be CARDDAT (the primary card file), with CXACAIX as the VSAM AIX path. The record layout is CARD-XREF-RECORD from CVACT03Y.

#### 6.1.1 Additional Batch-Only Files

| DD Name | Access | Record Length | Copybook | Programs | Description |
|---|---|---|---|---|---|
| DALYTRAN | ESDS/Sequential input | 350 | CVTRA06Y | CBTRN01C, CBTRN02C | Daily transaction input from external systems |
| EXPFILE | Sequential output | 500 | CVEXPORT | CBEXPORT | Multi-entity export file |
| IMPFILE | Sequential input | 500 | CVEXPORT | CBIMPORT | Multi-entity import file |
| STMTFILE | Sequential | 350 | COSTM01 | CBSTM03A | Statement transaction file (key: CARD-NUM+TRAN-ID) |
| TRAN-CAT-BAL-FILE | VSAM KSDS | 50 | CVTRA01Y | CBACT04C, CBTRN02C | Transaction category balance |
| DIS-GROUP-FILE | VSAM KSDS | 50 | CVTRA02Y | CBACT04C | Disclosure/interest rate by group+type+category |
| TRAN-TYPE-FILE | VSAM/Sequential | 60 | CVTRA03Y | CBTRN03C | Transaction type code table |
| TRAN-CAT-FILE | VSAM/Sequential | 60 | CVTRA04Y | CBTRN03C | Transaction category code table |
| RPTFILE | Print/Sequential | Variable | CVTRA07Y | CBTRN03C | Daily transaction report output |

### 6.2 DB2 Tables

| Table | Schema | CRUD Operations | Programs |
|---|---|---|---|
| TRANSACTION_TYPE | CARDDEMO | SELECT (cursor), INSERT, UPDATE, DELETE | COTRTLIC, COTRTUPC (online); COBTUPDT (batch) |
| AUTHFRDS | CARDDEMO | INSERT, UPDATE | COPAUS2C (online) |
| TRANSACTION_CATEGORY | CARDDEMO (inferred) | SELECT | COTRTUPC (EXEC SQL INCLUDE DCLTRCAT, line 288) |

**DB2 DCLGEN includes:**
- `DCLTRTYP` — DB2 DCLGEN for TRANSACTION_TYPE table (referenced via `EXEC SQL INCLUDE DCLTRTYP END-EXEC` in COTRTLIC line 333, COTRTUPC line 286)
- `DCLTRCAT` — DB2 DCLGEN for TRANSACTION_CATEGORY table (referenced via `EXEC SQL INCLUDE DCLTRCAT END-EXEC` in COTRTUPC line 288)

**[ARTIFACTS NOT AVAILABLE FOR INSPECTION: DCLTRTYP, DCLTRCAT]** These DB2 DCLGEN-generated copybooks define host variable structures corresponding to the DB2 tables. They are not present in the analyzed copybook directories.

**Source citations:**
- CARDDEMO.TRANSACTION_TYPE SELECT: `app/app-transaction-type-db2/cbl/COTRTLIC.cbl` line 342
- CARDDEMO.TRANSACTION_TYPE DELETE: `app/app-transaction-type-db2/cbl/COTRTLIC.cbl` line 1901
- CARDDEMO.AUTHFRDS INSERT: `app/app-authorization-ims-db2-mq/cbl/COPAUS2C.cbl` line 142
- CARDDEMO.AUTHFRDS UPDATE: `app/app-authorization-ims-db2-mq/cbl/COPAUS2C.cbl` line 223

### 6.3 IMS Databases

The authorization subsystem uses IMS DL/I with three PCBs:

| PCB Name | PCB Copybook | Segments | Key Field | Batch Programs |
|---|---|---|---|---|
| PAUT | PAUTBPCB.CPY | Authorization Table (root) | Keyfb 255 bytes | PAUDBLOD, PAUDBUNL, DBUNLDGS |
| PASFL | PASFLPCB.CPY | Authorization Summary (CIPAUSMY segment) | Keyfb 100 bytes | DBUNLDGS only |
| PADFL | PADFLPCB.CPY | Authorization Details (CIPAUDTY segment) | Keyfb 255 bytes | DBUNLDGS only |

**IMS Segment Hierarchy (inferred from PCB names and copybook structure):**

```
Root Segment (PAUT PCB):
  |-- Authorization Summary (PA-ACCT-ID, PA-CUST-ID, PA-AUTH-STATUS, balances/counts)
      |-- Authorization Detail (PA-AUTH-DATE-9C/PA-AUTH-TIME-9C key, full auth record, match status, fraud flag)
```

**CICS IMS Access:** COPAUS0C and COPAUS1C access IMS data. The mechanism used is not DL/I batch (no ENTRY DLITCBL) — these are CICS programs. The IMS access from CICS is via CICS-IMS bridge or DL/I calls through EXEC DLI. Exact DL/I call syntax in CICS context was not fully confirmed from grep evidence; the copybooks CIPAUSMY and CIPAUDTY are used for both CICS programs and IMS batch programs.

### 6.4 Entity Relationship Model

```
CUSTOMER (CUST-ID pk, 500 bytes)
    |
    |-- has many --> CARD-XREF (XREF-CARD-NUM pk, XREF-CUST-ID fk, XREF-ACCT-ID fk)
                                 |                          |
                                 |                          v
                                 |                    ACCOUNT (ACCT-ID pk, 300 bytes)
                                 |                          |
                                 v                          |-- has many -->
                            CARD (CARD-NUM pk, CARD-ACCT-ID fk, 150 bytes)
                                                            |
                                                   TRANSACTION (TRAN-ID pk, TRAN-CARD-NUM fk, 350 bytes)

AUTHORIZATION_SUMMARY (IMS, PA-ACCT-ID, PA-CUST-ID)
    |-- has many --> AUTHORIZATION_DETAIL (IMS, key=date+time, CARD-NUM, match status, fraud flag)

DB2.TRANSACTION_TYPE (type code, description, 60 bytes)
DB2.AUTHFRDS (fraud records with INSERT/UPDATE by COPAUS2C)
```

---

## 7. BMS Screen Navigation Flow

### 7.1 Screen Navigation Map

```
[Entry: CICS transaction CC00]
        |
        v
  COSGN00 (COSGN00C)
  Sign-On: USERID, PASSWD
        |
        |-- [admin] --> COADM01 (COADM01C)
        |               Admin Menu
        |               |-- opt 1 --> COUSR00 (COUSR00C) -- User list (browse USRSEC)
        |               |               |-- select --> COUSR01 (COUSR01C) -- Add user
        |               |               |-- select --> COUSR02 (COUSR02C) -- Update user
        |               |               |-- select --> COUSR03 (COUSR03C) -- Delete user
        |               |-- opt 2 --> COUSR01 (COUSR01C) -- Add user
        |               |-- opt 3 --> COUSR02 (COUSR02C) -- Update user
        |               |-- opt 4 --> COUSR03 (COUSR03C) -- Delete user
        |               |-- opt 5 --> COTRTLI (COTRTLIC) -- Transaction type list
        |               |               |-- select --> COTRTUP (COTRTUPC) -- Tran type update
        |               |               |-- back  --> COADM01
        |               |-- opt 6 --> COTRTUP (COTRTUPC) -- Tran type maintenance
        |               |-- back  --> COSGN00
        |
        |-- [user]  --> COMEN01 (COMEN01C)
                        User Menu
                        |-- opt 1  --> COACTVW (COACTVWC) -- Account view
                        |               |-- back --> COMEN01
                        |-- opt 2  --> COACTUP (COACTUPC) -- Account update
                        |               |-- back --> COMEN01
                        |-- opt 3  --> COCRDLI (COCRDLIC) -- Card list (browse CARDDAT)
                        |               |-- select/view --> COCRDSL (COCRDSLC) -- Card view
                        |               |-- select/upd  --> COCRDUP (COCRDUPC) -- Card update
                        |               |-- back        --> COMEN01
                        |-- opt 4  --> COCRDSL (COCRDSLC) -- Card view
                        |               |-- back --> COMEN01
                        |-- opt 5  --> COCRDUP (COCRDUPC) -- Card update
                        |               |-- back --> COMEN01
                        |-- opt 6  --> COTRN00 (COTRN00C) -- Transaction list
                        |               |-- select --> COTRN01 (COTRN01C) -- Tran detail
                        |               |-- back   --> COMEN01
                        |-- opt 7  --> COTRN01 (COTRN01C) -- Transaction view
                        |               |-- back --> COMEN01
                        |-- opt 8  --> COTRN02 (COTRN02C) -- Transaction add
                        |               |-- back --> COMEN01
                        |-- opt 9  --> CORPT00 (CORPT00C) -- Reports
                        |               |-- submit --> COBSWAIT/CICS delay
                        |               |-- back   --> COMEN01
                        |-- opt 10 --> COBIL00 (COBIL00C) -- Bill payment
                        |               |-- back --> COMEN01
                        |-- opt 11 --> COPAU00 (COPAUS0C) -- Auth list
                                        |-- select --> COPAU01 (COPAUS1C) -- Auth detail
                                        |               |-- fraud flag --> COPAUS2C
                                        |               |-- back       --> COPAU00
                                        |-- back   --> COMEN01
```

### 7.2 Standard Screen Layout

All BMS screens share a standard two-line header and one-line footer:
- **Line 1:** TRNNAME (current transaction ID, left) | TITLE01 (40 chars, center: "AWS Mainframe Modernization") | CURDATE (date, right)
- **Line 2:** PGMNAME (current program name, left) | TITLE02 (40 chars: "CardDemo") | CURTIME (time, right)
- **Last line:** ERRMSG (78 chars, error message area)

Header literals come from COTTL01Y (`CCDA-TITLE01` = 'AWS Mainframe Modernization', `CCDA-TITLE02` = 'CardDemo'). The transaction ID and program name in the header are self-populated from the program's own WS-TRANID / LIT-THISTRANID working storage.

---

## 8. End-to-End Transaction Flows

### 8.1 User Sign-On to Account Update

1. User enters transaction CC00 on 3270 terminal → CICS invokes COSGN00C
2. COSGN00C sends BMS map COSGN00 (COSGN0AI): blank screen with USERID/PASSWD fields
3. User enters credentials, presses ENTER
4. COSGN00C receives map, reads USRSEC VSAM (`EXEC CICS READ DATASET('USRSEC') RIDFLD(userid)`), compares password
5. If valid user type = 'U': populates CARDDEMO-COMMAREA, `EXEC CICS XCTL PROGRAM('COMEN01C')`
6. COMEN01C sends BMS map COMEN01 showing 11 menu options (from COMEN02Y table)
7. User enters option 2 (Account Update), presses ENTER
8. COMEN01C reads `CDEMO-MENU-OPT-PGMNAME(2)` = 'COACTUPC', sets CDEMO-TO-PROGRAM, issues `EXEC CICS XCTL PROGRAM('COACTUPC')`
9. COACTUPC (first entry: CDEMO-PGM-ENTER=0): reads account ID from COMMAREA (`CDEMO-ACCT-ID`), issues:
   - `EXEC CICS READ DATASET('CXACAIX') RIDFLD(acct-id)` to get card xref
   - `EXEC CICS READ DATASET('ACCTDAT') RIDFLD(acct-id)` to get account record
   - `EXEC CICS READ DATASET('CUSTDAT') RIDFLD(cust-id)` to get customer record
10. COACTUPC populates COACTUP map (CACTUPAI), sends to screen
11. User modifies fields, presses ENTER
12. COACTUPC (re-entry: CDEMO-PGM-REENTER=1): receives map, validates all fields using CSSETATY inline attribute logic, phone/state validation via CSLKPCDY, date validation via CSUTLDPY/CSUTLDWY (CALL 'CSUTLDTC')
13. If valid: `EXEC CICS REWRITE FILE('ACCTDAT')` and `EXEC CICS REWRITE FILE('CUSTDAT')`
14. On F3/back: sets CDEMO-TO-PROGRAM = 'COMEN01C', `EXEC CICS XCTL PROGRAM('COMEN01C')`

### 8.2 Bill Payment

1. From COMEN01C, user selects option 10 → XCTL to COBIL00C
2. COBIL00C presents COBIL00 map
3. User enters account ID and payment amount
4. COBIL00C:
   - `EXEC CICS READ DATASET('ACCTDAT')` — reads current account balance
   - `EXEC CICS REWRITE DATASET('ACCTDAT')` — updates balance
   - `EXEC CICS READ DATASET('CXACAIX')` — finds card number by account
   - `EXEC CICS STARTBR/READPREV DATASET('TRANSACT')` — browses recent transactions
   - `EXEC CICS WRITE DATASET('TRANSACT')` — writes new payment transaction record

### 8.3 Daily Transaction Batch Processing

1. JCL invokes CBTRN01C with DD DALYTRAN (input), CUSTFILE, XREFFILE, CARDFILE, ACCTFILE (lookup), TRANFILE (output)
2. CBTRN01C reads each DALYTRAN-RECORD (CVTRA06Y), looks up card/account/customer, validates, writes TRAN-RECORD to TRANFILE
3. JCL invokes CBTRN02C: reads DALYTRAN again + existing TRANSACT file, updates TRAN-CAT-BAL-FILE (category running balances), also updates ACCTFILE with cycle debit/credit totals
4. JCL invokes CBACT04C: reads TRAN-CAT-BAL-FILE and DIS-GROUP-FILE, computes interest per group/category, updates ACCTFILE
5. JCL invokes CBTRN03C: reads TRANSACT + TRAN-TYPE + TRAN-CAT, produces formatted RPTFILE (print) using CVTRA07Y layout

### 8.4 Pending Authorization View Flow

1. From COMEN01C option 11 → XCTL to COPAUS0C
2. COPAUS0C displays COPAU00 screen; reads IMS CIPAUSMY (summary) segments for account-level pending authorization data
3. User selects a pending authorization → XCTL to COPAUS1C
4. COPAUS1C reads IMS CIPAUDTY (detail) segment for the selected authorization
5. If fraud is to be flagged: COPAUS1C issues `EXEC CICS LINK PROGRAM('COPAUS2C')` (line 248)
6. COPAUS2C receives COMMAREA with authorization key, issues `EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS` or `EXEC SQL UPDATE CARDDEMO.AUTHFRDS`

---

## 9. Batch Processing Overview

### 9.1 Batch Program Dependency Chain

The expected JCL job execution order for end-of-day processing:

```
Phase 1 — Transaction Posting:
  CBTRN01C (DALYTRAN → TRANFILE lookup/post)
  CBTRN02C (DALYTRAN + TRANFILE → TRAN-CAT-BAL-FILE update)

Phase 2 — Interest Calculation:
  CBACT04C (TRAN-CAT-BAL-FILE + DIS-GROUP-FILE → ACCTFILE interest update)

Phase 3 — Statement Generation:
  CBSTM03A/CBSTM03B (ACCTFILE + XREFFILE → STMTFILE)

Phase 4 — Reporting:
  CBTRN03C (TRANSACT + TRAN-TYPE + TRAN-CAT → RPTFILE)

Phase 5 — Data Migration (ad hoc):
  CBEXPORT (all VSAM files → EXPFILE)
  CBIMPORT (IMPFILE → all VSAM files)

Phase 6 — Utility/Reference:
  CBACT01C (ACCTFILE date conversion)
  CBACT02C (CARDFILE reporting)
  CBACT03C (XREFFILE reporting)
  CBCUS01C (CUSTFILE reporting)

IMS Batch (authorization utilities):
  PAUDBLOD (load IMS auth database)
  PAUDBUNL (unload IMS auth database)
  DBUNLDGS (full IMS multi-PCB unload)
  CBPAUP0C (authorization batch processing)

DB2 Batch:
  COBTUPDT (TRANSACTION_TYPE table maintenance via sequential file input)
```

### 9.2 Export/Import Format

CBEXPORT and CBIMPORT use the CVEXPORT copybook (500-byte EXPORT-RECORD). The first byte `EXPORT-REC-TYPE` is the record type discriminator. Bytes 2-27 carry a timestamp, bytes 28-36 carry a sequence number (COMP), bytes 37-40 carry branch ID, bytes 41-45 carry region code, and bytes 46-505 carry the entity data overlaid by REDEFINES for each entity type (customer, account, transaction, card xref, card).

---

## 10. Naming Conventions

### 10.1 Program Naming

| Prefix | Subsystem | Type |
|---|---|---|
| CO | CardDemo Online | CICS online program |
| CB | CardDemo Batch | Batch program |
| CS | CardDemo Shared | Utility/service program |
| COPA | CardDemo Online Pending Authorization | Authorization CICS programs |
| COPA/COPAU | Authorization | Online authorization screens |
| COTRT | Transaction Type | DB2 transaction type programs |
| COBT | Batch Transaction Type | Batch DB2 programs |
| PAU | Pending Authorization Utility | IMS batch programs |
| DB | Database | IMS database utilities |

### 10.2 Copybook Naming

| Prefix | Category |
|---|---|
| CV | CardDemo VSAM entity records (CVACTxxY = account, CVCUSxxY = customer, CVCRDxxY = card, CVTRAxxY = transaction) |
| CO | CardDemo Online structures (COCOMxxY = commarea, COSGNxx = sign-on map, etc.) |
| CS | CardDemo Shared utilities (CSDATeY = date, CSMSGxxY = messages, CSUSRxxY = user, etc.) |
| CI | CardDemo IMS segments (CIPAUxxx = pending authorization segments) |
| CC | CardDemo Communication structures (CCPAUxxx = auth request/response) |
| DFHBMSCA | IBM CICS BMS attribute constants (system copybook) |
| DFHAID | IBM CICS AID key constants (system copybook) |
| PA | Pending Authorization (PADFLPCB, PASFLPCB, PAUTBPCB = IMS PCBs) |
| CMQ | IBM MQ system copybooks |

### 10.3 CICS Transaction ID Conventions

| Range | Subsystem |
|---|---|
| CC00 | Sign-on |
| CA00 | Admin menu |
| CM00 | User main menu |
| CT00-CT02 | Transaction screens (list, view, add) |
| CR00 | Reports |
| CB00 | Bill payment |
| CU00-CU03 | User security management |
| CTLI | Transaction type list (DB2) |

---

## 11. Open Questions and Gaps

1. **CBSTM03B** — Source program exists (`app/cbl/CBSTM03B.CBL`) but its COPY statements and internal logic were not fully captured in the grep analysis. Its role in the statement generation chain (step B after CBSTM03A) is unknown from available evidence.

2. **COBSWAIT** — Program exists and its PROGRAM-ID is COBSWAIT. No COPY statements and no EXEC CICS DELAY confirmed. Likely invoked by CORPT00C for report scheduling/waiting, but the linkage is not confirmed in source.

3. **CICS Resource Definitions** — No CICS CSD (DFHCSDUP) extract, RACF definitions, or JCL were found in the repository. The VSAM dataset names (ACCTDAT, CUSTDAT, etc.) are CICS FCT logical names; physical DSN patterns are unknown.

4. **JCL Not Present** — No JCL job streams were found in the analyzed directories. The batch program execution order above is inferred from data dependencies between programs, not from observed JCL.

5. **DCLTRTYP/DCLTRCAT** — DB2 DCLGEN copybooks for CARDDEMO.TRANSACTION_TYPE and CARDDEMO.TRANSACTION_CATEGORY tables are referenced but not present in any copybook directory. Column definitions for these tables cannot be confirmed.

6. **CSSTRPFY** — Procedure division utility copybook referenced by 6 programs (COCRDLIC, COACTVWC, COCRDUPC, COACTUPC, COTRTLIC, COTRTUPC) but not found in any analyzed directory. Likely contains string-processing or error-handling logic.

7. **IBM MQ Copybooks** — CMQGMOV, CMQPMOV, CMQMDV, CMQODV, CMQV, CMQTML are IBM MQ system library copybooks, not application-owned. The MQ message format and queue names used by COPAUA0C, COACCT01, CODATE01 were not analyzed.

8. **CARDDEMO.AUTHFRDS Column Structure** — DB2 table AUTHFRDS is accessed by INSERT and UPDATE in COPAUS2C but no DCLGEN copybook for it was found. Column structure is inferred from CCPAURQY/CCPAURLY/CIPAUDTY fields but not directly confirmed.

9. **IMS DBD/PSB Definitions** — IMS Database Definitions (DBD) and Program Specification Blocks (PSB) for the authorization databases (PAUT, PASFL, PADFL) are not present in the repository. The full segment hierarchy, PCB names, and sensitivity definitions cannot be confirmed from source alone.

10. **COACTVWC PROGRAM-ID** — The PROGRAM-ID paragraph in `app/cbl/COACTVWC.cbl` line 22 appears blank/incomplete in source (the grep shows `PROGRAM-ID.` with the name on a continuation line). This is a formatting artifact but does not affect runtime, as the CICS program name is controlled by the CSD definition.
