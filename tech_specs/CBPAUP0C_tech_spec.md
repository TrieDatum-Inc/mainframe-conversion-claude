# Technical Specification: CBPAUP0C — Expired Authorization Purge

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | CBPAUP0C |
| Source File | `app/app-authorization-ims-db2-mq/cbl/CBPAUP0C.cbl` |
| Type | Batch COBOL (IMS BMP) |
| JCL | CBPAUP0J.jcl |

## 2. Purpose

CBPAUP0C **purges expired authorization records** from the IMS DBPAUTP0 database. It walks all PAUTSUM0 root segments, iterates child PAUTDTL1 segments, deletes detail records older than the configured expiry threshold, and deletes empty summary records.

## 3. IMS Access (PSB PSBPAUTB, PCB +2)

| Operation | Segment | Description |
|-----------|---------|-------------|
| GN | PAUTSUM0 | Sequential scan of all root segments |
| GNP | PAUTDTL1 | Get next child under current parent |
| DLET | PAUTDTL1 | Delete expired detail |
| DLET | PAUTSUM0 | Delete root when both counts = 0 |
| CHKP | — | IMS restart checkpoint (ID format: RMADnnnn) |

## 4. Expiry Logic

The IMS detail segment stores dates as **9-complement** values:
```
COMPUTE WS-AUTH-DATE = 99999 - PA-AUTH-DATE-9C
COMPUTE WS-DAY-DIFF = CURRENT-YYDDD - WS-AUTH-DATE
If WS-DAY-DIFF >= WS-EXPIRY-DAYS → qualified for deletion
```

For each deleted record:
- If response='00' (approved): decrement PA-APPROVED-AUTH-CNT, subtract from PA-APPROVED-AUTH-AMT
- Otherwise: decrement PA-DECLINED-AUTH-CNT, subtract from PA-DECLINED-AUTH-AMT

When both counts on the summary reach zero → delete the summary segment.

## 5. SYSIN Parameters

| Parameter | PIC | Default | Description |
|-----------|-----|---------|-------------|
| P-EXPIRY-DAYS | 9(02) | 5 | Days before expiry |
| P-CHKP-FREQ | X(05) | 5 | Checkpoint frequency |
| P-CHKP-DIS-FREQ | X(05) | 10 | Display frequency |
| P-DEBUG-FLAG | X(01) | Y | Debug output Y/N |

## 6. JCL (CBPAUP0J.jcl)

```
EXEC DFSRRC00 PARM='BMP,CBPAUP0C,PSBPAUTB'
SYSIN: 00,00001,00001,Y
```

## 7. Copybooks Used

CIPAUSMY (IMS summary), CIPAUDTY (IMS detail)
