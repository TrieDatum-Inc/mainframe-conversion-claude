# CardDemo Databricks Workflow Orchestration Specification
## JCL Job Stream → Databricks Workflow Mapping

**Document Version:** 1.0  
**Date:** 2026-04-06  
**Total JCL Jobs Covered:** 46

---

## Table of Contents

1. [Orchestration Design Principles](#1-orchestration-design-principles)
2. [Daily Batch Cycle Workflow](#2-daily-batch-cycle-workflow)
3. [Monthly Statement Cycle Workflow](#3-monthly-statement-cycle-workflow)
4. [Data Exchange Workflows](#4-data-exchange-workflows)
5. [Authorization Database Maintenance Workflow](#5-authorization-database-maintenance-workflow)
6. [Transaction Type Maintenance Workflow](#6-transaction-type-maintenance-workflow)
7. [On-Demand Reporting Workflows](#7-on-demand-reporting-workflows)
8. [MQ Service Workflows (Streaming)](#8-mq-service-workflows-streaming)
9. [Complete JCL-to-Workflow Mapping Table](#9-complete-jcl-to-workflow-mapping-table)
10. [Cluster Sizing Recommendations](#10-cluster-sizing-recommendations)
11. [Retry and Notification Policies](#11-retry-and-notification-policies)
12. [Parameterization Reference](#12-parameterization-reference)

---

## 1. Orchestration Design Principles

### 1.1 JCL Step → Databricks Task Translation

| JCL Concept | Databricks Equivalent |
|------------|----------------------|
| JCL JOB statement | Databricks Workflow |
| JCL EXEC STEP (PGM=COBOLPGM) | Databricks Workflow Task (PySpark notebook or Python script) |
| JCL EXEC STEP (PGM=SORT) | Databricks Task with `orderBy()` in PySpark |
| JCL EXEC STEP (PGM=IEFBR14) | Removed (Delta table DDL handles dataset management) |
| JCL EXEC STEP (PGM=DFSRRC00, BMP) | Databricks Task (IMS replaced by Delta table operations) |
| JCL COND parameter | Task `run_if` condition + `depends_on` |
| JCL IF/THEN/ELSE/ENDIF | Databricks conditional tasks with `run_if` expressions |
| JCL PARM='value' | Databricks job parameters (key-value pairs) |
| JCL symbolic &PARAM | Databricks widget: `dbutils.widgets.text("param", "default")` |
| JCL DD name to dataset | Delta table path in pipeline_config.py |
| JCL MSGCLASS/SYSOUT | Databricks job run logs (stdout capture) |
| JCL REGION=0M | Cluster memory configuration |
| JCL CLASS=A | Cluster queue/pool assignment |
| JCL RESTART=stepname | Databricks task-level retry from specific task |

### 1.2 COND Parameter Translation

The following table translates common JCL `COND` parameter patterns to Databricks Workflow conditions:

| JCL COND Syntax | Meaning | Databricks run_if |
|----------------|---------|-----------------|
| `COND=(0,EQ)` | Run only if previous RC = 0 | `"{{tasks.prev_task.values.return_code}} == 0"` |
| `COND=(4,GE)` | Run only if all previous RC < 4 | `run_if: "ALL_SUCCESS"` (maps RC=0→success) |
| `COND=(4,LT)` | Skip if RC < 4 (i.e., run if any RC >= 4) | `run_if: "AT_LEAST_ONE_FAILED"` |
| `COND=EVEN` | Run even if previous step failed | `run_if: "ALL_DONE"` |
| `COND=ONLY` | Run only if previous step failed | `run_if: "AT_LEAST_ONE_FAILED"` |
| No COND | Always run | `run_if: "ALL_SUCCESS"` (default with `depends_on`) |

### 1.3 Return Code Semantics

Databricks tasks use Spark exit codes to communicate COBOL RETURN-CODE values:

| COBOL RETURN-CODE | Databricks Task Exit Code | Workflow Effect |
|------------------|--------------------------|-----------------|
| 0 (success) | 0 (normal exit) | Task succeeds |
| 4 (warning, e.g., rejects in CBTRN02C) | Custom: task succeeds but sets parameter `return_code=4` | Downstream tasks can check this parameter |
| 8+ (error) | Non-zero exit | Task fails; downstream tasks blocked |
| 16 (CBPAUP0C fatal) | Non-zero exit | Task fails; alert triggered |

---

## 2. Daily Batch Cycle Workflow

### 2.1 Workflow Definition

**Workflow Name:** `carddemo_daily_batch_cycle`  
**Schedule:** Nightly, configurable (e.g., `0 1 * * *` — 1:00 AM UTC)  
**Cluster:** Job cluster, auto-terminated  
**Tags:** `cycle=daily`, `environment=prod`, `migrated_from=JCL`

### 2.2 JCL Job Stream Being Replaced

```
Original Daily JCL Sequence:
  1. CLOSEFIL.jcl        (close CICS files for batch window)
  2. TRANBKP.jcl         (backup transaction file)
  3. COMBTRAN.jcl        (combine daily transactions into DALYTRAN)
  4. POSTTRAN.jcl        (verify + post daily transactions; CBTRN01C + CBTRN02C)
  5. INTCALC.jcl         (calculate interest; CBACT04C)
  6. DALYREJS.jcl        (process daily rejects)
  7. CBPAUP0J.jcl        (purge expired authorizations; CBPAUP0C)
  8. OPENFIL.jcl         (re-open CICS files)
```

### 2.3 Workflow YAML Definition

```yaml
name: carddemo_daily_batch_cycle
schedule:
  quartz_cron_expression: "0 0 1 * * ?"  # 1:00 AM UTC nightly
  timezone_id: "UTC"

tasks:
  - task_key: stop_streaming_services
    description: "Replaces CLOSEFIL.jcl — quiesce streaming jobs before batch window"
    job_cluster_key: daily_small_cluster
    notebook_task:
      notebook_path: /pipelines/admin/stop_streaming_services
    run_if: "ALL_SUCCESS"
    max_retries: 1

  - task_key: backup_transaction_delta
    description: "Replaces TRANBKP.jcl — Delta table snapshot/clone"
    depends_on:
      - task_key: stop_streaming_services
    notebook_task:
      notebook_path: /pipelines/admin/backup_transaction_delta
      base_parameters:
        backup_date: "{{start_time | date: '%Y-%m-%d'}}"
    run_if: "ALL_SUCCESS"
    max_retries: 2

  - task_key: combine_daily_transactions
    description: "Replaces COMBTRAN.jcl — merge daily transaction input files into bronze.daily_transactions"
    depends_on:
      - task_key: backup_transaction_delta
    notebook_task:
      notebook_path: /pipelines/bronze/combine_daily_transactions
      base_parameters:
        batch_date: "{{start_time | date: '%Y-%m-%d'}}"
    run_if: "ALL_SUCCESS"
    max_retries: 2

  - task_key: cbtrn01c_verify_transactions
    description: "Replaces POSTTRAN.jcl step 1 (CBTRN01C) — transaction verification"
    depends_on:
      - task_key: combine_daily_transactions
    notebook_task:
      notebook_path: /pipelines/cbtrn01c_tran_verify
      base_parameters:
        batch_date: "{{start_time | date: '%Y-%m-%d'}}"
    run_if: "ALL_SUCCESS"
    max_retries: 1

  - task_key: cbtrn02c_post_transactions
    description: "Replaces POSTTRAN.jcl step 2 (CBTRN02C) — daily transaction posting; RC=4 if rejects"
    depends_on:
      - task_key: cbtrn01c_verify_transactions
    notebook_task:
      notebook_path: /pipelines/cbtrn02c_tran_posting
      base_parameters:
        batch_date: "{{start_time | date: '%Y-%m-%d'}}"
    run_if: "ALL_SUCCESS"
    max_retries: 1
    # Note: This task may succeed with return_code=4 (rejects exist)
    # Downstream tasks check the return_code parameter, not task success/failure

  - task_key: cbact04c_calculate_interest
    description: "Replaces INTCALC.jcl (CBACT04C) — monthly interest calculation"
    depends_on:
      - task_key: cbtrn02c_post_transactions
    notebook_task:
      notebook_path: /pipelines/cbact04c_interest_calc
      base_parameters:
        run_date: "{{start_time | date: '%Y-%m-%d'}}"
    run_if: "ALL_SUCCESS"
    max_retries: 2

  - task_key: process_daily_rejects
    description: "Replaces DALYREJS.jcl — process and report on rejected transactions"
    depends_on:
      - task_key: cbtrn02c_post_transactions
    notebook_task:
      notebook_path: /pipelines/process_daily_rejects
      base_parameters:
        batch_date: "{{start_time | date: '%Y-%m-%d'}}"
    run_if: "ALL_DONE"  # Runs whether cbtrn02c had rejects (RC=4) or not
    max_retries: 1

  - task_key: cbpaup0c_purge_authorizations
    description: "Replaces CBPAUP0J.jcl (CBPAUP0C IMS BMP) — purge expired pending authorizations"
    depends_on:
      - task_key: cbtrn02c_post_transactions
    notebook_task:
      notebook_path: /pipelines/cbpaup0c_auth_purge
      base_parameters:
        expiry_days: "5"      # P-EXPIRY-DAYS default
        checkpoint_freq: "5"  # P-CHKP-FREQ default
        debug_enabled: "false" # P-DEBUG-FLAG default
    run_if: "ALL_DONE"
    max_retries: 2

  - task_key: resume_streaming_services
    description: "Replaces OPENFIL.jcl — resume streaming jobs after batch window"
    depends_on:
      - task_key: cbact04c_calculate_interest
      - task_key: process_daily_rejects
      - task_key: cbpaup0c_purge_authorizations
    notebook_task:
      notebook_path: /pipelines/admin/resume_streaming_services
    run_if: "ALL_DONE"  # Always resume services regardless of batch outcome
    max_retries: 3

  - task_key: notify_batch_completion
    description: "Send daily batch completion notification with statistics"
    depends_on:
      - task_key: resume_streaming_services
    python_wheel_task:
      package_name: carddemo_notifications
      entry_point: send_batch_completion_email
    run_if: "ALL_DONE"

job_clusters:
  - job_cluster_key: daily_small_cluster
    new_cluster:
      spark_version: "14.3.x-scala2.12"
      node_type_id: "m5.xlarge"
      autoscale:
        min_workers: 2
        max_workers: 8
      spark_conf:
        spark.sql.extensions: "io.delta.sql.DeltaSparkSessionExtension"
        spark.sql.catalog.spark_catalog: "org.apache.spark.sql.delta.catalog.DeltaCatalog"

notification_settings:
  no_alert_for_skipped_runs: false
  email_notifications:
    on_failure:
      - batch-ops@carddemo.internal
    on_success:
      - batch-summary@carddemo.internal
```

### 2.4 Task Dependency Diagram

```
stop_streaming_services
        │
        ▼
backup_transaction_delta
        │
        ▼
combine_daily_transactions
        │
        ▼
cbtrn01c_verify_transactions
        │
        ▼
cbtrn02c_post_transactions
       / \ \
      /   \ \
     ▼    ▼  ▼
interest rejects purge_auth
  calc          
     \    |   /
      \   |  /
       ▼  ▼  ▼
  resume_streaming_services
              │
              ▼
  notify_batch_completion
```

---

## 3. Monthly Statement Cycle Workflow

### 3.1 Workflow Definition

**Workflow Name:** `carddemo_monthly_statement_cycle`  
**Schedule:** Monthly, 1st of each month at 2:00 AM UTC (`0 0 2 1 * ?`)  
**Cluster:** Job cluster (larger — statement generation is I/O intensive)

### 3.2 JCL Job Stream Being Replaced

```
Original Monthly JCL Sequence:
  1. CREASTMT.JCL (step 1: CBSTM03A reads files, generates statements via CBSTM03B)
  2. CREASTMT.JCL (step 2: CBSTM03B called as subroutine by CBSTM03A)
  3. TXT2PDF1.JCL (convert STMTFILE text statements to PDF)
  4. TRANREPT.jcl (generate transaction detail reports with CBTRN02C logic)
  5. PRTCATBL.jcl (print catalog of report outputs)
```

### 3.3 Workflow YAML Definition

```yaml
name: carddemo_monthly_statement_cycle
schedule:
  quartz_cron_expression: "0 0 2 1 * ?"  # 2:00 AM UTC on 1st of each month
  timezone_id: "UTC"

tasks:
  - task_key: cbstm03_generate_statements
    description: >
      Replaces CREASTMT.JCL steps 1+2 (CBSTM03A + CBSTM03B combined).
      Generates plain text and HTML account statements.
      CBSTM03B file I/O dispatcher is inlined — no separate task needed.
    job_cluster_key: monthly_large_cluster
    notebook_task:
      notebook_path: /pipelines/cbstm03_statement_gen
      base_parameters:
        stmt_year: "{{start_time | date: '%Y'}}"
        stmt_month: "{{start_time | date: '%-m'}}"
    run_if: "ALL_SUCCESS"
    max_retries: 2

  - task_key: convert_statements_to_pdf
    description: "Replaces TXT2PDF1.JCL — convert plain text statements to PDF"
    depends_on:
      - task_key: cbstm03_generate_statements
    python_wheel_task:
      package_name: carddemo_pdf_converter
      entry_point: convert_statements
      parameters:
        - "--stmt_year={{start_time | date: '%Y'}}"
        - "--stmt_month={{start_time | date: '%-m'}}"
    run_if: "ALL_SUCCESS"
    max_retries: 1

  - task_key: cbtrn03c_transaction_report
    description: >
      Replaces TRANREPT.jcl (CBTRN03C).
      Generates transaction detail report for statement month date range.
    depends_on:
      - task_key: cbstm03_generate_statements
    job_cluster_key: monthly_large_cluster
    notebook_task:
      notebook_path: /pipelines/cbtrn03c_tran_report
      base_parameters:
        start_date: "{{start_time | date: '%Y-%m-01'}}"
        end_date: "{{start_time | date: '%Y-%m-'}}{{start_time | date: '%d'}}"
        report_year: "{{start_time | date: '%Y'}}"
        report_month: "{{start_time | date: '%-m'}}"
    run_if: "ALL_SUCCESS"
    max_retries: 1

  - task_key: print_report_catalog
    description: "Replaces PRTCATBL.jcl — generate summary catalog of report outputs"
    depends_on:
      - task_key: cbtrn03c_transaction_report
      - task_key: convert_statements_to_pdf
    python_wheel_task:
      package_name: carddemo_reporting
      entry_point: print_catalog
    run_if: "ALL_DONE"

job_clusters:
  - job_cluster_key: monthly_large_cluster
    new_cluster:
      spark_version: "14.3.x-scala2.12"
      node_type_id: "m5.2xlarge"
      autoscale:
        min_workers: 4
        max_workers: 16
```

---

## 4. Data Exchange Workflows

### 4.1 Export Workflow

**Workflow Name:** `carddemo_data_exchange_export`  
**Trigger:** On-demand (no schedule)

```yaml
name: carddemo_data_exchange_export

tasks:
  - task_key: cbexport_export_entities
    description: >
      Replaces CBEXPORT.jcl (CBEXPORT program).
      Exports all entities (Customer/Account/XREF/Transaction/Card) to bronze.export_raw.
      Entity order: C→A→X→T→D (matching COBOL 2000-EXPORT-CUSTOMERS sequence).
    notebook_task:
      notebook_path: /pipelines/cbexport_data_export
      base_parameters:
        export_date: "{{start_time | date: '%Y-%m-%d'}}"
        branch_id: "0001"      # EXPORT-BRANCH-ID hardcoded default
        region_code: "NORTH"   # EXPORT-REGION-CODE hardcoded default
    max_retries: 1

  - task_key: transfer_export_file
    description: "Replaces FTPJCL.JCL — transfer export to target location"
    depends_on:
      - task_key: cbexport_export_entities
    python_wheel_task:
      package_name: carddemo_transfer
      entry_point: transfer_export_to_adls
    run_if: "ALL_SUCCESS"
```

### 4.2 Import Workflow

**Workflow Name:** `carddemo_data_exchange_import`  
**Trigger:** On-demand

```yaml
name: carddemo_data_exchange_import

tasks:
  - task_key: cbimport_data_import
    description: >
      Replaces CBIMPORT.jcl (CBIMPORT program).
      Reads bronze.export_raw; splits into 5 Silver entity tables.
      Unknown record types written to migration_ctrl.error_log.
    notebook_task:
      notebook_path: /pipelines/cbimport_data_import
      base_parameters:
        import_date: "{{start_time | date: '%Y-%m-%d'}}"
    max_retries: 1

  - task_key: validate_import_counts
    description: "Post-import reconciliation (replaces CBIMPORT 3000-VALIDATE-IMPORT stub)"
    depends_on:
      - task_key: cbimport_data_import
    python_wheel_task:
      package_name: carddemo_validation
      entry_point: validate_import_reconciliation
    run_if: "ALL_SUCCESS"
```

---

## 5. Authorization Database Maintenance Workflow

### 5.1 Workflow Definition

**Workflow Name:** `carddemo_auth_db_maintenance`  
**Trigger:** On-demand (or scheduled weekly)

### 5.2 JCL Job Stream Being Replaced

```
UNLDPADB.JCL → STEP0 (IEFBR14 delete old files) + STEP01 (PAUDBUNL IMS DLI)
UNLDGSAM.JCL → STEP01 (DBUNLDGS IMS DLI to GSAM)
LOADPADB.JCL → STEP01 (PAUDBLOD IMS BMP)
```

### 5.3 Workflow YAML Definition

```yaml
name: carddemo_auth_db_maintenance

tasks:
  - task_key: paudbunl_unload_auth_db
    description: >
      Replaces UNLDPADB.JCL (PAUDBUNL IMS DLI).
      Unloads silver.auth_summary and silver.auth_detail to Bronze flat files.
      STEP0 (IEFBR14 delete) not needed — Delta table truncate replaces it.
    notebook_task:
      notebook_path: /pipelines/paudbunl_auth_unload
      base_parameters:
        extract_date: "{{start_time | date: '%Y-%m-%d'}}"
    max_retries: 1

  - task_key: dbunldgs_unload_gsam
    description: >
      Replaces UNLDGSAM.JCL (DBUNLDGS IMS DLI).
      Functional equivalent to paudbunl but output to bronze.auth_gsam_root/child tables.
      Runs in parallel with paudbunl_unload_auth_db.
    notebook_task:
      notebook_path: /pipelines/dbunldgs_gsam_unload
      base_parameters:
        extract_date: "{{start_time | date: '%Y-%m-%d'}}"
    max_retries: 1
    # No dependency — runs in parallel with paudbunl

  - task_key: paudblod_load_auth_db
    description: >
      Replaces LOADPADB.JCL (PAUDBLOD IMS BMP).
      Loads Silver auth tables from Bronze flat files produced by paudbunl.
      Duplicate key (IMS 'II' status equivalent) tolerated — MERGE handles gracefully.
    depends_on:
      - task_key: paudbunl_unload_auth_db
    notebook_task:
      notebook_path: /pipelines/paudblod_auth_load
    run_if: "ALL_SUCCESS"
    max_retries: 2
```

---

## 6. Transaction Type Maintenance Workflow

### 6.1 Workflow Definition

**Workflow Name:** `carddemo_tran_type_maintenance`  
**Trigger:** On-demand

### 6.2 JCL Job Stream Being Replaced

```
CREADB21.jcl (schema validation step)
MNTTRDB2.jcl → COBTUPDT batch program (runs under IKJEFT01/DSN)
TRANEXTR.jcl (extract verification step)
```

### 6.3 Workflow YAML Definition

```yaml
name: carddemo_tran_type_maintenance

tasks:
  - task_key: validate_tran_type_schema
    description: >
      Replaces CREADB21.jcl — validate reference.tran_type table structure
      before applying batch maintenance changes.
    python_wheel_task:
      package_name: carddemo_validation
      entry_point: validate_tran_type_schema
    max_retries: 1

  - task_key: cobtupdt_maintain_tran_types
    description: >
      Replaces MNTTRDB2.jcl (COBTUPDT run under IKJEFT01/DSN PLAN=CARDDEMO).
      Reads bronze.tran_type_input; applies A/U/D/* operations to reference.tran_type.
      Note: 9999-ABEND in COBOL does NOT stop processing — PySpark matches this behavior
      (errors logged to migration_ctrl.error_log; processing continues).
    depends_on:
      - task_key: validate_tran_type_schema
    notebook_task:
      notebook_path: /pipelines/cobtupdt_tran_type_maint
      base_parameters:
        input_file_date: "{{start_time | date: '%Y-%m-%d'}}"
    run_if: "ALL_SUCCESS"
    max_retries: 1

  - task_key: extract_verify_tran_types
    description: "Replaces TRANEXTR.jcl — extract and verify applied changes"
    depends_on:
      - task_key: cobtupdt_maintain_tran_types
    python_wheel_task:
      package_name: carddemo_validation
      entry_point: verify_tran_type_extract
    run_if: "ALL_DONE"
```

---

## 7. On-Demand Reporting Workflows

### 7.1 Account Reporting Workflow

**Workflow Name:** `carddemo_account_reporting`  
**Trigger:** On-demand

```yaml
name: carddemo_account_reporting

tasks:
  - task_key: cbact01c_account_file_proc
    description: >
      Replaces READACCT.jcl (CBACT01C).
      Generates fixed, array, and variable-length account output formats.
    notebook_task:
      notebook_path: /pipelines/cbact01c_account_file_proc
      base_parameters:
        run_date: "{{start_time | date: '%Y-%m-%d'}}"

  - task_key: cbact02c_card_list_report
    description: "Replaces READCARD.jcl (CBACT02C) — card listing to log"
    notebook_task:
      notebook_path: /pipelines/cbact02c_card_list_report
    max_retries: 1

  - task_key: cbact03c_xref_extract
    description: "Replaces READXREF.jcl (CBACT03C) — cross-reference listing to log"
    notebook_task:
      notebook_path: /pipelines/cbact03c_xref_extract
    max_retries: 1

  - task_key: cbcus01c_customer_file_proc
    description: "Replaces READCUST.jcl (CBCUS01C) — customer listing to log"
    notebook_task:
      notebook_path: /pipelines/cbcus01c_customer_file_proc
    max_retries: 1
```

---

## 8. MQ Service Workflows (Streaming)

### 8.1 Architecture Decision

COACCT01 and CODATE01 are CICS-MQ trigger programs (not batch programs). In the cloud migration, they are replaced by Databricks Structured Streaming jobs:

- **Trigger mechanism:** IBM MQ → Apache Kafka / Azure Event Hub
- **Processing:** Databricks Structured Streaming continuous query
- **State management:** Databricks checkpoint directory

### 8.2 Account Inquiry Streaming Workflow

**Workflow Name:** `carddemo_account_inquiry_service`  
**Type:** Always-on streaming job (not scheduled)

```yaml
name: carddemo_account_inquiry_service
continuous:
  pause_status: UNPAUSED

tasks:
  - task_key: coacct01_account_inquiry
    description: >
      Replaces COACCT01 (CICS MQ trigger, CDRA transaction).
      Reads from Kafka topic card.demo.inquiry.account.input.
      Processes INQA requests: validates WS-FUNC='INQA' and WS-KEY > 0.
      Reads silver.account for account details.
      Writes reply to Kafka topic card.demo.reply.acct.
      Note: ZIP code NOT included in reply (replicates documented COBOL defect).
      ACTION(BACKOUT) equivalent: Kafka offset committed only on successful MQPUT.
    notebook_task:
      notebook_path: /pipelines/streaming/coacct01_account_inquiry
      base_parameters:
        kafka_input_topic: "card.demo.inquiry.account.input"
        kafka_output_topic: "card.demo.reply.acct"
        kafka_error_topic: "card.demo.error.queue"
        checkpoint_location: "/mnt/carddemo/checkpoints/coacct01"

job_clusters:
  - job_cluster_key: streaming_cluster
    new_cluster:
      spark_version: "14.3.x-scala2.12"
      node_type_id: "m5.large"
      num_workers: 2
```

### 8.3 Date Service Streaming Workflow

**Workflow Name:** `carddemo_date_service`  
**Type:** Always-on streaming job

```yaml
name: carddemo_date_service
continuous:
  pause_status: UNPAUSED

tasks:
  - task_key: codate01_date_service
    description: >
      Replaces CODATE01 (CICS MQ trigger, CDRD transaction).
      Reads from Kafka topic card.demo.inquiry.date.input.
      Returns current system date/time for any valid message (no input validation).
      ASKTIME/FORMATTIME replaced by Python datetime.now().
      Note: No error handling on date retrieval (replicates CODATE01 behavior —
      no RESP/RESP2 checking on ASKTIME — documented in overall spec Section 12).
    notebook_task:
      notebook_path: /pipelines/streaming/codate01_date_service
      base_parameters:
        kafka_input_topic: "card.demo.inquiry.date.input"
        kafka_output_topic: "card.demo.reply.date"
        checkpoint_location: "/mnt/carddemo/checkpoints/codate01"
```

---

## 9. Complete JCL-to-Workflow Mapping Table

This table covers all 46 JCL jobs across all four CardDemo modules:

| # | JCL Job | Original Programs | Batch Cycle | Target Workflow | Target Task(s) | Disposition |
|---|---------|------------------|-------------|----------------|----------------|-------------|
| 1 | ACCTFILE.jcl | (VSAM cluster define) | Setup | Setup DDL | `setup_bronze_acct_table` | Replaced by Delta DDL |
| 2 | READACCT.jcl | CBACT01C | On-demand | `account_reporting` | `cbact01c_account_file_proc` | Migrated |
| 3 | CARDFILE.jcl | (VSAM cluster define) | Setup | Setup DDL | `setup_bronze_card_table` | Replaced by Delta DDL |
| 4 | READCARD.jcl | CBACT02C (implied) | On-demand | `account_reporting` | `cbact02c_card_list_report` | Migrated |
| 5 | CUSTFILE.jcl | (VSAM cluster define) | Setup | Setup DDL | `setup_bronze_cust_table` | Replaced by Delta DDL |
| 6 | READCUST.jcl | CBCUS01C | On-demand | `account_reporting` | `cbcus01c_customer_file_proc` | Migrated |
| 7 | DEFCUST.jcl | (VSAM cluster define) | Setup | Setup DDL | `setup_bronze_cust_table` | Replaced by Delta DDL (duplicate of CUSTFILE) |
| 8 | TRANFILE.jcl | (VSAM cluster define) | Setup | Setup DDL | `setup_bronze_transact_table` | Replaced by Delta DDL |
| 9 | COMBTRAN.jcl | (sort/merge) | Daily | `daily_batch_cycle` | `combine_daily_transactions` | Migrated as Bronze landing task |
| 10 | POSTTRAN.jcl | CBTRN01C + CBTRN02C | Daily | `daily_batch_cycle` | `cbtrn01c_verify` + `cbtrn02c_post` | Migrated (2 tasks) |
| 11 | TRANBKP.jcl | (IDCAMS copy) | Daily | `daily_batch_cycle` | `backup_transaction_delta` | Migrated as Delta CLONE |
| 12 | TRANCATG.jcl | (reference data load) | Setup | `setup_reference_data` | `load_tran_category_ref` | Migrated as Bronze→Reference load |
| 13 | TRANIDX.jcl | (VSAM index rebuild) | Periodic | Z-order optimize | `optimize_transaction_delta` | Replaced by Delta `OPTIMIZE ... ZORDER BY` |
| 14 | TRANREPT.jcl | CBTRN02C (report) / CBTRN03C | Monthly | `monthly_statement_cycle` | `cbtrn03c_transaction_report` | Migrated |
| 15 | TRANTYPE.jcl | (reference data load) | Setup | `setup_reference_data` | `load_tran_type_ref` | Migrated as Bronze→Reference load |
| 16 | DALYREJS.jcl | (reject processing) | Daily | `daily_batch_cycle` | `process_daily_rejects` | Migrated (reads gold.daily_rejects from CBTRN02C) |
| 17 | INTCALC.jcl | CBACT04C | Daily | `daily_batch_cycle` | `cbact04c_calculate_interest` | Migrated |
| 18 | CREASTMT.JCL | CBSTM03A, CBSTM03B | Monthly | `monthly_statement_cycle` | `cbstm03_generate_statements` | Migrated (CBSTM03B inlined) |
| 19 | REPTFILE.jcl | (report file management) | Monthly | `monthly_statement_cycle` | `manage_report_partitions` | Replaced by Delta partition management |
| 20 | PRTCATBL.jcl | (print catalog) | Monthly | `monthly_statement_cycle` | `print_report_catalog` | Migrated as Python task |
| 21 | TXT2PDF1.JCL | (text to PDF conversion) | Monthly | `monthly_statement_cycle` | `convert_statements_to_pdf` | Migrated as Python task (PDF lib) |
| 22 | CBEXPORT.jcl | CBEXPORT | On-demand | `data_exchange_export` | `cbexport_export_entities` | Migrated |
| 23 | CBIMPORT.jcl | CBIMPORT | On-demand | `data_exchange_import` | `cbimport_data_import` | Migrated |
| 24 | FTPJCL.JCL | (FTP transfer) | On-demand | `data_exchange_export` | `transfer_export_file` | Migrated as ADLS transfer task |
| 25 | DUSRSECJ.jcl | (user security maintain) | Admin | `admin_maintenance` | `maintain_user_security` | Migrated as admin maintenance task |
| 26 | CBADMCDJ.jcl | (admin card job) | Admin | `admin_maintenance` | `admin_card_maintenance` | Migrated as admin task |
| 27 | OPENFIL.jcl | (open CICS files) | Daily | `daily_batch_cycle` | `resume_streaming_services` | Migrated as streaming resume task |
| 28 | CLOSEFIL.jcl | (close CICS files) | Daily | `daily_batch_cycle` | `stop_streaming_services` | Migrated as streaming quiesce task |
| 29 | XREFFILE.jcl | (VSAM cluster define) | Setup | Setup DDL | `setup_bronze_xref_table` | Replaced by Delta DDL |
| 30 | READXREF.jcl | CBACT03C | On-demand | `account_reporting` | `cbact03c_xref_extract` | Migrated |
| 31 | WAITSTEP.jcl | COBSWAIT | Embedded | N/A | N/A | Replaced by Databricks task retry policy + `time.sleep()` where needed |
| 32 | CBPAUP0J.jcl | CBPAUP0C (IMS BMP) | Daily | `daily_batch_cycle` | `cbpaup0c_purge_authorizations` | Migrated |
| 33 | DBPAUTP0.jcl | (IMS DB config) | Setup | Setup DDL | `setup_auth_db_config` | Replaced by Silver table DDL |
| 34 | LOADPADB.JCL | PAUDBLOD (IMS BMP) | On-demand | `auth_db_maintenance` | `paudblod_load_auth_db` | Migrated |
| 35 | UNLDPADB.JCL | PAUDBUNL (IMS DLI) | On-demand | `auth_db_maintenance` | `paudbunl_unload_auth_db` | Migrated |
| 36 | UNLDGSAM.JCL | DBUNLDGS (IMS DLI) | On-demand | `auth_db_maintenance` | `dbunldgs_unload_gsam` | Migrated (GSAM replaced by Delta) |
| 37 | CREADB21.jcl | (DB2 table creation) | Setup | Setup DDL | `setup_tran_type_schema` | Replaced by Delta DDL |
| 38 | MNTTRDB2.jcl | COBTUPDT (IKJEFT01/DSN) | On-demand | `tran_type_maintenance` | `cobtupdt_maintain_tran_types` | Migrated |
| 39 | TRANEXTR.jcl | (extract verification) | On-demand | `tran_type_maintenance` | `extract_verify_tran_types` | Migrated as verification task |
| **AUTH (5)** | | | | | | |
| 40 | CBPAUP0J.jcl | CBPAUP0C | Daily | `daily_batch_cycle` | `cbpaup0c_purge_authorizations` | (Same as row 32) |
| 41 | DBPAUTP0.jcl | — | Setup | Setup DDL | — | (Same as row 33) |
| 42 | LOADPADB.JCL | PAUDBLOD | On-demand | `auth_db_maintenance` | `paudblod_load_auth_db` | (Same as row 34) |
| 43 | UNLDPADB.JCL | PAUDBUNL | On-demand | `auth_db_maintenance` | `paudbunl_unload_auth_db` | (Same as row 35) |
| 44 | UNLDGSAM.JCL | DBUNLDGS | On-demand | `auth_db_maintenance` | `dbunldgs_unload_gsam` | (Same as row 36) |
| **TRAN TYPE DB2 (3)** | | | | | | |
| 45 | CREADB21.jcl | — | Setup | Setup DDL | — | (Same as row 37) |
| 46 | MNTTRDB2.jcl | COBTUPDT | On-demand | `tran_type_maintenance` | `cobtupdt_maintain_tran_types` | (Same as row 38) |

---

## 10. Cluster Sizing Recommendations

### 10.1 Per-Workflow Cluster Specification

| Workflow | Cluster Type | Driver | Workers | Autoscale Min/Max | Rationale |
|---------|-------------|--------|---------|-------------------|-----------|
| `daily_batch_cycle` | Job cluster | m5.xlarge | Autoscale | 2/8 | Mixed workload; CBTRN02C is the heaviest (joins + multiple MERGE operations) |
| `monthly_statement_cycle` | Job cluster | m5.2xlarge | Autoscale | 4/16 | Statement generation reads full XREF + customer + account + transaction data |
| `data_exchange_export` | Job cluster | m5.xlarge | Autoscale | 2/8 | Sequential entity scans; moderate size |
| `data_exchange_import` | Job cluster | m5.xlarge | Autoscale | 2/8 | Split by record type; parallel write |
| `auth_db_maintenance` | Job cluster | m5.large | Fixed | 2 | Auth data is relatively small (IMS database) |
| `tran_type_maintenance` | Job cluster | m5.large | Fixed | 2 | Small reference table; minimal compute |
| `account_reporting` | Shared interactive | m5.large | Autoscale | 1/4 | Diagnostic listing programs; minimal compute |
| `account_inquiry_service` (streaming) | Long-running cluster | m5.large | Fixed | 2 | Always-on; low latency requirement |
| `date_service` (streaming) | Long-running cluster | m5.large | Fixed | 1 | Very lightweight; no I/O |

### 10.2 Spark Configuration

```python
# Recommended Spark configuration for all CardDemo pipelines
spark_conf = {
    # Delta Lake
    "spark.sql.extensions": "io.delta.sql.DeltaSparkSessionExtension",
    "spark.sql.catalog.spark_catalog": "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    
    # Broadcast join threshold (DISCGRP, TRNTYPE, TRANCATG are broadcast candidates)
    "spark.sql.autoBroadcastJoinThreshold": "10MB",
    
    # Decimal precision (critical for COMP-3 financial fields)
    "spark.sql.ansi.enabled": "true",
    "spark.sql.decimalOperations.allowPrecisionLoss": "false",
    
    # Shuffle partitions
    "spark.sql.shuffle.partitions": "200",  # Tune per environment
    
    # Delta write optimization
    "spark.databricks.delta.optimizeWrite.enabled": "true",
    "spark.databricks.delta.autoCompact.enabled": "true"
}
```

---

## 11. Retry and Notification Policies

### 11.1 Per-Task Retry Policy

| Task Type | Max Retries | Retry Wait (min) | Rationale |
|-----------|------------|-----------------|-----------|
| Bronze ingestion tasks | 3 | 2 | Network/storage transient failures |
| MERGE/UPSERT tasks (CBTRN02C, CBACT04C) | 2 | 5 | Delta concurrent write conflicts |
| Read-only reporting tasks | 1 | 1 | Low risk; quick retry |
| IMS-equivalent tasks (CBPAUP0C, PAUDBUNL, PAUDBLOD) | 2 | 5 | Delta ACID guarantees idempotent re-run |
| Streaming tasks | 5 | 1 | Connection drops are transient |
| Admin tasks (stop/resume streaming) | 3 | 1 | Service state may take time to settle |

### 11.2 Notification Configuration

```yaml
notification_settings:
  email_notifications:
    on_failure:
      - batch-ops@carddemo.internal
      - on-call@carddemo.internal
    on_success:
      - batch-summary@carddemo.internal
    on_duration_warning_threshold_exceeded:
      - performance-alerts@carddemo.internal
  
  # Duration warnings (alert if job takes > 2x historical average)
  health:
    rules:
      - metric: run_duration_seconds
        operator: GREATER_THAN
        value: 3600  # 1 hour warning for daily batch
```

### 11.3 COBOL ABEND → Databricks Alert Mapping

| COBOL Condition | COBOL Behavior | Databricks Behavior |
|----------------|---------------|---------------------|
| `PERFORM 9999-ABEND-PROGRAM` (CEE3ABD 999) | ABEND with dump | Task fails with exit code 1; email notification to on-call |
| `MOVE 16 TO RETURN-CODE; GOBACK` (CBPAUP0C) | RC=16, job fails | Task fails with custom exit code 16; escalated notification |
| `MOVE 4 TO RETURN-CODE` (CBTRN02C, COBTUPDT) | RC=4, job continues in stream | Task succeeds but logs `return_code=4` in pipeline_metrics; warning notification |
| `STOP RUN` (COBTUPDT — not called!) | Normal termination | Task succeeds with exit code 0 |

---

## 12. Parameterization Reference

### 12.1 Workflow-Level Parameters (replacing JCL symbolic parameters)

| JCL Symbolic | Workflow | Parameter Key | Default Value | Description |
|-------------|---------|---------------|---------------|-------------|
| `&RUNDATE` | All workflows | `run_date` | `{{start_time \| date: '%Y-%m-%d'}}` | Business processing date |
| `&BATCHID` | All workflows | `batch_id` | Auto-generated UUID | Batch run identifier |
| `&EXPDAYS` | `daily_batch_cycle` | `expiry_days` | `5` | P-EXPIRY-DAYS for CBPAUP0C |
| `&CHKPFREQ` | `daily_batch_cycle` | `checkpoint_freq` | `5` | P-CHKP-FREQ for CBPAUP0C |
| `&DEBUGFLG` | `daily_batch_cycle` | `debug_enabled` | `false` | P-DEBUG-FLAG for CBPAUP0C |
| `&STMTYR` | `monthly_statement_cycle` | `stmt_year` | `{{start_time \| date: '%Y'}}` | Statement generation year |
| `&STMTMO` | `monthly_statement_cycle` | `stmt_month` | `{{start_time \| date: '%-m'}}` | Statement generation month |
| `&STARTDT` | `tran_type_maintenance` | `start_date` | — | CBTRN03C report start date |
| `&ENDDT` | `tran_type_maintenance` | `end_date` | — | CBTRN03C report end date |
| `&BRANCHID` | `data_exchange_export` | `branch_id` | `0001` | CBEXPORT EXPORT-BRANCH-ID |
| `&REGION` | `data_exchange_export` | `region_code` | `NORTH` | CBEXPORT EXPORT-REGION-CODE |

### 12.2 Secret Parameters (replacing JCL `//SYSIN DD *` sensitive data)

All sensitive values stored in Databricks Secret Scope `carddemo`:

| Secret Key | Replaces | Usage |
|-----------|---------|-------|
| `carddemo/adls_storage_key` | JCL RACF dataset access | ADLS storage authentication |
| `carddemo/kafka_bootstrap_servers` | MQ queue manager hostname | Kafka/Event Hub endpoint |
| `carddemo/kafka_sasl_password` | MQ channel auth | Kafka SASL authentication |
| `carddemo/notification_smtp_password` | N/A (new capability) | Email notification SMTP |
