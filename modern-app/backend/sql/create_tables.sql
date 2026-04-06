-- =============================================================================
-- CardDemo Account & Credit Card Module — DDL
-- Migrated from VSAM KSDS: ACCTDATA, CUSTDATA, CARDDATA, CARDXREF
-- Copybooks: CVACT01Y (Account), CVCUS01Y (Customer), CVACT02Y (Card),
--            CVACT03Y (Card-Xref)
-- =============================================================================

-- accounts — ACCTDATA VSAM KSDS (CVACT01Y)
CREATE TABLE IF NOT EXISTS accounts (
    id                  SERIAL          NOT NULL,
    account_id          VARCHAR(11)     NOT NULL,
    active_status       CHAR(1)         NOT NULL DEFAULT 'Y',
    current_balance     NUMERIC(12,2)   NOT NULL DEFAULT 0,
    credit_limit        NUMERIC(12,2)   NOT NULL DEFAULT 0,
    cash_credit_limit   NUMERIC(12,2)   NOT NULL DEFAULT 0,
    open_date           DATE,
    expiration_date     DATE,
    reissue_date        DATE,
    current_cycle_credit NUMERIC(12,2)  NOT NULL DEFAULT 0,
    current_cycle_debit  NUMERIC(12,2)  NOT NULL DEFAULT 0,
    address_zip         VARCHAR(10),
    group_id            VARCHAR(10),
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_accounts PRIMARY KEY (id),
    CONSTRAINT uq_accounts_account_id UNIQUE (account_id),
    CONSTRAINT ck_accounts_active_status CHECK (active_status IN ('Y', 'N')),
    CONSTRAINT ck_accounts_credit_limit_nonneg CHECK (credit_limit >= 0),
    CONSTRAINT ck_accounts_cash_credit_limit_nonneg CHECK (cash_credit_limit >= 0)
);

COMMENT ON TABLE accounts IS 'Credit card accounts (COBOL ACCTDATA VSAM KSDS, CVACT01Y)';
CREATE INDEX IF NOT EXISTS idx_accounts_active_status ON accounts (active_status);

-- customers — CUSTDATA VSAM KSDS (CVCUS01Y)
CREATE TABLE IF NOT EXISTS customers (
    id                  SERIAL          NOT NULL,
    customer_id         VARCHAR(9)      NOT NULL,
    first_name          VARCHAR(25)     NOT NULL DEFAULT '',
    middle_name         VARCHAR(25)     NOT NULL DEFAULT '',
    last_name           VARCHAR(25)     NOT NULL DEFAULT '',
    address_line_1      VARCHAR(50)     NOT NULL DEFAULT '',
    address_line_2      VARCHAR(50)     NOT NULL DEFAULT '',
    address_line_3      VARCHAR(50)     NOT NULL DEFAULT '',
    state_code          CHAR(2)         NOT NULL DEFAULT '',
    country_code        CHAR(3)         NOT NULL DEFAULT 'USA',
    zip_code            VARCHAR(10)     NOT NULL DEFAULT '',
    phone_1             VARCHAR(15)     NOT NULL DEFAULT '',
    phone_2             VARCHAR(15)     NOT NULL DEFAULT '',
    ssn                 VARCHAR(9)      NOT NULL DEFAULT '',
    govt_issued_id      VARCHAR(20)     NOT NULL DEFAULT '',
    date_of_birth       DATE,
    eft_account_id      VARCHAR(10)     NOT NULL DEFAULT '',
    primary_card_holder CHAR(1)         NOT NULL DEFAULT 'Y',
    fico_score          INTEGER,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_customers PRIMARY KEY (id),
    CONSTRAINT uq_customers_customer_id UNIQUE (customer_id),
    CONSTRAINT ck_customers_primary_card_holder CHECK (primary_card_holder IN ('Y', 'N')),
    CONSTRAINT ck_customers_fico_range CHECK (fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850))
);

COMMENT ON TABLE customers IS 'Customer demographics (COBOL CUSTDATA VSAM KSDS, CVCUS01Y)';
CREATE INDEX IF NOT EXISTS idx_customers_last_name ON customers (last_name);

-- cards — CARDDATA VSAM KSDS (CVACT02Y)
CREATE TABLE IF NOT EXISTS cards (
    id              SERIAL          NOT NULL,
    card_number     VARCHAR(16)     NOT NULL,
    account_id      VARCHAR(11)     NOT NULL,
    cvv_code        VARCHAR(3)      NOT NULL DEFAULT '',
    embossed_name   VARCHAR(50)     NOT NULL DEFAULT '',
    expiration_date DATE,
    active_status   CHAR(1)         NOT NULL DEFAULT 'Y',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_cards PRIMARY KEY (id),
    CONSTRAINT uq_cards_card_number UNIQUE (card_number),
    CONSTRAINT fk_cards_account_id
        FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE,
    CONSTRAINT ck_cards_active_status CHECK (active_status IN ('Y', 'N'))
);

COMMENT ON TABLE cards IS 'Credit card records (COBOL CARDDATA VSAM KSDS, CVACT02Y)';
-- Replicates CARDAIX alternate index
CREATE INDEX IF NOT EXISTS idx_cards_account_id ON cards (account_id);

-- card_xref — CARDXREF VSAM KSDS (CVACT03Y)
CREATE TABLE IF NOT EXISTS card_xref (
    id          SERIAL      NOT NULL,
    card_number VARCHAR(16) NOT NULL,
    customer_id VARCHAR(9)  NOT NULL,
    account_id  VARCHAR(11) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_card_xref PRIMARY KEY (id),
    CONSTRAINT uq_card_xref_card_number UNIQUE (card_number),
    CONSTRAINT fk_card_xref_card_number
        FOREIGN KEY (card_number) REFERENCES cards (card_number) ON DELETE CASCADE,
    CONSTRAINT fk_card_xref_customer_id
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE CASCADE,
    CONSTRAINT fk_card_xref_account_id
        FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE
);

COMMENT ON TABLE card_xref IS 'Card-Customer-Account cross-reference (COBOL CARDXREF VSAM KSDS, CVACT03Y)';
-- Replicates CXACAIX alternate index
CREATE INDEX IF NOT EXISTS idx_card_xref_account_id ON card_xref (account_id);
CREATE INDEX IF NOT EXISTS idx_card_xref_customer_id ON card_xref (customer_id);

-- Triggers for accounts/customers/cards updated_at
DROP TRIGGER IF EXISTS trg_accounts_updated_at ON accounts;
CREATE TRIGGER trg_accounts_updated_at
    BEFORE UPDATE ON accounts FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

DROP TRIGGER IF EXISTS trg_customers_updated_at ON customers;
CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

DROP TRIGGER IF EXISTS trg_cards_updated_at ON cards;
CREATE TRIGGER trg_cards_updated_at
    BEFORE UPDATE ON cards FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

-- =============================================================================
-- CardDemo Transaction Type Module — DDL
-- Migrated from DB2 CARDDEMO.TRANSACTION_TYPE and CARDDEMO.TRANSACTION_TYPE_CATEGORY
-- =============================================================================

-- transaction_types
-- Maps to DB2 CARDDEMO.TRANSACTION_TYPE (TR_TYPE CHAR(2), TR_DESCRIPTION VARCHAR(50))
-- TR_TYPE PIC X(2) -> type_code CHAR(2) PRIMARY KEY
-- TR_DESCRIPTION PIC X(50) -> description VARCHAR(50)
CREATE TABLE IF NOT EXISTS transaction_types (
    id           SERIAL          NOT NULL,
    type_code    CHAR(2)         NOT NULL,
    description  VARCHAR(50)     NOT NULL,
    created_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_transaction_types PRIMARY KEY (id),
    CONSTRAINT uq_transaction_types_type_code UNIQUE (type_code),
    CONSTRAINT ck_transaction_types_type_code_length CHECK (length(trim(type_code)) > 0),
    CONSTRAINT ck_transaction_types_description_nonempty CHECK (length(trim(description)) > 0)
);

COMMENT ON TABLE transaction_types IS 'Reference data for card transaction type codes (COBOL DB2 CARDDEMO.TRANSACTION_TYPE)';
COMMENT ON COLUMN transaction_types.type_code IS 'Two-character alphanumeric code, maps to COBOL TR_TYPE CHAR(2)';
COMMENT ON COLUMN transaction_types.description IS 'Human-readable label, maps to COBOL TR_DESCRIPTION VARCHAR(50)';

-- transaction_type_categories
-- Maps to DB2 CARDDEMO.TRANSACTION_TYPE_CATEGORY
-- (TR_TYPE CHAR(2), TR_CAT VARCHAR(4), TR_CAT_DESCRIPTION VARCHAR(50))
CREATE TABLE IF NOT EXISTS transaction_type_categories (
    id            SERIAL       NOT NULL,
    type_code     CHAR(2)      NOT NULL,
    category_code VARCHAR(4)   NOT NULL,
    description   VARCHAR(50)  NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_transaction_type_categories PRIMARY KEY (id),
    CONSTRAINT uq_txn_type_category UNIQUE (type_code, category_code),
    CONSTRAINT fk_txn_type_categories_type_code
        FOREIGN KEY (type_code) REFERENCES transaction_types (type_code)
        ON DELETE CASCADE,
    CONSTRAINT ck_txn_cat_category_code_nonempty CHECK (length(trim(category_code)) > 0),
    CONSTRAINT ck_txn_cat_description_nonempty CHECK (length(trim(description)) > 0)
);

COMMENT ON TABLE transaction_type_categories IS 'Sub-categories for each transaction type (COBOL DB2 CARDDEMO.TRANSACTION_TYPE_CATEGORY)';
COMMENT ON COLUMN transaction_type_categories.type_code IS 'FK to transaction_types.type_code';
COMMENT ON COLUMN transaction_type_categories.category_code IS 'Up to 4-char category code, maps to COBOL TR_CAT';
COMMENT ON COLUMN transaction_type_categories.description IS 'Category label, maps to COBOL TR_CAT_DESCRIPTION';

-- Indexes for common query patterns (list + filter)
CREATE INDEX IF NOT EXISTS idx_transaction_types_description ON transaction_types (description);
CREATE INDEX IF NOT EXISTS idx_txn_type_categories_type_code ON transaction_type_categories (type_code);

-- Trigger to keep updated_at in sync (PostgreSQL)
CREATE OR REPLACE FUNCTION trg_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_transaction_types_updated_at ON transaction_types;
CREATE TRIGGER trg_transaction_types_updated_at
    BEFORE UPDATE ON transaction_types
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

DROP TRIGGER IF EXISTS trg_txn_type_categories_updated_at ON transaction_type_categories;
CREATE TRIGGER trg_txn_type_categories_updated_at
    BEFORE UPDATE ON transaction_type_categories
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
