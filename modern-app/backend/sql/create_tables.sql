-- Authorization Module Database Schema
-- Converted from COBOL CardDemo Authorization Sub-Application
-- IMS DBPAUTP0 (PAUTSUM0 + PAUTDTL1) and DB2 AUTHFRDS tables

-- Authorization Summaries
-- Maps to IMS root segment PAUTSUM0 (100 bytes)
-- Key was PA-ACCT-ID (packed decimal 6 bytes)
CREATE TABLE IF NOT EXISTS authorization_summaries (
    id                  SERIAL PRIMARY KEY,
    account_id          VARCHAR(11)     NOT NULL UNIQUE,
    customer_id         VARCHAR(9)      NOT NULL,
    auth_status         CHAR(1)         NOT NULL DEFAULT 'A'
                        CHECK (auth_status IN ('A', 'C', 'I')),
    credit_limit        NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    cash_limit          NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    credit_balance      NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    cash_balance        NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    approved_count      INTEGER         NOT NULL DEFAULT 0,
    declined_count      INTEGER         NOT NULL DEFAULT 0,
    approved_amount     NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    declined_amount     NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE authorization_summaries IS
    'Account-level authorization summary. Maps to IMS PAUTSUM0 root segment.';
COMMENT ON COLUMN authorization_summaries.auth_status IS
    'A=Active, C=Closed, I=Inactive';
COMMENT ON COLUMN authorization_summaries.approved_count IS
    'Cumulative count of approved authorizations (PA-APPROVED-AUTH-CNT)';
COMMENT ON COLUMN authorization_summaries.declined_count IS
    'Cumulative count of declined authorizations (PA-DECLINED-AUTH-CNT)';

CREATE INDEX IF NOT EXISTS idx_auth_summaries_account_id
    ON authorization_summaries(account_id);
CREATE INDEX IF NOT EXISTS idx_auth_summaries_customer_id
    ON authorization_summaries(customer_id);


-- Authorization Details
-- Maps to IMS child segment PAUTDTL1 (200 bytes)
-- Key was PA-AUTH-DATE-9C + PA-AUTH-TIME-9C (9-complement COMP-3 timestamp)
CREATE TABLE IF NOT EXISTS authorization_details (
    id                      SERIAL PRIMARY KEY,
    summary_id              INTEGER         NOT NULL
                            REFERENCES authorization_summaries(id) ON DELETE CASCADE,
    card_number             VARCHAR(16)     NOT NULL,
    auth_date               DATE            NOT NULL,
    auth_time               TIME            NOT NULL,
    auth_type               VARCHAR(4)      NOT NULL DEFAULT '',
    card_expiry             VARCHAR(5)      NOT NULL DEFAULT '',
    message_type            VARCHAR(6)      NOT NULL DEFAULT '',
    auth_response_code      CHAR(2)         NOT NULL DEFAULT '00',
    auth_response_reason    VARCHAR(20)     NOT NULL DEFAULT '',
    auth_code               VARCHAR(6)      NOT NULL DEFAULT '',
    transaction_amount      NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    approved_amount         NUMERIC(12, 2)  NOT NULL DEFAULT 0.00,
    pos_entry_mode          VARCHAR(4)      NOT NULL DEFAULT '',
    auth_source             VARCHAR(10)     NOT NULL DEFAULT '',
    mcc_code                VARCHAR(4)      NOT NULL DEFAULT '',
    merchant_name           VARCHAR(25)     NOT NULL DEFAULT '',
    merchant_id             VARCHAR(15)     NOT NULL DEFAULT '',
    merchant_city           VARCHAR(25)     NOT NULL DEFAULT '',
    merchant_state          CHAR(2)         NOT NULL DEFAULT '',
    merchant_zip            VARCHAR(10)     NOT NULL DEFAULT '',
    transaction_id          VARCHAR(15)     NOT NULL DEFAULT '',
    match_status            CHAR(1)         NOT NULL DEFAULT 'P'
                            CHECK (match_status IN ('P', 'D', 'E', 'M')),
    fraud_status            CHAR(1)         CHECK (fraud_status IN ('F', 'R', NULL)),
    fraud_report_date       DATE,
    processing_code         VARCHAR(6)      NOT NULL DEFAULT '',
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE authorization_details IS
    'Individual authorization records. Maps to IMS PAUTDTL1 child segment.';
COMMENT ON COLUMN authorization_details.auth_response_code IS
    '0000=Approved, 3100=Invalid Card, 4100=Insufficient Fund, 4200=Card Not Active, 4300=Account Closed, 4400=Exceed Daily Limit, 5100=Card Fraud, 5200=Merchant Fraud, 5300=Lost Card, 9000=Unknown';
COMMENT ON COLUMN authorization_details.match_status IS
    'P=Pending, D=Declined, E=Expired, M=Matched';
COMMENT ON COLUMN authorization_details.fraud_status IS
    'F=Fraud confirmed, R=Fraud removed (removed flag), NULL=no fraud action taken';

CREATE INDEX IF NOT EXISTS idx_auth_details_summary_id
    ON authorization_details(summary_id);
CREATE INDEX IF NOT EXISTS idx_auth_details_card_number
    ON authorization_details(card_number);
CREATE INDEX IF NOT EXISTS idx_auth_details_auth_date
    ON authorization_details(auth_date);
CREATE INDEX IF NOT EXISTS idx_auth_details_transaction_id
    ON authorization_details(transaction_id);
CREATE INDEX IF NOT EXISTS idx_auth_details_match_status
    ON authorization_details(match_status);


-- Fraud Records
-- Maps to DB2 table CARDDEMO.AUTHFRDS
-- Composite unique key: card_number + auth_timestamp
CREATE TABLE IF NOT EXISTS fraud_records (
    id                  SERIAL PRIMARY KEY,
    card_number         VARCHAR(16)     NOT NULL,
    auth_timestamp      TIMESTAMP       NOT NULL,
    fraud_flag          CHAR(1)         NOT NULL
                        CHECK (fraud_flag IN ('F', 'R')),
    fraud_report_date   DATE            NOT NULL,
    match_status        CHAR(1)         NOT NULL DEFAULT 'P'
                        CHECK (match_status IN ('P', 'D', 'E', 'M')),
    account_id          VARCHAR(11)     NOT NULL,
    customer_id         VARCHAR(9)      NOT NULL,
    auth_detail_id      INTEGER
                        REFERENCES authorization_details(id) ON DELETE SET NULL,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_fraud_card_timestamp UNIQUE (card_number, auth_timestamp)
);

COMMENT ON TABLE fraud_records IS
    'Fraud flag records. Maps to DB2 CARDDEMO.AUTHFRDS table. Managed by COPAUS2C.';
COMMENT ON COLUMN fraud_records.fraud_flag IS
    'F=Fraud reported, R=Fraud removed';

CREATE INDEX IF NOT EXISTS idx_fraud_records_card_number
    ON fraud_records(card_number);
CREATE INDEX IF NOT EXISTS idx_fraud_records_account_id
    ON fraud_records(account_id);
CREATE INDEX IF NOT EXISTS idx_fraud_records_auth_detail_id
    ON fraud_records(auth_detail_id);
