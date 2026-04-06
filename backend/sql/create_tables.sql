-- =============================================================================
-- CardDemo PostgreSQL Schema — Credit Cards Module
-- Converted from COBOL VSAM KSDS datasets (CVACT01Y, CVACT02Y, CVACT03Y, CVCUS01Y, CSUSR01Y)
-- =============================================================================

-- shared trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Table: users
-- COBOL: USRSEC VSAM KSDS (CSUSR01Y copybook)
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id         VARCHAR(8)   NOT NULL,
    first_name      VARCHAR(20)  NOT NULL,
    last_name       VARCHAR(20)  NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    user_type       CHAR(1)      NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT chk_users_type CHECK (user_type IN ('A', 'U'))
);
CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name);
CREATE OR REPLACE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Table: accounts
-- COBOL: ACCTDAT VSAM KSDS (CVACT01Y copybook, 300-byte record)
-- Key: ACCT-ID PIC 9(11) → BIGINT
-- =============================================================================
CREATE TABLE IF NOT EXISTS accounts (
    account_id          BIGINT          NOT NULL,
    active_status       CHAR(1)         NOT NULL DEFAULT 'Y',
    current_balance     NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    credit_limit        NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    cash_credit_limit   NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    curr_cycle_credit   NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    curr_cycle_debit    NUMERIC(12,2)   NOT NULL DEFAULT 0.00,
    open_date           DATE,
    expiration_date     DATE,
    reissue_date        DATE,
    group_id            VARCHAR(10),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_accounts PRIMARY KEY (account_id),
    CONSTRAINT chk_accounts_status CHECK (active_status IN ('Y', 'N')),
    CONSTRAINT chk_accounts_credit_limit CHECK (credit_limit >= 0),
    CONSTRAINT chk_accounts_cash_limit CHECK (cash_credit_limit >= 0 AND cash_credit_limit <= credit_limit)
);
COMMENT ON TABLE accounts IS 'COBOL: ACCTDAT VSAM KSDS (CVACT01Y copybook, 300-byte record). Key: ACCT-ID PIC 9(11).';
CREATE OR REPLACE TRIGGER trg_accounts_updated_at
    BEFORE UPDATE ON accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Table: customers
-- COBOL: CUSTDAT VSAM KSDS (CVCUS01Y copybook, 500-byte record)
-- Key: CUST-ID PIC 9(09) → INTEGER
-- =============================================================================
CREATE TABLE IF NOT EXISTS customers (
    customer_id             INTEGER         NOT NULL,
    first_name              VARCHAR(25)     NOT NULL,
    middle_name             VARCHAR(25),
    last_name               VARCHAR(25)     NOT NULL,
    address_line_1          VARCHAR(50),
    address_line_2          VARCHAR(50),
    address_line_3          VARCHAR(50),
    state_code              CHAR(2),
    country_code            CHAR(3),
    zip_code                VARCHAR(10),
    phone_1                 VARCHAR(15),
    phone_2                 VARCHAR(15),
    ssn                     VARCHAR(11),    -- NNN-NN-NNNN; NEVER returned plain
    government_id_ref       VARCHAR(20),
    date_of_birth           DATE,
    eft_account_id          VARCHAR(10),
    primary_card_holder     CHAR(1)         NOT NULL DEFAULT 'Y',
    fico_score              SMALLINT,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_customers PRIMARY KEY (customer_id),
    CONSTRAINT chk_customers_primary CHECK (primary_card_holder IN ('Y', 'N')),
    CONSTRAINT chk_customers_fico CHECK (fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850))
);
COMMENT ON TABLE customers IS 'COBOL: CUSTDAT VSAM KSDS (CVCUS01Y copybook, 500-byte record). Key: CUST-ID PIC 9(09). SSN masked in all API responses.';
CREATE INDEX IF NOT EXISTS idx_customers_last_name ON customers(last_name);
CREATE OR REPLACE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Table: account_customer_xref
-- Links accounts to customers (replaces CARDAIX AIX browse in COACTVWC)
-- =============================================================================
CREATE TABLE IF NOT EXISTS account_customer_xref (
    account_id      BIGINT      NOT NULL REFERENCES accounts(account_id),
    customer_id     INTEGER     NOT NULL REFERENCES customers(customer_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_account_customer_xref PRIMARY KEY (account_id, customer_id)
);
CREATE INDEX IF NOT EXISTS idx_acctcust_customer ON account_customer_xref(customer_id);

-- =============================================================================
-- Table: credit_cards
-- COBOL: CARDDAT VSAM KSDS (CVACT02Y copybook, 150-byte record)
-- Key: CARD-NUM PIC X(16) → CHAR(16)
-- =============================================================================
CREATE TABLE IF NOT EXISTS credit_cards (
    card_number         CHAR(16)    NOT NULL,
    account_id          BIGINT      NOT NULL REFERENCES accounts(account_id),
    customer_id         INTEGER     NOT NULL REFERENCES customers(customer_id),
    card_embossed_name  VARCHAR(50),
    expiration_date     DATE,
    expiration_day      INTEGER,    -- EXPDAY DRK PROT FSET hidden field from COCRDUPC
    active_status       CHAR(1)     NOT NULL DEFAULT 'Y',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- optimistic lock (replaces CCUP-OLD-DETAILS)
    CONSTRAINT pk_credit_cards PRIMARY KEY (card_number),
    CONSTRAINT chk_cards_status CHECK (active_status IN ('Y', 'N'))
);
COMMENT ON TABLE credit_cards IS 'COBOL: CARDDAT VSAM KSDS (CVACT02Y copybook). CVV not stored (PCI-DSS). updated_at replaces CCUP-OLD-DETAILS snapshot.';
CREATE INDEX IF NOT EXISTS idx_cards_account ON credit_cards(account_id);
CREATE INDEX IF NOT EXISTS idx_cards_customer ON credit_cards(customer_id);
CREATE OR REPLACE TRIGGER trg_cards_updated_at
    BEFORE UPDATE ON credit_cards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Table: card_account_xref
-- COBOL: CARDXREF VSAM KSDS + CARDAIX AIX (CVACT03Y copybook, 50-byte record)
-- Key: XREF-CARD-NUM PIC X(16) → CHAR(16)
-- =============================================================================
CREATE TABLE IF NOT EXISTS card_account_xref (
    card_number     CHAR(16)    NOT NULL,
    customer_id     INTEGER     NOT NULL,
    account_id      BIGINT      NOT NULL,
    CONSTRAINT pk_card_account_xref PRIMARY KEY (card_number)
);
COMMENT ON TABLE card_account_xref IS 'COBOL: CARDXREF VSAM KSDS (CVACT03Y). idx_cardxref_account replaces CARDAIX Alternate Index on XREF-ACCT-ID.';
CREATE INDEX IF NOT EXISTS idx_cardxref_account ON card_account_xref(account_id);
CREATE INDEX IF NOT EXISTS idx_cardxref_customer ON card_account_xref(customer_id);
