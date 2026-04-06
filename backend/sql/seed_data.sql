-- =============================================================================
-- Seed Data: Authorization Module
-- Minimum 10 rows per table as per DB spec section 6
-- authorization_summary: 10 rows; authorization_detail: 30+ rows; auth_fraud_log: 5 rows
-- =============================================================================

-- NOTE: This seed data assumes accounts table already has these account IDs.
-- In a full deployment, accounts seed data must be loaded first.
-- For standalone testing, the FK constraints to accounts must be deferred or
-- accounts rows inserted here first.

-- =============================================================================
-- authorization_summary: 10 rows
-- Maps PA-CREDIT-LIMIT, PA-CASH-LIMIT, PA-CREDIT-BALANCE, PA-CASH-BALANCE
-- PA-APPROVED-AUTH-CNT, PA-DECLINED-AUTH-CNT from IMS PAUTSUM0 segment
-- =============================================================================
INSERT INTO authorization_summary
    (account_id, credit_limit, cash_limit, credit_balance, cash_balance,
     approved_auth_count, declined_auth_count, approved_auth_amount, declined_auth_amount)
VALUES
    (10000000001, 10000.00,  2000.00,  3500.00,  500.00,  12, 2,  4200.00,   350.00),
    (10000000002, 15000.00,  3000.00,  8000.00,  1200.00, 25, 5,  9500.00,   800.00),
    (10000000003, 5000.00,   1000.00,  1200.00,  200.00,  8,  1,  1500.00,   100.00),
    (10000000004, 20000.00,  5000.00,  12000.00, 2000.00, 45, 8,  15000.00,  1200.00),
    (10000000005, 8000.00,   1500.00,  4500.00,  600.00,  18, 3,  5200.00,   450.00),
    (10000000006, 25000.00,  6000.00,  18000.00, 3000.00, 60, 10, 22000.00,  2500.00),
    (10000000007, 3000.00,   500.00,   800.00,   100.00,  5,  0,  900.00,    0.00),
    (10000000008, 12000.00,  2500.00,  6500.00,  800.00,  30, 6,  7800.00,   650.00),
    (10000000009, 7500.00,   1000.00,  2500.00,  300.00,  15, 4,  3200.00,   400.00),
    (10000000010, 18000.00,  4000.00,  10000.00, 1500.00, 40, 7,  12000.00,  1100.00)
ON CONFLICT (account_id) DO NOTHING;

-- =============================================================================
-- authorization_detail: 30 rows across accounts
-- Maps PAUTDTL1 segment (CIPAUDTY copybook)
-- auth_response_code '00'=approved, else declined
-- match_status: P=Pending, D=Declined, E=Expired, M=Matched
-- fraud_status: N=none, F=fraud confirmed, R=fraud removed
-- =============================================================================
INSERT INTO authorization_detail
    (account_id, transaction_id, card_number, auth_date, auth_time,
     auth_response_code, auth_code, transaction_amount, pos_entry_mode,
     auth_source, mcc_code, card_expiry_date, auth_type, match_status,
     fraud_status, merchant_name, merchant_id, merchant_city, merchant_state,
     merchant_zip, processed_at)
VALUES
    -- Account 10000000001 — 4 records
    (10000000001, 'TXN0000000000001', '4111111111111001', '2026-03-01', '10:25:33',
     '00', 'AUTH01', 125.50, '0101', 'POS', '5411', '03/28', 'PURCHASE',
     'P', 'N', 'WHOLE FOODS MARKET', 'M000000001', 'SEATTLE',
     'WA', '98101', '2026-03-01 10:25:33-07'),
    (10000000001, 'TXN0000000000002', '4111111111111001', '2026-03-05', '14:12:00',
     '00', 'AUTH02', 89.99, '0201', 'POS', '5912', '03/28', 'PURCHASE',
     'M', 'N', 'CVS PHARMACY', 'M000000002', 'SEATTLE',
     'WA', '98102', '2026-03-05 14:12:00-07'),
    (10000000001, 'TXN0000000000003', '4111111111111001', '2026-03-10', '09:45:22',
     '4100', NULL, 250.00, '0101', 'POS', '5411', '03/28', 'PURCHASE',
     'D', 'N', 'WHOLE FOODS MARKET', 'M000000001', 'SEATTLE',
     'WA', '98101', '2026-03-10 09:45:22-07'),
    (10000000001, 'TXN0000000000004', '4111111111111001', '2026-03-15', '16:33:10',
     '00', 'AUTH03', 450.00, '0101', 'POS', '5812', '03/28', 'PURCHASE',
     'P', 'F', 'RESTAURANT XYZ', 'M000000003', 'SEATTLE',
     'WA', '98103', '2026-03-15 16:33:10-07'),

    -- Account 10000000002 — 5 records
    (10000000002, 'TXN0000000000005', '4111111111111002', '2026-03-02', '11:00:00',
     '00', 'AUTH04', 320.00, '0101', 'POS', '5734', '06/27', 'PURCHASE',
     'P', 'N', 'BEST BUY', 'M000000004', 'PORTLAND',
     'OR', '97201', '2026-03-02 11:00:00-07'),
    (10000000002, 'TXN0000000000006', '4111111111111002', '2026-03-08', '13:22:45',
     '00', 'AUTH05', 75.00, '0201', 'POS', '5411', '06/27', 'PURCHASE',
     'M', 'N', 'SAFEWAY', 'M000000005', 'PORTLAND',
     'OR', '97202', '2026-03-08 13:22:45-07'),
    (10000000002, 'TXN0000000000007', '4111111111111002', '2026-03-12', '08:15:30',
     '4200', NULL, 100.00, '0101', 'POS', '5812', '06/27', 'PURCHASE',
     'D', 'N', 'MCDONALDS', 'M000000006', 'PORTLAND',
     'OR', '97203', '2026-03-12 08:15:30-07'),
    (10000000002, 'TXN0000000000008', '4111111111111002', '2026-03-18', '19:40:12',
     '00', 'AUTH06', 1500.00, '0101', 'POS', '5047', '06/27', 'PURCHASE',
     'P', 'R', 'MEDICAL SUPPLIES INC', 'M000000007', 'PORTLAND',
     'OR', '97204', '2026-03-18 19:40:12-07'),
    (10000000002, 'TXN0000000000009', '4111111111111002', '2026-03-22', '12:05:00',
     '00', 'AUTH07', 45.99, '0201', 'POS', '5912', '06/27', 'PURCHASE',
     'M', 'N', 'WALGREENS', 'M000000008', 'PORTLAND',
     'OR', '97205', '2026-03-22 12:05:00-07'),

    -- Account 10000000003 — 3 records
    (10000000003, 'TXN0000000000010', '4111111111111003', '2026-03-03', '15:30:00',
     '00', 'AUTH08', 55.20, '0101', 'POS', '5411', '09/26', 'PURCHASE',
     'P', 'N', 'KROGER', 'M000000009', 'DENVER',
     'CO', '80201', '2026-03-03 15:30:00-07'),
    (10000000003, 'TXN0000000000011', '4111111111111003', '2026-03-14', '10:10:10',
     '00', 'AUTH09', 200.00, '0101', 'POS', '5999', '09/26', 'PURCHASE',
     'M', 'N', 'TARGET', 'M000000010', 'DENVER',
     'CO', '80202', '2026-03-14 10:10:10-07'),
    (10000000003, 'TXN0000000000012', '4111111111111003', '2026-03-20', '17:55:00',
     '5100', NULL, 99.00, '0101', 'POS', '5812', '09/26', 'PURCHASE',
     'D', 'N', 'OUTBACK STEAKHOUSE', 'M000000011', 'DENVER',
     'CO', '80203', '2026-03-20 17:55:00-07'),

    -- Account 10000000004 — 5 records
    (10000000004, 'TXN0000000000013', '4111111111111004', '2026-02-28', '09:00:00',
     '00', 'AUTH10', 3500.00, '0101', 'POS', '5065', '12/28', 'PURCHASE',
     'M', 'N', 'ELECTRONICS DEPOT', 'M000000012', 'CHICAGO',
     'IL', '60601', '2026-02-28 09:00:00-06'),
    (10000000004, 'TXN0000000000014', '4111111111111004', '2026-03-04', '14:30:22',
     '00', 'AUTH11', 180.00, '0201', 'POS', '5411', '12/28', 'PURCHASE',
     'P', 'N', 'WHOLE FOODS MARKET', 'M000000001', 'CHICAGO',
     'IL', '60602', '2026-03-04 14:30:22-06'),
    (10000000004, 'TXN0000000000015', '4111111111111004', '2026-03-09', '11:45:00',
     '4400', NULL, 5000.00, '0101', 'POS', '5912', '12/28', 'PURCHASE',
     'D', 'N', 'LUXURY GOODS CO', 'M000000013', 'CHICAGO',
     'IL', '60603', '2026-03-09 11:45:00-06'),
    (10000000004, 'TXN0000000000016', '4111111111111004', '2026-03-16', '16:20:00',
     '00', 'AUTH12', 250.00, '0101', 'POS', '5812', '12/28', 'PURCHASE',
     'P', 'N', 'GIBSONS BAR', 'M000000014', 'CHICAGO',
     'IL', '60604', '2026-03-16 16:20:00-06'),
    (10000000004, 'TXN0000000000017', '4111111111111004', '2026-03-23', '08:45:30',
     '00', 'AUTH13', 125.75, '0201', 'POS', '5411', '12/28', 'PURCHASE',
     'M', 'N', 'JEWEL OSCO', 'M000000015', 'CHICAGO',
     'IL', '60605', '2026-03-23 08:45:30-06'),

    -- Account 10000000005 — 3 records
    (10000000005, 'TXN0000000000018', '4111111111111005', '2026-03-06', '12:00:00',
     '00', 'AUTH14', 89.50, '0101', 'POS', '5411', '01/27', 'PURCHASE',
     'P', 'N', 'PUBLIX', 'M000000016', 'MIAMI',
     'FL', '33101', '2026-03-06 12:00:00-05'),
    (10000000005, 'TXN0000000000019', '4111111111111005', '2026-03-13', '15:15:15',
     '00', 'AUTH15', 299.99, '0101', 'POS', '5945', '01/27', 'PURCHASE',
     'M', 'F', 'TOYS R US', 'M000000017', 'MIAMI',
     'FL', '33102', '2026-03-13 15:15:15-05'),
    (10000000005, 'TXN0000000000020', '4111111111111005', '2026-03-19', '10:30:00',
     '3100', NULL, 150.00, '0101', 'POS', '5912', '01/27', 'PURCHASE',
     'D', 'N', 'CVS PHARMACY', 'M000000002', 'MIAMI',
     'FL', '33103', '2026-03-19 10:30:00-05'),

    -- Account 10000000006 — 4 records
    (10000000006, 'TXN0000000000021', '4111111111111006', '2026-03-01', '09:30:00',
     '00', 'AUTH16', 8500.00, '0101', 'POS', '5944', '04/29', 'PURCHASE',
     'P', 'N', 'TIFFANY AND CO', 'M000000018', 'NEW YORK',
     'NY', '10001', '2026-03-01 09:30:00-05'),
    (10000000006, 'TXN0000000000022', '4111111111111006', '2026-03-07', '14:00:00',
     '00', 'AUTH17', 1200.00, '0201', 'POS', '5812', '04/29', 'PURCHASE',
     'M', 'N', 'DANIEL NYC', 'M000000019', 'NEW YORK',
     'NY', '10002', '2026-03-07 14:00:00-05'),
    (10000000006, 'TXN0000000000023', '4111111111111006', '2026-03-17', '19:00:00',
     '00', 'AUTH18', 450.00, '0101', 'POS', '5812', '04/29', 'PURCHASE',
     'P', 'N', 'ELEVEN MADISON', 'M000000020', 'NEW YORK',
     'NY', '10003', '2026-03-17 19:00:00-05'),
    (10000000006, 'TXN0000000000024', '4111111111111006', '2026-03-24', '11:20:00',
     '4300', NULL, 300.00, '0101', 'POS', '5999', '04/29', 'PURCHASE',
     'D', 'N', 'SAKS FIFTH AVE', 'M000000021', 'NEW YORK',
     'NY', '10004', '2026-03-24 11:20:00-05'),

    -- Account 10000000007 — 2 records
    (10000000007, 'TXN0000000000025', '4111111111111007', '2026-03-11', '13:45:00',
     '00', 'AUTH19', 45.00, '0101', 'POS', '5411', '08/26', 'PURCHASE',
     'P', 'N', 'ALDI', 'M000000022', 'AUSTIN',
     'TX', '78701', '2026-03-11 13:45:00-06'),
    (10000000007, 'TXN0000000000026', '4111111111111007', '2026-03-21', '16:30:00',
     '00', 'AUTH20', 120.00, '0201', 'POS', '5812', '08/26', 'PURCHASE',
     'M', 'N', 'TORCHYS TACOS', 'M000000023', 'AUSTIN',
     'TX', '78702', '2026-03-21 16:30:00-06'),

    -- Account 10000000008 — 3 records
    (10000000008, 'TXN0000000000027', '4111111111111008', '2026-03-04', '10:00:00',
     '00', 'AUTH21', 750.00, '0101', 'POS', '5065', '11/27', 'PURCHASE',
     'M', 'N', 'HOME DEPOT', 'M000000024', 'PHOENIX',
     'AZ', '85001', '2026-03-04 10:00:00-07'),
    (10000000008, 'TXN0000000000028', '4111111111111008', '2026-03-15', '14:50:00',
     '5200', NULL, 200.00, '0101', 'POS', '5912', '11/27', 'PURCHASE',
     'D', 'N', 'SUSPICIOUS VENDOR', 'M000000025', 'PHOENIX',
     'AZ', '85002', '2026-03-15 14:50:00-07'),
    (10000000008, 'TXN0000000000029', '4111111111111008', '2026-03-25', '09:15:00',
     '00', 'AUTH22', 380.00, '0201', 'POS', '5411', '11/27', 'PURCHASE',
     'P', 'N', 'FRY\'S FOOD', 'M000000026', 'PHOENIX',
     'AZ', '85003', '2026-03-25 09:15:00-07'),

    -- Account 10000000009 — 2 records
    (10000000009, 'TXN0000000000030', '4111111111111009', '2026-03-08', '11:30:00',
     '00', 'AUTH23', 95.00, '0101', 'POS', '5411', '05/28', 'PURCHASE',
     'P', 'N', 'MEIJER', 'M000000027', 'DETROIT',
     'MI', '48201', '2026-03-08 11:30:00-05'),
    (10000000009, 'TXN0000000000031', '4111111111111009', '2026-03-18', '13:00:00',
     '00', 'AUTH24', 1800.00, '0101', 'POS', '5047', '05/28', 'PURCHASE',
     'M', 'N', 'HENRY FORD HEALTH', 'M000000028', 'DETROIT',
     'MI', '48202', '2026-03-18 13:00:00-05')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- auth_fraud_log: 5 rows
-- Corresponds to authorizations that have been flagged (fraud_status != 'N')
-- auth_id values correspond to the auth_detail rows inserted above with fraud flags
-- Note: auth_ids are BIGSERIAL so may not match exactly — use subquery in real migration
-- =============================================================================
-- These will be inserted after the detail rows are created; using transaction IDs as reference
INSERT INTO auth_fraud_log
    (auth_id, transaction_id, card_number, account_id, fraud_flag,
     fraud_report_date, auth_response_code, auth_amount, merchant_name, merchant_id)
SELECT
    ad.auth_id,
    ad.transaction_id,
    ad.card_number,
    ad.account_id,
    'F',
    NOW() - INTERVAL '10 days',
    ad.auth_response_code,
    ad.transaction_amount,
    LEFT(ad.merchant_name, 22),
    LEFT(COALESCE(ad.merchant_id, ''), 9)
FROM authorization_detail ad
WHERE ad.transaction_id = 'TXN0000000000004'  -- fraud confirmed
ON CONFLICT DO NOTHING;

INSERT INTO auth_fraud_log
    (auth_id, transaction_id, card_number, account_id, fraud_flag,
     fraud_report_date, auth_response_code, auth_amount, merchant_name, merchant_id)
SELECT
    ad.auth_id,
    ad.transaction_id,
    ad.card_number,
    ad.account_id,
    'F',
    NOW() - INTERVAL '7 days',
    ad.auth_response_code,
    ad.transaction_amount,
    LEFT(ad.merchant_name, 22),
    LEFT(COALESCE(ad.merchant_id, ''), 9)
FROM authorization_detail ad
WHERE ad.transaction_id = 'TXN0000000000019'  -- fraud confirmed
ON CONFLICT DO NOTHING;

INSERT INTO auth_fraud_log
    (auth_id, transaction_id, card_number, account_id, fraud_flag,
     fraud_report_date, auth_response_code, auth_amount, merchant_name, merchant_id)
SELECT
    ad.auth_id,
    ad.transaction_id,
    ad.card_number,
    ad.account_id,
    'F',
    NOW() - INTERVAL '12 days',
    ad.auth_response_code,
    ad.transaction_amount,
    LEFT(ad.merchant_name, 22),
    LEFT(COALESCE(ad.merchant_id, ''), 9)
FROM authorization_detail ad
WHERE ad.transaction_id = 'TXN0000000000008'  -- was fraud, now removed
ON CONFLICT DO NOTHING;

-- Log the removal action for TXN0000000000008
INSERT INTO auth_fraud_log
    (auth_id, transaction_id, card_number, account_id, fraud_flag,
     fraud_report_date, auth_response_code, auth_amount, merchant_name, merchant_id)
SELECT
    ad.auth_id,
    ad.transaction_id,
    ad.card_number,
    ad.account_id,
    'R',
    NOW() - INTERVAL '5 days',
    ad.auth_response_code,
    ad.transaction_amount,
    LEFT(ad.merchant_name, 22),
    LEFT(COALESCE(ad.merchant_id, ''), 9)
FROM authorization_detail ad
WHERE ad.transaction_id = 'TXN0000000000008'
ON CONFLICT DO NOTHING;

-- Additional fraud log entry
INSERT INTO auth_fraud_log
    (auth_id, transaction_id, card_number, account_id, fraud_flag,
     fraud_report_date, auth_response_code, auth_amount, merchant_name, merchant_id)
SELECT
    ad.auth_id,
    ad.transaction_id,
    ad.card_number,
    ad.account_id,
    'F',
    NOW() - INTERVAL '3 days',
    ad.auth_response_code,
    ad.transaction_amount,
    LEFT(ad.merchant_name, 22),
    LEFT(COALESCE(ad.merchant_id, ''), 9)
FROM authorization_detail ad
WHERE ad.transaction_id = 'TXN0000000000021'
ON CONFLICT DO NOTHING;
