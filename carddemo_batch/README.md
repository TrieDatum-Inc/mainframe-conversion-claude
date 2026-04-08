# CardDemo Batch Pipeline - Databricks PySpark Migration

Databricks PySpark equivalents of four AWS CardDemo mainframe batch COBOL programs.

---

## Migration Scope

| COBOL Program | Type | PySpark Pipeline | Description |
|---|---|---|---|
| `CBTRN02C.cbl` | Batch | `pipelines/cbtrn02c_pipeline.py` | Daily transaction posting |
| `CBACT04C.cbl` | Batch | `pipelines/cbact04c_pipeline.py` | Monthly interest calculator |
| `CBSTM03A.CBL` + `CBSTM03B.CBL` | Batch + Subroutine | `pipelines/cbstm03_pipeline.py` | Account statement generation |
| `CBTRN03C.cbl` | Batch | `pipelines/cbtrn03c_pipeline.py` | Transaction detail report |

---

## COBOL-to-PySpark Paragraph Mapping

### CBTRN02C - Daily Transaction Posting

| COBOL Paragraph | PySpark Function / Action |
|---|---|
| `0000-DALYTRAN-OPEN` | `spark.read.table(daily_transactions)` |
| `0100-TRANFILE-OPEN` | Output: `transactions` Delta table |
| `0200-XREFFILE-OPEN` | `spark.read.table(card_xref)` |
| `0300-DALYREJS-OPEN` | Output: `daily_reject_transactions` Delta table |
| `0400-ACCTFILE-OPEN` | `spark.read.table(accounts)` [I-O] |
| `0500-TCATBALF-OPEN` | `spark.read.table(transaction_category_balance)` [I-O] |
| `1500-VALIDATE-TRAN` | `validate_transactions()` |
| `1500-A-LOOKUP-XREF` | `_flag_invalid_cards()` - left join on card_xref |
| `1500-B-LOOKUP-ACCT` | `_flag_account_errors()` - overlimit + expiry checks |
| `2000-POST-TRANSACTION` | `build_posted_transactions()` |
| `2500-WRITE-REJECT-REC` | `extract_rejected_transactions()` |
| `2700-UPDATE-TCATBAL` | `build_tcatbal_updates()` + Delta MERGE |
| `2700-A-CREATE-TCATBAL-REC` | Delta MERGE WHEN NOT MATCHED INSERT |
| `2700-B-UPDATE-TCATBAL-REC` | Delta MERGE WHEN MATCHED UPDATE |
| `2800-UPDATE-ACCOUNT-REC` | `build_account_balance_updates()` + Delta MERGE |
| `9999-ABEND-PROGRAM` | `raise PipelineAbendError(...)` |

### CBACT04C - Interest Calculator

| COBOL Paragraph | PySpark Function / Action |
|---|---|
| `1000-TCATBALF-GET-NEXT` | Sequential read of `transaction_category_balance` |
| `1050-UPDATE-ACCOUNT` | `build_account_interest_updates()` + Delta MERGE |
| `1100-GET-ACCT-DATA` | Join with `accounts` inside `resolve_interest_rates()` |
| `1110-GET-XREF-DATA` | Join with `card_xref` inside `resolve_interest_rates()` |
| `1200-GET-INTEREST-RATE` | `resolve_interest_rates()` - specific group lookup |
| `1200-A-GET-DEFAULT-INT-RATE` | Fallback join to DEFAULT group inside `resolve_interest_rates()` |
| `1300-COMPUTE-INTEREST` | `compute_monthly_interest()` - `(bal * rate) / 1200` |
| `1300-B-WRITE-TX` | `build_interest_transactions()` |
| `1400-COMPUTE-FEES` | Stub - not implemented in COBOL, not implemented here |

### CBSTM03A + CBSTM03B - Account Statement Generation

| COBOL Paragraph | PySpark Function / Action |
|---|---|
| `0000-START` (ALTER/GO TO state machine) | Not applicable - all files read upfront |
| `CBSTM03B` (subroutine dispatcher) | Absorbed into Spark joins; no subroutine needed |
| `1000-XREFFILE-GET-NEXT` | Sequential read of `card_xref` |
| `2000-CUSTFILE-GET` | Join with `customers` in `enrich_xref_with_customer_account()` |
| `3000-ACCTFILE-GET` | Join with `accounts` in `enrich_xref_with_customer_account()` |
| `4000-TRNXFILE-GET` (2D array loop) | Join on `transactions_by_card` in `match_transactions_to_cards()` |
| `5000-CREATE-STATEMENT` | `build_customer_full_name()` + header fields |
| `5100-WRITE-HTML-HEADER` | **Intentionally omitted** (HTML output not required) |
| `5200-WRITE-HTML-NMADBS` | **Intentionally omitted** |
| `6000-WRITE-TRANS` | `build_statement_rows()` |

### CBTRN03C - Transaction Detail Report

| COBOL Paragraph | PySpark Function / Action |
|---|---|
| `0550-DATEPARM-READ` | `start_date` / `end_date` run arguments |
| `1000-TRANFILE-GET-NEXT` | Sequential read of `transactions` |
| Date filter (inline) | `filter_by_date_range()` |
| `1500-A-LOOKUP-XREF` | `enrich_with_xref()` |
| `1500-B-LOOKUP-TRANTYPE` | `enrich_with_tran_type()` |
| `1500-C-LOOKUP-TRANCATG` | `enrich_with_tran_category()` |
| `1100-WRITE-TRANSACTION-REPORT` | `build_report_detail_rows()` |
| `1110-WRITE-PAGE-TOTALS` | `compute_page_totals()` |
| `1120-WRITE-ACCOUNT-TOTALS` | `compute_account_totals()` |
| `1110-WRITE-GRAND-TOTALS` | `compute_grand_total()` |

---

## Project Structure

```
carddemo_batch/
├── config/
│   └── settings.py          # Table names, constants, validation codes
├── transformations/
│   ├── cbtrn02c_transforms.py
│   ├── cbact04c_transforms.py
│   ├── cbstm03_transforms.py
│   └── cbtrn03c_transforms.py
├── validators/
│   └── common.py            # PipelineAbendError, date validation, logging
├── pipelines/
│   ├── cbtrn02c_pipeline.py
│   ├── cbact04c_pipeline.py
│   ├── cbstm03_pipeline.py
│   └── cbtrn03c_pipeline.py
├── tests/
│   ├── conftest.py          # SparkSession fixture, sample DataFrames
│   ├── test_cbtrn02c.py
│   ├── test_cbact04c.py
│   ├── test_cbstm03.py
│   ├── test_cbtrn03c.py
│   └── test_validators.py
├── sql/
│   ├── setup_tables.sql     # CREATE TABLE DDL for all Delta tables
│   └── sample_data.sql      # INSERT statements for testing
├── setup.py
├── pytest.ini
└── README.md
```

---

## Prerequisites

- Databricks Runtime 12.x or higher (includes PySpark 3.3+ and Delta 2.3+)
- Python 3.9+
- Delta Lake 2.3+

For local development and testing:
```
pip install pyspark==3.4.0 delta-spark==2.4.0 pytest==7.4.0
```

---

## Setup: Create Delta Tables

Run the DDL script in a Databricks SQL editor or notebook:

```sql
%run /path/to/sql/setup_tables.sql
```

Or using the CLI:
```bash
databricks fs cp sql/setup_tables.sql dbfs:/tmp/
databricks sql execute --warehouse-id <id> --file /tmp/setup_tables.sql
```

Load sample data:
```sql
%run /path/to/sql/sample_data.sql
```

---

## Running the Pipelines

### CBTRN02C - Daily Transaction Posting

```python
# In a Databricks notebook
from carddemo_batch.pipelines.cbtrn02c_pipeline import run
reject_count = run(spark)
print(f"Reject count: {reject_count}")
# reject_count > 0 is equivalent to COBOL RETURN-CODE=4
```

```bash
# spark-submit
spark-submit \
  --packages io.delta:delta-core_2.12:2.4.0 \
  carddemo_batch/pipelines/cbtrn02c_pipeline.py
```

### CBACT04C - Interest Calculator

```python
from carddemo_batch.pipelines.cbact04c_pipeline import run
tran_written = run(spark, run_date="2024-01-31")
print(f"Interest transactions written: {tran_written}")
```

```bash
spark-submit \
  --packages io.delta:delta-core_2.12:2.4.0 \
  carddemo_batch/pipelines/cbact04c_pipeline.py --run-date 2024-01-31
```

### CBSTM03A/B - Account Statement Generation

```python
from carddemo_batch.pipelines.cbstm03_pipeline import run
rows = run(spark)
print(f"Statement rows written: {rows}")
```

```bash
spark-submit \
  --packages io.delta:delta-core_2.12:2.4.0 \
  carddemo_batch/pipelines/cbstm03_pipeline.py
```

### CBTRN03C - Transaction Detail Report

```python
from carddemo_batch.pipelines.cbtrn03c_pipeline import run
result = run(spark, start_date="2024-01-01", end_date="2024-01-31")
print(f"Grand Total: {result['grand_total']}")
result["page_totals_df"].show()
result["account_totals_df"].show()
```

```bash
spark-submit \
  --packages io.delta:delta-core_2.12:2.4.0 \
  carddemo_batch/pipelines/cbtrn03c_pipeline.py \
  --start-date 2024-01-01 --end-date 2024-01-31
```

---

## Running Tests

```bash
cd carddemo_batch
pip install -e ".[dev]"
pytest tests/ -v
```

Run a specific test module:
```bash
pytest tests/test_cbtrn02c.py -v
pytest tests/test_cbact04c.py -v
pytest tests/test_cbstm03.py -v
pytest tests/test_cbtrn03c.py -v
pytest tests/test_validators.py -v
```

---

## Configuration

All pipeline-wide constants are in `config/settings.py`:

| Constant | Value | COBOL Source |
|---|---|---|
| `REJECT_CODE_INVALID_CARD` | 100 | `CBTRN02C` `WS-VALIDATION-FAIL-REASON` |
| `REJECT_CODE_ACCOUNT_NOT_FOUND` | 101 | `CBTRN02C` |
| `REJECT_CODE_OVERLIMIT` | 102 | `CBTRN02C` |
| `REJECT_CODE_EXPIRED_ACCT` | 103 | `CBTRN02C` |
| `INTEREST_TRAN_TYPE_CD` | `"01"` | `CBACT04C` paragraph `1300-B-WRITE-TX` |
| `INTEREST_TRAN_CAT_CD` | `5` | `CBACT04C` paragraph `1300-B-WRITE-TX` |
| `INTEREST_DIVISOR` | `1200` | `CBACT04C` monthly rate formula |
| `INTEREST_DEFAULT_GROUP` | `"DEFAULT"` | `CBACT04C` paragraph `1200-GET-INTEREST-RATE` |
| `REPORT_PAGE_SIZE` | `20` | `CBTRN03C` `WS-PAGE-SIZE` |

To change catalog or database prefix, update `CATALOG` and `DATABASE` in `settings.py`.

---

## Error Handling and Monitoring

### Abend Equivalents

The `PipelineAbendError` exception (in `validators/common.py`) is raised wherever
the COBOL program calls `9999-ABEND-PROGRAM`.  Each raise includes:
- The program name (`CBTRN02C`, etc.)
- A descriptive message
- The equivalent COBOL abend/file-status code

### Reject Monitoring (CBTRN02C)

Rejected transactions are written to `carddemo.daily_reject_transactions`.
Query for daily reject analysis:

```sql
SELECT
    validation_fail_reason,
    validation_fail_reason_desc,
    COUNT(*) AS reject_count
FROM carddemo.daily_reject_transactions
GROUP BY validation_fail_reason, validation_fail_reason_desc
ORDER BY reject_count DESC;
```

Reject codes:
- `100` - Invalid card number (no XREF record)
- `101` - Account record not found
- `102` - Overlimit transaction
- `103` - Account expired

### Interest Transaction Audit (CBACT04C)

All generated interest transactions land in `carddemo.interest_transactions`.
They have `tran_type_cd='01'`, `tran_cat_cd=5`, `tran_source='System'`.

---

## COBOL Program Cross-Reference

| Copybook | Table | Used by |
|---|---|---|
| `CVTRA06Y.cpy` | `daily_transactions` | CBTRN02C (input) |
| `CVTRA05Y.cpy` | `transactions` | CBTRN02C (output), CBACT04C (output), CBTRN03C (input) |
| `CVACT01Y.cpy` | `accounts` | CBTRN02C, CBACT04C, CBSTM03A |
| `CVACT03Y.cpy` | `card_xref` | CBTRN02C, CBACT04C, CBSTM03A, CBTRN03C |
| `CVTRA01Y.cpy` | `transaction_category_balance` | CBTRN02C, CBACT04C |
| `CVTRA02Y.cpy` | `disclosure_groups` | CBACT04C |
| `CVTRA03Y.cpy` | `transaction_types` | CBTRN03C |
| `CVTRA04Y.cpy` | `transaction_categories` | CBTRN03C |
| `CVTRA07Y.cpy` | `transaction_report` | CBTRN03C (output schema) |
| `CUSTREC.cpy` | `customers` | CBSTM03A |
| `COSTM01.cpy` | `transactions_by_card` | CBSTM03A/B |
