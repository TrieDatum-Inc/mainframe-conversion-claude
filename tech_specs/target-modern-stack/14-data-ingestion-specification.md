# CardDemo Data Ingestion Specification
## Mainframe-to-Delta Lake Ingestion — All Source Data Stores

**Document Version:** 1.0  
**Date:** 2026-04-06  
**Catalog:** `carddemo`  
**Target Schema:** `carddemo.bronze` (landing layer)

---

## Table of Contents

1. [Ingestion Architecture Overview](#1-ingestion-architecture-overview)
2. [VSAM File Extraction and Ingestion](#2-vsam-file-extraction-and-ingestion)
3. [DB2 Table Extraction and Ingestion](#3-db2-table-extraction-and-ingestion)
4. [IMS Database Extraction and Ingestion](#4-ims-database-extraction-and-ingestion)
5. [Sequential and Flat File Parsing](#5-sequential-and-flat-file-parsing)
6. [Initial Full Load Strategy](#6-initial-full-load-strategy)
7. [Incremental and Delta Load Strategy](#7-incremental-and-delta-load-strategy)
8. [Data Validation and Reconciliation](#8-data-validation-and-reconciliation)
9. [SLA and Scheduling Requirements](#9-sla-and-scheduling-requirements)
10. [Landing Zone Specifications](#10-landing-zone-specifications)
11. [Error Handling and Recovery](#11-error-handling-and-recovery)

---

## 1. Ingestion Architecture Overview

### 1.1 End-to-End Ingestion Flow

```
Mainframe z/OS
┌──────────────────────────────────────────────────────┐
│  VSAM KSDS Files    DB2 Tables    IMS Databases      │
│  ACCTDAT CARDDAT    TRNTYPE       PAUTHDTL            │
│  CCXREF  CUSTDAT    AUTHFRDS      PAUTHSUM            │
│  TRANSACT USRSEC    TRNTYCAT                          │
└────────────┬────────────┬──────────────┬─────────────┘
             │ AWS DMS    │ AWS DMS      │ IMS Connect
             │ (VSAM CDC) │ (DB2 CDC)    │ + Custom
             ▼            ▼              ▼
┌──────────────────────────────────────────────────────┐
│           AWS S3 Landing Zone                        │
│  s3://carddemo-landing/                              │
│    vsam/{filename}/full/YYYYMMDD/                    │
│    vsam/{filename}/cdc/YYYYMMDD/HH/                  │
│    db2/{tablename}/full/YYYYMMDD/                    │
│    db2/{tablename}/cdc/YYYYMMDD/HH/                  │
│    ims/{dbname}/full/YYYYMMDD/                       │
│    flatfiles/{jobname}/YYYYMMDD/                     │
└────────────────────────┬─────────────────────────────┘
                         │ Databricks Auto Loader /
                         │ Structured Streaming
                         ▼
┌──────────────────────────────────────────────────────┐
│           carddemo.bronze (Delta Lake)               │
│  Raw records with ingestion metadata columns         │
│  Preserves source bytes; no business transformation  │
└──────────────────────────────────────────────────────┘
                         │ Silver pipeline
                         ▼
┌──────────────────────────────────────────────────────┐
│           carddemo.silver (Delta Lake)               │
│  Parsed, typed, validated, deduplicated records      │
└──────────────────────────────────────────────────────┘
```

### 1.2 Ingestion Metadata Columns

Every Bronze table includes the following ingestion metadata columns appended to every record. These columns do not exist in the mainframe source and are added exclusively during ingestion.

| Column | Type | Purpose |
|--------|------|---------|
| `_ingest_ts` | `TimestampType()` | UTC timestamp when record landed in Bronze |
| `_ingest_run_id` | `StringType()` | Databricks job run ID for lineage |
| `_source_file` | `StringType()` | Full S3 path of source file |
| `_source_system` | `StringType()` | One of: `VSAM`, `DB2`, `IMS`, `FLATFILE` |
| `_source_dataset` | `StringType()` | Dataset name on mainframe (e.g., `AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS`) |
| `_load_type` | `StringType()` | `FULL` or `CDC` |
| `_record_offset` | `LongType()` | Byte offset in source file (for fixed-width files) |
| `_raw_bytes` | `BinaryType()` | Original fixed-width record bytes (Bronze only; null for DB2) |
| `_op_type` | `StringType()` | For CDC records: `I` (insert), `U` (update), `D` (delete); `F` for full load |
| `_cdc_ts` | `TimestampType()` | CDC event timestamp from source (null for full loads) |

### 1.3 Extraction Tool Selection

| Source Type | Extraction Tool | Rationale |
|-------------|----------------|-----------|
| VSAM KSDS (full) | AWS Mainframe Modernization — VSAM to S3 export job | Native EBCDIC-aware; preserves packed decimal bytes |
| VSAM KSDS (incremental) | AWS DMS with VSAM CDC connector | Captures VSAM file updates in near-real-time |
| DB2 (full) | AWS DMS full load task | Native DB2 JDBC connection |
| DB2 (incremental) | AWS DMS CDC with DB2 log reader | DB2 log-based CDC; minimal impact on source |
| IMS (full) | Custom JCL batch unload (PAUDBUNL / DBUNLDGS) | IMS does not expose JDBC; batch unload is the only viable path |
| IMS (incremental) | IMS Connect + CDC adapter or daily full reload | IMS CDC tooling is complex; daily full reload preferred unless volume warrants CDC |
| Sequential/flat files | Direct S3 transfer via SFTP/MFT gateway | JCL job outputs copied to S3 post-run |
| MQ messages | Kafka Connect MQ Source Connector | Real-time streaming to Kafka; consumed by Structured Streaming |

---

## 2. VSAM File Extraction and Ingestion

### 2.1 VSAM File Inventory

| CICS DD Name | Mainframe Dataset | Type | Key Field | Record Length | Copybook |
|-------------|-------------------|------|-----------|---------------|----------|
| ACCTDAT | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | KSDS | Account ID (bytes 1–11) | 300 bytes | CVACT01Y |
| CARDDAT | AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS | KSDS | Card Number (bytes 1–16) | 150 bytes | CVACT02Y |
| CARDAIX | AWS.M2.CARDDEMO.CARDDATA.VSAM.AIX.PATH | AIX Path | Account ID (alternate) | 150 bytes | CVACT02Y (via base) |
| CCXREF | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | KSDS | Card Number (bytes 1–16) | 50 bytes | CVACT03Y |
| CXACAIX | AWS.M2.CARDDEMO.CARDXREF.VSAM.AIX.PATH | AIX Path | Account ID (alternate) | 50 bytes | CVACT03Y (via base) |
| CUSTDAT | AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | KSDS | Customer ID (bytes 1–9) | 500 bytes | CVCUS01Y |
| TRANSACT | AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | KSDS | Transaction ID (bytes 1–16) | 350 bytes | CVTRA05Y |
| USRSEC | AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS | KSDS | User ID (bytes 1–8) | Variable (~80 bytes) | Internal |

### 2.2 ACCTDAT — Account Master File

#### Extraction Configuration

```
Source:       AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS
Tool:         AWS Mainframe Modernization batch export job
Output:       s3://carddemo-landing/vsam/acctdat/full/YYYYMMDD/acctdat_full.bin
Format:       Fixed-width binary, EBCDIC, 300 bytes per record
Encoding:     EBCDIC IBM-037 (convert to UTF-8 during Bronze parse)
```

#### Field Parsing Specification (CVACT01Y Copybook)

| Byte Range | Field Name | COBOL PIC | Length | Encoding | Bronze Column | Parse Action |
|-----------|-----------|-----------|--------|----------|---------------|-------------|
| 1–11 | ACCT-ID | 9(11) | 11 | EBCDIC zoned decimal | `acct_id_raw` | `StringType()` — cast to `LongType()` in Silver |
| 12 | ACCT-ACTIVE-STATUS | X(1) | 1 | EBCDIC | `acct_active_status` | `StringType()` |
| 13–24 | ACCT-CURR-BAL | S9(10)V99 COMP-3 | 6 (packed) | Packed decimal | `acct_curr_bal_raw` | Unpack COMP-3 → `DecimalType(12,2)` |
| 25–36 | ACCT-CREDIT-LIMIT | S9(10)V99 COMP-3 | 6 (packed) | Packed decimal | `acct_credit_limit_raw` | Unpack COMP-3 → `DecimalType(12,2)` |
| 37–48 | ACCT-CASH-CREDIT-LIMIT | S9(10)V99 COMP-3 | 6 (packed) | Packed decimal | `acct_cash_credit_limit_raw` | Unpack COMP-3 → `DecimalType(12,2)` |
| 49–58 | ACCT-OPEN-DATE | X(10) | 10 | EBCDIC | `acct_open_date_raw` | `StringType()` (YYYY-MM-DD format) |
| 59–68 | ACCT-EXPIRAION-DATE | X(10) | 10 | EBCDIC | `acct_expiraion_date_raw` | `StringType()` (YYYY-MM-DD format) |
| 69–78 | ACCT-REISSUE-DATE | X(10) | 10 | EBCDIC | `acct_reissue_date_raw` | `StringType()` (YYYY-MM-DD format) |
| 79–90 | ACCT-CURR-CYC-CREDIT | S9(10)V99 COMP-3 | 6 (packed) | Packed decimal | `acct_curr_cyc_credit_raw` | Unpack COMP-3 → `DecimalType(12,2)` |
| 91–96 | ACCT-CURR-CYC-DEBIT | S9(10)V99 COMP-3 | 6 (packed) | Packed decimal | `acct_curr_cyc_debit_raw` | Unpack COMP-3 → `DecimalType(12,2)` |
| 97–106 | ACCT-ADDR-ZIP | X(10) | 10 | EBCDIC | `acct_addr_zip` | `StringType()` |
| 107–116 | ACCT-GROUP-ID | X(10) | 10 | EBCDIC | `acct_group_id` | `StringType()` |
| 117–300 | FILLER | X(178) | 178 | — | — | Omit |

**Note on byte ranges:** The exact byte layout depends on the compiled copybook structure with COMP-3 packing. The ranges above are approximate. Actual byte offsets must be validated against the compiled DMAP listing during migration testing.

#### Bronze Table Load

```
Target:       carddemo.bronze.acct_raw
Write Mode:   MERGE on acct_id_raw (upsert for CDC; overwrite partition for full load)
Partition:    load_date (daily)
```

#### CDC Strategy

- **Tool:** AWS DMS with VSAM CDC source
- **Trigger:** Any WRITE, REWRITE, or DELETE to ACCTDAT
- **CDC output path:** `s3://carddemo-landing/vsam/acctdat/cdc/YYYYMMDD/HH/`
- **CDC format:** AWS DMS CSV with operation column (`INSERT`, `UPDATE`, `DELETE`)
- **Frequency:** Near-real-time during batch window; captured and applied post-batch

### 2.3 CARDDAT — Card Master File

#### Extraction Configuration

```
Source:       AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS
Tool:         AWS Mainframe Modernization batch export
Output:       s3://carddemo-landing/vsam/carddat/full/YYYYMMDD/carddat_full.bin
Format:       Fixed-width binary, EBCDIC, 150 bytes per record
```

#### Field Parsing Specification (CVACT02Y Copybook)

| Byte Range | Field Name | COBOL PIC | Length | Encoding | Bronze Column | Parse Action |
|-----------|-----------|-----------|--------|----------|---------------|-------------|
| 1–16 | CARD-NUM | X(16) | 16 | EBCDIC | `card_num` | `StringType()` — trim trailing spaces |
| 17–27 | CARD-ACCT-ID | 9(11) | 11 | EBCDIC zoned decimal | `card_acct_id_raw` | `StringType()` → `LongType()` in Silver |
| 28–30 | CARD-CVV-CD | 9(3) | 3 | EBCDIC zoned decimal | `card_cvv_cd_raw` | `StringType()` → `IntegerType()` in Silver |
| 31–80 | CARD-EMBOSSED-NAME | X(50) | 50 | EBCDIC | `card_embossed_name` | `StringType()` — trim trailing spaces |
| 81–90 | CARD-EXPIRAION-DATE | X(10) | 10 | EBCDIC | `card_expiraion_date_raw` | `StringType()` (MM/YY format — NOT YYYY-MM-DD) |
| 91 | CARD-ACTIVE-STATUS | X(1) | 1 | EBCDIC | `card_active_status` | `StringType()` |
| 92–150 | FILLER | X(59) | 59 | — | — | Omit |

**Important:** CARD-EXPIRAION-DATE uses MM/YY format (not YYYY-MM-DD). Silver pipeline must handle this non-standard format. Spell as "EXPIRAION" (matching original typo in copybook) for traceability.

**AIX Path (CARDAIX):** The alternate index CARDAIX is not independently extracted. CARDDAT full extract covers all records. The AIX is used by CICS for account-ID-keyed lookups; in Delta Lake this is replaced by a simple filter on `card_acct_id`.

#### Bronze Table Load

```
Target:       carddemo.bronze.card_raw
Write Mode:   MERGE on card_num (upsert for CDC; overwrite partition for full load)
Partition:    load_date (daily)
```

### 2.4 CCXREF — Card-Account Cross-Reference File

#### Extraction Configuration

```
Source:       AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS
Tool:         AWS Mainframe Modernization batch export
Output:       s3://carddemo-landing/vsam/ccxref/full/YYYYMMDD/ccxref_full.bin
Format:       Fixed-width binary, EBCDIC, 50 bytes per record
```

#### Field Parsing Specification (CVACT03Y Copybook)

| Byte Range | Field Name | COBOL PIC | Length | Encoding | Bronze Column | Parse Action |
|-----------|-----------|-----------|--------|----------|---------------|-------------|
| 1–16 | XREF-CARD-NUM | X(16) | 16 | EBCDIC | `xref_card_num` | `StringType()` |
| 17–25 | XREF-CUST-ID | 9(9) | 9 | EBCDIC zoned decimal | `xref_cust_id_raw` | `StringType()` → `LongType()` in Silver |
| 26–36 | XREF-ACCT-ID | 9(11) | 11 | EBCDIC zoned decimal | `xref_acct_id_raw` | `StringType()` → `LongType()` in Silver |
| 37–50 | FILLER | X(14) | 14 | — | — | Omit |

**AIX Path (CXACAIX):** Same rationale as CARDAIX — not extracted separately; replaced by DataFrame filter.

#### Bronze Table Load

```
Target:       carddemo.bronze.xref_raw
Write Mode:   MERGE on xref_card_num
Partition:    load_date (daily)
```

### 2.5 CUSTDAT — Customer Master File

#### Extraction Configuration

```
Source:       AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS
Tool:         AWS Mainframe Modernization batch export
Output:       s3://carddemo-landing/vsam/custdat/full/YYYYMMDD/custdat_full.bin
Format:       Fixed-width binary, EBCDIC, 500 bytes per record
```

#### Field Parsing Specification (CVCUS01Y Copybook)

| Byte Range | Field Name | COBOL PIC | Length | Encoding | Bronze Column | Parse Action |
|-----------|-----------|-----------|--------|----------|---------------|-------------|
| 1–9 | CUST-ID | 9(9) | 9 | EBCDIC zoned decimal | `cust_id_raw` | `StringType()` → `LongType()` in Silver |
| 10–34 | CUST-FIRST-NAME | X(25) | 25 | EBCDIC | `cust_first_name` | `StringType()` — trim |
| 35–59 | CUST-MIDDLE-NAME | X(25) | 25 | EBCDIC | `cust_middle_name` | `StringType()` — trim |
| 60–84 | CUST-LAST-NAME | X(25) | 25 | EBCDIC | `cust_last_name` | `StringType()` — trim |
| 85–134 | CUST-ADDR-LINE-1 | X(50) | 50 | EBCDIC | `cust_addr_line_1` | `StringType()` — trim |
| 135–184 | CUST-ADDR-LINE-2 | X(50) | 50 | EBCDIC | `cust_addr_line_2` | `StringType()` — trim |
| 185–234 | CUST-ADDR-LINE-3 | X(50) | 50 | EBCDIC | `cust_addr_line_3` | `StringType()` — trim |
| 235–236 | CUST-ADDR-STATE-CD | X(2) | 2 | EBCDIC | `cust_addr_state_cd` | `StringType()` |
| 237–239 | CUST-ADDR-COUNTRY-CD | X(3) | 3 | EBCDIC | `cust_addr_country_cd` | `StringType()` |
| 240–249 | CUST-ADDR-ZIP | X(10) | 10 | EBCDIC | `cust_addr_zip` | `StringType()` |
| 250–264 | CUST-PHONE-NUM-1 | X(15) | 15 | EBCDIC | `cust_phone_num_1` | `StringType()` — trim |
| 265–279 | CUST-PHONE-NUM-2 | X(15) | 15 | EBCDIC | `cust_phone_num_2` | `StringType()` — trim |
| 280–288 | CUST-SSN | 9(9) | 9 | EBCDIC zoned decimal | `cust_ssn_raw` | `StringType()` — **do not cast to integer; treat as PII string** |
| 289–308 | CUST-GOVT-ISSUED-ID | X(20) | 20 | EBCDIC | `cust_govt_issued_id` | `StringType()` — PII; encrypt at rest |
| 309–318 | CUST-DOB-YYYY-MM-DD | X(10) | 10 | EBCDIC | `cust_dob_raw` | `StringType()` (YYYY-MM-DD) → `DateType()` in Silver |
| 319–328 | CUST-EFT-ACCOUNT-ID | X(10) | 10 | EBCDIC | `cust_eft_account_id` | `StringType()` |
| 329 | CUST-PRI-CARD-HOLDER-IND | X(1) | 1 | EBCDIC | `cust_pri_card_holder_ind` | `StringType()` |
| 330–332 | CUST-FICO-CREDIT-SCORE | 9(3) | 3 | EBCDIC zoned decimal | `cust_fico_credit_score_raw` | `StringType()` → `IntegerType()` in Silver |
| 333–500 | FILLER | X(168) | 168 | — | — | Omit |

**PII Handling:** `cust_ssn_raw`, `cust_govt_issued_id`, `cust_dob_raw` are PII fields. Bronze table must be stored in an encrypted S3 bucket with restricted IAM access. Silver table must use column-level encryption or masking via Databricks column masking policies.

#### Bronze Table Load

```
Target:       carddemo.bronze.cust_raw
Write Mode:   MERGE on cust_id_raw
Partition:    load_date (daily)
```

### 2.6 TRANSACT — Transaction File

#### Extraction Configuration

```
Source:       AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS
Tool:         AWS Mainframe Modernization batch export
Output:       s3://carddemo-landing/vsam/transact/full/YYYYMMDD/transact_full.bin
Format:       Fixed-width binary, EBCDIC, 350 bytes per record
```

#### Field Parsing Specification (CVTRA05Y Copybook)

| Byte Range | Field Name | COBOL PIC | Length | Encoding | Bronze Column | Parse Action |
|-----------|-----------|-----------|--------|----------|---------------|-------------|
| 1–16 | TRAN-ID | X(16) | 16 | EBCDIC | `tran_id` | `StringType()` — trim |
| 17–18 | TRAN-TYPE-CD | X(2) | 2 | EBCDIC | `tran_type_cd` | `StringType()` |
| 19–22 | TRAN-CAT-CD | 9(4) | 4 | EBCDIC zoned decimal | `tran_cat_cd_raw` | `StringType()` → `IntegerType()` in Silver |
| 23–32 | TRAN-SOURCE | X(10) | 10 | EBCDIC | `tran_source` | `StringType()` — trim |
| 33–132 | TRAN-DESC | X(100) | 100 | EBCDIC | `tran_desc` | `StringType()` — trim |
| 133–143 | TRAN-AMT | S9(9)V99 COMP-3 | 6 (packed) | Packed decimal | `tran_amt_raw` | Unpack COMP-3 → `DecimalType(11,2)` |
| 144–152 | TRAN-MERCHANT-ID | 9(9) | 9 | EBCDIC zoned decimal | `tran_merchant_id_raw` | `StringType()` → `LongType()` in Silver |
| 153–202 | TRAN-MERCHANT-NAME | X(50) | 50 | EBCDIC | `tran_merchant_name` | `StringType()` — trim |
| 203–252 | TRAN-MERCHANT-CITY | X(50) | 50 | EBCDIC | `tran_merchant_city` | `StringType()` — trim |
| 253–262 | TRAN-MERCHANT-ZIP | X(10) | 10 | EBCDIC | `tran_merchant_zip` | `StringType()` |
| 263–278 | TRAN-CARD-NUM | X(16) | 16 | EBCDIC | `tran_card_num` | `StringType()` — trim |
| 279–304 | TRAN-ORIG-TS | X(26) | 26 | EBCDIC | `tran_orig_ts_raw` | `StringType()` (DB2 format YYYY-MM-DD-HH.MM.SS.mmm0000) → `TimestampType()` in Silver |
| 305–330 | TRAN-PROC-TS | X(26) | 26 | EBCDIC | `tran_proc_ts_raw` | `StringType()` → `TimestampType()` in Silver |
| 331–350 | FILLER | X(20) | 20 | — | — | Omit |

#### Bronze Table Load

```
Target:       carddemo.bronze.transact_raw
Write Mode:   MERGE on tran_id
Partition:    load_date (daily), tran_type_cd
```

**Transaction Volume Note:** TRANSACT is the highest-volume VSAM file. Initial full load may contain millions of records. Ingestion must be parallelized by splitting the binary file into 128 MB chunks and processing in parallel Spark tasks.

### 2.7 USRSEC — User Security File

#### Extraction Configuration

```
Source:       AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS
Tool:         AWS Mainframe Modernization batch export
Output:       s3://carddemo-landing/vsam/usrsec/full/YYYYMMDD/usrsec_full.bin
Format:       Fixed-width binary, EBCDIC, variable (approximately 80 bytes)
```

#### Field Parsing Specification (Internal Structure)

| Byte Range | Field Name | COBOL PIC | Bronze Column | Parse Action |
|-----------|-----------|-----------|---------------|-------------|
| 1–8 | SEC-USR-ID | X(8) | `sec_usr_id` | `StringType()` — trim |
| 9–28 | SEC-USR-PWD | X(20) | `sec_usr_pwd` | `StringType()` — **PII; encrypt** |
| 29–53 | SEC-USR-FNAME | X(25) | `sec_usr_fname` | `StringType()` — trim |
| 54–78 | SEC-USR-LNAME | X(25) | `sec_usr_lname` | `StringType()` — trim |
| 79 | SEC-USR-TYPE | X(1) | `sec_usr_type` | `StringType()` — values: 'A' (admin), 'U' (user) |

**Security Note:** This file contains plaintext passwords. The Bronze table must have the most restrictive access controls. In the target system, passwords will be migrated to a proper identity provider (e.g., AWS Cognito) and this field will be retired. The Bronze ingestion preserves it for migration validation only.

#### Bronze Table Load

```
Target:       carddemo.bronze.usrsec_raw
Write Mode:   MERGE on sec_usr_id
Partition:    load_date (daily)
Access:       Restricted — security team only
```

### 2.8 VSAM Binary Parsing — Common PySpark Pattern

All VSAM fixed-width binary files share the same parsing pattern. The canonical ingestion notebook reads the raw binary file and applies field-level extraction:

```
Parsing Steps (specification — not code):
1. Read binary file from S3 using spark.read.format("binaryFile")
2. Split each file's content into fixed-width records using byte slicing
3. For EBCDIC alphanumeric fields (PIC X): decode bytes using codecs.decode(bytes, 'cp037') → UTF-8 string
4. For EBCDIC zoned decimal fields (PIC 9): decode EBCDIC then strip zone nibbles
5. For COMP-3 packed decimal fields (PIC S9...COMP-3):
   a. Extract raw bytes from record slice
   b. Unpack nibble pairs: high nibble = digit, low nibble = next digit or sign
   c. Final nibble: 'C' or 'F' = positive, 'D' = negative
   d. Apply implicit decimal point based on V9(m) specification
6. Append ingestion metadata columns
7. Write to Bronze Delta table as parquet-backed Delta format (no raw bytes stored in Bronze — use _raw_bytes column only if debugging is enabled)
```

**EBCDIC Code Page:** IBM Code Page 037 (US English) for all CardDemo VSAM files. Verify with mainframe team if regional variant (285, 500, etc.) is in use.

---

## 3. DB2 Table Extraction and Ingestion

### 3.1 DB2 Table Inventory

| DB2 Table | Schema | Purpose | Volume | CDC Required |
|-----------|--------|---------|--------|-------------|
| TRNTYPE | CARDDEMO | Transaction type master reference | Low (< 100 rows) | No — full reload daily |
| TRNTYCAT | CARDDEMO | Transaction type category reference | Low (< 100 rows) | No — full reload daily |
| AUTHFRDS | (default) | Fraud-flagged authorization records | Medium (grows daily) | Yes |

### 3.2 TRNTYPE — Transaction Type Master

#### Extraction Configuration

```
Source:       DB2 subsystem; table CARDDEMO.TRNTYPE
Tool:         AWS DMS full load task (JDBC DB2 source)
Output:       s3://carddemo-landing/db2/trntype/full/YYYYMMDD/trntype.csv
Format:       CSV with header; UTF-8
Frequency:    Daily full reload (low volume; CDC not justified)
```

#### Schema

| DB2 Column | DB2 Type | Bronze Column | Spark Type | Notes |
|-----------|---------|---------------|------------|-------|
| TR_TYPE | CHAR(2) | `tr_type` | `StringType()` | Primary key |
| TR_TYPE_DESC | CHAR(50) | `tr_type_desc` | `StringType()` | trim trailing spaces |

#### Bronze Table Load

```
Target:       carddemo.bronze.tran_type_input  (also feeds carddemo.reference.tran_type)
Write Mode:   Overwrite (full reload; small table)
Partition:    load_date (daily)
```

### 3.3 TRNTYCAT — Transaction Type Category Reference

#### Extraction Configuration

```
Source:       DB2 subsystem; table CARDDEMO.TRNTYCAT
Tool:         AWS DMS full load task
Output:       s3://carddemo-landing/db2/trntycat/full/YYYYMMDD/trntycat.csv
Format:       CSV with header; UTF-8
Frequency:    Daily full reload
```

**Note:** TRNTYCAT is included in COBOL DCL but not actively queried in any of the 16 batch programs examined. It is extracted for completeness and loaded into a reference table. Schema must be validated against the actual DB2 catalog during migration.

#### Bronze Table Load

```
Target:       carddemo.bronze.tran_cat_input
Write Mode:   Overwrite (full reload)
```

### 3.4 AUTHFRDS — Authorization Fraud Records

#### Extraction Configuration — Full Load

```
Source:       DB2 subsystem; table AUTHFRDS
Tool:         AWS DMS full load task
Output:       s3://carddemo-landing/db2/authfrds/full/YYYYMMDD/authfrds.csv
Format:       CSV with header; UTF-8
Frequency:    Initial full load only; then CDC takes over
```

#### Extraction Configuration — CDC

```
Tool:         AWS DMS CDC task with DB2 Log Reader (LogMiner equivalent)
Output:       s3://carddemo-landing/db2/authfrds/cdc/YYYYMMDD/HH/
Format:       AWS DMS parquet with op column (I/U/D) and before/after images
Frequency:    Near-real-time; applied hourly to Bronze
Latency SLA: Applied to carddemo.bronze.auth_fraud within 1 hour of DB2 commit
```

#### Schema

| DB2 Column | DB2 Type | Bronze Column | Spark Type | Notes |
|-----------|---------|---------------|------------|-------|
| CARD_NUM | CHAR(16) | `card_num` | `StringType()` | Part of composite key |
| AUTH_TS | TIMESTAMP | `auth_ts_raw` | `StringType()` → `TimestampType()` in Silver | DB2 timestamp format |
| AUTH_AMT | DECIMAL(11,2) | `auth_amt` | `DecimalType(11,2)` | |
| MERCHANT_ID | CHAR(9) | `merchant_id` | `StringType()` | |
| FRAUD_FLAG | CHAR(1) | `fraud_flag` | `StringType()` | 'Y'/'N' |

**Note:** AUTHFRDS exact schema is not fully documented in the source specifications. The columns above are derived from program analysis of COPAUS2C. A reverse-engineering step against the DB2 catalog is required before production ingestion.

#### Bronze Table Load

```
Target:       carddemo.bronze.auth_fraud_raw
Write Mode:   MERGE on (card_num, auth_ts_raw) — upsert for CDC
Partition:    load_date (daily)
```

---

## 4. IMS Database Extraction and Ingestion

### 4.1 IMS Database Inventory

| IMS Database | DBD Name | Segment Type | Key | Record Layout | Copybook Reference |
|-------------|----------|-------------|-----|---------------|-------------------|
| Pending Auth Summary | PAUTHSUM | Root (PAUTSUM0) | Card Number (ACCNTID, 11 bytes) | 100-byte root segment | PAUDBUNL OUTFIL1 layout |
| Pending Auth Detail | PAUTHDTL | Dependent (PAUTDTL1) | Card + Inverted Timestamp | 200-byte child segment | PAUDBUNL OUTFIL2 layout |

### 4.2 Extraction Approach — Batch Unload via PAUDBUNL

IMS does not provide a direct JDBC or S3-native export path. Extraction uses the existing PAUDBUNL batch program (IMS BMP) which already writes QSAM sequential output files. The JCL job UNLDPADB.JCL is the extraction vehicle.

```
Extraction Steps:
1. Execute UNLDPADB.JCL on mainframe during the batch window (after IMS quiesce or with BMP access)
2. PAUDBUNL writes:
   a. OUTFIL1 (DD: OPFILE1) — 100-byte root records (PAUTHSUM segments); one per card
   b. OUTFIL2 (DD: OPFILE2) — 206-byte child records (PAUTHDTL segments); multiple per card
3. Transfer OUTFIL1 and OUTFIL2 to S3 via SFTP/MFT gateway:
   a. s3://carddemo-landing/ims/pauthsum/full/YYYYMMDD/pauthsum.bin
   b. s3://carddemo-landing/ims/pauthdtl/full/YYYYMMDD/pauthdtl.bin
4. Databricks ingestion job parses both files and loads Bronze tables
```

**Alternative (Future):** IMS Connect with an IMS CDC adapter (e.g., IBM IMS Change Data Capture) can provide near-real-time streaming. This is deferred to Phase 2. Initial migration uses daily batch unload.

### 4.3 PAUTHSUM — Auth Summary Root Segment Parsing

#### OUTFIL1 (OPFILE1) — 100-byte Root Record

This is the layout as written by PAUDBUNL OUTFIL1 (WS-ROOT-REC):

| Byte Range | Field Name (COBOL) | PIC | Bronze Column | Spark Type |
|-----------|-------------------|-----|---------------|------------|
| 1–11 | ROOT-ACCT-ID (PA-ACCT-ID) | 9(11) | `pa_acct_id_raw` | `StringType()` → `LongType()` in Silver |
| 12–27 | PA-CARD-NUM | X(16) | `pa_card_num` | `StringType()` |
| 28–32 | PA-APPROVED-AUTH-CNT | S9(5) COMP-3 | `pa_approved_auth_cnt_raw` | Unpack COMP-3 → `IntegerType()` |
| 33–44 | PA-APPROVED-AUTH-AMT | S9(9)V99 COMP-3 | `pa_approved_auth_amt_raw` | Unpack COMP-3 → `DecimalType(11,2)` |
| 45–100 | Remaining auth fields | Various | Various raw columns | Per full PAUTHSUM DBD definition |

**Note:** The full PAUTHSUM segment layout (100 bytes) is not completely enumerated in the available PAUDBUNL specification. The field list above covers the fields referenced in CBPAUP0C and PAUDBUNL. A full segment layout must be obtained from the IMS DBD source during migration.

#### Bronze Table Load

```
Target:       carddemo.bronze.auth_summary_raw
Write Mode:   Overwrite (full daily reload; small dataset expected)
Partition:    load_date (daily)
Key Column:   pa_card_num (maps to PAUTSUM0 key field ACCNTID)
```

### 4.4 PAUTHDTL — Auth Detail Child Segment Parsing

#### OUTFIL2 (OPFILE2) — 206-byte Child Record

This is the layout as written by PAUDBUNL OUTFIL2 (WS-CHILD-REC):

| Byte Range | Field Name (COBOL) | PIC | Bronze Column | Spark Type |
|-----------|-------------------|-----|---------------|------------|
| 1–6 | ROOT-SEG-KEY | S9(11) COMP-3 | `root_seg_key_raw` | Unpack COMP-3 → `LongType()` (parent card/acct key) |
| 7–206 | PAUTDTL1 (child data) | X(200) | `pautdtl1_raw` | `BinaryType()` in Bronze; parsed in Silver |

**Child Segment Detail (PAUTDTL1, 200 bytes):** The internal structure of the 200-byte PAUTDTL1 segment is defined by the IMS DBD and was not fully enumerated in the available specification. Individual fields (authorization date, amount, type, inverted timestamp key) must be mapped from the DBD source. Bronze stores the full 200 bytes as binary; Silver pipeline parses individual fields.

#### Bronze Table Load

```
Target:       carddemo.bronze.auth_detail_raw
Write Mode:   Overwrite (full daily reload)
Partition:    load_date (daily)
Relationship: root_seg_key_raw → carddemo.bronze.auth_summary_raw.pa_acct_id_raw
```

### 4.5 DBUNLDGS — GSAM Unload Output

DBUNLDGS writes to GSAM (Generalized Sequential Access Method — IMS sequential output), not to a traditional QSAM file. GSAM is IMS-specific and has no cloud equivalent. On the mainframe, DBUNLDGS writes to two GSAM datasets (PASFLPCB root, PADFLPCB child) using CBLTDLI ISRT calls.

**Migration Decision:** GSAM output is replaced with direct Delta table writes in the migrated pipeline. There is no physical file to ingest. The DBUNLDGS pipeline (carddemo pipeline: `dbunldgs_gsam_unload`) reads from `carddemo.silver.auth_summary` and `carddemo.silver.auth_detail` and writes to `carddemo.gold.auth_gsam_export`. No separate ingestion step is required for GSAM.

---

## 5. Sequential and Flat File Parsing

Sequential and flat files are produced by JCL steps and consumed by batch programs. In the migrated architecture, these files are replaced by intermediate Delta tables. However, for the initial migration, physical files from the mainframe may be transferred to S3 as input to specific ingestion pipelines.

### 5.1 File Inventory

| File (JCL DD Name) | Format | Length | Produced By | Consumed By | Replacement Strategy |
|-------------------|--------|--------|-------------|-------------|---------------------|
| DALYTRAN | Sequential fixed | 350 bytes | Upstream JCL | CBTRN01C, CBTRN02C | Delta table: `carddemo.bronze.daily_transactions` |
| TCATBALF | Sequential fixed | ~200 bytes | CBTRN02C | CBACT04C | Delta table: `carddemo.bronze.tran_cat_balance_raw` |
| DISCGRP | Sequential fixed | ~200 bytes | Reference file | CBACT04C | Delta table: `carddemo.bronze.disclosure_group_raw` |
| DATEPARM | Sequential fixed | 22 bytes | JCL SYSIN | CBTRN03C | Databricks job parameter; not a Delta table |
| EXPFILE | VSAM KSDS | 500 bytes | CBEXPORT | External consumer | Delta table: `carddemo.bronze.export_raw` |
| Import input file | Sequential fixed | 500 bytes | External producer | CBIMPORT | Delta table: `carddemo.bronze.import_raw` |
| TRNTYPE input | Sequential fixed | 53 bytes | External | COBTUPDT | Delta table: `carddemo.bronze.tran_type_input` |
| STMTFILE | Sequential fixed | 80 bytes | CBSTM03A | CBSTM03B | Eliminated — replaced by CBSTM03B reading Silver directly |
| HTMLFILE | Sequential fixed | 100 bytes | CBSTM03A | Downstream | Delta table: `carddemo.gold.account_statement` |

### 5.2 DALYTRAN — Daily Transaction Input File

#### File Layout

```
Record Length:  350 bytes (fixed)
Format:         Same as CVTRA05Y transaction record (see TRANSACT parsing above)
Encoding:       EBCDIC IBM-037
Key:            TRAN-ID (bytes 1–16)
Sort:           No sort requirement (processed sequentially by CBTRN01C)
```

#### Ingestion Specification

```
Source (mainframe):  DD:DALYTRAN in POSTTRAN.jcl
Transfer:            FTP/MFT to s3://carddemo-landing/flatfiles/dalytran/YYYYMMDD/dalytran.bin
Parsing:             Identical to TRANSACT VSAM parsing (CVTRA05Y layout)
Target:              carddemo.bronze.daily_transactions
Write Mode:          Overwrite partition (load_date); new file each batch cycle
```

### 5.3 TCATBALF — Transaction Category Balance File

#### File Layout

```
Record Length:  Approximately 200 bytes (exact layout from CBACT04C spec)
Key:            TRANCAT-ACCT-ID (account ID) + TRANCAT-TYPE-CD + TRANCAT-CD
Sort:           ASCENDING by TRANCAT-ACCT-ID (required by CBACT04C driving file logic)
```

The exact byte layout of TCATBALF is derived from the CVTRA01Y copybook referenced in CBACT04C.

| Byte Range | Field | PIC | Bronze Column | Spark Type |
|-----------|-------|-----|---------------|------------|
| 1–11 | TRANCAT-ACCT-ID | 9(11) | `trancat_acct_id_raw` | `StringType()` → `LongType()` |
| 12–13 | TRANCAT-TYPE-CD | X(2) | `trancat_type_cd` | `StringType()` |
| 14–17 | TRANCAT-CD | 9(4) | `trancat_cd_raw` | `StringType()` → `IntegerType()` |
| 18–28 | TRAN-CAT-BAL | S9(9)V99 COMP-3 | `tran_cat_bal_raw` | Unpack COMP-3 → `DecimalType(11,2)` |

**Sort Requirement:** The TCATBALF file must be sorted by TRANCAT-ACCT-ID (ascending) before CBACT04C processes it. In the migrated pipeline, `carddemo.bronze.tran_cat_balance_raw` must be read with an `orderBy("trancat_acct_id")` clause in the CBACT04C pipeline.

#### Ingestion Specification

```
Target:       carddemo.bronze.tran_cat_balance_raw
Write Mode:   Overwrite partition (load_date)
Note:         Populated by CBTRN02C pipeline output, not by external ingestion
```

### 5.4 DISCGRP — Disclosure Group Interest Rate File

#### File Layout

The DISCGRP file contains interest rate records keyed by GROUP-ID. Layout from CVTRA02Y copybook:

| Field | PIC | Bronze Column | Spark Type |
|-------|-----|---------------|------------|
| DIS-ACCT-GROUP-ID | X(10) | `dis_acct_group_id` | `StringType()` |
| DIS-INT-RATE | S9(3)V9(6) COMP-3 | `dis_int_rate_raw` | Unpack COMP-3 → `DecimalType(9,6)` |
| DIS-GRACE-DAYS | 9(3) | `dis_grace_days_raw` | `IntegerType()` |
| 'DEFAULT' entry | — | — | Must be present; used as fallback by CBACT04C |

#### Ingestion Specification

```
Source:       DISCGRP dataset on mainframe (reference file; rarely changes)
Transfer:     FTP/MFT to s3://carddemo-landing/flatfiles/discgrp/YYYYMMDD/discgrp.bin
Target:       carddemo.bronze.disclosure_group_raw
Write Mode:   Overwrite (full reload; reference data)
Frequency:    Monthly or on-demand (changes only when rates are updated)
```

### 5.5 COBTUPDT Input — Transaction Type Maintenance File

#### File Layout

```
Record Length:  53 bytes (fixed)
Encoding:       ASCII (generated by external system, not mainframe EBCDIC)
```

| Byte Range | Field | Value Spec | Bronze Column | Spark Type |
|-----------|-------|-----------|---------------|------------|
| 1 | TRNTYPE-ACTION-CODE | 'A' (Add), 'U' (Update), 'D' (Delete), '*' (other) | `action_code` | `StringType()` |
| 2–3 | TR-TYPE-CODE | 2-char type code | `tr_type_code` | `StringType()` |
| 4–53 | TR-TYPE-DESCRIPTION | 50-char description | `tr_type_desc` | `StringType()` — trim |

#### Ingestion Specification

```
Source:       External input file; transferred to S3 by file exchange process
Transfer:     s3://carddemo-landing/flatfiles/trntype_input/YYYYMMDD/trntype_maint.txt
Target:       carddemo.bronze.tran_type_input
Write Mode:   Overwrite (each maintenance batch replaces prior input)
```

### 5.6 CBEXPORT / CBIMPORT — Data Exchange File (CVEXPORT Copybook)

#### File Layout

```
Record Length:  500 bytes (fixed)
Key:            EXPORT-SEQUENCE-NUM (bytes 1–9), PIC 9(9)
Encoding:       EBCDIC IBM-037
Entity types:   'C' (Customer), 'A' (Account), 'X' (Cross-reference), 'T' (Transaction), 'D' (Discount group)
```

| Byte Range | Field | PIC | Bronze Column | Spark Type |
|-----------|-------|-----|---------------|------------|
| 1–9 | EXPORT-SEQUENCE-NUM | 9(9) | `export_seq_num_raw` | `StringType()` → `LongType()` |
| 10 | EXPORT-ENTITY-TYPE | X(1) | `export_entity_type` | `StringType()` — 'C','A','X','T','D' |
| 11–14 | EXPORT-BRANCH-ID | X(4) | `export_branch_id` | `StringType()` — hardcoded '0001' |
| 15–19 | EXPORT-REGION-CODE | X(5) | `export_region_code` | `StringType()` — hardcoded 'NORTH' |
| 20–519 | EXPORT-DATA | X(500) | `export_data_raw` | `StringType()` — content varies by entity type |

**REDEFINES handling:** The EXPORT-DATA field is redefined per entity type. Bronze stores the raw 500-byte string. Silver pipeline splits into entity-specific tables using `export_entity_type` as a filter and re-parses `export_data_raw` per entity layout.

#### Ingestion Specification

```
For CBEXPORT output (exported from CardDemo to external):
  Source:   EXPFILE VSAM on mainframe (keyed KSDS, 500 bytes)
  Transfer: FTP/MFT to s3://carddemo-landing/flatfiles/expfile/YYYYMMDD/expfile.bin
  Target:   carddemo.bronze.export_raw
  Write:    Overwrite partition (load_date)

For CBIMPORT input (imported into CardDemo from external):
  Source:   External partner file; delivered to s3://carddemo-landing/flatfiles/import/YYYYMMDD/
  Target:   carddemo.bronze.import_raw
  Write:    Overwrite partition (load_date)
```

---

## 6. Initial Full Load Strategy

### 6.1 Load Sequence

The initial full load must follow entity dependency order to avoid referential integrity issues during Silver pipeline execution:

```
Phase 1 — Reference data (no dependencies):
  1a. DB2 TRNTYPE     → carddemo.reference.tran_type
  1b. DB2 TRNTYCAT    → carddemo.reference.tran_category
  1c. DISCGRP file    → carddemo.bronze.disclosure_group_raw → carddemo.silver.disclosure_group

Phase 2 — Master entities (depend on reference data):
  2a. CUSTDAT VSAM    → carddemo.bronze.cust_raw → carddemo.silver.customer
  2b. ACCTDAT VSAM    → carddemo.bronze.acct_raw → carddemo.silver.account
  2c. CARDDAT VSAM    → carddemo.bronze.card_raw → carddemo.silver.card
  2d. CCXREF VSAM     → carddemo.bronze.xref_raw → carddemo.silver.card_xref

Phase 3 — Transactional data (depends on master entities):
  3a. TRANSACT VSAM   → carddemo.bronze.transact_raw → carddemo.silver.transaction
  3b. DB2 AUTHFRDS    → carddemo.bronze.auth_fraud_raw → carddemo.silver.auth_fraud

Phase 4 — IMS hierarchical data:
  4a. PAUTHSUM via PAUDBUNL → carddemo.bronze.auth_summary_raw → carddemo.silver.auth_summary
  4b. PAUTHDTL via PAUDBUNL → carddemo.bronze.auth_detail_raw → carddemo.silver.auth_detail

Phase 5 — Security data (restricted access):
  5a. USRSEC VSAM     → carddemo.bronze.usrsec_raw (restricted schema; not promoted to Silver in automated pipeline)
```

### 6.2 Validation Gates Between Phases

Before promoting from Bronze to Silver and advancing to the next phase, each phase must pass record count validation:

| Gate | Check | Threshold |
|------|-------|-----------|
| Phase 1 complete | Reference tables non-empty | TRNTYPE count > 0 |
| Phase 2 complete | Customer/Account/Card counts match mainframe report | Within 0.1% of expected |
| Phase 3 complete | Transaction count matches CBTRN01C output record count | Exact match |
| Phase 4 complete | Auth summary count matches PAUDBUNL OUTFIL1 record count | Exact match |

### 6.3 Initial Load Execution Window

```
Recommended window:    Weekend maintenance window (minimum 8-hour window)
Preferred sequence:
  Saturday 18:00 — Close CICS files (CLOSEFIL.jcl)
  Saturday 18:30 — Begin VSAM exports via AWS Mainframe Modernization
  Saturday 19:00 — Begin FTP/MFT transfers to S3
  Saturday 20:00 — Begin Databricks Bronze ingestion (parallelized)
  Saturday 22:00 — Begin Databricks Silver promotion
  Sunday   02:00 — Begin reconciliation validation
  Sunday   06:00 — Final sign-off; reopen CICS files (OPENFIL.jcl)
```

### 6.4 Rollback Plan

If any phase fails validation:
1. Do not promote to Silver; leave Bronze tables in place for investigation.
2. Re-run extraction for the failed entity from the mainframe (VSAM/DB2/IMS unchanged during window).
3. Truncate and reload the failed Bronze partition.
4. Re-execute Silver promotion.
5. If systemic failure: revert by dropping all `carddemo.*` tables; mainframe continues as authoritative system.

---

## 7. Incremental and Delta Load Strategy

### 7.1 Strategy Per Source

| Source | Incremental Strategy | Frequency | Latency Requirement |
|--------|---------------------|-----------|---------------------|
| ACCTDAT VSAM | AWS DMS CDC | Continuous; applied post-batch | < 1 hour lag from mainframe write |
| CARDDAT VSAM | AWS DMS CDC | Continuous; applied post-batch | < 1 hour lag |
| CCXREF VSAM | AWS DMS CDC | Continuous; applied post-batch | < 1 hour lag |
| CUSTDAT VSAM | AWS DMS CDC | Continuous; applied post-batch | < 1 hour lag |
| TRANSACT VSAM | AWS DMS CDC | Continuous; highest priority | < 30 minutes lag |
| USRSEC VSAM | Daily full reload | Daily during batch window | Batch-aligned |
| DB2 TRNTYPE | Daily full reload | Daily | Batch-aligned |
| DB2 TRNTYCAT | Daily full reload | Daily | Batch-aligned |
| DB2 AUTHFRDS | AWS DMS CDC | Continuous | < 1 hour lag |
| IMS PAUTHSUM | Daily batch unload (PAUDBUNL) | Daily | Batch-aligned |
| IMS PAUTHDTL | Daily batch unload (PAUDBUNL) | Daily | Batch-aligned |
| Sequential flat files | Per-job transfer | After each producing JCL step | < 15 minutes post-job |

### 7.2 CDC Application Pattern — VSAM Sources

CDC events from AWS DMS arrive in S3 in DMS format. The Databricks incremental load job applies them using the following merge pattern:

```
For each CDC event in the landing zone:
  IF op_type = 'I' (Insert):
    MERGE INTO bronze_table
    USING cdc_batch ON (primary_key_match)
    WHEN NOT MATCHED THEN INSERT all columns
    WHEN MATCHED THEN UPDATE all columns  -- Handle late-arriving duplicate inserts
  IF op_type = 'U' (Update):
    MERGE INTO bronze_table
    USING cdc_batch ON (primary_key_match)
    WHEN MATCHED THEN UPDATE all columns
    WHEN NOT MATCHED THEN INSERT  -- Handle out-of-order events
  IF op_type = 'D' (Delete):
    MERGE INTO bronze_table
    USING cdc_batch ON (primary_key_match)
    WHEN MATCHED THEN UPDATE _op_type = 'D', _cdc_ts = event_ts
    -- Soft delete only in Bronze; hard delete in Silver after validation
```

### 7.3 Silver Incremental Promotion

Silver tables are updated by each batch pipeline run, not by a separate incremental load job. The pipeline reads from Bronze (filtering by `load_date >= last_successful_run_date`) and merges into Silver. This ensures Silver always reflects the most recent Bronze state including CDC-applied updates.

### 7.4 Watermark Management

The `carddemo.migration_ctrl.pipeline_metrics` table serves as the watermark store:

| Column | Purpose |
|--------|---------|
| `last_bronze_load_ts` | Latest `_ingest_ts` successfully loaded into Bronze per source |
| `last_silver_run_ts` | Latest Silver pipeline completion timestamp per entity |
| `last_cdc_file_processed` | S3 path of last CDC file applied; prevents re-processing |

---

## 8. Data Validation and Reconciliation

### 8.1 Record Count Reconciliation

After every load (full or incremental), the following counts must be compared between source and target:

| Source | Mainframe Count Source | Delta Count Query | Tolerance |
|--------|----------------------|-------------------|-----------|
| ACCTDAT | CBACT01C total records output | `SELECT COUNT(*) FROM carddemo.silver.account` | 0% (exact) |
| CARDDAT | CBACT02C total records output | `SELECT COUNT(*) FROM carddemo.silver.card` | 0% |
| CCXREF | CBACT03C total records output | `SELECT COUNT(*) FROM carddemo.silver.card_xref` | 0% |
| CUSTDAT | CBCUS01C total records output | `SELECT COUNT(*) FROM carddemo.silver.customer` | 0% |
| TRANSACT | CBTRN01C total processed | `SELECT COUNT(*) FROM carddemo.silver.transaction` | 0% |
| DB2 TRNTYPE | `SELECT COUNT(*) FROM CARDDEMO.TRNTYPE` on DB2 | `SELECT COUNT(*) FROM carddemo.reference.tran_type` | 0% |
| IMS PAUTHSUM | PAUDBUNL OUTFIL1 record count | `SELECT COUNT(*) FROM carddemo.silver.auth_summary` | 0% |
| IMS PAUTHDTL | PAUDBUNL OUTFIL2 record count | `SELECT COUNT(*) FROM carddemo.silver.auth_detail` | 0% |

Record count discrepancies of any magnitude must halt Silver promotion and trigger an alert.

### 8.2 Financial Control Totals

For financial fields, sum-level reconciliation must be performed:

| Field | Source Control Total | Delta Query | Tolerance |
|-------|---------------------|-------------|-----------|
| ACCT-CURR-BAL | Sum from CBACT01C report | `SELECT SUM(acct_curr_bal) FROM carddemo.silver.account` | 0.00 (exact decimal) |
| ACCT-CREDIT-LIMIT | Sum from CBACT01C report | `SELECT SUM(acct_credit_limit) FROM carddemo.silver.account` | 0.00 |
| TRAN-AMT | Sum from CBTRN02C report | `SELECT SUM(tran_amt) FROM carddemo.silver.transaction` | 0.00 |
| TRAN-CAT-BAL | Sum from CBACT04C input | `SELECT SUM(tran_cat_bal) FROM carddemo.silver.tran_cat_balance` | 0.00 |

**Decimal Precision Requirement:** All financial reconciliation must use `DECIMAL` arithmetic. Floating-point sums are not permitted for reconciliation.

### 8.3 Key Integrity Checks

After Silver promotion, the following referential integrity checks must pass:

```sql
-- 1. Every CARD must have a valid ACCOUNT
SELECT COUNT(*) FROM carddemo.silver.card c
LEFT JOIN carddemo.silver.account a ON c.card_acct_id = a.acct_id
WHERE a.acct_id IS NULL;
-- Expected: 0

-- 2. Every XREF card must have a card record
SELECT COUNT(*) FROM carddemo.silver.card_xref x
LEFT JOIN carddemo.silver.card c ON x.card_num = c.card_num
WHERE c.card_num IS NULL;
-- Expected: 0

-- 3. Every TRANSACTION must have a valid card in XREF
SELECT COUNT(*) FROM carddemo.silver.transaction t
LEFT JOIN carddemo.silver.card_xref x ON t.tran_card_num = x.card_num
WHERE x.card_num IS NULL;
-- Expected: 0 (or flagged/quarantined — matches CBTRN01C behavior)

-- 4. Every TRANSACTION type code must exist in reference
SELECT COUNT(*) FROM carddemo.silver.transaction t
LEFT JOIN carddemo.reference.tran_type r ON t.tran_type_cd = r.tr_type
WHERE r.tr_type IS NULL;
-- Expected: 0 after COBTUPDT pipeline ensures reference data loaded

-- 5. Auth detail records must have parent summary
SELECT COUNT(*) FROM carddemo.silver.auth_detail d
LEFT JOIN carddemo.silver.auth_summary s ON d.root_seg_key = s.pa_acct_id
WHERE s.pa_acct_id IS NULL;
-- Expected: 0
```

Failed integrity checks write detailed violation records to `carddemo.migration_ctrl.error_log`.

### 8.4 Data Quality Rules Applied During Bronze Ingestion

| Rule | Check | Action on Failure |
|------|-------|------------------|
| Non-null primary key | Key field must not be null or all-spaces | Quarantine to `error_log`; exclude from Silver |
| Numeric fields parseable | Zoned/packed decimal fields must be valid digits | Set to NULL with error flag; alert |
| Date fields valid | YYYY-MM-DD dates must be valid calendar dates | Set to NULL with error flag; log |
| Record length exact | Each record slice must equal expected byte count | Alert; halt ingestion job |
| EBCDIC decode clean | No substitution characters in decoded strings | Log warnings; continue |

### 8.5 COMP-3 Packed Decimal Validation

Packed decimal is the most common source of ingestion errors. Each packed decimal field must be validated:

```
Validation rules for COMP-3 parsing:
1. Each byte (except the last) must have both nibbles in range 0x0–0x9
2. The last byte: high nibble is the last digit (0x0–0x9); low nibble is sign (0xC=positive, 0xD=negative, 0xF=unsigned)
3. Total digit count must match PIC clause precision
4. If any nibble is out of range: field is corrupt; quarantine record

Example: PIC S9(10)V99 COMP-3 → 6 bytes
  Bytes: 0x01 0x23 0x45 0x67 0x89 0x0C
  Digits: 0,1,2,3,4,5,6,7,8,9,0
  Sign:   C (positive)
  Value:  +01234567890 → with V99 → +012345678.90
```

---

## 9. SLA and Scheduling Requirements

### 9.1 Daily Batch SLA

| Ingestion Stage | Start Time | Completion SLA | Dependency |
|----------------|-----------|----------------|------------|
| CLOSEFIL.jcl executes (CICS files closed) | 02:00 local | 02:15 | None |
| VSAM exports begin (ACCTDAT, CARDDAT, CCXREF, CUSTDAT) | 02:15 | 03:00 | CICS closed |
| TRANSACT VSAM export | 02:15 | 03:15 | CICS closed |
| FTP/MFT transfer to S3 | 03:00 | 03:45 | Exports complete |
| Bronze ingestion — master entities | 03:45 | 04:30 | S3 transfer complete |
| Bronze ingestion — transactions | 03:45 | 05:00 | S3 transfer complete |
| Bronze ingestion — IMS (if daily full reload) | 03:45 | 04:30 | PAUDBUNL JCL complete |
| Silver promotion — all entities | 05:00 | 06:00 | Bronze ingestion complete |
| Batch pipeline execution (CBACT04C, CBTRN02C, etc.) | 06:00 | 08:00 | Silver promotion complete |
| OPENFIL.jcl executes (CICS files reopened) | 08:00 | 08:15 | Batch pipelines complete |
| Reconciliation report available | 08:30 | 08:30 | All pipelines complete |

**Total batch window:** 02:00–08:30 (6.5 hours). Any SLA breach triggers an alert to the on-call engineer with automatic escalation if not acknowledged within 15 minutes.

### 9.2 Monthly Batch Additional SLA

| Stage | Timing | Completion SLA |
|-------|--------|----------------|
| Statement generation (CBSTM03A/B) | 1st of month after daily batch | 10:00 |
| Transaction report (CBTRN03C) | 1st of month | 10:00 |
| Report delivery | 1st of month | 11:00 |

### 9.3 On-Demand Ingestion (Data Exchange)

| Trigger | Response SLA |
|---------|-------------|
| CBEXPORT run request | S3 file available within 30 minutes of pipeline completion |
| CBIMPORT file arrival | Bronze ingestion begins within 10 minutes of S3 landing; Silver within 30 minutes |
| COBTUPDT input file arrival | Maintenance pipeline starts within 5 minutes of S3 landing |

### 9.4 CDC Latency Targets

| Source | CDC Start Latency (from mainframe write) | Apply Latency (from S3 landing) |
|--------|------------------------------------------|--------------------------------|
| TRANSACT VSAM | < 5 minutes | < 10 minutes |
| ACCTDAT VSAM | < 10 minutes | < 15 minutes |
| CARDDAT VSAM | < 10 minutes | < 15 minutes |
| CUSTDAT VSAM | < 10 minutes | < 15 minutes |
| DB2 AUTHFRDS | < 5 minutes | < 10 minutes |

---

## 10. Landing Zone Specifications

### 10.1 S3 Bucket Structure

```
s3://carddemo-landing/
├── vsam/
│   ├── acctdat/
│   │   ├── full/
│   │   │   └── YYYYMMDD/
│   │   │       └── acctdat_full.bin          # Fixed-width binary, EBCDIC
│   │   └── cdc/
│   │       └── YYYYMMDD/
│   │           └── HH/
│   │               └── acctdat_cdc_{n}.parquet  # DMS CDC format
│   ├── carddat/
│   │   ├── full/ ...
│   │   └── cdc/ ...
│   ├── ccxref/
│   │   ├── full/ ...
│   │   └── cdc/ ...
│   ├── custdat/
│   │   ├── full/ ...
│   │   └── cdc/ ...
│   ├── transact/
│   │   ├── full/ ...
│   │   └── cdc/ ...
│   └── usrsec/
│       └── full/ ...                          # No CDC; daily full reload only
├── db2/
│   ├── trntype/
│   │   └── full/ ...                          # CSV with header
│   ├── trntycat/
│   │   └── full/ ...
│   └── authfrds/
│       ├── full/ ...
│       └── cdc/ ...
├── ims/
│   ├── pauthsum/
│   │   └── full/
│   │       └── YYYYMMDD/
│   │           └── pauthsum.bin               # PAUDBUNL OUTFIL1 output
│   └── pauthdtl/
│       └── full/
│           └── YYYYMMDD/
│               └── pauthdtl.bin               # PAUDBUNL OUTFIL2 output
└── flatfiles/
    ├── dalytran/
    │   └── YYYYMMDD/
    │       └── dalytran.bin                   # Daily transaction input
    ├── discgrp/
    │   └── YYYYMMDD/
    │       └── discgrp.bin                    # Disclosure group reference
    ├── trntype_input/
    │   └── YYYYMMDD/
    │       └── trntype_maint.txt              # COBTUPDT input
    ├── expfile/
    │   └── YYYYMMDD/
    │       └── expfile.bin                    # CBEXPORT output
    └── import/
        └── YYYYMMDD/
            └── import_input.bin               # CBIMPORT input
```

### 10.2 File Naming Conventions

| Convention | Pattern | Example |
|-----------|---------|---------|
| Full load binary | `{source}_{yyyymmdd}_full.bin` | `acctdat_20260406_full.bin` |
| CDC parquet | `{source}_cdc_{yyyymmdd}_{hh}_{seq}.parquet` | `transact_cdc_20260406_03_001.parquet` |
| DB2 CSV full | `{table}_{yyyymmdd}_full.csv` | `trntype_20260406_full.csv` |
| Flat file binary | `{ddname}_{yyyymmdd}.bin` | `dalytran_20260406.bin` |

### 10.3 S3 Bucket Security

| Control | Specification |
|---------|--------------|
| Encryption | SSE-S3 for all objects; SSE-KMS for PII-containing sources (custdat, usrsec) |
| Access | IAM role-based; least privilege per source type |
| Lifecycle | Raw files retained 30 days; then archived to S3 Glacier |
| Versioning | Enabled on landing bucket (protects against accidental overwrite) |
| Logging | S3 access logging enabled; alerts on unexpected access patterns |

### 10.4 Auto Loader Configuration

Databricks Auto Loader (`cloudFiles`) monitors landing zone paths and triggers Bronze ingestion:

```
Configuration (specification — not code):
  format:            "binaryFile" for VSAM/IMS fixed-width files
                     "csv" for DB2 CSV files
                     "parquet" for CDC DMS files
  cloudFiles.source: "s3"
  inferSchema:       false — schema explicitly provided
  path:              s3://carddemo-landing/{source_type}/{source_name}/{load_type}/
  trigger:           processingTime("15 minutes") for CDC
                     availableNow() for scheduled full loads
  checkpointLocation: s3://carddemo-checkpoints/{source_name}/bronze/
```

---

## 11. Error Handling and Recovery

### 11.1 Ingestion Error Classification

| Error Class | Examples | Action |
|-------------|---------|--------|
| File not found | S3 file not present at expected path | Alert; retry 3× at 5-minute intervals; escalate if still missing |
| Parse error (COMP-3) | Invalid nibble sequence in packed decimal | Quarantine record; log to `migration_ctrl.error_log`; continue with remaining records |
| Parse error (EBCDIC) | Unmappable byte sequence | Replace with substitution character; log warning; continue |
| Record length mismatch | File contains record shorter/longer than expected | Alert; halt ingestion job; do not write partial data |
| Primary key null | Key field decodes to null or all-spaces | Quarantine record; log error; continue |
| Count mismatch | Bronze count ≠ mainframe expected count | Alert; halt Silver promotion; investigate |
| Financial control mismatch | Sum discrepancy in amount fields | Critical alert; halt all downstream pipelines |

### 11.2 Quarantine Table

All quarantined records are written to `carddemo.migration_ctrl.error_log`:

| Column | Type | Purpose |
|--------|------|---------|
| `error_id` | `StringType()` (UUID) | Unique error identifier |
| `error_ts` | `TimestampType()` | When error was detected |
| `source_system` | `StringType()` | `VSAM`, `DB2`, `IMS`, `FLATFILE` |
| `source_dataset` | `StringType()` | Source file/table name |
| `record_offset` | `LongType()` | Byte offset in source file |
| `raw_bytes` | `BinaryType()` | Original bytes of the failing record |
| `error_code` | `StringType()` | Error classification code |
| `error_message` | `StringType()` | Human-readable error description |
| `pipeline_run_id` | `StringType()` | Databricks job run ID |
| `resolved` | `BooleanType()` | True when manually resolved and reprocessed |

### 11.3 Retry and Idempotency

All ingestion jobs are designed to be idempotent:
- Full load jobs: overwrite the target partition (`load_date = YYYYMMDD`). Re-running the same day overwrites the same partition. No duplicate data.
- CDC jobs: MERGE operations are idempotent. Replaying the same CDC file re-applies the same UPSERTs.
- Auto Loader: uses checkpoints to track processed files. Files already processed are not reprocessed on job restart.

### 11.4 Manual Recovery Procedures

| Scenario | Recovery Steps |
|----------|---------------|
| VSAM export corrupted | Re-trigger AWS Mainframe Modernization export job for specific date |
| S3 transfer incomplete | Re-initiate MFT transfer for specific file; ingestion job detects file presence via checkpoint |
| Bronze ingestion failed mid-run | Drop the failed partition; re-run ingestion job (idempotent) |
| Silver promotion failed | Bronze data is intact; re-run Silver pipeline with same run_date parameter |
| CDC gap detected (missed events) | Trigger a targeted full reload for the affected entity; DMS will reconcile |
