---
name: COBOL-to-Python Mapping Patterns
description: Key COBOL constructs and their Python/FastAPI/SQLAlchemy equivalents discovered during CardDemo batch module conversion
type: reference
---

## COBOL Paragraph Logic -> Python Service Methods

- Each COBOL paragraph (PERFORM xxx) maps to a private method in a service class
- Keep cognitive complexity under 15 — split complex EVALUATE/PERFORM chains into small functions
- WS-VALIDATION-FAIL-REASON maps to a `ValidationResult` dataclass with `fail(code)` method

## VSAM KSDS -> SQLAlchemy ORM

- KSDS primary key -> SQLAlchemy primary_key=True column
- VSAM alternate key -> CREATE INDEX + repository method using that column
- KSDS composite key (e.g., TCATBALF: acct_id + type_cd + cat_cd) -> multi-column primary key
- INVALID KEY -> `result.scalar_one_or_none()` returning None
- REWRITE -> load record, mutate attributes, flush

## COBOL Date/Timestamp Handling

- DB2-FORMAT-TS (YYYY-MM-DD-HH.MM.SS.ssssss) -> Python `datetime.now(tz=timezone.utc)`
- Z-GET-DB2-FORMAT-TIMESTAMP -> `datetime.now(tz=timezone.utc)` at post time
- COBOL date comparison `ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS(1:10)` -> `account.acct_expiration_date >= orig_ts.date()`

## CBTRN02C Business Rule: Dual-fail Reason Codes

- Both checks always run (COBOL spec: both credit limit AND expiry checks execute unconditionally)
- Reason 103 (EXPIRED) overwrites reason 102 (OVERLIMIT) if both fail
- This is preserved intentionally (noted as potential defect in spec)
- In Python: call `_check_credit_limit()` then `_check_expiration()` always; second `fail()` call overwrites first

## Interest Formula (CBACT04C)

- `monthly_interest = (balance * annual_rate) / 1200`
- Rate stored as percentage (18.00 = 18% APR); divisor 1200 = 12 months * 100
- Zero rate -> skip entirely (IF DIS-INT-RATE NOT = 0)
- DEFAULT group fallback: try specific group first, then retry with group_id='DEFAULT'

## COBOL Transaction ID Generation (CBACT04C)

- TRAN-ID = PARM-DATE (10 chars) + WS-TRANID-SUFFIX (6-digit seq)
- Modern: `run_date.strftime("%Y%m%d")` (8 chars) + `f"{suffix:06d}"` (6 chars) = 14 chars, max 16

## COBOL Account Break Detection (CBACT04C)

- TCATBALF sorted by account ID; loop detects `TRANCAT-ACCT-ID NOT= WS-LAST-ACCT-NUM`
- Modern: `ORDER BY acct_id` in SQL, then compare `balance.acct_id != current_acct_id` in Python

## GDG Output Files -> Database Tables

- DALYREJS GDG -> `daily_rejects` table with `batch_job_id` FK to `batch_jobs`
- TRANREPT GDG -> JSON response + formatted text string in response body
- JCL RETURN-CODE 4 -> `has_rejects: bool` field in response

## CBTRN03C: COBOL ABEND on Missing Reference Data

- Original COBOL: INVALID KEY on xref/type/category lookup -> 9999-ABEND-PROGRAM
- Modern equivalent: `logger.warning(...)` and use placeholder/skip instead of aborting
- This matches the requirement: "Fix CBTRN03C abend on missing reference data: log warning and skip"
