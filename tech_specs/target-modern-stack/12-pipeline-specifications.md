# CardDemo PySpark Pipeline Specifications
## Detailed Per-Program Pipeline Specifications

**Document Version:** 1.0  
**Date:** 2026-04-06  
**Catalog:** `carddemo`

---

## Table of Contents

1. [CBACT01C — Account File Processing Pipeline](#1-cbact01c--account-file-processing-pipeline)
2. [CBACT02C — Card List Report Pipeline](#2-cbact02c--card-list-report-pipeline)
3. [CBACT03C — Cross-Reference Extract Pipeline](#3-cbact03c--cross-reference-extract-pipeline)
4. [CBACT04C — Interest Calculation Pipeline](#4-cbact04c--interest-calculation-pipeline)
5. [CBCUS01C — Customer File Processing Pipeline](#5-cbcus01c--customer-file-processing-pipeline)
6. [CBTRN01C — Transaction Verification Pipeline](#6-cbtrn01c--transaction-verification-pipeline)
7. [CBTRN02C — Daily Transaction Posting Pipeline](#7-cbtrn02c--daily-transaction-posting-pipeline)
8. [CBTRN03C — Transaction Category Report Pipeline](#8-cbtrn03c--transaction-category-report-pipeline)
9. [CBSTM03A/B — Statement Generation Pipeline](#9-cbstm03ab--statement-generation-pipeline)
10. [CBEXPORT — Data Export Pipeline](#10-cbexport--data-export-pipeline)
11. [CBIMPORT — Data Import Pipeline](#11-cbimport--data-import-pipeline)
12. [CBPAUP0C — Authorization Purge Pipeline](#12-cbpaup0c--authorization-purge-pipeline)
13. [PAUDBUNL — Authorization DB Unload Pipeline](#13-paudbunl--authorization-db-unload-pipeline)
14. [PAUDBLOD — Authorization DB Load Pipeline](#14-paudblod--authorization-db-load-pipeline)
15. [DBUNLDGS — GSAM Unload Pipeline](#15-dbunldgs--gsam-unload-pipeline)
16. [COBTUPDT — Transaction Type Maintenance Pipeline](#16-cobtupdt--transaction-type-maintenance-pipeline)
17. [COACCT01 — Account Inquiry Service](#17-coacct01--account-inquiry-service)
18. [CODATE01 — Date Service](#18-codate01--date-service)

---

## 1. CBACT01C — Account File Processing Pipeline

### 1.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBACT01C (app/cbl/CBACT01C.cbl) |
| JCL Job | READACCT.jcl |
| Databricks Job Name | `cbact01c_account_file_proc` |
| Function | Sequential account file read; generate multiple output formats (fixed, array, variable-length) |
| Replaces | COBOL paragraphs: PROCEDURE DIVISION, 1000-ACCTFILE-GET-NEXT, 1100-DISPLAY-ACCT-RECORD, 1300-POPUL-ACCT-RECORD, 1350-WRITE-ACCT-RECORD, 1400-POPUL-ARRAY-RECORD, 1500-POPUL-VBRC-RECORD |

### 1.2 Input Delta Tables

| Delta Table | Replaces | Access Pattern |
|------------|---------|----------------|
| `carddemo.silver.account` | VSAM KSDS ACCTFILE (DD: ACCTFILE) | Full sequential scan (no filter) |

### 1.3 Output Delta Tables

| Delta Table | Replaces | Write Mode |
|------------|---------|------------|
| `carddemo.bronze.account_fixed_out` | Sequential OUTFILE (OUT-ACCT-REC) | Overwrite (partition by run_date) |
| `carddemo.bronze.account_array_out` | Sequential ARRYFILE (ARR-ARRAY-REC) | Overwrite |
| `carddemo.bronze.account_vbr_short_out` | VBRCFILE VBR-REC1 (12-byte records) | Overwrite |
| `carddemo.bronze.account_vbr_long_out` | VBRCFILE VBR-REC2 (39-byte records) | Overwrite |
| `carddemo.migration_ctrl.pipeline_metrics` | SYSOUT statistics | Append |

### 1.4 Step-by-Step Processing Logic

#### Step 1: Read Source (replaces 0000-ACCTFILE-OPEN + 1000-ACCTFILE-GET-NEXT loop)
```python
# Replace: OPEN INPUT ACCTFILE, PERFORM UNTIL END-OF-FILE = 'Y': READ ACCTFILE INTO ACCOUNT-RECORD
accounts_df = spark.read.format("delta").table("carddemo.silver.account")
```

#### Step 2: Date Reformatting (replaces 1300-POPUL-ACCT-RECORD + COBDATFT call)
```python
# Replace: CALL 'COBDATFT' USING CODATECN-REC (TYPE='2', OUTTYPE='2')
# COBDATFT reformats ACCT-REISSUE-DATE from CODATECN-INP-DATE (X(10)) to CODATECN-0UT-DATE (X(10))
# The assembler date formatter with type='2'/'2' is a date string reformatter
# Replace with Python datetime parsing and formatting
from pyspark.sql import functions as F

def reformat_reissue_date(date_str):
    """
    Replaces: CALL 'COBDATFT' USING CODATECN-REC
    CODATECN-TYPE='2', CODATECN-OUTTYPE='2'
    Source format: ACCT-REISSUE-DATE PIC X(10) as stored in VSAM
    Output: reformatted date string
    TODO: VERIFY — exact COBDATFT type='2' format requires confirmation with source assembler spec
    """
    # Assuming input/output both YYYY-MM-DD given PIC X(10) date field
    return date_str  # Passthrough unless format confirmation reveals different behavior

reformat_date_udf = F.udf(reformat_reissue_date, StringType())
```

#### Step 3: Zero Debit Substitution (replaces paragraph 1300-POPUL-ACCT-RECORD lines 236-238)
```python
# Replace: IF ACCT-CURR-CYC-DEBIT = 0 MOVE 2525.00 TO OUT-ACCT-CURR-CYC-DEBIT
# NOTE: This is a hardcoded test/demonstration value in the original COBOL
# BUSINESS RULE: If current cycle debit is zero, substitute 2525.00 in OUTFILE output
out_fixed_df = accounts_df.withColumn(
    "out_acct_curr_cyc_debit",
    F.when(F.col("acct_curr_cyc_debit") == 0, F.lit(Decimal("2525.00")))
     .otherwise(F.col("acct_curr_cyc_debit"))
)
```

#### Step 4: Array Record Population (replaces 1400-POPUL-ARRAY-RECORD)
```python
# Replace: ARR-ACCT-BAL(1) through ARR-ACCT-BAL(3) with hardcoded test values
# BUSINESS RULE (paragraph 1400, lines 255-260):
#   ARR-ACCT-CURR-BAL(1) = actual ACCT-CURR-BAL (no hardcode)
#   ARR-ACCT-CURR-CYC-DEBIT(1) = 1005.00 (hardcoded)
#   ARR-ACCT-CURR-BAL(2) = 1525.00 (hardcoded)
#   ARR-ACCT-CURR-CYC-DEBIT(2) = -1025.00 (hardcoded)
#   ARR-ACCT-CURR-BAL(3) = -2500.00 (hardcoded)  [TODO: VERIFY exact values]
#   Occurrences 4 and 5 remain zero (initialized)
# This reproduces the COBOL OCCURS 5 TIMES array with hardcoded test data
array_records = []
for occurrence in range(1, 6):  # OCCURS 5 TIMES
    array_records.append(
        accounts_df.withColumn("occurrence_num", F.lit(occurrence))
                   .withColumn("arr_acct_curr_bal", apply_array_balance_rule(occurrence))
                   .withColumn("arr_acct_curr_cyc_debit", apply_array_debit_rule(occurrence))
    )
```

#### Step 5: Variable-Length Record Generation (replaces 1500-POPUL-VBRC-RECORD + 1550-WRITE-VB1 + 1575-WRITE-VB2)
```python
# Replace: Two WRITE calls per account to VBRCFILE
# VBR-REC1 (12 bytes): ACCT-ID + ACCT-ACTIVE-STATUS
# VBR-REC2 (39 bytes): ACCT-ID + ACCT-CURR-BAL + ACCT-CREDIT-LIMIT + ACCT-REISSUE-YYYY

vbr_short_df = accounts_df.select(
    F.col("acct_id"),
    F.col("acct_active_status"),
    F.lit("VBR1").alias("record_type"),
    F.lit(12).alias("record_length")  # WS-RECD-LEN = 12
)

vbr_long_df = accounts_df.select(
    F.col("acct_id"),
    F.col("acct_curr_bal"),
    F.col("acct_credit_limit"),
    F.year(F.col("acct_reissue_date")).alias("acct_reissue_yyyy"),  # VB2-ACCT-REISSUE-YYYY X(4)
    F.lit("VBR2").alias("record_type"),
    F.lit(39).alias("record_length")  # WS-RECD-LEN = 39
)
```

### 1.5 Business Rules

| COBOL Rule | Paragraph | PySpark Implementation |
|-----------|-----------|----------------------|
| Zero debit substitution: if `ACCT-CURR-CYC-DEBIT = 0` → output 2525.00 | 1300-POPUL-ACCT-RECORD (lines 236-238) | `F.when(debit==0, 2525.00).otherwise(debit)` |
| COBDATFT date reformatting with TYPE='2', OUTTYPE='2' | 1300-POPUL-ACCT-RECORD (line 231) | Python `datetime.strptime/strftime` — TODO: VERIFY format spec |
| Array occurrence 1: real balance, hardcoded debit 1005.00 | 1400-POPUL-ARRAY-RECORD | `F.when(occ==1, 1005.00)` |
| Array occurrences 4-5: remain zero | 1400-POPUL-ARRAY-RECORD | `F.when(occ > 3, 0.00)` |
| VBR short record: 12 bytes (ACCT-ID + ACTIVE-STATUS) | 1550-WRITE-VB1-RECORD | Separate DataFrame with 2 columns |
| VBR long record: 39 bytes (ACCT-ID + BAL + LIMIT + REISSUE-YYYY) | 1575-WRITE-VB2-RECORD | Separate DataFrame with 4 columns |

### 1.6 Error Handling

| COBOL Condition | COBOL Action | PySpark Equivalent |
|----------------|-------------|-------------------|
| ACCTFILE open failure | 9999-ABEND-PROGRAM (CEE3ABD code 999) | Raise `RuntimeError("Cannot read silver.account table")` |
| ACCTFILE status not '00'/'10' | 9910-DISPLAY-IO-STATUS + 9999-ABEND | Try/except on Delta read; re-raise as job failure |
| OUTFILE write failure | 9910 + 9999-ABEND | Try/except on Delta write; raise job failure |

### 1.7 Performance Considerations

- Full table scan of `silver.account` — no filter needed (matches COBOL sequential read)
- All 4 output DataFrames derived from single scan (cache `accounts_df` before branching)
- Array records expand 1-to-5 via `F.explode(F.array(...))` — small fan-out, no performance concern

### 1.8 Checkpoint/Restart Strategy

- **Idempotent**: All outputs use `OVERWRITE` mode with `replaceWhere` on `run_date` partition
- Re-running the pipeline replaces the entire run's output — safe to restart from scratch

---

## 2. CBACT02C — Card List Report Pipeline

### 2.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBACT02C (app/cbl/CBACT02C.cbl) |
| Function | Sequential read of CARDFILE; print all card records to SYSOUT |
| Databricks Job Name | `cbact02c_card_list_report` |

### 2.2 Input Delta Tables

| Delta Table | Replaces | Access Pattern |
|------------|---------|----------------|
| `carddemo.silver.card` | VSAM KSDS CARDFILE (DD: CARDFILE) | Full sequential scan |

### 2.3 Output Delta Tables

| Delta Table | Replaces | Write Mode |
|------------|---------|------------|
| `carddemo.migration_ctrl.pipeline_metrics` | SYSOUT DISPLAY | Append |

**Note:** CBACT02C in COBOL produces no output files — only SYSOUT (DISPLAY) output. The PySpark pipeline logs a summary count to pipeline_metrics and uses Databricks job logs (stdout) to replace the DISPLAY output. No Delta table output is required to match the original program's business function.

### 2.4 Processing Logic

```python
# Replace: PERFORM UNTIL END-OF-FILE = 'Y': READ CARDFILE INTO CARD-RECORD: DISPLAY CARD-RECORD
# Replaces PROCEDURE DIVISION (lines 70-87) + 1000-CARDFILE-GET-NEXT

cards_df = spark.read.format("delta").table("carddemo.silver.card")
record_count = cards_df.count()  # Equivalent to counting loop iterations

# Log each record (replaces DISPLAY CARD-RECORD at line 78)
# Use Databricks display() or write to log file — not a separate Delta table
# The DISPLAY in COBOL was diagnostic/listing output only
```

### 2.5 Business Rules

- **Read-only diagnostic utility**: No business transformations; pure listing program
- **Full sequential scan**: No filtering applied
- **Note on duplicate display**: The COBOL source has a bug where `DISPLAY CARD-RECORD` appears both inside `1000-CARDFILE-GET-NEXT` (line 96, commented out) and in the main loop body (line 78). The PySpark implementation displays each record **once** (correcting the behavior to the intended single-display design)

---

## 3. CBACT03C — Cross-Reference Extract Pipeline

### 3.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBACT03C (app/cbl/CBACT03C.cbl) |
| JCL Job | READXREF.jcl |
| Databricks Job Name | `cbact03c_xref_extract` |
| Function | Sequential read of XREFFILE (CCXREF); print all cross-reference records |

### 3.2 Input/Output

- **Input:** `carddemo.silver.card_xref` (replaces VSAM KSDS CCXREF, DD: XREFFILE)
- **Output:** `carddemo.migration_ctrl.pipeline_metrics` only (SYSOUT-equivalent listing)

### 3.3 Processing Logic

```python
# Replace: 1000-XREFFILE-GET-NEXT loop + DISPLAY CARD-XREF-RECORD
xref_df = spark.read.format("delta").table("carddemo.silver.card_xref")

# Note: Original COBOL has a duplicate DISPLAY bug (records printed twice)
# Each record has DISPLAY in BOTH 1000-XREFFILE-GET-NEXT (line 96) AND main loop (line 78)
# The PySpark pipeline displays each record ONCE (corrects the defect)
```

### 3.4 Business Rules

- **Read-only diagnostic utility**: No writes except metrics
- **XREF structure**: Each record links `card_num` (16 chars) to `cust_id` (9 digits) and `acct_id` (11 digits)
- **Duplicate display defect**: Not replicated — PySpark displays each record once

---

## 4. CBACT04C — Interest Calculation Pipeline

### 4.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBACT04C (app/cbl/CBACT04C.cbl) |
| JCL Job | INTCALC.jcl |
| Databricks Job Name | `cbact04c_interest_calc` |
| Function | Interest calculator: reads TCATBALF, looks up rates from DISCGRP, computes monthly interest, writes interest transactions to TRANSACT, updates ACCTFILE balances |

### 4.2 Input Delta Tables

| Delta Table | Replaces | Access Pattern |
|------------|---------|----------------|
| `carddemo.silver.tran_cat_balance` | VSAM KSDS TCATBALF (DD: TCATBALF) — driving file, sorted by acct_id | Sort by `acct_id` to match COBOL sequential account grouping |
| `carddemo.silver.disclosure_group` | VSAM KSDS DISCGRP (DD: DISCGRP) | Broadcast join (small reference table) |
| `carddemo.silver.card_xref` | VSAM KSDS XREFFILE (DD: XREFFILE) | Random read by `acct_id` to get card number |
| `carddemo.silver.account` | VSAM KSDS ACCTFILE (DD: ACCTFILE) | Random read by `acct_id` for group lookup; REWRITE for balance update |

### 4.3 Output Delta Tables

| Delta Table | Replaces | Write Mode |
|------------|---------|------------|
| `carddemo.silver.transaction` | VSAM KSDS TRANSACT (DD: TRANSACT, OUTPUT) | MERGE (insert new interest charge rows) |
| `carddemo.silver.account` | VSAM KSDS ACCTFILE (DD: ACCTFILE, I-O, REWRITE) | MERGE (update `acct_curr_bal`, zero `acct_curr_cyc_credit`, `acct_curr_cyc_debit`) |
| `carddemo.gold.interest_charges` | SYSOUT audit trail | Append |

### 4.4 Parameters (replaces JCL PARM)

| Parameter | COBOL Field | Description |
|-----------|------------|-------------|
| `run_date` | `PARM-DATE X(10)` | Date embedded in generated TRAN-IDs |

### 4.5 Step-by-Step Processing Logic

#### Step 1: Read and Sort Driving File (replaces 1000-TCATBALF-GET-NEXT)
```python
# Replace: READ TCATBAL-FILE INTO TRAN-CAT-BAL-RECORD (sequential)
# COBOL assumes TCATBALF is sorted by TRANCAT-ACCT-ID
tcatbal_df = (spark.read.format("delta")
              .table("carddemo.silver.tran_cat_balance")
              .orderBy("acct_id", "tran_type_cd", "tran_cat_cd"))
```

#### Step 2: Broadcast Interest Rate Lookup (replaces 1200-GET-INTEREST-RATE + 1200-A-GET-DEFAULT-INT-RATE)
```python
# Replace: READ DISCGRP-FILE by composite key (GROUP-ID + TYPE-CD + CAT-CD)
# With fallback to 'DEFAULT' group (1200-A-GET-DEFAULT-INT-RATE) when status='23'
discgrp_df = spark.read.format("delta").table("carddemo.silver.disclosure_group")
discgrp_broadcast = F.broadcast(discgrp_df)

# Primary rate lookup: join on actual group_id + type_cd + cat_cd
# Fallback: join on 'DEFAULT' group_id when primary not found
# This replicates: 1200-GET-INTEREST-RATE → if status='23' → 1200-A-GET-DEFAULT-INT-RATE
acct_df = spark.read.format("delta").table("carddemo.silver.account")

tcatbal_with_rate = (tcatbal_df
    .join(acct_df.select("acct_id", "acct_group_id"), "acct_id", "left")
    .join(discgrp_broadcast,
          [tcatbal_df.acct_id == acct_df.acct_id,
           F.col("tran_type_cd") == F.col("dis_tran_type_cd"),
           F.col("tran_cat_cd") == F.col("dis_tran_cat_cd"),
           F.col("acct_group_id") == F.col("dis_acct_group_id")],
          "left")
)

# Fallback for rows where primary lookup failed (status='23' equivalent)
default_rate_df = discgrp_df.filter(F.col("dis_acct_group_id") == "DEFAULT")

tcatbal_with_rate = tcatbal_with_rate.join(
    default_rate_df.withColumnRenamed("dis_int_rate", "dis_int_rate_default"),
    (F.col("tran_type_cd") == F.col("dis_tran_type_cd")) &
    (F.col("tran_cat_cd") == F.col("dis_tran_cat_cd")),
    "left"
).withColumn(
    "effective_int_rate",
    F.coalesce(F.col("dis_int_rate"), F.col("dis_int_rate_default"))
)
```

#### Step 3: Interest Calculation (replaces 1300-COMPUTE-INTEREST)
```python
# Replace: COMPUTE WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200
# CRITICAL: Use DecimalType arithmetic, not floating point
# Formula: annual_rate / 12 months / 100 percent = monthly fraction
interest_df = (tcatbal_with_rate
    .filter(F.col("effective_int_rate").isNotNull())
    .filter(F.col("effective_int_rate") != 0)  # Skip zero-rate categories
    .withColumn(
        "monthly_interest",
        (F.col("tran_cat_bal").cast(DecimalType(11, 2)) *
         F.col("effective_int_rate").cast(DecimalType(7, 4)) /
         F.lit(Decimal("1200"))).cast(DecimalType(11, 2))
    )
)
```

#### Step 4: Account-Level Aggregation (replaces 1050-UPDATE-ACCOUNT accumulation logic)
```python
# Replace: WS-TOTAL-INT accumulates all category interests per account
# In COBOL: ADD WS-MONTHLY-INT TO WS-TOTAL-INT; then 1050-UPDATE-ACCOUNT on account change
account_interest_df = (interest_df
    .groupBy("acct_id")
    .agg(
        F.sum("monthly_interest").cast(DecimalType(11, 2)).alias("total_interest"),
        F.collect_list(F.struct("tran_type_cd", "tran_cat_cd", "monthly_interest")).alias("detail")
    )
)
```

#### Step 5: Generate Interest Transaction Records (replaces 1300-B-WRITE-TX)
```python
# Replace: Build TRAN-RECORD with:
#   TRAN-TYPE-CD = '01'
#   TRAN-CAT-CD = 05
#   TRAN-SOURCE = 'System'
#   TRAN-MERCHANT-ID = 0
#   TRAN-DESC = 'Int. for a/c ' + ACCT-ID
#   TRAN-ID = PARM-DATE + WS-TRANID-SUFFIX (zero-padded 6-digit counter)
#   TRAN-ORIG-TS and TRAN-PROC-TS = DB2-FORMAT-TS (from FUNCTION CURRENT-DATE)
run_date = get_run_date_param()
current_ts = F.current_timestamp()

xref_df = spark.read.format("delta").table("carddemo.silver.card_xref")

interest_transactions_df = (account_interest_df
    .join(xref_df.select("acct_id", "card_num"), "acct_id", "left")
    .withColumn("tran_id",
        F.concat(F.lit(run_date.replace("-", "")),
                 F.lpad(F.monotonically_increasing_id().cast("string"), 6, "0")))
    .withColumn("tran_type_cd", F.lit("01"))
    .withColumn("tran_cat_cd", F.lit(5))
    .withColumn("tran_source", F.lit("System"))
    .withColumn("tran_desc",
        F.concat(F.lit("Int. for a/c "),
                 F.col("acct_id").cast("string")))
    .withColumn("tran_amt", F.col("total_interest"))
    .withColumn("tran_merchant_id", F.lit(0))
    .withColumn("tran_orig_ts", current_ts)
    .withColumn("tran_proc_ts", current_ts)
    .withColumn("tran_card_num", F.col("card_num"))
)
```

#### Step 6: Update Account Balances (replaces 1050-UPDATE-ACCOUNT REWRITE)
```python
# Replace: 1050-UPDATE-ACCOUNT:
#   ACCT-CURR-BAL += WS-TOTAL-INT
#   ACCT-CURR-CYC-CREDIT = 0
#   ACCT-CURR-CYC-DEBIT = 0
#   REWRITE ACCOUNT-FILE FROM ACCOUNT-RECORD
DeltaTable.forName(spark, "carddemo.silver.account").alias("target").merge(
    account_interest_df.alias("source"),
    "target.acct_id = source.acct_id"
).whenMatchedUpdate(set={
    "acct_curr_bal": "target.acct_curr_bal + source.total_interest",
    "acct_curr_cyc_credit": "CAST(0 AS DECIMAL(12,2))",
    "acct_curr_cyc_debit": "CAST(0 AS DECIMAL(12,2))",
    "_silver_last_updated_ts": "CURRENT_TIMESTAMP()"
}).execute()
```

### 4.6 Business Rules

| COBOL Rule | Paragraph | PySpark Implementation |
|-----------|-----------|----------------------|
| Interest formula: `WS-MONTHLY-INT = (TRAN-CAT-BAL × DIS-INT-RATE) / 1200` | 1300-COMPUTE-INTEREST | `(bal * rate / 1200).cast(DecimalType(11,2))` |
| Fallback to 'DEFAULT' group when rate not found | 1200-A-GET-DEFAULT-INT-RATE | Left join to default rate, `coalesce()` |
| Skip zero-rate categories entirely | 1300-COMPUTE-INTEREST (zero-rate bypass) | `filter(effective_int_rate != 0)` |
| Balance update: bal += total_int; cycle credit/debit = 0 | 1050-UPDATE-ACCOUNT | Delta MERGE update |
| TRAN-TYPE-CD='01', TRAN-CAT-CD=05 for interest charges | 1300-B-WRITE-TX | Hardcoded in `withColumn` |
| TRAN-ID = PARM-DATE (10 chars) + 6-digit suffix counter | 1300-B-WRITE-TX | `concat(run_date, lpad(monotonically_increasing_id, 6, '0'))` |
| Fee computation (1400-COMPUTE-FEES) is a stub — EXIT only | 1400-COMPUTE-FEES | Not implemented (matching COBOL stub behavior) |
| Account not found in ACCTFILE → continue (no abend) | 1100-GET-ACCT-DATA (INVALID KEY) | Log to error_log; skip account |
| XREF not found → continue (no abend) | 1110-GET-XREF-DATA (INVALID KEY) | Log to error_log; tran_card_num = NULL |

### 4.7 Error Handling

| COBOL Condition | COBOL Action | PySpark Equivalent |
|----------------|-------------|-------------------|
| TCATBALF EOF | Normal termination + final REWRITE | Loop terminates; final `account_interest_df` batch written |
| DISCGRP not found, no DEFAULT | Status error → ABEND | Raise warning; skip account; log to error_log |
| ACCOUNT-FILE not found on REWRITE | DISPLAY + ABEND | `MERGE` with `WHEN NOT MATCHED` ignored; log error |
| TRANSACT-FILE write failure | ABEND | Exception on Delta write; job fails |

### 4.8 Data Quality Checks

1. All generated TRAN-IDs must be unique within the run (assert no duplicates post-write)
2. Sum of interest charges must equal sum of account balance increases
3. Every processed account must have a matching XREF record (log missing XREFs as warnings)

---

## 5. CBCUS01C — Customer File Processing Pipeline

### 5.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBCUS01C (app/cbl/CBCUS01C.cbl) |
| JCL Job | READCUST.jcl |
| Databricks Job Name | `cbcus01c_customer_file_proc` |
| Function | Sequential read of CUSTFILE; print all customer records (diagnostic listing) |

### 5.2 Input/Output

- **Input:** `carddemo.silver.customer` (replaces VSAM KSDS CUSTFILE)
- **Output:** `carddemo.migration_ctrl.pipeline_metrics` (Databricks job logs replace SYSOUT DISPLAY)

### 5.3 Processing Logic

```python
# Replace: PERFORM UNTIL END-OF-FILE = 'Y': READ CUSTFILE INTO CUSTOMER-RECORD: DISPLAY CUSTOMER-RECORD
# NOTE: COBOL has double-display defect — both inside 1000-CUSTFILE-GET-NEXT (line 96)
# AND in main loop (line 78). PySpark displays each record ONCE (corrects defect)
customers_df = spark.read.format("delta").table("carddemo.silver.customer")
```

---

## 6. CBTRN01C — Transaction Verification Pipeline

### 6.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBTRN01C (app/cbl/CBTRN01C.cbl) |
| JCL Job | POSTTRAN.jcl (verification step) |
| Databricks Job Name | `cbtrn01c_tran_verify` |
| Function | Daily transaction verification: cross-check each DALYTRAN record against XREFFILE (card lookup) and ACCTFILE (account existence). No posting. |

### 6.2 Input Delta Tables

| Delta Table | Replaces | Access Pattern |
|------------|---------|----------------|
| `carddemo.bronze.daily_transactions` | Sequential file DALYTRAN (DD: DALYTRAN) | Full scan, partitioned by batch_date |
| `carddemo.silver.card_xref` | VSAM KSDS XREFFILE (DD: XREFFILE) | Random read by `card_num` (2000-LOOKUP-XREF) |
| `carddemo.silver.account` | VSAM KSDS ACCTFILE (DD: ACCTFILE) | Random read by `acct_id` (3000-READ-ACCOUNT) |

**Note on unused files:** In CBTRN01C, CUSTFILE, CARDFILE, and TRANSACT-FILE are opened and closed but never read. The PySpark pipeline does not reference these tables — no equivalent joins needed. This matches the COBOL "dead code" behavior documented in Section 9 of the spec (see note on unused files).

### 6.3 Output Delta Tables

| Delta Table | Replaces | Write Mode |
|------------|---------|------------|
| `carddemo.migration_ctrl.pipeline_metrics` | SYSOUT DISPLAY | Append |
| `carddemo.migration_ctrl.error_log` | DISPLAY 'INVALID CARD NUMBER' / 'INVALID ACCOUNT NUMBER' | Append |

### 6.4 Processing Logic

#### Step 1: Read Daily Transactions and Join XREF
```python
# Replace: 1000-DALYTRAN-GET-NEXT + 2000-LOOKUP-XREF
batch_date = get_batch_date_param()

dalytran_df = (spark.read.format("delta")
    .table("carddemo.bronze.daily_transactions")
    .filter(F.col("_meta_batch_date") == batch_date))

xref_df = spark.read.format("delta").table("carddemo.silver.card_xref")

# Perform XREF lookup (replaces 2000-LOOKUP-XREF READ XREF-FILE by FD-XREF-CARD-NUM)
dalytran_with_xref = dalytran_df.join(
    xref_df.select("card_num", "acct_id", "cust_id").alias("xref"),
    dalytran_df.dalytran_card_num == xref_df.card_num,
    "left"
)
```

#### Step 2: Identify XREF Failures (replaces 2000-LOOKUP-XREF INVALID KEY)
```python
# Replace: WS-XREF-READ-STATUS = 4 when INVALID KEY
# COBOL action: DISPLAY 'INVALID CARD NUMBER FOR XREF'; continue processing
xref_failed = dalytran_with_xref.filter(F.col("acct_id").isNull())
xref_ok = dalytran_with_xref.filter(F.col("acct_id").isNotNull())
```

#### Step 3: Account Existence Check (replaces 3000-READ-ACCOUNT — only when XREF succeeded)
```python
# Replace: 3000-READ-ACCOUNT: READ ACCOUNT-FILE KEY IS FD-ACCT-ID
# Only performed when xref lookup succeeded (cascading INVALID KEY from COBOL)
acct_df = spark.read.format("delta").table("carddemo.silver.account")

xref_with_acct = xref_ok.join(
    acct_df.select("acct_id").alias("acct"),
    "acct_id",
    "left"
)
acct_failed = xref_with_acct.filter(F.col("acct.acct_id").isNull())
acct_ok = xref_with_acct.filter(F.col("acct.acct_id").isNotNull())
```

### 6.5 Business Rules

| COBOL Rule | Paragraph | PySpark Implementation |
|-----------|-----------|----------------------|
| XREF lookup fails → skip account lookup | 2000-LOOKUP-XREF (cascading INVALID KEY) | Left join; `null` XREF result skips account join |
| All results logged to SYSOUT | DISPLAY statements throughout | Databricks job log + error_log table |
| No writes to any dataset | CBTRN01C spec Section 9.1 | Confirm no Delta writes (read-only pipeline) |
| CUSTFILE/CARDFILE/TRANSACT-FILE opened but unused | CBTRN01C spec Section 5 | These Delta tables are NOT joined (dead code preserved as no-op) |

---

## 7. CBTRN02C — Daily Transaction Posting Pipeline

### 7.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBTRN02C (app/cbl/CBTRN02C.cbl) |
| JCL Job | POSTTRAN.jcl |
| Databricks Job Name | `cbtrn02c_tran_posting` |
| Function | Daily transaction posting: validate, post valid transactions to TRANSACT; update ACCTFILE balances and TCATBALF category balances; write rejects to DALYREJS. RC=4 if any rejects. |

### 7.2 Input Delta Tables

| Delta Table | Replaces | Access Pattern |
|------------|---------|----------------|
| `carddemo.bronze.daily_transactions` | Sequential file DALYTRAN (DD: DALYTRAN) — driving file | Full scan by batch_date partition |
| `carddemo.silver.card_xref` | VSAM KSDS XREFFILE (DD: XREFFILE) | Random join by card_num |
| `carddemo.silver.account` | VSAM KSDS ACCTFILE (DD: ACCTFILE, I-O) | Random read + REWRITE |

### 7.3 Output Delta Tables

| Delta Table | Replaces | Write Mode |
|------------|---------|------------|
| `carddemo.silver.transaction` | VSAM KSDS TRANSACT/TRANFILE (DD: TRANFILE, OUTPUT) | MERGE insert (new records only) |
| `carddemo.silver.account` | VSAM KSDS ACCTFILE (REWRITE) | MERGE update balances |
| `carddemo.silver.tran_cat_balance` | VSAM KSDS TCATBALF (I-O, WRITE or REWRITE) | MERGE upsert (insert if new, update if exists) |
| `carddemo.gold.daily_rejects` | Sequential file DALYREJS (DD: DALYREJS, OUTPUT) | Overwrite by reject_date partition |
| `carddemo.migration_ctrl.pipeline_metrics` | SYSOUT statistics + RETURN-CODE=4 | Append |

### 7.4 Step-by-Step Processing Logic

#### Step 1: Read Daily Transactions
```python
# Replace: 0000-DALYTRAN-OPEN + 1000-DALYTRAN-GET-NEXT loop
dalytran_df = (spark.read.format("delta")
    .table("carddemo.bronze.daily_transactions")
    .filter(F.col("_meta_batch_date") == batch_date))
```

#### Step 2: Validation — XREF Lookup (replaces 1500-A-LOOKUP-XREF)
```python
# Replace: 1500-A-LOOKUP-XREF
# READ XREF-FILE by DALYTRAN-CARD-NUM
# INVALID KEY: WS-VALIDATION-FAIL-REASON = 100, 'INVALID CARD NUMBER FOUND'
xref_df = spark.read.format("delta").table("carddemo.silver.card_xref")
with_xref = dalytran_df.join(
    xref_df.select("card_num", "acct_id").alias("xref"),
    F.col("dalytran_card_num") == F.col("xref.card_num"),
    "left"
).withColumn(
    "validation_fail_reason",
    F.when(F.col("xref.acct_id").isNull(), F.lit(100)).otherwise(F.lit(0))
)
```

#### Step 3: Validation — Account Lookup + Balance/Expiry Checks (replaces 1500-B-LOOKUP-ACCT)
```python
# Replace: 1500-B-LOOKUP-ACCT
# READ ACCOUNT-FILE by XREF-ACCT-ID
# INVALID KEY: WS-VALIDATION-FAIL-REASON = 101
# WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT
# IF WS-TEMP-BAL > ACCT-CREDIT-LIMIT: reason = 102
# IF ACCT-EXPIRAION-DATE < current date: reason = 103 (TODO: VERIFY comparison type)
acct_df = spark.read.format("delta").table("carddemo.silver.account")

# Only validate account when XREF succeeded (reason==0)
xref_ok = with_xref.filter(F.col("validation_fail_reason") == 0)
xref_fail = with_xref.filter(F.col("validation_fail_reason") != 0)

with_acct = xref_ok.join(
    acct_df.alias("acct"),
    F.col("xref.acct_id") == F.col("acct.acct_id"),
    "left"
)

validated = with_acct.withColumn(
    "ws_temp_bal",
    F.col("acct.acct_curr_cyc_credit") -
    F.col("acct.acct_curr_cyc_debit") +
    F.col("dalytran_amt_raw").cast(DecimalType(11, 2))
).withColumn(
    "validation_fail_reason",
    F.when(F.col("acct.acct_id").isNull(), F.lit(101))
     .when(F.col("ws_temp_bal") > F.col("acct.acct_credit_limit"), F.lit(102))
     .when(F.col("acct.acct_expiraion_date") < F.current_date(), F.lit(103))
     .otherwise(F.lit(0))
)
```

#### Step 4: Split Valid vs Rejected
```python
# Replace: IF WS-VALIDATION-FAIL-REASON = 0: 2000-POST-TRANSACTION ELSE: 2500-WRITE-REJECT-REC
all_validated = validated.unionByName(xref_fail, allowMissingColumns=True)
valid_trans = all_validated.filter(F.col("validation_fail_reason") == 0)
rejected_trans = all_validated.filter(F.col("validation_fail_reason") != 0)
```

#### Step 5: Build and Write Posted Transactions (replaces 2000-POST-TRANSACTION + 2900-WRITE-TRANSACTION-FILE)
```python
# Replace: 2000-POST-TRANSACTION — map DALYTRAN-* to TRAN-RECORD fields
# TRAN-PROC-TS set to current timestamp (Z-GET-DB2-FORMAT-TIMESTAMP)
posted_transactions = valid_trans.select(
    F.col("dalytran_id").alias("tran_id"),
    F.col("dalytran_type_cd").alias("tran_type_cd"),
    # ... (all DALYTRAN-* fields mapped to TRAN-* fields)
    F.current_timestamp().alias("tran_proc_ts"),
    # TRAN-ORIG-TS from DALYTRAN-ORIG-TS (unchanged)
    F.col("dalytran_orig_ts_raw").alias("tran_orig_ts")
)

DeltaTable.forName(spark, "carddemo.silver.transaction").alias("t").merge(
    posted_transactions.alias("s"), "t.tran_id = s.tran_id"
).whenNotMatchedInsertAll().execute()
```

#### Step 6: Update TCATBAL (replaces 2700-UPDATE-TCATBAL + 2700-A + 2700-B)
```python
# Replace: 2700-UPDATE-TCATBAL:
#   READ TCATBAL-FILE by composite key
#   if INVALID KEY (status '23'): 2700-A-CREATE-TCATBAL-REC (WRITE new record)
#   else: 2700-B-UPDATE-TCATBAL-REC (ADD DALYTRAN-AMT TO TRAN-CAT-BAL; REWRITE)
# The MERGE INTO ... WHEN MATCHED ... WHEN NOT MATCHED pattern replaces the READ+CREATE/UPDATE logic
tcatbal_updates = valid_trans.groupBy("xref.acct_id", "dalytran_type_cd", "dalytran_cat_cd").agg(
    F.sum("dalytran_amt_raw".cast(DecimalType(11,2))).alias("total_amt")
)

DeltaTable.forName(spark, "carddemo.silver.tran_cat_balance").alias("t").merge(
    tcatbal_updates.alias("s"),
    "t.acct_id = s.acct_id AND t.tran_type_cd = s.dalytran_type_cd AND t.tran_cat_cd = s.dalytran_cat_cd"
).whenMatchedUpdate(set={"tran_cat_bal": "t.tran_cat_bal + s.total_amt"})
 .whenNotMatchedInsert(values={"acct_id": "s.acct_id", "tran_type_cd": "s.dalytran_type_cd",
                                "tran_cat_cd": "s.dalytran_cat_cd", "tran_cat_bal": "s.total_amt"})
 .execute()
```

#### Step 7: Update Account Balances (replaces 2800-UPDATE-ACCOUNT-REC)
```python
# Replace: 2800-UPDATE-ACCOUNT-REC:
#   ADD DALYTRAN-AMT TO ACCT-CURR-BAL
#   IF DALYTRAN-AMT > 0: ADD DALYTRAN-AMT TO ACCT-CURR-CYC-CREDIT
#   IF DALYTRAN-AMT < 0: ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT (note: adds negative value)
#   REWRITE ACCOUNT-FILE

acct_updates = valid_trans.groupBy("xref.acct_id").agg(
    F.sum(F.col("dalytran_amt_raw").cast(DecimalType(11,2))).alias("net_amt"),
    F.sum(F.when(F.col("dalytran_amt_raw").cast(DecimalType(11,2)) > 0,
                 F.col("dalytran_amt_raw").cast(DecimalType(11,2)))).alias("credit_amt"),
    F.sum(F.when(F.col("dalytran_amt_raw").cast(DecimalType(11,2)) < 0,
                 F.col("dalytran_amt_raw").cast(DecimalType(11,2)))).alias("debit_amt")
)

DeltaTable.forName(spark, "carddemo.silver.account").alias("t").merge(
    acct_updates.alias("s"), "t.acct_id = s.acct_id"
).whenMatchedUpdate(set={
    "acct_curr_bal": "t.acct_curr_bal + s.net_amt",
    "acct_curr_cyc_credit": "t.acct_curr_cyc_credit + COALESCE(s.credit_amt, 0)",
    "acct_curr_cyc_debit": "t.acct_curr_cyc_debit + COALESCE(s.debit_amt, 0)"
}).execute()
```

#### Step 8: Write Rejects (replaces 2500-WRITE-REJECT-REC)
```python
# Replace: 2500-WRITE-REJECT-REC:
#   MOVE DALYTRAN-RECORD TO REJECT-TRAN-DATA (350 bytes)
#   MOVE WS-VALIDATION-TRAILER TO VALIDATION-TRAILER (80 bytes)
#   WRITE DALYREJS record (430 bytes total)
reject_df = rejected_trans.select(
    F.lit(batch_date).alias("reject_date"),
    F.col("dalytran_id"),
    F.col("dalytran_card_num"),
    F.col("dalytran_amt_raw").cast(DecimalType(11,2)).alias("dalytran_amt"),
    F.col("validation_fail_reason"),
    build_reject_description_udf(F.col("validation_fail_reason")).alias("validation_fail_desc")
)
reject_df.write.format("delta").mode("overwrite").option("replaceWhere", f"reject_date = '{batch_date}'").saveAsTable("carddemo.gold.daily_rejects")
```

#### Step 9: Set Return Code (replaces MOVE 4 TO RETURN-CODE if WS-REJECT-COUNT > 0)
```python
reject_count = rejected_trans.count()
if reject_count > 0:
    # Replaces: MOVE 4 TO RETURN-CODE
    # Databricks equivalent: exit code 4 or custom metric flag
    log_pipeline_metrics(return_code=4, records_rejected=reject_count)
    # Note: Pipeline continues; downstream tasks conditioned on return_code in Workflow
```

### 7.5 Validation Rejection Codes

| Code | COBOL Constant | Condition | Paragraph |
|------|---------------|-----------|-----------|
| 100 | WS-VALIDATION-FAIL-REASON=100 | Card number not found in XREFFILE | 1500-A-LOOKUP-XREF (INVALID KEY) |
| 101 | WS-VALIDATION-FAIL-REASON=101 | Account not found in ACCTFILE | 1500-B-LOOKUP-ACCT (INVALID KEY) |
| 102 | WS-VALIDATION-FAIL-REASON=102 | `WS-TEMP-BAL > ACCT-CREDIT-LIMIT` | 1500-B-LOOKUP-ACCT (credit limit check) |
| 103 | WS-VALIDATION-FAIL-REASON=103 | `ACCT-EXPIRAION-DATE < today` | 1500-B-LOOKUP-ACCT (expiry check) |

### 7.6 Return Code Behavior

| Condition | COBOL RETURN-CODE | Databricks Workflow Effect |
|-----------|------------------|--------------------------|
| No rejects | RC = 0 | All downstream tasks run normally |
| Any rejects | RC = 4 | Pipeline_metrics return_code = 4; workflow flag triggers notification |
| IO error / abend | RC = 8+ (via CEE3ABD) | Job task fails; downstream tasks blocked |

---

## 8. CBTRN03C — Transaction Category Report Pipeline

### 8.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBTRN03C (app/cbl/CBTRN03C.cbl) |
| JCL Job | TRANREPT.jcl |
| Databricks Job Name | `cbtrn03c_tran_report` |
| Function | Transaction detail report filtered by date range from DATEPARM; lookups for account (XREF), type description (TRANTYPE), category description (TRANCATG); 133-byte formatted report with page breaks every 20 lines, account totals, grand totals. |

### 8.2 Input Delta Tables

| Delta Table | Replaces | Access Pattern |
|------------|---------|----------------|
| `carddemo.bronze.date_params` | Sequential file DATEPARM (DD: DATEPARM) — single record | Read single row |
| `carddemo.silver.transaction` | Sequential TRANSACT/TRANFILE (DD: TRANFILE) | Scan, filter by `tran_proc_ts` date range |
| `carddemo.silver.card_xref` | VSAM KSDS CARDXREF (DD: CARDXREF) | Broadcast join by `card_num` |
| `carddemo.reference.tran_type` | VSAM KSDS TRANTYPE (DD: TRANTYPE) | Broadcast join by `tran_type_cd` |
| `carddemo.reference.tran_category` | VSAM KSDS TRANCATG (DD: TRANCATG) | Broadcast join by `(tran_type_cd, tran_cat_cd)` |

### 8.3 Output Delta Tables

| Delta Table | Replaces | Write Mode |
|------------|---------|------------|
| `carddemo.gold.transaction_report` | Sequential REPORT-FILE (DD: TRANREPT, 133-byte lines) | Overwrite by report partition |

### 8.4 Processing Logic

#### Step 1: Read Date Parameters (replaces 0550-DATEPARM-READ)
```python
# Replace: 0550-DATEPARM-READ: READ DATE-PARMS-FILE INTO WS-DATEPARM-RECORD
# WS-START-DATE at bytes 1-10, WS-END-DATE at bytes 12-21 (byte 11 = filler space)
dateparm_df = spark.read.format("delta").table("carddemo.bronze.date_params")
dateparm_row = dateparm_df.filter(F.col("_meta_pipeline_run_id") == run_id).first()
start_date = dateparm_row["start_date_raw"]
end_date = dateparm_row["end_date_raw"]
```

#### Step 2: Filter Transactions by Date Range (replaces date filter in main loop)
```python
# Replace: IF TRAN-PROC-TS(1:10) >= WS-START-DATE AND <= WS-END-DATE
# COBOL uses string comparison on first 10 chars of TRAN-PROC-TS (YYYY-MM-DD prefix)
# PySpark: compare date part of tran_proc_ts
transactions_in_range = (spark.read.format("delta")
    .table("carddemo.silver.transaction")
    .filter(F.to_date(F.col("tran_proc_ts")) >= start_date)
    .filter(F.to_date(F.col("tran_proc_ts")) <= end_date))
```

#### Step 3: Lookup Joins (replaces 1500-A-LOOKUP-XREF, 1500-B-LOOKUP-TRANTYPE, 1500-C-LOOKUP-TRANCATG)
```python
# Replace: 1500-A-LOOKUP-XREF: READ XREF-FILE by FD-XREF-CARD-NUM; INVALID KEY = ABEND
# Replace: 1500-B-LOOKUP-TRANTYPE: READ TRANTYPE-FILE by FD-TRAN-TYPE; INVALID KEY = ABEND
# Replace: 1500-C-LOOKUP-TRANCATG: READ TRANCATG-FILE by composite key; INVALID KEY = ABEND
# Note: COBOL ABENDs on any of these lookup failures (unlike CBTRN01C/02C which continue)

xref_bc = F.broadcast(spark.read.format("delta").table("carddemo.silver.card_xref"))
tran_type_bc = F.broadcast(spark.read.format("delta").table("carddemo.reference.tran_type"))
tran_cat_bc = F.broadcast(spark.read.format("delta").table("carddemo.reference.tran_category"))

enriched_df = (transactions_in_range
    .join(xref_bc, "tran_card_num", "left")
    .join(tran_type_bc, "tran_type_cd", "left")
    .join(tran_cat_bc, ["tran_type_cd", "tran_cat_cd"], "left")
)

# Validate lookups succeeded (COBOL ABENDs on failure; PySpark raises exception)
missing_xref_count = enriched_df.filter(F.col("acct_id").isNull()).count()
if missing_xref_count > 0:
    raise ValueError(f"INVALID CARD NUMBER: {missing_xref_count} transactions have unresolvable card numbers. Replaces CBTRN03C 1500-A-LOOKUP-XREF INVALID KEY abend.")
```

#### Step 4: Sort by Card Number (replaces 1100-WRITE-TRANSACTION-REPORT card-change detection)
```python
# Replace: COBOL detects card-number changes to trigger account totals
# IF TRAN-CARD-NUM != WS-CURR-CARD-NUM: write account totals for previous card
sorted_df = enriched_df.orderBy("tran_card_num", "tran_proc_ts")
```

#### Step 5: Page Break Logic and Totals (replaces WS-LINE-COUNTER / WS-PAGE-SIZE=20 / 1110-WRITE-PAGE-TOTALS)
```python
# Replace: WS-LINE-COUNTER % WS-PAGE-SIZE = 0 (every 20 lines) triggers page break
# Replace: 1120-WRITE-ACCOUNT-TOTALS on card-number change
# Replace: 1110-WRITE-GRAND-TOTALS at EOF
from pyspark.sql.window import Window

page_window = Window.partitionBy("report_run_id").orderBy("tran_card_num", "tran_proc_ts")
report_df = sorted_df.withColumn(
    "line_number", F.row_number().over(page_window)
).withColumn(
    "page_number", F.ceil(F.col("line_number") / F.lit(20))  # WS-PAGE-SIZE = 20
).withColumn(
    "is_new_card", F.col("tran_card_num") != F.lag("tran_card_num").over(page_window)
)
```

### 8.5 Business Rules

| COBOL Rule | Paragraph | PySpark Implementation |
|-----------|-----------|----------------------|
| Date filter: `TRAN-PROC-TS(1:10)` string comparison | Main loop filter | `to_date(tran_proc_ts) BETWEEN start_date AND end_date` |
| Page break every 20 lines | 1100-WRITE-TRANSACTION-REPORT (MOD function) | `CEIL(line_number / 20)` for page number |
| Account total on card-number change | Main loop (WS-CURR-CARD-NUM comparison) | Window LAG to detect card change; accumulate by card |
| Grand total = sum of page totals | 1110-WRITE-PAGE-TOTALS (ADD WS-PAGE-TOTAL TO WS-GRAND-TOTAL) | `SUM(tran_amt) OVER (PARTITION BY report_run_id)` |
| XREF/TRANTYPE/TRANCATG failures → ABEND | 1500-A/B/C paragraphs | Raise exception on null join results |

---

## 9. CBSTM03A/B — Statement Generation Pipeline

### 9.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Programs | CBSTM03A (driver) + CBSTM03B (file I/O subroutine) |
| JCL Job | CREASTMT.JCL |
| Databricks Job Name | `cbstm03_statement_gen` |
| Function | Generate account statements (plain text + HTML) for all accounts in XREFFILE. CBSTM03B is the I/O dispatcher called by CBSTM03A via a generic interface. Both programs combined into a single PySpark pipeline. |

### 9.2 CBSTM03A Notable Features (design decisions for migration)

- **ALTER/GO TO eliminated**: The `0000-START` paragraph's `ALTER` statements (used to dynamically redirect GO TO destinations for file opens) are replaced by explicit Python function calls for each file open operation
- **Mainframe control block walk eliminated**: The PSA/TCB/TIOT addressing in CBSTM03A (PSAPTR → TCB → TIOT) that walks DD names is cloud-irrelevant; replaced by Databricks job run API calls for metadata
- **In-memory transaction table (WS-TRNX-TABLE)**: The 51×10 OCCURS array (51 cards × 10 transactions each) is replaced by a grouped DataFrame
- **CBSTM03B subroutine inlined**: The generic file I/O dispatch subroutine (LK-M03B-DD + LK-M03B-OPER interface) is not needed; all I/O is direct Delta table reads in PySpark

### 9.3 Input Delta Tables

| Delta Table | Replaces | Access Pattern (CBSTM03B Operation) |
|------------|---------|-------------------------------------|
| `carddemo.silver.card_xref` | VSAM KSDS XREFFILE (via CBSTM03B, M03B-READ sequential) | Full sequential scan — drives main loop |
| `carddemo.silver.customer` | VSAM KSDS CUSTFILE (via CBSTM03B, M03B-READ-K by CUST-ID) | Random read by `cust_id` |
| `carddemo.silver.account` | VSAM KSDS ACCTFILE (via CBSTM03B, M03B-READ-K by ACCT-ID) | Random read by `acct_id` |
| `carddemo.silver.transaction` | VSAM KSDS TRNXFILE (via CBSTM03B, M03B-READ sequential) | Scan; filter by `tran_card_num` matching XREF card numbers |

### 9.4 Output Delta Tables

| Delta Table | Replaces | Write Mode |
|------------|---------|------------|
| `carddemo.gold.account_statement` | Sequential STMTFILE (DD: STMTFILE, 80 bytes/line) + HTMLFILE (100 bytes/line) | Overwrite by `stmt_year`, `stmt_month` |

### 9.5 Processing Logic

#### Step 1: Read XREFFILE (replaces 1000-XREFFILE-GET-NEXT via CBSTM03B M03B-READ)
```python
# Replace: PERFORM UNTIL END-OF-FILE = 'Y': CALL CBSTM03B (DD='XREFFILE', OPER='R')
# Then: MOVE WS-M03B-FLDT TO CARD-XREF-RECORD
xref_df = spark.read.format("delta").table("carddemo.silver.card_xref")
```

#### Step 2: Customer and Account Lookups (replaces 2000-CUSTFILE-GET + 3000-ACCTFILE-GET)
```python
# Replace: CALL CBSTM03B (DD='CUSTFILE', OPER='K', KEY=XREF-CUST-ID)
# Replace: CALL CBSTM03B (DD='ACCTFILE', OPER='K', KEY=XREF-ACCT-ID)
cust_df = spark.read.format("delta").table("carddemo.silver.customer")
acct_df = spark.read.format("delta").table("carddemo.silver.account")

statements_base = (xref_df
    .join(cust_df, "cust_id", "left")
    .join(acct_df, "acct_id", "left"))
```

#### Step 3: Transaction Lookup (replaces 4000-TRNXFILE-GET / WS-TRNX-TABLE search)
```python
# Replace: WS-TRNX-TABLE (51 cards × 10 transactions) in-memory search
# TRNX-FILE has composite key: FD-TRNXS-ID = FD-TRNX-CARD X(16) + FD-TRNX-ID X(16)
# COBOL pre-loads all transactions into the 2D table; PySpark uses a join
tran_df = spark.read.format("delta").table("carddemo.silver.transaction")

# Note: COBOL limits to 10 transactions per card (WS-TRAN-TBL OCCURS 10 TIMES)
# PySpark has no such limit — processes all transactions per card
# TODO: VERIFY whether the 10-transaction limit is a real business constraint or a demo artifact

statement_transactions = (tran_df
    .join(xref_df.select("card_num"), "tran_card_num", "inner")
    .withColumnRenamed("tran_card_num", "card_num"))
```

#### Step 4: Statement Generation — Plain Text (replaces 5000-CREATE-STATEMENT + 6000-WRITE-TRANS)
```python
# Replace: 5000-CREATE-STATEMENT writes ST-LINE0 through ST-LINE13 (80-byte lines)
# Replace: 6000-WRITE-TRANS writes one transaction line per transaction (ST-LINE14)
# Replace: ST-LINE14A = "Total EXP:" + WS-TOTAL-AMT
# Hardcoded bank identity: 'Bank of XYZ', '410 Terry Ave N', 'Seattle WA 99999'

stmt_text_df = generate_plain_text_statement(statements_base, statement_transactions)
stmt_html_df = generate_html_statement(statements_base, statement_transactions)
```

#### Step 5: Write Statements (replaces WRITE to STMTFILE and HTMLFILE)
```python
stmt_df = stmt_text_df.join(stmt_html_df, ["acct_id", "stmt_year", "stmt_month"])
(stmt_df.write.format("delta")
 .mode("overwrite")
 .option("replaceWhere", f"stmt_year = {stmt_year} AND stmt_month = {stmt_month}")
 .saveAsTable("carddemo.gold.account_statement"))
```

### 9.6 Business Rules

| COBOL Rule | Source | PySpark Implementation |
|-----------|--------|----------------------|
| Two output formats per account (text + HTML) | CBSTM03A Section 9.1 | Two columns in single `account_statement` row |
| WS-TOTAL-AMT: sum all TRNX-AMT values | 4000-TRNXFILE-GET | `SUM(tran_amt) OVER (PARTITION BY card_num)` |
| ST-LINE14A: "Total EXP:" + total | 4000-TRNXFILE-GET | `F.concat(F.lit("Total EXP: "), F.col("total_tran_amt"))` |
| Table capacity: 51 cards × 10 transactions | WS-TRNX-TABLE OCCURS clauses | No artificial limit in PySpark (TODO: VERIFY business rule) |
| Hardcoded bank address in HTML | 5100-WRITE-HTML-HEADER (lines 540-542) | Python constant: `BANK_NAME = "Bank of XYZ"`, `BANK_ADDR = "410 Terry Ave N"`, `BANK_CITY_STATE = "Seattle WA 99999"` |
| PSA/TCB/TIOT walk for DD name listing | CBSTM03A PROCEDURE DIVISION init | Not replicated in cloud; Databricks job run API for metadata |

---

## 10. CBEXPORT — Data Export Pipeline

### 10.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBEXPORT (app/cbl/CBEXPORT.cbl) |
| JCL Job | CBEXPORT.jcl |
| Databricks Job Name | `cbexport_data_export` |
| Function | Export all entity data (Customer/Account/XREF/Transaction/Card) into consolidated 500-byte KSDS export file with type codes C/A/X/T/D |

### 10.2 Input Delta Tables

| Delta Table | Replaces | Program Paragraph |
|------------|---------|------------------|
| `carddemo.silver.customer` | VSAM KSDS CUSTFILE | 2000-EXPORT-CUSTOMERS + 2100-READ-CUSTOMER-RECORD |
| `carddemo.silver.account` | VSAM KSDS ACCTFILE | 3000-EXPORT-ACCOUNTS + 3100-READ-ACCOUNT-RECORD |
| `carddemo.silver.card_xref` | VSAM KSDS XREFFILE | 4000-EXPORT-XREFS + 4100-READ-XREF-RECORD |
| `carddemo.silver.transaction` | VSAM KSDS TRANSACT | 5000-EXPORT-TRANSACTIONS + 5100-READ-TRANSACTION-RECORD |
| `carddemo.silver.card` | VSAM KSDS CARDFILE | 5500-EXPORT-CARDS + 5600-READ-CARD-RECORD |

### 10.3 Output Delta Tables

| Delta Table | Replaces | Write Mode |
|------------|---------|------------|
| `carddemo.bronze.export_raw` | VSAM KSDS EXPFILE (DD: EXPFILE, OUTPUT, 500-byte records) | Overwrite by export_date |

### 10.4 Processing Logic

```python
# Replace: Sequential export of each entity type with type codes C/A/X/T/D
# EXPORT-SEQUENCE-NUM: monotonically increasing across all entity types
# Ordering: C → A → X → T → D (matching COBOL 2000→3000→4000→5000→5500 sequence)

export_ts = F.current_timestamp()
export_date = F.current_date()

# Replaces 1050-GENERATE-TIMESTAMP
branch_id = get_config("export.branch_id", "0001")
region_code = get_config("export.region_code", "NORTH")

customers = spark.read.format("delta").table("carddemo.silver.customer")
accounts = spark.read.format("delta").table("carddemo.silver.account")
xrefs = spark.read.format("delta").table("carddemo.silver.card_xref")
transactions = spark.read.format("delta").table("carddemo.silver.transaction")
cards = spark.read.format("delta").table("carddemo.silver.card")

# Build each entity export (2200-CREATE-CUSTOMER-EXP-REC → 5700-CREATE-CARD-EXPORT-RECORD)
cust_export = customers.withColumn("export_rec_type", F.lit("C"))
acct_export = accounts.withColumn("export_rec_type", F.lit("A"))
xref_export = xrefs.withColumn("export_rec_type", F.lit("X"))
tran_export = transactions.withColumn("export_rec_type", F.lit("T"))
card_export = cards.withColumn("export_rec_type", F.lit("D"))

# Union all types (preserves C→A→X→T→D ordering)
all_export = cust_export.unionByName(acct_export, allowMissingColumns=True) \
    .unionByName(xref_export, allowMissingColumns=True) \
    .unionByName(tran_export, allowMissingColumns=True) \
    .unionByName(card_export, allowMissingColumns=True)

# Assign sequence numbers (replaces WS-SEQUENCE-COUNTER monotonic increment)
all_export_with_seq = all_export.withColumn(
    "export_sequence_num", F.monotonically_increasing_id()
).withColumn("export_timestamp", F.lit(str(export_ts)))
 .withColumn("export_branch_id", F.lit(branch_id))
 .withColumn("export_region_code", F.lit(region_code))
```

### 10.5 Business Rules

| COBOL Rule | Paragraph | PySpark Implementation |
|-----------|-----------|----------------------|
| Record type codes: C/A/X/T/D | 2200/3200/4200/5200/5700 | Hardcoded `withColumn("export_rec_type", F.lit("C"))` etc. |
| BRANCH-ID='0001', REGION='NORTH' hardcoded | All CREATE-*-EXP-REC paragraphs | Configuration parameter with default values |
| Sequence key: monotonically increasing | WS-SEQUENCE-COUNTER | `F.monotonically_increasing_id()` |
| Single timestamp for entire export | 1050-GENERATE-TIMESTAMP | `F.lit(datetime.now().isoformat())` set once |
| Export order: C → A → X → T → D | 0000-MAIN-PROCESSING call sequence | `unionByName` in correct order |

---

## 11. CBIMPORT — Data Import Pipeline

### 11.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBIMPORT (app/cbl/CBIMPORT.cbl) |
| JCL Job | CBIMPORT.jcl |
| Databricks Job Name | `cbimport_data_import` |
| Function | Reverse of CBEXPORT: reads consolidated export file; splits by type code into 5 entity output files; writes unknowns to error file |

### 11.2 Input/Output

| | Table | COBOL DD Name |
|-|-------|--------------|
| Input | `carddemo.bronze.export_raw` | EXPFILE |
| Output | `carddemo.silver.customer` | CUSTOUT |
| Output | `carddemo.silver.account` | ACCTOUT |
| Output | `carddemo.silver.card_xref` | XREFOUT |
| Output | `carddemo.silver.transaction` | TRNXOUT |
| Output | `carddemo.silver.card` | CARDOUT |
| Output | `carddemo.migration_ctrl.error_log` | ERROUT (132-byte error records) |

### 11.3 Processing Logic

```python
# Replace: 2200-PROCESS-RECORD-BY-TYPE: EVALUATE EXPORT-REC-TYPE WHEN 'C'/'A'/'X'/'T'/'D'/OTHER
export_df = spark.read.format("delta").table("carddemo.bronze.export_raw")

# Dispatch by type code (replaces COBOL EVALUATE)
customer_df = export_df.filter(F.col("export_rec_type") == "C")
account_df = export_df.filter(F.col("export_rec_type") == "A")
xref_df = export_df.filter(F.col("export_rec_type") == "X")
transaction_df = export_df.filter(F.col("export_rec_type") == "T")
card_df = export_df.filter(F.col("export_rec_type") == "D")
unknown_df = export_df.filter(~F.col("export_rec_type").isin("C", "A", "X", "T", "D"))

# Write unknowns to error log (2700-PROCESS-UNKNOWN-RECORD)
unknown_errors = unknown_df.withColumn("error_type", F.lit("UNKNOWN_RECORD_TYPE"))
unknown_errors.write.format("delta").mode("append").saveAsTable("carddemo.migration_ctrl.error_log")

# Note: 3000-VALIDATE-IMPORT is a stub in COBOL (only DISPLAY statements)
# PySpark adds actual row count reconciliation as a post-import check
```

### 11.4 Business Rules

| COBOL Rule | Paragraph | PySpark Implementation |
|-----------|-----------|----------------------|
| Type dispatch: C/A/X/T/D | 2200-PROCESS-RECORD-BY-TYPE | `filter(export_rec_type == "X")` per type |
| Unknown types → error file (no abend) | 2700-PROCESS-UNKNOWN-RECORD | Write to `migration_ctrl.error_log` with `error_type = 'UNKNOWN_RECORD_TYPE'` |
| ERROR-OUTPUT write failure → no abend | CBIMPORT Section 8 | Error on error_log write is caught and logged to stderr only |
| 3000-VALIDATE-IMPORT is a stub | CBIMPORT Section 9.3 | Add actual validation (row counts, referential integrity) — improvement on original COBOL |
| 1-to-1 field mapping (no transform) | 2300-2650 paragraphs | Direct column rename without transformation |

---

## 12. CBPAUP0C — Authorization Purge Pipeline

### 12.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CBPAUP0C (cbl/CBPAUP0C.cbl) |
| JCL Job | CBPAUP0J.jcl |
| Databricks Job Name | `cbpaup0c_auth_purge` |
| IMS Type | IMS BMP (Batch Message Processing) |
| Function | Delete expired pending authorizations from IMS. Scans PAUTSUM0 root segments + PAUTDTL1 children; deletes children exceeding expiry threshold; deletes parent when approved count reaches zero |

### 12.2 Parameters (replaces SYSIN PRM-INFO)

| Parameter | COBOL Field | Default | Description |
|-----------|------------|---------|-------------|
| `expiry_days` | P-EXPIRY-DAYS 9(02) | 5 | Days before authorization expires |
| `checkpoint_freq` | P-CHKP-FREQ X(05) | 5 | Checkpoint every N summary records (IMS CHKP → Delta table commit) |
| `debug_enabled` | P-DEBUG-FLAG X(01) | 'N' | Enable verbose logging |

### 12.3 Input/Output Delta Tables

| Table | Access | Replaces |
|-------|--------|---------|
| `carddemo.silver.auth_summary` | Read + Delete | IMS PAUTSUM0 (GN = sequential scan) |
| `carddemo.silver.auth_detail` | Read + Delete | IMS PAUTDTL1 (GNP = get-next-within-parent child scan) |

### 12.4 Processing Logic

#### Step 1: Compute Expiry (replaces 4000-CHECK-IF-EXPIRED)
```python
# Replace: 4000-CHECK-IF-EXPIRED:
#   COMPUTE WS-AUTH-DATE = 99999 - PA-AUTH-DATE-9C
#   COMPUTE WS-DAY-DIFF = CURRENT-YYDDD - WS-AUTH-DATE
#   IF WS-DAY-DIFF >= WS-EXPIRY-DAYS: QUALIFIED-FOR-DELETE

# In Silver, pa_auth_date is pre-computed from pa_auth_date_9c:
#   pa_auth_date = convert yyddd to actual date
# Expiry logic:
current_yyddd = get_current_julian_yyddd()  # Equivalent to ACCEPT CURRENT-YYDDD FROM DAY
expiry_days = int(get_config("expiry_days", "5"))

detail_df = spark.read.format("delta").table("carddemo.silver.auth_detail")

expired_details = detail_df.withColumn(
    "day_diff",
    # Replicate: WS-DAY-DIFF = CURRENT-YYDDD - WS-AUTH-DATE
    # WS-AUTH-DATE = 99999 - PA-AUTH-DATE-9C (inverted Julian)
    F.lit(current_yyddd) - (F.lit(99999) - F.col("pa_auth_date_9c"))
).filter(F.col("day_diff") >= F.lit(expiry_days))
```

#### Step 2: Adjust Summary Counts (replaces count adjustments in 4000-CHECK-IF-EXPIRED)
```python
# Replace: Summary count adjustments (lines 287-293):
#   Approved record (resp_code='00'): SUBTRACT 1 FROM PA-APPROVED-AUTH-CNT; SUBTRACT PA-APPROVED-AMT
#   Declined record: SUBTRACT 1 FROM PA-DECLINED-AUTH-CNT; SUBTRACT PA-TRANSACTION-AMT

count_adjustments = (expired_details
    .groupBy("pa_acct_id")
    .agg(
        F.sum(F.when(F.col("pa_auth_resp_code") == "00", 1).otherwise(0)).alias("approved_cnt_adj"),
        F.sum(F.when(F.col("pa_auth_resp_code") == "00",
                     F.col("pa_transaction_amt")).otherwise(F.lit(0))).alias("approved_amt_adj"),
        F.sum(F.when(F.col("pa_auth_resp_code") != "00", 1).otherwise(0)).alias("declined_cnt_adj"),
        F.sum(F.when(F.col("pa_auth_resp_code") != "00",
                     F.col("pa_transaction_amt")).otherwise(F.lit(0))).alias("declined_amt_adj")
    )
)
```

#### Step 3: Delete Expired Detail Records (replaces 5000-DELETE-AUTH-DTL)
```python
# Replace: EXEC DLI DLET PAUTDTL1
DeltaTable.forName(spark, "carddemo.silver.auth_detail").delete(
    F.col("auth_detail_seq").isin(
        expired_details.select("auth_detail_seq").collect()  # Use join for large datasets
    )
)
```

#### Step 4: Determine Summary Deletions (replaces 6000-DELETE-AUTH-SUMMARY condition check)
```python
# Replace: IF PA-APPROVED-AUTH-CNT <= 0 AND PA-APPROVED-AUTH-CNT <= 0 → DELETE summary
# NOTE: COBOL source has a defect: second predicate checks PA-APPROVED-AUTH-CNT twice
# instead of checking PA-DECLINED-AUTH-CNT. We replicate the defect exactly.
# TODO: VERIFY whether this is intentional business logic or a code defect

summary_df = spark.read.format("delta").table("carddemo.silver.auth_summary")

updated_summary = summary_df.join(count_adjustments, "pa_acct_id", "left").withColumn(
    "new_approved_cnt",
    F.col("pa_approved_auth_cnt") - F.coalesce(F.col("approved_cnt_adj"), F.lit(0))
)

# Replicate COBOL defect: both predicates check approved_cnt (not declined_cnt)
summaries_to_delete = updated_summary.filter(
    (F.col("new_approved_cnt") <= 0) &
    (F.col("new_approved_cnt") <= 0)  # INTENTIONAL REPLICATION OF COBOL DEFECT (line 170-171)
)
```

#### Step 5: Delete Qualifying Summary Records (replaces 6000-DELETE-AUTH-SUMMARY)
```python
# Replace: EXEC DLI DLET PAUTSUM0
DeltaTable.forName(spark, "carddemo.silver.auth_summary").delete(
    F.col("pa_acct_id").isin(summaries_to_delete.select("pa_acct_id").rdd.flatMap(lambda x: x).collect())
)
```

#### Step 6: Write Audit Log (replaces DISPLAY statistics + IMS CHKP)
```python
# Replace: WS-NO-SUMRY-READ, WS-NO-SUMRY-DELETED, WS-NO-DTL-READ, WS-NO-DTL-DELETED
# Replace: IMS CHKP (checkpoint replaced by Delta transaction commit boundary)
audit_df = spark.createDataFrame([{
    "purge_run_id": run_id,
    "purge_date": batch_date,
    "expiry_days_used": expiry_days,
    "total_summaries_read": summary_df.count(),
    "total_summaries_deleted": summaries_to_delete.count(),
    "total_details_read": detail_df.count(),
    "total_details_deleted": expired_details.count()
}])
audit_df.write.format("delta").mode("append").saveAsTable("carddemo.gold.auth_purge_audit")
```

### 12.5 Business Rules

| COBOL Rule | Paragraph | PySpark Implementation |
|-----------|-----------|----------------------|
| Expiry formula: `WS-DAY-DIFF = CURRENT-YYDDD - (99999 - PA-AUTH-DATE-9C)` | 4000-CHECK-IF-EXPIRED | Replicated exactly with Python datetime/Julian conversion |
| Delete detail when `day_diff >= expiry_days` | 4000-CHECK-IF-EXPIRED + 5000-DELETE-AUTH-DTL | Delta DELETE with exact same condition |
| Delete summary when `approved_cnt <= 0 AND approved_cnt <= 0` | 6000-DELETE-AUTH-SUMMARY | **Defect replicated exactly** — both conditions check approved_cnt |
| Checkpoint after every P-CHKP-FREQ summaries | 9000-TAKE-CHECKPOINT | Delta table commit after every `checkpoint_freq` batch |
| Any IMS error → RC=16 (no recovery) | 9999-ABEND | `raise RuntimeError(f"IMS equivalent error: {error}")` + `sys.exit(16)` |

---

## 13. PAUDBUNL — Authorization DB Unload Pipeline

### 13.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | PAUDBUNL (cbl/PAUDBUNL.CBL) |
| JCL Job | UNLDPADB.JCL |
| Databricks Job Name | `paudbunl_auth_unload` |
| Function | Unload IMS DBPAUTP0 to two sequential output files (root 100-byte, child 206-byte with parent key) |

### 13.2 Processing Logic

```python
# Replace: CALL 'CBLTDLI' USING FUNC-GN PAUTBPCB PENDING-AUTH-SUMMARY ROOT-UNQUAL-SSA
# Replace: CALL 'CBLTDLI' USING FUNC-GNP PAUTBPCB PENDING-AUTH-DETAILS CHILD-UNQUAL-SSA
# Replace: MOVE PENDING-AUTH-SUMMARY TO OPFIL1-REC; WRITE OPFIL1-REC (OPFILE1, 100 bytes)
# Replace: MOVE PENDING-AUTH-DETAILS TO CHILD-SEG-REC; WRITE OPFIL2-REC (OPFILE2, 206 bytes)

# Filter: PA-ACCT-ID IS NUMERIC (replicated exactly)
summary_df = (spark.read.format("delta")
    .table("carddemo.silver.auth_summary")
    .filter(F.col("pa_acct_id").cast("string").rlike("^[0-9]+$")))

detail_df = spark.read.format("delta").table("carddemo.silver.auth_detail")

# Write root records to Bronze output (replaces OPFILE1, 100-byte QSAM records)
summary_df.write.format("delta").mode("overwrite").saveAsTable("carddemo.bronze.auth_root_file")

# Write child records with parent key (replaces OPFILE2, 206-byte records with ROOT-SEG-KEY)
detail_df.withColumn("root_seg_key", F.col("pa_acct_id")) \
    .write.format("delta").mode("overwrite").saveAsTable("carddemo.bronze.auth_child_file")
```

---

## 14. PAUDBLOD — Authorization DB Load Pipeline

### 14.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | PAUDBLOD (cbl/PAUDBLOD.CBL) |
| JCL Job | LOADPADB.JCL |
| Databricks Job Name | `paudblod_auth_load` |
| Function | Load IMS DBPAUTP0 from flat files produced by PAUDBUNL; inverse of PAUDBUNL |

### 14.2 Processing Logic

```python
# Replace: 2000-READ-ROOT-SEG-FILE: READ INFILE1 + CALL 'CBLTDLI' FUNC-ISRT (root)
# Replace: 3000-READ-CHILD-SEG-FILE: READ INFILE2 + GU parent + ISRT child
# Duplicate key ('II') tolerance: continue processing without error

root_df = spark.read.format("delta").table("carddemo.bronze.auth_root_file")
child_df = spark.read.format("delta").table("carddemo.bronze.auth_child_file")

# Validate root_seg_key is numeric (replicate PAUDBLOD non-numeric skip logic)
valid_children = child_df.filter(F.col("root_seg_key").cast("long").isNotNull())

# Load roots first (replaces 2000 loop): MERGE with duplicate key tolerance
DeltaTable.forName(spark, "carddemo.silver.auth_summary").alias("t").merge(
    root_df.alias("s"), "t.pa_acct_id = s.pa_acct_id"
).whenMatchedUpdate("true", {"pa_approved_auth_cnt": "s.pa_approved_auth_cnt"})  # Replaces 'II' tolerance
 .whenNotMatchedInsertAll()
 .execute()

# Load children second (replaces 3000 loop + GU + ISRT)
DeltaTable.forName(spark, "carddemo.silver.auth_detail").alias("t").merge(
    valid_children.alias("s"), "t.auth_detail_seq = s.auth_detail_seq"
).whenNotMatchedInsertAll()
 .execute()
```

---

## 15. DBUNLDGS — GSAM Unload Pipeline

### 15.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | DBUNLDGS (cbl/DBUNLDGS.CBL) |
| JCL Job | UNLDGSAM.JCL |
| Databricks Job Name | `dbunldgs_gsam_unload` |
| Function | Functional equivalent of PAUDBUNL using GSAM output instead of QSAM; writes to GSAM PCBs PASFLPCB/PADFLPCB |

### 15.2 GSAM Replacement Strategy

GSAM (Generalized Sequential Access Method) is an IMS-specific sequential data storage method. In the cloud migration, GSAM output is replaced by Delta table writes, identical to PAUDBUNL.

```python
# Replace: CALL 'CBLTDLI' USING FUNC-ISRT PASFLPCB PENDING-AUTH-SUMMARY (GSAM root write)
# Replace: CALL 'CBLTDLI' USING FUNC-ISRT PADFLPCB PENDING-AUTH-DETAILS (GSAM child write)
# Note: OPFILE1/OPFILE2 WRITE statements in DBUNLDGS are commented out — only GSAM ISRT is active

# Migration: GSAM files (PASFILOP/PADFILOP) → Bronze Delta tables
summary_df = (spark.read.format("delta")
    .table("carddemo.silver.auth_summary")
    .filter(F.col("pa_acct_id").cast("string").rlike("^[0-9]+$")))  # PA-ACCT-ID IS NUMERIC

summary_df.write.format("delta").mode("overwrite").saveAsTable("carddemo.bronze.auth_gsam_root")

detail_df = spark.read.format("delta").table("carddemo.silver.auth_detail")
detail_df.write.format("delta").mode("overwrite").saveAsTable("carddemo.bronze.auth_gsam_child")
```

---

## 16. COBTUPDT — Transaction Type Maintenance Pipeline

### 16.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | COBTUPDT (app/app-transaction-type-db2/cbl/COBTUPDT.cbl) |
| JCL Job | MNTTRDB2.jcl |
| Databricks Job Name | `cobtupdt_tran_type_maint` |
| Function | Batch maintenance of `CARDDEMO.TRANSACTION_TYPE` (DB2) via input file. Operations: A=Add, U=Update, D=Delete, *=Comment |

### 16.2 Input/Output

- **Input:** `carddemo.bronze.tran_type_input` (replaces sequential INPFILE, 53-byte records)
- **Output:** `carddemo.reference.tran_type` (replaces DB2 table `CARDDEMO.TRANSACTION_TYPE`)

### 16.3 Input Record Layout

| Position | Field | COBOL Field | Length | Values |
|---------|-------|------------|--------|--------|
| 1 | Operation type | INPUT-REC-TYPE PIC X(1) | 1 | A=Add, U=Update, D=Delete, *=Comment |
| 2-3 | Type code | INPUT-REC-NUMBER PIC X(2) | 2 | 01-99 |
| 4-53 | Description | INPUT-REC-DESC PIC X(50) | 50 | Free text |

### 16.4 Processing Logic

```python
# Replace: 1003-TREAT-RECORD: EVALUATE INPUT-REC-TYPE WHEN 'A'/'U'/'D'/'*'/OTHER

input_df = spark.read.format("delta").table("carddemo.bronze.tran_type_input")

# Sort by sequence to preserve COBOL file processing order (critical for A/U/D ordering)
input_df = input_df.orderBy("_meta_batch_seq")

# Separate by operation type (replaces COBOL EVALUATE on INPUT-REC-TYPE)
inserts = input_df.filter(F.col("input_rec_type") == "A")  # 10031-INSERT-DB
updates = input_df.filter(F.col("input_rec_type") == "U")  # 10032-UPDATE-DB
deletes = input_df.filter(F.col("input_rec_type") == "D")  # 10033-DELETE-DB
comments = input_df.filter(F.col("input_rec_type") == "*")  # No-op + log
unknowns = input_df.filter(~F.col("input_rec_type").isin("A", "U", "D", "*"))

# Handle unknowns as errors (replaces 9999-ABEND with RC=4, no STOP RUN)
if unknowns.count() > 0:
    log_error(unknowns, "INVALID_RECORD_TYPE", return_code=4)
    # NOTE: COBOL 9999-ABEND does NOT stop processing — it sets RC=4 and continues
    # PySpark pipeline continues with remaining records (matching COBOL behavior)

# Process INSERTs (replaces 10031-INSERT-DB)
# SQL: INSERT INTO TRANSACTION_TYPE (TR_TYPE, TR_DESCRIPTION) VALUES (INPUT-REC-NUMBER, INPUT-REC-DESC)
DeltaTable.forName(spark, "carddemo.reference.tran_type").alias("t").merge(
    inserts.select(
        F.col("input_rec_number").alias("tr_type"),
        F.col("input_rec_desc").alias("tr_description")
    ).alias("s"),
    "t.tr_type = s.tr_type"
).whenNotMatchedInsertAll()  # Duplicate key → error (SQLCODE < 0 equivalent)
 .execute()

# Process UPDATEs (replaces 10032-UPDATE-DB)
# SQL: UPDATE TRANSACTION_TYPE SET TR_DESCRIPTION = INPUT-REC-DESC WHERE TR_TYPE = INPUT-REC-NUMBER
DeltaTable.forName(spark, "carddemo.reference.tran_type").alias("t").merge(
    updates.select(
        F.col("input_rec_number").alias("tr_type"),
        F.col("input_rec_desc").alias("tr_description")
    ).alias("s"),
    "t.tr_type = s.tr_type"
).whenMatchedUpdate(set={"tr_description": "s.tr_description"})
 .execute()
# Note: SQLCODE=+100 equivalent (no rows matched) → log error + RC=4, continue

# Process DELETEs (replaces 10033-DELETE-DB)
# SQL: DELETE FROM TRANSACTION_TYPE WHERE TR_TYPE = INPUT-REC-NUMBER
delete_keys = deletes.select(F.col("input_rec_number").alias("tr_type"))
DeltaTable.forName(spark, "carddemo.reference.tran_type").delete(
    F.col("tr_type").isin([row.tr_type for row in delete_keys.collect()])
)
```

### 16.5 Business Rules

| COBOL Rule | Paragraph | PySpark Implementation |
|-----------|-----------|----------------------|
| 'A': Unconditional INSERT; duplicate → ABEND RC=4, continue | 10031-INSERT-DB | MERGE; log duplicate as error; continue |
| 'U': UPDATE by TR_TYPE; not found → ABEND RC=4, continue | 10032-UPDATE-DB | MERGE; log no-match as error; continue |
| 'D': DELETE by TR_TYPE; not found → ABEND RC=4, continue | 10033-DELETE-DB | DELETE; log no-match as error; continue |
| '*': Comment line → DISPLAY + skip | 1003-TREAT-RECORD WHEN '*' | Log to pipeline_metrics, skip |
| No SQL COMMIT in COBOL batch | COBTUPDT Section business rules #6 | Delta operations auto-commit; all within single Delta transaction |
| 9999-ABEND: sets RC=4, does NOT stop processing | 9999-ABEND paragraph | Pipeline logs error + continues processing next record |
| Processing order: COBOL processes file sequentially | 1002-READ-RECORDS + PERFORM UNTIL | `orderBy("_meta_batch_seq")` preserves file order |

### 16.6 Return Code

COBTUPDT sets `RETURN-CODE=4` on any error but does not stop. The PySpark pipeline:
- Logs all errors to `carddemo.migration_ctrl.error_log`
- Sets `return_code=4` in pipeline_metrics when any error occurs
- Continues processing remaining records

---

## 17. COACCT01 — Account Inquiry Service

### 17.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | COACCT01 (app/app-vsam-mq/cbl/COACCT01.cbl) |
| CICS Transaction | CDRA |
| Databricks Job Name | `coacct01_account_inquiry` (structured streaming job) |
| Function | Receives MQ account inquiry requests; reads ACCTDAT VSAM; returns account details via MQ reply |
| Migration Approach | Replace IBM MQ trigger with Kafka/Event Hub + Structured Streaming |

### 17.2 MQ → Streaming Migration

| COACCT01 Component | Databricks Replacement |
|-------------------|----------------------|
| IBM MQ input queue | Apache Kafka topic / Azure Event Hub |
| EXEC CICS RETRIEVE (trigger message) | Kafka consumer / Event Hub consumer |
| EXEC CICS READ DATASET(ACCTDAT) | Delta table lookup: `carddemo.silver.account` |
| MQPUT reply to output queue | Kafka producer to reply topic |
| ACTION(BACKOUT) on failure | Kafka offset commit only on success |

### 17.3 Request Validation (replaces 4000-PROCESS-REQUEST-REPLY)

```python
# Replace: WS-FUNC = 'INQA' AND WS-KEY > 0 (valid request check)
# WS-KEY is the account number from MQ message
def process_account_inquiry(request_msg):
    """
    Replaces: COACCT01 4000-PROCESS-REQUEST-REPLY
    Validates: WS-FUNC == 'INQA' and WS-KEY > 0
    Note: ZIP code NOT included in reply (replicates COBOL defect documented in overall spec)
    """
    func_code = request_msg["function"]  # WS-FUNC
    acct_key = request_msg["account_key"]  # WS-KEY

    if func_code != "INQA":
        return error_reply("Invalid function code")
    if acct_key <= 0:
        return error_reply("Invalid account key")

    # Read account (replaces EXEC CICS READ DATASET(ACCTDAT) INTO(ACCOUNT-DATA))
    acct = lookup_account_from_delta(acct_key)

    # NOTE: ZIP code intentionally excluded from reply
    # Original COBOL reads ACCT-ADDR-ZIP but does not include it in MQ reply message
    # This replicates the documented defect (overall-system-specification.md Section 12)
    return build_reply(acct, include_zip=False)
```

---

## 18. CODATE01 — Date Service

### 18.1 Overview

| Attribute | Value |
|-----------|-------|
| Source Program | CODATE01 (app/app-vsam-mq/cbl/CODATE01.cbl) |
| CICS Transaction | CDRD |
| Databricks Job Name | `codate01_date_service` (scheduled micro-batch or streaming) |
| Function | Receives any MQ request; returns current CICS system date/time via MQ reply |

### 18.2 Processing Logic

```python
# Replace: EXEC CICS ASKTIME / FORMATTIME (get current date/time)
# No VSAM file I/O (unlike COACCT01)
# Known issue: No RESP/RESP2 checking on ASKTIME/FORMATTIME (replicate as-is)

def process_date_inquiry(request_msg):
    """
    Replaces: CODATE01 4000-PROCESS-REQUEST-REPLY
    Any message triggers a date/time reply (no validation of message content)
    Replicates: EXEC CICS ASKTIME ABSTIME / FORMATTIME with YYYYMMDD, HHMMSS
    Note: No error handling on ASKTIME (replicates COBOL behavior — overall spec Section 12)
    """
    from datetime import datetime
    now = datetime.now()
    return {
        "current_date": now.strftime("%Y%m%d"),  # YYYYMMDD format from FORMATTIME
        "current_time": now.strftime("%H%M%S"),  # HHMMSS format from FORMATTIME
        "timestamp": now.isoformat()
    }
```

### 18.3 Unused Variables (from spec)

The following COBOL working storage variables in CODATE01 are declared but never used — **do not create corresponding Python variables**:
- `LIT-ACCTFILENAME` — account file name literal (dead code)
- `WS-RESP-CD` — CICS response code (never checked)
- `WS-REAS-CD` — CICS reason code (never checked)
