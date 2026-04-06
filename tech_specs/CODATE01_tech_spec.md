# Technical Specification: CODATE01 — Date MQ Service

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CODATE01 |
| Source File | `app/app-vsam-mq/cbl/CODATE01.cbl` |
| Type | CICS Online (MQ, IS INITIAL) |
| Sub-Application | app-vsam-mq |

## 2. Purpose

CODATE01 is an **MQ-driven date/time service**. Structurally identical to COACCT01 but instead of a VSAM read, it calls EXEC CICS ASKTIME / FORMATTIME to obtain the current system date and time, then returns it as a reply message.

## 3. Data Access

No VSAM or DB2. Uses:
- `EXEC CICS ASKTIME` → WS-ABS-TIME
- `EXEC CICS FORMATTIME` → WS-MMDDYYYY, WS-TIME

## 4. MQ Infrastructure

Same pattern as COACCT01:
- MQGET from input queue
- MQPUT formatted date/time to reply queue
- MQPUT errors to error queue

## 5. Copybooks Used

CMQGMOV, CMQPMOV, CMQMDV, CMQODV, CMQV, CMQTML (IBM MQ API)
