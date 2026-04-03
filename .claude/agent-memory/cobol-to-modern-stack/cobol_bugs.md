---
name: Common COBOL Bugs Found in CardDemo
description: Recurring defects identified in CardDemo programs that should be fixed in modern conversion
type: reference
---

## Bug 1: User Type Validation (COUSR01C)

**Location:** COUSR01C PROCESS-ENTER-KEY, validation step 5 (USRTYPEI)
**COBOL Defect:** Only checks `IF USRTYPEI = SPACES` — any non-blank character is accepted.
**Correct Behaviour:** user_type must be strictly 'A' (Admin) or 'U' (User).
**Fix Applied:** Pydantic `Literal['A', 'U']` in schemas; PostgreSQL `CHECK (user_type IN ('A', 'U'))`.

## Bug 2: Delete Error Message (COUSR03C)

**Location:** COUSR03C DELETE-USER-SEC-FILE, OTHER response branch (line 332)
**COBOL Defect:** Error message says "Unable to Update User..." (copy-paste from COUSR02C).
**Correct Behaviour:** Should say "Unable to Delete User...".
**Fix Applied:** In service layer and API error responses, use correct "Delete" terminology.

## Bug 3: Commented-out User ID/Type in COMMAREA (COUSR01C)

**Location:** COUSR01C RETURN-TO-PREV-SCREEN, lines 172-173
**COBOL Defect:** Two lines that set CDEMO-USER-ID and CDEMO-USER-TYPE are commented out.
**Impact:** Not a functional bug for the conversion — just dead code noted.

## Pattern: Copy-Paste Error Messages

CardDemo programs COUSR02C and COUSR03C share nearly identical structures. When errors arise in COUSR03C, some error messages were copied verbatim from COUSR02C and not updated to reflect "delete" vs "update" context. Always verify error message text matches the operation when converting similar COBOL programs.

## Pattern: WS-USR-MODIFIED Declared but Unused (COUSR03C)

**Location:** COUSR03C WS-VARIABLES
**COBOL Pattern:** USR-MODIFIED flag and 88-levels declared (mirroring COUSR02C) but never set to 'Y'.
**Handling:** Dead code — not ported to the modern stack.
