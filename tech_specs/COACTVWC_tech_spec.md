# Technical Specification: COACTVWC — View Account Details

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COACTVWC |
| Source File | `app/cbl/COACTVWC.cbl` |
| Type | CICS Online |
| Transaction ID | CAVW |
| BMS Mapset | COACTVW |
| BMS Map | CACTVWA |

## 2. Purpose

COACTVWC displays the **complete detail of a credit card account** including account financial data (balance, credit limits, dates) and associated customer demographics (name, address, phone, SSN, FICO score). It also provides navigation to card list and card update screens.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| CVCRD01Y | CC-WORK-AREAS (screen navigation state) |
| COCOM01Y | CARDDEMO-COMMAREA |
| COACTVW | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y, CSMSG02Y | Standard infrastructure |
| CSUSR01Y | User record layout |
| CVACT01Y | ACCOUNT-RECORD layout |
| CVACT02Y | CARD-RECORD layout |
| CVACT03Y | CARD-XREF-RECORD layout |
| CVCUS01Y | CUSTOMER-RECORD layout |
| CSSTRPFY | PF-key storage paragraph |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| ACCTDAT | Read | READ by ACCT-ID | ACCT-ID 9(11) |
| CUSTDAT | Read | READ by CUST-ID | CUST-ID 9(9) |
| CARDAIX | Browse | STARTBR, READNEXT, ENDBR (alternate index by account) | ACCT-ID |
| CXACAIX | Read | READ by account | XREF-ACCT-ID 9(11) |

## 5. Screen Fields

### Input Fields
| Field | Length | Attributes | Description |
|-------|--------|------------|-------------|
| ACCTSID | 11 | UNPROT, PICIN='99999999999', MUSTFILL | Account ID (numeric only) |

### Output Fields — Account Financial Data
| Field | Description | Format |
|-------|-------------|--------|
| ACSTTUS | Account active Y/N | X(1) |
| ADTOPEN | Date opened | X(10) |
| ACRDLIM | Credit limit | +ZZZ,ZZZ,ZZZ.99 |
| AEXPDT | Expiry date | X(10) |
| ACSHLIM | Cash credit limit | +ZZZ,ZZZ,ZZZ.99 |
| AREISDT | Reissue date | X(10) |
| ACURBAL | Current balance | +ZZZ,ZZZ,ZZZ.99 |
| ACRCYCR | Current cycle credit | +ZZZ,ZZZ,ZZZ.99 |
| AADDGRP | Account group | X(10) |
| ACRCYDB | Current cycle debit | +ZZZ,ZZZ,ZZZ.99 |

### Output Fields — Customer Demographics
| Field | Description |
|-------|-------------|
| ACSTNUM | Customer ID |
| ACSTSSN | SSN (formatted) |
| ACSTDOB | Date of birth |
| ACSTFCO | FICO score |
| ACSFNAM / ACSMNAM / ACSLNAM | First / Middle / Last name |
| ACSADL1 / ACSADL2 | Address lines |
| ACSSTTE / ACSZIPC / ACSCITY / ACSCTRY | State / Zip / City / Country |
| ACSPHN1 / ACSPHN2 | Phone numbers |
| ACSGOVT | Government ID reference |
| ACSEFTC | EFT Account ID |
| ACSPFLG | Primary card holder Y/N |

### Function Keys
| Key | Action |
|-----|--------|
| F3 | Exit to menu |

## 6. Program Flow

```
1. Accept account ID input
2. READ ACCTDAT by ACCT-ID
3. READ CUSTDAT by ACCT-CUSTID (from account record)
4. Browse CARDAIX for associated cards
5. Populate all account and customer fields
6. SEND MAP
```

## 7. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COCRDLIC | XCTL | Navigate to card list |
| COCRDUPC | XCTL | Navigate to card update |
| COCRDSLC | XCTL | Navigate to card detail |
| COMEN01C | XCTL | PF3 return to menu |
