-- ============================================================================
-- CardDemo FastAPI Migration - Seed Data Script
-- Realistic dummy data for development and testing
-- ============================================================================

BEGIN;

-- ============================================================================
-- Customers (5 records)
-- ============================================================================
INSERT INTO customers (
    cust_id, cust_first_name, cust_middle_name, cust_last_name,
    cust_addr_line_1, cust_addr_line_2, cust_addr_line_3,
    cust_addr_state_cd, cust_addr_country_cd, cust_addr_zip,
    cust_phone_num_1, cust_phone_num_2,
    cust_ssn, cust_govt_issued_id, cust_dob_yyyymmdd,
    cust_eft_account_id, cust_pri_card_holder_ind, cust_fico_credit_score
) VALUES
(1, 'Margaret',  'A', 'Thompson',
 '1247 Oak Ridge Drive', 'Apt 3B', NULL,
 'VA', 'USA', '22101',
 '703-555-0142', '703-555-0198',
 123456789, 'DL-VA-90412756', '1978-05-14',
 'EFT000101', 'Y', 742),

(2, 'Robert',    'J', 'Chen',
 '8830 Maple Avenue', NULL, NULL,
 'CA', 'USA', '94102',
 '415-555-0237', NULL,
 234567890, 'DL-CA-B1234567', '1985-11-22',
 'EFT000202', 'Y', 680),

(3, 'Patricia',  'M', 'Williams',
 '562 Elm Street', 'Suite 100', NULL,
 'TX', 'USA', '75201',
 '214-555-0319', '214-555-0320',
 345678901, 'DL-TX-12345678', '1990-03-08',
 'EFT000303', 'Y', 795),

(4, 'James',     NULL, 'Rodriguez',
 '4401 Pine Boulevard', NULL, NULL,
 'FL', 'USA', '33101',
 '305-555-0456', NULL,
 456789012, 'DL-FL-R567890123', '1972-09-30',
 'EFT000404', 'Y', 620),

(5, 'Linda',     'K', 'Nakamura',
 '2100 Cedar Lane', 'Unit 7', NULL,
 'WA', 'USA', '98101',
 '206-555-0587', '206-555-0588',
 567890123, 'DL-WA-NAKAM5678', '1995-01-17',
 'EFT000505', 'Y', 710);

-- ============================================================================
-- Accounts (5 records - one per customer)
-- ============================================================================
INSERT INTO accounts (
    acct_id, acct_active_status, acct_curr_bal, acct_credit_limit,
    acct_cash_credit_limit, acct_open_date, acct_expiration_date,
    acct_reissue_date, acct_curr_cyc_credit, acct_curr_cyc_debit,
    acct_addr_zip, acct_group_id
) VALUES
(80010001001, 'Y', 1247.53, 10000.00,
 2000.00, '2020-03-15', '2027-03-15',
 NULL, 500.00, 1747.53,
 '22101', 'GROUP001'),

(80020002002, 'Y', 3589.22, 15000.00,
 3000.00, '2019-07-01', '2026-07-01',
 '2023-07-01', 1200.00, 4789.22,
 '94102', 'GROUP001'),

(80030003003, 'Y', 127.45, 25000.00,
 5000.00, '2021-01-10', '2028-01-10',
 NULL, 8000.00, 8127.45,
 '75201', 'GROUP002'),

(80040004004, 'N', 4950.00, 5000.00,
 1000.00, '2018-11-20', '2024-11-20',
 NULL, 0.00, 50.00,
 '33101', 'GROUP001'),

(80050005005, 'Y', 832.17, 12000.00,
 2500.00, '2022-06-05', '2029-06-05',
 NULL, 3200.00, 4032.17,
 '98101', 'GROUP002');

-- ============================================================================
-- Cards (8 records - some accounts have 2 cards)
-- ============================================================================
INSERT INTO cards (
    card_num, card_acct_id, card_cvv_cd, card_embossed_name,
    card_expiration_date, card_active_status
) VALUES
('4111111111111111', 80010001001, 123, 'MARGARET A THOMPSON',
 '2027-03-15', 'Y'),

('4111111111112222', 80010001001, 456, 'MARGARET A THOMPSON',
 '2027-03-15', 'Y'),

('4222222222223333', 80020002002, 789, 'ROBERT J CHEN',
 '2026-07-01', 'Y'),

('4333333333334444', 80030003003, 321, 'PATRICIA M WILLIAMS',
 '2028-01-10', 'Y'),

('4333333333335555', 80030003003, 654, 'PATRICIA M WILLIAMS',
 '2028-01-10', 'N'),

('4444444444446666', 80040004004, 987, 'JAMES RODRIGUEZ',
 '2024-11-20', 'N'),

('4555555555557777', 80050005005, 147, 'LINDA K NAKAMURA',
 '2029-06-05', 'Y'),

('4555555555558888', 80050005005, 258, 'LINDA K NAKAMURA',
 '2029-06-05', 'Y');

-- ============================================================================
-- Card Cross-Reference (8 records matching all cards)
-- ============================================================================
INSERT INTO card_xref (xref_card_num, xref_cust_id, xref_acct_id)
VALUES
('4111111111111111', 1, 80010001001),
('4111111111112222', 1, 80010001001),
('4222222222223333', 2, 80020002002),
('4333333333334444', 3, 80030003003),
('4333333333335555', 3, 80030003003),
('4444444444446666', 4, 80040004004),
('4555555555557777', 5, 80050005005),
('4555555555558888', 5, 80050005005);

-- ============================================================================
-- Transaction Types (5 records)
-- ============================================================================
INSERT INTO transaction_types (tran_type, tran_type_desc)
VALUES
('01', 'Purchase'),
('02', 'Payment'),
('03', 'Cash Advance'),
('04', 'Balance Transfer'),
('05', 'Fee');

-- ============================================================================
-- Transaction Categories (10 records)
-- ============================================================================
INSERT INTO transaction_categories (tran_type_cd, tran_cat_cd, tran_cat_type_desc)
VALUES
('01', 5001, 'Retail Purchase'),
('01', 5002, 'Online Purchase'),
('01', 5003, 'Restaurant/Dining'),
('01', 5004, 'Grocery'),
('01', 5005, 'Travel'),
('02', 6001, 'Monthly Payment'),
('02', 6002, 'One-Time Payment'),
('03', 7001, 'ATM Cash Advance'),
('04', 8001, 'Account Balance Transfer'),
('05', 9001, 'Annual Fee');

-- ============================================================================
-- Transactions (20 records)
-- ============================================================================
INSERT INTO transactions (
    tran_id, tran_type_cd, tran_cat_cd, tran_source, tran_desc,
    tran_amt, tran_merchant_id, tran_merchant_name, tran_merchant_city,
    tran_merchant_zip, tran_card_num, tran_orig_ts, tran_proc_ts
) VALUES
('TRN0000000000001', '01', 5001, 'POS',
 'Electronics purchase at Best Buy',
 249.99, 10001, 'Best Buy #1247', 'Arlington',
 '22201', '4111111111111111',
 '2025-01-15 10:23:45.123456', '2025-01-15 10:23:47.654321'),

('TRN0000000000002', '01', 5003, 'POS',
 'Dinner at Olive Garden',
 67.42, 10002, 'Olive Garden #892', 'McLean',
 '22102', '4111111111111111',
 '2025-01-18 19:15:30.000000', '2025-01-18 19:15:32.000000'),

('TRN0000000000003', '02', 6001, 'ONLINE',
 'Monthly payment - auto pay',
 500.00, NULL, NULL, NULL,
 NULL, '4111111111111111',
 '2025-02-01 00:00:01.000000', '2025-02-01 00:00:03.000000'),

('TRN0000000000004', '01', 5002, 'ONLINE',
 'Amazon.com order #112-7654321',
 134.87, 20001, 'Amazon.com', 'Seattle',
 '98101', '4222222222223333',
 '2025-01-20 14:30:00.000000', '2025-01-20 14:30:02.000000'),

('TRN0000000000005', '01', 5004, 'POS',
 'Grocery shopping at Safeway',
 89.23, 30001, 'Safeway #4521', 'San Francisco',
 '94102', '4222222222223333',
 '2025-01-22 11:45:12.000000', '2025-01-22 11:45:14.000000'),

('TRN0000000000006', '01', 5005, 'POS',
 'United Airlines ticket purchase',
 487.00, 40001, 'United Airlines', 'Chicago',
 '60601', '4222222222223333',
 '2025-01-25 08:00:00.000000', '2025-01-25 08:00:05.000000'),

('TRN0000000000007', '02', 6002, 'ONLINE',
 'One-time payment via web portal',
 1200.00, NULL, NULL, NULL,
 NULL, '4222222222223333',
 '2025-02-05 16:20:00.000000', '2025-02-05 16:20:01.000000'),

('TRN0000000000008', '01', 5001, 'POS',
 'Apple Store purchase - MacBook',
 1299.00, 50001, 'Apple Store #312', 'Dallas',
 '75201', '4333333333334444',
 '2025-01-10 13:00:00.000000', '2025-01-10 13:00:03.000000'),

('TRN0000000000009', '01', 5002, 'ONLINE',
 'Target.com household items',
 56.78, 50002, 'Target.com', 'Minneapolis',
 '55403', '4333333333334444',
 '2025-01-12 09:30:00.000000', '2025-01-12 09:30:02.000000'),

('TRN0000000000010', '01', 5003, 'POS',
 'The Cheesecake Factory dinner',
 112.50, 50003, 'Cheesecake Factory #67', 'Plano',
 '75024', '4333333333334444',
 '2025-01-28 20:00:00.000000', '2025-01-28 20:00:02.000000'),

('TRN0000000000011', '02', 6001, 'ONLINE',
 'Monthly payment - auto pay',
 8000.00, NULL, NULL, NULL,
 NULL, '4333333333334444',
 '2025-02-01 00:00:01.000000', '2025-02-01 00:00:03.000000'),

('TRN0000000000012', '03', 7001, 'ATM',
 'Cash advance at Chase ATM',
 200.00, 60001, 'Chase ATM #8817', 'Miami',
 '33101', '4444444444446666',
 '2025-01-05 15:45:00.000000', '2025-01-05 15:45:05.000000'),

('TRN0000000000013', '05', 9001, 'SYSTEM',
 'Annual membership fee',
 95.00, NULL, NULL, NULL,
 NULL, '4444444444446666',
 '2025-01-01 00:00:00.000000', '2025-01-01 00:00:01.000000'),

('TRN0000000000014', '01', 5001, 'POS',
 'Nordstrom clothing purchase',
 215.30, 70001, 'Nordstrom #145', 'Seattle',
 '98101', '4555555555557777',
 '2025-01-14 12:10:00.000000', '2025-01-14 12:10:02.000000'),

('TRN0000000000015', '01', 5004, 'POS',
 'Whole Foods Market groceries',
 147.62, 70002, 'Whole Foods #201', 'Seattle',
 '98101', '4555555555557777',
 '2025-01-16 17:30:00.000000', '2025-01-16 17:30:02.000000'),

('TRN0000000000016', '01', 5005, 'ONLINE',
 'Marriott hotel reservation',
 342.00, 70003, 'Marriott Hotels', 'Portland',
 '97201', '4555555555558888',
 '2025-01-19 09:00:00.000000', '2025-01-19 09:00:04.000000'),

('TRN0000000000017', '02', 6002, 'ONLINE',
 'One-time extra payment',
 3200.00, NULL, NULL, NULL,
 NULL, '4555555555557777',
 '2025-02-10 10:00:00.000000', '2025-02-10 10:00:01.000000'),

('TRN0000000000018', '04', 8001, 'ONLINE',
 'Balance transfer from external card',
 2500.00, NULL, NULL, NULL,
 NULL, '4111111111112222',
 '2025-01-30 08:15:00.000000', '2025-01-30 08:15:10.000000'),

('TRN0000000000019', '01', 5002, 'ONLINE',
 'Wayfair furniture order',
 399.99, 80001, 'Wayfair.com', 'Boston',
 '02116', '4111111111112222',
 '2025-02-03 14:22:00.000000', '2025-02-03 14:22:03.000000'),

('TRN0000000000020', '01', 5001, 'POS',
 'Home Depot building supplies',
 78.45, 80002, 'Home Depot #3340', 'Reston',
 '20190', '4111111111111111',
 '2025-02-08 11:05:00.000000', '2025-02-08 11:05:02.000000');

-- ============================================================================
-- Users (3 records)
-- ============================================================================
INSERT INTO users (usr_id, usr_fname, usr_lname, usr_pwd, usr_type)
VALUES
('ADMIN123',  'System',  'Admin',    'ADMIN123', 'A'),
('USER001', 'Emily',   'Carter',   'USER0001', 'U'),
('USER002', 'David',   'Park',     'USER0002', 'U');

-- ============================================================================
-- Transaction Category Balances (3 records)
-- ============================================================================
INSERT INTO tran_cat_balance (trancat_acct_id, trancat_type_cd, trancat_cd, tran_cat_bal)
VALUES
(80010001001, '01', 5001, 578.43),
(80020002002, '01', 5002, 134.87),
(80030003003, '01', 5001, 1299.00);

-- ============================================================================
-- Disclosure Groups (2 records)
-- ============================================================================
INSERT INTO disclosure_groups (dis_acct_group_id, dis_tran_type_cd, dis_tran_cat_cd, dis_int_rate)
VALUES
('GROUP001', '01', 5001, 19.99),
('GROUP002', '03', 7001, 24.99);

-- ============================================================================
-- Pending Auth Summary (3 records)
-- ============================================================================
INSERT INTO pending_auth_summary (
    pa_acct_id, pa_cust_id, pa_auth_status,
    pa_account_status_1, pa_account_status_2, pa_account_status_3,
    pa_account_status_4, pa_account_status_5,
    pa_credit_limit, pa_cash_limit, pa_credit_balance, pa_cash_balance,
    pa_approved_auth_cnt, pa_declined_auth_cnt,
    pa_approved_auth_amt, pa_declined_auth_amt
) VALUES
(80010001001, 1, 'A',
 'OK', 'OK', 'OK', 'OK', 'OK',
 10000.00, 2000.00, 1247.53, 0.00,
 12, 0, 3450.00, 0.00),

(80020002002, 2, 'A',
 'OK', 'OK', 'RV', NULL, NULL,
 15000.00, 3000.00, 3589.22, 0.00,
 8, 1, 2100.00, 500.00),

(80050005005, 5, 'A',
 'OK', 'OK', 'OK', 'OK', NULL,
 12000.00, 2500.00, 832.17, 0.00,
 5, 0, 1050.00, 0.00);

-- ============================================================================
-- Pending Auth Details (5 records)
-- ============================================================================
INSERT INTO pending_auth_details (
    pa_acct_id, pa_auth_date, pa_auth_time, pa_card_num,
    pa_auth_type, pa_card_expiry_date, pa_message_type, pa_message_source,
    pa_auth_id_code, pa_auth_resp_code, pa_auth_resp_reason,
    pa_processing_code, pa_transaction_amt, pa_approved_amt,
    pa_merchant_category_code, pa_acqr_country_code, pa_pos_entry_mode,
    pa_merchant_id, pa_merchant_name, pa_merchant_city,
    pa_merchant_state, pa_merchant_zip, pa_transaction_id,
    pa_match_status, pa_auth_fraud, pa_fraud_rpt_date
) VALUES
(80010001001, '250215', '102345', '4111111111111111',
 'SALE', '2703', '0100  ', 'POS   ',
 'AUTH01', 'AP', 'APPR',
 0, 249.99, 249.99,
 '5411', 'USA', 51,
 'MERCH0000001001', 'Best Buy #1247        ', 'Arlington    ',
 'VA', '222010000', 'TXN000000000001',
 'M', 'N', NULL),

(80010001001, '250218', '191530', '4111111111111111',
 'SALE', '2703', '0100  ', 'POS   ',
 'AUTH02', 'AP', 'APPR',
 0, 67.42, 67.42,
 '5812', 'USA', 51,
 'MERCH0000001002', 'Olive Garden #892     ', 'McLean       ',
 'VA', '221020000', 'TXN000000000002',
 'M', 'N', NULL),

(80020002002, '250120', '143000', '4222222222223333',
 'SALE', '2607', '0100  ', 'ONLINE',
 'AUTH03', 'AP', 'APPR',
 0, 134.87, 134.87,
 '5942', 'USA', 81,
 'MERCH0000002001', 'Amazon.com            ', 'Seattle      ',
 'WA', '981010000', 'TXN000000000003',
 'M', 'N', NULL),

(80020002002, '250125', '080000', '4222222222223333',
 'SALE', '2607', '0100  ', 'POS   ',
 'AUTH04', 'DC', 'INSF',
 0, 9500.00, 0.00,
 '4511', 'USA', 51,
 'MERCH0000004001', 'United Airlines       ', 'Chicago      ',
 'IL', '606010000', 'TXN000000000004',
 'N', 'N', NULL),

(80050005005, '250214', '121000', '4555555555557777',
 'SALE', '2906', '0100  ', 'POS   ',
 'AUTH05', 'AP', 'APPR',
 0, 215.30, 215.30,
 '5651', 'USA', 51,
 'MERCH0000007001', 'Nordstrom #145        ', 'Seattle      ',
 'WA', '981010000', 'TXN000000000005',
 'M', 'N', NULL);

-- ============================================================================
-- Auth Fraud (2 records)
-- ============================================================================
INSERT INTO auth_fraud (
    card_num, auth_ts, auth_type, card_expiry_date,
    message_type, message_source, auth_id_code, auth_resp_code,
    auth_resp_reason, processing_code, transaction_amt, approved_amt,
    merchant_category_code, acqr_country_code, pos_entry_mode,
    merchant_id, merchant_name, merchant_city, merchant_state,
    merchant_zip, transaction_id, match_status, auth_fraud,
    fraud_rpt_date, acct_id, cust_id
) VALUES
('4444444444446666', '2025-01-05 15:45:00',
 'CASH', '2411', '0100  ', 'ATM   ', 'FRD001', 'AP',
 'APPR', '010000', 200.00, 200.00,
 '6011', 'USA', 51,
 'MERCH0000006001', 'Chase ATM #8817       ', 'Miami        ', 'FL',
 '331010000', 'TXN000000000012',
 'M', 'Y', '2025-01-06',
 80040004004, 4),

('4444444444446666', '2025-01-06 02:30:00',
 'SALE', '2411', '0100  ', 'POS   ', 'FRD002', 'DC',
 'SUSP', '000000', 4750.00, 0.00,
 '5944', 'BRA', 90,
 'MERCH9999999999', 'Unknown Merchant      ', 'Sao Paulo    ', 'SP',
 '01310100 ', 'TXN000000000099',
 'N', 'Y', '2025-01-06',
 80040004004, 4);

COMMIT;
