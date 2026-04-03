-- CardDemo Transaction Processing Module — Seed Data
-- Provides sufficient data for functional testing of COTRN00C, COTRN01C, COTRN02C equivalents

-- ============================================================
-- Transaction Types (5 types matching TRANTYPE VSAM)
-- ============================================================
INSERT INTO transaction_types (tran_type, tran_type_desc) VALUES
    ('PU', 'Purchase'),
    ('PA', 'Payment'),
    ('CR', 'Credit Adjustment'),
    ('FE', 'Fee'),
    ('RF', 'Refund')
ON CONFLICT (tran_type) DO NOTHING;

-- ============================================================
-- Transaction Categories (10 categories across types)
-- ============================================================
INSERT INTO transaction_categories (tran_type, tran_cat_cd, tran_cat_desc) VALUES
    ('PU', '0001', 'Grocery'),
    ('PU', '0002', 'Gas / Fuel'),
    ('PU', '0003', 'Restaurant'),
    ('PU', '0004', 'Travel'),
    ('PU', '0005', 'Entertainment'),
    ('PA', '0001', 'Online Payment'),
    ('PA', '0002', 'Branch Payment'),
    ('CR', '0001', 'Billing Dispute'),
    ('FE', '0001', 'Annual Fee'),
    ('RF', '0001', 'Merchant Refund')
ON CONFLICT (tran_type, tran_cat_cd) DO NOTHING;

-- ============================================================
-- Accounts (5 accounts — mix of active/inactive)
-- ============================================================
INSERT INTO accounts (
    acct_id, acct_active_status, acct_curr_bal, acct_credit_limit,
    acct_cash_credit_limit, acct_open_date, acct_expiration_date,
    acct_addr_zip, acct_group_id
) VALUES
    ('00000000001', 'Y', 1250.75,  10000.00, 2000.00, '2020-01-15', '2025-01-15', '10001', 'PLATINUM'),
    ('00000000002', 'Y', 3400.00,  15000.00, 3000.00, '2019-06-01', '2024-06-01', '90210', 'GOLD'),
    ('00000000003', 'Y',  500.00,   5000.00, 1000.00, '2021-03-10', '2026-03-10', '60601', 'SILVER'),
    ('00000000004', 'N',    0.00,   8000.00, 1600.00, '2018-09-20', '2023-09-20', '77001', 'GOLD'),
    ('00000000005', 'Y', 9999.99,  20000.00, 4000.00, '2022-11-05', '2027-11-05', '33101', 'PLATINUM')
ON CONFLICT (acct_id) DO NOTHING;

-- ============================================================
-- Card Cross-References (one card per account)
-- ============================================================
INSERT INTO card_cross_references (xref_card_num, xref_cust_id, xref_acct_id) VALUES
    ('4111111111111111', '000000001', '00000000001'),
    ('4222222222222222', '000000002', '00000000002'),
    ('4333333333333333', '000000003', '00000000003'),
    ('4444444444444444', '000000004', '00000000004'),
    ('4555555555555555', '000000005', '00000000005')
ON CONFLICT (xref_card_num) DO NOTHING;

-- ============================================================
-- Transactions (25 records — sufficient for pagination testing)
-- IDs are zero-padded 16-digit strings matching COBOL PIC X(16)
-- ============================================================
INSERT INTO transactions (
    tran_id, tran_type_cd, tran_cat_cd, tran_source, tran_desc,
    tran_amt, tran_merchant_id, tran_merchant_name, tran_merchant_city,
    tran_merchant_zip, tran_card_num, tran_orig_ts, tran_proc_ts
) VALUES
    ('0000000000000001', 'PU', '0001', 'ONLINE    ', 'Whole Foods Market grocery run',
     -52.47, '000000001', 'Whole Foods Market',     'New York',       '10001',
     '4111111111111111', '2026-03-01 09:15:00+00', '2026-03-01 09:16:02+00'),

    ('0000000000000002', 'PU', '0002', 'POS       ', 'Shell gas station fill-up',
     -65.20, '000000002', 'Shell Gas Station',      'Los Angeles',    '90001',
     '4111111111111111', '2026-03-02 11:30:00+00', '2026-03-02 11:30:45+00'),

    ('0000000000000003', 'PU', '0003', 'POS       ', 'Olive Garden dinner for two',
     -87.35, '000000003', 'Olive Garden',            'Chicago',        '60601',
     '4222222222222222', '2026-03-03 19:00:00+00', '2026-03-03 19:01:12+00'),

    ('0000000000000004', 'PA', '0001', 'ONLINE    ', 'Online minimum payment',
     250.00, '000000004', 'CardDemo Bank',           'Houston',        '77001',
     '4222222222222222', '2026-03-04 08:00:00+00', '2026-03-04 08:00:30+00'),

    ('0000000000000005', 'PU', '0004', 'ONLINE    ', 'Delta Airlines ticket purchase',
    -432.00, '000000005', 'Delta Airlines',          'Atlanta',        '30301',
     '4333333333333333', '2026-03-05 14:22:00+00', '2026-03-05 14:23:01+00'),

    ('0000000000000006', 'PU', '0005', 'POS       ', 'AMC Theaters movie tickets',
     -38.50, '000000006', 'AMC Theaters',            'Phoenix',        '85001',
     '4333333333333333', '2026-03-06 20:00:00+00', '2026-03-06 20:01:00+00'),

    ('0000000000000007', 'CR', '0001', 'SYSTEM    ', 'Billing dispute resolution credit',
     120.00, '000000007', 'CardDemo Adjustments',    'Dallas',         '75201',
     '4111111111111111', '2026-03-07 10:00:00+00', '2026-03-07 10:05:00+00'),

    ('0000000000000008', 'PU', '0001', 'POS       ', 'Kroger weekly grocery shopping',
     -98.72, '000000008', 'Kroger Supermarket',      'San Antonio',    '78201',
     '4444444444444444', '2026-03-08 12:30:00+00', '2026-03-08 12:31:10+00'),

    ('0000000000000009', 'FE', '0001', 'SYSTEM    ', 'Annual membership fee charge',
     -99.00, '000000009', 'CardDemo Bank',           'San Diego',      '92101',
     '4555555555555555', '2026-03-09 00:01:00+00', '2026-03-09 00:01:00+00'),

    ('0000000000000010', 'PU', '0002', 'POS       ', 'Chevron gas and car wash',
     -48.15, '000000010', 'Chevron Station',         'Dallas',         '75202',
     '4555555555555555', '2026-03-10 07:45:00+00', '2026-03-10 07:46:00+00'),

    ('0000000000000011', 'PU', '0003', 'POS       ', 'Chipotle Mexican Grill lunch',
     -14.75, '000000011', 'Chipotle Mexican Grill',  'San Jose',       '95101',
     '4111111111111111', '2026-03-11 12:15:00+00', '2026-03-11 12:16:00+00'),

    ('0000000000000012', 'RF', '0001', 'ONLINE    ', 'Amazon return merchandise refund',
      45.99, '000000012', 'Amazon.com',              'Seattle',        '98101',
     '4222222222222222', '2026-03-12 15:00:00+00', '2026-03-12 15:30:00+00'),

    ('0000000000000013', 'PU', '0004', 'ONLINE    ', 'Marriott hotel weekend stay',
    -215.00, '000000013', 'Marriott Hotels',         'Austin',         '73301',
     '4333333333333333', '2026-03-13 13:00:00+00', '2026-03-13 13:01:00+00'),

    ('0000000000000014', 'PA', '0002', 'BRANCH    ', 'Branch full balance payment',
    1200.00, '000000014', 'CardDemo Bank Branch',    'Jacksonville',   '32099',
     '4333333333333333', '2026-03-14 10:30:00+00', '2026-03-14 10:35:00+00'),

    ('0000000000000015', 'PU', '0001', 'MOBILE    ', 'Trader Joes specialty groceries',
     -76.30, '000000015', 'Trader Joes',             'Fort Worth',     '76101',
     '4555555555555555', '2026-03-15 16:45:00+00', '2026-03-15 16:46:00+00'),

    ('0000000000000016', 'PU', '0005', 'ONLINE    ', 'Spotify annual subscription',
     -99.99, '000000016', 'Spotify AB',              'Columbus',       '43201',
     '4111111111111111', '2026-03-16 08:00:00+00', '2026-03-16 08:01:00+00'),

    ('0000000000000017', 'PU', '0002', 'POS       ', 'BP gas station highway fill',
     -55.40, '000000017', 'BP Gas Station',          'Charlotte',      '28201',
     '4222222222222222', '2026-03-17 06:30:00+00', '2026-03-17 06:31:00+00'),

    ('0000000000000018', 'CR', '0001', 'SYSTEM    ', 'Promotional statement credit',
      50.00, '000000018', 'CardDemo Bank',           'Indianapolis',   '46201',
     '4555555555555555', '2026-03-18 09:00:00+00', '2026-03-18 09:05:00+00'),

    ('0000000000000019', 'PU', '0003', 'POS       ', 'Starbucks coffee morning run',
     -12.50, '000000019', 'Starbucks Corporation',   'San Francisco',  '94101',
     '4333333333333333', '2026-03-19 07:00:00+00', '2026-03-19 07:01:00+00'),

    ('0000000000000020', 'PU', '0004', 'ONLINE    ', 'United Airlines booking upgrade',
    -180.00, '000000020', 'United Airlines',         'Seattle',        '98102',
     '4111111111111111', '2026-03-20 11:00:00+00', '2026-03-20 11:01:00+00'),

    ('0000000000000021', 'PU', '0001', 'POS       ', 'Target household items purchase',
     -143.22, '000000021', 'Target Corporation',     'Denver',         '80201',
     '4222222222222222', '2026-03-21 14:00:00+00', '2026-03-21 14:01:00+00'),

    ('0000000000000022', 'FE', '0001', 'SYSTEM    ', 'Late payment fee assessment',
     -39.00, '000000022', 'CardDemo Bank',           'Nashville',      '37201',
     '4444444444444444', '2026-03-22 00:01:00+00', '2026-03-22 00:01:00+00'),

    ('0000000000000023', 'RF', '0001', 'POS       ', 'Best Buy defective product return',
      89.99, '000000023', 'Best Buy Co Inc',         'Baltimore',      '21201',
     '4555555555555555', '2026-03-23 13:30:00+00', '2026-03-23 14:00:00+00'),

    ('0000000000000024', 'PU', '0005', 'ONLINE    ', 'Netflix streaming subscription',
     -22.99, '000000024', 'Netflix Inc',             'Oklahoma City',  '73101',
     '4111111111111111', '2026-03-24 00:00:00+00', '2026-03-24 00:01:00+00'),

    ('0000000000000025', 'PA', '0001', 'ONLINE    ', 'Statement balance full payment',
    3400.00, '000000025', 'CardDemo Bank Online',    'Louisville',     '40201',
     '4222222222222222', '2026-03-25 08:30:00+00', '2026-03-25 08:31:00+00')
ON CONFLICT (tran_id) DO NOTHING;

-- Update the sequence to start after the seeded data
SELECT setval('transaction_id_seq', 25, true);
