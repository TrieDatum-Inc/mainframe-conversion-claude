# Technical Specification: PAUDBLOD — IMS Database Load

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | PAUDBLOD |
| Source File | `app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL` |
| Type | Batch COBOL (IMS BMP) |
| JCL | LOADPADB.JCL |

## 2. Purpose

PAUDBLOD **loads the IMS DBPAUTP0 database** from flat files previously produced by PAUDBUNL. Reads root records from INFILE1 and child records from INFILE2.

## 3. IMS Access

Uses a qualified SSA on PAUTSUM0 segment (field=ACCNTID, operator=EQ) to perform targeted GU + ISRT operations. PSB: PSBPAUTB.

### Root SSA Structure
- Segment: PAUTSUM0
- Field: ACCNTID
- Operator: EQ
- Value: QUAL-SSA-KEY-VALUE (COMP-3 packed decimal 11 digits)

## 4. Input Files

| File DD | Source | Content |
|---------|--------|---------|
| INFILE1 | AWS.M2.CARDDEMO.PAUTDB.ROOT.FILEO | Root segments |
| INFILE2 | AWS.M2.CARDDEMO.PAUTDB.CHILD.FILEO | Child segments |

## 5. JCL (LOADPADB.JCL)

```
EXEC DFSRRC00 PARM='BMP,PAUDBLOD,PSBPAUTB'
```
