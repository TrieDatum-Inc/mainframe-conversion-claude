-- =============================================================================
-- CardDemo Transaction Module - PostgreSQL Schema
-- Converted from COBOL VSAM KSDS: TRANSACT (CVTRA05Y) and TCATBALF (CVTRA01Y)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TRANSACTIONS table
-- Maps to VSAM KSDS TRANSACT with key TRAN-ID X(16)
-- CVTRA05Y: TRAN-RECORD 350 bytes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id                   SERIAL PRIMARY KEY,
    -- TRAN-ID X(16): unique transaction identifier, auto-generated (max+1)
    transaction_id       VARCHAR(16)     NOT NULL UNIQUE,
    -- TRAN-TYPE-CD CHAR(2): e.g. '01'=Purchase, '02'=Payment
    type_code            CHAR(2)         NOT NULL,
    -- TRAN-CAT-CD 9(4): category code, stored as varchar to allow leading zeros
    category_code        VARCHAR(4)      NOT NULL,
    -- TRAN-SOURCE X(10): e.g. 'POS TERM', 'ONLINE'
    source               VARCHAR(10)     NOT NULL DEFAULT '',
    -- TRAN-DESC X(100): transaction description
    description          VARCHAR(100)    NOT NULL DEFAULT '',
    -- TRAN-AMT S9(9)V99 COMP-3: signed decimal up to +/-99999999.99
    amount               NUMERIC(11, 2)  NOT NULL,
    -- TRAN-MERCHANT-ID 9(9): must be all numeric
    merchant_id          VARCHAR(9)      NOT NULL DEFAULT '',
    -- TRAN-MERCHANT-NAME X(50)
    merchant_name        VARCHAR(50)     NOT NULL DEFAULT '',
    -- TRAN-MERCHANT-CITY X(50)
    merchant_city        VARCHAR(50)     NOT NULL DEFAULT '',
    -- TRAN-MERCHANT-ZIP X(10)
    merchant_zip         VARCHAR(10)     NOT NULL DEFAULT '',
    -- TRAN-CARD-NUM X(16): card number (FK reference)
    card_number          VARCHAR(16)     NOT NULL,
    -- TRAN-ORIG-TS: original transaction timestamp (26-char in COBOL → TIMESTAMP)
    original_timestamp   TIMESTAMP       NOT NULL,
    -- TRAN-PROC-TS: processing timestamp
    processing_timestamp TIMESTAMP       NOT NULL,
    -- Audit columns
    created_at           TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_transaction_id ON transactions (transaction_id);
CREATE INDEX IF NOT EXISTS idx_transactions_card_number   ON transactions (card_number);
CREATE INDEX IF NOT EXISTS idx_transactions_orig_ts       ON transactions (original_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_type_category ON transactions (type_code, category_code);

-- ---------------------------------------------------------------------------
-- TRANSACTION_CATEGORY_BALANCES table
-- Maps to VSAM KSDS TCATBALF with composite key (ACCT-ID + TYPE-CD + CAT-CD)
-- CVTRA01Y: TRAN-CAT-BAL-RECORD 50 bytes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transaction_category_balances (
    id            SERIAL PRIMARY KEY,
    -- ACCT-ID 9(11): account identifier
    account_id    VARCHAR(11)    NOT NULL,
    -- TRAN-TYPE-CD CHAR(2)
    type_code     CHAR(2)        NOT NULL,
    -- TRAN-CAT-CD VARCHAR(4)
    category_code VARCHAR(4)     NOT NULL,
    -- TRAN-CAT-BAL S9(9)V99: running balance for this category
    balance       NUMERIC(11, 2) NOT NULL DEFAULT 0.00,
    -- Audit columns
    created_at    TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP      NOT NULL DEFAULT NOW(),
    -- Unique composite key matching VSAM KSDS key structure
    CONSTRAINT uq_tcat_bal UNIQUE (account_id, type_code, category_code)
);

CREATE INDEX IF NOT EXISTS idx_tcatbal_account ON transaction_category_balances (account_id);

-- ---------------------------------------------------------------------------
-- Trigger: auto-update updated_at on row modification
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_transactions_updated_at ON transactions;
CREATE TRIGGER trg_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_tcatbal_updated_at ON transaction_category_balances;
CREATE TRIGGER trg_tcatbal_updated_at
    BEFORE UPDATE ON transaction_category_balances
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
