# Technical Specification: DBUNLDGS — IMS Database Unload Template

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | DBUNLDGS |
| Source File | `app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL` |
| Type | Batch COBOL (IMS) — Template/Incomplete |

## 2. Purpose

DBUNLDGS is a **structural template** for IMS database unload operations. It unloads DBPAUTP0 segments to working storage buffers. The FILE-CONTROL section is commented out, and output goes to WORKING-STORAGE fields rather than files.

## 3. Status

- WS-PGMNAME is hardcoded to 'IMSUNLOD' (not 'DBUNLDGS'), indicating this was copied from a template.
- PSB-NAME and PCB-OFFSET declarations are commented out.
- Not production-complete — PAUDBUNL is the production unload program.

## 4. IMS SSAs

- ROOT-UNQUAL-SSA for PAUTSUM0
- CHILD-UNQUAL-SSA for PAUTDTL1
