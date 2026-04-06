# Technical Specification: PAUDBUNL — IMS Database Unload

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | PAUDBUNL |
| Source File | `app/app-authorization-ims-db2-mq/cbl/PAUDBUNL.CBL` |
| Type | Batch COBOL (IMS DLI) |
| JCL | UNLDPADB.JCL |

## 2. Purpose

PAUDBUNL performs a **full sequential unload** of the IMS DBPAUTP0 database to two flat files: root (summary) records to OUTFIL1 and child (detail) records to OUTFIL2.

## 3. IMS Access

Sequential GN traversal of DBPAUTP0. Uses WS-END-OF-ROOT-SEG and WS-END-OF-CHILD-SEG flags to control the nested loop.

## 4. Output Files

| File DD | LRECL | Content |
|---------|-------|---------|
| OUTFIL1 | 100 bytes | PAUTSUM0 root segments (account summaries) |
| OUTFIL2 | 206 bytes | PAUTDTL1 child segments (authorization details) |

## 5. JCL (UNLDPADB.JCL)

```
EXEC DFSRRC00 PARM='DLI,PAUDBUNL,PAUTBUNL'
DDPAUTP0, DDPAUTX0 → physical IMS datasets
```

PSB: PAUTBUNL (full-function unload PSB)
