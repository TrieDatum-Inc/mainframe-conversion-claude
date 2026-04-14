# Technical Specifications: Transaction Type DB2 Extension — Programs

This directory contains program-level technical specifications for the CardDemo Transaction Type DB2 extension.

## Programs

| Spec File      | Program ID | Transaction | Type        | Function                                                  |
|----------------|------------|-------------|-------------|-----------------------------------------------------------|
| COBTUPDT.md    | COBTUPDT   | (batch)     | Batch COBOL | Batch INSERT/UPDATE/DELETE of TRANSACTION_TYPE from sequential file |
| COTRTLIC.md    | COTRTLIC   | CTLI        | CICS online | Transaction Type list, filter, page, inline-update, delete |
| COTRTUPC.md    | COTRTUPC   | CTTU        | CICS online | Transaction Type single-record add/edit/delete             |

## DB2 Tables Accessed

| Table                               | Programs                        | Operations          |
|-------------------------------------|---------------------------------|---------------------|
| CARDDEMO.TRANSACTION_TYPE           | COBTUPDT, COTRTLIC, COTRTUPC    | SELECT, INSERT, UPDATE, DELETE |
| CARDDEMO.TRANSACTION_TYPE_CATEGORY  | (none — FK constraint only)     | (FK enforcement)    |

## Key Dependencies

- All programs require DB2 precompile with DCLTRTYP (DCLGEN for TRANSACTION_TYPE)
- COTRTLIC and COTRTUPC require CICS with DB2 support (CSD entries in csd/CRDDEMOD.csd)
- COTRTLIC includes common DB2 procedures via CSDB2RPY and CSDB2RWY copybooks
- COTRTUPC includes DCLTRCAT (DCLGEN for TRANSACTION_TYPE_CATEGORY) but does not issue SQL against it
- Batch program COBTUPDT runs under DSN RUN PROGRAM via TSO/IKJEFT01 — see jcl/MNTTRDB2.jcl

## Analysis Notes

- COTRTLIC demonstrates bidirectional DB2 cursor paging (forward C-TR-TYPE-FORWARD and backward C-TR-TYPE-BACKWARD)
- COTRTUPC implements an upsert pattern: UPDATE first, then INSERT if SQLCODE=+100
- COBTUPDT does not issue SQL COMMIT; all changes are in a single DB2 unit of work per job step
- All three programs use static embedded SQL with DCLGEN-generated host variable structures
