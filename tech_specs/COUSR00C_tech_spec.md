# Technical Specification: COUSR00C — User List (Browse)

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COUSR00C |
| Source File | `app/cbl/COUSR00C.cbl` |
| Type | CICS Online |
| Transaction ID | CU00 |
| BMS Mapset | COUSR00 |
| BMS Map | COUSR0A |

## 2. Purpose

COUSR00C is an **admin function** that provides a paginated browse of all user records in the USRSEC VSAM file. It displays 10 users per page with forward/backward paging. Users can select a row with 'U' (update) or 'D' (delete) to navigate to COUSR02C or COUSR03C respectively.

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA (extended with CDEMO-CU00-INFO) |
| COUSR00 | BMS symbolic map |
| COTTL01Y | Application title strings |
| CSDAT01Y | Date/time working storage |
| CSMSG01Y | Common screen messages |
| CSUSR01Y | SEC-USER-DATA record layout |
| DFHAID | CICS AID constants |
| DFHBMSCA | BMS field attribute constants |

## 4. VSAM Files Accessed

| File DD | Access Mode | Operations | Key |
|---------|-------------|------------|-----|
| USRSEC | Browse | STARTBR, READNEXT, READPREV, ENDBR | SEC-USR-ID X(8) |

## 5. Screen Fields

### Input Fields
| Field | Length | Description |
|-------|--------|-------------|
| USRIDIN | 8 | Search/filter by User ID (starting position) |
| SEL0001–SEL0010 | 1 each | Row selection ('U' = update, 'D' = delete) |

### Output Fields (10 rows)
| Field | Length | Description |
|-------|--------|-------------|
| USRID01–USRID10 | 8 each | User IDs |
| FNAME01–FNAME10 | 20 each | First names |
| LNAME01–LNAME10 | 20 each | Last names |
| UTYPE01–UTYPE10 | 1 each | User types (A/U) |
| PAGENUM | 8 | Current page number |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Process selection or refresh |
| PF3 | Back to admin menu (COADM01C) |
| PF7 | Page backward |
| PF8 | Page forward |

## 6. Program Flow

```
1. If EIBCALEN = 0 → redirect to COSGN00C

2. First entry:
   → STARTBR from beginning of USRSEC
   → READNEXT 10 records (fill page)
   → Peek at one more record to set NEXT-PAGE flag
   → Store first/last USR-ID in COMMAREA for page boundary tracking
   → SEND MAP

3. On ENTER with selection:
   → Scan SEL0001–SEL0010 for 'U' or 'D'
   → If 'U': set COMMAREA fields, XCTL to COUSR02C
   → If 'D': set COMMAREA fields, XCTL to COUSR03C

4. On PF8 (Forward):
   → STARTBR from last key on current page
   → READNEXT 10 records
   → Increment page counter

5. On PF7 (Backward):
   → STARTBR from first key on current page
   → READPREV 10 records
   → Decrement page counter
```

## 7. Pagination Logic

- Page boundaries tracked via `CDEMO-CU00-TRNID-FIRST` and `CDEMO-CU00-TRNID-LAST` in COMMAREA.
- Page number stored in `CDEMO-CU00-PAGE-NUM`.
- At top of file: "You are at the top" message.
- At bottom of file: "Bottom of page" message.

## 8. Inter-Program Communication

### Programs Called
| Target | Method | Condition |
|--------|--------|-----------|
| COUSR02C | XCTL | Row selected with 'U' |
| COUSR03C | XCTL | Row selected with 'D' |
| COADM01C | XCTL | PF3 |

## 9. Error Handling

| Condition | Message |
|-----------|---------|
| STARTBR NOTFND | "You are at the top" |
| READNEXT ENDFILE | "Bottom of page" |
| READPREV ENDFILE | "Top of page" |
| Other RESP | Display RESP/REAS codes |
