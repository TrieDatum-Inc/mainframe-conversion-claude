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
