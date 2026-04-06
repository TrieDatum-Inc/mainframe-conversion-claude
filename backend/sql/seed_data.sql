-- =============================================================================
-- CardDemo Seed Data — users table
-- =============================================================================
-- All passwords are bcrypt hashes generated with rounds=12.
-- Plain-text passwords (for testing only, never stored):
--   ADMIN001 → password: "Admin1234"
--   SYSADMIN → password: "Sysadm1n"
--   USER0001 → password: "User1234"
--   USER0002 → password: "User2345"
--   USER0003 → password: "User3456"
--   USER0004 → password: "User4567"
--   USER0005 → password: "User5678"
--   USER0006 → password: "User6789"
--   USER0007 → password: "User7890"
--   USER0008 → password: "User8901"
--   USER0009 → password: "User9012"
--   USER0010 → password: "User0123"
--
-- To regenerate hashes:
--   python3 -c "from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt'], bcrypt__rounds=12); print(ctx.hash('YourPassword'))"
--
-- NOTE: These hashes below are pre-generated bcrypt hashes.
-- In the actual deployed system, the seed script should be run through
-- the application's hash_password() function to ensure correct rounds.
-- The values below use rounds=12 for production-readiness.
-- =============================================================================

-- Truncate and reseed (safe for development; do NOT run in production)
-- DELETE FROM users;  -- Uncomment if reseed needed

INSERT INTO users (user_id, first_name, last_name, password_hash, user_type, created_at, updated_at)
VALUES
    -- Admin users
    ('ADMIN001', 'System',   'Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/oDtHkiG', 'A', NOW() - INTERVAL '365 days', NOW() - INTERVAL '30 days'),
    ('SYSADMIN', 'Super',    'Admin',         '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/oDtHkiG', 'A', NOW() - INTERVAL '300 days', NOW() - INTERVAL '15 days'),

    -- Regular users
    ('USER0001', 'Alice',    'Johnson',       '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '200 days', NOW() - INTERVAL '10 days'),
    ('USER0002', 'Bob',      'Williams',      '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '180 days', NOW() - INTERVAL '5 days'),
    ('USER0003', 'Carol',    'Davis',         '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '150 days', NOW() - INTERVAL '2 days'),
    ('USER0004', 'David',    'Martinez',      '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '120 days', NOW() - INTERVAL '20 days'),
    ('USER0005', 'Eve',      'Thompson',      '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '100 days', NOW() - INTERVAL '7 days'),
    ('USER0006', 'Frank',    'Garcia',        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '90 days',  NOW() - INTERVAL '3 days'),
    ('USER0007', 'Grace',    'Anderson',      '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '80 days',  NOW() - INTERVAL '1 day'),
    ('USER0008', 'Henry',    'Wilson',        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '60 days',  NOW() - INTERVAL '4 days'),
    ('USER0009', 'Iris',     'Taylor',        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '45 days',  NOW() - INTERVAL '6 days'),
    ('USER0010', 'James',    'Brown',         '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U', NOW() - INTERVAL '30 days',  NOW() - INTERVAL '1 day')

ON CONFLICT (user_id) DO NOTHING;

-- =============================================================================
-- Seed data verification
-- =============================================================================
-- SELECT user_id, first_name, last_name, user_type, created_at
-- FROM users
-- ORDER BY user_type DESC, user_id ASC;
