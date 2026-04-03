---
name: Transaction Program Technical Specifications
description: Documents the six transaction programs analyzed and spec files generated in the CardDemo application
type: project
---

Six transaction program technical specs generated in tech_specs/ directory as of 2026-04-03:

- COTRN00C_spec.md — CICS online transaction list (CT00), paginates TRANSACT VSAM with STARTBR/READNEXT/READPREV; 10 rows/page; PF7/PF8 scroll; 'S' to drill to COTRN01C
- COTRN01C_spec.md — CICS online transaction view (CT01); single-record READ with UPDATE (anomaly — no subsequent REWRITE); auto-fetch when entered from COTRN00C with CDEMO-CT01-TRN-SELECTED populated
- COTRN02C_spec.md — CICS online transaction add (CT02); validates Account ID via CXACAIX alternate index or Card Number via CCXREF; auto-increments TRAN-ID by reading last record + 1; calls CSUTLDTC for calendar date validation; Y/N confirmation required; PF5 copies last tran
- CBTRN01C_spec.md — Batch diagnostic/verify program; reads DALYTRAN, looks up XREF and ACCOUNT; no posting; TRANSACT-FILE opened but never read (skeleton)
- CBTRN02C_spec.md — Batch transaction posting; validates card (fail 100), account exists (101), credit limit (102), expiration (103); posts to TRANSACT (OUTPUT mode — full replace); updates TCATBAL and ACCOUNT; rejects to DALYREJS with reason code; sets RETURN-CODE=4 if rejects
- CBTRN03C_spec.md — Batch report (DALYREPT); date-range filtered by DATEPARM control file; sequential read of TRANSACT; lookups to CARDXREF, TRANTYPE, TRANCATG; page breaks every 20 lines; account-level and grand totals

**Why:** User requested detailed spec documentation for these six programs.
**How to apply:** These specs are the authoritative reference for the transaction subsystem. Cross-reference them when analyzing other programs that touch the TRANSACT file or DALYTRAN workflow.
