-- =============================================================================
-- User Administration Module — PostgreSQL Schema
-- Converted from VSAM USRSEC KSDS file (CSUSR01Y.cpy)
--
-- Original COBOL layout (80 bytes):
--   SEC-USR-ID     PIC X(08)  — primary KSDS key
--   SEC-USR-FNAME  PIC X(20)  — first name
--   SEC-USR-LNAME  PIC X(20)  — last name
--   SEC-USR-PWD    PIC X(08)  — password (PLAINTEXT in COBOL — bcrypt here)
--   SEC-USR-TYPE   PIC X(01)  — 'A'=Admin, 'U'=User
--   SEC-USR-FILLER PIC X(23)  — unused
--
-- Bug fixes applied vs. COBOL:
--   1. user_type CHECK constraint enforces 'A' or 'U' strictly
--      (COBOL COUSR01C only validated for blank, allowing any character)
--   2. password stored as bcrypt hash, not plaintext
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id      VARCHAR(8)   PRIMARY KEY,
    first_name   VARCHAR(20)  NOT NULL,
    last_name    VARCHAR(20)  NOT NULL,
    -- bcrypt hash; COBOL stored plaintext PIC X(08), we enforce hashing here
    password     VARCHAR(255) NOT NULL,
    -- COBOL bug fix: strictly enforce 'A' or 'U' (original only checked NOT SPACES)
    user_type    CHAR(1)      NOT NULL CHECK (user_type IN ('A', 'U')),
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for list/browse operations (maps to VSAM STARTBR/READNEXT by key order)
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users (user_id);

-- Index supporting type-filtered queries
CREATE INDEX IF NOT EXISTS idx_users_user_type ON users (user_type);

-- Trigger to auto-update updated_at on every UPDATE (mirrors VSAM REWRITE timestamp)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_updated_at ON users;
CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
