---
name: CardDemo BMS Screen Inventory
description: Complete inventory of all 21 BMS screens in the CardDemo mainframe app — mapset names, map names, field counts, subsystem locations, and navigation flow
type: project
---

CardDemo has 21 BMS screens fully documented in tech_specs/BMS_Screens_spec.md (written 2026-04-03).

**Why:** Baseline documentation for mainframe-to-modern conversion effort.

**How to apply:** Use this as the authoritative source for screen field layouts, attribute codes, and inter-screen navigation when working on any CICS program analysis or UI modernization tasks.

Screen locations:
- 17 screens in app/bms/
- 2 screens in app/app-authorization-ims-db2-mq/bms/ (COPAU00, COPAU01)
- 2 screens in app/app-transaction-type-db2/bms/ (COTRTUP, COTRTLI)

All screens are 24x80. Consistent header band on rows 1-2, ERRMSG on row 23, key guide on row 24.

Key navigation: COSGN00 → COMEN01 (regular) / COADM01 (admin). Admin functions: user management (COUSR00-03), authorizations (COPAU00-01), transaction types (COTRTLI/COTRTUP). Regular user functions: accounts (COACTVW/COACTUP), cards (COCRDSL/COCRDLI/COCRDUP), transactions (COTRN00-02), reports (CORPT00), bill payment (COBIL00).

Open gaps: CICS transaction codes and exact COBOL program names require PCT/PPT lookup — not in BMS sources.
