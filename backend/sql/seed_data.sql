-- Seed data for the users table
-- COBOL origin: USRSEC VSAM KSDS test records
--
-- Passwords are bcrypt hashes (rounds=12):
--   ADMIN001 / Admin01!   → $2b$12$...
--   ADMIN002 / Admin02!   → $2b$12$...
--   USER0001 / User001!   → $2b$12$...
--   USER0002 / User002!   → $2b$12$...
--   USER0003 / User003!   → $2b$12$...
--
-- SECURITY NOTE: These are TEST hashes for development/CI only.
-- Production data must be generated via the application's hash_password() utility.
-- The bcrypt hashes below correspond to the test passwords listed above.
-- Run `python -c "from app.utils.security import hash_password; print(hash_password('Admin01!'))"` to regenerate.
--
-- To apply: psql -U carddemo -d carddemo -f seed_data.sql

INSERT INTO users (user_id, first_name, last_name, password_hash, user_type) VALUES
(
    'ADMIN001',
    'John',
    'Admin',
    '$2b$12$WdLAWlZ4GHZxUh2tEMV6.upvhXIVsEcAWp4Wft3v9Nl1Q.lM/xDlK',
    'A'
),
(
    'ADMIN002',
    'Jane',
    'Supervisor',
    '$2b$12$TBOjHgHnPk8WmGjlmm/Ybuy9B6WqC9.9aYi1LK9CweAju3zJDcXp2',
    'A'
),
(
    'USER0001',
    'Alice',
    'Smith',
    '$2b$12$yxixEHb89Q0/6nhm6VzOZOkShuUs1/oBdLa.iCE5HjBhRrauKr0te',
    'U'
),
(
    'USER0002',
    'Bob',
    'Jones',
    '$2b$12$mvBdGvX.OdGWwg5o7DDEUuvl7GjuQlugZZ7XYuFec9XTK9BFaxxQS',
    'U'
),
(
    'USER0003',
    'Carol',
    'Williams',
    '$2b$12$Z2cpwLm0QruGWOuUguc5L.94f/gbJ56xTcSQJfbGwO30I9YhZbuI6',
    'U'
)
ON CONFLICT (user_id) DO NOTHING;
