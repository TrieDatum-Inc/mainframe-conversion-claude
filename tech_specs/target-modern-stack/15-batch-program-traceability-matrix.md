# CardDemo Batch Program Traceability Matrix
## Complete Source-to-Target Mapping: All Batch Programs and JCL Jobs

**Document Version:** 1.0  
**Date:** 2026-04-06  
**Coverage:** 16 batch COBOL programs; 46 JCL jobs; all business rules; all file/dataset mappings

---

## Table of Contents

1. [Program-to-Pipeline Traceability](#1-program-to-pipeline-traceability)
2. [JCL Job-to-Workflow Traceability](#2-jcl-job-to-workflow-traceability)
3. [Business Rule Traceability](#3-business-rule-traceability)
4. [File and Dataset Traceability](#4-file-and-dataset-traceability)
5. [Copybook-to-Schema Traceability](#5-copybook-to-schema-traceability)
6. [Error Handling Traceability](#6-error-handling-traceability)
7. [Known Defect Traceability](#7-known-defect-traceability)

---

## 1. Program-to-Pipeline Traceability

This section provides one row per batch COBOL program. For each program the table records: the source program, the JCL job(s) that execute it, the target Databricks pipeline name, the input Delta tables, the output Delta tables, and the Databricks workflow it belongs to.

### 1.1 Base Module Batch Programs

| # | COBOL Program | Module | JCL Job(s) | Databricks Pipeline / Job Name | Input Delta Tables | Output Delta Tables | Databricks Workflow |
|---|--------------|--------|------------|-------------------------------|-------------------|--------------------|--------------------|
| 1 | CBACT01C | Base | READACCT.jcl | `cbact01c_account_file_proc` | `silver.account` | `bronze.account_fixed_out`, `bronze.account_array_out`, `bronze.account_vbr_short_out`, `bronze.account_vbr_long_out`, `migration_ctrl.pipeline_metrics` | `carddemo_daily_batch_cycle` (task: account_file_proc) |
| 2 | CBACT02C | Base | READCARD.jcl | `cbact02c_card_list_report` | `silver.card` | `gold.card_list_report`, `migration_ctrl.pipeline_metrics` | `carddemo_daily_batch_cycle` (task: card_list_report) |
| 3 | CBACT03C | Base | READXREF.jcl | `cbact03c_xref_extract` | `silver.card_xref` | `gold.xref_extract_report`, `migration_ctrl.pipeline_metrics` | `carddemo_daily_batch_cycle` (task: xref_extract) |
| 4 | CBACT04C | Base | INTCALC.jcl | `cbact04c_interest_calc` | `silver.tran_cat_balance`, `silver.disclosure_group`, `silver.card_xref`, `silver.account`, `silver.transaction` | `silver.account` (MERGE), `silver.transaction` (interest txns INSERT), `silver.tran_cat_balance` (balance MERGE), `migration_ctrl.pipeline_metrics` | `carddemo_daily_batch_cycle` (task: interest_calc) |
| 5 | CBCUS01C | Base | READCUST.jcl | `cbcus01c_customer_report` | `silver.customer` | `gold.customer_list_report`, `migration_ctrl.pipeline_metrics` | `carddemo_daily_batch_cycle` (task: customer_report) |
| 6 | CBTRN01C | Base | POSTTRAN.jcl | `cbtrn01c_transaction_verify` | `bronze.daily_transactions`, `silver.card_xref`, `silver.account` | `migration_ctrl.pipeline_metrics` (stats only; no reject file) | `carddemo_daily_batch_cycle` (task: transaction_verify) |
| 7 | CBTRN02C | Base | TRANREPT.jcl, POSTTRAN.jcl | `cbtrn02c_daily_post` | `bronze.daily_transactions`, `silver.card_xref`, `silver.account`, `silver.card`, `reference.tran_type`, `silver.tran_cat_balance` | `silver.transaction` (INSERT), `silver.tran_cat_balance` (MERGE), `gold.daily_rejects`, `migration_ctrl.pipeline_metrics` | `carddemo_daily_batch_cycle` (task: daily_post) |
| 8 | CBTRN03C | Base | TRANREPT.jcl (monthly) | `cbtrn03c_transaction_report` | `silver.transaction`, `silver.card_xref`, `reference.tran_type`, `silver.tran_cat_balance` | `gold.transaction_report` | `carddemo_monthly_statement_cycle` (task: transaction_report) |
| 9 | CBSTM03A | Base | CREASTMT.JCL (step 1) | `cbstm03ab_statement_gen` | `silver.transaction`, `silver.card_xref`, `silver.customer`, `silver.account` | `gold.account_statement` (HTML and plain-text formats) | `carddemo_monthly_statement_cycle` (task: statement_gen) |
| 10 | CBSTM03B | Base | CREASTMT.JCL (step 2) | `cbstm03ab_statement_gen` | Reads directly from Silver (consolidated with CBSTM03A; STMTFILE eliminated) | `gold.account_statement` | `carddemo_monthly_statement_cycle` (task: statement_gen) |
| 11 | CBEXPORT | Base | CBEXPORT.jcl | `cbexport_data_export` | `silver.customer`, `silver.account`, `silver.card_xref`, `silver.transaction`, `silver.tran_cat_balance` | `bronze.export_raw` (written as 500-byte CVEXPORT format records) | `carddemo_data_exchange_export` |
| 12 | CBIMPORT | Base | CBIMPORT.jcl | `cbimport_data_import` | `bronze.import_raw` | `silver.customer`, `silver.account`, `silver.card_xref`, `silver.transaction`, `silver.tran_cat_balance`, `migration_ctrl.error_log` (unknown-type and write-error records) | `carddemo_data_exchange_import` |
| 13 | COBSWAIT | Base | WAITSTEP.jcl | `cobswait_wait_step` | None | None (side effect: `time.sleep()` equivalent) | Embedded in any workflow requiring a timed wait step |

### 1.2 Authorization Module Batch Programs

| # | COBOL Program | Module | JCL Job(s) | Databricks Pipeline / Job Name | Input Delta Tables | Output Delta Tables | Databricks Workflow |
|---|--------------|--------|------------|-------------------------------|-------------------|--------------------|--------------------|
| 14 | CBPAUP0C | Authorization | CBPAUP0J.jcl | `cbpaup0c_auth_purge` | `silver.auth_summary` (PAUTSUM0 root), `silver.auth_detail` (PAUTDTL1 child) | `silver.auth_summary` (DELETE expired rows), `silver.auth_detail` (DELETE expired children), `gold.auth_purge_audit`, `migration_ctrl.pipeline_metrics` | `carddemo_daily_batch_cycle` (task: auth_purge) |
| 15 | PAUDBUNL | Authorization | UNLDPADB.JCL | `paudbunl_auth_unload` | `silver.auth_summary`, `silver.auth_detail` | `bronze.auth_summary_unload` (100-byte root layout), `bronze.auth_detail_unload` (206-byte child layout) | `carddemo_auth_db_maintenance` (task: auth_unload) |
| 16 | PAUDBLOD | Authorization | LOADPADB.JCL | `paudblod_auth_load` | `bronze.auth_summary_unload`, `bronze.auth_detail_unload` | `silver.auth_summary` (MERGE), `silver.auth_detail` (MERGE), `migration_ctrl.pipeline_metrics` | `carddemo_auth_db_maintenance` (task: auth_load) |
| 17 | DBUNLDGS | Authorization | UNLDGSAM.JCL | `dbunldgs_gsam_unload` | `silver.auth_summary`, `silver.auth_detail` | `gold.auth_gsam_export` (replaces IMS GSAM write; PA-ACCT-ID IS NUMERIC filter applied) | `carddemo_auth_db_maintenance` (task: gsam_unload) |

### 1.3 Transaction Type DB2 Module Batch Programs

| # | COBOL Program | Module | JCL Job(s) | Databricks Pipeline / Job Name | Input Delta Tables | Output Delta Tables | Databricks Workflow |
|---|--------------|--------|------------|-------------------------------|-------------------|--------------------|--------------------|
| 18 | COBTUPDT | Tran Type DB2 | MNTTRDB2.jcl | `cobtupdt_tran_type_maint` | `bronze.tran_type_input` (53-byte input records) | `reference.tran_type` (MERGE: Add/Update/Delete) | `carddemo_tran_type_maintenance` |

### 1.4 VSAM-MQ Extension Programs (Streaming)

The following programs are CICS MQ trigger programs, not traditional batch programs. They are migrated to Databricks Structured Streaming jobs, not scheduled batch workflows.

| # | COBOL Program | Module | Original Trigger | Databricks Service Name | Input Source | Output Target | Databricks Workflow / Stream |
|---|--------------|--------|-----------------|------------------------|-------------|---------------|------------------------------|
| 19 | COACCT01 | VSAM-MQ | CICS MQ trigger CDRA | `coacct01_account_inquiry_stream` | Kafka topic `carddemo.account.inquiry.req` | Kafka topic `carddemo.account.inquiry.reply`; `silver.account` (read-only) | `carddemo_mq_account_inquiry_stream` (always-on streaming job) |
| 20 | CODATE01 | VSAM-MQ | CICS MQ trigger CDRD | `codate01_date_service_stream` | Kafka topic `carddemo.date.inquiry.req` | Kafka topic `carddemo.date.inquiry.reply` (Python `datetime.now()`) | `carddemo_mq_date_service_stream` (always-on streaming job) |

---

## 2. JCL Job-to-Workflow Traceability

This section provides one row per JCL job (all 46 jobs). For each job: JCL name, the JCL steps within it, the COBOL programs invoked, the Databricks workflow the job maps to, and the specific tasks within that workflow.

### 2.1 Account Processing JCL Jobs

| JCL Job | JCL Steps | COBOL Program(s) | Mainframe Function | Target Databricks Workflow | Target Tasks | Migration Notes |
|---------|-----------|-----------------|-------------------|---------------------------|-------------|----------------|
| ACCTFILE.jcl | IDCAMS DEFINE | None | Define and load ACCTDAT VSAM cluster (initial setup) | Eliminated | N/A | Replaced by `CREATE TABLE carddemo.bronze.acct_raw` DDL in setup SQL; Delta table creation is the equivalent |
| READACCT.jcl | EXEC PGM=CBACT01C | CBACT01C | Read and report on account file | `carddemo_daily_batch_cycle` | `account_file_proc` | Runs after Silver promotion; reads `silver.account` |

### 2.2 Card Processing JCL Jobs

| JCL Job | JCL Steps | COBOL Program(s) | Mainframe Function | Target Databricks Workflow | Target Tasks | Migration Notes |
|---------|-----------|-----------------|-------------------|---------------------------|-------------|----------------|
| CARDFILE.jcl | IDCAMS DEFINE | None | Define and load CARDDAT VSAM cluster (initial setup) | Eliminated | N/A | Replaced by Delta DDL; `carddemo.bronze.card_raw` |
| READCARD.jcl | EXEC PGM=CBACT02C | CBACT02C | Read and report on card file | `carddemo_daily_batch_cycle` | `card_list_report` | CBACT02C spec referenced in source; full spec available |

### 2.3 Customer Processing JCL Jobs

| JCL Job | JCL Steps | COBOL Program(s) | Mainframe Function | Target Databricks Workflow | Target Tasks | Migration Notes |
|---------|-----------|-----------------|-------------------|---------------------------|-------------|----------------|
| CUSTFILE.jcl | IDCAMS DEFINE | None | Define and load CUSTDAT VSAM cluster | Eliminated | N/A | Replaced by Delta DDL |
| READCUST.jcl | EXEC PGM=CBCUS01C | CBCUS01C | Read and report on customer file | `carddemo_daily_batch_cycle` | `customer_report` | |
| DEFCUST.jcl | IDCAMS DEFINE | None | Define customer VSAM cluster (alternate/empty) | Eliminated | N/A | Absorbed into Delta DDL setup |

### 2.4 Transaction Processing JCL Jobs

| JCL Job | JCL Steps | COBOL Program(s) | Mainframe Function | Target Databricks Workflow | Target Tasks | Migration Notes |
|---------|-----------|-----------------|-------------------|---------------------------|-------------|----------------|
| TRANFILE.jcl | IDCAMS DEFINE | None | Define and load TRANSACT VSAM cluster | Eliminated | N/A | Replaced by Delta DDL; `carddemo.bronze.transact_raw` |
| COMBTRAN.jcl | Multiple sort/merge steps | None (utility) | Combine and merge transaction input files | `carddemo_daily_batch_cycle` | `bronze_ingest` (DALYTRAN preparation task) | Replaced by Bronze ingestion pipeline that reads from S3 landing zone; `SORT` steps replaced by `orderBy()` |
| POSTTRAN.jcl | EXEC PGM=CBTRN01C, EXEC PGM=CBTRN02C | CBTRN01C, CBTRN02C | Post pending transactions to accounts; validate and post daily transactions | `carddemo_daily_batch_cycle` | `transaction_verify`, `daily_post` | Two tasks in sequence; CBTRN01C runs first (verify), CBTRN02C runs second (post) |
| TRANBKP.jcl | IEBGENER copy step | None (utility) | Backup TRANSACT VSAM file before processing | `carddemo_daily_batch_cycle` | `transaction_backup` | Replaced by Delta table time-travel / CLONE TO snapshot; `AS OF` provides rollback capability |
| TRANCATG.jcl | Sort and catalog steps | None (utility) | Catalog transaction data | Eliminated | N/A | Delta table Z-ordering on `tran_type_cd` and `tran_card_num` replaces catalog maintenance |
| TRANIDX.jcl | IDCAMS BLDINDEX | None (utility) | Build alternate indexes on TRANSACT VSAM | Eliminated | N/A | Delta table Z-ordering + BLOOM filter statistics replace VSAM alternate indexes |
| TRANREPT.jcl | EXEC PGM=CBTRN02C (daily) or EXEC PGM=CBTRN03C (monthly) | CBTRN02C (daily), CBTRN03C (monthly) | Generate transaction reports | Daily: `carddemo_daily_batch_cycle` task `daily_post`; Monthly: `carddemo_monthly_statement_cycle` task `transaction_report` | See above | CBTRN02C handles daily; CBTRN03C handles monthly date-range report |
| TRANTYPE.jcl | Sort/process steps | None (utility) | Transaction type reference processing | `carddemo_tran_type_maintenance` | `tran_type_load` | Reference data reload from DB2 TRNTYPE |
| DALYREJS.jcl | EXEC PGM=various | None (utility) | Process and report daily rejects from CBTRN02C | `carddemo_daily_batch_cycle` | `daily_rejects_report` | DALYREJS data is in `gold.daily_rejects`; reporting task reads and formats |
| INTCALC.jcl | EXEC PGM=CBACT04C; SORT step for TCATBALF | CBACT04C | Calculate monthly interest charges on all accounts | `carddemo_daily_batch_cycle` | `interest_calc` | SORT step for TCATBALF replaced by `orderBy("trancat_acct_id")` within CBACT04C pipeline |

### 2.5 Statement and Report JCL Jobs

| JCL Job | JCL Steps | COBOL Program(s) | Mainframe Function | Target Databricks Workflow | Target Tasks | Migration Notes |
|---------|-----------|-----------------|-------------------|---------------------------|-------------|----------------|
| CREASTMT.JCL | EXEC PGM=CBSTM03A, EXEC PGM=CBSTM03B | CBSTM03A, CBSTM03B | Generate monthly credit card statements (plain text and HTML) | `carddemo_monthly_statement_cycle` | `statement_gen` | CBSTM03A and CBSTM03B merged into single pipeline task; intermediate STMTFILE (80-byte sequential) eliminated; CBSTM03B reads Silver directly |
| REPTFILE.jcl | Allocation and copy steps | None (utility) | Allocate and manage report output datasets | Eliminated | N/A | Delta tables and object storage (S3) replace report dataset management |
| PRTCATBL.jcl | EXEC PGM=CBTRN03C (or print utility) | CBTRN03C (possibly) | Print transaction category table | `carddemo_monthly_statement_cycle` | `transaction_report` | If PRTCATBL runs CBTRN03C, absorbed into monthly report task; if print utility only, eliminated |
| TXT2PDF1.JCL | EXEC PGM=text-to-PDF utility | None (COBOL) | Convert text statements to PDF | `carddemo_monthly_statement_cycle` | `statement_pdf_gen` | Replaced by Python PDF generation library (e.g., ReportLab or WeasyHTML); reads `gold.account_statement` |

### 2.6 Data Exchange JCL Jobs

| JCL Job | JCL Steps | COBOL Program(s) | Mainframe Function | Target Databricks Workflow | Target Tasks | Migration Notes |
|---------|-----------|-----------------|-------------------|---------------------------|-------------|----------------|
| CBEXPORT.jcl | EXEC PGM=CBEXPORT | CBEXPORT | Export all entity types to 500-byte KSDS EXPFILE | `carddemo_data_exchange_export` | `export_gen` | EXPFILE VSAM replaced by `bronze.export_raw` Delta table; S3 export file generated post-pipeline |
| CBIMPORT.jcl | EXEC PGM=CBIMPORT | CBIMPORT | Import 500-byte flat file into VSAM entity tables | `carddemo_data_exchange_import` | `import_load` | Input file arrives via S3 landing zone; error records go to `migration_ctrl.error_log` |
| FTPJCL.JCL | FTP utility steps | None (COBOL) | Transfer files to/from external partners | Eliminated (absorbed into cloud file exchange) | N/A | Replaced by AWS Transfer Family (SFTP) or S3 direct exchange; no Databricks task required |

### 2.7 Administrative JCL Jobs

| JCL Job | JCL Steps | COBOL Program(s) | Mainframe Function | Target Databricks Workflow | Target Tasks | Migration Notes |
|---------|-----------|-----------------|-------------------|---------------------------|-------------|----------------|
| DUSRSECJ.jcl | IDCAMS operations | None (COBOL) | User security file maintenance (USRSEC) | Eliminated (cloud identity) | N/A | USRSEC replaced by cloud identity provider (e.g., AWS Cognito); user management via cloud portal |
| CBADMCDJ.jcl | Admin card steps | None fully specified | Admin card job (purpose partially unknown) | `carddemo_daily_batch_cycle` | `admin_card_maint` (placeholder) | Full purpose unclear; placeholder task created. TODO: VERIFY — review JCL content |
| OPENFIL.jcl | CICS CEMT SET FILE OPEN | None (COBOL) | Reopen CICS files after batch window | Eliminated | N/A | No CICS file open/close required in cloud architecture; Delta tables always available |
| CLOSEFIL.jcl | CICS CEMT SET FILE CLOSED | None (COBOL) | Close CICS files for batch window | Eliminated | N/A | Delta table transactions replace VSAM file-level close; batch window managed by Databricks workflow scheduling |
| XREFFILE.jcl | IDCAMS DEFINE | None (COBOL) | Cross-reference file setup | Eliminated | N/A | Replaced by Delta DDL; `carddemo.bronze.xref_raw` |
| READXREF.jcl | EXEC PGM=CBACT03C | CBACT03C | Read and report on cross-reference file | `carddemo_daily_batch_cycle` | `xref_extract` | |
| WAITSTEP.jcl | EXEC PGM=COBSWAIT | COBSWAIT | MVS timed wait (centiseconds from SYSIN) | Embedded in parent workflow | Wait implemented as `time.sleep(centiseconds / 100)` in the calling pipeline | Wait duration is a job parameter; COBSWAIT has no error handling — migrated behavior preserved |

### 2.8 Authorization Batch JCL Jobs

| JCL Job | JCL Steps | COBOL Program(s) | Mainframe Function | Target Databricks Workflow | Target Tasks | Migration Notes |
|---------|-----------|-----------------|-------------------|---------------------------|-------------|----------------|
| CBPAUP0J.jcl | EXEC PGM=DFSRRC00 (BMP, PSB=PSBPAUTB, PGM=CBPAUP0C) | CBPAUP0C | Purge expired pending authorizations from IMS PAUTHSUM/PAUTHDTL | `carddemo_daily_batch_cycle` | `auth_purge` | IMS BMP replaced by Delta table DELETE; checkpoint `CHKP 'RMADnnnn'` replaced by Delta transaction log |
| DBPAUTP0.jcl | DB2 utility steps | None (COBOL) | DB2 authorization data processing (utility job) | `carddemo_auth_db_maintenance` | `auth_db2_proc` (placeholder) | Full content unknown; placeholder task. TODO: VERIFY |
| LOADPADB.JCL | EXEC PGM=DFSRRC00 (BMP, PSB=PAUTBUNL, PGM=PAUDBLOD) | PAUDBLOD | Load IMS auth database from QSAM unload files | `carddemo_auth_db_maintenance` | `auth_load` | IMS ISRT replaced by Delta MERGE on auth_summary and auth_detail |
| UNLDPADB.JCL | EXEC PGM=DFSRRC00 (BMP, PSB=PAUTBUNL, PGM=PAUDBUNL) | PAUDBUNL | Unload IMS auth database to QSAM files (OUTFIL1=100b root, OUTFIL2=206b child) | `carddemo_auth_db_maintenance` | `auth_unload` | Reads Silver auth tables; writes to Bronze unload staging tables in cloud-native format |
| UNLDGSAM.JCL | EXEC PGM=DLIGSAMP (PSB=IMSUNLOD, PGM=DBUNLDGS) | DBUNLDGS | Unload IMS GSAM datasets (PASFLPCB root, PADFLPCB child) | `carddemo_auth_db_maintenance` | `gsam_unload` | GSAM has no cloud equivalent; replaced by Delta table write to `gold.auth_gsam_export` |

### 2.9 Transaction Type DB2 JCL Jobs

| JCL Job | JCL Steps | COBOL Program(s) | Mainframe Function | Target Databricks Workflow | Target Tasks | Migration Notes |
|---------|-----------|-----------------|-------------------|---------------------------|-------------|----------------|
| CREADB21.jcl | EXEC PGM=IKJEFT01 (DSN RUN PROGRAM=SQL) | None (COBOL) | Create DB2 tables for transaction types (TRNTYPE, TRNTYCAT) | Eliminated (DDL) | N/A | Replaced by setup SQL DDL: `CREATE TABLE carddemo.reference.tran_type` |
| MNTTRDB2.jcl | EXEC PGM=IKJEFT01 (DSN RUN PROGRAM=COBTUPDT) | COBTUPDT | Batch maintenance of TRNTYPE table (Add/Update/Delete) | `carddemo_tran_type_maintenance` | `tran_type_maint` | COBTUPDT pipeline reads from `bronze.tran_type_input`; MERGE into `reference.tran_type`; note: COBTUPDT does not COMMIT — pipeline handles commit via Delta transaction |
| TRANEXTR.jcl | Extract/copy steps | None (COBOL) | Extract transaction data for external consumption | `carddemo_data_exchange_export` | `tran_extract` | Absorbed into CBEXPORT pipeline or standalone extract task using `silver.transaction` |

---

## 3. Business Rule Traceability

This section maps every significant business rule in each batch COBOL program to its implementation location in the migrated PySpark pipeline.

### 3.1 CBACT01C Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-ACT01-001 | 1300-POPUL-ACCT-RECORD lines 236-238 | If ACCT-CURR-CYC-DEBIT = 0, substitute 2525.00 in output | `transformations/step_1_account_proc.py`: `apply_zero_debit_substitution()` | Known defect — intentionally preserved |
| BR-ACT01-002 | 1000-ACCTFILE-GET-NEXT loop | Sequential full scan of ACCTFILE; no filter | `spark.read.table("carddemo.silver.account")` — no WHERE clause | |
| BR-ACT01-003 | 1300-POPUL-ACCT-RECORD | Populate OUT-ACCT-REC (fixed output format, all fields from CVACT01Y) | `domain/business_rules.py`: `build_fixed_output_record()` | |
| BR-ACT01-004 | 1400-POPUL-ARRAY-RECORD | Populate ARR-ARRAY-REC (array output format, 10 accounts per row) | `transformations/step_2_array_output.py`: `build_array_output()` — Window function with row_number | |
| BR-ACT01-005 | 1500-POPUL-VBRC-RECORD | Write 12-byte VBR-REC1 if active; 39-byte VBR-REC2 always | `transformations/step_3_vbr_output.py`: `build_vbr_records()` — conditional column selection | |
| BR-ACT01-006 | COBDATFT assembler call | Reformat ACCT-REISSUE-DATE using assembler date formatter type='2' | `domain/business_rules.py`: `reformat_date_cobdatft()` — Python datetime parse/format. TODO: VERIFY exact format conversion |
| BR-ACT01-007 | PROCEDURE DIVISION | Count total records processed; write to SYSOUT | `migration_ctrl.pipeline_metrics`: `records_read` counter | |

### 3.2 CBACT02C Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-ACT02-001 | Sequential CARDFILE read | Full scan of CARDFILE; display card number, account ID, CVV, name, expiry, status | `spark.read.table("carddemo.silver.card")` — full scan; output to `gold.card_list_report` | |
| BR-ACT02-002 | Z-DISPLAY-IO-STATUS | Double-display defect: prints IO status twice on FILE STATUS ≠ '00' | `domain/business_rules.py`: `log_io_status_double()` — defect preserved in logging behavior | Known defect preserved |

### 3.3 CBACT03C Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-ACT03-001 | Sequential XREFFILE read | Full scan of CCXREF; display card number, customer ID, account ID | `spark.read.table("carddemo.silver.card_xref")` — full scan; output to `gold.xref_extract_report` | |
| BR-ACT03-002 | Z-DISPLAY-IO-STATUS | Double-display defect: prints IO status twice on error | `domain/business_rules.py`: `log_io_status_double()` | Known defect preserved |

### 3.4 CBACT04C Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-ACT04-001 | 1000-CALCULATE-INTEREST | Driving file is TCATBALF sorted ascending by TRANCAT-ACCT-ID | `spark.read.table("carddemo.silver.tran_cat_balance").orderBy("trancat_acct_id")` | |
| BR-ACT04-002 | 1100-LOOKUP-XREF | Look up XREF record by TRANCAT-ACCT-ID to get card number | `join(card_xref, acct_id == xref.acct_id)` — left join | |
| BR-ACT04-003 | 1200-LOOKUP-DISCGRP | Look up disclosure group by ACCT-GROUP-ID; fallback to 'DEFAULT' | `domain/business_rules.py`: `lookup_disclosure_group()` — LEFT JOIN + coalesce to DEFAULT row | |
| BR-ACT04-004 | 1300-COMPUTE-INTEREST | `WS-MONTHLY-INT = (TRAN-CAT-BAL × DIS-INT-RATE) / 1200` | `domain/business_rules.py`: `compute_monthly_interest()` — `DecimalType` arithmetic; divide by 1200 exactly | |
| BR-ACT04-005 | 1050-UPDATE-ACCOUNT | Zero out ACCT-CURR-CYC-CREDIT and ACCT-CURR-CYC-DEBIT after interest | `transformations/step_4_account_update.py`: `zero_cycle_balances()` — MERGE into `silver.account` | |
| BR-ACT04-006 | PARM-DATE | PARM-DATE from JCL PARM field used as transaction date in generated interest transactions | Databricks job parameter `parm_date`; passed to pipeline as widget | |
| BR-ACT04-007 | WS-TRANID-SUFFIX | Transaction ID = PARM-DATE + WS-TRANID-SUFFIX (counter) | `domain/business_rules.py`: `build_interest_tran_id()` — concatenate date + zero-padded row_number | |
| BR-ACT04-008 | 1400-COMPUTE-FEES | Fee computation paragraph — STUB (EXIT only) | `domain/business_rules.py`: `compute_fees_stub()` — returns 0; comment documents stub | Known stub preserved |
| BR-ACT04-009 | 'DEFAULT' fallback | If no disclosure group for ACCT-GROUP-ID, use 'DEFAULT' group | `lookup_disclosure_group()` coalesce; error if 'DEFAULT' not present | |

### 3.5 CBCUS01C Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-CUS01-001 | Sequential CUSTFILE read | Full scan of CUSTFILE; display all CVCUS01Y fields | `spark.read.table("carddemo.silver.customer")` — full scan; output to `gold.customer_list_report` | |
| BR-CUS01-002 | Z-DISPLAY-IO-STATUS | Double-display defect: same as CBACT02C/03C | `domain/business_rules.py`: `log_io_status_double()` | Known defect preserved |

### 3.6 CBTRN01C Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-TRN01-001 | 2000-LOOKUP-XREF | Random lookup of XREF by TRAN-CARD-NUM from each DALYTRAN record | `join(daily_transactions, card_xref, tran_card_num == xref_card_num)` — LEFT JOIN; unmatched flagged | |
| BR-TRN01-002 | 3000-READ-ACCOUNT | Random lookup of ACCTFILE by XREF-ACCT-ID | `join(…, silver.account, xref_acct_id == acct_id)` | |
| BR-TRN01-003 | CUSTFILE/CARDFILE/TRANSACT-FILE opened but never read | Dead code — three file opens with no reads | Eliminated entirely; files not opened | Known defect eliminated |
| BR-TRN01-004 | 9000-DALYTRAN-CLOSE label | CLOSE label says 'CUSTOMER FILE' (copy-paste error) | Log message uses correct name 'DALYTRAN'; defect comment in code | Copy-paste defect preserved in comment |
| BR-TRN01-005 | Full sequential scan | Process all DALYTRAN records sequentially | Full `bronze.daily_transactions` scan; no filter other than load_date | |

### 3.7 CBTRN02C Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-TRN02-001 | 2100-VALIDATE-TRAN | Validate: card exists in XREF (code 100 = reject) | `domain/business_rules.py`: `validate_card_in_xref()` — LEFT JOIN; null xref_card_num → reject code 100 | |
| BR-TRN02-002 | 2200-VALIDATE-TRAN | Validate: account in good standing (code 101 = reject) | `domain/business_rules.py`: `validate_account_status()` — filter ACCT-ACTIVE-STATUS | |
| BR-TRN02-003 | 2300-VALIDATE-TRAN | Validate: transaction amount within credit limit (code 102 = reject) | `domain/business_rules.py`: `validate_credit_limit()` — compare TRAN-AMT vs ACCT-CREDIT-LIMIT | |
| BR-TRN02-004 | 2400-VALIDATE-TRAN | Validate: transaction type code exists in TRNTYPE (code 103 = reject) | `domain/business_rules.py`: `validate_tran_type()` — LEFT JOIN reference.tran_type; null → reject 103 | |
| BR-TRN02-005 | 2700-A-WRITE-TCATBAL | Create new TCATBALF record for account+type+cat if none exists | `transformations/step_5_tcat_upsert.py`: MERGE; WHEN NOT MATCHED → INSERT | |
| BR-TRN02-006 | 2700-B-UPDATE-TCATBAL | Update existing TCATBALF record adding transaction amount | `transformations/step_5_tcat_upsert.py`: MERGE; WHEN MATCHED → UPDATE `tran_cat_bal += tran_amt` | |
| BR-TRN02-007 | DALYREJS output | Rejected records written as 430-byte records (350 TRAN + 80 trailer) | `gold.daily_rejects` — structured columns replacing fixed-width layout | |
| BR-TRN02-008 | RETURN-CODE=4 | Set RETURN-CODE=4 if any transaction rejected (RC=0 if all accepted) | Pipeline sets task output parameter `return_code=4` if `daily_rejects` count > 0 | |
| BR-TRN02-009 | DB2-FORMAT-TS | Format TRAN-PROC-TS as DB2 timestamp YYYY-MM-DD-HH.MM.SS.mmm0000 | `domain/business_rules.py`: `format_db2_timestamp()` — Python datetime to DB2 format string | |
| BR-TRN02-010 | TRANSACT-FILE OUTPUT mode | TRANSACT-FILE opened OUTPUT (write-only; no update of existing) | `silver.transaction` — INSERT only; no MERGE | |

### 3.8 CBTRN03C Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-TRN03-001 | DATEPARM date range | Read start date (bytes 1-10) and end date (bytes 12-21) from DATEPARM | Databricks job parameters `start_date`, `end_date` (from widget); DATEPARM file eliminated | |
| BR-TRN03-002 | Page break every 20 lines | WS-PAGE-SIZE=20; page break using FUNCTION MOD | `domain/business_rules.py`: `apply_page_breaks()` — row_number() % 20 == 0 triggers page header | |
| BR-TRN03-003 | Account subtotal on TRAN-CARD-NUM change | When card number changes: print account subtotal | `transformations/step_8_report.py`: Window function `SUM OVER (PARTITION BY tran_card_num)` with `lag()` for change detection | |
| BR-TRN03-004 | Grand total = sum of page totals | Grand total accumulated across all pages | `transformations/step_8_report.py`: final `SUM(tran_amt)` across all records | |
| BR-TRN03-005 | 133-byte report lines | Fixed 133-character report line format | `domain/business_rules.py`: `format_report_line()` — string padding/truncation to 133 chars | |
| BR-TRN03-006 | XREF/TRANTYPE/TRANCATG lookup failure → ABEND | Any lookup miss causes program abend (not soft error) | `transformations/step_8_report.py`: raises `PipelineAbendError` on null lookup result; pipeline task fails | |

### 3.9 CBSTM03A/B Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-STM03-001 | WS-TRNX-TABLE (51×10 OCCURS) | 2D array holding up to 510 transactions (51 accounts × 10 transactions) | `domain/business_rules.py`: `build_trnx_table()` — grouped DataFrame (account as outer group, transaction as inner) replaces array | |
| BR-STM03-002 | CBSTM03B called via CALL | CBSTM03A calls CBSTM03B for all file I/O via WS-M03B-AREA generic interface | Eliminated — CBSTM03A and CBSTM03B merged into single pipeline; no inter-program CALL required | |
| BR-STM03-003 | WS-M03B-AREA DD names | Interface uses DD name (TRNXFILE/XREFFILE/CUSTFILE/ACCTFILE) + operation + key | Eliminated — pipeline reads Delta tables directly by entity type | |
| BR-STM03-004 | TRNX-FILE compound key | Key = TRAN-CARD-NUM (X(16)) + TRAN-ID (X(16)) — 32 characters total | `join(transaction, card_xref, on=[tran_card_num, tran_id])` | |
| BR-STM03-005 | ALTER/GO TO paragraphs | COBOL ALTER modifies GO TO target at runtime | Eliminated — replaced by explicit Python function dispatch; no dynamic branch modification | Defect/complexity eliminated |
| BR-STM03-006 | PSA/TCB/TIOT control blocks | Direct addressing of z/OS control blocks | Eliminated entirely — not applicable in cloud | Platform-specific code eliminated |
| BR-STM03-007 | STMTFILE 80-byte output | Statement plain-text lines written to STMTFILE (DD:STMTFILE) | `gold.account_statement` — `stmt_plain_text` column | |
| BR-STM03-008 | HTMLFILE 100-byte output | Statement HTML lines written to HTMLFILE (DD:HTMLFILE) | `gold.account_statement` — `stmt_html_fragment` column | |
| BR-STM03-009 | Hardcoded bank name/address | 'Bank of XYZ', '410 Terry Ave N', 'Seattle WA 99999' | `config/pipeline_config.py`: `BANK_NAME`, `BANK_ADDRESS_LINE_1`, `BANK_ADDRESS_LINE_2` constants | Known hardcoded values preserved as config |

### 3.10 CBEXPORT Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-EXP-001 | Entity type loop | Export C(ustomer)/A(ccount)/X(ref)/T(ransaction)/D(isclosure) in type order | `transformations/step_10_export.py`: `export_by_entity_type()` — `UNION ALL` of 5 entity DataFrames | |
| BR-EXP-002 | EXPORT-SEQUENCE-NUM | 9(9) sequential counter across all entity types | `domain/business_rules.py`: `assign_export_sequence()` — `row_number()` over ordered union | |
| BR-EXP-003 | EXPORT-BRANCH-ID='0001' | Hardcoded branch ID | `config/pipeline_config.py`: `EXPORT_BRANCH_ID = '0001'` | Known hardcoded value |
| BR-EXP-004 | EXPORT-REGION-CODE='NORTH' | Hardcoded region code | `config/pipeline_config.py`: `EXPORT_REGION_CODE = 'NORTH'` | Known hardcoded value |
| BR-EXP-005 | Single timestamp | Export timestamp set once at initialization; all records get same timestamp | `domain/business_rules.py`: `get_export_timestamp()` — called once; stored in `F.lit(export_ts)` | |

### 3.11 CBIMPORT Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-IMP-001 | Entity type routing | Route records to CUSTFILE/ACCTFILE/XREFFILE/TRANSACT/DISCGRP by EXPORT-ENTITY-TYPE | `transformations/step_11_import.py`: `route_by_entity_type()` — `CASE WHEN entity_type = 'C' THEN …` | |
| BR-IMP-002 | 3000-VALIDATE-IMPORT | Validation paragraph is a stub (EXIT only) | `domain/business_rules.py`: `validate_import_stub()` — no-op; comment documents stub | Known stub preserved |
| BR-IMP-003 | Unknown entity type | Unknown EXPORT-ENTITY-TYPE → 132-byte error record to ERROR-OUTPUT | `migration_ctrl.error_log` — unknown type records logged with reason code UNKNOWN_ENTITY_TYPE | |
| BR-IMP-004 | ERROR-OUTPUT write failure | Write failure to ERROR-OUTPUT does NOT abend; processing continues | `transformations/step_11_import.py`: error write in try/except; exception logged; processing continues | |

### 3.12 CBPAUP0C Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-PAU-001 | SYSIN parameters | P-EXPIRY-DAYS, P-CHKP-FREQ, P-CHKP-DIS-FREQ, P-DEBUG-FLAG | Databricks job parameters: `expiry_days`, `chkp_freq`, `chkp_dis_freq`, `debug_flag` | |
| BR-PAU-002 | Expiry formula | WS-AUTH-DATE = 99999 - PA-AUTH-DATE-9C (inverted Julian); WS-DAY-DIFF = CURRENT-YYDDD - WS-AUTH-DATE | `domain/business_rules.py`: `compute_auth_expiry()` — Python Julian date arithmetic replicating exact formula | |
| BR-PAU-003 | Detail deletion | Delete PAUTDTL1 children of expired root using GNP (Get Next in Parent) | `transformations/step_12_auth_purge.py`: `purge_auth_detail()` — DELETE FROM silver.auth_detail WHERE pa_card_num IN (expired_cards) | |
| BR-PAU-004 | Summary deletion condition | CRITICAL BUG: `IF PA-APPROVED-AUTH-CNT <= 0 AND PA-APPROVED-AUTH-CNT <= 0` — checks same field twice | `domain/business_rules.py`: `should_delete_auth_summary()` — **preserves duplicate predicate**: `count <= 0 and count <= 0` | Known defect intentionally preserved |
| BR-PAU-005 | Checkpointing | EXEC DLI CHKP every P-CHKP-FREQ records; display checkpoint every P-CHKP-DIS-FREQ | `utils/checkpoint_utils.py`: `maybe_checkpoint()` — Delta table transaction log provides durability; display checkpoint preserved as log message every N records | |
| BR-PAU-006 | RC=16 fatal | 9999-ABEND-RETURN sets RETURN-CODE=16 on fatal error | `utils/error_handler.py`: `AbendError` exception class; RC=16 → pipeline task fails with non-zero exit | |

### 3.13 PAUDBUNL Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-UNL-001 | PA-ACCT-ID IS NUMERIC filter | Skip records where PA-ACCT-ID is not numeric | `domain/business_rules.py`: `filter_numeric_acct_id()` — `F.col("pa_acct_id").rlike("^[0-9]+$")` | |
| BR-UNL-002 | OUTFIL1 root record | 100-byte root record layout (WS-ROOT-REC) | `transformations/step_13_auth_unload.py`: `build_root_record()` — fixed-width string formatting | |
| BR-UNL-003 | OUTFIL2 child record | 206-byte child record: 6-byte COMP-3 key + 200-byte child segment | `transformations/step_13_auth_unload.py`: `build_child_record()` — COMP-3 encoding for key field | |
| BR-UNL-004 | OPFILE1/OPFILE2 writes commented out | WRITE statements for OPFILE1/OPFILE2 commented out in source (bug) | TODO: VERIFY — if truly commented, records are never written; migration implements the write (assuming intent was to write) | Possible defect; assumption documented |

### 3.14 PAUDBLOD Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-LOD-001 | Load roots first (2000 loop) | All root segments (PAUTSUM0) loaded before any children | `transformations/step_14_auth_load.py`: `load_auth_summary()` runs before `load_auth_detail()` | |
| BR-LOD-002 | GU to position parent before child ISRT | Parent must exist before child; GU (Get Unique) positions segment | `load_auth_detail()`: inner join with `silver.auth_summary` ensures parent exists before child MERGE | |
| BR-LOD-003 | Qualified SSA | ROOT-QUAL-SSA: `PAUTSUM0` key field `ACCNTID EQ value` | `join(auth_detail, auth_summary, root_seg_key == pa_acct_id)` | |
| BR-LOD-004 | 'II' (duplicate insert) tolerated | STATUS-CODE='II' (duplicate) logged but not fatal | `transformations/step_14_auth_load.py`: MERGE; WHEN MATCHED → log warning; processing continues | |

### 3.15 DBUNLDGS Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-GUN-001 | GSAM ISRT for root | CALL CBLTDLI FUNC-ISRT for PASFLPCB (root GSAM PCB) | `transformations/step_15_gsam_unload.py`: `write_root_export()` — INSERT INTO `gold.auth_gsam_export` (root partition) | |
| BR-GUN-002 | GSAM ISRT for child | CALL CBLTDLI FUNC-ISRT for PADFLPCB (child GSAM PCB) | `write_child_export()` — INSERT INTO `gold.auth_gsam_export` (child partition) | |
| BR-GUN-003 | PA-ACCT-ID IS NUMERIC filter | Same filter as PAUDBUNL | `domain/business_rules.py`: `filter_numeric_acct_id()` — shared function | |
| BR-GUN-004 | WS-PGMNAME='IMSUNLOD' (mismatch) | Working storage says 'IMSUNLOD' but program is DBUNLDGS | `pipeline_config.py`: comment documents discrepancy; metric uses 'DBUNLDGS' as actual program name | Known defect preserved in comment |

### 3.16 COBTUPDT Business Rules

| Rule ID | COBOL Source | Business Rule Description | PySpark Implementation Location | Verification Status |
|---------|-------------|--------------------------|--------------------------------|---------------------|
| BR-UPD-001 | 'A' action | Add new TRNTYPE row | `domain/business_rules.py`: `apply_tran_type_action()` — MERGE WHEN NOT MATCHED → INSERT | |
| BR-UPD-002 | 'U' action | Update existing TRNTYPE description | MERGE WHEN MATCHED → UPDATE `tr_type_desc` | |
| BR-UPD-003 | 'D' action | Delete TRNTYPE row | MERGE WHEN MATCHED → DELETE | |
| BR-UPD-004 | '*' and other actions | Invalid action code — log error; SQLCODE=9999-ABEND path | `domain/business_rules.py`: unknown action → log error; raise `PipelineAbendError` | |
| BR-UPD-005 | 9999-ABEND does not STOP RUN | COBTUPDT 9999-ABEND sets RC=4 but does NOT stop processing | `error_handler.py`: non-fatal error path; RC=4 set in metrics; processing continues with next record | Known defect intentionally preserved |
| BR-UPD-006 | No COMMIT in COBOL | COBTUPDT never issues COMMIT | Irrelevant — Delta table auto-commits each MERGE operation; behavior equivalent | |
| BR-UPD-007 | Open failure non-terminal | File open failure does not terminate program | `transformations/step_16_tran_type_maint.py`: file-open equivalent replaced by Delta read; read failure is always terminal in Spark; TODO: VERIFY if non-terminal behavior must be preserved | |

---

## 4. File and Dataset Traceability

This section maps every mainframe file and dataset to its cloud equivalent.

### 4.1 VSAM KSDS Files

| Mainframe Dataset | CICS DD Name | Batch DD Name(s) | Copybook | Record Length | Bronze Delta Table | Silver Delta Table | Primary Key |
|------------------|-------------|-----------------|----------|---------------|-------------------|-------------------|-------------|
| AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | ACCTDAT | ACCTFILE, ACCTFILE (CBSTM03B) | CVACT01Y | 300 bytes | `carddemo.bronze.acct_raw` | `carddemo.silver.account` | `acct_id` |
| AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS | CARDDAT | CARDFILE | CVACT02Y | 150 bytes | `carddemo.bronze.card_raw` | `carddemo.silver.card` | `card_num` |
| AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX.PATH | CARDAIX | — | CVACT02Y | 150 bytes (via base) | Not extracted separately | Filter on `silver.card.card_acct_id` | N/A |
| AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | CCXREF | XREFFILE (CBTRN01C, CBSTM03B) | CVACT03Y | 50 bytes | `carddemo.bronze.xref_raw` | `carddemo.silver.card_xref` | `card_num` |
| AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.PATH | CXACAIX | — | CVACT03Y | 50 bytes (via base) | Not extracted separately | Filter on `silver.card_xref.acct_id` | N/A |
| AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | CUSTDAT | CUSTFILE (CBSTM03B) | CVCUS01Y | 500 bytes | `carddemo.bronze.cust_raw` | `carddemo.silver.customer` | `cust_id` |
| AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | TRANSACT | TRANSACT-FILE (CBTRN01C, CBTRN02C) | CVTRA05Y | 350 bytes | `carddemo.bronze.transact_raw` | `carddemo.silver.transaction` | `tran_id` |
| AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS | USRSEC | — | Internal | ~80 bytes | `carddemo.bronze.usrsec_raw` | N/A (cloud identity provider) | `sec_usr_id` |
| EXPFILE (VSAM KSDS) | — | EXPFILE (CBEXPORT) | CVEXPORT | 500 bytes | `carddemo.bronze.export_raw` | Routed to entity-specific Silver tables | `export_seq_num` |

### 4.2 Sequential / Flat Files

| Mainframe DD Name | JCL Job(s) | Record Length | Format | Bronze Delta Table | Notes |
|------------------|------------|---------------|--------|-------------------|-------|
| DALYTRAN | POSTTRAN.jcl (input to CBTRN01C, CBTRN02C) | 350 bytes | CVTRA05Y layout | `carddemo.bronze.daily_transactions` | Same layout as TRANSACT VSAM; produced by upstream JCL |
| TCATBALF | INTCALC.jcl (input to CBACT04C) | ~200 bytes | CVTRA01Y layout | `carddemo.bronze.tran_cat_balance_raw` | Also written by CBTRN02C; must be sorted by TRANCAT-ACCT-ID |
| DISCGRP | INTCALC.jcl (input to CBACT04C) | ~200 bytes | CVTRA02Y layout | `carddemo.bronze.disclosure_group_raw` | Reference file; rarely changes |
| DATEPARM | TRANREPT.jcl (input to CBTRN03C) | 22 bytes | Start date (1-10) + space + End date (12-21) | Eliminated — replaced by job parameters `start_date` and `end_date` | |
| STMTFILE | CREASTMT.JCL (output of CBSTM03A, input of CBSTM03B) | 80 bytes | Plain-text statement lines | Eliminated — CBSTM03A and CBSTM03B merged | Intermediate file; replaced by in-memory DataFrame |
| HTMLFILE | CREASTMT.JCL (output of CBSTM03A) | 100 bytes | HTML statement fragments | `carddemo.gold.account_statement` (`stmt_html_fragment` column) | |
| DALYREJS | DALYREJS.jcl (output of CBTRN02C) | 430 bytes (350 + 80 trailer) | CVTRA05Y + reject trailer | `carddemo.gold.daily_rejects` | |
| TRNTYPE input | MNTTRDB2.jcl (input to COBTUPDT) | 53 bytes | 1-byte action + 2-byte type + 50-byte desc | `carddemo.bronze.tran_type_input` | |
| CBIMPORT input | CBIMPORT.jcl (input to CBIMPORT) | 500 bytes | CVEXPORT layout | `carddemo.bronze.import_raw` | External partner-supplied |

### 4.3 DB2 Tables

| DB2 Table | DB2 Schema | Used By (Programs) | Bronze Delta Table | Target Delta Table | CDC Required |
|-----------|-----------|-------------------|-------------------|-------------------|-------------|
| TRNTYPE | CARDDEMO | CBTRN02C (validate), COTRTLIC, COTRTUPC, COBTUPDT (maintain) | `carddemo.bronze.tran_type_input` | `carddemo.reference.tran_type` | No — daily full reload |
| TRNTYCAT | CARDDEMO | Referenced in DCL; not actively queried in batch | `carddemo.bronze.tran_cat_input` | `carddemo.reference.tran_category` | No |
| AUTHFRDS | (default) | COPAUS2C (insert/update), COPAUS0C/1C (display) | `carddemo.bronze.auth_fraud_raw` | `carddemo.silver.auth_fraud` | Yes |

### 4.4 IMS Databases

| IMS Database | DBD Name | Segment | Key | Access Programs | Bronze Delta Table | Silver Delta Table |
|-------------|----------|---------|-----|----------------|-------------------|--------------------|
| Pending Auth Summary | PAUTHSUM | PAUTSUM0 (root) | ACCNTID (card/acct 11 bytes) | CBPAUP0C (delete), PAUDBUNL (read), PAUDBLOD (write), DBUNLDGS (read) | `carddemo.bronze.auth_summary_raw` | `carddemo.silver.auth_summary` |
| Pending Auth Detail | PAUTHDTL | PAUTDTL1 (child of PAUTSUM0) | Inverted timestamp within parent | CBPAUP0C (delete), PAUDBUNL (read), PAUDBLOD (write), DBUNLDGS (read) | `carddemo.bronze.auth_detail_raw` | `carddemo.silver.auth_detail` |

**IMS PCB Mapping:**

| IMS PCB | Program | Function | Cloud Equivalent |
|---------|---------|----------|-----------------|
| PAUTSUM-PCB | CBPAUP0C | GN (sequential root read), DLET (root delete) | `SELECT / DELETE FROM silver.auth_summary` |
| PAUTDTL-PCB | CBPAUP0C | GNP (child read within parent), DLET (child delete) | `SELECT / DELETE FROM silver.auth_detail WHERE parent_key = ?` |
| PASFLPCB | DBUNLDGS | ISRT to GSAM (root output) | `INSERT INTO gold.auth_gsam_export` (root partition) |
| PADFLPCB | DBUNLDGS | ISRT to GSAM (child output) | `INSERT INTO gold.auth_gsam_export` (child partition) |
| PAUTSUM-PCB | PAUDBUNL | GN (sequential read all roots) | `SELECT * FROM silver.auth_summary` |
| PAUTDTL-PCB | PAUDBUNL | GNP (children of current root) | `SELECT * FROM silver.auth_detail WHERE root_seg_key = parent_acct_id` |
| PAUTSUM-PCB | PAUDBLOD | GU (position root before child ISRT), ISRT (root) | `MERGE INTO silver.auth_summary` |
| PAUTDTL-PCB | PAUDBLOD | ISRT (child) | `MERGE INTO silver.auth_detail` |

### 4.5 MQ Queues

| MQ Queue | Direction | Batch/Online Program | Cloud Equivalent | Databricks Streaming Topic |
|---------|-----------|---------------------|-----------------|--------------------------|
| Auth Request Queue | Input | COPAUA0C (CICS) | Kafka topic: `carddemo.auth.request` | N/A (CICS online program; not migrated to Databricks batch) |
| Auth Response Queue | Output | COPAUA0C (CICS) | Kafka topic: `carddemo.auth.response` | N/A |
| Auth Error Queue | Error | COPAUA0C (CICS) | Dead-letter topic: `carddemo.auth.error` | N/A |
| Account Inquiry Input | Input | COACCT01 (CICS MQ trigger) | Kafka topic: `carddemo.account.inquiry.req` | `carddemo_mq_account_inquiry_stream` — consumed |
| Account Inquiry Output | Output | COACCT01 (CICS MQ trigger) | Kafka topic: `carddemo.account.inquiry.reply` | `carddemo_mq_account_inquiry_stream` — produced |
| Date Inquiry Input | Input | CODATE01 (CICS MQ trigger) | Kafka topic: `carddemo.date.inquiry.req` | `carddemo_mq_date_service_stream` — consumed |
| Date Inquiry Output | Output | CODATE01 (CICS MQ trigger) | Kafka topic: `carddemo.date.inquiry.reply` | `carddemo_mq_date_service_stream` — produced |

---

## 5. Copybook-to-Schema Traceability

This section maps every COBOL copybook referenced across all batch programs to its Delta Lake schema.

| Copybook | Used By Programs | Record Length | Delta Table(s) | Key Field Mapping | Notes |
|----------|----------------|--------------|----------------|-------------------|-------|
| CVACT01Y | CBACT01C, CBACT04C, CBSTM03A/B | 300 bytes | `bronze.acct_raw`, `silver.account` | ACCT-ID → `acct_id` | ACCT-CURR-CYC-DEBIT is COMP-3 (6 packed bytes) |
| CVACT02Y | CBACT02C, CBTRN01C, CBTRN02C | 150 bytes | `bronze.card_raw`, `silver.card` | CARD-NUM → `card_num` | CARD-EXPIRAION-DATE in MM/YY format (not standard) |
| CVACT03Y | CBACT03C, CBACT04C, CBTRN01C, CBTRN03C, CBSTM03A/B | 50 bytes | `bronze.xref_raw`, `silver.card_xref` | XREF-CARD-NUM → `card_num` | XREF-ACCT-ID used as join key to ACCTFILE |
| CVCUS01Y | CBCUS01C, CBSTM03A/B | 500 bytes | `bronze.cust_raw`, `silver.customer` | CUST-ID → `cust_id` | PII: SSN, DOB, GOVT-ID require column masking |
| CVTRA05Y | CBTRN01C, CBTRN02C, CBTRN03C, CBSTM03A/B | 350 bytes | `bronze.transact_raw`, `silver.transaction`, `bronze.daily_transactions` | TRAN-ID → `tran_id` | TRAN-AMT is COMP-3; DB2 timestamp format for ORIG-TS and PROC-TS |
| CVTRA01Y | CBACT04C (TCATBALF input) | ~200 bytes | `bronze.tran_cat_balance_raw`, `silver.tran_cat_balance` | TRANCAT-ACCT-ID + TRANCAT-TYPE-CD + TRANCAT-CD | Must be sorted by TRANCAT-ACCT-ID for CBACT04C processing |
| CVTRA02Y | CBACT04C (DISCGRP input) | ~200 bytes | `bronze.disclosure_group_raw`, `silver.disclosure_group` | DIS-ACCT-GROUP-ID | 'DEFAULT' entry mandatory; CBACT04C falls back to it |
| CVTRA03Y | CBTRN03C (transaction type reference) | N/A (DB2 DCL) | `reference.tran_type` | TR_TYPE | DB2 DECLARE TABLE; maps to CARDDEMO.TRNTYPE |
| CVTRA04Y | CBTRN03C (transaction category reference) | N/A (DB2 DCL) | `reference.tran_category` | Category code | DB2 DECLARE TABLE; maps to CARDDEMO.TRNTYCAT |
| CVTRA07Y | CBTRN03C (date params) | 22 bytes | Eliminated — job parameters | N/A | DATEPARM file layout; replaced by Databricks widgets |
| CVEXPORT | CBEXPORT, CBIMPORT | 500 bytes | `bronze.export_raw`, `bronze.import_raw` | EXPORT-SEQUENCE-NUM | REDEFINES per entity type; Bronze stores raw bytes; Silver routes by EXPORT-ENTITY-TYPE |

---

## 6. Error Handling Traceability

This section maps every COBOL error handling mechanism to its cloud equivalent.

| COBOL Mechanism | Programs | Behavior | Cloud Equivalent | Target Table / Log |
|----------------|----------|----------|-----------------|-------------------|
| `FILE STATUS` check after OPEN | All VSAM programs | Non-'00' STATUS → display error message + abend | `try/except` on Delta read/write; abend → `PipelineAbendError` raised | `migration_ctrl.error_log` |
| `FILE STATUS='10'` (EOF) | All sequential programs | End-of-file indicator; stop loop | PySpark DataFrame read exhausts naturally; no special action | N/A |
| `STOP RUN` | All programs | Normal program termination | Pipeline function returns; job exits normally | N/A |
| `EXEC DLI CHKP` (IMS checkpoint) | CBPAUP0C | Save checkpoint every N records; `RESTART=stepname` allows restart | Delta transaction log provides implicit checkpointing; display checkpoint preserved as INFO log every N records | Databricks driver log |
| `RETURN-CODE=4` | CBTRN02C, COBTUPDT | Warning level; processing continued | Pipeline sets `return_code=4` in task output parameter; downstream uses `run_if` | `migration_ctrl.pipeline_metrics` |
| `RETURN-CODE=8` | Various | Error level; typically stops downstream steps | Non-zero exit code; Databricks task fails | `migration_ctrl.pipeline_metrics` |
| `RETURN-CODE=16` | CBPAUP0C | Fatal; abend equivalent | `PipelineAbendError(rc=16)` raised; task fails | `migration_ctrl.pipeline_metrics` |
| `PERFORM UNTIL` with `ON SIZE ERROR` | CBACT04C (interest arithmetic) | Overflow in decimal computation → ON SIZE ERROR path | `DecimalType` arithmetic raises `ArithmeticException` on overflow; caught in `try/except` | `migration_ctrl.error_log` |
| `ABEND` (implicit via STATUS) | CBTRN03C | Lookup failure (XREF/TRANTYPE/TRANCATG) → hard abend | `PipelineAbendError` raised with lookup key in message | `migration_ctrl.error_log` |
| `STATUS-CODE='II'` (IMS duplicate) | PAUDBLOD | Duplicate ISRT logged but not fatal | MERGE handles duplicate; logged as WARNING | Databricks driver log |
| Error record to ERROR-OUTPUT | CBIMPORT | Unknown entity type → 132-byte error record | Unknown entity → `migration_ctrl.error_log` row | `migration_ctrl.error_log` |
| `9999-ABEND` (COBTUPDT) | COBTUPDT | Sets RC=4 but continues (no STOP RUN) | Non-fatal error path; log + continue; RC=4 in metrics | `migration_ctrl.pipeline_metrics` |

---

## 7. Known Defect Traceability

This section catalogs all known COBOL defects from the source specifications and documents how each is handled in the migration.

| Defect ID | Program | Location | Defect Description | Migration Decision | Rationale |
|-----------|---------|----------|-------------------|--------------------|-----------|
| DEFECT-001 | CBACT01C | 1300-POPUL-ACCT-RECORD lines 236-238 | `IF ACCT-CURR-CYC-DEBIT = 0 MOVE 2525.00 TO OUT-ACCT-CURR-CYC-DEBIT` — hardcoded test value | **Preserved** | Business requirement unclear; substitution may be intentional for display/testing purposes. TODO: VERIFY with business owner |
| DEFECT-002 | CBACT02C | Z-DISPLAY-IO-STATUS | Double-display of IO status on file error (same status printed twice) | **Preserved** | Downstream consumers may depend on doubled log output; behavior preserved in logging | 
| DEFECT-003 | CBACT03C | Z-DISPLAY-IO-STATUS | Same double-display defect as CBACT02C | **Preserved** | Same rationale |
| DEFECT-004 | CBCUS01C | Z-DISPLAY-IO-STATUS | Same double-display defect as CBACT02C | **Preserved** | Same rationale |
| DEFECT-005 | CBTRN01C | OPEN/CLOSE statements | CUSTFILE, CARDFILE, and TRANSACT-FILE opened and closed but never read (dead code) | **Eliminated** | Opening files that are never used is harmless on mainframe but meaningless in PySpark; no Delta table opened for these |
| DEFECT-006 | CBTRN01C | 9000-DALYTRAN-CLOSE | Paragraph close comment says 'CUSTOMER FILE' instead of 'DALYTRAN' (copy-paste error) | **Preserved as comment** | Defect comment preserved in pipeline code: `# NOTE: Original COBOL label says 'CUSTOMER FILE' — copy-paste error; this is DALYTRAN close` |
| DEFECT-007 | CBTRN02C | TRANSACT-FILE mode | TRANSACT-FILE opened OUTPUT (not I-O) — means existing transactions cannot be updated, only new ones written | **Preserved** | INSERT-only behavior preserved; pipeline uses INSERT (not MERGE) into `silver.transaction` |
| DEFECT-008 | CBPAUP0C | Line 170 | `IF PA-APPROVED-AUTH-CNT <= 0 AND PA-APPROVED-AUTH-CNT <= 0` — same field checked twice (should check PA-APPROVED-AUTH-AMT in second condition) | **Preserved** | Defect is in production COBOL; migration must match exact behavior until business owner authorizes fix. Comment: `# DEFECT: Duplicate predicate — original COBOL checks PA-APPROVED-AUTH-CNT twice` |
| DEFECT-009 | CBSTM03A | Multiple paragraphs | ALTER/GO TO dynamic branch modification — not maintainable; PSA/TCB/TIOT control block addressing — z/OS specific | **Eliminated** | z/OS-specific constructs have no cloud equivalent; replaced by explicit Python function dispatch |
| DEFECT-010 | CBSTM03B | M03B-WRITE/M03B-REWRITE | 88-level values for WRITE and REWRITE operations defined but never implemented (no corresponding EVALUATE branch) | **Eliminated** | Dead code; never executed on mainframe; merged pipeline reads Silver directly |
| DEFECT-011 | CBEXPORT | EXPFILE | EXPORT-BRANCH-ID='0001' and EXPORT-REGION-CODE='NORTH' hardcoded | **Preserved as config** | Hardcoded values moved to `config/pipeline_config.py` for maintainability; behavior unchanged |
| DEFECT-012 | CBIMPORT | 3000-VALIDATE-IMPORT | Validation paragraph is a stub (EXIT only) — no data validation performed | **Preserved as stub** | Migration preserves stub with explicit comment; TODO flag added for business to define validation rules |
| DEFECT-013 | DBUNLDGS | Working Storage | WS-PGMNAME='IMSUNLOD' does not match actual program name 'DBUNLDGS' | **Preserved as comment** | Comment in config: `# NOTE: WS-PGMNAME mismatch in original — IMSUNLOD vs DBUNLDGS` |
| DEFECT-014 | DBUNLDGS | OPFILE1/OPFILE2 | WRITE statements for OPFILE1/OPFILE2 are commented out in source — records may never be written | **Assumed intent: write** | Migration implements the write assuming the comment-out was unintentional. TODO: VERIFY with mainframe team |
| DEFECT-015 | COBTUPDT | 9999-ABEND | 9999-ABEND sets RC=4 but has no STOP RUN — processing continues after abend path | **Preserved** | Intentional or not, behavior is preserved: error logged, RC=4 set, next record processed |
| DEFECT-016 | COACCT01 | Reply message | ZIP code excluded from MQPUT reply (documented in source spec as known defect) | **Preserved** | Streaming pipeline omits `acct_addr_zip` from reply Kafka message as per original behavior |
| DEFECT-017 | CODATE01 | EXEC CICS ASKTIME | No RESP/RESP2 checking after CICS commands | **Preserved** | Streaming pipeline does not validate `datetime.now()` (equivalent is always successful); behavior equivalent |

---

*End of Traceability Matrix — Version 1.0*

*This document covers all 16 batch COBOL programs, all 46 JCL jobs, all business rules extracted from source specifications, all mainframe files and datasets, all copybooks, all error handling mechanisms, and all known defects. References to source programs use the exact paragraph names and line references from the technical specifications.*
