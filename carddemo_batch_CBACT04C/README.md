# CBACT04C — Interest Calculation Pipeline

Databricks PySpark migration of COBOL batch program `CBACT04C` from the CardDemo application.

## What This Pipeline Does

This pipeline replaces `app/cbl/CBACT04C.cbl` and its JCL job `INTCALC.jcl`.

It runs as step 5 of the `carddemo_daily_batch_cycle` Databricks workflow (after `posttran_cbtrn02c`).

**Business function:** Reads transaction category balances, looks up annual interest rates, computes monthly interest per account, generates interest charge transaction records, and updates account balances.

## COBOL-to-PySpark Traceability

| COBOL Paragraph | PySpark Module | Function |
|----------------|---------------|---------|
| `PROCEDURE DIVISION` (main loop) | `src/pipeline.py:run_pipeline` | Orchestration |
| `1000-TCATBALF-GET-NEXT` | `src/interest_calc.py:read_tran_cat_balance` | Read + sort driving file |
| `1100-GET-ACCT-DATA` | `src/interest_calc.py:join_interest_rates` | Left-join accounts for `acct_group_id` |
| `1110-GET-XREF-DATA` | `src/transaction_writer.py:read_card_xref` | Left-join XREF for `card_num` |
| `1200-GET-INTEREST-RATE` | `src/interest_calc.py:join_interest_rates` | Primary rate broadcast join |
| `1200-A-GET-DEFAULT-INT-RATE` | `src/interest_calc.py:join_interest_rates` | DEFAULT fallback + `coalesce()` |
| `1300-COMPUTE-INTEREST` | `src/interest_calc.py:compute_monthly_interest` | `(bal * rate) / 1200` |
| `1050-UPDATE-ACCOUNT` (accumulate) | `src/interest_calc.py:aggregate_account_interest` | `groupBy + sum` |
| `1300-B-WRITE-TX` | `src/transaction_writer.py:build_interest_transactions` | Build TRAN-RECORD |
| `1050-UPDATE-ACCOUNT` (REWRITE) | `src/account_updater.py:update_account_balances` | Delta MERGE |
| `1400-COMPUTE-FEES` | **Not implemented** — stub EXIT in COBOL | N/A |
| `Z-GET-DB2-FORMAT-TIMESTAMP` | `src/timestamp_utils.py:get_db2_format_timestamp` | 26-char DB2 timestamp |
| JCL PARM | Databricks widget `run_date` | YYYY-MM-DD processing date |
| SYSOUT DISPLAY | `carddemo.gold.interest_charges` + `pipeline_metrics` | Audit + stats |

## Business Rules

| Rule | Description | Implementation |
|------|-------------|---------------|
| BR-1 | `monthly_interest = (tran_cat_bal * dis_int_rate) / 1200` | `interest_calc.py:compute_monthly_interest` |
| BR-2 | Primary group → DEFAULT fallback when status='23' | `coalesce(primary_rate, default_rate)` in `join_interest_rates` |
| BR-3 | Zero-rate bypass: skip categories with `dis_int_rate = 0` or NULL | `.filter(rate != 0)` in `compute_monthly_interest` |
| BR-4 | Accumulate all categories per account before REWRITE | `groupBy(acct_id).sum()` in `aggregate_account_interest` |
| BR-5 | One interest transaction per account (not per category) | Aggregation + single `build_interest_transactions` row per account |
| BR-6 | `TRAN-TYPE-CD='01'`, `TRAN-CAT-CD=5`, `TRAN-SOURCE='System'`, `TRAN-MERCHANT-ID=0` | Hardcoded in `src/constants.py` |
| BR-7 | `acct_curr_cyc_credit = 0`, `acct_curr_cyc_debit = 0` on REWRITE | Delta MERGE SET in `update_account_balances` |
| BR-8 | `TRAN-ID = YYYYMMDD + 6-digit-suffix` | `concat(run_date_compact, lpad(monotonic_id, 6, '0'))` |

## Input Delta Tables

| Delta Table | Replaces | Role |
|------------|---------|------|
| `carddemo.silver.tran_cat_balance` | VSAM KSDS TCATBALF | Driving file (sorted by acct_id) |
| `carddemo.silver.disclosure_group` | VSAM KSDS DISCGRP | Interest rate lookup (broadcast join) |
| `carddemo.silver.card_xref` | VSAM KSDS XREFFILE | Card number lookup |
| `carddemo.silver.account` | VSAM KSDS ACCTFILE | Account group read + balance REWRITE |

## Output Delta Tables

| Delta Table | Replaces | Write Mode |
|------------|---------|------------|
| `carddemo.silver.transaction` | VSAM KSDS TRANSACT (OUTPUT) | MERGE (insert interest rows) |
| `carddemo.silver.account` | VSAM KSDS ACCTFILE (I-O, REWRITE) | MERGE (update balances) |
| `carddemo.gold.interest_charges` | SYSOUT DISPLAY audit | Append (per-category detail) |
| `carddemo.migration_ctrl.pipeline_metrics` | SYSOUT statistics | Append (run counts + status) |

## Project Structure

```
carddemo_batch_CBACT04C/
├── src/
│   ├── __init__.py
│   ├── constants.py           # Hardcoded COBOL values (TRAN-TYPE-CD, TRAN-CAT-CD, etc.)
│   ├── interest_calc.py       # Rate join, interest formula, account aggregation
│   ├── account_updater.py     # Delta MERGE for account balance update + gold write
│   ├── transaction_writer.py  # TRAN-RECORD construction + Delta MERGE to silver.transaction
│   ├── timestamp_utils.py     # DB2-format 26-char timestamp (Z-GET-DB2-FORMAT-TIMESTAMP)
│   └── pipeline.py            # Main entry point (orchestration + widgets + metrics)
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Shared SparkSession fixture (local Delta)
│   ├── test_interest_calc.py  # Unit tests: BR-1, BR-2, BR-3, BR-4
│   ├── test_account_updater.py # Unit tests: balance update logic + balance integrity check
│   ├── test_transaction_writer.py # Unit tests: TRAN-ID, field values, XREF lookup
│   └── test_pipeline_integration.py # End-to-end pipeline logic tests
├── sql/
│   ├── bronze_tables.sql      # DDL: bronze.tran_cat_balance_raw, bronze.disclosure_group_raw
│   └── gold_tables.sql        # DDL: gold.interest_charges
├── workflow/
│   └── cbact04c_workflow.yml  # Databricks task YAML (embedded in daily_batch_cycle)
└── README.md                  # This file
```

## Running the Pipeline

### Databricks Job (Production)

The pipeline runs automatically as part of `carddemo_daily_batch_cycle`. To trigger standalone:

```bash
databricks jobs run-now \
  --job-id <cbact04c_interest_calc_standalone_job_id> \
  --python-params '{"run_date": "2026-04-07"}'
```

### Local / Test Execution

```bash
# Install dependencies (requires delta-spark and pyspark)
pip install pyspark delta-spark pytest

# Run unit tests (no cluster required)
cd /path/to/repo
pytest carddemo_batch_CBACT04C/tests/ -v

# Run pipeline locally (uses today's date as fallback if run_date not provided)
python -m carddemo_batch_CBACT04C.src.pipeline 2026-04-07
```

### Delta Table Setup (One-Time)

Run the DDL scripts before the first pipeline execution:

```sql
-- In Databricks SQL or a notebook:
%run ./sql/bronze_tables
%run ./sql/gold_tables
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|---------|-------------|
| `run_date` | STRING (YYYY-MM-DD) | Yes | Processing date. Embedded as prefix in generated TRAN-IDs. Replaces JCL `PARM-DATE X(10)`. |

## Error Handling

| Condition | Behaviour |
|-----------|-----------|
| Account not found in `silver.account` | Warning logged to `pipeline_metrics`; account skipped in MERGE |
| XREF not found | Warning logged; `tran_card_num = NULL` in output transaction |
| No rate (primary + DEFAULT both absent) | Warning logged; category skipped (zero-rate bypass) |
| Delta write failure | Exception raised; Databricks task fails; upstream workflow blocked |
| Empty TCATBALF | Pipeline exits cleanly with `status=SUCCESS_NO_DATA` |

## Data Quality Checks

Two assertions run after computation, before writing:

1. **TRAN-ID uniqueness**: all generated `tran_id` values within the run must be unique.
2. **Balance integrity**: `sum(total_interest)` == `sum(tran_amt)` across all accounts.

Violations raise `AssertionError` and fail the job.

## Copybook-to-Delta Type Mapping

| COBOL Copybook | COBOL PIC | Delta Column | Spark Type |
|---------------|----------|-------------|-----------|
| CVTRA01Y: `TRANCAT-ACCT-ID` | `9(11)` | `acct_id` | `BIGINT` |
| CVTRA01Y: `TRANCAT-TYPE-CD` | `X(2)` | `tran_type_cd` | `STRING` |
| CVTRA01Y: `TRANCAT-CD` | `9(4)` | `tran_cat_cd` | `INTEGER` |
| CVTRA01Y: `TRAN-CAT-BAL` | `S9(9)V99` | `tran_cat_bal` | `DECIMAL(11,2)` |
| CVTRA02Y: `DIS-INT-RATE` | numeric | `dis_int_rate` | `DECIMAL(7,4)` |
| CVACT01Y: `ACCT-CURR-BAL` | `S9(10)V99` | `acct_curr_bal` | `DECIMAL(12,2)` |
| CVTRA05Y: `TRAN-AMT` | `S9(9)V99` | `tran_amt` | `DECIMAL(11,2)` |
| CVTRA05Y: `TRAN-ORIG-TS` | `X(26)` | `tran_orig_ts` | `STRING` (DB2 format) |

## Not Implemented

- `1400-COMPUTE-FEES`: This COBOL paragraph contains only `EXIT` (stub). Fees are not implemented in the pipeline, matching COBOL behaviour exactly.
