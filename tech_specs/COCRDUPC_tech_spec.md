# Technical Specification: COCRDUPC — Update Credit Card

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COCRDUPC |
| Source File | `app/cbl/COCRDUPC.cbl` |
| Type | CICS Online |
| Transaction ID | CCUP |
| BMS Mapset | COCRDUP |
| BMS Map | CCRDUPA |

## 2. Purpose

COCRDUPC **updates a credit card record** in the CARDDAT VSAM file. Editable fields include embossed name, card active status (Y/N), and expiration month/year with range validation.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| CVCRD01Y | CC-WORK-AREAS |
| COCOM01Y | CARDDEMO-COMMAREA |
| COCRDUP | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y, CSMSG02Y | Standard infrastructure |
| CSUSR01Y | User record layout |
| CVACT02Y | CARD-RECORD layout |
| CVCUS01Y | CUSTOMER-RECORD layout |
| CSSTRPFY | PF-key storage paragraph |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| CARDDAT | Update | READ with UPDATE, REWRITE | CARD-NUM X(16) |

## 5. Screen Fields

### Protected Output
| Field | Length | Description |
|-------|--------|-------------|
| ACCTSID | 11 | Account number (PROTECTED — cannot edit) |

### Editable Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| CARDSID | 16 | Card number |
| CRDNAME | 50 | Name on card |
| CRDSTCD | 1 | Card active Y/N |
| EXPMON | 2 | Expiry month (1–12) |
| EXPYEAR | 4 | Expiry year (1950–2099) |

### Hidden Fields
| Field | Description |
|-------|-------------|
| EXPDAY | Hidden expiry day (system-maintained) |
| FKEYSC | "F5=Save F12=Cancel" (initially dark, revealed dynamically) |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Process/validate |
| F3 | Exit |
| F5 | Save (revealed after validation passes) |
| F12 | Cancel |

## 6. Validation Rules

| Field | Rule |
|-------|------|
| Card name | Non-blank alphanumeric |
| Status | Must be 'Y' or 'N' (88-level FLG-YES-NO-VALID) |
| Expiry month | PIC 9(2), VALID-MONTH VALUE 1 THRU 12 |
| Expiry year | PIC 9(4), VALID-YEAR VALUE 1950 THRU 2099 |

## 7. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COCRDLIC | XCTL | Navigate to card list |
| COMEN01C | XCTL | PF3 or PF12 |
