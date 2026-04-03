-- =============================================================================
-- Seed Data — User Administration Module
-- 5 users: 2 admin (type 'A'), 3 regular (type 'U')
--
-- Passwords are bcrypt hashes of the shown plaintext values.
-- Hash generated with bcrypt cost factor 12.
--   admin001  → password: "Admin001!"
--   admin002  → password: "Admin002!"
--   user0001  → password: "User0001!"
--   user0002  → password: "User0002!"
--   user0003  → password: "User0003!"
--
-- User IDs are 8 characters (PIC X(08) from CSUSR01Y.cpy)
-- First/Last names are up to 20 chars each (PIC X(20))
-- =============================================================================

INSERT INTO users (user_id, first_name, last_name, password, user_type, created_at, updated_at)
VALUES
    -- Admin users (type 'A')
    (
        'admin001',
        'Alice',
        'Administrator',
        -- bcrypt hash for "Admin001!"
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0/nRs5TpUu',
        'A',
        NOW(),
        NOW()
    ),
    (
        'admin002',
        'Bob',
        'Supervisor',
        -- bcrypt hash for "Admin002!"
        '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
        'A',
        NOW(),
        NOW()
    ),
    -- Regular users (type 'U')
    (
        'user0001',
        'Carol',
        'Smith',
        -- bcrypt hash for "User0001!"
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        'U',
        NOW(),
        NOW()
    ),
    (
        'user0002',
        'David',
        'Johnson',
        -- bcrypt hash for "User0002!"
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        'U',
        NOW(),
        NOW()
    ),
    (
        'user0003',
        'Eve',
        'Williams',
        -- bcrypt hash for "User0003!"
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        'U',
        NOW(),
        NOW()
    )
ON CONFLICT (user_id) DO NOTHING;
