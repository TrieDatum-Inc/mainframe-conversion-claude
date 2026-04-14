# CardDemo Delta Table Schema Specification
## Complete Delta Lake Schema for All Data Entities — Medallion Architecture

**Document Version:** 1.0  
**Date:** 2026-04-06  
**Catalog:** `carddemo`  
**Schemas:** `bronze`, `silver`, `gold`, `reference`, `migration_ctrl`

---

## Table of Contents

1. [COBOL-to-Spark Data Type Reference](#1-cobol-to-spark-data-type-reference)
2. [Table Naming Conventions](#2-table-naming-conventions)
3. [Bronze Layer Tables](#3-bronze-layer-tables)
4. [Silver Layer Tables](#4-silver-layer-tables)
5. [Gold Layer Tables](#5-gold-layer-tables)
6. [Reference Layer Tables](#6-reference-layer-tables)
7. [Migration Control Tables](#7-migration-control-tables)
8. [Partitioning Strategy](#8-partitioning-strategy)
9. [Z-Ordering Strategy](#9-z-ordering-strategy)
10. [Schema Evolution Approach](#10-schema-evolution-approach)
11. [Data Retention and Archival Policy](#11-data-retention-and-archival-policy)

---

## 1. COBOL-to-Spark Data Type Reference

### 1.1 Complete Type Mapping Table

| COBOL PIC Clause | COBOL Usage | Spark Type | Notes |
|-----------------|-------------|------------|-------|
| `PIC X(n)` | Standard alphanumeric | `StringType()` | Trailing spaces preserved in Bronze; trimmed in Silver |
| `PIC 9(n)` where n ≤ 9 | Unsigned integer | `IntegerType()` | |
| `PIC 9(n)` where n > 9 | Unsigned large integer | `LongType()` | |
| `PIC 9(n)V9(m)` | Unsigned decimal | `DecimalType(n+m, m)` | Never use DoubleType for financial fields |
| `PIC S9(n) COMP-3` | Signed packed decimal | `DecimalType(n, 0)` | Unpacked during Bronze ingestion |
| `PIC S9(n)V9(m) COMP-3` | Signed packed decimal | `DecimalType(n+m, m)` | Unpacked during Bronze ingestion |
| `PIC S9(n) COMP` | Signed binary integer | `IntegerType()` (n ≤ 9) or `LongType()` (n > 9) | |
| `PIC S9(n)V9(m) COMP` | Signed binary decimal | `DecimalType(n+m, m)` | |
| `PIC X(8)` (date YYYYMMDD) | Date as string | `StringType()` in Bronze, `DateType()` in Silver | Format documented in comments |
| `PIC X(10)` (date YYYY-MM-DD) | Date with dashes | `StringType()` in Bronze, `DateType()` in Silver | |
| `PIC 9(8)` (date YYYYMMDD) | Numeric date | `IntegerType()` in Bronze, `DateType()` in Silver | |
| `PIC X(26)` (DB2 timestamp) | DB2 YYYY-MM-DD-HH.MM.SS.mmm0000 | `StringType()` in Bronze, `TimestampType()` in Silver | |
| `PIC 9(6)` (YYMMDD) | Julian date component | `StringType()` | Preserve raw value |
| `PIC 9(5)` (YYDDD Julian) | Julian date | `IntegerType()` | |
| `PIC X(1)` (flag/indicator) | Single-character flag | `StringType()` | e.g., 'Y'/'N', 'A'/'I', '00'/'01' |
| `PIC X(2)` (status/type code) | Two-character code | `StringType()` | |
| `FILLER` | Padding bytes | **Omitted** unless data-bearing | Not stored in Delta |
| `OCCURS n TIMES` | Array | Separate rows via `EXPLODE` | Array elements become individual rows with occurrence index |
| `REDEFINES` | Alternate view of same bytes | Multiple columns with `_interpretation` suffix | Both interpretations stored in Bronze |

### 1.2 Specific Field Mappings from CardDemo Copybooks

#### CVACT01Y — Account Record (ACCTFILE, 300 bytes)

| Copybook Field | PIC Clause | Bytes | Bronze Column | Silver Column | Spark Type |
|---------------|-----------|-------|---------------|---------------|------------|
| ACCT-ID | 9(11) | 11 | `acct_id_raw` | `acct_id` | `StringType()` → `LongType()` |
| ACCT-ACTIVE-STATUS | X(1) | 1 | `acct_active_status` | `acct_active_status` | `StringType()` |
| ACCT-CURR-BAL | S9(10)V99 | 12 (implied) | `acct_curr_bal_raw` | `acct_curr_bal` | `DecimalType(12, 2)` |
| ACCT-CREDIT-LIMIT | S9(10)V99 | 12 | `acct_credit_limit_raw` | `acct_credit_limit` | `DecimalType(12, 2)` |
| ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | 12 | `acct_cash_credit_limit_raw` | `acct_cash_credit_limit` | `DecimalType(12, 2)` |
| ACCT-OPEN-DATE | X(10) | 10 | `acct_open_date_raw` | `acct_open_date` | `DateType()` (YYYY-MM-DD format) |
| ACCT-EXPIRAION-DATE | X(10) | 10 | `acct_expiraion_date_raw` | `acct_expiraion_date` | `DateType()` |
| ACCT-REISSUE-DATE | X(10) | 10 | `acct_reissue_date_raw` | `acct_reissue_date` | `DateType()` |
| ACCT-CURR-CYC-CREDIT | S9(10)V99 | 12 | `acct_curr_cyc_credit_raw` | `acct_curr_cyc_credit` | `DecimalType(12, 2)` |
| ACCT-CURR-CYC-DEBIT | S9(10)V99 COMP-3 | 6 (packed) | `acct_curr_cyc_debit_raw` | `acct_curr_cyc_debit` | `DecimalType(12, 2)` |
| ACCT-ADDR-ZIP | X(10) | 10 | `acct_addr_zip` | `acct_addr_zip` | `StringType()` |
| ACCT-GROUP-ID | X(10) | 10 | `acct_group_id` | `acct_group_id` | `StringType()` |
| FILLER | X(178) | 178 | — | — | Omitted |

#### CVACT02Y — Card Record (CARDFILE, 150 bytes)

| Copybook Field | PIC Clause | Bytes | Bronze Column | Silver Column | Spark Type |
|---------------|-----------|-------|---------------|---------------|------------|
| CARD-NUM | X(16) | 16 | `card_num` | `card_num` | `StringType()` |
| CARD-ACCT-ID | 9(11) | 11 | `card_acct_id_raw` | `card_acct_id` | `LongType()` |
| CARD-CVV-CD | 9(3) | 3 | `card_cvv_cd_raw` | `card_cvv_cd` | `IntegerType()` |
| CARD-EMBOSSED-NAME | X(50) | 50 | `card_embossed_name` | `card_embossed_name` | `StringType()` |
| CARD-EXPIRAION-DATE | X(10) | 10 | `card_expiraion_date_raw` | `card_expiraion_date` | `StringType()` (MM/YY format) |
| CARD-ACTIVE-STATUS | X(1) | 1 | `card_active_status` | `card_active_status` | `StringType()` |
| FILLER | X(59) | 59 | — | — | Omitted |

#### CVACT03Y — Card-Account Cross-Reference (XREFFILE/CCXREF, 50 bytes)

| Copybook Field | PIC Clause | Bytes | Bronze Column | Silver Column | Spark Type |
|---------------|-----------|-------|---------------|---------------|------------|
| XREF-CARD-NUM | X(16) | 16 | `xref_card_num` | `card_num` | `StringType()` |
| XREF-CUST-ID | 9(9) | 9 | `xref_cust_id_raw` | `cust_id` | `LongType()` |
| XREF-ACCT-ID | 9(11) | 11 | `xref_acct_id_raw` | `acct_id` | `LongType()` |
| FILLER | X(14) | 14 | — | — | Omitted |

#### CVCUS01Y — Customer Record (CUSTFILE, 500 bytes)

| Copybook Field | PIC Clause | Bytes | Bronze Column | Silver Column | Spark Type |
|---------------|-----------|-------|---------------|---------------|------------|
| CUST-ID | 9(9) | 9 | `cust_id_raw` | `cust_id` | `LongType()` |
| CUST-FIRST-NAME | X(25) | 25 | `cust_first_name` | `cust_first_name` | `StringType()` |
| CUST-MIDDLE-NAME | X(25) | 25 | `cust_middle_name` | `cust_middle_name` | `StringType()` |
| CUST-LAST-NAME | X(25) | 25 | `cust_last_name` | `cust_last_name` | `StringType()` |
| CUST-ADDR-LINE-1 | X(50) | 50 | `cust_addr_line_1` | `cust_addr_line_1` | `StringType()` |
| CUST-ADDR-LINE-2 | X(50) | 50 | `cust_addr_line_2` | `cust_addr_line_2` | `StringType()` |
| CUST-ADDR-LINE-3 | X(50) | 50 | `cust_addr_line_3` | `cust_addr_line_3` | `StringType()` |
| CUST-ADDR-STATE-CD | X(2) | 2 | `cust_addr_state_cd` | `cust_addr_state_cd` | `StringType()` |
| CUST-ADDR-COUNTRY-CD | X(3) | 3 | `cust_addr_country_cd` | `cust_addr_country_cd` | `StringType()` |
| CUST-ADDR-ZIP | X(10) | 10 | `cust_addr_zip` | `cust_addr_zip` | `StringType()` |
| CUST-PHONE-NUM-1 | X(15) | 15 | `cust_phone_num_1` | `cust_phone_num_1` | `StringType()` |
| CUST-PHONE-NUM-2 | X(15) | 15 | `cust_phone_num_2` | `cust_phone_num_2` | `StringType()` |
| CUST-SSN | 9(9) | 9 | `cust_ssn_raw` | `cust_ssn` | `StringType()` (treat as string; do not cast to int for PII) |
| CUST-GOVT-ISSUED-ID | X(20) | 20 | `cust_govt_issued_id` | `cust_govt_issued_id` | `StringType()` |
| CUST-DOB-YYYY-MM-DD | X(10) | 10 | `cust_dob_raw` | `cust_dob` | `DateType()` |
| CUST-EFT-ACCOUNT-ID | X(10) | 10 | `cust_eft_account_id` | `cust_eft_account_id` | `StringType()` |
| CUST-PRI-CARD-HOLDER-IND | X(1) | 1 | `cust_pri_card_holder_ind` | `cust_pri_card_holder_ind` | `StringType()` |
| CUST-FICO-CREDIT-SCORE | 9(3) | 3 | `cust_fico_credit_score_raw` | `cust_fico_credit_score` | `IntegerType()` |
| FILLER | X(168) | 168 | — | — | Omitted |

#### CVTRA05Y — Transaction Record (TRANSACT, 350 bytes)

| Copybook Field | PIC Clause | Bytes | Bronze Column | Silver Column | Spark Type |
|---------------|-----------|-------|---------------|---------------|------------|
| TRAN-ID | X(16) | 16 | `tran_id` | `tran_id` | `StringType()` |
| TRAN-TYPE-CD | X(2) | 2 | `tran_type_cd` | `tran_type_cd` | `StringType()` |
| TRAN-CAT-CD | 9(4) | 4 | `tran_cat_cd_raw` | `tran_cat_cd` | `IntegerType()` |
| TRAN-SOURCE | X(10) | 10 | `tran_source` | `tran_source` | `StringType()` |
| TRAN-DESC | X(100) | 100 | `tran_desc` | `tran_desc` | `StringType()` |
| TRAN-AMT | S9(9)V99 | 11 | `tran_amt_raw` | `tran_amt` | `DecimalType(11, 2)` |
| TRAN-MERCHANT-ID | 9(9) | 9 | `tran_merchant_id_raw` | `tran_merchant_id` | `LongType()` |
| TRAN-MERCHANT-NAME | X(50) | 50 | `tran_merchant_name` | `tran_merchant_name` | `StringType()` |
| TRAN-MERCHANT-CITY | X(50) | 50 | `tran_merchant_city` | `tran_merchant_city` | `StringType()` |
| TRAN-MERCHANT-ZIP | X(10) | 10 | `tran_merchant_zip` | `tran_merchant_zip` | `StringType()` |
| TRAN-CARD-NUM | X(16) | 16 | `tran_card_num` | `tran_card_num` | `StringType()` |
| TRAN-ORIG-TS | X(26) | 26 | `tran_orig_ts_raw` | `tran_orig_ts` | `TimestampType()` |
| TRAN-PROC-TS | X(26) | 26 | `tran_proc_ts_raw` | `tran_proc_ts` | `TimestampType()` |
| FILLER | X(20) | 20 | — | — | Omitted |

---

## 2. Table Naming Conventions

### 2.1 Naming Pattern

```
{catalog}.{schema}.{entity}[_{qualifier}]

Examples:
  carddemo.bronze.acct_raw
  carddemo.silver.account
  carddemo.gold.account_statement
  carddemo.reference.tran_type
  carddemo.migration_ctrl.pipeline_metrics
```

### 2.2 Naming Rules

- **Catalog**: Always `carddemo`
- **Bronze tables**: Suffix `_raw`; named after VSAM DD name or DB2 table in lowercase with underscores
- **Silver tables**: Named after entity (no suffix); singular noun
- **Gold tables**: Descriptive name indicating the business-level aggregate
- **Reference tables**: Named after the mainframe table/copybook they replace
- **Column names**: Snake_case; original COBOL field names with hyphens replaced by underscores and leading qualifiers dropped (e.g., `ACCT-CURR-BAL` → `acct_curr_bal`)
- **Raw columns** in Bronze: Suffix `_raw` for columns that need type conversion in Silver
- **Metadata columns**: Prefix `_meta_` (e.g., `_meta_extract_date`, `_meta_pipeline_run_id`)

---

## 3. Bronze Layer Tables

### 3.1 `carddemo.bronze.acct_raw`
**Source:** VSAM KSDS `AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS` (ACCTFILE)  
**Copybook:** CVACT01Y  
**Record size:** 300 bytes  
**Partitioned by:** `_meta_extract_date`

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.acct_raw (
  -- VSAM Record Fields (mapped from CVACT01Y)
  acct_id_raw             STRING         COMMENT 'ACCT-ID PIC 9(11) — 11-digit account ID, zero-padded',
  acct_active_status      STRING         COMMENT 'ACCT-ACTIVE-STATUS PIC X(1) — Active indicator',
  acct_curr_bal_raw       STRING         COMMENT 'ACCT-CURR-BAL S9(10)V99 — Raw balance string including sign',
  acct_credit_limit_raw   STRING         COMMENT 'ACCT-CREDIT-LIMIT S9(10)V99',
  acct_cash_credit_limit_raw STRING      COMMENT 'ACCT-CASH-CREDIT-LIMIT S9(10)V99',
  acct_open_date_raw      STRING         COMMENT 'ACCT-OPEN-DATE PIC X(10) — Format YYYY-MM-DD',
  acct_expiraion_date_raw STRING         COMMENT 'ACCT-EXPIRAION-DATE PIC X(10) — Note: original COBOL field has typo in name',
  acct_reissue_date_raw   STRING         COMMENT 'ACCT-REISSUE-DATE PIC X(10)',
  acct_curr_cyc_credit_raw STRING        COMMENT 'ACCT-CURR-CYC-CREDIT S9(10)V99',
  acct_curr_cyc_debit_raw STRING         COMMENT 'ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3 — packed decimal; unpacked here',
  acct_addr_zip           STRING         COMMENT 'ACCT-ADDR-ZIP PIC X(10)',
  acct_group_id           STRING         COMMENT 'ACCT-GROUP-ID PIC X(10) — links to DISCGRP disclosure group',
  -- Metadata columns
  _meta_extract_date      DATE           COMMENT 'Date this record was extracted from mainframe',
  _meta_pipeline_run_id   STRING         COMMENT 'Databricks job run ID that loaded this record',
  _meta_source_system     STRING         COMMENT 'Always: CARDDEMO_VSAM_ACCTFILE',
  _meta_record_hash       STRING         COMMENT 'SHA-256 hash of all business fields for change detection'
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Raw account records from VSAM KSDS ACCTFILE (CVACT01Y copybook)';
```

**Z-ORDER:** `acct_id_raw`  
**Retention:** 90 days

---

### 3.2 `carddemo.bronze.card_raw`
**Source:** VSAM KSDS `AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS` (CARDFILE)  
**Copybook:** CVACT02Y  
**Record size:** 150 bytes

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.card_raw (
  card_num                STRING         COMMENT 'CARD-NUM PIC X(16) — primary key',
  card_acct_id_raw        STRING         COMMENT 'CARD-ACCT-ID PIC 9(11)',
  card_cvv_cd_raw         STRING         COMMENT 'CARD-CVV-CD PIC 9(3)',
  card_embossed_name      STRING         COMMENT 'CARD-EMBOSSED-NAME PIC X(50)',
  card_expiraion_date_raw STRING         COMMENT 'CARD-EXPIRAION-DATE PIC X(10) — typo preserved from original COBOL',
  card_active_status      STRING         COMMENT 'CARD-ACTIVE-STATUS PIC X(1)',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING,
  _meta_record_hash       STRING
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Raw card records from VSAM KSDS CARDFILE (CVACT02Y copybook)';
```

---

### 3.3 `carddemo.bronze.cust_raw`
**Source:** VSAM KSDS `AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS` (CUSTFILE)  
**Copybook:** CVCUS01Y  
**Record size:** 500 bytes

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.cust_raw (
  cust_id_raw             STRING         COMMENT 'CUST-ID PIC 9(9) — 9-digit customer ID',
  cust_first_name         STRING         COMMENT 'CUST-FIRST-NAME PIC X(25)',
  cust_middle_name        STRING         COMMENT 'CUST-MIDDLE-NAME PIC X(25)',
  cust_last_name          STRING         COMMENT 'CUST-LAST-NAME PIC X(25)',
  cust_addr_line_1        STRING         COMMENT 'CUST-ADDR-LINE-1 PIC X(50)',
  cust_addr_line_2        STRING         COMMENT 'CUST-ADDR-LINE-2 PIC X(50)',
  cust_addr_line_3        STRING         COMMENT 'CUST-ADDR-LINE-3 PIC X(50)',
  cust_addr_state_cd      STRING         COMMENT 'CUST-ADDR-STATE-CD PIC X(2)',
  cust_addr_country_cd    STRING         COMMENT 'CUST-ADDR-COUNTRY-CD PIC X(3)',
  cust_addr_zip           STRING         COMMENT 'CUST-ADDR-ZIP PIC X(10)',
  cust_phone_num_1        STRING         COMMENT 'CUST-PHONE-NUM-1 PIC X(15)',
  cust_phone_num_2        STRING         COMMENT 'CUST-PHONE-NUM-2 PIC X(15)',
  cust_ssn_raw            STRING         COMMENT 'CUST-SSN PIC 9(9) — stored as string for PII handling',
  cust_govt_issued_id     STRING         COMMENT 'CUST-GOVT-ISSUED-ID PIC X(20)',
  cust_dob_raw            STRING         COMMENT 'CUST-DOB-YYYY-MM-DD PIC X(10)',
  cust_eft_account_id     STRING         COMMENT 'CUST-EFT-ACCOUNT-ID PIC X(10)',
  cust_pri_card_holder_ind STRING        COMMENT 'CUST-PRI-CARD-HOLDER-IND PIC X(1)',
  cust_fico_credit_score_raw STRING      COMMENT 'CUST-FICO-CREDIT-SCORE PIC 9(3)',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING,
  _meta_record_hash       STRING
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Raw customer records from VSAM KSDS CUSTFILE (CVCUS01Y copybook)';
```

---

### 3.4 `carddemo.bronze.xref_raw`
**Source:** VSAM KSDS `AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS` (CCXREF/XREFFILE)  
**Copybook:** CVACT03Y  
**Record size:** 50 bytes

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.xref_raw (
  xref_card_num           STRING         COMMENT 'XREF-CARD-NUM PIC X(16) — primary key',
  xref_cust_id_raw        STRING         COMMENT 'XREF-CUST-ID PIC 9(9)',
  xref_acct_id_raw        STRING         COMMENT 'XREF-ACCT-ID PIC 9(11)',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING,
  _meta_record_hash       STRING
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Raw card-to-account cross-reference from VSAM KSDS CCXREF (CVACT03Y copybook)';
```

---

### 3.5 `carddemo.bronze.transact_raw`
**Source:** VSAM KSDS `AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS` (TRANSACT)  
**Copybook:** CVTRA05Y  
**Record size:** 350 bytes

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.transact_raw (
  tran_id                 STRING         COMMENT 'TRAN-ID PIC X(16) — primary key',
  tran_type_cd            STRING         COMMENT 'TRAN-TYPE-CD PIC X(2)',
  tran_cat_cd_raw         STRING         COMMENT 'TRAN-CAT-CD PIC 9(4)',
  tran_source             STRING         COMMENT 'TRAN-SOURCE PIC X(10)',
  tran_desc               STRING         COMMENT 'TRAN-DESC PIC X(100)',
  tran_amt_raw            STRING         COMMENT 'TRAN-AMT S9(9)V99 — raw signed numeric string',
  tran_merchant_id_raw    STRING         COMMENT 'TRAN-MERCHANT-ID PIC 9(9)',
  tran_merchant_name      STRING         COMMENT 'TRAN-MERCHANT-NAME PIC X(50)',
  tran_merchant_city      STRING         COMMENT 'TRAN-MERCHANT-CITY PIC X(50)',
  tran_merchant_zip       STRING         COMMENT 'TRAN-MERCHANT-ZIP PIC X(10)',
  tran_card_num           STRING         COMMENT 'TRAN-CARD-NUM PIC X(16)',
  tran_orig_ts_raw        STRING         COMMENT 'TRAN-ORIG-TS PIC X(26) — DB2 format YYYY-MM-DD-HH.MM.SS.mmm0000',
  tran_proc_ts_raw        STRING         COMMENT 'TRAN-PROC-TS PIC X(26) — DB2 format YYYY-MM-DD-HH.MM.SS.mmm0000',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING,
  _meta_record_hash       STRING
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Raw transaction records from VSAM KSDS TRANSACT (CVTRA05Y copybook)';
```

---

### 3.6 `carddemo.bronze.daily_transactions`
**Source:** Sequential file DALYTRAN (input to CBTRN01C, CBTRN02C)  
**Copybook:** CVTRA06Y  
**Note:** CVTRA06Y not provided in source; fields inferred from program usage

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.daily_transactions (
  dalytran_id             STRING         COMMENT 'DALYTRAN-ID PIC X(16)',
  dalytran_card_num       STRING         COMMENT 'DALYTRAN-CARD-NUM PIC X(16) — used as XREF lookup key',
  dalytran_type_cd        STRING         COMMENT 'DALYTRAN-TYPE-CD PIC X(2)',
  dalytran_cat_cd_raw     STRING         COMMENT 'DALYTRAN-CAT-CD PIC 9(4)',
  dalytran_source         STRING         COMMENT 'DALYTRAN-SOURCE PIC X(10)',
  dalytran_desc           STRING         COMMENT 'DALYTRAN-DESC PIC X(100)',
  dalytran_amt_raw        STRING         COMMENT 'DALYTRAN-AMT S9(9)V99 — raw signed numeric',
  dalytran_merchant_id_raw STRING        COMMENT 'DALYTRAN-MERCHANT-ID PIC 9(9)',
  dalytran_merchant_name  STRING         COMMENT 'DALYTRAN-MERCHANT-NAME PIC X(50)',
  dalytran_merchant_city  STRING         COMMENT 'DALYTRAN-MERCHANT-CITY PIC X(50)',
  dalytran_merchant_zip   STRING         COMMENT 'DALYTRAN-MERCHANT-ZIP PIC X(10)',
  dalytran_orig_ts_raw    STRING         COMMENT 'DALYTRAN-ORIG-TS PIC X(26)',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_batch_date        DATE           COMMENT 'Business date of the daily batch run',
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING
) USING DELTA
PARTITIONED BY (_meta_batch_date)
COMMENT 'Bronze: Daily transaction input file (DALYTRAN, CVTRA06Y) — input to CBTRN01C and CBTRN02C';
```

---

### 3.7 `carddemo.bronze.tran_cat_balance_raw`
**Source:** VSAM KSDS TCATBALF  
**Copybook:** CVTRA01Y

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.tran_cat_balance_raw (
  trancat_acct_id_raw     STRING         COMMENT 'TRANCAT-ACCT-ID PIC 9(11) — part of composite primary key',
  trancat_type_cd         STRING         COMMENT 'TRANCAT-TYPE-CD PIC X(2) — part of composite key',
  trancat_cd_raw          STRING         COMMENT 'TRANCAT-CD PIC 9(4) — part of composite key',
  tran_cat_bal_raw        STRING         COMMENT 'TRAN-CAT-BAL S9(9)V99 — balance for this category',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Transaction category balance records from VSAM KSDS TCATBALF (CVTRA01Y)';
```

---

### 3.8 `carddemo.bronze.disclosure_group_raw`
**Source:** VSAM KSDS DISCGRP  
**Copybook:** CVTRA02Y

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.disclosure_group_raw (
  dis_acct_group_id       STRING         COMMENT 'FD-DIS-ACCT-GROUP-ID PIC X(10) — part of composite key; DEFAULT=fallback',
  dis_tran_type_cd        STRING         COMMENT 'FD-DIS-TRAN-TYPE-CD PIC X(2) — part of composite key',
  dis_tran_cat_cd_raw     STRING         COMMENT 'FD-DIS-TRAN-CAT-CD PIC 9(4) — part of composite key',
  dis_int_rate_raw        STRING         COMMENT 'DIS-INT-RATE — annual interest rate percentage',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Disclosure group interest rates from VSAM KSDS DISCGRP (CVTRA02Y)';
```

---

### 3.9 `carddemo.bronze.auth_summary_raw`
**Source:** IMS HISAM database DBPAUTP0, segment PAUTSUM0 (100 bytes)  
**Copybook:** CIPAUSMY

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.auth_summary_raw (
  pa_acct_id_raw          STRING         COMMENT 'Account ID — IMS root segment key (numeric)',
  pa_approved_auth_cnt_raw STRING        COMMENT 'PA-APPROVED-AUTH-CNT — count of approved authorizations',
  pa_approved_auth_amt_raw STRING        COMMENT 'PA-APPROVED-AUTH-AMT — sum of approved auth amounts',
  pa_declined_auth_cnt_raw STRING        COMMENT 'PA-DECLINED-AUTH-CNT — count of declined authorizations',
  pa_declined_auth_amt_raw STRING        COMMENT 'PA-DECLINED-AUTH-AMT — sum of declined auth amounts',
  raw_segment_bytes       BINARY         COMMENT 'Full 100-byte PAUTSUM0 segment (preserved for validation)',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING         COMMENT 'IMS_DBPAUTP0_PAUTSUM0'
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: IMS PAUTSUM0 root segments from DBPAUTP0 (CIPAUSMY copybook)';
```

---

### 3.10 `carddemo.bronze.auth_detail_raw`
**Source:** IMS HISAM database DBPAUTP0, segment PAUTDTL1 (200 bytes)  
**Copybook:** CIPAUDTY

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.auth_detail_raw (
  pa_acct_id_raw          STRING         COMMENT 'Parent account ID (ROOT-SEG-KEY from PAUDBUNL output)',
  pa_auth_date_9c_raw     STRING         COMMENT 'PA-AUTH-DATE-9C — stored as 99999 - YYDDD (inverted Julian date)',
  pa_auth_resp_code       STRING         COMMENT 'PA-AUTH-RESP-CODE — 00=approved, other=declined',
  pa_transaction_amt_raw  STRING         COMMENT 'PA-TRANSACTION-AMT',
  pa_card_num             STRING         COMMENT 'Card number associated with this authorization',
  raw_segment_bytes       BINARY         COMMENT 'Full 200-byte PAUTDTL1 segment',
  parent_key_raw          STRING         COMMENT 'ROOT-SEG-KEY from PAUDBUNL file 2 (S9(11) COMP-3)',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING         COMMENT 'IMS_DBPAUTP0_PAUTDTL1'
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: IMS PAUTDTL1 child segments from DBPAUTP0 (CIPAUDTY copybook)';
```

---

### 3.11 `carddemo.bronze.export_raw`
**Source:** VSAM KSDS EXPFILE (output of CBEXPORT, input to CBIMPORT)  
**Copybook:** CVEXPORT  
**Record size:** 500 bytes

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.export_raw (
  export_sequence_num     BIGINT         COMMENT 'EXPORT-SEQUENCE-NUM PIC 9(9) — KSDS primary key',
  export_rec_type         STRING         COMMENT 'EXPORT-REC-TYPE PIC X(1) — C=Customer, A=Account, X=XREF, T=Transaction, D=Card',
  export_timestamp        STRING         COMMENT 'EXPORT-TIMESTAMP PIC X(26) — generation timestamp',
  export_branch_id        STRING         COMMENT 'EXPORT-BRANCH-ID PIC X(4) — hardcoded 0001',
  export_region_code      STRING         COMMENT 'EXPORT-REGION-CODE PIC X(5) — hardcoded NORTH',
  export_data_raw         BINARY         COMMENT 'Full 500-byte record (all entity fields in raw bytes)',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_source_system     STRING
) USING DELTA
PARTITIONED BY (_meta_extract_date, export_rec_type)
COMMENT 'Bronze: Consolidated export file from CBEXPORT (CVEXPORT copybook, 500-byte records)';
```

---

### 3.12 `carddemo.bronze.tran_type_input`
**Source:** Sequential input file INPFILE (input to COBTUPDT)  
**Record size:** 53 bytes

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.tran_type_input (
  input_rec_type          STRING         COMMENT 'INPUT-REC-TYPE PIC X(1) — A=Add, U=Update, D=Delete, *=Comment',
  input_rec_number        STRING         COMMENT 'INPUT-REC-NUMBER PIC X(2) — TR_TYPE code',
  input_rec_desc          STRING         COMMENT 'INPUT-REC-DESC PIC X(50) — description text',
  raw_record              STRING         COMMENT 'Full 53-byte input record',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_batch_seq         BIGINT         COMMENT 'Sequence number within the batch run (preserves COBOL file order)'
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Batch transaction type maintenance input (COBTUPDT INPFILE, 53-byte records)';
```

---

### 3.13 `carddemo.bronze.date_params`
**Source:** Sequential file DATEPARM (input to CBTRN03C)  
**Record size:** 80 bytes

```sql
CREATE TABLE IF NOT EXISTS carddemo.bronze.date_params (
  start_date_raw          STRING         COMMENT 'WS-START-DATE PIC X(10) — bytes 1-10, YYYY-MM-DD format',
  end_date_raw            STRING         COMMENT 'WS-END-DATE PIC X(10) — bytes 12-21 (byte 11 is filler space)',
  raw_record              STRING         COMMENT 'Full 80-byte DATEPARM record',
  -- Metadata
  _meta_extract_date      DATE,
  _meta_pipeline_run_id   STRING,
  _meta_report_run_id     STRING         COMMENT 'Links to specific report generation run'
) USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Date parameter file for CBTRN03C transaction report (DATEPARM, 80-byte single record)';
```

---

## 4. Silver Layer Tables

### 4.1 `carddemo.silver.account`
**Source:** `bronze.acct_raw`  
**Copybook:** CVACT01Y  
**Partitioned by:** First 2 digits of `acct_id` (000-999 partitioned into 10 ranges)

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.account (
  acct_id                 BIGINT         NOT NULL COMMENT 'ACCT-ID PIC 9(11) — primary key',
  acct_active_status      STRING         NOT NULL COMMENT 'ACCT-ACTIVE-STATUS PIC X(1)',
  acct_curr_bal           DECIMAL(12,2)  NOT NULL COMMENT 'ACCT-CURR-BAL S9(10)V99',
  acct_credit_limit       DECIMAL(12,2)  NOT NULL COMMENT 'ACCT-CREDIT-LIMIT S9(10)V99',
  acct_cash_credit_limit  DECIMAL(12,2)  NOT NULL COMMENT 'ACCT-CASH-CREDIT-LIMIT S9(10)V99',
  acct_open_date          DATE                    COMMENT 'ACCT-OPEN-DATE X(10) YYYY-MM-DD',
  acct_expiraion_date     DATE                    COMMENT 'ACCT-EXPIRAION-DATE X(10) — typo preserved from COBOL',
  acct_reissue_date       DATE                    COMMENT 'ACCT-REISSUE-DATE X(10)',
  acct_curr_cyc_credit    DECIMAL(12,2)  NOT NULL COMMENT 'ACCT-CURR-CYC-CREDIT S9(10)V99',
  acct_curr_cyc_debit     DECIMAL(12,2)  NOT NULL COMMENT 'ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3 in source',
  acct_addr_zip           STRING                  COMMENT 'ACCT-ADDR-ZIP PIC X(10)',
  acct_group_id           STRING                  COMMENT 'ACCT-GROUP-ID PIC X(10) — links to disclosure_group table',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL COMMENT 'When this record was loaded to Silver',
  _silver_pipeline_run_id STRING         NOT NULL,
  _silver_source_extract_date DATE
) USING DELTA
PARTITIONED BY (CAST(acct_id / 10000000000 AS INT))  -- partition by leading digit of 11-digit ID
COMMENT 'Silver: Account master records (CVACT01Y, ACCTFILE VSAM KSDS)';

ALTER TABLE carddemo.silver.account ADD CONSTRAINT pk_account PRIMARY KEY (acct_id) NOT ENFORCED;
```

**Z-ORDER:** `acct_group_id`, `acct_active_status`

---

### 4.2 `carddemo.silver.card`
**Source:** `bronze.card_raw`  
**Copybook:** CVACT02Y

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.card (
  card_num                STRING         NOT NULL COMMENT 'CARD-NUM PIC X(16) — primary key',
  card_acct_id            BIGINT         NOT NULL COMMENT 'CARD-ACCT-ID PIC 9(11) — FK to silver.account',
  card_cvv_cd             INTEGER                 COMMENT 'CARD-CVV-CD PIC 9(3)',
  card_embossed_name      STRING                  COMMENT 'CARD-EMBOSSED-NAME PIC X(50)',
  card_expiraion_date     STRING                  COMMENT 'CARD-EXPIRAION-DATE PIC X(10) — kept as string (MM/YY format)',
  card_active_status      STRING         NOT NULL COMMENT 'CARD-ACTIVE-STATUS PIC X(1)',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL,
  _silver_pipeline_run_id STRING         NOT NULL,
  _silver_source_extract_date DATE
) USING DELTA
COMMENT 'Silver: Credit card master records (CVACT02Y, CARDFILE VSAM KSDS)';

ALTER TABLE carddemo.silver.card ADD CONSTRAINT pk_card PRIMARY KEY (card_num) NOT ENFORCED;
ALTER TABLE carddemo.silver.card ADD CONSTRAINT fk_card_account FOREIGN KEY (card_acct_id) REFERENCES carddemo.silver.account (acct_id) NOT ENFORCED;
```

**Z-ORDER:** `card_acct_id`, `card_active_status`

---

### 4.3 `carddemo.silver.customer`
**Source:** `bronze.cust_raw`  
**Copybook:** CVCUS01Y

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.customer (
  cust_id                 BIGINT         NOT NULL COMMENT 'CUST-ID PIC 9(9) — primary key',
  cust_first_name         STRING                  COMMENT 'CUST-FIRST-NAME PIC X(25)',
  cust_middle_name        STRING                  COMMENT 'CUST-MIDDLE-NAME PIC X(25)',
  cust_last_name          STRING                  COMMENT 'CUST-LAST-NAME PIC X(25)',
  cust_addr_line_1        STRING                  COMMENT 'CUST-ADDR-LINE-1 PIC X(50)',
  cust_addr_line_2        STRING                  COMMENT 'CUST-ADDR-LINE-2 PIC X(50)',
  cust_addr_line_3        STRING                  COMMENT 'CUST-ADDR-LINE-3 PIC X(50)',
  cust_addr_state_cd      STRING                  COMMENT 'CUST-ADDR-STATE-CD PIC X(2)',
  cust_addr_country_cd    STRING                  COMMENT 'CUST-ADDR-COUNTRY-CD PIC X(3)',
  cust_addr_zip           STRING                  COMMENT 'CUST-ADDR-ZIP PIC X(10)',
  cust_phone_num_1        STRING                  COMMENT 'CUST-PHONE-NUM-1 PIC X(15)',
  cust_phone_num_2        STRING                  COMMENT 'CUST-PHONE-NUM-2 PIC X(15)',
  cust_ssn                STRING                  COMMENT 'CUST-SSN PIC 9(9) — PII: stored encrypted in production',
  cust_govt_issued_id     STRING                  COMMENT 'CUST-GOVT-ISSUED-ID PIC X(20)',
  cust_dob                DATE                    COMMENT 'CUST-DOB-YYYY-MM-DD PIC X(10)',
  cust_eft_account_id     STRING                  COMMENT 'CUST-EFT-ACCOUNT-ID PIC X(10)',
  cust_pri_card_holder_ind STRING                 COMMENT 'CUST-PRI-CARD-HOLDER-IND PIC X(1)',
  cust_fico_credit_score  INTEGER                 COMMENT 'CUST-FICO-CREDIT-SCORE PIC 9(3)',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL,
  _silver_pipeline_run_id STRING         NOT NULL,
  _silver_source_extract_date DATE
) USING DELTA
COMMENT 'Silver: Customer master records (CVCUS01Y, CUSTFILE VSAM KSDS)';

ALTER TABLE carddemo.silver.customer ADD CONSTRAINT pk_customer PRIMARY KEY (cust_id) NOT ENFORCED;
```

---

### 4.4 `carddemo.silver.card_xref`
**Source:** `bronze.xref_raw`  
**Copybook:** CVACT03Y

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.card_xref (
  card_num                STRING         NOT NULL COMMENT 'XREF-CARD-NUM PIC X(16) — primary key',
  cust_id                 BIGINT         NOT NULL COMMENT 'XREF-CUST-ID PIC 9(9) — FK to silver.customer',
  acct_id                 BIGINT         NOT NULL COMMENT 'XREF-ACCT-ID PIC 9(11) — FK to silver.account',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL,
  _silver_pipeline_run_id STRING         NOT NULL,
  _silver_source_extract_date DATE
) USING DELTA
COMMENT 'Silver: Card-to-account-to-customer cross-reference (CVACT03Y, CCXREF VSAM KSDS)';

ALTER TABLE carddemo.silver.card_xref ADD CONSTRAINT pk_card_xref PRIMARY KEY (card_num) NOT ENFORCED;
```

**Z-ORDER:** `acct_id`, `cust_id`

---

### 4.5 `carddemo.silver.transaction`
**Source:** `bronze.transact_raw` + `bronze.daily_transactions` (via CBTRN02C)  
**Copybook:** CVTRA05Y  
**Partitioned by:** Year and month of `tran_proc_ts`

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.transaction (
  tran_id                 STRING         NOT NULL COMMENT 'TRAN-ID PIC X(16) — primary key',
  tran_type_cd            STRING         NOT NULL COMMENT 'TRAN-TYPE-CD PIC X(2)',
  tran_cat_cd             INTEGER        NOT NULL COMMENT 'TRAN-CAT-CD PIC 9(4)',
  tran_source             STRING                  COMMENT 'TRAN-SOURCE PIC X(10) — e.g., System for interest charges',
  tran_desc               STRING                  COMMENT 'TRAN-DESC PIC X(100)',
  tran_amt                DECIMAL(11,2)  NOT NULL COMMENT 'TRAN-AMT S9(9)V99 — positive=credit, negative=debit',
  tran_merchant_id        BIGINT                  COMMENT 'TRAN-MERCHANT-ID PIC 9(9)',
  tran_merchant_name      STRING                  COMMENT 'TRAN-MERCHANT-NAME PIC X(50)',
  tran_merchant_city      STRING                  COMMENT 'TRAN-MERCHANT-CITY PIC X(50)',
  tran_merchant_zip       STRING                  COMMENT 'TRAN-MERCHANT-ZIP PIC X(10)',
  tran_card_num           STRING         NOT NULL COMMENT 'TRAN-CARD-NUM PIC X(16) — FK to silver.card',
  tran_orig_ts            TIMESTAMP               COMMENT 'TRAN-ORIG-TS PIC X(26) — original transaction timestamp',
  tran_proc_ts            TIMESTAMP      NOT NULL COMMENT 'TRAN-PROC-TS PIC X(26) — processing timestamp (set by CBTRN02C)',
  tran_year               INT            NOT NULL COMMENT 'Derived: YEAR(tran_proc_ts) — partition column',
  tran_month              INT            NOT NULL COMMENT 'Derived: MONTH(tran_proc_ts) — partition column',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL,
  _silver_pipeline_run_id STRING         NOT NULL,
  _silver_source_system   STRING                  COMMENT 'VSAM_TRANSACT or CBTRN02C_POSTING or CBACT04C_INTEREST'
) USING DELTA
PARTITIONED BY (tran_year, tran_month)
COMMENT 'Silver: Transaction records (CVTRA05Y, TRANSACT VSAM KSDS + daily postings from CBTRN02C + interest from CBACT04C)';

ALTER TABLE carddemo.silver.transaction ADD CONSTRAINT pk_transaction PRIMARY KEY (tran_id) NOT ENFORCED;
```

**Z-ORDER:** `tran_card_num`, `tran_type_cd`, `tran_cat_cd`

---

### 4.6 `carddemo.silver.tran_cat_balance`
**Source:** `bronze.tran_cat_balance_raw` (TCATBALF VSAM KSDS)  
**Copybook:** CVTRA01Y  
**Key:** Composite `(acct_id, tran_type_cd, tran_cat_cd)`

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.tran_cat_balance (
  acct_id                 BIGINT         NOT NULL COMMENT 'TRANCAT-ACCT-ID PIC 9(11) — part of composite key',
  tran_type_cd            STRING         NOT NULL COMMENT 'TRANCAT-TYPE-CD PIC X(2) — part of composite key',
  tran_cat_cd             INTEGER        NOT NULL COMMENT 'TRANCAT-CD PIC 9(4) — part of composite key',
  tran_cat_bal            DECIMAL(11,2)  NOT NULL COMMENT 'TRAN-CAT-BAL S9(9)V99 — running balance for this category',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL,
  _silver_pipeline_run_id STRING         NOT NULL,
  _silver_last_updated_ts TIMESTAMP               COMMENT 'Last time CBTRN02C or CBACT04C updated this record'
) USING DELTA
COMMENT 'Silver: Transaction category balance table (CVTRA01Y, TCATBALF VSAM KSDS) — composite key';

ALTER TABLE carddemo.silver.tran_cat_balance ADD CONSTRAINT pk_tran_cat_balance PRIMARY KEY (acct_id, tran_type_cd, tran_cat_cd) NOT ENFORCED;
```

**Z-ORDER:** `acct_id`

---

### 4.7 `carddemo.silver.disclosure_group`
**Source:** `bronze.disclosure_group_raw` (DISCGRP VSAM KSDS)  
**Copybook:** CVTRA02Y

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.disclosure_group (
  dis_acct_group_id       STRING         NOT NULL COMMENT 'FD-DIS-ACCT-GROUP-ID PIC X(10) — DEFAULT for fallback',
  dis_tran_type_cd        STRING         NOT NULL COMMENT 'FD-DIS-TRAN-TYPE-CD PIC X(2)',
  dis_tran_cat_cd         INTEGER        NOT NULL COMMENT 'FD-DIS-TRAN-CAT-CD PIC 9(4)',
  dis_int_rate            DECIMAL(7,4)   NOT NULL COMMENT 'DIS-INT-RATE — annual interest rate (e.g., 18.0000 = 18%)',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL,
  _silver_pipeline_run_id STRING         NOT NULL
) USING DELTA
COMMENT 'Silver: Disclosure group interest rates (CVTRA02Y, DISCGRP VSAM KSDS) — broadcast join candidate';

ALTER TABLE carddemo.silver.disclosure_group ADD CONSTRAINT pk_disclosure_group PRIMARY KEY (dis_acct_group_id, dis_tran_type_cd, dis_tran_cat_cd) NOT ENFORCED;
```

**Note:** This table qualifies for broadcast join in CBACT04C interest calculation (small, fully fits in memory).

---

### 4.8 `carddemo.silver.auth_summary`
**Source:** IMS DBPAUTP0 PAUTSUM0 segments (100 bytes each)  
**Copybook:** CIPAUSMY  
**IMS Equivalent:** Parent segment keyed by account ID

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.auth_summary (
  pa_acct_id              BIGINT         NOT NULL COMMENT 'Account ID — PAUTSUM0 root segment key (card number in some contexts)',
  pa_approved_auth_cnt    INTEGER        NOT NULL COMMENT 'PA-APPROVED-AUTH-CNT — count of approved auth records',
  pa_approved_auth_amt    DECIMAL(13,2)           COMMENT 'PA-APPROVED-AUTH-AMT — sum of approved auth amounts',
  pa_declined_auth_cnt    INTEGER        NOT NULL COMMENT 'PA-DECLINED-AUTH-CNT — count of declined auth records',
  pa_declined_auth_amt    DECIMAL(13,2)           COMMENT 'PA-DECLINED-AUTH-AMT — sum of declined auth amounts',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL,
  _silver_pipeline_run_id STRING         NOT NULL,
  _silver_last_purge_ts   TIMESTAMP               COMMENT 'Last time CBPAUP0C processed this summary'
) USING DELTA
COMMENT 'Silver: Pending authorization summary (IMS PAUTSUM0 segments, CIPAUSMY copybook, DBPAUTP0 database)';

ALTER TABLE carddemo.silver.auth_summary ADD CONSTRAINT pk_auth_summary PRIMARY KEY (pa_acct_id) NOT ENFORCED;
```

---

### 4.9 `carddemo.silver.auth_detail`
**Source:** IMS DBPAUTP0 PAUTDTL1 segments (200 bytes each)  
**Copybook:** CIPAUDTY  
**IMS Equivalent:** Child segment under PAUTSUM0

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.auth_detail (
  pa_acct_id              BIGINT         NOT NULL COMMENT 'Parent account ID (FK to auth_summary)',
  pa_auth_date_9c         INTEGER                 COMMENT 'PA-AUTH-DATE-9C — stored as 99999 - YYDDD (inverted Julian)',
  pa_auth_date            DATE                    COMMENT 'Derived: actual auth date computed from pa_auth_date_9c',
  pa_auth_resp_code       STRING                  COMMENT 'PA-AUTH-RESP-CODE — 00=approved',
  pa_transaction_amt      DECIMAL(13,2)           COMMENT 'PA-TRANSACTION-AMT',
  pa_card_num             STRING                  COMMENT 'Card number for this authorization',
  auth_detail_seq         BIGINT         NOT NULL COMMENT 'Surrogate key — sequence within parent (replaces IMS child position)',
  is_expired              BOOLEAN        NOT NULL COMMENT 'Derived: TRUE when (CURRENT_YYDDD - auth_date) >= expiry_days',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL,
  _silver_pipeline_run_id STRING         NOT NULL,
  _silver_purge_ts        TIMESTAMP               COMMENT 'Set by CBPAUP0C when this record is logically deleted'
) USING DELTA
PARTITIONED BY (CAST(pa_auth_date / 100 AS INT))  -- partition by YYMM equivalent
COMMENT 'Silver: Pending authorization detail records (IMS PAUTDTL1 segments, CIPAUDTY copybook)';
```

**Z-ORDER:** `pa_acct_id`, `pa_card_num`, `pa_auth_resp_code`

---

### 4.10 `carddemo.silver.auth_fraud`
**Source:** DB2 table AUTHFRDS  
**Used by:** COPAUS2C (online), read by auth batch programs

```sql
CREATE TABLE IF NOT EXISTS carddemo.silver.auth_fraud (
  card_num                STRING         NOT NULL COMMENT 'Card number — primary key component',
  auth_timestamp          TIMESTAMP      NOT NULL COMMENT 'Authorization timestamp — primary key component',
  auth_amount             DECIMAL(13,2)           COMMENT 'Authorization amount',
  merchant_id             STRING                  COMMENT 'Merchant identifier',
  fraud_flag              BOOLEAN        NOT NULL COMMENT 'TRUE=fraud flagged by COPAUS2C',
  -- Silver metadata
  _silver_load_ts         TIMESTAMP      NOT NULL,
  _silver_pipeline_run_id STRING         NOT NULL
) USING DELTA
COMMENT 'Silver: Fraud-flagged authorizations (DB2 AUTHFRDS table) — populated by COPAUS2C online program';
```

---

## 5. Gold Layer Tables

### 5.1 `carddemo.gold.account_statement`
**Source:** CBSTM03A + CBSTM03B output (STMTFILE, 80 bytes/line)  
**Partitioned by:** `stmt_year`, `stmt_month`

```sql
CREATE TABLE IF NOT EXISTS carddemo.gold.account_statement (
  stmt_id                 STRING         NOT NULL COMMENT 'Surrogate statement ID',
  acct_id                 BIGINT         NOT NULL COMMENT 'Account ID',
  card_num                STRING         NOT NULL COMMENT 'Card number (from XREFFILE)',
  cust_id                 BIGINT                  COMMENT 'Customer ID',
  stmt_year               INT            NOT NULL COMMENT 'Statement year — partition column',
  stmt_month              INT            NOT NULL COMMENT 'Statement month — partition column',
  cust_full_name          STRING                  COMMENT 'Customer full name (CUST-FIRST-NAME + MIDDLE + LAST)',
  cust_addr_full          STRING                  COMMENT 'Full address concatenated',
  acct_curr_bal           DECIMAL(12,2)           COMMENT 'Account current balance at statement time',
  acct_credit_limit       DECIMAL(12,2)           COMMENT 'Credit limit at statement time',
  total_transaction_amt   DECIMAL(13,2)           COMMENT 'WS-TOTAL-AMT: sum of all transactions in statement',
  transaction_count       INTEGER                 COMMENT 'Number of transactions on this statement',
  stmt_plain_text         STRING                  COMMENT 'Full plain text statement (ST-LINE0 through ST-LINE14A concatenated)',
  stmt_html               STRING                  COMMENT 'Full HTML statement content',
  stmt_generation_ts      TIMESTAMP               COMMENT 'When CBSTM03A generated this statement',
  -- Gold metadata
  _gold_load_ts           TIMESTAMP      NOT NULL,
  _gold_pipeline_run_id   STRING         NOT NULL
) USING DELTA
PARTITIONED BY (stmt_year, stmt_month)
COMMENT 'Gold: Account statements generated by CBSTM03A/CBSTM03B (STMTFILE + HTMLFILE output)';
```

---

### 5.2 `carddemo.gold.transaction_report`
**Source:** CBTRN03C output (TRANREPT, 133 bytes/line)  
**Partitioned by:** `report_year`, `report_month`

```sql
CREATE TABLE IF NOT EXISTS carddemo.gold.transaction_report (
  report_run_id           STRING         NOT NULL COMMENT 'Links to a specific CBTRN03C run',
  report_start_date       DATE           NOT NULL COMMENT 'WS-START-DATE from DATEPARM',
  report_end_date         DATE           NOT NULL COMMENT 'WS-END-DATE from DATEPARM',
  report_year             INT            NOT NULL COMMENT 'Derived from report_start_date — partition column',
  report_month            INT            NOT NULL COMMENT 'Derived from report_start_date — partition column',
  tran_id                 STRING                  COMMENT 'TRAN-REPORT-TRANS-ID',
  acct_id                 BIGINT                  COMMENT 'TRAN-REPORT-ACCOUNT-ID (from XREF lookup)',
  tran_type_cd            STRING                  COMMENT 'TRAN-REPORT-TYPE-CD',
  tran_type_desc          STRING                  COMMENT 'TRAN-REPORT-TYPE-DESC (from TRANTYPE lookup)',
  tran_cat_cd             INTEGER                 COMMENT 'TRAN-REPORT-CAT-CD',
  tran_cat_desc           STRING                  COMMENT 'TRAN-REPORT-CAT-DESC (from TRANCATG lookup)',
  tran_source             STRING                  COMMENT 'TRAN-REPORT-SOURCE',
  tran_amt                DECIMAL(11,2)           COMMENT 'TRAN-REPORT-AMT',
  page_number             INTEGER                 COMMENT 'Page number (changes every 20 lines per WS-PAGE-SIZE)',
  line_number             INTEGER                 COMMENT 'Line number within page',
  is_page_total           BOOLEAN                 COMMENT 'TRUE for page total rows',
  is_account_total        BOOLEAN                 COMMENT 'TRUE for account total rows',
  is_grand_total          BOOLEAN                 COMMENT 'TRUE for grand total row',
  total_amount            DECIMAL(13,2)           COMMENT 'Amount for total rows (REPT-PAGE-TOTAL, REPT-ACCOUNT-TOTAL, REPT-GRAND-TOTAL)',
  -- Gold metadata
  _gold_load_ts           TIMESTAMP      NOT NULL,
  _gold_pipeline_run_id   STRING         NOT NULL
) USING DELTA
PARTITIONED BY (report_year, report_month)
COMMENT 'Gold: Transaction detail report (CBTRN03C TRANREPT output, 133-byte report lines modeled as rows)';
```

---

### 5.3 `carddemo.gold.interest_charges`
**Source:** CBACT04C output (interest transactions written to TRANSACT)  
**Partitioned by:** `charge_year`, `charge_month`

```sql
CREATE TABLE IF NOT EXISTS carddemo.gold.interest_charges (
  tran_id                 STRING         NOT NULL COMMENT 'Generated TRAN-ID (PARM-DATE + WS-TRANID-SUFFIX)',
  acct_id                 BIGINT         NOT NULL COMMENT 'Account this interest was charged to',
  card_num                STRING                  COMMENT 'Card number from XREF lookup',
  dis_acct_group_id       STRING                  COMMENT 'Account group used for rate lookup',
  tran_type_cd            STRING                  COMMENT 'Always 01 for interest charges',
  tran_cat_cd             INTEGER                 COMMENT 'Always 05 for interest charges',
  tran_cat_bal_basis      DECIMAL(11,2)           COMMENT 'TRAN-CAT-BAL: the balance used for interest calculation',
  dis_int_rate            DECIMAL(7,4)            COMMENT 'Annual interest rate from DISCGRP',
  monthly_interest        DECIMAL(11,2)           COMMENT 'WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200',
  total_interest          DECIMAL(11,2)           COMMENT 'WS-TOTAL-INT: sum of all category interests for this account',
  charge_year             INT            NOT NULL COMMENT 'Partition column',
  charge_month            INT            NOT NULL COMMENT 'Partition column',
  run_date                DATE                    COMMENT 'PARM-DATE: the JCL PARM date used as transaction ID prefix',
  -- Gold metadata
  _gold_load_ts           TIMESTAMP      NOT NULL,
  _gold_pipeline_run_id   STRING         NOT NULL
) USING DELTA
PARTITIONED BY (charge_year, charge_month)
COMMENT 'Gold: Interest charge audit detail (CBACT04C, 1300-B-WRITE-TX paragraph output)';
```

---

### 5.4 `carddemo.gold.daily_rejects`
**Source:** CBTRN02C output (DALYREJS, 430-byte records)  
**Partitioned by:** `reject_date`

```sql
CREATE TABLE IF NOT EXISTS carddemo.gold.daily_rejects (
  reject_run_id           STRING         NOT NULL COMMENT 'CBTRN02C pipeline run ID',
  reject_date             DATE           NOT NULL COMMENT 'Business date of the rejected batch',
  dalytran_id             STRING                  COMMENT 'DALYTRAN-ID from rejected record',
  dalytran_card_num       STRING                  COMMENT 'DALYTRAN-CARD-NUM from rejected record',
  dalytran_amt            DECIMAL(11,2)           COMMENT 'DALYTRAN-AMT from rejected record',
  validation_fail_reason  INTEGER        NOT NULL COMMENT 'WS-VALIDATION-FAIL-REASON: 100=invalid card, 101=acct not found, 102=overlimit, 103=expired',
  validation_fail_desc    STRING                  COMMENT 'WS-VALIDATION-FAIL-REASON-DESC: human-readable rejection message',
  raw_dalytran_data       STRING                  COMMENT 'First 350 bytes of reject record (REJECT-TRAN-DATA)',
  -- Gold metadata
  _gold_load_ts           TIMESTAMP      NOT NULL,
  _gold_pipeline_run_id   STRING         NOT NULL
) USING DELTA
PARTITIONED BY (reject_date)
COMMENT 'Gold: Daily transaction reject records (CBTRN02C DALYREJS output, 430-byte records with 80-byte trailer)';
```

---

### 5.5 `carddemo.gold.auth_purge_audit`
**Source:** CBPAUP0C execution audit  
**Partitioned by:** `purge_date`

```sql
CREATE TABLE IF NOT EXISTS carddemo.gold.auth_purge_audit (
  purge_run_id            STRING         NOT NULL,
  purge_date              DATE           NOT NULL COMMENT 'Date purge job ran',
  expiry_days_used        INTEGER                 COMMENT 'P-EXPIRY-DAYS parameter used',
  pa_acct_id              BIGINT                  COMMENT 'Account whose summary was processed',
  detail_records_deleted  INTEGER                 COMMENT 'Number of PAUTDTL1 records deleted for this account',
  summary_deleted         BOOLEAN                 COMMENT 'Whether PAUTSUM0 was also deleted',
  checkpoint_count        INTEGER                 COMMENT 'WS-NO-CHKP: checkpoints taken during run',
  total_summaries_read    BIGINT                  COMMENT 'WS-NO-SUMRY-READ',
  total_summaries_deleted BIGINT                  COMMENT 'WS-NO-SUMRY-DELETED',
  total_details_read      BIGINT                  COMMENT 'WS-NO-DTL-READ',
  total_details_deleted   BIGINT                  COMMENT 'WS-NO-DTL-DELETED',
  -- Gold metadata
  _gold_load_ts           TIMESTAMP      NOT NULL,
  _gold_pipeline_run_id   STRING         NOT NULL
) USING DELTA
PARTITIONED BY (purge_date)
COMMENT 'Gold: Authorization purge audit (CBPAUP0C statistics: summaries/details read and deleted)';
```

---

## 6. Reference Layer Tables

### 6.1 `carddemo.reference.tran_type`
**Source:** DB2 table CARDDEMO.TRNTYPE / COBTUPDT batch maintenance  
**Copybook:** DCLTRTYP

```sql
CREATE TABLE IF NOT EXISTS carddemo.reference.tran_type (
  tr_type                 STRING         NOT NULL COMMENT 'TR_TYPE CHAR(2) — primary key',
  tr_description          STRING         NOT NULL COMMENT 'TR_DESCRIPTION VARCHAR(50)',
  -- Reference metadata
  _ref_load_ts            TIMESTAMP      NOT NULL,
  _ref_pipeline_run_id    STRING         NOT NULL,
  _ref_last_maintained_by STRING                  COMMENT 'COBTUPDT (batch) or COTRTUPC (online)'
) USING DELTA
COMMENT 'Reference: Transaction type master (DB2 CARDDEMO.TRNTYPE, DCLTRTYP copybook)';

ALTER TABLE carddemo.reference.tran_type ADD CONSTRAINT pk_tran_type PRIMARY KEY (tr_type) NOT ENFORCED;
```

---

### 6.2 `carddemo.reference.tran_category`
**Source:** VSAM KSDS TRANCATG (used by CBTRN03C)  
**Copybook:** CVTRA04Y

```sql
CREATE TABLE IF NOT EXISTS carddemo.reference.tran_category (
  tran_type_cd            STRING         NOT NULL COMMENT 'FD-TRAN-TYPE-CD PIC X(2) — part of composite key',
  tran_cat_cd             INTEGER        NOT NULL COMMENT 'FD-TRAN-CAT-CD PIC 9(4) — part of composite key',
  tran_cat_desc           STRING                  COMMENT 'TRAN-CAT-TYPE-DESC — category description for reports',
  -- Reference metadata
  _ref_load_ts            TIMESTAMP      NOT NULL,
  _ref_pipeline_run_id    STRING         NOT NULL
) USING DELTA
COMMENT 'Reference: Transaction category descriptions (CVTRA04Y, TRANCATG VSAM KSDS used by CBTRN03C)';

ALTER TABLE carddemo.reference.tran_category ADD CONSTRAINT pk_tran_category PRIMARY KEY (tran_type_cd, tran_cat_cd) NOT ENFORCED;
```

---

## 7. Migration Control Tables

### 7.1 `carddemo.migration_ctrl.pipeline_metrics`

```sql
CREATE TABLE IF NOT EXISTS carddemo.migration_ctrl.pipeline_metrics (
  pipeline_name           STRING         NOT NULL COMMENT 'e.g., cbtrn02c_tran_posting',
  run_id                  STRING         NOT NULL COMMENT 'Databricks job run ID',
  run_date                DATE           NOT NULL,
  records_read            BIGINT,
  records_processed       BIGINT,
  records_rejected        BIGINT         COMMENT 'WS-REJECT-COUNT equivalent',
  records_written         BIGINT,
  return_code             INTEGER        COMMENT '0=success, 4=warning, 8+=error (COBOL RETURN-CODE semantics)',
  start_time              TIMESTAMP,
  end_time                TIMESTAMP,
  duration_seconds        DOUBLE,
  error_message           STRING
) USING DELTA
PARTITIONED BY (run_date)
COMMENT 'Migration control: Pipeline execution metrics (replaces SYSOUT statistics from COBOL programs)';
```

### 7.2 `carddemo.migration_ctrl.error_log`

```sql
CREATE TABLE IF NOT EXISTS carddemo.migration_ctrl.error_log (
  pipeline_name           STRING         NOT NULL,
  run_id                  STRING         NOT NULL,
  error_timestamp         TIMESTAMP      NOT NULL,
  error_type              STRING         NOT NULL COMMENT 'INVALID_KEY, VALIDATION_FAIL, IO_ERROR, etc.',
  error_code              STRING                  COMMENT 'Numeric code e.g., 100=invalid card, 101=acct not found',
  error_description       STRING                  COMMENT 'WS-VALIDATION-FAIL-REASON-DESC equivalent',
  source_record           STRING                  COMMENT 'JSON of the failing source record',
  run_date                DATE           NOT NULL
) USING DELTA
PARTITIONED BY (run_date)
COMMENT 'Migration control: Error quarantine log (replaces DALYREJS, ERROUT, COBOL DISPLAY error messages)';
```

---

## 8. Partitioning Strategy

| Table | Partition Column(s) | Rationale |
|-------|--------------------|---------||
| `bronze.*_raw` | `_meta_extract_date` | Supports incremental processing; prune by extraction date |
| `silver.transaction` | `tran_year`, `tran_month` | CBTRN03C date-range reports; interest calculation by month |
| `silver.auth_detail` | `CAST(pa_auth_date/100 AS INT)` | CBPAUP0C date-based expiry deletion |
| `gold.account_statement` | `stmt_year`, `stmt_month` | Monthly statement cycles; one partition = one monthly run |
| `gold.transaction_report` | `report_year`, `report_month` | Report date ranges; matches CBTRN03C DATEPARM ranges |
| `gold.interest_charges` | `charge_year`, `charge_month` | Matches CBACT04C monthly interest cycle |
| `gold.daily_rejects` | `reject_date` | Daily posting cycle; prune by business date |
| `gold.auth_purge_audit` | `purge_date` | Daily purge cycle |
| `migration_ctrl.*` | `run_date` | Operational date-based management |
| `reference.*` | None | Small tables; no benefit from partitioning |
| `silver.account` | First digit of `acct_id` | Distribute 11-digit account IDs evenly |
| `bronze.export_raw` | `_meta_extract_date`, `export_rec_type` | CBIMPORT processes by record type |

---

## 9. Z-Ordering Strategy

| Table | Z-Order Columns | Rationale |
|-------|----------------|-----------|
| `silver.account` | `acct_group_id`, `acct_active_status` | CBACT04C joins by group_id; filter by active_status |
| `silver.card` | `card_acct_id`, `card_active_status` | Auth checks by account_id; status filter common |
| `silver.card_xref` | `acct_id`, `cust_id` | CBTRN01C/02C/03C all do random lookup by card_num (primary key); account filter common |
| `silver.transaction` | `tran_card_num`, `tran_type_cd`, `tran_cat_cd` | CBTRN03C groups by card_num; CBACT04C by type/cat |
| `silver.tran_cat_balance` | `acct_id` | CBACT04C and CBTRN02C both access by account_id |
| `silver.auth_detail` | `pa_acct_id`, `pa_card_num`, `pa_auth_resp_code` | CBPAUP0C deletes by account; filter by resp_code |
| `bronze.acct_raw` | `acct_id_raw` | Ingestion pipeline lookups |

---

## 10. Schema Evolution Approach

### 10.1 Bronze Layer
- **Policy:** `mergeSchema = true` on all writes
- **Rationale:** Mainframe extracts may add new fields during phased migration
- **Breaking changes:** Prohibited; new columns only

### 10.2 Silver Layer
- **Policy:** Additive schema evolution only (new nullable columns)
- **Versioning:** Existing column renames require new table version with `_v2` suffix
- **Breaking changes:** Require data migration plan + cutover window

### 10.3 Gold Layer
- **Policy:** Rebuild on structural changes (drop and recreate from Silver)
- **Versioning:** Tag with `_v{n}` suffix for structural changes

---

## 11. Data Retention and Archival Policy

| Layer | Retention Period | Archival Action | Replaces |
|-------|-----------------|-----------------|---------|
| Bronze | 90 days rolling | Delete partitions older than 90 days | VSAM file management JCLs |
| Silver (transactions) | 7 years | Move to cold storage tier after 2 years | TRANBKP.jcl backup strategy |
| Silver (master data) | Indefinite | N/A (small tables) | VSAM cluster definitions |
| Gold (statements) | 7 years | Cold tier after 3 years | Statement archive tapes |
| Gold (reports) | 3 years | Cold tier after 1 year | Report tape management |
| Gold (audit) | 7 years | Cold tier after 2 years | Audit file archives |
| Auth data (detail) | 30 days active | Purged by CBPAUP0C equivalent daily | IMS DBPAUTP0 expiry policy |
| Auth data (summary) | Purged with last detail | Cascade delete | IMS database maintenance |
| Migration control | 1 year | Archive to cold | N/A (new in cloud) |
