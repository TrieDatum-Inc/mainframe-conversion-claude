# Technical Specification: COCRDSLC — Credit Card Detail View

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COCRDSLC |
| Source File | `app/cbl/COCRDSLC.cbl` |
| Type | CICS Online |
| Transaction ID | CCDL |
| BMS Mapset | COCRDSL |
| BMS Map | CCRDSLA |

## 2. Purpose

COCRDSLC displays **all fields of a single credit card record**: card number, account ID, CVV, embossed name, active status, and expiration date. It serves as a search/lookup entry point for card detail.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| CVCRD01Y | CC-WORK-AREAS |
| COCOM01Y | CARDDEMO-COMMAREA |
| COCRDSL | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y, CSMSG02Y | Standard infrastructure |
| CSUSR01Y | User record layout |
| CVACT02Y | CARD-RECORD layout |
| CVCUS01Y | CUSTOMER-RECORD layout |
| CSSTRPFY | PF-key storage paragraph |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| CARDDAT | Read | READ by card number | CARD-NUM X(16) |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| ACCTSID | 11 | Account number (search key) |
| CARDSID | 16 | Card number (search key) |

### Output Fields
| Field | Length | Description |
|-------|--------|-------------|
| CRDNAME | 50 | Name on card |
| CRDSTCD | 1 | Card active (Y/N) |
| EXPMON | 2 | Expiry month |
| EXPYEAR | 4 | Expiry year |
| INFOMSG | 40 | Informational message |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Search and display card |
| F3 | Exit |

## 6. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COMEN01C | XCTL | PF3 or calling program |
