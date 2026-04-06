# Technical Specification: COACCT01 — Account MQ Service

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COACCT01 |
| Source File | `app/app-vsam-mq/cbl/COACCT01.cbl` |
| Type | CICS Online (MQ, IS INITIAL) |
| Sub-Application | app-vsam-mq |

## 2. Purpose

COACCT01 is an **MQ-driven account lookup service**. It receives request messages from an input queue, reads the ACCTDAT VSAM file by the account key in the message, and returns the account record to the reply queue. Errors go to an error queue.

## 3. MQ Infrastructure

| Operation | API | Description |
|-----------|-----|-------------|
| Connect | MQDISC/MQCONN | Queue manager connection |
| Open | MQOPEN | Open input, reply, and error queues |
| Get | MQGET | Read request message |
| Put | MQPUT | Send reply or error message |
| Close | MQCLOSE | Close all queues |

### Request Message Layout
| Field | PIC | Description |
|-------|-----|-------------|
| WS-FUNC | X(4) | Function code |
| WS-KEY | 9(11) | Account ID key |
| WS-FILLER | X(985) | Reserved |

## 4. VSAM Access

| File DD | Operation | Key |
|---------|-----------|-----|
| ACCTDAT | EXEC CICS READ NOHANDLE | WS-KEY (11-digit account ID) |

## 5. Processing Flow

```
1. MQOPEN input queue
2. MQGET request message
3. Extract WS-KEY (account ID) from message
4. EXEC CICS READ FILE('ACCTDAT') INTO(ACCOUNT-RECORD) RIDFLD(WS-KEY)
5. If found: MQPUT account record to reply queue
6. If not found: MQPUT error to error queue
7. MQCLOSE all queues
```

## 6. Copybooks Used

CMQGMOV, CMQPMOV, CMQMDV, CMQODV, CMQV, CMQTML (IBM MQ API)
