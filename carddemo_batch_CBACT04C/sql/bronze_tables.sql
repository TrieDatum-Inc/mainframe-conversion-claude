-- =============================================================================
-- CBACT04C Bronze Layer DDL
-- =============================================================================
-- Catalog:  carddemo
-- Schema:   bronze
-- Source:   VSAM KSDS files TCATBALF and DISCGRP
-- Copybooks: CVTRA01Y (TCATBALF), CVTRA02Y (DISCGRP)
--
-- These tables land raw mainframe records before type coercion.
-- All business fields stored as STRING in Bronze; numeric conversion happens
-- in the Silver transformation step.
--
-- NOTE: carddemo.bronze.acct_raw, carddemo.bronze.xref_raw, and
--       carddemo.bronze.transact_raw are NOT created here — they were already
--       created by earlier pipelines (CBTRN02C). Do not re-create them.
-- =============================================================================

USE CATALOG carddemo;
USE SCHEMA bronze;

-- ---------------------------------------------------------------------------
-- 3.7 carddemo.bronze.tran_cat_balance_raw
-- Source: VSAM KSDS TCATBALF (DD: TCATBALF in INTCALC.jcl)
-- Copybook: CVTRA01Y
-- Purpose: Driving file for CBACT04C interest calculation
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS carddemo.bronze.tran_cat_balance_raw (
  -- CVTRA01Y fields
  trancat_acct_id_raw     STRING  NOT NULL
                          COMMENT 'TRANCAT-ACCT-ID PIC 9(11) — 11-digit account ID, part of composite key',
  trancat_type_cd         STRING  NOT NULL
                          COMMENT 'TRANCAT-TYPE-CD PIC X(2) — transaction type code, part of composite key',
  trancat_cd_raw          STRING  NOT NULL
                          COMMENT 'TRANCAT-CD PIC 9(4) — transaction category code, part of composite key',
  tran_cat_bal_raw        STRING  NOT NULL
                          COMMENT 'TRAN-CAT-BAL S9(9)V99 — running balance for this category/type; sign included',

  -- Ingestion metadata
  _meta_extract_date      DATE
                          COMMENT 'Date this record was extracted from mainframe',
  _meta_pipeline_run_id   STRING
                          COMMENT 'Databricks job run ID that loaded this record',
  _meta_source_system     STRING
                          COMMENT 'Always: CARDDEMO_VSAM_TCATBALF'
)
USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Raw transaction category balance records from VSAM KSDS TCATBALF (CVTRA01Y). '
        'Driving file for CBACT04C interest calculation. One row per (account, type, category) combination.';

ALTER TABLE carddemo.bronze.tran_cat_balance_raw
  SET TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.dataSkippingNumIndexedCols' = '3',
    'migrated_from' = 'VSAM_KSDS_TCATBALF',
    'cobol_copybook' = 'CVTRA01Y'
  );

-- Z-ORDER on primary lookup key (applied via OPTIMIZE command after initial load)
-- OPTIMIZE carddemo.bronze.tran_cat_balance_raw
--   ZORDER BY (trancat_acct_id_raw);


-- ---------------------------------------------------------------------------
-- 3.8 carddemo.bronze.disclosure_group_raw
-- Source: VSAM KSDS DISCGRP (DD: DISCGRP in INTCALC.jcl)
-- Copybook: CVTRA02Y
-- Purpose: Interest rate lookup table for CBACT04C
-- Note: This table is small enough to qualify for broadcast join in Silver.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS carddemo.bronze.disclosure_group_raw (
  -- CVTRA02Y fields
  dis_acct_group_id       STRING  NOT NULL
                          COMMENT 'FD-DIS-ACCT-GROUP-ID PIC X(10) — account group; DEFAULT=fallback rate',
  dis_tran_type_cd        STRING  NOT NULL
                          COMMENT 'FD-DIS-TRAN-TYPE-CD PIC X(2) — transaction type code',
  dis_tran_cat_cd_raw     STRING  NOT NULL
                          COMMENT 'FD-DIS-TRAN-CAT-CD PIC 9(4) — transaction category code',
  dis_int_rate_raw        STRING  NOT NULL
                          COMMENT 'DIS-INT-RATE — annual interest rate percentage (e.g., "18.0000" = 18%)',

  -- Ingestion metadata
  _meta_extract_date      DATE
                          COMMENT 'Date this record was extracted from mainframe',
  _meta_pipeline_run_id   STRING
                          COMMENT 'Databricks job run ID that loaded this record',
  _meta_source_system     STRING
                          COMMENT 'Always: CARDDEMO_VSAM_DISCGRP'
)
USING DELTA
PARTITIONED BY (_meta_extract_date)
COMMENT 'Bronze: Raw disclosure group interest rate records from VSAM KSDS DISCGRP (CVTRA02Y). '
        'Used by CBACT04C for interest rate lookup. Small table — qualifies for broadcast join in Silver.';

ALTER TABLE carddemo.bronze.disclosure_group_raw
  SET TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'migrated_from' = 'VSAM_KSDS_DISCGRP',
    'cobol_copybook' = 'CVTRA02Y'
  );
