-- Create the users table and supporting objects
-- COBOL origin: USRSEC VSAM KSDS (CSUSR01Y copybook)
--
--   SEC-USR-ID     X(8)  → user_id VARCHAR(8) PRIMARY KEY
--   SEC-USR-FNAME  X(20) → first_name VARCHAR(20)
--   SEC-USR-LNAME  X(20) → last_name VARCHAR(20)
--   SEC-USR-PWD    X(8)  → password_hash VARCHAR(255) [bcrypt; plain-text replaced]
--   SEC-USR-TYPE   X(1)  → user_type CHAR(1) CHECK IN ('A','U')
--   SEC-USR-FILLER X(23) → NOT MIGRATED (unused padding)
--
-- To apply: psql -U carddemo -d carddemo -f create_table.sql

-- --------------------------------------------------------------------
-- Trigger function: auto-update updated_at on every row modification
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- --------------------------------------------------------------------
-- users table — replaces USRSEC VSAM KSDS
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       VARCHAR(8)   NOT NULL,
    first_name    VARCHAR(20)  NOT NULL,
    last_name     VARCHAR(20)  NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type     CHAR(1)      NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_users      PRIMARY KEY (user_id),
    CONSTRAINT chk_users_type CHECK (user_type IN ('A', 'U'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_last_name ON users (last_name);
CREATE INDEX IF NOT EXISTS idx_users_user_type ON users (user_type);

-- Trigger: auto-update updated_at on row modification
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
