---
name: CardDemo Credit Card Online Module
description: Architecture and key facts about the three credit card CICS programs in the CardDemo mainframe application
type: project
---

Three-program CICS online module handles credit card list/select/update:

**Program chain:**
- COCRDLIC (CCLI) — paginated card list, 7 rows, STARTBR/READNEXT/READPREV on CARDDAT KSDS
- COCRDSLC (CCDL) — card detail view, direct READ on CARDDAT by primary key (card number)
- COCRDUPC (CCUP) — card update, READ+UPDATE+REWRITE on CARDDAT, optimistic concurrency

**Why:** These three form the core credit card maintenance flow in the CardDemo AWS mainframe modernization demo application.

**How to apply:** When analyzing data flows, inter-program calls, or modernization tasks, treat these three as a unit. COCRDLIC is the list entry point (from menu COMEN01C via CM00). It XCTLs to COCRDSLC or COCRDUPC passing CDEMO-ACCT-ID and CDEMO-CARD-NUM in CARDDEMO-COMMAREA.

**VSAM files:**
- CARDDAT (KSDS, primary key = CARD-NUM X(16), record = CVACT02Y, 150 bytes)
- CARDAIX (alternate index on CARD-ACCT-ID 9(11)) — defined in COCRDSLC but dead code; not called

**Key copybooks:**
- COCOM01Y — shared COMMAREA (CARDDEMO-COMMAREA), all programs
- CVCRD01Y — CC-WORK-AREA with CCARD-AID-xxx PF key 88s, CC-ACCT-ID, CC-CARD-NUM
- CVACT02Y — CARD-RECORD 150 bytes
- CSSTRPFY — PF key mapping routine (MISSING from sources — inferred from all three programs)
- CSUSR01Y — signed-on user data (MISSING from sources)

**State machine in COCRDUPC:** CCUP-CHANGE-ACTION drives a 3-phase update: LOW-VALUES (search) → 'S' (show) → 'N' (confirmed, await PF5) → 'C' (done) / 'E' (edit errors) / 'L'/'F' (lock/update failures)

**Concurrency:** COCRDUPC uses optimistic locking — READ non-update to snapshot, then READ UPDATE to lock before REWRITE; 9300-CHECK-CHANGE-IN-REC compares CVV+name+expiry+status against snapshot.

**Expiry day not user-editable:** EXPDAY field exists in COCRDUP BMS but is DRK (hidden). Only EXPMON and EXPYEAR are user-editable. Old EXPDAY always preserved in write.

**Menu:** COMEN01C (CM00) is the main menu. COCRDLIC receives XCTL from it directly.
