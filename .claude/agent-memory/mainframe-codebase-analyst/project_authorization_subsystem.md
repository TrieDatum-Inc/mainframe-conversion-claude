---
name: Authorization Subsystem — IMS/DB2/MQ
description: Architecture and key findings for the CardDemo authorization subsystem (IMS, MQ, DB2, CICS batch utilities)
type: project
---

## Authorization Subsystem Components

**Location:** `/app/app-authorization-ims-db2-mq/`

### Programs Analyzed (all specs in /tech_specs/)

| Program | Type | Trans | Key Function |
|---------|------|-------|-------------|
| COPAUA0C | CICS+IMS+MQ | CP00 | Core auth decision engine; MQ-triggered, writes IMS |
| COPAUS0C | CICS+IMS+BMS | CPVS | Auth summary list; paged 5 records; IMS GNP |
| COPAUS1C | CICS+IMS+BMS | CPVD | Auth detail view; PF5 fraud toggle via COPAUS2C |
| COPAUS2C | CICS+DB2 | (none) | LINK sub-prog; INSERT/UPDATE CARDDEMO.AUTHFRDS |
| CBPAUP0C | Batch IMS | — | Housekeeping; delete expired auths (configurable days) |
| DBUNLDGS | Batch IMS+GSAM | — | Unload IMS auth DB to GSAM output datasets |
| PAUDBUNL | Batch IMS+seq | — | Unload IMS auth DB to flat sequential files |
| PAUDBLOD | Batch IMS+seq | — | Load IMS auth DB from flat files (PAUDBUNL output) |

### IMS Database Structure

**PSB:** PSBPAUTB  
**PCB numbers:** Programs use PCB(1) for online; CBPAUP0C uses PCB(2)

**Segment hierarchy:**
- **PAUTSUM0** (root) — 01 PENDING-AUTH-SUMMARY — copybook CIPAUSMY
  - Key: PA-ACCT-ID (S9(11) COMP-3)
  - Contains: credit/cash limits and balances, approved/declined counts and amounts
- **PAUTDTL1** (child) — 01 PENDING-AUTH-DETAILS — copybook CIPAUDTY
  - Key: PA-AUTHORIZATION-KEY (PA-AUTH-DATE-9C + PA-AUTH-TIME-9C)
  - Key encoding: COMPLEMENT (99999 - YYDDD, 999999999 - time-ms) for descending IMS sort
  - Contains: full auth record (card, merchant, amounts, response, fraud flag)

**IMS DBD field names used in SSAs:**
- ACCNTID = account ID field in PAUTSUM0
- PAUT9CTS = composite date+time key in PAUTDTL1

### MQ Architecture (COPAUA0C)

- Request queue name comes from MQ trigger message (MQTM-QNAME)
- Reply queue name comes from MQMD-REPLYTOQ of each request message
- Message format: comma-delimited text in W01-GET-BUFFER (500 bytes)
- Response format: comma-delimited text in W02-PUT-BUFFER (200 bytes)
- MQPUT1 used for reply (atomic open+put+close)
- Expiry on reply: 50 centiseconds (5 seconds)
- Max messages per invocation: 500 (WS-REQSTS-PROCESS-LIMIT)

### DB2 Table: CARDDEMO.AUTHFRDS

Written by COPAUS2C. Contains fraud-flagged authorization records.
Key: CARD_NUM + AUTH_TS (TIMESTAMP).
SQLCODE -803 (duplicate) triggers UPDATE instead of INSERT.
AUTH_FRAUD column: 'F' = fraud confirmed, 'R' = fraud removed.

### BMS Maps

| Mapset | Map | Program | Trans | Purpose |
|--------|-----|---------|-------|---------|
| COPAU00 | COPAU0A | COPAUS0C | CPVS | Auth summary list, 5 rows, account search |
| COPAU01 | COPAU1A | COPAUS1C | CPVD | Auth detail, read-only, PF5 fraud, PF8 next |

### Online Navigation Flow

```
COMEN01C --[XCTL]--> COPAUS0C (CPVS)
                         |-- 'S' + ENTER --[XCTL]--> COPAUS1C (CPVD)
                                                          |-- PF5 --[LINK]--> COPAUS2C
                                                          |-- PF3 --[XCTL]--> COPAUS0C
                         |-- PF3 --[XCTL]--> COMEN01C
```

### COMMAREA Conventions

COPAUS0C uses CDEMO-CPVS-INFO extension with paging keys (up to 20 pages of backward navigation via CDEMO-CPVS-PAUKEY-PREV-PG array).  
COPAUS1C uses CDEMO-CPVD-INFO extension with fraud data area (CDEMO-CPVD-FRAUD-DATA X(100)).

### Known Issues / Defects

1. **CBPAUP0C line 156:** Condition `PA-APPROVED-AUTH-CNT <= 0 AND PA-APPROVED-AUTH-CNT <= 0` repeats the same field twice (should be PA-DECLINED-AUTH-CNT in second clause). Summary deleted only when approved count is zero regardless of declined count.
2. **WS-PGMNAME in DBUNLDGS, PAUDBUNL, PAUDBLOD:** Hardcoded as 'IMSUNLOD' — not matching the actual program name. Template clone artifact.
3. **PAUDBLOD 3100-INSERT-CHILD-SEG:** Logic indentation of the abend check may not fire correctly if GU fails (nested IF structure issue at lines 305–314).

### Copybooks in /cpy/

CIPAUSMY.cpy — PAUTSUM0 root segment  
CIPAUDTY.cpy — PAUTDTL1 child segment  
CCPAURQY.cpy — MQ request message layout (18 fields, comma-delimited)  
CCPAURLY.cpy — MQ response message layout (6 fields)  
CCPAUERY.cpy — Error log record (ERR-DATE, ERR-PROGRAM, ERR-LEVEL, ERR-SUBSYSTEM, ERR-CODE-1/2, ERR-MESSAGE)  
IMSFUNCS.cpy — CBLTDLI function codes (GU, GHU, GN, GHN, GNP, GHNP, REPL, ISRT, DLET)  
PAUTBPCB.CPY — PAUTBPCB PCB mask  
PASFLPCB.CPY — PASFLPCB GSAM summary output PCB  
PADFLPCB.CPY — PADFLPCB GSAM detail output PCB  

**Why:** Full IMS/MQ/DB2 authorization subsystem requires careful understanding for migration to avoid breaking the MQ trigger pattern, the IMS complement-key sorting, and the DB2 fraud reporting integration.

**How to apply:** When generating migration specs or code for this subsystem, treat COPAUA0C as the authoritative data writer; COPAUS0C/1C/2C as read-mostly with single-record IMS REPL for fraud only. The batch utilities (PAUDBUNL/PAUDBLOD/DBUNLDGS/CBPAUP0C) are standalone jobs with no CICS dependency.
