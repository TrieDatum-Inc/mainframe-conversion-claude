-- CardDemo Seed Data
-- Comprehensive test data covering: normal cases, boundary conditions, edge cases
-- All passwords are bcrypt hashes of 'Admin123' for all seed users.
-- In production, create users via the API to get proper hashes.

-- ============================================================
-- USERS (USRSEC VSAM KSDS)
-- SEC-USR-ID PIC X(08), SEC-USR-TYPE: 'A'=Admin, 'U'=User
-- Passwords: hash below represents password 'Admin123'
-- ============================================================
INSERT INTO users (usr_id, first_name, last_name, pwd_hash, usr_type) VALUES
-- Admin user (usr_type='A' -> routes to COADM01C in original)
('SYSADM00', 'System', 'Admin',
 '$2b$12$yFzkNe/9upngS5jDOVoxnup3WwxnbeIXYlx3VTWoW7BKJeUZ7Fqee',
 'A'),
-- Regular users (usr_type='U' -> routes to COMEN01C in original)
('USER0001', 'John', 'Smith',
 '$2b$12$yFzkNe/9upngS5jDOVoxnup3WwxnbeIXYlx3VTWoW7BKJeUZ7Fqee',
 'U'),
('USER0002', 'Jane', 'Doe',
 '$2b$12$yFzkNe/9upngS5jDOVoxnup3WwxnbeIXYlx3VTWoW7BKJeUZ7Fqee',
 'U'),
('USER0003', 'Bob', 'Johnson',
 '$2b$12$yFzkNe/9upngS5jDOVoxnup3WwxnbeIXYlx3VTWoW7BKJeUZ7Fqee',
 'U'),
('ADMN0001', 'Alice', 'Manager',
 '$2b$12$yFzkNe/9upngS5jDOVoxnup3WwxnbeIXYlx3VTWoW7BKJeUZ7Fqee',
 'A'),
-- Edge case: maximum length user ID (8 chars)
('LONGID01', 'Max', 'User',
 '$2b$12$yFzkNe/9upngS5jDOVoxnup3WwxnbeIXYlx3VTWoW7BKJeUZ7Fqee',
 'U');

-- ============================================================
-- TRANSACTION TYPES (DB2 CARDDEMO.TRANSACTION_TYPE)
-- TRAN-TYPE PIC X(02) - 2-char code
-- Used by COTRTLIC/COTRTUPC programs
-- ============================================================
INSERT INTO transaction_types (tran_type_cd, tran_type_desc) VALUES
('PU', 'Purchase'),
('PR', 'Payment Received'),
('RF', 'Refund'),
('CA', 'Cash Advance'),
('FE', 'Fee Charge'),
('IN', 'Interest Charge'),
('BA', 'Balance Transfer'),
('CR', 'Credit Adjustment');

-- ============================================================
-- TRANSACTION CATEGORIES (DB2 CARDDEMO.TRANSACTION_CATEGORY)
-- ============================================================
INSERT INTO transaction_categories (tran_type_cd, tran_cat_cd, tran_cat_desc) VALUES
('PU', 1001, 'Grocery'),
('PU', 1002, 'Restaurant'),
('PU', 1003, 'Gas Station'),
('PU', 1004, 'Online Retail'),
('PU', 1005, 'Travel'),
('CA', 2001, 'ATM Cash'),
('CA', 2002, 'Bank Cash Advance'),
('FE', 3001, 'Annual Fee'),
('FE', 3002, 'Late Payment Fee'),
('IN', 4001, 'Purchase Interest'),
('IN', 4002, 'Cash Advance Interest'),
('PR', 9999, 'Bill Payment'),
('RF', 5001, 'Merchant Refund'),
('BA', 6001, 'Balance Transfer In');

-- ============================================================
-- CUSTOMERS (CUSTDAT VSAM KSDS / CVCUS01Y, 500 bytes)
-- CUST-ID PIC 9(09) - 9-digit ID
-- ============================================================
INSERT INTO customers (
    cust_id, first_name, middle_name, last_name,
    addr_line1, addr_line2, addr_line3,
    addr_state_cd, addr_country_cd, addr_zip,
    phone_num1, phone_num2,
    ssn, govt_issued_id, dob,
    eft_account_id, pri_card_holder, fico_score
) VALUES
-- Normal case: complete customer record
(100000001, 'Alice', 'Marie', 'Johnson',
 '123 Main Street', 'Apt 4B', 'Springfield',
 'IL', 'USA', '62701-1234',
 '(217)555-1234', '(217)555-5678',
 123456789, 'DL-IL-A12345678', '1985-03-15',
 'EFT0000001', 'Y', 720),

-- Normal case: second customer
(100000002, 'Bob', NULL, 'Williams',
 '456 Oak Avenue', NULL, 'Chicago',
 'IL', 'USA', '60601',
 '(312)555-9876', NULL,
 987654321, 'DL-IL-B98765432', '1972-11-28',
 'EFT0000002', 'Y', 680),

-- Edge case: minimum FICO score (300)
(100000003, 'Carol', 'Ann', 'Davis',
 '789 Pine Road', 'Suite 100', 'Aurora',
 'IL', 'USA', '60502',
 '(630)555-1111', '(630)555-2222',
 234567890, 'PP-US-C23456789', '1960-07-04',
 'EFT0000003', 'Y', 300),

-- Edge case: maximum FICO score (850)
(100000004, 'David', 'Lee', 'Brown',
 '321 Elm Street', NULL, 'Naperville',
 'IL', 'USA', '60540',
 '(630)555-3333', NULL,
 345678901, 'DL-IL-D34567890', '1990-12-25',
 'EFT0000004', 'Y', 850),

-- Normal case: different state
(100000005, 'Eve', NULL, 'Martinez',
 '555 Sunset Blvd', 'Unit 200', 'Los Angeles',
 'CA', 'USA', '90001',
 '(213)555-7777', '(213)555-8888',
 456789012, 'DL-CA-E45678901', '1978-09-10',
 'EFT0000005', 'N', 750),

-- Edge case: non-primary card holder
(100000006, 'Frank', 'Joseph', 'Taylor',
 '100 First Ave', NULL, 'Seattle',
 'WA', 'USA', '98101',
 '(206)555-4444', NULL,
 567890123, 'DL-WA-F56789012', '1995-02-14',
 NULL, 'N', 650),

-- Normal case: TX customer
(100000007, 'Grace', 'Ellen', 'Anderson',
 '2000 Congress Ave', NULL, 'Austin',
 'TX', 'USA', '78701',
 '(512)555-6666', '(512)555-7777',
 678901234, 'DL-TX-G67890123', '1982-06-30',
 'EFT0000007', 'Y', 780),

-- Edge case: NY state
(100000008, 'Henry', NULL, 'Thomas',
 '42 Broadway', 'Floor 5', 'New York',
 'NY', 'USA', '10001',
 '(212)555-5555', NULL,
 789012345, 'PP-US-H78901234', '1968-04-01',
 'EFT0000008', 'Y', 710);

-- ============================================================
-- ACCOUNTS (ACCTDAT VSAM KSDS / CVACT01Y, 300 bytes)
-- ACCT-ID PIC 9(11) - 11-digit ID
-- ============================================================
INSERT INTO accounts (
    acct_id, active_status, curr_bal, credit_limit, cash_credit_limit,
    open_date, expiration_date, reissue_date,
    curr_cycle_credit, curr_cycle_debit, addr_zip, group_id
) VALUES
-- Normal case: active account with balance
(10000000001, 'Y', -1250.75, 5000.00, 1000.00,
 '2020-01-15', '2025-01-31', '2022-01-31',
 500.00, 1750.75, '62701-1234', 'GOLD01'),

-- Normal case: active account near credit limit
(10000000002, 'Y', -4800.00, 5000.00, 500.00,
 '2019-06-01', '2024-06-30', '2021-06-30',
 0.00, 4800.00, '60601', 'SILVER'),

-- Edge case: zero balance
(10000000003, 'Y', 0.00, 3000.00, 500.00,
 '2021-03-01', '2026-03-31', NULL,
 0.00, 0.00, '60502', 'BASIC01'),

-- Edge case: inactive account
(10000000004, 'N', -250.00, 2000.00, 200.00,
 '2018-11-15', '2023-11-30', '2020-11-30',
 250.00, 500.00, '60540', 'BASIC01'),

-- Normal case: high credit limit (Platinum)
(10000000005, 'Y', -3200.50, 25000.00, 5000.00,
 '2015-07-20', '2025-07-31', '2020-07-31',
 1200.00, 4400.50, '90001', 'PLAT01'),

-- Normal case: second account for customer 1 (COACTUPC tests multiple cards)
(10000000006, 'Y', -750.25, 2500.00, 250.00,
 '2022-05-10', '2027-05-31', NULL,
 0.00, 750.25, '62701-1234', 'BASIC01'),

-- Edge case: credit limit at maximum (10-digit)
(10000000007, 'Y', -12500.00, 50000.00, 10000.00,
 '2010-01-01', '2025-01-31', '2015-01-31',
 5000.00, 17500.00, '78701', 'GOLD01'),

-- Edge case: new account (open date = today simulation)
(10000000008, 'Y', 0.00, 1000.00, 200.00,
 '2024-01-01', '2029-01-31', NULL,
 0.00, 0.00, '10001', 'BASIC01');

-- ============================================================
-- CARDS (CARDDAT VSAM KSDS / CVACT02Y, 150 bytes)
-- CARD-NUM PIC X(16) - 16-character card number
-- ============================================================
INSERT INTO cards (
    card_num, acct_id, cvv_cd, embossed_name, expiration_date, active_status
) VALUES
-- Normal case: active Visa-format number
('4111111111111001', 10000000001, 123, 'ALICE M JOHNSON', '2025-01-31', 'Y'),
('4111111111112002', 10000000002, 456, 'BOB WILLIAMS', '2024-06-30', 'Y'),
('4111111111113003', 10000000003, 789, 'CAROL A DAVIS', '2026-03-31', 'Y'),
-- Edge case: inactive card
('4111111111114004', 10000000004, 111, 'DAVID L BROWN', '2023-11-30', 'N'),
-- Normal case: high-limit platinum card
('4111111111115005', 10000000005, 222, 'EVE MARTINEZ', '2025-07-31', 'Y'),
-- Normal case: second card for customer 1
('4111111111116006', 10000000006, 333, 'ALICE M JOHNSON', '2027-05-31', 'Y'),
-- Normal case: max-limit card
('4111111111117007', 10000000007, 444, 'GRACE E ANDERSON', '2025-01-31', 'Y'),
-- New card
('4111111111118008', 10000000008, 555, 'HENRY THOMAS', '2029-01-31', 'Y');

-- ============================================================
-- CARD_XREF (CXACAIX VSAM AIX / CVACT03Y, 50 bytes)
-- Links card_num -> cust_id + acct_id
-- ============================================================
INSERT INTO card_xref (card_num, cust_id, acct_id) VALUES
('4111111111111001', 100000001, 10000000001),
('4111111111112002', 100000002, 10000000002),
('4111111111113003', 100000003, 10000000003),
('4111111111114004', 100000004, 10000000004),
('4111111111115005', 100000005, 10000000005),
('4111111111116006', 100000001, 10000000006),  -- Alice has 2 cards
('4111111111117007', 100000007, 10000000007),
('4111111111118008', 100000008, 10000000008);

-- ============================================================
-- TRANSACTIONS (TRANSACT VSAM KSDS / CVTRA05Y, 350 bytes)
-- TRAN-ID PIC X(16) - 16-char transaction ID
-- ============================================================
INSERT INTO transactions (
    tran_id, tran_type_cd, tran_cat_cd, tran_source, tran_desc,
    tran_amt, merchant_id, merchant_name, merchant_city, merchant_zip,
    card_num, orig_ts, proc_ts
) VALUES
-- Normal purchases for card 1
('0000000000000001', 'PU', 1001, 'POS', 'Whole Foods Market',
 -125.50, 100000001, 'Whole Foods Market', 'Springfield', '62701',
 '4111111111111001', '2024-01-15 10:30:00', '2024-01-15 10:30:05'),
('0000000000000002', 'PU', 1002, 'POS', 'McDonalds',
 -12.75, 100000002, 'McDonalds Restaurant', 'Springfield', '62701',
 '4111111111111001', '2024-01-16 12:15:00', '2024-01-16 12:15:03'),
('0000000000000003', 'PU', 1003, 'POS', 'Shell Gas Station',
 -45.00, 100000003, 'Shell', 'Springfield', '62703',
 '4111111111111001', '2024-01-17 08:00:00', '2024-01-17 08:00:04'),

-- Payment received for card 1
('0000000000000004', 'PR', 9999, 'ONLINE', 'Bill Payment',
 200.00, NULL, NULL, NULL, NULL,
 '4111111111111001', '2024-01-20 14:00:00', '2024-01-20 14:00:01'),

-- Purchases for card 2
('0000000000000005', 'PU', 1004, 'WEB', 'Amazon.com',
 -350.00, 100000004, 'Amazon.com', 'Seattle', '98108',
 '4111111111112002', '2024-01-10 19:45:00', '2024-01-10 19:45:10'),
('0000000000000006', 'PU', 1005, 'POS', 'United Airlines',
 -450.00, 100000005, 'United Airlines', 'Chicago', '60666',
 '4111111111112002', '2024-01-12 07:30:00', '2024-01-12 07:30:08'),

-- Fee charge
('0000000000000007', 'FE', 3001, 'BATCH', 'Annual Fee',
 -95.00, NULL, 'Card Services', 'Omaha', '68179',
 '4111111111115005', '2024-01-01 00:00:00', '2024-01-01 00:00:00'),

-- Interest charge
('0000000000000008', 'IN', 4001, 'BATCH', 'Purchase Interest Jan',
 -18.50, NULL, 'Card Services', 'Omaha', '68179',
 '4111111111111001', '2024-01-31 23:59:00', '2024-01-31 23:59:00'),

-- Refund
('0000000000000009', 'RF', 5001, 'POS', 'Amazon Return',
 75.00, 100000004, 'Amazon.com', 'Seattle', '98108',
 '4111111111112002', '2024-01-22 11:00:00', '2024-01-22 11:00:05'),

-- Large purchase (boundary: near credit limit)
('0000000000000010', 'PU', 1004, 'WEB', 'Apple Store',
 -1200.00, 100000006, 'Apple Inc', 'Cupertino', '95014',
 '4111111111117007', '2024-01-25 15:30:00', '2024-01-25 15:30:12');

-- ============================================================
-- TRAN_CAT_BAL (TRAN-CAT-BAL-FILE / CVTRA01Y)
-- Used by CBACT04C for interest calculation
-- ============================================================
INSERT INTO tran_cat_bal (acct_id, tran_type_cd, tran_cat_cd, tran_cat_bal) VALUES
(10000000001, 'PU', 1001, -125.50),
(10000000001, 'PU', 1002, -12.75),
(10000000001, 'PU', 1003, -45.00),
(10000000002, 'PU', 1004, -350.00),
(10000000002, 'PU', 1005, -450.00),
(10000000005, 'FE', 3001, -95.00),
(10000000007, 'PU', 1004, -1200.00);

-- ============================================================
-- DISCLOSURE_GROUPS (DIS-GROUP-FILE / CVTRA02Y)
-- Interest rate lookup table for CBACT04C
-- ============================================================
INSERT INTO disclosure_groups (acct_group_id, tran_type_cd, tran_cat_cd, int_rate) VALUES
('GOLD01',  'PU', 1001, 15.99),
('GOLD01',  'PU', 1002, 15.99),
('GOLD01',  'PU', 1003, 15.99),
('GOLD01',  'PU', 1004, 17.99),
('GOLD01',  'PU', 1005, 15.99),
('GOLD01',  'CA', 2001, 24.99),
('GOLD01',  'CA', 2002, 24.99),
('SILVER',  'PU', 1001, 18.99),
('SILVER',  'PU', 1002, 18.99),
('SILVER',  'PU', 1003, 18.99),
('SILVER',  'PU', 1004, 20.99),
('SILVER',  'PU', 1005, 18.99),
('BASIC01', 'PU', 1001, 22.99),
('BASIC01', 'PU', 1002, 22.99),
('BASIC01', 'PU', 1003, 22.99),
('BASIC01', 'PU', 1004, 24.99),
('PLAT01',  'PU', 1001, 12.99),
('PLAT01',  'PU', 1002, 12.99),
('PLAT01',  'PU', 1004, 14.99),
('PLAT01',  'PU', 1005, 12.99),
('DEFAULT', 'PU', 1001, 21.99),  -- Fallback rate used by CBACT04C
('DEFAULT', 'CA', 2001, 25.99);

-- ============================================================
-- AUTH_SUMMARY (IMS PAUTSUM0 / CIPAUSMY)
-- ============================================================
INSERT INTO auth_summary (
    acct_id, cust_id, auth_status,
    credit_limit, cash_limit, curr_bal, cash_bal,
    approved_count, approved_amt,
    declined_count, declined_amt
) VALUES
(10000000001, 100000001, 'A', 5000.00, 1000.00, -1250.75, 0.00, 3, 183.25, 0, 0.00),
(10000000002, 100000002, 'A', 5000.00, 500.00, -4800.00, 0.00, 2, 800.00, 1, 500.00),
(10000000005, 100000005, 'A', 25000.00, 5000.00, -3200.50, 0.00, 1, 200.00, 0, 0.00);

-- ============================================================
-- AUTH_DETAIL (IMS PAUTDTL1 / CIPAUDTY)
-- Composite key: auth_date + auth_time + acct_id
-- ============================================================
INSERT INTO auth_detail (
    auth_date, auth_time, acct_id,
    card_num, tran_id, auth_id_code,
    response_code, response_reason, approved_amt,
    auth_type, match_status, fraud_flag
) VALUES
-- Approved authorization
('2024-01-15', '10:30:00', 10000000001,
 '4111111111111001', '0000000000000001', 'AUTH000001',
 '00', 'Approved', 125.50, 'P', 'Y', 'N'),
-- Declined authorization (insufficient funds)
('2024-01-20', '18:00:00', 10000000002,
 '4111111111112002', NULL, 'AUTH000002',
 '51', 'Insuf funds', 0.00, 'P', 'N', 'N'),
-- Fraud-flagged authorization
('2024-01-10', '03:00:00', 10000000001,
 '4111111111111001', NULL, 'AUTH000003',
 '00', 'Approved', 999.99, 'P', 'N', 'Y');
