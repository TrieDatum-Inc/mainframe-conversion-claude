# CardDemo Application - Overall System Technical Specification

## Table of Contents

1. [System Overview](#1-system-overview)
2. [System Architecture](#2-system-architecture)
3. [Application Modules](#3-application-modules)
4. [CICS Transaction Registry](#4-cics-transaction-registry)
5. [Screen Navigation Map](#5-screen-navigation-map)
6. [End-to-End Transaction Flows](#6-end-to-end-transaction-flows)
7. [Inter-Program Dependencies](#7-inter-program-dependencies)
8. [Data Architecture](#8-data-architecture)
9. [Batch Processing Flows](#9-batch-processing-flows)
10. [Asynchronous Processing (MQ)](#10-asynchronous-processing-mq)
11. [Copybook Inventory](#11-copybook-inventory)
12. [Known Issues and Anomalies](#12-known-issues-and-anomalies)
13. [File Inventory](#13-file-inventory)

---

## 1. System Overview

**CardDemo** is a credit card management application built on IBM mainframe technology. It provides online (CICS) and batch capabilities for managing credit card accounts, transactions, customer data, user security, billing, reporting, and authorization processing.

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Online TP Monitor | CICS Transaction Server |
| Programming Language | COBOL |
| Screen Presentation | BMS (Basic Mapping Support) |
| Primary Data Store | VSAM (KSDS, AIX) |
| Relational Database | DB2 (for authorization fraud tracking and transaction types) |
| Hierarchical Database | IMS (for pending authorization storage) |
| Message Queuing | IBM MQ (for async account/date inquiries and authorization triggers) |
| Batch | z/OS JCL with COBOL batch programs |
| Security | VSAM-based user authentication (USRSEC file) |
| Date Utilities | IBM Language Environment (LE) CEEDAYS |

### Application Modules

The system is organized into four modules:

1. **Base CardDemo** - Core credit card processing (31 COBOL programs, 17 BMS maps)
2. **Authorization Extension (IMS/DB2/MQ)** - Real-time authorization processing (8 programs, 2 BMS maps)
3. **Transaction Type Management (DB2)** - Reference data management (3 programs, 2 BMS maps)
4. **VSAM-MQ Extension** - Asynchronous data extraction (2 programs, no screens)

---

## 2. System Architecture

### High-Level Architecture Diagram

```
                    ┌─────────────────────────────────────────────────────┐
                    │                   CICS Region                       │
                    │                                                     │
  3270 Terminal ──► │  ┌──────────┐    ┌──────────────┐                  │
                    │  │ BMS Maps │◄──►│ Online COBOL │                  │
                    │  │ (21 maps)│    │  Programs    │                  │
                    │  └──────────┘    └──────┬───────┘                  │
                    │                         │                          │
                    │         ┌───────────────┼───────────────┐          │
                    │         ▼               ▼               ▼          │
                    │    ┌─────────┐    ┌──────────┐    ┌──────────┐    │
                    │    │  VSAM   │    │   DB2    │    │   IMS    │    │
                    │    │  Files  │    │  Tables  │    │   DBs    │    │
                    │    └─────────┘    └──────────┘    └──────────┘    │
                    │         ▲                                          │
                    │         │          ┌──────────┐                    │
                    │         └──────────│  IBM MQ  │◄── MQ Triggers    │
                    │                    │  Queues  │                    │
                    │                    └──────────┘                    │
                    └─────────────────────────────────────────────────────┘
                                          ▲
                                          │
                    ┌─────────────────────────────────────────────────────┐
                    │                Batch Region (JCL)                   │
                    │                                                     │
                    │  CBACT01C-04C  CBTRN01C-03C  CBEXPORT  CBIMPORT   │
                    │  CBSTM03A/B    CBCUS01C      COBTUPDT  CBPAUP0C   │
                    │                                                     │
                    │         ┌─────────┐    ┌──────────┐                │
                    │         │  VSAM   │    │ Sequential│                │
                    │         │  Files  │    │  Files    │                │
                    │         └─────────┘    └──────────┘                │
                    └─────────────────────────────────────────────────────┘
```

### CICS Program Interaction Pattern

All online COBOL programs follow a **pseudo-conversational** pattern:

1. First entry (EIBCALEN = 0): Initialize and display screen
2. Re-entry (EIBCALEN > 0): Receive input, process, re-display or transfer
3. Navigation: XCTL (transfer control) to sibling programs; LINK for subroutines
4. State: Passed via CARDDEMO-COMMAREA (defined in COCOM01Y.cpy)

---

## 3. Application Modules

### 3.1 Base CardDemo

The core application providing credit card account management, transaction processing, user administration, billing, and reporting.

#### Online Programs (CICS)

| Program | Transaction | BMS Map | Function |
|---------|-------------|---------|----------|
| COSGN00C | CC00 | COSGN00 | Sign-on/Authentication |
| COMEN01C | CM00 | COMEN01 | Main menu (regular users) |
| COADM01C | CA00 | COADM01 | Admin menu |
| COACTVWC | CAVW | COACTVW | Account view |
| COACTUPC | - | COACTUP | Account update |
| COCRDLIC | CC00 | COCRDLI | Credit card list |
| COCRDSLC | CCDL | COCRDSL | Credit card view/select |
| COCRDUPC | - | COCRDUP | Credit card update |
| COTRN00C | CT00 | COTRN00 | Transaction list (paginated) |
| COTRN01C | - | COTRN01 | Transaction detail view |
| COTRN02C | - | COTRN02 | Transaction add |
| COUSR00C | CU00 | COUSR00 | User list (admin only) |
| COUSR01C | - | COUSR01 | User add |
| COUSR02C | - | COUSR02 | User update |
| COUSR03C | - | COUSR03 | User delete |
| COBIL00C | - | COBIL00 | Bill payment |
| CORPT00C | CR00 | CORPT00 | Report request |
| CSUTLDTC | - | - | Date validation utility (LINK subroutine) |

#### Batch Programs

| Program | Function | Input | Output |
|---------|----------|-------|--------|
| CBACT01C | Account file processing | ACCTFILE VSAM | Report |
| CBACT02C | Account list report | ACCTFILE VSAM | Report |
| CBACT03C | Account details extract | ACCTFILE VSAM | Sequential |
| CBACT04C | Account update batch | Input file | ACCTFILE VSAM |
| CBCUS01C | Customer file processing | CUSTFILE VSAM | Report |
| CBTRN01C | Transaction processing | TRANSACT VSAM | Report |
| CBTRN02C | Transaction category report | TRANSACT VSAM | Report |
| CBTRN03C | Transaction purge/archive | TRANSACT VSAM | Archive file |
| CBSTM03A | Statement generation (phase A) | Account/Transaction VSAM | Statement file |
| CBSTM03B | Statement generation (phase B) | Statement file | Print output |
| CBEXPORT | Data export | VSAM files | Export flat file |
| CBIMPORT | Data import | Import flat file | VSAM files |
| COBSWAIT | MVS wait utility | Wait time parameter | - |

### 3.2 Authorization Extension (IMS/DB2/MQ)

Real-time credit card authorization processing with fraud tracking.

#### Online Programs (CICS)

| Program | Transaction | BMS Map | Function |
|---------|-------------|---------|----------|
| COPAUS0C | CPVS | COPAU00 | Authorization summary list |
| COPAUS1C | CPVD | COPAU01 | Authorization detail view |
| COPAUS2C | CPVD | - | Fraud flag toggle (DB2 update) |

#### Batch/Trigger Programs

| Program | Type | Function |
|---------|------|----------|
| COPAUA0C | MQ Trigger (CICS) | Process authorization requests from MQ; write to IMS |
| CBPAUP0C | Batch | Purge expired pending authorizations from IMS |
| DBUNLDGS | Batch | Unload GSAM data |
| PAUDBUNL | Batch (IMS BMP) | Unload authorization IMS database |
| PAUDBLOD | Batch (IMS BMP) | Load authorization IMS database |

#### Data Stores

| Store | Type | Purpose |
|-------|------|---------|
| PAUTHDTL | IMS Database (HISAM) | Pending authorization details (keyed by card+timestamp inverted) |
| PAUTHSUM | IMS Database (HISAM) | Pending authorization summaries (keyed by card number) |
| AUTHFRDS | DB2 Table | Fraud-flagged authorizations |

### 3.3 Transaction Type Management (DB2)

Reference data management for transaction type codes.

#### Online Programs (CICS)

| Program | Transaction | BMS Map | Function |
|---------|-------------|---------|----------|
| COTRTLIC | CTLI | COTRTLI | Transaction type list with update/delete |
| COTRTUPC | CTTU | COTRTUP | Transaction type add/edit (15-state machine) |

#### Batch Programs

| Program | Function |
|---------|----------|
| COBTUPDT | Batch maintenance of transaction types via input file (Add/Update/Delete) |

#### Data Stores

| Table | Purpose |
|-------|---------|
| TRNTYPE | Transaction type master (TR_TYPE char(2), TR_TYPE_DESC char(50)) |
| TRNTYCAT | Transaction type categories (referenced but not actively queried) |

### 3.4 VSAM-MQ Extension

Asynchronous data services triggered by MQ messages.

| Program | Transaction | Function |
|---------|-------------|----------|
| COACCT01 | CDRA | MQ trigger: process INQA requests, read ACCTDAT VSAM, reply via MQ |
| CODATE01 | CDRD | MQ trigger: return current system date/time via MQ reply |

---

## 4. CICS Transaction Registry

Complete mapping of CICS transactions to programs, derived from CSD definitions:

| Transaction ID | Program | Module | Description |
|----------------|---------|--------|-------------|
| CC00 | COSGN00C | Base | Sign-on |
| CM00 | COMEN01C | Base | Main menu |
| CA00 | COADM01C | Base | Admin menu |
| CAVW | COACTVWC | Base | Account view |
| CT00 | COTRN00C | Base | Transaction list |
| CCDL | COCRDSLC | Base | Card view |
| CU00 | COUSR00C | Base | User list |
| CR00 | CORPT00C | Base | Reports |
| CPVS | COPAUS0C | Authorization | Auth summary |
| CPVD | COPAUS1C | Authorization | Auth detail |
| CP00 | COPAUA0C | Authorization | Auth MQ processor |
| CTLI | COTRTLIC | Tran Type DB2 | Tran type list |
| CTTU | COTRTUPC | Tran Type DB2 | Tran type maint |
| CDRA | COACCT01 | VSAM-MQ | Account inquiry (MQ) |
| CDRD | CODATE01 | VSAM-MQ | Date inquiry (MQ) |

---

## 5. Screen Navigation Map

### Complete Screen Flow Diagram

```
                              ┌────────────┐
                              │  COSGN00C  │
                              │  Sign-On   │
                              │  (CC00)    │
                              └─────┬──────┘
                                    │ Authentication
                         ┌──────────┴──────────┐
                         │                     │
                    Admin User            Regular User
                         │                     │
                         ▼                     ▼
                  ┌────────────┐        ┌────────────┐
                  │  COADM01C  │        │  COMEN01C  │
                  │ Admin Menu │        │ Main Menu  │
                  │  (CA00)    │        │  (CM00)    │
                  └─────┬──────┘        └─────┬──────┘
                        │                     │
       ┌────────────────┤              ┌──────┼──────────────────────────────┐
       │                │              │      │      │      │      │        │
       ▼                ▼              ▼      ▼      ▼      ▼      ▼        ▼
  ┌─────────┐    ┌──────────┐   ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
  │User Mgmt│    │Tran Type │   │Account ││Card    ││Transact││Reports ││  More  │
  │ Suite   │    │  Suite   │   │ Suite  ││ Suite  ││ Suite  ││        ││        │
  └────┬────┘    └────┬─────┘   └───┬────┘└───┬────┘└───┬────┘└────────┘└────────┘
       │              │             │          │         │
       ▼              ▼             ▼          ▼         ▼
  (See below)    (See below)  (See below)(See below)(See below)
```

### User Management Flow (Admin Only)

```
COADM01C ──► COUSR00C (User List) ──► COUSR02C (Update selected)
   │              │                         │
   │              └───────────────────► COUSR03C (Delete selected)
   │
   ├──► COUSR01C (Add New User)
   ├──► COUSR02C (Update User - direct)
   └──► COUSR03C (Delete User - direct)

Navigation:
  COUSR00C: Select 'U' → COUSR02C, Select 'D' → COUSR03C
  All user screens: PF3 → COADM01C (Admin Menu)
```

### Account Management Flow

```
COMEN01C ──► COACTVWC (Account View)
   │              │ Enter Account ID
   │              ▼
   │         Display account details (read-only)
   │         PF3 → COMEN01C
   │
   └──► COACTUPC (Account Update)
              │ Enter Account ID
              ▼
         Edit account fields
         PF5 = Save, PF12 = Cancel
         PF3 → COMEN01C
```

### Credit Card Management Flow

```
COMEN01C ──► COCRDLIC (Card List)
   │              │ Page through cards (PF7/PF8)
   │              │ Select card number
   │              ▼
   │         COCRDSLC (Card View) ◄──── COMEN01C (option 4)
   │              │ Read-only display
   │              │ PF3 → COMEN01C
   │
   └──► COCRDUPC (Card Update) ◄──── COMEN01C (option 5)
              │ Edit card details
              │ PF5 = Save, PF3 → COMEN01C
```

### Transaction Management Flow

```
COMEN01C ──► COTRN00C (Transaction List)
   │              │ Paginated browse (PF7/PF8)
   │              │ Select transaction
   │              ▼
   │         COTRN01C (Transaction Detail)
   │              │ Read-only view
   │              │ PF3 → COTRN00C
   │
   ├──► COTRN01C (Transaction View - direct)
   │
   └──► COTRN02C (Transaction Add)
              │ Enter account/card + amount
              │ PF5 = Save
              │ PF3 → COMEN01C
```

### Authorization Flow

```
COMEN01C ──► COPAUS0C (Auth Summary List)
                  │ Browse pending authorizations (PF7/PF8)
                  │ Select row
                  ▼
             COPAUS1C (Auth Detail View)
                  │ View authorization details
                  │ PF5 = Toggle Fraud Flag
                  │       └──► COPAUS2C (DB2 update) ──► return to COPAUS1C
                  │ PF3 → COPAUS0C
```

### Transaction Type Flow (Admin Only)

```
COADM01C ──► COTRTLIC (Tran Type List)
   │              │ Page through types (PF7/PF8)
   │              │ Select 'U' = Update, 'D' = Delete
   │              ▼
   │         COTRTUPC (Tran Type Add/Edit)
   │              │ 15-state state machine
   │              │ PF5 = Save, PF3 → COTRTLIC
   │
   └──► COTRTUPC (Tran Type Maintenance - direct)
```

### Other Screens

```
COMEN01C ──► COBIL00C (Bill Payment)
   │              │ Two-phase: lookup then confirm
   │              │ PF3 → COMEN01C
   │
   └──► CORPT00C (Report Request)
              │ Select report type + date range
              │ Submits JCL via TDQ
              │ PF3 → COMEN01C
```

---

## 6. End-to-End Transaction Flows

### 6.1 User Login Flow

```
Step 1: User enters transaction CC00 on 3270 terminal
Step 2: CICS starts COSGN00C (first time: EIBCALEN=0)
Step 3: COSGN00C sends COSGN0A map (sign-on screen) with APPLID/SYSID
Step 4: User enters User ID + Password, presses ENTER
Step 5: CICS restarts COSGN00C (EIBCALEN > 0, pseudo-conversational)
Step 6: COSGN00C receives COSGN0A map
Step 7: Validates non-blank User ID
Step 8: READ USRSEC VSAM file with User ID as key
Step 9: Compares entered password with stored password (plain-text)
Step 10: On success:
         - Sets CDEMO-USER-ID and CDEMO-USER-TYPE in COMMAREA
         - If CDEMO-USRTYP-ADMIN: XCTL to COADM01C
         - If CDEMO-USRTYP-USER:  XCTL to COMEN01C
Step 11: On failure: redisplays sign-on screen with error message
```

### 6.2 View Account Details Flow

```
Step 1: User selects "Account View" (option 1) from main menu
Step 2: COMEN01C validates option, XCTL to COACTVWC with COMMAREA
Step 3: COACTVWC displays COACTVW map with account ID input field
Step 4: User enters Account ID, presses ENTER
Step 5: COACTVWC reads ACCTDAT VSAM with account ID
Step 6: Reads CUSTDAT VSAM for customer details
Step 7: Reads CARDAIX (alternate index) for associated card numbers
Step 8: Populates all screen fields and sends COACTVW map
Step 9: User views data; PF3 returns to COMEN01C
```

### 6.3 Add Transaction Flow

```
Step 1: User selects "Transaction Add" (option 8) from main menu
Step 2: COMEN01C XCTL to COTRN02C
Step 3: COTRN02C displays COTRN02 map (blank form)
Step 4: User enters Account ID or Card Number + transaction details
Step 5: COTRN02C validates:
        - Account exists (READ ACCTDAT)
        - Card exists and belongs to account (READ CCXREF)
        - Amount is numeric and valid
Step 6: Generates new Transaction ID:
        - STARTBR TRANSACT with HIGH-VALUES key
        - READPREV to get highest existing ID
        - Increments by 1 (race condition risk in high-volume)
Step 7: WRITE to TRANSACT VSAM with new transaction record
Step 8: Displays confirmation message
```

### 6.4 Credit Card Authorization Flow (MQ-Triggered)

```
Step 1: External system places authorization request on MQ input queue
Step 2: CICS MQ trigger monitor detects message, starts COPAUA0C (tran CP00)
Step 3: COPAUA0C opens error queue, input queue, output queue
Step 4: MQGET reads request message
Step 5: Validates card number via READ CARDDAT VSAM
Step 6: Reads CCXREF to get account cross-reference
Step 7: Reads ACCTDAT for account status/credit limit
Step 8: Applies authorization rules (credit limit check, account status)
Step 9: If approved: DL/I ISRT to PAUTHDTL IMS database (pending auth)
Step 10: Builds response message (approved/declined + reason)
Step 11: MQPUT response to output queue
Step 12: CICS SYNCPOINT to commit
Step 13: Loop back to MQGET for next message until queue empty
```

### 6.5 View Pending Authorizations (Online)

```
Step 1: User selects "Pending Authorization View" (option 11) from main menu
Step 2: COMEN01C does CICS INQUIRE PROGRAM on COPAUS0C (special check)
Step 3: XCTL to COPAUS0C
Step 4: COPAUS0C issues DL/I GU (Get Unique) then GN (Get Next) calls
        to PAUTHSUM IMS database to build summary list
Step 5: Displays COPAU00 map with paginated list of pending authorizations
Step 6: User selects a row, presses ENTER
Step 7: COPAUS0C passes selected card number in COMMAREA, XCTL to COPAUS1C
Step 8: COPAUS1C issues DL/I GU to PAUTHDTL for detail record
Step 9: Displays COPAU01 map with full authorization details
Step 10: User can press PF5 to toggle fraud flag:
         - COPAUS1C LINK to COPAUS2C
         - COPAUS2C issues DB2 INSERT/UPDATE on AUTHFRDS table
         - Returns to COPAUS1C which refreshes display
Step 11: PF3 returns to COPAUS0C summary list
```

### 6.6 Report Generation Flow

```
Step 1: User selects "Transaction Reports" (option 9) from main menu
Step 2: COMEN01C XCTL to CORPT00C
Step 3: CORPT00C displays CORPT00 map with:
        - Report type selection (Monthly/Yearly/Custom)
        - Start/End date fields
Step 4: User selects report options, presses ENTER
Step 5: CORPT00C validates date ranges using CSUTLDTC (LINK)
Step 6: Builds JCL for TRANREPT job with parameters
Step 7: Writes JCL to TDQ named 'JOBS' for internal reader submission
Step 8: Displays confirmation message with job submission status
```

### 6.7 Batch Statement Generation Flow

```
JCL Step 1: CBSTM03A reads ACCTDAT and TRANSACT VSAM files
            - For each account, collects all transactions in date range
            - Formats statement line items
            - Writes intermediate statement file
JCL Step 2: CBSTM03B reads intermediate statement file
            - Formats final print output
            - Produces printed statements
```

### 6.8 MQ Account Inquiry Flow

```
Step 1: External system places INQA request on MQ queue for COACCT01
Step 2: CICS MQ trigger starts COACCT01 (tran CDRA)
Step 3: COACCT01 opens error/input/output MQ queues
Step 4: MQGET reads request; validates WS-FUNC='INQA' and WS-KEY > 0
Step 5: Reads ACCTDAT VSAM with account number key
Step 6: Builds reply with account details (note: ZIP code is dropped)
Step 7: MQPUT reply to output queue
Step 8: SYNCPOINT and loop for next message
```

---

## 7. Inter-Program Dependencies

### Program Call Graph (XCTL Transfers)

```
COSGN00C ─── XCTL ──► COADM01C (admin users)
         ─── XCTL ──► COMEN01C (regular users)

COMEN01C ─── XCTL ──► COACTVWC (Account View)
         ─── XCTL ──► COACTUPC (Account Update)
         ─── XCTL ──► COCRDLIC (Card List)
         ─── XCTL ──► COCRDSLC (Card View)
         ─── XCTL ──► COCRDUPC (Card Update)
         ─── XCTL ──► COTRN00C (Transaction List)
         ─── XCTL ──► COTRN01C (Transaction View)
         ─── XCTL ──► COTRN02C (Transaction Add)
         ─── XCTL ──► CORPT00C (Reports)
         ─── XCTL ──► COBIL00C (Bill Payment)
         ─── XCTL ──► COPAUS0C (Auth Summary)

COADM01C ─── XCTL ──► COUSR00C (User List)
         ─── XCTL ──► COUSR01C (User Add)
         ─── XCTL ──► COUSR02C (User Update)
         ─── XCTL ──► COUSR03C (User Delete)
         ─── XCTL ──► COTRTLIC (Tran Type List)
         ─── XCTL ──► COTRTUPC (Tran Type Maint)

COACTVWC ─── XCTL ──► COMEN01C (PF3 return)
COACTUPC ─── XCTL ──► COMEN01C (PF3 return)
COCRDLIC ─── XCTL ──► COMEN01C (PF3 return)
COCRDSLC ─── XCTL ──► COMEN01C (PF3 return)
COCRDUPC ─── XCTL ──► COMEN01C (PF3 return)
COTRN00C ─── XCTL ──► COMEN01C (PF3 return)
COTRN01C ─── XCTL ──► COTRN00C (PF3 return)
COTRN02C ─── XCTL ──► COMEN01C (PF3 return)
COBIL00C ─── XCTL ──► COMEN01C (PF3 return)
CORPT00C ─── XCTL ──► COMEN01C (PF3 return)

COUSR00C ─── XCTL ──► COADM01C (PF3 return)
         ─── XCTL ──► COUSR02C (Update selected)
         ─── XCTL ──► COUSR03C (Delete selected)
COUSR01C ─── XCTL ──► COADM01C (PF3 return)
COUSR02C ─── XCTL ──► COADM01C (PF3 return)
COUSR03C ─── XCTL ──► COADM01C (PF3 return)

COPAUS0C ─── XCTL ──► COMEN01C (PF3 return)
         ─── XCTL ──► COPAUS1C (View selected detail)
COPAUS1C ─── XCTL ──► COPAUS0C (PF3 return)
         ─── LINK ──► COPAUS2C (Fraud toggle)

COTRTLIC ─── XCTL ──► COADM01C (PF3 return)
         ─── XCTL ──► COTRTUPC (Edit selected)
COTRTUPC ─── XCTL ──► COTRTLIC (PF3 return)
```

### Program LINK Calls (Subroutines)

```
CORPT00C ─── LINK ──► CSUTLDTC (Date validation)
COACTUPC ─── LINK ──► CSUTLDTC (Date validation)
COTRN02C ─── LINK ──► CSUTLDTC (Date validation)
COPAUS1C ─── LINK ──► COPAUS2C (DB2 fraud flag update)
```

### Shared Copybook Dependencies

```
COCOM01Y.cpy ──► Used by ALL online programs (CARDDEMO-COMMAREA)
COTTL01Y.cpy ──► Used by ALL online programs (screen title constants)
CSDAT01Y.cpy ──► Used by ALL online programs (date/time fields)
CSMSG01Y.cpy ──► Used by ALL online programs (common error messages)
CSMSG02Y.cpy ──► Used by most online programs (additional messages)
CSUSR01Y.cpy ──► Used by ALL online programs (signed-on user data)
DFHAID    ──► Used by ALL online programs (AID key constants)
DFHBMSCA  ──► Used by ALL online programs (BMS attribute constants)
```

---

## 8. Data Architecture

### 8.1 VSAM Files

| CICS File Name | Dataset Name | Type | Key | Record Description |
|----------------|-------------|------|-----|-------------------|
| ACCTDAT | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | KSDS | Account ID (11 bytes) | Account master: ID, status, credit limit, balances, customer ID, dates |
| CARDDAT | AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS | KSDS | Card Number (16 bytes) | Card master: number, account ID, CVV, expiry, name, status |
| CARDAIX | AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX.PATH | AIX Path | Account ID (alternate) | Alternate index over CARDDAT by account ID |
| CCXREF | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | KSDS | Card Number (16 bytes) | Card-to-account cross-reference |
| CXACAIX | AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.PATH | AIX Path | Account ID (alternate) | Alternate index over CCXREF by account ID |
| CUSTDAT | AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | KSDS | Customer ID (9 bytes) | Customer master: name, address, SSN, DOB, phone, FICO |
| TRANSACT | AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | KSDS | Transaction ID (16 bytes) | Transaction records: ID, type, category, amount, card, timestamp |
| USRSEC | AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS | KSDS | User ID (8 bytes) | User security: ID, password, first/last name, user type (A/U) |

### 8.2 DB2 Tables

| Table | Schema | Columns | Used By |
|-------|--------|---------|---------|
| AUTHFRDS | - | Card number, timestamp, auth amount, merchant, fraud flag | COPAUS2C (insert/update fraud flags) |
| TRNTYPE | CARDDEMO | TR_TYPE CHAR(2), TR_TYPE_DESC CHAR(50) | COTRTLIC, COTRTUPC, COBTUPDT |
| TRNTYCAT | CARDDEMO | Category code, description | COTRTLIC (DCL included but not queried) |

### 8.3 IMS Databases

| Database | DBD Name | Segment | Key | Purpose |
|----------|----------|---------|-----|---------|
| Pending Auth Detail | PAUTHDTL | Detail segment | Card Number + Inverted Timestamp | Individual authorization records |
| Pending Auth Summary | PAUTHSUM | Summary segment | Card Number | Aggregated authorization summaries per card |

### 8.4 MQ Queues

| Queue | Direction | Used By | Message Content |
|-------|-----------|---------|----------------|
| Auth Request Queue | Input | COPAUA0C | Authorization request (card, amount, merchant) |
| Auth Response Queue | Output | COPAUA0C | Authorization response (approved/declined + reason) |
| Auth Error Queue | Error | COPAUA0C | Error messages for failed processing |
| Account Inquiry Input | Input | COACCT01 | INQA function + account key |
| Account Inquiry Output | Output | COACCT01 | Account details reply |
| Date Inquiry Input | Input | CODATE01 | Any message (no validation) |
| Date Inquiry Output | Output | CODATE01 | Current date/time |

### 8.5 Entity Relationship Summary

```
  CUSTOMER (CUSTDAT)
      │ 1
      │
      │ N
  ACCOUNT (ACCTDAT) ◄───────► CARD-XREF (CCXREF)
      │ 1                           │
      │                             │
      │ N                           │ 1
  TRANSACTION (TRANSACT)      CARD (CARDDAT)
      │                             │
      │ N:1                         │ 1
  TRAN-TYPE (DB2:TRNTYPE)          │ N
                              PENDING-AUTH (IMS:PAUTHDTL)
                                    │
                              FRAUD-FLAG (DB2:AUTHFRDS)
```

---

## 9. Batch Processing Flows

### 9.1 JCL Job Inventory

#### Account Processing Jobs

| JCL | Programs | Purpose |
|-----|----------|---------|
| ACCTFILE.jcl | - | Define/load ACCTDAT VSAM cluster |
| READACCT.jcl | CBACT01C | Read and report on account file |

#### Card Processing Jobs

| JCL | Programs | Purpose |
|-----|----------|---------|
| CARDFILE.jcl | - | Define/load CARDDAT VSAM cluster |
| READCARD.jcl | - | Read and report on card file |

#### Customer Processing Jobs

| JCL | Programs | Purpose |
|-----|----------|---------|
| CUSTFILE.jcl | - | Define/load CUSTDAT VSAM cluster |
| READCUST.jcl | CBCUS01C | Read and report on customer file |
| DEFCUST.jcl | - | Define customer VSAM cluster |

#### Transaction Processing Jobs

| JCL | Programs | Purpose |
|-----|----------|---------|
| TRANFILE.jcl | - | Define/load TRANSACT VSAM cluster |
| COMBTRAN.jcl | - | Combine/merge transaction files |
| POSTTRAN.jcl | - | Post transactions to accounts |
| TRANBKP.jcl | - | Backup transaction file |
| TRANCATG.jcl | - | Catalog transaction data |
| TRANIDX.jcl | - | Build transaction indexes |
| TRANREPT.jcl | CBTRN02C | Generate transaction reports |
| TRANTYPE.jcl | - | Transaction type processing |
| DALYREJS.jcl | - | Process daily rejects |
| INTCALC.jcl | - | Interest calculation |

#### Statement and Report Jobs

| JCL | Programs | Purpose |
|-----|----------|---------|
| CREASTMT.JCL | CBSTM03A, CBSTM03B | Generate credit card statements |
| REPTFILE.jcl | - | Report file processing |
| PRTCATBL.jcl | - | Print catalog |
| TXT2PDF1.JCL | - | Convert text reports to PDF |

#### Data Exchange Jobs

| JCL | Programs | Purpose |
|-----|----------|---------|
| CBEXPORT.jcl | CBEXPORT | Export data from VSAM to flat file |
| CBIMPORT.jcl | CBIMPORT | Import data from flat file to VSAM |
| FTPJCL.JCL | - | FTP file transfer |

#### Administrative Jobs

| JCL | Programs | Purpose |
|-----|----------|---------|
| DUSRSECJ.jcl | - | User security maintenance |
| CBADMCDJ.jcl | - | Admin card job |
| OPENFIL.jcl | - | Open CICS files |
| CLOSEFIL.jcl | - | Close CICS files |
| XREFFILE.jcl | - | Cross-reference file processing |
| READXREF.jcl | - | Read cross-reference data |
| WAITSTEP.jcl | COBSWAIT | MVS wait step |

#### Authorization Batch Jobs

| JCL | Programs | Purpose |
|-----|----------|---------|
| CBPAUP0J.jcl | CBPAUP0C | Purge expired pending authorizations |
| DBPAUTP0.jcl | - | DB2 authorization processing |
| LOADPADB.JCL | PAUDBLOD | Load authorization IMS database |
| UNLDPADB.JCL | PAUDBUNL | Unload authorization IMS database |
| UNLDGSAM.JCL | DBUNLDGS | Unload GSAM data |

#### Transaction Type DB2 Jobs

| JCL | Programs | Purpose |
|-----|----------|---------|
| CREADB21.jcl | - | Create DB2 tables for transaction types |
| MNTTRDB2.jcl | COBTUPDT | Batch maintenance of transaction types |
| TRANEXTR.jcl | - | Extract transaction data |

### 9.2 Typical Batch Processing Sequence

```
Daily Cycle:
  1. CLOSEFIL.jcl     - Close CICS files for batch window
  2. TRANBKP.jcl      - Backup transaction file
  3. POSTTRAN.jcl      - Post pending transactions
  4. INTCALC.jcl       - Calculate interest charges
  5. DALYREJS.jcl      - Process daily rejects
  6. CBPAUP0J.jcl      - Purge expired authorizations
  7. OPENFIL.jcl       - Reopen CICS files

Monthly Cycle:
  8. CREASTMT.JCL      - Generate statements (CBSTM03A → CBSTM03B)
  9. TXT2PDF1.JCL      - Convert statements to PDF
  10. TRANREPT.jcl     - Monthly transaction reports
```

---

## 10. Asynchronous Processing (MQ)

### MQ Trigger Architecture

Both VSAM-MQ programs (COACCT01, CODATE01) and the authorization processor (COPAUA0C) follow an identical MQ trigger listener pattern:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ External App │     │   MQ Queue   │     │ CICS Trigger │
│  (Requester) │────►│  (Input)     │────►│   Monitor    │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │ Starts program
                                                  ▼
                                          ┌──────────────┐
                                          │ COBOL Program│
                                          │ (MQ Listener)│
                                          └──────┬───────┘
                                                  │
                              ┌────────────────────┼────────────────────┐
                              ▼                    ▼                    ▼
                      ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
                      │  Process     │    │ MQPUT Reply  │    │ SYNCPOINT    │
                      │  (VSAM/IMS)  │    │ (Output Q)   │    │ (Commit)     │
                      └──────────────┘    └──────────────┘    └──────────────┘
```

**Processing Loop:**
1. Open error queue, input queue, output queue
2. Initial MQGET (outside loop)
3. Loop: SYNCPOINT → MQGET → Process → MQPUT → repeat
4. Exit when MQRC-NO-MSG-AVAILABLE
5. All operations under CICS syncpoint scope
6. CSD `ACTION(BACKOUT)` ensures message requeue on abnormal termination

---

## 11. Copybook Inventory

### Common Copybooks (app/cpy/)

| Copybook | Purpose | Used By |
|----------|---------|---------|
| COCOM01Y | CARDDEMO-COMMAREA - inter-program communication area | All online programs |
| COADM02Y | Admin menu option table (6 options) | COADM01C |
| COMEN02Y | Main menu option table (11 options) | COMEN01C |
| COTTL01Y | Screen title constants | All online programs |
| CSDAT01Y | Date/time working storage | All online programs |
| CSLKPCDY | Lockpad/security structure | Security programs |
| CSMSG01Y | Common messages (invalid key, thank you) | All online programs |
| CSMSG02Y | Additional messages | Most online programs |
| CSSETATY | Attribute settings | Screen programs |
| CSSTRPFY | String format utilities | Various programs |
| CSUSR01Y | Signed-on user data | All online programs |
| CSUTLDPY | Date utility parameters (for CSUTLDTC) | Programs calling date validation |
| CSUTLDWY | Date utility work areas | CSUTLDTC |
| CODATECN | Date conversion routines | Date-related programs |
| CUSTREC | Customer record layout | Customer programs |
| CVACT01Y-03Y | Account view structures | Account programs |
| CVCRD01Y | Card view structure | Card programs |
| CVCUS01Y | Customer view structure | Customer programs |
| CVTRA01Y-07Y | Transaction view structures (7 variants) | Transaction programs |
| CVEXPORT | Export data structure | CBEXPORT |
| COSTM01 | Statement structure | Statement programs |

### BMS Copybooks (app/cpy-bms/)

Each BMS map generates a corresponding copybook with input (xxxI) and output (xxxO) structures:

| Copybook | Map | Contains |
|----------|-----|----------|
| COSGN00.CPY | COSGN0A | COSGN0AI/COSGN0AO - sign-on fields |
| COMEN01.CPY | COMEN1A | COMEN1AI/COMEN1AO - menu fields |
| COADM01.CPY | COADM1A | COADM1AI/COADM1AO - admin menu fields |
| COACTUP.CPY | COACTUPA | COACTUPAI/COACTUPAO - account update fields |
| COACTVW.CPY | COACTVWA | COACTVWAI/COACTVWAO - account view fields |
| COBIL00.CPY | COBIL0A | COBIL0AI/COBIL0AO - billing fields |
| COCRDLI.CPY | CCRDLIA | CCRDLIAI/CCRDLIAO - card list fields |
| COCRDSL.CPY | CCRDSLA | CCRDSLAI/CCRDSLAO - card select fields |
| COCRDUP.CPY | CCRDUPA | CCRDUPAI/CCRDUPAO - card update fields |
| CORPT00.CPY | CORPT0A | CORPT0AI/CORPT0AO - report fields |
| COTRN00.CPY | COTRN0A | COTRN0AI/COTRN0AO - transaction list fields |
| COTRN01.CPY | COTRN1A | COTRN1AI/COTRN1AO - transaction detail fields |
| COTRN02.CPY | COTRN2A | COTRN2AI/COTRN2AO - transaction add fields |
| COUSR00.CPY | COUSR0A | COUSR0AI/COUSR0AO - user list fields |
| COUSR01.CPY | COUSR1A | COUSR1AI/COUSR1AO - user add fields |
| COUSR02.CPY | COUSR2A | COUSR2AI/COUSR2AO - user update fields |
| COUSR03.CPY | COUSR3A | COUSR3AI/COUSR3AO - user delete fields |

### Authorization Extension Copybooks

| Copybook | Purpose |
|----------|---------|
| CCPAUERY | Authorization error logging structure |
| CCPAURLY | Authorization response layout |
| CCPAURQY | Authorization request layout |
| CIPAUDTY | IMS pending auth detail segment |
| CIPAUSMY | IMS pending auth summary segment |
| IMSFUNCS | IMS DL/I function codes |
| PADFLPCB | IMS PCB for auth detail (flat) |
| PASFLPCB | IMS PCB for auth summary (flat) |
| PAUTBPCB | IMS PCB for auth both |

### Transaction Type DB2 Copybooks

| Copybook | Purpose |
|----------|---------|
| CSDB2RPY | DB2 read/process structure |
| CSDB2RWY | DB2 read/write structure |
| DCLTRCAT | DCL for TRNTYCAT table |
| DCLTRTYP | DCL for TRNTYPE table |

---

## 12. Known Issues and Anomalies

The following issues were identified during code analysis:

### Security Concerns

| Issue | Location | Description |
|-------|----------|-------------|
| Plain-text passwords | COSGN00C | Passwords stored and compared in plain text in USRSEC VSAM |
| No session timeout | All programs | No idle timeout mechanism; sessions persist indefinitely |
| No password masking storage | USRSEC | Password field stored as-is in VSAM record |

### Concurrency Risks

| Issue | Location | Description |
|-------|----------|-------------|
| Transaction ID race condition | COTRN02C | New ID generated via READPREV from HIGH-VALUES; concurrent users could get duplicate IDs |
| Unnecessary UPDATE lock | COTRN01C | READ TRANSACT with UPDATE option for display-only operation; holds exclusive lock |

### Code Quality Issues

| Issue | Location | Description |
|-------|----------|-------------|
| Missing COMMIT | COBTUPDT | No SQL COMMIT issued after DB2 DML operations |
| Error continues after ABEND | COBTUPDT | 9999-ABEND sets RC=4 but does not issue STOP RUN |
| Copy-paste error message | COUSR03C | Delete failure shows "Update" error message (copied from COUSR02C) |
| Dead working storage | COUSR03C | WS-USR-MODIFIED declared but never referenced |
| Dead working storage | CODATE01 | LIT-ACCTFILENAME, WS-RESP-CD, WS-REAS-CD declared but unused |
| Misspelled paragraph | CORPT00C | WIRTE-JOBSUB-TDQ (should be WRITE) |
| ZIP code dropped | COACCT01 | ACCT-ADDR-ZIP read from VSAM but not included in MQ reply |
| Hardcoded JCL path | CORPT00C | 'AWS.M2.CARDDEMO.PROC' JCLLIB path hardcoded |
| No ASKTIME error handling | CODATE01 | ASKTIME/FORMATTIME have no RESP/RESP2 checking |
| F6 label never activated | COTRTUPC | BMS includes F6=Add label that program logic never shows |
| Unused DCL | COTRTUPC | DCLTRCAT included but no SQL against TRANSACTION_TYPE_CATEGORY |
| Row 8 dummy data | COTRTLI BMS | 8th data row defined but never populated by COTRTLIC |

### Architectural Observations

| Observation | Description |
|-------------|-------------|
| Mixed data stores | System uses VSAM, DB2, and IMS simultaneously - different stores for different functions |
| No centralized logging | No application-level audit trail or centralized logging mechanism |
| COMMAREA size fixed | CARDDEMO-COMMAREA is a fixed structure; extensions use separate commarea fields |
| Menu options hardcoded | Menu options defined in copybooks (COMEN02Y, COADM02Y) rather than configuration |

---

## 13. File Inventory

### Complete Artifact Count

| Artifact Type | Base | Authorization | Tran Type DB2 | VSAM-MQ | Total |
|---------------|------|---------------|---------------|---------|-------|
| COBOL Programs | 31 | 8 | 3 | 2 | **44** |
| BMS Maps | 17 | 2 | 2 | 0 | **21** |
| Data Copybooks | 30 | 9 | 4 | 0 | **43** |
| BMS Copybooks | 17 | 2 | 2 | 0 | **21** |
| JCL Jobs | 38 | 5 | 3 | 0 | **46** |
| DDL Files | 0 | 2 | 4 | 0 | **6** |
| DCL Files | 0 | 1 | 2 | 0 | **3** |
| CSD Files | 1 | 1 | 1 | 1 | **4** |
| CTL Files | 1 | 0 | 7 | 0 | **8** |
| ASM/Macro | 4 | 0 | 0 | 0 | **4** |
| **Total** | **139** | **30** | **28** | **3** | **200** |

### Tech Specs Document Index

All technical specification documents are located in the `tech_specs/` directory:

```
tech_specs/
├── overall-system-specification.md          (this document)
├── programs/
│   ├── base/
│   │   ├── CBACT01C.md through CBACT04C.md  (account batch programs)
│   │   ├── CBCUS01C.md                      (customer batch)
│   │   ├── CBEXPORT.md, CBIMPORT.md         (data exchange)
│   │   ├── CBSTM03A.md, CBSTM03B.md        (statement generation)
│   │   ├── CBTRN01C.md through CBTRN03C.md  (transaction batch)
│   │   ├── COACTUPC.md, COACTVWC.md         (account online)
│   │   ├── COADM01C.md                      (admin menu)
│   │   ├── COBIL00C.md                      (billing)
│   │   ├── COBSWAIT.md                      (wait utility)
│   │   ├── COCRDLIC.md, COCRDSLC.md, COCRDUPC.md  (card management)
│   │   ├── COMEN01C.md                      (main menu)
│   │   ├── CORPT00C.md                      (reports)
│   │   ├── COSGN00C.md                      (sign-on)
│   │   ├── COTRN00C.md through COTRN02C.md  (transaction online)
│   │   ├── COUSR00C.md through COUSR03C.md  (user management)
│   │   └── CSUTLDTC.md                      (date utility)
│   ├── authorization/
│   │   ├── CBPAUP0C.md                      (auth purge batch)
│   │   ├── COPAUA0C.md                      (auth MQ processor)
│   │   ├── COPAUS0C.md                      (auth summary online)
│   │   ├── COPAUS1C.md                      (auth detail online)
│   │   ├── COPAUS2C.md                      (fraud toggle)
│   │   ├── DBUNLDGS.md                      (GSAM unload)
│   │   ├── PAUDBLOD.md                      (IMS DB load)
│   │   └── PAUDBUNL.md                      (IMS DB unload)
│   ├── transaction-type-db2/
│   │   ├── COBTUPDT.md                      (batch maintenance)
│   │   ├── COTRTLIC.md                      (list online)
│   │   └── COTRTUPC.md                      (add/edit online)
│   └── vsam-mq/
│       ├── COACCT01-spec.md                 (account inquiry MQ)
│       └── CODATE01-spec.md                 (date inquiry MQ)
├── screens/
│   ├── base/
│   │   ├── COSGN00.md                       (sign-on screen)
│   │   ├── COMEN01.md                       (main menu screen)
│   │   ├── COADM01.md                       (admin menu screen)
│   │   ├── COACTUP.md                       (account update screen)
│   │   ├── COACTVW.md                       (account view screen)
│   │   ├── COBIL00.md                       (billing screen)
│   │   ├── COCRDLI.md                       (card list screen)
│   │   ├── COCRDSL.md                       (card select screen)
│   │   ├── COCRDUP.md                       (card update screen)
│   │   ├── CORPT00.md                       (report screen)
│   │   ├── COTRN00.md                       (transaction list screen)
│   │   ├── COTRN01.md                       (transaction detail screen)
│   │   ├── COTRN02.md                       (transaction add screen)
│   │   ├── COUSR00.md                       (user list screen)
│   │   ├── COUSR01.md                       (user add screen)
│   │   ├── COUSR02.md                       (user update screen)
│   │   └── COUSR03.md                       (user delete screen)
│   ├── authorization/
│   │   ├── COPAU00.md                       (auth summary screen)
│   │   └── COPAU01.md                       (auth detail screen)
│   └── transaction-type-db2/
│       ├── COTRTLI-CTRTLIA.md               (tran type list screen)
│       └── COTRTUP-CTRTUPA.md               (tran type update screen)
```

---

*Generated from source code analysis of the CardDemo mainframe application repository.*
