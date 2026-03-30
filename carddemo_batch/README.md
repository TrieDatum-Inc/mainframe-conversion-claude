# CardDemo COBOL-to-Databricks PySpark Migration

Migrated batch COBOL programs from the AWS CardDemo mainframe application to PySpark pipelines backed by Delta tables. All pipelines are **platform-independent** — they run both as Databricks notebooks and via `spark-submit` on any Spark cluster or local machine.

## Programs Migrated

| COBOL Program | PySpark Pipeline | Description |
|---|---|---|
| CBTRN02C | `cbtrn02c_post_daily_transactions.py` | Post daily transactions: validate, post, reject, update balances |
| CBACT04C | `cbact04c_interest_calculator.py` | Calculate monthly interest on transaction category balances |
| CBSTM03A + CBSTM03B | `cbstm03_account_statements.py` | Generate account statements (CSV output) |
| CBTRN03C | `cbtrn03c_transaction_report.py` | Generate transaction detail report (CSV output) |

## Directory Structure

```
databricks_migration/
  setup/
    01_create_tables.sql        -- Delta table DDL (10 tables)
    02_load_sample_data.sql     -- Sample data for testing
  pipelines/
    cbtrn02c_post_daily_transactions.py
    cbact04c_interest_calculator.py
    cbstm03_account_statements.py
    cbtrn03c_transaction_report.py
  run_all.sh                    -- Orchestrator script (Linux / macOS)
  run_all.bat                   -- Orchestrator script (Windows)
  run_setup.sh                  -- Table setup via spark-sql (Linux / macOS)
  run_setup.bat                 -- Table setup via spark-sql (Windows)
  README.md
```

## Platform Support

Each pipeline uses **runtime detection** to automatically adapt:

| Feature | Databricks Notebook | spark-submit (standalone) |
|---|---|---|
| SparkSession | `getOrCreate()` (runtime) | Built with Delta extensions |
| Parameters | `dbutils.widgets` | `argparse` CLI flags |
| Delta Lake | Built into DBR | `--packages io.delta:delta-spark_2.12:3.1.0` |
| Output paths | DBFS (`/tmp/...`) | Local filesystem (configurable) |

---

## Option A: Run on Databricks

### 1. Create Delta Tables

Run `setup/01_create_tables.sql` in a Databricks SQL notebook or SQL editor.

### 2. Load Sample Data

Run `setup/02_load_sample_data.sql` in a Databricks SQL notebook.

### 3. Verify Setup

```sql
USE carddemo;
SHOW TABLES;
SELECT COUNT(*) FROM daily_transactions;   -- Should return 10
SELECT COUNT(*) FROM transactions;          -- Should return 8
SELECT COUNT(*) FROM card_xref;             -- Should return 5
SELECT COUNT(*) FROM customers;             -- Should return 3
SELECT COUNT(*) FROM accounts;              -- Should return 3
```

### 4. Run Pipelines

Import each `.py` file under `pipelines/` as a Databricks notebook. Run them in order:

1. **CBTRN02C** — no parameters needed
2. **CBACT04C** — set widget: `dbutils.widgets.text("parm_date", "2025-03-08")`
3. **CBSTM03** — no parameters needed (output: `/tmp/carddemo/statements`)
4. **CBTRN03C** — set widgets: `start_date`, `end_date` (output: `/tmp/carddemo/transaction_report`)

Steps 3 and 4 are read-only and can run in parallel.

---

## Option B: Run via Shell Script (spark-submit)

### Prerequisites

- **Apache Spark 3.x** installed with `SPARK_HOME` set (or `spark-submit` / `spark-sql` on PATH)
- **Java 8 or 11** (required by Spark)
- Delta Lake jars are auto-downloaded via `--packages` on first run

### 1. Setup: Create & Populate Tables

```bash
# Linux / macOS
chmod +x run_setup.sh
./run_setup.sh

# Windows
run_setup.bat
```

This runs `spark-sql` to execute the DDL and sample data SQL scripts, creating Delta tables in a local `./spark-warehouse/` directory.

To customise the warehouse location:
```bash
./run_setup.sh --warehouse /path/to/my/warehouse
```

### 2. Run All Pipelines

```bash
# Linux / macOS
chmod +x run_all.sh
./run_all.sh

# Windows
run_all.bat
```

The orchestrator runs all four pipelines in the correct order (Steps 1 → 2 → 3+4). On Linux/macOS, Steps 3 and 4 run **in parallel**.

### CLI Options

| Flag | Description | Default |
|---|---|---|
| `--schema` | Catalog schema / database name | `carddemo` |
| `--parm-date` | Interest calculation date (YYYY-MM-DD) | today |
| `--start-date` | Transaction report start date | `2025-03-01` |
| `--end-date` | Transaction report end date | `2025-03-31` |
| `--output` | Output base directory for CSV files | `./output` |
| `--delta-pkg` | Delta Lake Maven coordinate | `io.delta:delta-spark_2.12:3.1.0` |

Examples:

```bash
# Run with custom dates
./run_all.sh --parm-date 2025-04-01 --start-date 2025-01-01 --end-date 2025-12-31

# Run with custom output directory
./run_all.sh --output /data/carddemo/output

# Windows with custom schema
run_all.bat --schema my_carddemo --parm-date 2025-04-01
```

### 3. Run Individual Pipelines

Each pipeline can also be submitted independently:

```bash
# CBTRN02C - Post Daily Transactions
spark-submit --packages io.delta:delta-spark_2.12:3.1.0 \
  pipelines/cbtrn02c_post_daily_transactions.py --schema carddemo

# CBACT04C - Interest Calculator
spark-submit --packages io.delta:delta-spark_2.12:3.1.0 \
  pipelines/cbact04c_interest_calculator.py --schema carddemo --parm-date 2025-03-08

# CBSTM03 - Account Statements
spark-submit --packages io.delta:delta-spark_2.12:3.1.0 \
  pipelines/cbstm03_account_statements.py --schema carddemo --output ./output/statements

# CBTRN03C - Transaction Detail Report
spark-submit --packages io.delta:delta-spark_2.12:3.1.0 \
  pipelines/cbtrn03c_transaction_report.py --schema carddemo \
  --start-date 2025-03-01 --end-date 2025-03-31 --output ./output/report
```

### Output Files

After `run_all.sh` completes:

```
output/
  statements/               -- CBSTM03 account statement CSV
    part-00000-*.csv
  transaction_report/
    detail/                  -- CBTRN03C transaction detail CSV
      part-00000-*.csv
    account_totals/          -- Per-account subtotals CSV
      part-00000-*.csv
    page_totals/             -- Per-page subtotals CSV
      part-00000-*.csv
```

---

## Execution Order

The pipelines must run in this order, matching the original mainframe batch job sequence:

```
Step 1: CBTRN02C  (post daily transactions)    -- writes to transactions, accounts
Step 2: CBACT04C  (calculate interest)          -- reads updated balances, writes interest
Step 3: CBSTM03   (generate statements)         ──┐ can run in parallel
Step 4: CBTRN03C  (transaction report)           ──┘ (both are read-only)
```

## Delta Table to COBOL Copybook Mapping

| Delta Table | COBOL Copybook | COBOL Record | Key |
|---|---|---|---|
| `daily_transactions` | CVTRA06Y | DALYTRAN-RECORD | (sequential) |
| `transactions` | CVTRA05Y | TRAN-RECORD | tran_id |
| `card_xref` | CVACT03Y | CARD-XREF-RECORD | xref_card_num |
| `customers` | CUSTREC | CUSTOMER-RECORD | cust_id |
| `accounts` | CVACT01Y | ACCOUNT-RECORD | acct_id |
| `transaction_category_balances` | CVTRA01Y | TRAN-CAT-BAL-RECORD | (acct_id, type_cd, cat_cd) |
| `disclosure_groups` | CVTRA02Y | DIS-GROUP-RECORD | (group_id, type_cd, cat_cd) |
| `transaction_types` | CVTRA03Y | TRAN-TYPE-RECORD | tran_type |
| `transaction_categories` | CVTRA04Y | TRAN-CAT-RECORD | (type_cd, cat_cd) |
| `daily_transaction_rejects` | (WS layout) | REJECT-RECORD | (sequential output) |

## Pipeline Details

### CBTRN02C - Post Daily Transactions

**What it does:**
- Reads `daily_transactions` (batch input)
- Validates each transaction:
  - Code 100: Card number not found in `card_xref`
  - Code 101: Account not found in `accounts`
  - Code 102: Transaction would exceed credit limit (overlimit)
  - Code 103: Transaction after account expiration date
- Posts valid transactions to `transactions` table
- Writes rejects to `daily_transaction_rejects` table
- Updates `accounts` balances (current balance, cycle credit/debit)
- Upserts `transaction_category_balances`

If both 102 and 103 apply, code 103 takes priority (matches COBOL behaviour where expiration check overwrites overlimit).

### CBACT04C - Interest Calculator

**What it does:**
- Reads `transaction_category_balances` (driving table)
- Looks up interest rate from `disclosure_groups` (with DEFAULT fallback)
- Computes: `monthly_interest = (category_balance * annual_rate) / 1200`
- Writes interest transaction records to `transactions`
- Updates `accounts`: adds total interest to balance, resets cycle credit/debit to 0

### CBSTM03 - Account Statements (CSV)

**What it does:**
- Joins `card_xref` → `customers` → `accounts` for statement headers
- Matches `transactions` by card number
- Outputs CSV with: card number, account ID, customer name, address, balance, FICO score, transaction details, totals

### CBTRN03C - Transaction Detail Report (CSV)

**What it does:**
- Filters `transactions` by date range (on `tran_proc_ts`)
- Enriches with account ID (via `card_xref`), type descriptions, category descriptions
- Computes account totals (control break on card number), page totals (every 20 rows), grand total
- Outputs CSV report files: `detail/`, `account_totals/`, `page_totals/`

## Sequential Processing Notes

The original COBOL programs process records sequentially, where each record's processing can affect subsequent records (e.g., balance updates affect overlimit checks). The PySpark pipelines replicate this behaviour using:

- **Window functions** with `rowsBetween(unboundedPreceding, currentRow)` for running cumulative calculations (CBTRN02C overlimit check)
- **MERGE operations** for VSAM KSDS upsert patterns (CBTRN02C category balance updates)
- **Control break logic** replicated via `groupBy` and window partitioning (CBTRN03C account totals)
- **Ordered processing** via `orderBy` on timestamp columns to maintain the original sequential semantics
