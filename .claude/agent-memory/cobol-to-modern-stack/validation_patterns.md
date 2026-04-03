---
name: Validation Patterns
description: COBOL edit paragraph to Pydantic/Zod validator equivalents, field-by-field
type: reference
---

## COBOL Edit Paragraph → Modern Validator

| COBOL Paragraph | Pydantic (Python) | Zod (TypeScript) |
|---|---|---|
| 1210-EDIT-ACCOUNT | Path param regex `^\d{1,11}$`, non-zero check | N/A (server-side only) |
| 1220-EDIT-YESNO | `field_validator` checking `upper in {'Y','N'}` | `.transform(v=>v.toUpperCase()).refine(v=>['Y','N'].includes(v))` |
| 1225-EDIT-ALPHA-REQD | `re.match(r'^[A-Za-z ]+$', stripped)` | `/.../test(v.trim())` |
| 1235-EDIT-ALPHA-OPT | Same but `if v is None return v` first | `nullable().optional()` + refine |
| 1245-EDIT-NUM-REQD | `.isdigit()` check + non-empty | `z.string().regex(/^\d+$/)` |
| 1250-EDIT-SIGNED-9V2 | Decimal field (Pydantic auto-validates) | `z.coerce.number().multipleOf(0.01)` |
| 1260-EDIT-US-PHONE-NUM | `PhoneInput` nested model with area code >= 200 | `phoneSchema` with NANP rules |
| 1265-EDIT-US-SSN | `SsnInput` with part1 ≠ 000/666/900-999 | `ssnSchema` with part1 rules |
| 1270-EDIT-US-STATE-CD | Set membership check vs VALID_US_STATES | Same set check |
| 1275-EDIT-FICO-SCORE | `ge=300, le=850` on int field | `z.coerce.number().min(300).max(850)` |
| EDIT-DATE-OF-BIRTH | `v > date.today()` raises ValueError | `new Date(v) <= new Date()` |
| EDIT-DATE-CCYYMMDD | Python `date` type auto-validates format | `z.string()` with date parse |
| 1280-EDIT-US-STATE-ZIP-CD | `model_validator` cross-field check | Zod superRefine (not yet implemented) |

## Account Number Validation (2210-EDIT-ACCOUNT)
1. Not blank → 400 "Account number not provided"
2. Numeric 1-11 digits → 400 "Account Filter must be a non-zero 11 digit number"
3. Not all zeros → 400 "Account number must be a non zero 11 digit number"
4. Zero-pad to 11 digits before lookup (COBOL PIC 9(11) semantics)

## SSN Rules (per US SSN spec, mirroring COACTUPC)
- Part 1 (3 digits): not 000, not 666, not 900-999
- Parts 2 and 3: any valid digits
- Display format: XXX-XX-XXXX (formatted by format_ssn())
- Storage format: 9-digit string (no dashes)

## State Codes
- 50 US states + DC, PR, VI, GU, AS, MP
- Stored in VALID_US_STATES set (both Python and TypeScript)
- Case-insensitive (upcased before check)
