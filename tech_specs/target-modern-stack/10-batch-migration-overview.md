# CardDemo Batch Migration Overview
## Mainframe COBOL/JCL to Databricks PySpark — Overall Strategy

**Document Version:** 1.0  
**Date:** 2026-04-06  
**Scope:** All batch COBOL programs and JCL jobs in the CardDemo credit card application

---

## Table of Contents

1. [Source Batch Landscape Summary](#1-source-batch-landscape-summary)
2. [Target Databricks Architecture Overview](#2-target-databricks-architecture-overview)
3. [Migration Approach](#3-migration-approach)
4. [Delta Lake Medallion Architecture Decisions](#4-delta-lake-medallion-architecture-decisions)
5. [Orchestration Strategy](#5-orchestration-strategy)
6. [Source-to-Target Program Mapping](#6-source-to-target-program-mapping)
7. [JCL-to-Databricks Workflow Mapping](#7-jcl-to-databricks-workflow-mapping)
8. [Dependencies and Execution Order](#8-dependencies-and-execution-order)
9. [Environment and Configuration Management](#9-environment-and-configuration-management)
10. [Error Handling and Restart/Recovery Strategy](#10-error-handling-and-restartrecovery-strategy)
11. [Monitoring and Alerting Approach](#11-monitoring-and-alerting-approach)

---

## 1. Source Batch Landscape Summary

### 1.1 Batch Program Inventory

The CardDemo application contains **16 batch COBOL programs** distributed across four modules:

#### Base CardDemo Batch Programs (13 programs)

| Program | Source File | Type | Function |
|---------|------------|------|----------|
| CBACT01C | app/cbl/CBACT01C.cbl | Batch COBOL | Read Account VSAM (ACCTFILE) sequentially; write to 3 output formats (fixed, array, variable-length); calls external COBDATFT date formatter |
| CBACT02C | app/cbl/CBACT02C.cbl | Batch COBOL | Read Credit Card VSAM (CARDFILE) sequentially; print all records to SYSOUT |
| CBACT03C | app/cbl/CBACT03C.cbl | Batch COBOL | Read Card/Account Cross-Reference VSAM (XREFFILE) sequentially; print all records to SYSOUT |
| CBACT04C | app/cbl/CBACT04C.cbl | Batch COBOL | Interest calculator; reads TCATBALF driving file, looks up rates from DISCGRP; writes interest transactions to TRANSACT; updates ACCTFILE balances |
| CBCUS01C | app/cbl/CBCUS01C.cbl | Batch COBOL | Read Customer VSAM (CUSTFILE) sequentially; print all records to SYSOUT |
| CBTRN01C | app/cbl/CBTRN01C.cbl | Batch COBOL | Daily transaction verification; reads DALYTRAN; cross-checks via XREFFILE and ACCTFILE; DISPLAY-only output |
| CBTRN02C | app/cbl/CBTRN02C.cbl | Batch COBOL | Daily transaction posting; validates and posts to TRANSACT; updates ACCTFILE and TCATBALF; writes rejects to DALYREJS; RC=4 on any rejects |
| CBTRN03C | app/cbl/CBTRN03C.cbl | Batch COBOL | Transaction detail report; filters TRANSACT by date range from DATEPARM; lookups via CARDXREF/TRANTYPE/TRANCATG; writes 133-byte formatted report |
| CBSTM03A | app/cbl/CBSTM03A.CBL | Batch COBOL | Statement generation driver; reads XREFFILE/CUSTFILE/ACCTFILE/TRNXFILE via CBSTM03B subroutine; produces plain text and HTML statements; uses ALTER/GO TO and mainframe control blocks |
| CBSTM03B | app/cbl/CBSTM03B.CBL | Batch Subroutine | File I/O dispatcher for CBSTM03A; handles TRNXFILE, XREFFILE, CUSTFILE, ACCTFILE via generic DD name + operation code interface |
| CBEXPORT | app/cbl/CBEXPORT.cbl | Batch COBOL | Exports all entity data (Customer/Account/XREF/Transaction/Card) into consolidated 500-byte KSDS export file; type codes C/A/X/T/D |
| CBIMPORT | app/cbl/CBIMPORT.cbl | Batch COBOL | Reverses CBEXPORT; reads consolidated file; splits into 5 entity sequential output files; writes unknowns to error file |
| COBSWAIT | app/cbl/COBSWAIT.cbl | Batch COBOL | MVS wait utility; reads centisecond duration from SYSIN; calls MVSWAIT assembler routine |

#### Authorization Batch Programs (4 programs)

| Program | Source File | Type | Function |
|---------|------------|------|----------|
| CBPAUP0C | cbl/CBPAUP0C.cbl | Batch IMS BMP | Purge expired pending authorizations; scans PAUTSUM0/PAUTDTL1 IMS segments; deletes by expiry date; IMS CHKP for restart |
| PAUDBUNL | cbl/PAUDBUNL.cbl | Batch IMS DLI | Unload IMS DBPAUTP0 to two QSAM sequential files (100-byte root records, 206-byte child records with parent key) |
| PAUDBLOD | cbl/PAUDBLOD.cbl | Batch IMS DLI | Load IMS DBPAUTP0 from PAUDBUNL output files; inserts PAUTSUM0 root then PAUTDTL1 child segments via CBLTDLI |
| DBUNLDGS | cbl/DBUNLDGS.CBL | Batch IMS DLI | Unload IMS DBPAUTP0 to GSAM datasets; functional equivalent of PAUDBUNL using GSAM PCBs instead of QSAM |

#### Transaction Type DB2 Batch Programs (1 program)

| Program | Source File | Type | Function |
|---------|------------|------|----------|
| COBTUPDT | app/app-transaction-type-db2/cbl/COBTUPDT.cbl | Batch COBOL with DB2 | Batch maintenance of CARDDEMO.TRANSACTION_TYPE table; reads 53-byte input records; dispatches A/U/D/* operations to DB2 |

#### MQ-Triggered Programs (2 programs — online/batch hybrid)

| Program | Source File | Type | Function |
|---------|------------|------|----------|
| COACCT01 | app/app-vsam-mq/cbl/COACCT01.cbl | CICS MQ Trigger | Receives MQ account inquiry requests; reads ACCTDAT VSAM; returns account details via MQ reply |
| CODATE01 | app/app-vsam-mq/cbl/CODATE01.cbl | CICS MQ Trigger | Receives MQ date inquiry requests; returns current CICS system date/time via MQ reply |

### 1.2 JCL Job Inventory

The CardDemo application contains **46 JCL jobs** distributed as follows:

- **Base:** 38 JCL jobs
- **Authorization:** 5 JCL jobs
- **Transaction Type DB2:** 3 JCL jobs

#### Key Batch JCL Jobs

| JCL Job | Programs Invoked | Batch Cycle | Purpose |
|---------|-----------------|-------------|---------|
| READACCT.jcl | CBACT01C | On-demand | Account file read/report |
| READCUST.jcl | CBCUS01C | On-demand | Customer file read/report |
| TRANREPT.jcl | CBTRN02C (report mode) | Monthly | Transaction detail reports |
| CREASTMT.JCL | CBSTM03A, CBSTM03B | Monthly | Credit card statement generation |
| CBEXPORT.jcl | CBEXPORT | On-demand | Data export for migration |
| CBIMPORT.jcl | CBIMPORT | On-demand | Data import from migration |
| WAITSTEP.jcl | COBSWAIT | Embedded | Timed delays within job streams |
| CBPAUP0J.jcl | CBPAUP0C | Daily | Purge expired authorizations (IMS BMP) |
| LOADPADB.JCL | PAUDBLOD | On-demand | Load IMS authorization database |
| UNLDPADB.JCL | PAUDBUNL | On-demand | Unload IMS authorization database |
| UNLDGSAM.JCL | DBUNLDGS | On-demand | Unload IMS to GSAM |
| MNTTRDB2.jcl | COBTUPDT | On-demand | Batch transaction type DB2 maintenance |
| POSTTRAN.jcl | (implicit CBTRN02C) | Daily | Post daily transactions |
| INTCALC.jcl | CBACT04C | Daily | Interest calculation |
| DALYREJS.jcl | (implied by CBTRN02C) | Daily | Process daily rejects |

### 1.3 Source Data Stores

| Data Store | Technology | Record Size | Primary Use |
|-----------|-----------|-------------|-------------|
| ACCTDAT (ACCTFILE) | VSAM KSDS | 300 bytes | Account master; key=ACCT-ID 9(11) |
| CARDDAT (CARDFILE) | VSAM KSDS | 150 bytes | Card master; key=CARD-NUM X(16) |
| CARDAIX | VSAM AIX Path | — | Alternate index on CARDDAT by Account ID |
| CCXREF (XREFFILE) | VSAM KSDS | 50 bytes | Card-to-account cross-reference; key=CARD-NUM X(16) |
| CXACAIX | VSAM AIX Path | — | Alternate index on CCXREF by Account ID |
| CUSTDAT (CUSTFILE) | VSAM KSDS | 500 bytes | Customer master; key=CUST-ID 9(9) |
| TRANSACT (TRANFILE) | VSAM KSDS | 350 bytes | Transaction records; key=TRAN-ID X(16) |
| USRSEC | VSAM KSDS | varies | User security; key=USER-ID X(8) |
| PAUTHDTL (IMS) | IMS HISAM | 200 bytes | Pending authorization details; segment PAUTDTL1 |
| PAUTHSUM (IMS) | IMS HISAM | 100 bytes | Pending authorization summaries; segment PAUTSUM0 |
| AUTHFRDS | DB2 Table | — | Fraud-flagged authorizations |
| TRNTYPE | DB2 Table | — | Transaction type master; TR_TYPE CHAR(2) |
| TRNTYCAT | DB2 Table | — | Transaction type categories |
| TCATBALF | VSAM KSDS | variable | Transaction category balances per account |
| DISCGRP | VSAM KSDS | variable | Disclosure group interest rates |

---

## 2. Target Databricks Architecture Overview

### 2.1 Platform Components

```
                    ┌─────────────────────────────────────────────────────────┐
                    │              Databricks Lakehouse Platform               │
                    │                                                         │
                    │  ┌───────────────────────────────────────────────────┐  │
                    │  │           Unity Catalog (Data Governance)         │  │
                    │  └───────────────────────────────────────────────────┘  │
                    │                                                         │
                    │  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
                    │  │   Bronze    │  │    Silver    │  │     Gold      │  │
                    │  │ (Raw/Land)  │  │  (Cleaned)   │  │ (Aggregated)  │  │
                    │  │ Delta Lake  │  │  Delta Lake  │  │  Delta Lake   │  │
                    │  └─────────────┘  └──────────────┘  └───────────────┘  │
                    │                                                         │
                    │  ┌─────────────────────────────────────────────────┐    │
                    │  │              Databricks Workflows                │    │
                    │  │  (Replaces z/OS JCL Job Scheduler)              │    │
                    │  └─────────────────────────────────────────────────┘    │
                    │                                                         │
                    │  ┌─────────────────────────────────────────────────┐    │
                    │  │        Databricks Jobs (PySpark Notebooks)      │    │
                    │  │  (Replaces COBOL Batch Programs)                │    │
                    │  └─────────────────────────────────────────────────┘    │
                    └─────────────────────────────────────────────────────────┘
                                           |
                    ┌──────────────────────┴──────────────────────────────────┐
                    │               Azure Data Lake Storage Gen2              │
                    │        (Replaces VSAM/DB2/IMS/Sequential datasets)      │
                    └─────────────────────────────────────────────────────────┘
```

### 2.2 Key Technology Replacements

| Mainframe Component | Databricks Equivalent |
|--------------------|----------------------|
| VSAM KSDS files | Delta tables (Silver layer, primary keyed) |
| DB2 tables | Delta tables (Silver layer) |
| IMS HISAM databases | Flattened Delta tables with parent-child schema |
| Sequential flat files | Delta tables (Bronze layer) |
| JCL job streams | Databricks Workflows |
| JCL job steps | Databricks Workflow tasks |
| JCL COND parameters | Task dependencies + error handling in PySpark |
| JCL PARM values | Databricks job parameters (widgets/env vars) |
| SYSOUT / DISPLAY | Databricks job logs + Delta audit tables |
| IBM MQ queues | Databricks Structured Streaming (Kafka/Event Hub) |
| IMS BMP checkpoints | Databricks checkpoint directories + Delta transaction log |
| COBOL programs | PySpark notebooks / Python scripts |

### 2.3 Catalog and Namespace Design

```
Unity Catalog:
  catalog: carddemo
    schema: bronze          -- Raw/landing zone
    schema: silver          -- Cleansed/conformed
    schema: gold            -- Business-ready aggregates
    schema: migration_ctrl  -- Migration control tables, audit logs
    schema: reference       -- Transaction types, interest rates, categories
```

---

## 3. Migration Approach

### 3.1 Guiding Principles

1. **Exact Business Logic Fidelity**: Every business rule in every COBOL paragraph is translated to PySpark with the same computational outcome. No business logic is approximated or reinterpreted.

2. **COBOL Paragraph to Function Mapping**: Each COBOL PROCEDURE DIVISION paragraph maps to one Python function. Paragraph names are preserved as function names (with underscores replacing hyphens) and documented in docstrings.

3. **Sequential-to-Parallel Transformation**: Where COBOL programs process records sequentially, PySpark uses DataFrame transformations that operate in parallel. Sequential accumulators (WS-TOTAL-INT, WS-TRANSACTION-COUNT) map to DataFrame aggregations or Window functions.

4. **Data Type Precision**: All signed packed decimal fields (COMP-3), binary integers (COMP), and signed numeric fields (S9(n)V9(m)) use PySpark DecimalType — never DoubleType — to preserve exact numeric precision.

5. **Incremental Migration**: Migrate in dependency order:
   - Phase 1: Reference data (TRNTYPE, TRANCATG, DISCGRP)
   - Phase 2: Master data ingestion (Customer, Account, Card, XREF)
   - Phase 3: Transaction processing (CBTRN01C, CBTRN02C, CBTRN03C)
   - Phase 4: Interest calculation (CBACT04C)
   - Phase 5: Statement generation (CBSTM03A/B)
   - Phase 6: Export/Import (CBEXPORT, CBIMPORT)
   - Phase 7: Authorization processing (CBPAUP0C, PAUDBUNL, PAUDBLOD, DBUNLDGS)

### 3.2 Per-Program Migration Pattern

Each COBOL batch program is migrated to a **Databricks Job** consisting of:

1. **Configuration module** (`config/pipeline_config.py`): JCL PARM → Python parameters; DD names → Delta table paths
2. **Schema module** (`domain/models.py`): COPY copybooks → PySpark StructType definitions
3. **Business rules module** (`domain/business_rules.py`): COBOL paragraphs → pure Python/PySpark functions
4. **Reader module** (`infrastructure/readers.py`): VSAM READ/DB2 SELECT → Delta table reads
5. **Writer module** (`infrastructure/writers.py`): VSAM WRITE/REWRITE → Delta table merges/inserts
6. **Transformation module** (`transformations/step_N_name.py`): One per major JCL step or logical stage
7. **Test module** (`tests/test_*.py`): pytest tests for each function

### 3.3 COBOL Construct Translation Rules

| COBOL Construct | PySpark Translation |
|----------------|---------------------|
| `OPEN INPUT file / READ file INTO ws` | `spark.read.format("delta").load(table_path)` |
| `OPEN OUTPUT file / WRITE record FROM ws` | `df.write.format("delta").mode("append").save(table_path)` |
| `OPEN I-O file / REWRITE record FROM ws` | `DeltaTable.forPath(spark, path).merge(...)` |
| `PERFORM UNTIL END-OF-FILE = 'Y'` | DataFrame transformation (no loop needed) |
| `EVALUATE expr WHEN val1 WHEN val2` | `F.when(cond1, val1).when(cond2, val2).otherwise(...)` |
| `COMPUTE ws-field = expr` | `df.withColumn("field", expr)` with DecimalType |
| `ADD field1 TO field2` | `df.withColumn("field2", F.col("field1") + F.col("field2"))` |
| `SORT file ON ASCENDING KEY key` | `df.orderBy(F.col("key").asc())` |
| `INSPECT TALLYING` | `F.length(col) - F.length(F.regexp_replace(col, pattern, ''))` |
| `STRING s1 s2 INTO ws` | `F.concat(F.col("s1"), F.col("s2"))` |
| `IF INVALID KEY (VSAM)` | `left join + filter IS NULL` → quarantine record |
| `PERFORM VARYING idx FROM 1 BY 1 UNTIL` | `F.explode()` / Window functions |
| `FUNCTION CURRENT-DATE` | `F.current_timestamp()` |
| Level-88 condition names | Python constants / Enum class |
| COMP-3 `S9(n)V9(m)` | `DecimalType(n+m, m)` |
| COMP `S9(9)` | `IntegerType()` |
| COMP `S9(18)` | `LongType()` |

### 3.4 Known Migration Challenges

| Challenge | Source Programs | Migration Strategy |
|-----------|----------------|-------------------|
| ALTER/GO TO (CBSTM03A) | CBSTM03A | Replace with explicit Python function dispatch; eliminate ALTER entirely |
| IMS DLI calls (CBPAUP0C, PAUDBUNL, PAUDBLOD, DBUNLDGS) | Auth batch programs | Extract IMS data to Bronze Delta tables during initial load; replace DLI calls with Delta table reads/writes |
| GSAM output (DBUNLDGS) | DBUNLDGS | Write to Delta table instead of GSAM; GSAM files not applicable in cloud |
| COBDATFT assembler call (CBACT01C) | CBACT01C | Replace with Python datetime formatting |
| MVSWAIT assembler call (COBSWAIT) | COBSWAIT | Replace with `time.sleep()` or Databricks cluster pause |
| IBM MQ triggers (COACCT01, CODATE01) | VSAM-MQ | Replace with Structured Streaming from Kafka/Event Hub or scheduled polling job |
| IMS BMP checkpoints (CBPAUP0C) | CBPAUP0C | Replace with Delta table transaction log + Databricks checkpoint files |
| Mainframe PSA/TCB/TIOT addressing (CBSTM03A) | CBSTM03A | Eliminate entirely; not applicable in cloud; capture job metadata via Databricks job run API |
| COMP-3 packed decimal in VSAM records | All programs | Unpack during Bronze ingestion using Python `struct` library; store as DecimalType in Delta |

---

## 4. Delta Lake Medallion Architecture Decisions

### 4.1 Medallion Layer Definitions

#### Bronze Layer (`carddemo.bronze`)
- **Purpose**: Landing zone for raw mainframe data extracts
- **Format**: Delta tables with exact column representations of COBOL copybook layouts
- **Data Types**: Strings for all numeric fields (to preserve raw mainframe format including leading zeros, packed bytes); separate columns for field offsets where REDEFINES is used
- **Partitioning**: By `extract_date` (the date the extract was loaded)
- **Retention**: 90 days (rolling window)
- **Schema Evolution**: `mergeSchema = true` to accommodate any format changes during migration
- **Key Principle**: No business transformations; store exactly what came from the mainframe

#### Silver Layer (`carddemo.silver`)
- **Purpose**: Cleansed, conformed, business-typed data
- **Format**: Delta tables with proper PySpark types (DecimalType, IntegerType, etc.)
- **Data Types**: All types correctly mapped from COBOL PIC clauses
- **Partitioning**: By business-relevant columns (e.g., `account_id` prefix, `transaction_date`)
- **Retention**: 7 years (financial record retention)
- **Schema Evolution**: Additive only; breaking changes require new table version
- **Key Principle**: Single source of truth for each entity; deduplication applied; referential integrity enforced

#### Gold Layer (`carddemo.gold`)
- **Purpose**: Business-ready aggregated and pre-joined data for reporting and analytics
- **Format**: Delta tables optimized for query performance
- **Partitioning**: By reporting period (month/year)
- **Retention**: 7 years
- **Key Principle**: Derived from Silver; updated on schedule matching the original batch cycle

### 4.2 Design Decisions

| Decision | Rationale |
|----------|-----------|
| All IMS data flattened to two Delta tables (auth_summary, auth_detail) | IMS hierarchical model has exactly 2 segment types; parent-child relationship captured via foreign key |
| VSAM alternate indexes (AIX) replaced with Delta table Z-ordering | Z-ordering on account_id enables efficient account-based queries without separate index structures |
| TCATBALF modeled as Silver table keyed on (account_id, tran_type_cd, tran_cat_cd) | Matches VSAM composite key; enables upsert semantics using MERGE |
| DISCGRP as a broadcast-eligible reference table | Small lookup table; broadcast join avoids shuffle in interest calculation pipeline |
| Transaction type records (TRNTYPE) in reference schema | Shared by online and batch; modeled separately to avoid conflicts |
| Export/Import uses intermediate Bronze tables | CBEXPORT output modeled as Bronze Delta table; CBIMPORT reads from Bronze and writes to Silver |

### 4.3 Data Flow by Medallion Layer

```
Mainframe Extract (VSAM/DB2/IMS)
    │
    ▼
Bronze Layer (Raw)
    carddemo.bronze.acct_raw
    carddemo.bronze.card_raw
    carddemo.bronze.cust_raw
    carddemo.bronze.xref_raw
    carddemo.bronze.transact_raw
    carddemo.bronze.auth_summary_raw
    carddemo.bronze.auth_detail_raw
    carddemo.bronze.export_raw
    │
    ▼ (Cleanse + Type mapping)
Silver Layer (Conformed)
    carddemo.silver.account
    carddemo.silver.card
    carddemo.silver.customer
    carddemo.silver.card_xref
    carddemo.silver.transaction
    carddemo.silver.tran_cat_balance
    carddemo.silver.disclosure_group
    carddemo.silver.auth_summary
    carddemo.silver.auth_detail
    carddemo.silver.auth_fraud
    carddemo.silver.user_security
    carddemo.reference.tran_type
    carddemo.reference.tran_category
    │
    ▼ (Aggregate + Join)
Gold Layer (Business-ready)
    carddemo.gold.account_statement
    carddemo.gold.transaction_report
    carddemo.gold.interest_charges
    carddemo.gold.daily_reject_summary
    carddemo.gold.auth_purge_audit
```

---

## 5. Orchestration Strategy

### 5.1 Databricks Workflows Replace JCL Job Streams

Each JCL job stream maps to a **Databricks Workflow** with tasks representing individual JCL steps. Task dependencies replace JCL COND parameters.

### 5.2 Workflow Categories

| Workflow Name | Replaces | Schedule | Description |
|--------------|----------|----------|-------------|
| `daily_batch_cycle` | Daily JCL sequence | Nightly | CLOSEFIL → TRANBKP → POSTTRAN → INTCALC → DALYREJS → CBPAUP0J → OPENFIL equivalent |
| `monthly_statement_cycle` | Monthly JCL sequence | Monthly (1st) | CREASTMT → TXT2PDF1 → TRANREPT |
| `data_exchange_export` | CBEXPORT.jcl | On-demand | Export all entity data |
| `data_exchange_import` | CBIMPORT.jcl | On-demand | Import entity data |
| `auth_db_maintenance` | UNLDPADB + LOADPADB | On-demand | IMS authorization DB backup/restore cycle |
| `tran_type_maintenance` | MNTTRDB2.jcl | On-demand | Transaction type DB2 maintenance |
| `account_reporting` | READACCT.jcl | On-demand | Account file reporting |

### 5.3 JCL COND Parameter Replacement

| JCL Pattern | Databricks Equivalent |
|------------|----------------------|
| `COND=(4,GE)` — run only if RC < 4 | Task dependency `run_if: "ALL_SUCCESS"` |
| `COND=(0,EQ)` — run only if RC = 0 | Task dependency `run_if: "ALL_SUCCESS"` + custom exit code check |
| `IF ABEND THEN ... ENDIF` | Task dependency `run_if: "AT_LEAST_ONE_FAILED"` with notification task |
| `COND=(4,GE)` on downstream step | Task `depends_on` with `outcome: "success"` |
| No COND (always run) | Task dependency `run_if: "ALL_DONE"` |

### 5.4 Parameterization

JCL symbolic parameters (`&RUNDATE`, `&BATCHID`) map to Databricks job parameters:

```python
# Example: Replaces JCL //PARM DD DATA='2026-04-06'
dbutils.widgets.text("run_date", "2026-04-06")
dbutils.widgets.text("expiry_days", "5")
dbutils.widgets.text("checkpoint_freq", "5")
```

### 5.5 Cluster Strategy

| Workflow | Cluster Type | Sizing Recommendation |
|----------|-------------|----------------------|
| daily_batch_cycle | Job cluster (ephemeral) | 4-8 workers, m5.xlarge equivalent |
| monthly_statement_cycle | Job cluster (ephemeral) | 8-16 workers (statement generation is I/O intensive) |
| data_exchange_export/import | Job cluster (ephemeral) | 4-8 workers |
| auth_db_maintenance | Job cluster (ephemeral) | 2-4 workers (small IMS datasets) |
| on-demand reporting | Interactive cluster (shared) | 4-8 workers |

---

## 6. Source-to-Target Program Mapping

| Source Program | JCL Job(s) | Target Pipeline | Target Databricks Job | Primary Delta Tables (Input) | Primary Delta Tables (Output) |
|---------------|-----------|----------------|----------------------|------------------------------|-------------------------------|
| CBACT01C | READACCT.jcl | Account File Processing Pipeline | `cbact01c_account_file_proc` | `silver.account` | `gold.account_extract`, `bronze.account_array_out`, `bronze.account_vbr_out` |
| CBACT02C | (embedded in READACCT/reporting) | Card List Report Pipeline | `cbact02c_card_list_report` | `silver.card` | `migration_ctrl.card_listing_log` |
| CBACT03C | READXREF.jcl | Cross-Reference Extract Pipeline | `cbact03c_xref_extract` | `silver.card_xref` | `migration_ctrl.xref_listing_log` |
| CBACT04C | INTCALC.jcl | Interest Calculation Pipeline | `cbact04c_interest_calc` | `silver.tran_cat_balance`, `silver.card_xref`, `silver.disclosure_group`, `silver.account` | `silver.transaction` (interest charges), `silver.account` (balance update) |
| CBCUS01C | READCUST.jcl | Customer File Processing Pipeline | `cbcus01c_customer_file_proc` | `silver.customer` | `migration_ctrl.customer_listing_log` |
| CBTRN01C | POSTTRAN.jcl (verification step) | Transaction Verification Pipeline | `cbtrn01c_tran_verify` | `bronze.daily_transactions`, `silver.card_xref`, `silver.account` | `migration_ctrl.verification_log` |
| CBTRN02C | POSTTRAN.jcl | Daily Transaction Posting Pipeline | `cbtrn02c_tran_posting` | `bronze.daily_transactions`, `silver.card_xref`, `silver.account`, `silver.tran_cat_balance` | `silver.transaction`, `silver.account`, `silver.tran_cat_balance`, `gold.daily_rejects` |
| CBTRN03C | TRANREPT.jcl | Transaction Category Report Pipeline | `cbtrn03c_tran_report` | `silver.transaction`, `bronze.date_parms`, `silver.card_xref`, `reference.tran_type`, `reference.tran_category` | `gold.transaction_report` |
| CBSTM03A + CBSTM03B | CREASTMT.JCL | Statement Generation Pipeline | `cbstm03_statement_gen` | `silver.card_xref`, `silver.customer`, `silver.account`, `silver.transaction` | `gold.account_statement`, `gold.account_statement_html` |
| CBEXPORT | CBEXPORT.jcl | Data Export Pipeline | `cbexport_data_export` | `silver.customer`, `silver.account`, `silver.card_xref`, `silver.transaction`, `silver.card` | `bronze.export_file` |
| CBIMPORT | CBIMPORT.jcl | Data Import Pipeline | `cbimport_data_import` | `bronze.export_file` | `silver.customer`, `silver.account`, `silver.card_xref`, `silver.transaction`, `silver.card`, `migration_ctrl.import_errors` |
| CBPAUP0C | CBPAUP0J.jcl | Authorization Purge Pipeline | `cbpaup0c_auth_purge` | `silver.auth_detail`, `silver.auth_summary` | `silver.auth_detail` (deletes), `silver.auth_summary` (deletes), `gold.auth_purge_audit` |
| PAUDBUNL | UNLDPADB.JCL | Auth DB Unload Pipeline | `paudbunl_auth_unload` | `silver.auth_summary`, `silver.auth_detail` | `bronze.auth_root_file`, `bronze.auth_child_file` |
| PAUDBLOD | LOADPADB.JCL | Auth DB Load Pipeline | `paudblod_auth_load` | `bronze.auth_root_file`, `bronze.auth_child_file` | `silver.auth_summary`, `silver.auth_detail` |
| DBUNLDGS | UNLDGSAM.JCL | GSAM Unload Pipeline | `dbunldgs_gsam_unload` | `silver.auth_summary`, `silver.auth_detail` | `bronze.auth_gsam_root`, `bronze.auth_gsam_child` |
| COBTUPDT | MNTTRDB2.jcl | Transaction Type Maintenance Pipeline | `cobtupdt_tran_type_maint` | `bronze.tran_type_input` | `reference.tran_type` |
| COACCT01 | (MQ trigger → scheduled) | Account Inquiry Service | `coacct01_account_inquiry` (streaming) | `silver.account` | `migration_ctrl.account_inquiry_responses` |
| CODATE01 | (MQ trigger → scheduled) | Date Service | `codate01_date_service` (streaming) | System clock | `migration_ctrl.date_inquiry_responses` |

---

## 7. JCL-to-Databricks Workflow Mapping

### 7.1 Daily Batch Cycle Workflow

| JCL Step (Sequence) | JCL Job | Databricks Task | Task Type | Dependency |
|--------------------|---------|-----------------|-----------|-----------|
| 1 | CLOSEFIL.jcl | `stop_streaming_jobs` | Python task | None |
| 2 | TRANBKP.jcl | `backup_transaction_delta` | Delta Live Tables snapshot | After step 1 |
| 3 | POSTTRAN.jcl (verify) | `cbtrn01c_verify_transactions` | PySpark notebook | After step 2 |
| 4 | POSTTRAN.jcl (post) | `cbtrn02c_post_transactions` | PySpark notebook | After step 3 |
| 5 | INTCALC.jcl | `cbact04c_calculate_interest` | PySpark notebook | After step 4 |
| 6 | DALYREJS.jcl | `process_daily_rejects` | PySpark notebook | After step 4 (parallel with 5) |
| 7 | CBPAUP0J.jcl | `cbpaup0c_purge_authorizations` | PySpark notebook | After step 4 |
| 8 | OPENFIL.jcl | `resume_streaming_jobs` | Python task | After steps 5, 6, 7 |

### 7.2 Monthly Statement Cycle Workflow

| JCL Step | JCL Job | Databricks Task | Task Type | Dependency |
|---------|---------|-----------------|-----------|-----------|
| 1 | CREASTMT.JCL step 1 | `cbstm03_generate_statements` | PySpark notebook | None |
| 2 | TXT2PDF1.JCL | `convert_statements_to_pdf` | Python task (PDF lib) | After step 1 |
| 3 | TRANREPT.jcl | `cbtrn03c_transaction_report` | PySpark notebook | After step 1 |
| 4 | PRTCATBL.jcl | `print_catalog` | Python task | After step 3 |

### 7.3 Data Exchange Workflow

| JCL Step | JCL Job | Databricks Task | Task Type | Dependency |
|---------|---------|-----------------|-----------|-----------|
| 1 | CBEXPORT.jcl | `cbexport_export_entities` | PySpark notebook | None |
| 2 | FTPJCL.JCL | `transfer_export_file` | Python task | After step 1 |

### 7.4 Authorization Database Maintenance Workflow

| JCL Step | JCL Job | Databricks Task | Task Type | Dependency |
|---------|---------|-----------------|-----------|-----------|
| 1 | UNLDPADB.JCL | `paudbunl_unload_auth_db` | PySpark notebook | None |
| 2 | UNLDGSAM.JCL | `dbunldgs_unload_gsam` | PySpark notebook | Parallel with step 1 |
| 3 | LOADPADB.JCL | `paudblod_load_auth_db` | PySpark notebook | After step 1 |

### 7.5 Transaction Type Maintenance Workflow

| JCL Step | JCL Job | Databricks Task | Task Type | Dependency |
|---------|---------|-----------------|-----------|-----------|
| 1 | CREADB21.jcl | `validate_tran_type_schema` | Python task | None |
| 2 | MNTTRDB2.jcl | `cobtupdt_maintain_tran_types` | PySpark notebook | After step 1 |

### 7.6 Complete JCL Coverage (46 jobs)

| JCL Job | Migration Disposition |
|---------|----------------------|
| ACCTFILE.jcl | Replaced by Bronze Delta table DDL (one-time setup) |
| READACCT.jcl | `cbact01c_account_file_proc` workflow task |
| CARDFILE.jcl | Replaced by Bronze Delta table DDL |
| READCARD.jcl | `cbact02c_card_list_report` workflow task |
| CUSTFILE.jcl | Replaced by Bronze Delta table DDL |
| READCUST.jcl | `cbcus01c_customer_file_proc` workflow task |
| DEFCUST.jcl | Replaced by Bronze Delta table DDL |
| TRANFILE.jcl | Replaced by Bronze Delta table DDL |
| COMBTRAN.jcl | Replaced by Bronze merge task in `daily_batch_cycle` |
| POSTTRAN.jcl | Tasks `cbtrn01c_verify` + `cbtrn02c_post` in `daily_batch_cycle` |
| TRANBKP.jcl | `backup_transaction_delta` task (Delta table CLONE) |
| TRANCATG.jcl | `reference.tran_category` table load task |
| TRANIDX.jcl | Delta Z-ordering task (replaces VSAM index rebuild) |
| TRANREPT.jcl | `cbtrn03c_tran_report` task in `monthly_statement_cycle` |
| TRANTYPE.jcl | `reference.tran_type` table load task |
| DALYREJS.jcl | `process_daily_rejects` task in `daily_batch_cycle` |
| INTCALC.jcl | `cbact04c_calculate_interest` task in `daily_batch_cycle` |
| CREASTMT.JCL | `cbstm03_generate_statements` task in `monthly_statement_cycle` |
| REPTFILE.jcl | Gold Delta table partition management task |
| PRTCATBL.jcl | `print_catalog` Python task |
| TXT2PDF1.JCL | `convert_statements_to_pdf` Python task |
| CBEXPORT.jcl | `cbexport_export_entities` task in `data_exchange_export` workflow |
| CBIMPORT.jcl | `cbimport_data_import` task in `data_exchange_import` workflow |
| FTPJCL.JCL | `transfer_export_file` Python task (replaced by ADLS transfer) |
| DUSRSECJ.jcl | User security Delta table maintenance task |
| CBADMCDJ.jcl | Admin card maintenance task |
| OPENFIL.jcl | `resume_streaming_jobs` Python task |
| CLOSEFIL.jcl | `stop_streaming_jobs` Python task |
| XREFFILE.jcl | Replaced by Silver Delta table DDL |
| READXREF.jcl | `cbact03c_xref_extract` workflow task |
| WAITSTEP.jcl | Replaced by Databricks task retry policies / sleep() where needed |
| CBPAUP0J.jcl | `cbpaup0c_purge_authorizations` task in `daily_batch_cycle` |
| DBPAUTP0.jcl | `reference.auth_db_config` setup task |
| LOADPADB.JCL | `paudblod_load_auth_db` task in `auth_db_maintenance` workflow |
| UNLDPADB.JCL | `paudbunl_unload_auth_db` task in `auth_db_maintenance` workflow |
| UNLDGSAM.JCL | `dbunldgs_unload_gsam` task in `auth_db_maintenance` workflow |
| CREADB21.jcl | `validate_tran_type_schema` setup task |
| MNTTRDB2.jcl | `cobtupdt_maintain_tran_types` task in `tran_type_maintenance` workflow |
| TRANEXTR.jcl | `extract_tran_type_data` Python task |

---

## 8. Dependencies and Execution Order

### 8.1 Data Dependencies (Silver Layer)

```
bronze.acct_raw ──────────────────► silver.account
bronze.card_raw ──────────────────► silver.card
bronze.cust_raw ──────────────────► silver.customer
bronze.xref_raw ──────────────────► silver.card_xref
bronze.transact_raw ──────────────► silver.transaction
bronze.daily_transactions ────────► silver.transaction (via CBTRN02C)
silver.account ◄───────────────────── silver.tran_cat_balance (updated by CBACT04C)
```

### 8.2 Pipeline Dependency Chain

```
Ingestion Tasks:
  load_bronze_all_vsam ──► cleanse_silver_master_data
                               │
                               ▼
Daily Cycle (sequential):
  cbtrn01c_verify ──► cbtrn02c_post ──┬──► cbact04c_interest
                                      ├──► dalyrejs_process
                                      └──► cbpaup0c_auth_purge

Monthly Cycle:
  cbtrn02c_post ──► cbtrn03c_report ──► statement_pdf
  silver.account ──► cbstm03_statements ──► statement_pdf
```

### 8.3 Replacing JCL COND Logic

| Original JCL Logic | PySpark/Workflow Replacement |
|-------------------|------------------------------|
| `CBTRN02C COND=(4,GE)` — downstream step skips if rejects | Databricks task `depends_on: cbtrn02c, outcome: success`. If RC=4 (rejects), downstream is conditioned via task run_if |
| `COND=(0,EQ)` on purge step | Task `run_if: "ALL_SUCCESS"` with explicit return code check in PySpark |
| `STEP EXEC PGM=IEFBR14` (null step) | Remove entirely; Delta table DDL handles file management |
| `IF ABEND THEN notification step` | Databricks Workflow notification + email on task failure |

---

## 9. Environment and Configuration Management

### 9.1 Configuration Hierarchy

```
config/
├── pipeline_config.py          # Base configuration class
├── environments/
│   ├── dev.yaml                # Development environment
│   ├── staging.yaml            # Staging/UAT environment
│   └── prod.yaml               # Production environment
└── secrets/
    └── secret_scope_config.py  # Databricks Secret Scope references
```

### 9.2 Configuration Parameters (Replacing JCL PARM and DD Names)

| COBOL/JCL Parameter | Config Key | Type | Example Value |
|--------------------|-----------|------|---------------|
| JCL PARM date (CBACT04C) | `run_date` | String (YYYY-MM-DD) | `"2026-04-06"` |
| P-EXPIRY-DAYS (CBPAUP0C) | `auth.expiry_days` | Integer | `5` |
| P-CHKP-FREQ (CBPAUP0C) | `auth.checkpoint_freq` | Integer | `5` |
| P-DEBUG-FLAG (CBPAUP0C) | `auth.debug_enabled` | Boolean | `false` |
| WS-PAGE-SIZE (CBTRN03C) | `report.page_size` | Integer | `20` |
| WS-START-DATE/WS-END-DATE (CBTRN03C) | `report.start_date`, `report.end_date` | String | `"2026-01-01"` |
| EXPORT-BRANCH-ID (CBEXPORT) | `export.branch_id` | String | `"0001"` |
| EXPORT-REGION-CODE (CBEXPORT) | `export.region_code` | String | `"NORTH"` |
| DD ACCTFILE path | `vsam.acctfile_table` | String | `"carddemo.silver.account"` |
| DB2 subsystem (COBTUPDT) | `db2.subsystem` | String (not needed in Delta) | Replaced by Delta table path |

### 9.3 Secret Management

| Secret | Purpose | Databricks Secret Scope Key |
|--------|---------|---------------------------|
| ADLS Storage Account Key | Delta Lake storage access | `carddemo/adls_key` |
| Kafka connection string | MQ replacement (COACCT01, CODATE01) | `carddemo/kafka_conn` |
| Notification email | Job failure alerts | `carddemo/alert_email` |

---

## 10. Error Handling and Restart/Recovery Strategy

### 10.1 Error Classification

| COBOL Error Type | Databricks Equivalent | Recovery Action |
|-----------------|----------------------|-----------------|
| VSAM status '23' (key not found) | `INVALID KEY` equivalent — join produces null | Log to `migration_ctrl.error_log`; quarantine record to error Delta table |
| VSAM status non-'00'/'10' (I/O error) | Delta table read exception | Raise `IOError`; job fails; Databricks retry policy applies |
| COBOL ABEND (CEE3ABD) | Python `raise RuntimeError(...)` | Job task fails; downstream tasks blocked; notification sent |
| RETURN-CODE=4 (partial failure, CBTRN02C) | PySpark job exits with sys.exit(4) | Workflow continues but flags downstream tasks as "warning" state |
| RETURN-CODE=16 (CBPAUP0C, IMS error) | PySpark job exits with sys.exit(16) | Workflow halts all downstream tasks |

### 10.2 Restart Strategy

| Program | COBOL Restart Mechanism | Databricks Restart Mechanism |
|---------|------------------------|------------------------------|
| CBPAUP0C | IMS CHKP with checkpoint ID 'RMADnnnn' | Delta table write with idempotent merge; re-run from last committed Delta version |
| CBTRN02C | Stateless; re-run processes same DALYTRAN file | Re-run task; Delta MERGE ensures no duplicates in TRANSACT |
| CBACT04C | Stateless; re-run replaces output | OVERWRITE mode on output Delta partition |
| CBSTM03A/B | Stateless; re-run regenerates statements | OVERWRITE on statement Gold table partition |
| CBEXPORT/CBIMPORT | Stateless; re-run replaces export file | Truncate Bronze export table and re-run |

### 10.3 Idempotency Design

All pipelines are designed for idempotent re-execution:

- **INSERT operations** use Delta `MERGE INTO ... WHEN NOT MATCHED THEN INSERT`
- **UPDATE operations** use Delta `MERGE INTO ... WHEN MATCHED THEN UPDATE`
- **DELETE operations** target specific partition/key ranges using Delta DELETE
- **Partition overwrites** use `OVERWRITE mode + replaceWhere` for exact partition replacement

### 10.4 Error Quarantine Table

All records that cannot be processed (equivalent to COBOL INVALID KEY or file errors) are written to:

```sql
carddemo.migration_ctrl.error_log (
    pipeline_name STRING,
    run_id STRING,
    error_timestamp TIMESTAMP,
    error_type STRING,           -- e.g., 'INVALID_KEY', 'VALIDATION_FAIL'
    error_code STRING,           -- e.g., '100', '101', '102', '103'
    error_description STRING,
    source_record STRING,        -- JSON representation of the failing record
    run_date DATE
)
PARTITIONED BY (run_date)
```

---

## 11. Monitoring and Alerting Approach

### 11.1 Job-Level Monitoring

Each Databricks Workflow is configured with:

- **Email notifications** on task failure and job completion
- **Databricks Job Run history** for audit trail (replaces JCL MSGCLASS/SYSOUT)
- **Custom job tags** for cost attribution: `{"environment": "prod", "cycle": "daily", "migrated_from": "JCL"}`

### 11.2 Pipeline Metrics

Each pipeline writes metrics to `carddemo.migration_ctrl.pipeline_metrics`:

```sql
carddemo.migration_ctrl.pipeline_metrics (
    pipeline_name STRING,        -- e.g., 'cbtrn02c_tran_posting'
    run_id STRING,
    run_date DATE,
    records_read BIGINT,         -- Equivalent to WS-TRANSACTION-COUNT
    records_processed BIGINT,
    records_rejected BIGINT,     -- Equivalent to WS-REJECT-COUNT
    records_written BIGINT,
    return_code INT,             -- 0=success, 4=warning, 8+=error (matching COBOL RETURN-CODE)
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds DOUBLE,
    error_message STRING
)
PARTITIONED BY (run_date)
```

### 11.3 Data Quality Monitoring

Using Databricks Delta Live Tables expectations (or equivalent) to enforce:

- Row count reconciliation between source and target
- Null checks on primary key fields
- Referential integrity checks (account_id in transaction must exist in account table)
- Amount sum reconciliation for financial records

### 11.4 Alerting Thresholds

| Metric | Warning Threshold | Critical Threshold | Action |
|--------|------------------|-------------------|--------|
| Records rejected (CBTRN02C) | > 0 (RC=4 equivalent) | > 5% of total | Email + Slack alert |
| Pipeline duration | > 2x historical average | > 3x historical average | Page on-call |
| Error quarantine growth | > 100 records/day | > 1000 records/day | Incident |
| Auth purge failures (CBPAUP0C) | Any IMS error equivalent | N/A | Page on-call |
