-- CardDemo Seed Data
-- Provides test users, accounts, cards, customers, and reference data
-- Passwords are bcrypt hashes of the values shown in comments
-- NOTE: In COBOL the password was stored as plaintext PIC X(08) and uppercased before comparison.
--       Modern equivalent: bcrypt hash stored here; login service uppercases input then verifies.

-- ============================================================
-- USERS (from USRSEC VSAM — admin and regular users)
-- Admin users: user_type = 'A'
-- Regular users: user_type = 'U'
-- Plaintext passwords (for reference / testing only):
--   ADMIN001 -> password: ADMIN001
--   ADMIN002 -> password: SYSADMIN
--   USER0001 -> password: USER0001
--   USER0002 -> password: TESTPASS
--   USER0003 -> password: MYPASSWD
-- bcrypt hashes generated with cost factor 12
-- ============================================================
INSERT INTO users (user_id, first_name, last_name, password, user_type) VALUES
(
    'ADMIN001',
    'System',
    'Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4oY4Qd5G/.',
    'A'
),
(
    'ADMIN002',
    'Jane',
    'Sysadmin',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'A'
),
(
    'USER0001',
    'John',
    'Doe',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4oY4Qd5G/.',
    'U'
),
(
    'USER0002',
    'Alice',
    'Smith',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    'U'
),
(
    'USER0003',
    'Bob',
    'Johnson',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    'U'
)
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================
-- TRANSACTION TYPES (reference data — from TRANTYPE VSAM / DB2 TRANSACTION_TYPE)
-- ============================================================
INSERT INTO transaction_types (tran_type_cd, description) VALUES
('01', 'Purchase'),
('02', 'Cash Advance'),
('03', 'Balance Transfer'),
('04', 'Payment'),
('05', 'Fee'),
('06', 'Interest Charge'),
('07', 'Credit Adjustment'),
('08', 'Debit Adjustment'),
('09', 'Dispute Credit'),
('10', 'Dispute Debit'),
('SA', 'Sale'),
('RE', 'Return/Refund'),
('PA', 'Payment')
ON CONFLICT (tran_type_cd) DO NOTHING;

-- ============================================================
-- TRANSACTION CATEGORIES (reference data)
-- ============================================================
INSERT INTO transaction_categories (tran_type_cd, tran_cat_cd, description) VALUES
('01', 1001, 'Grocery Stores'),
('01', 1002, 'Gas Stations'),
('01', 1003, 'Restaurants'),
('01', 1004, 'Travel'),
('01', 1005, 'Entertainment'),
('01', 1006, 'Online Retail'),
('02', 2001, 'ATM Cash Advance'),
('02', 2002, 'Over-Counter Cash Advance'),
('04', 4001, 'Online Payment'),
('04', 4002, 'Check Payment'),
('04', 4003, 'Automatic Payment'),
('05', 5001, 'Annual Fee'),
('05', 5002, 'Late Payment Fee'),
('05', 5003, 'Foreign Transaction Fee'),
('06', 6001, 'Purchase Interest'),
('06', 6002, 'Cash Advance Interest')
ON CONFLICT (tran_type_cd, tran_cat_cd) DO NOTHING;

-- ============================================================
-- CUSTOMERS
-- ============================================================
INSERT INTO customers (
    cust_id, first_name, middle_name, last_name,
    addr_line_1, addr_line_2, addr_state_cd, addr_country_cd, addr_zip,
    phone_num_1, ssn, dob, fico_credit_score
) VALUES
(
    100000001, 'John', 'M', 'Doe',
    '123 Main Street', NULL, 'CA', 'USA', '90210',
    '555-123-4567', 123456789, '1980-05-15', 720
),
(
    100000002, 'Alice', 'R', 'Smith',
    '456 Oak Avenue', 'Apt 2B', 'NY', 'USA', '10001',
    '555-234-5678', 234567890, '1975-09-22', 780
),
(
    100000003, 'Bob', 'T', 'Johnson',
    '789 Pine Road', NULL, 'TX', 'USA', '75201',
    '555-345-6789', 345678901, '1990-03-10', 650
),
(
    100000004, 'Carol', NULL, 'Williams',
    '321 Elm Street', NULL, 'FL', 'USA', '33101',
    '555-456-7890', 456789012, '1965-12-01', 800
),
(
    100000005, 'David', 'J', 'Brown',
    '654 Maple Drive', NULL, 'WA', 'USA', '98101',
    '555-567-8901', 567890123, '1985-07-18', 710
)
ON CONFLICT (cust_id) DO NOTHING;

-- ============================================================
-- ACCOUNTS
-- ============================================================
INSERT INTO accounts (
    acct_id, active_status, curr_bal, credit_limit, cash_credit_limit,
    open_date, expiration_date, reissue_date,
    curr_cycle_credit, curr_cycle_debit, addr_zip, group_id
) VALUES
(
    10000000001, 'Y', 1250.75, 10000.00, 2000.00,
    '2020-01-15', '2025-01-15', '2023-01-15',
    0.00, 1250.75, '90210', 'PREM01'
),
(
    10000000002, 'Y', 3500.00, 15000.00, 3000.00,
    '2019-06-01', '2024-06-01', '2022-06-01',
    500.00, 4000.00, '10001', 'GOLD01'
),
(
    10000000003, 'Y', 750.50, 5000.00, 1000.00,
    '2021-03-10', '2026-03-10', '2024-03-10',
    0.00, 750.50, '75201', 'STND01'
),
(
    10000000004, 'Y', 0.00, 25000.00, 5000.00,
    '2015-09-20', '2025-09-20', '2023-09-20',
    2000.00, 0.00, '33101', 'PLAT01'
),
(
    10000000005, 'N', 0.00, 8000.00, 1500.00,
    '2018-11-05', '2023-11-05', NULL,
    0.00, 0.00, '98101', 'STND01'
)
ON CONFLICT (acct_id) DO NOTHING;

-- ============================================================
-- CARDS
-- ============================================================
INSERT INTO cards (card_num, acct_id, cvv_cd, embossed_name, expiration_date, active_status) VALUES
('4111111111111001', 10000000001, 123, 'JOHN M DOE',      '2025-01-31', 'Y'),
('4111111111111002', 10000000002, 456, 'ALICE R SMITH',   '2024-06-30', 'Y'),
('4111111111111003', 10000000003, 789, 'BOB T JOHNSON',   '2026-03-31', 'Y'),
('4111111111111004', 10000000004, 321, 'CAROL WILLIAMS',  '2025-09-30', 'Y'),
('4111111111111005', 10000000005, 654, 'DAVID J BROWN',   '2023-11-30', 'N')
ON CONFLICT (card_num) DO NOTHING;

-- ============================================================
-- CARD CROSS REFERENCES
-- ============================================================
INSERT INTO card_cross_references (card_num, cust_id, acct_id) VALUES
('4111111111111001', 100000001, 10000000001),
('4111111111111002', 100000002, 10000000002),
('4111111111111003', 100000003, 10000000003),
('4111111111111004', 100000004, 10000000004),
('4111111111111005', 100000005, 10000000005)
ON CONFLICT (card_num) DO NOTHING;

-- ============================================================
-- TRANSACTIONS (sample data)
-- ============================================================
INSERT INTO transactions (
    tran_id, tran_type_cd, tran_cat_cd, source, description,
    amount, merchant_id, merchant_name, merchant_city, merchant_zip,
    card_num, orig_timestamp, proc_timestamp
) VALUES
(
    'TXN0000000000001', '01', 1001, 'POS', 'Grocery purchase',
    45.23, 100000001, 'SAFEWAY GROCERY', 'Los Angeles', '90211',
    '4111111111111001',
    NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days'
),
(
    'TXN0000000000002', '01', 1003, 'POS', 'Restaurant dining',
    78.50, 100000002, 'PIZZA PALACE', 'Los Angeles', '90212',
    '4111111111111001',
    NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days'
),
(
    'TXN0000000000003', '04', 4001, 'WEB', 'Online payment',
    -500.00, NULL, NULL, NULL, NULL,
    '4111111111111002',
    NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'
),
(
    'TXN0000000000004', '01', 1006, 'WEB', 'Online retail purchase',
    199.99, 100000003, 'AMAZON MARKETPLACE', 'Seattle', '98101',
    '4111111111111002',
    NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'
),
(
    'TXN0000000000005', '02', 2001, 'ATM', 'ATM cash advance',
    200.00, 100000004, 'BANK ATM', 'Houston', '77001',
    '4111111111111003',
    NOW() - INTERVAL '12 hours', NOW() - INTERVAL '12 hours'
)
ON CONFLICT (tran_id) DO NOTHING;

-- ============================================================
-- REPORT JOBS (sample data for CORPT00C testing)
-- These represent previously submitted report jobs.
-- ============================================================
INSERT INTO report_jobs (report_type, start_date, end_date, status, submitted_by, submitted_at, completed_at) VALUES
(
    'monthly',
    DATE_TRUNC('month', CURRENT_DATE)::DATE,
    (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month - 1 day')::DATE,
    'completed',
    'USER0001',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days' + INTERVAL '5 minutes'
),
(
    'yearly',
    (DATE_TRUNC('year', CURRENT_DATE))::DATE,
    (DATE_TRUNC('year', CURRENT_DATE) + INTERVAL '1 year - 1 day')::DATE,
    'completed',
    'ADMIN001',
    NOW() - INTERVAL '7 days',
    NOW() - INTERVAL '7 days' + INTERVAL '12 minutes'
),
(
    'custom',
    '2024-01-01',
    '2024-03-31',
    'pending',
    'USER0002',
    NOW() - INTERVAL '1 hour',
    NULL
)
ON CONFLICT DO NOTHING;

-- ============================================================
-- DISCLOSURE GROUPS (interest rate reference data)
-- ============================================================
INSERT INTO disclosure_groups (acct_group_id, tran_type_cd, tran_cat_cd, interest_rate, fee_amount) VALUES
('PREM01', '01', 1001, 15.99, 0.00),
('PREM01', '02', 2001, 24.99, 10.00),
('GOLD01', '01', 1001, 17.99, 0.00),
('GOLD01', '02', 2001, 26.99, 10.00),
('PLAT01', '01', 1001, 13.99, 0.00),
('PLAT01', '02', 2001, 22.99, 10.00),
('STND01', '01', 1001, 21.99, 0.00),
('STND01', '02', 2001, 29.99, 15.00),
('DEFAULT', '01', 1001, 24.99, 0.00),
('DEFAULT', '02', 2001, 29.99, 15.00)
ON CONFLICT (acct_group_id, tran_type_cd, tran_cat_cd) DO NOTHING;
