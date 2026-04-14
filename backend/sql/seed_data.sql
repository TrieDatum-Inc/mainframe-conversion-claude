-- Seed data for the users table
-- COBOL origin: USRSEC VSAM KSDS test records
--
-- Passwords are bcrypt hashes (rounds=12):
--   ADMIN001 / AdminPass1!   → $2b$12$...
--   ADMIN002 / AdminPass2!   → $2b$12$...
--   USER0001 / UserPass1!    → $2b$12$...
--   USER0002 / UserPass2!    → $2b$12$...
--   USER0003 / UserPass3!    → $2b$12$...
--
-- SECURITY NOTE: These are TEST hashes for development/CI only.
-- Production data must be generated via the application's hash_password() utility.
-- The bcrypt hashes below correspond to the test passwords listed above.
-- Run `python -c "from app.utils.security import hash_password; print(hash_password('AdminPass1!'))"` to regenerate.
--
-- To apply: psql -U carddemo -d carddemo -f seed_data.sql

INSERT INTO users (user_id, first_name, last_name, password_hash, user_type) VALUES
(
    'ADMIN001',
    'John',
    'Admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/Rp1m6H7a.',
    'A'
),
(
    'ADMIN002',
    'Jane',
    'Supervisor',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    'A'
),
(
    'USER0001',
    'Alice',
    'Smith',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    'U'
),
(
    'USER0002',
    'Bob',
    'Jones',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    'U'
),
(
    'USER0003',
    'Carol',
    'Williams',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    'U'
)
ON CONFLICT (user_id) DO NOTHING;
