# Technical Specification: COCRDLIC — Credit Card List (Browse)

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COCRDLIC |
| Source File | `app/cbl/COCRDLIC.cbl` |
| Type | CICS Online |
| Transaction ID | CCLI |
| BMS Mapset | COCRDLI |
| BMS Map | CCRDLIA |

## 2. Purpose

COCRDLIC displays a **paginated list of credit cards**, 7 per page. If context contains an account ID, it filters to only that account's cards (via CARDAIX alternate index). Supports row selection: 'S' for detail view, 'U' for update.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| CVCRD01Y | CC-WORK-AREAS |
| COCOM01Y | CARDDEMO-COMMAREA |
| COCRDLI | BMS symbolic map |
| COTTL01Y, CSDAT01Y, CSMSG01Y | Standard infrastructure |
| CSUSR01Y | User record layout |
| CVACT02Y | CARD-RECORD layout |
| CSSTRPFY | PF-key storage paragraph |
| DFHAID, DFHBMSCA | CICS constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| CARDDAT | Browse | STARTBR, READNEXT, ENDBR | CARD-NUM X(16) |
| CARDAIX | Browse | STARTBR, READNEXT, ENDBR (by account) | CARD-ACCT-ID 9(11) |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| ACCTSID | 11 | Account number filter |
| CARDSID | 16 | Card number filter |
| CRDSEL1–CRDSEL7 | 1 each | Row selectors |

### Output Fields (7 rows)
| Field | Length | Description |
|-------|--------|-------------|
| ACCTNO1–ACCTNO7 | 11 each | Account numbers |
| CRDNUM1–CRDNUM7 | 16 each | Card numbers |
| CRDSTS1–CRDSTS7 | 1 each | Card statuses (Y/N) |
| PAGENO | 3 | Page number |

### Function Keys
| Key | Action |
|-----|--------|
| F3 | Exit to menu |
| F7 | Page backward |
| F8 | Page forward |

## 6. Selection Logic

- WS-EDIT-SELECT-FLAGS (7-byte array) tracks selection per row
- Validates at most one row selected (WS-EDIT-SELECT-COUNTER = 1)
- WS-SCREEN-DATA (7 rows x 28 chars) holds page data in COMMAREA

## 7. Inter-Program Communication

| Target | Method | Condition |
|--------|--------|-----------|
| COCRDSLC | XCTL | Row selected with 'S' |
| COCRDUPC | XCTL | Row selected with 'U' |
| COMEN01C | XCTL | PF3 |
