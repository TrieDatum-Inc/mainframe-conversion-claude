-- CardDemo Batch Processing Module: Seed Data
-- Sufficient data to test all batch processing scenarios
-- Covers: transaction posting, interest calculation, export/import, report generation

-- ============================================================
-- Transaction Types (TRANTYPE KSDS / CVTRA03Y)
-- ============================================================
INSERT INTO transaction_types (tran_type, tran_type_desc) VALUES
    ('01', 'Purchase'),
    ('02', 'Refund'),
    ('03', 'Cash Advance'),
    ('04', 'Balance Transfer'),
    ('05', 'Interest Charge'),
    ('06', 'Fee'),
    ('07', 'Payment'),
    ('08', 'Adjustment'),
    ('09', 'Dispute Credit'),
    ('10', 'Reward Redemption')
ON CONFLICT (tran_type) DO NOTHING;

-- ============================================================
-- Transaction Categories (TRANCATG KSDS / CVTRA04Y)
-- ============================================================
INSERT INTO transaction_categories (tran_type, tran_cat_cd, tran_cat_desc) VALUES
    ('01', '0001', 'Groceries'),
    ('01', '0002', 'Restaurants and Dining'),
    ('01', '0003', 'Gas and Fuel'),
    ('01', '0004', 'Travel and Lodging'),
    ('01', '0005', 'Interest Charges'),
    ('01', '0006', 'Entertainment'),
    ('01', '0007', 'Healthcare and Medical'),
    ('01', '0008', 'Online Shopping'),
    ('02', '0001', 'Grocery Refund'),
    ('02', '0002', 'Restaurant Refund'),
    ('02', '0008', 'Online Shopping Refund'),
    ('03', '0001', 'ATM Cash Advance'),
    ('07', '0001', 'Online Payment'),
    ('07', '0002', 'Check Payment'),
    ('05', '0005', 'Monthly Interest Charge')
ON CONFLICT (tran_type, tran_cat_cd) DO NOTHING;

-- ============================================================
-- Customers (CUSTFILE KSDS / CVCUS01Y)
-- ============================================================
INSERT INTO customers (
    cust_id, cust_first_name, cust_middle_name, cust_last_name,
    cust_addr_line_1, cust_addr_line_2, cust_addr_line_3,
    cust_addr_state_cd, cust_addr_country_cd, cust_addr_zip,
    cust_phone_num_1, cust_phone_num_2, cust_ssn,
    cust_govt_issued_id, cust_dob, cust_eft_account_id,
    cust_pri_card_holder_ind, cust_fico_credit_score
) VALUES
    ('000000001', 'Alice', 'Marie', 'Johnson',
     '123 Main Street', 'Apt 4B', NULL,
     'CA', 'USA', '90210',
     '555-867-5309', NULL, '123456789',
     'DL-CA-12345678', '1985-03-15', 'EFT0000001',
     'Y', 780),
    ('000000002', 'Bob', NULL, 'Smith',
     '456 Oak Avenue', NULL, NULL,
     'NY', 'USA', '10001',
     '555-234-5678', '555-234-5679', '234567890',
     'DL-NY-87654321', '1990-07-22', 'EFT0000002',
     'Y', 720),
    ('000000003', 'Carol', 'Ann', 'Williams',
     '789 Pine Road', 'Suite 100', NULL,
     'TX', 'USA', '75201',
     '555-345-6789', NULL, '345678901',
     'PP-US-A1234567', '1978-11-30', 'EFT0000003',
     'Y', 650),
    ('000000004', 'David', 'James', 'Brown',
     '321 Elm Street', NULL, NULL,
     'FL', 'USA', '33101',
     '555-456-7890', '555-456-7891', '456789012',
     'DL-FL-11223344', '1995-01-08', 'EFT0000004',
     'Y', 800),
    ('000000005', 'Eve', 'Marie', 'Davis',
     '555 Maple Drive', NULL, NULL,
     'WA', 'USA', '98001',
     '555-567-8901', NULL, '567890123',
     'DL-WA-55667788', '1988-09-14', 'EFT0000005',
     'Y', 590)
ON CONFLICT (cust_id) DO NOTHING;

-- ============================================================
-- Accounts (ACCTFILE KSDS / CVACT01Y)
-- ============================================================
INSERT INTO accounts (
    acct_id, acct_active_status, acct_curr_bal, acct_credit_limit,
    acct_cash_credit_limit, acct_open_date, acct_expiration_date,
    acct_reissue_date, acct_curr_cyc_credit, acct_curr_cyc_debit,
    acct_addr_zip, acct_group_id
) VALUES
    -- Active account, within credit limit, not expired
    ('00000000001', 'Y', 1500.00, 5000.00, 1000.00,
     '2020-01-15', '2027-12-31', '2025-01-15',
     2500.00, 1000.00, '90210', 'GOLD'),
    -- Active account, near credit limit
    ('00000000002', 'Y', 4800.00, 5000.00, 1000.00,
     '2019-06-01', '2026-06-30', '2024-06-01',
     4800.00, 0.00, '10001', 'SILVER'),
    -- Active account for overlimit test (balance close to limit)
    ('00000000003', 'Y', 2000.00, 2500.00, 500.00,
     '2021-03-10', '2028-03-31', '2026-03-10',
     2000.00, 0.00, '75201', 'BRONZE'),
    -- Expired account (expiration date in the past)
    ('00000000004', 'Y', 500.00, 3000.00, 500.00,
     '2018-09-01', '2024-01-31', '2022-09-01',
     500.00, 0.00, '33101', 'GOLD'),
    -- Active account with zero balance for interest testing
    ('00000000005', 'Y', 0.00, 10000.00, 2000.00,
     '2022-11-01', '2029-11-30', '2027-11-01',
     0.00, 0.00, '98001', 'PLATINUM')
ON CONFLICT (acct_id) DO NOTHING;

-- ============================================================
-- Cards (CARDFILE KSDS / CVACT02Y)
-- ============================================================
INSERT INTO cards (
    card_num, card_acct_id, card_cvv_cd,
    card_embossed_name, card_expiration_date, card_active_status
) VALUES
    ('4111111111111111', '00000000001', '123', 'ALICE M JOHNSON', '2027-12-31', 'Y'),
    ('4222222222222222', '00000000002', '456', 'BOB SMITH', '2026-06-30', 'Y'),
    ('4333333333333333', '00000000003', '789', 'CAROL A WILLIAMS', '2028-03-31', 'Y'),
    ('4444444444444444', '00000000004', '321', 'DAVID J BROWN', '2024-01-31', 'Y'),
    ('4555555555555555', '00000000005', '654', 'EVE M DAVIS', '2029-11-30', 'Y'),
    -- Additional cards for testing
    ('4666666666666666', '00000000001', '987', 'ALICE M JOHNSON', '2027-12-31', 'Y')
ON CONFLICT (card_num) DO NOTHING;

-- ============================================================
-- Card Cross-References (XREFFILE KSDS / CVACT03Y)
-- ============================================================
INSERT INTO card_cross_references (xref_card_num, xref_cust_id, xref_acct_id) VALUES
    ('4111111111111111', '000000001', '00000000001'),
    ('4222222222222222', '000000002', '00000000002'),
    ('4333333333333333', '000000003', '00000000003'),
    ('4444444444444444', '000000004', '00000000004'),
    ('4555555555555555', '000000005', '00000000005'),
    ('4666666666666666', '000000001', '00000000001')
ON CONFLICT (xref_card_num) DO NOTHING;

-- ============================================================
-- Transactions (TRANSACT KSDS / CVTRA05Y)
-- Sample transactions for report generation testing
-- ============================================================
INSERT INTO transactions (
    tran_id, tran_type_cd, tran_cat_cd, tran_source, tran_desc,
    tran_amt, tran_merchant_id, tran_merchant_name,
    tran_merchant_city, tran_merchant_zip, tran_card_num,
    tran_orig_ts, tran_proc_ts
) VALUES
    ('TXN0000000000001', '01', '0001', 'POS', 'WHOLE FOODS MARKET',
     -125.50, '000000001', 'Whole Foods Market', 'Los Angeles', '90210',
     '4111111111111111',
     '2026-03-30 14:22:00+00', '2026-03-30 14:22:05+00'),
    ('TXN0000000000002', '01', '0002', 'POS', 'CHEESECAKE FACTORY',
     -89.75, '000000002', 'Cheesecake Factory', 'Los Angeles', '90210',
     '4111111111111111',
     '2026-03-31 19:45:00+00', '2026-03-31 19:45:10+00'),
    ('TXN0000000000003', '01', '0003', 'POS', 'SHELL GAS STATION',
     -55.00, '000000003', 'Shell Gas Station', 'New York', '10001',
     '4222222222222222',
     '2026-03-31 08:30:00+00', '2026-03-31 08:30:05+00'),
    ('TXN0000000000004', '07', '0001', 'WEB', 'ONLINE PAYMENT RECEIVED',
     500.00, NULL, NULL, NULL, NULL,
     '4222222222222222',
     '2026-04-01 10:00:00+00', '2026-04-01 10:00:15+00'),
    ('TXN0000000000005', '01', '0004', 'POS', 'MARRIOTT HOTEL',
     -350.00, '000000004', 'Marriott Hotel', 'Dallas', '75201',
     '4333333333333333',
     '2026-04-01 16:00:00+00', '2026-04-01 16:00:30+00'),
    ('TXN0000000000006', '02', '0002', 'POS', 'RESTAURANT REFUND',
     30.00, '000000002', 'Cheesecake Factory', 'Los Angeles', '90210',
     '4111111111111111',
     '2026-04-02 11:15:00+00', '2026-04-02 11:15:05+00'),
    ('TXN0000000000007', '01', '0008', 'WEB', 'AMAZON.COM ORDER',
     -215.99, '000000005', 'Amazon.com', 'Seattle', '98101',
     '4555555555555555',
     '2026-04-02 20:00:00+00', '2026-04-02 20:00:10+00'),
    ('TXN0000000000008', '01', '0001', 'POS', 'TRADER JOE''S',
     -75.20, '000000006', 'Trader Joes', 'Dallas', '75201',
     '4333333333333333',
     '2026-04-02 13:00:00+00', '2026-04-02 13:00:05+00')
ON CONFLICT (tran_id) DO NOTHING;

-- ============================================================
-- Transaction Category Balances (TCATBALF KSDS / CVTRA01Y)
-- Used by CBACT04C interest calculation
-- ============================================================
INSERT INTO transaction_category_balances (acct_id, tran_type_cd, tran_cat_cd, balance) VALUES
    -- Account 1: Gold group, multiple categories
    ('00000000001', '01', '0001', 500.00),   -- Groceries
    ('00000000001', '01', '0002', 350.00),   -- Restaurants
    ('00000000001', '01', '0003', 200.00),   -- Gas
    ('00000000001', '01', '0004', 450.00),   -- Travel
    -- Account 2: Silver group
    ('00000000002', '01', '0001', 1200.00),  -- Groceries
    ('00000000002', '01', '0003', 600.00),   -- Gas
    ('00000000002', '01', '0008', 3000.00),  -- Online Shopping
    -- Account 3: Bronze group
    ('00000000003', '01', '0002', 800.00),   -- Restaurants
    ('00000000003', '01', '0006', 1200.00),  -- Entertainment
    -- Account 5: Platinum group
    ('00000000005', '01', '0004', 0.00),     -- Travel (zero balance, no interest)
    ('00000000005', '01', '0007', 0.00)      -- Healthcare (zero balance)
ON CONFLICT (acct_id, tran_type_cd, tran_cat_cd) DO NOTHING;

-- ============================================================
-- Disclosure Groups / Interest Rates (DISCGRP KSDS / CVTRA02Y)
-- Used by CBACT04C
-- Interest rates stored as annual percentage (e.g., 18.00 = 18%)
-- Formula: (balance * rate) / 1200
-- ============================================================
INSERT INTO disclosure_groups (group_id, tran_type_cd, tran_cat_cd, interest_rate) VALUES
    -- GOLD group rates
    ('GOLD', '01', '0001', 18.00),   -- Groceries: 18% APR
    ('GOLD', '01', '0002', 18.00),   -- Restaurants: 18% APR
    ('GOLD', '01', '0003', 18.00),   -- Gas: 18% APR
    ('GOLD', '01', '0004', 20.00),   -- Travel: 20% APR
    ('GOLD', '01', '0008', 18.00),   -- Online: 18% APR
    -- SILVER group rates
    ('SILVER', '01', '0001', 21.99), -- Groceries: 21.99% APR
    ('SILVER', '01', '0003', 21.99), -- Gas: 21.99% APR
    ('SILVER', '01', '0008', 24.99), -- Online: 24.99% APR
    -- BRONZE group rates
    ('BRONZE', '01', '0002', 26.99), -- Restaurants: 26.99% APR
    ('BRONZE', '01', '0006', 26.99), -- Entertainment: 26.99% APR
    -- PLATINUM group rates (low rates)
    ('PLATINUM', '01', '0004', 14.99), -- Travel: 14.99% APR
    ('PLATINUM', '01', '0007', 14.99), -- Healthcare: 14.99% APR
    -- DEFAULT fallback rates (used when specific group not found)
    ('DEFAULT', '01', '0001', 24.00),
    ('DEFAULT', '01', '0002', 24.00),
    ('DEFAULT', '01', '0003', 24.00),
    ('DEFAULT', '01', '0004', 24.00),
    ('DEFAULT', '01', '0005', 0.00),
    ('DEFAULT', '01', '0006', 24.00),
    ('DEFAULT', '01', '0007', 24.00),
    ('DEFAULT', '01', '0008', 24.00),
    ('DEFAULT', '07', '0001', 0.00)
ON CONFLICT (group_id, tran_type_cd, tran_cat_cd) DO NOTHING;

-- ============================================================
-- Sample batch job records (for testing job tracking)
-- ============================================================
INSERT INTO batch_jobs (job_type, status, started_at, completed_at, records_processed, records_rejected, result_summary) VALUES
    ('transaction_posting', 'completed', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '5 minutes',
     8, 0, '{"transactions_posted": 8, "accounts_updated": 5}'),
    ('interest_calculation', 'completed', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '3 minutes',
     10, 0, '{"interest_records_created": 8, "accounts_updated": 4}')
ON CONFLICT DO NOTHING;
