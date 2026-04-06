-- =============================================================================
-- Authorization Module Tables
-- Source: IMS PAUTSUM0 (CIPAUSMY), PAUTDTL1 (CIPAUDTY), DB2 CARDDEMO.AUTHFRDS
-- Replaces: COPAUS0C, COPAUS1C, COPAUS2C programs
-- =============================================================================

-- Trigger function for automatic updated_at management
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 2.9 authorization_summary Table
-- Source: IMS PAUTSUM0 root segment (CIPAUSMY copybook)
-- Replaces: HISAM root segment under DBPAUTP0 database
-- COPAUS0C: EXEC DLI GU PAUTSUM0 WHERE(ACCNTID = WS-CARD-RID-ACCT-ID)
-- =============================================================================
CREATE TABLE IF NOT EXISTS authorization_summary (
    account_id              BIGINT          NOT NULL,
    credit_limit            NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    cash_limit              NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    credit_balance          NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    cash_balance            NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    approved_auth_count     INTEGER         NOT NULL DEFAULT 0,
    declined_auth_count     INTEGER         NOT NULL DEFAULT 0,
    approved_auth_amount    NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    declined_auth_amount    NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_auth_summary PRIMARY KEY (account_id),
    CONSTRAINT fk_authsum_account FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- =============================================================================
-- 2.10 authorization_detail Table
-- Source: IMS PAUTDTL1 child segment (CIPAUDTY copybook; 200 bytes)
-- IMS Key Note: IMS uses inverted timestamp key (999999999 - AUTH-TIME-9C)
--   for descending order. PostgreSQL uses processed_at DESC ordering instead.
-- COPAUS0C: EXEC DLI GNP PAUTDTL1 (reads up to 5 per page)
-- COPAUS1C: EXEC DLI GNP PAUTDTL1 WHERE(PAUT9CTS = PA-AUTHORIZATION-KEY)
-- COPAUS1C: EXEC DLI REPL PAUTDTL1 (fraud flag update)
-- =============================================================================
CREATE TABLE IF NOT EXISTS authorization_detail (
    auth_id                 BIGSERIAL       NOT NULL,
    account_id              BIGINT          NOT NULL,
    transaction_id          VARCHAR(16)     NOT NULL,
    card_number             CHAR(16)        NOT NULL,
    auth_date               DATE            NOT NULL,
    auth_time               TIME            NOT NULL,
    auth_response_code      CHAR(2)         NOT NULL,   -- '00'=approved, other=declined
    auth_code               VARCHAR(6),
    transaction_amount      NUMERIC(10, 2)  NOT NULL,
    pos_entry_mode          VARCHAR(4),
    auth_source             VARCHAR(10),
    mcc_code                VARCHAR(4),
    card_expiry_date        VARCHAR(5),
    auth_type               VARCHAR(14),
    match_status            CHAR(1)         NOT NULL DEFAULT 'P',   -- P/D/E/M
    fraud_status            CHAR(1)         NOT NULL DEFAULT 'N',   -- N/F/R
    merchant_name           VARCHAR(25),
    merchant_id             VARCHAR(15),
    merchant_city           VARCHAR(25),
    merchant_state          CHAR(2),
    merchant_zip            VARCHAR(10),
    processed_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_auth_detail PRIMARY KEY (auth_id),
    CONSTRAINT fk_authdet_summary FOREIGN KEY (account_id)
        REFERENCES authorization_summary(account_id),
    CONSTRAINT chk_authdet_match CHECK (match_status IN ('P', 'D', 'E', 'M')),
    CONSTRAINT chk_authdet_fraud CHECK (fraud_status IN ('N', 'F', 'R'))
);

-- Replaces IMS inverted timestamp key ordering (newest first)
CREATE INDEX IF NOT EXISTS idx_authdet_account_id ON authorization_detail(account_id);
CREATE INDEX IF NOT EXISTS idx_authdet_card_number ON authorization_detail(card_number);
CREATE INDEX IF NOT EXISTS idx_authdet_processed_at ON authorization_detail(processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_authdet_transaction_id ON authorization_detail(transaction_id);
CREATE INDEX IF NOT EXISTS idx_authdet_fraud_status ON authorization_detail(fraud_status);

-- Trigger for updated_at
CREATE TRIGGER trg_authdet_updated_at
    BEFORE UPDATE ON authorization_detail
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 2.11 auth_fraud_log Table
-- Source: DB2 CARDDEMO.AUTHFRDS table (COPAUS2C)
-- Purpose: Immutable audit log of fraud flag toggles
-- COPAUS2C: EXEC SQL INSERT INTO CARDDEMO.AUTHFRDS (26 columns)
-- COPAUS2C: EXEC SQL UPDATE on SQLCODE -803 (duplicate key)
-- =============================================================================
CREATE TABLE IF NOT EXISTS auth_fraud_log (
    log_id              BIGSERIAL       NOT NULL,
    auth_id             BIGINT          NOT NULL,
    transaction_id      VARCHAR(16)     NOT NULL,
    card_number         CHAR(16)        NOT NULL,
    account_id          BIGINT          NOT NULL,
    fraud_flag          CHAR(1)         NOT NULL,   -- 'F'=confirmed, 'R'=removed
    fraud_report_date   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    auth_response_code  CHAR(2),
    auth_amount         NUMERIC(10, 2),
    merchant_name       VARCHAR(22),
    merchant_id         VARCHAR(9),
    logged_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_fraud_log PRIMARY KEY (log_id),
    CONSTRAINT fk_fraudlog_auth FOREIGN KEY (auth_id)
        REFERENCES authorization_detail(auth_id)
);

CREATE INDEX IF NOT EXISTS idx_fraudlog_transaction ON auth_fraud_log(transaction_id);
CREATE INDEX IF NOT EXISTS idx_fraudlog_account ON auth_fraud_log(account_id);

-- Replaces SQLCODE -803 duplicate key handling from COPAUS2C
-- The unique index allows only one 'F' entry per auth at a time
CREATE UNIQUE INDEX IF NOT EXISTS idx_fraudlog_unique_auth
    ON auth_fraud_log(auth_id, fraud_flag) WHERE fraud_flag = 'F';
