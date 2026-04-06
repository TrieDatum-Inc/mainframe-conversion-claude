-- =============================================================================
-- CardDemo PostgreSQL Schema
-- COBOL Source: VSAM KSDS USRSEC (CSUSR01Y copybook)
-- Generated for: Authentication Module (initial schema)
-- =============================================================================

-- =============================================================================
-- Table: users
-- Source: USRSEC VSAM KSDS (CSUSR01Y copybook)
-- Key: SEC-USR-ID X(8) → user_id VARCHAR(8) PRIMARY KEY
--
-- COBOL field mapping:
--   SEC-USR-ID    PIC X(08)  → user_id    VARCHAR(8)   NOT NULL PRIMARY KEY
--   SEC-USR-PWD   PIC X(08)  → password_hash VARCHAR(255) NOT NULL  (bcrypt; NOT plain text)
--   SEC-USR-FNAME PIC X(20)  → first_name VARCHAR(20)  NOT NULL
--   SEC-USR-LNAME PIC X(20)  → last_name  VARCHAR(20)  NOT NULL
--   SEC-USR-TYPE  PIC X(01)  → user_type  CHAR(1)      NOT NULL CHECK IN ('A','U')
--   SEC-USR-FILLER PIC X(23) → (discarded — unused padding bytes)
--
-- Key changes from legacy:
--   1. SEC-USR-PWD (plain text) → password_hash (bcrypt, one-way)
--   2. SEC-USR-TYPE 'R' → normalized to 'U' (Regular)
--   3. created_at / updated_at added for audit trail (not in COBOL)
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id         VARCHAR(8)   NOT NULL,
    first_name      VARCHAR(20)  NOT NULL,
    last_name       VARCHAR(20)  NOT NULL,
    -- bcrypt hash replaces SEC-USR-PWD X(8) plain text storage
    -- password_hash is NEVER returned in any API response
    password_hash   VARCHAR(255) NOT NULL,
    -- SEC-USR-TYPE: 'A'=Admin, 'U'=User ('R' in legacy → normalized to 'U')
    user_type       CHAR(1)      NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT chk_users_type CHECK (user_type IN ('A', 'U'))
);

-- Index on last_name: supports user search/sort by name (COUSR00C display)
CREATE INDEX IF NOT EXISTS idx_users_last_name ON users(last_name);

-- Index on user_type: supports admin/user separation queries
CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type);

-- Function to auto-update updated_at on row modification
-- Replaces COBOL pattern: MOVE FUNCTION CURRENT-DATE TO WS-TIMESTAMP
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: update updated_at whenever a user row is modified
CREATE OR REPLACE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Comments for documentation
-- =============================================================================
COMMENT ON TABLE users IS
    'COBOL source: USRSEC VSAM KSDS (CSUSR01Y copybook). '
    'Replaces plain-text password storage with bcrypt hashing. '
    'Key: SEC-USR-ID PIC X(08).';

COMMENT ON COLUMN users.user_id IS
    'COBOL: SEC-USR-ID PIC X(08) — VSAM KSDS primary key';
COMMENT ON COLUMN users.first_name IS
    'COBOL: SEC-USR-FNAME PIC X(20)';
COMMENT ON COLUMN users.last_name IS
    'COBOL: SEC-USR-LNAME PIC X(20)';
COMMENT ON COLUMN users.password_hash IS
    'COBOL: SEC-USR-PWD PIC X(08) — was plain text; now bcrypt hash. NEVER returned in API responses.';
COMMENT ON COLUMN users.user_type IS
    'COBOL: SEC-USR-TYPE PIC X(01) — A=Admin, U=User (legacy R normalized to U)';
COMMENT ON COLUMN users.created_at IS
    'Audit: record creation timestamp. Not in COBOL source.';
COMMENT ON COLUMN users.updated_at IS
    'Audit: last modification timestamp. Supports optimistic locking. Not in COBOL source.';
