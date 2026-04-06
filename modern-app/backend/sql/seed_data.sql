-- Seed Data for Authorization Module
-- Sample authorization records aligned with CardDemo seed accounts

-- Clear existing data (safe for development)
TRUNCATE TABLE fraud_records CASCADE;
TRUNCATE TABLE authorization_details CASCADE;
TRUNCATE TABLE authorization_summaries CASCADE;

-- Reset sequences
ALTER SEQUENCE authorization_summaries_id_seq RESTART WITH 1;
ALTER SEQUENCE authorization_details_id_seq RESTART WITH 1;
ALTER SEQUENCE fraud_records_id_seq RESTART WITH 1;

-- ============================================================
-- Authorization Summaries (5 accounts)
-- Account IDs match CardDemo ACCTDATA seed records
-- ============================================================

INSERT INTO authorization_summaries
    (account_id, customer_id, auth_status, credit_limit, cash_limit,
     credit_balance, cash_balance, approved_count, declined_count,
     approved_amount, declined_amount)
VALUES
    ('00000000001', '000000001', 'A', 50000.00,  5000.00,  12345.67, 1500.00, 8, 2,  18750.00,  3200.00),
    ('00000000002', '000000002', 'A', 25000.00,  2500.00,   8900.50,  900.25, 5, 1,  12000.00,  1500.00),
    ('00000000003', '000000003', 'A', 75000.00,  7500.00,  45678.90, 3200.00, 12, 3, 55000.00,  8900.00),
    ('00000000004', '000000004', 'C', 10000.00,  1000.00,   9500.00,  800.00, 3,  4,   7500.00,  6000.00),
    ('00000000005', '000000005', 'A', 100000.00, 10000.00, 22000.00, 2200.00, 15, 2,  85000.00,  4200.00);


-- ============================================================
-- Authorization Details (5-7 per summary)
-- ============================================================

-- Account 00000000001 (summary_id=1) — 10 authorization records
INSERT INTO authorization_details
    (summary_id, card_number, auth_date, auth_time, auth_type, card_expiry,
     message_type, auth_response_code, auth_response_reason, auth_code,
     transaction_amount, approved_amount, pos_entry_mode, auth_source,
     mcc_code, merchant_name, merchant_id, merchant_city, merchant_state,
     merchant_zip, transaction_id, match_status, fraud_status, processing_code)
VALUES
    (1, '4111111111111111', '2026-04-01', '10:23:45', 'SALE', '12/28',
     '0110', '00', 'APPROVED',             'AUTH01',
     250.00, 250.00, '0101', 'TERMINAL',
     '5411', 'WHOLE FOODS MARKET',  'WHOL001234567', 'AUSTIN',         'TX', '78701',
     'TXN000000000001', 'M', NULL, '000000'),

    (1, '4111111111111111', '2026-04-01', '14:55:12', 'SALE', '12/28',
     '0110', '00', 'APPROVED',             'AUTH02',
     89.99, 89.99, '0101', 'TERMINAL',
     '5912', 'CVS PHARMACY',        'CVS0000000001', 'AUSTIN',         'TX', '78702',
     'TXN000000000002', 'M', NULL, '000000'),

    (1, '4111111111111111', '2026-04-02', '09:10:00', 'SALE', '12/28',
     '0110', '41', 'INSUFFICNT FUND',      '',
     5000.00, 0.00, '0101', 'TERMINAL',
     '5944', 'JEWELRY PALACE',      'JWLP00000001',  'AUSTIN',         'TX', '78703',
     'TXN000000000003', 'D', NULL, '000000'),

    (1, '4111111111111111', '2026-04-02', '16:30:22', 'SALE', '12/28',
     '0110', '00', 'APPROVED',             'AUTH03',
     125.50, 125.50, '0201', 'CHIP',
     '5812', 'OLIVE GARDEN',        'OLGD00000001',  'ROUND ROCK',     'TX', '78664',
     'TXN000000000004', 'M', NULL, '000000'),

    (1, '4111111111111111', '2026-04-03', '11:45:33', 'SALE', '12/28',
     '0110', '00', 'APPROVED',             'AUTH04',
     42.75, 42.75, '0201', 'CHIP',
     '5411', 'HEB GROCERY',         'HEB0000000001', 'PFLUGERVILLE',   'TX', '78660',
     'TXN000000000005', 'P', NULL, '000000'),

    (1, '4111111111111111', '2026-04-03', '18:20:11', 'SALE', '12/28',
     '0110', '00', 'APPROVED',             'AUTH05',
     310.00, 310.00, '0101', 'TERMINAL',
     '5651', 'BOOT BARN',           'BOOT00000001',  'CEDAR PARK',     'TX', '78613',
     'TXN000000000006', 'P', NULL, '000000'),

    (1, '4111111111111111', '2026-04-04', '08:05:59', 'SALE', '12/28',
     '0110', '00', 'APPROVED',             'AUTH06',
     15.25, 15.25, '0101', 'TERMINAL',
     '5812', 'STARBUCKS',           'SBUX00000001',  'AUSTIN',         'TX', '78701',
     'TXN000000000007', 'P', NULL, '000000'),

    (1, '4111111111111111', '2026-04-04', '12:00:00', 'SALE', '12/28',
     '0110', '51', 'CARD FRAUD',           '',
     999.00, 0.00, '0101', 'TERMINAL',
     '5944', 'GOLD MERCHANTS',      'GOLD00000001',  'DALLAS',         'TX', '75201',
     'TXN000000000008', 'D', 'F', '000000'),

    (1, '4111111111111111', '2026-04-05', '09:30:00', 'SALE', '12/28',
     '0110', '00', 'APPROVED',             'AUTH07',
     78.40, 78.40, '0201', 'CHIP',
     '5411', 'KROGER',              'KROG00000001',  'AUSTIN',         'TX', '78745',
     'TXN000000000009', 'P', NULL, '000000'),

    (1, '4111111111111111', '2026-04-05', '15:11:08', 'SALE', '12/28',
     '0110', '00', 'APPROVED',             'AUTH08',
     199.99, 199.99, '0101', 'TERMINAL',
     '5734', 'BEST BUY',            'BSTB00000001',  'AUSTIN',         'TX', '78759',
     'TXN000000000010', 'P', NULL, '000000');


-- Account 00000000002 (summary_id=2) — 6 authorization records
INSERT INTO authorization_details
    (summary_id, card_number, auth_date, auth_time, auth_type, card_expiry,
     message_type, auth_response_code, auth_response_reason, auth_code,
     transaction_amount, approved_amount, pos_entry_mode, auth_source,
     mcc_code, merchant_name, merchant_id, merchant_city, merchant_state,
     merchant_zip, transaction_id, match_status, fraud_status, processing_code)
VALUES
    (2, '5500005555555559', '2026-04-01', '09:00:00', 'SALE', '06/27',
     '0110', '00', 'APPROVED',             'AUTH09',
     540.00, 540.00, '0101', 'TERMINAL',
     '4411', 'DELTA AIRLINES',      'DELT00000001',  'ATLANTA',        'GA', '30320',
     'TXN000000000011', 'M', NULL, '000000'),

    (2, '5500005555555559', '2026-04-02', '14:22:00', 'SALE', '06/27',
     '0110', '00', 'APPROVED',             'AUTH10',
     65.00, 65.00, '0201', 'CHIP',
     '5812', 'CHILIS GRILL',        'CHIL00000001',  'HOUSTON',        'TX', '77001',
     'TXN000000000012', 'M', NULL, '000000'),

    (2, '5500005555555559', '2026-04-02', '18:10:44', 'SALE', '06/27',
     '0110', '42', 'CARD NOT ACTIVE',      '',
     200.00, 0.00, '0101', 'TERMINAL',
     '5999', 'MISC RETAIL',         'MISC00000001',  'HOUSTON',        'TX', '77002',
     'TXN000000000013', 'D', NULL, '000000'),

    (2, '5500005555555559', '2026-04-03', '10:00:00', 'SALE', '06/27',
     '0110', '00', 'APPROVED',             'AUTH11',
     1200.00, 1200.00, '0101', 'TERMINAL',
     '5211', 'HOME DEPOT',          'HOME00000001',  'HOUSTON',        'TX', '77003',
     'TXN000000000014', 'P', NULL, '000000'),

    (2, '5500005555555559', '2026-04-04', '16:45:00', 'SALE', '06/27',
     '0110', '00', 'APPROVED',             'AUTH12',
     85.99, 85.99, '0201', 'CHIP',
     '5912', 'WALGREENS',           'WALG00000001',  'HOUSTON',        'TX', '77004',
     'TXN000000000015', 'P', NULL, '000000'),

    (2, '5500005555555559', '2026-04-05', '11:30:00', 'SALE', '06/27',
     '0110', '00', 'APPROVED',             'AUTH13',
     320.00, 320.00, '0101', 'TERMINAL',
     '5651', 'MACYS',               'MACY00000001',  'HOUSTON',        'TX', '77005',
     'TXN000000000016', 'P', NULL, '000000');


-- Account 00000000003 (summary_id=3) — 7 authorization records
INSERT INTO authorization_details
    (summary_id, card_number, auth_date, auth_time, auth_type, card_expiry,
     message_type, auth_response_code, auth_response_reason, auth_code,
     transaction_amount, approved_amount, pos_entry_mode, auth_source,
     mcc_code, merchant_name, merchant_id, merchant_city, merchant_state,
     merchant_zip, transaction_id, match_status, fraud_status, processing_code)
VALUES
    (3, '3714496353984300', '2026-03-28', '08:15:00', 'SALE', '03/29',
     '0110', '00', 'APPROVED',             'AUTH14',
     4500.00, 4500.00, '0101', 'TERMINAL',
     '5944', 'TIFFANY AND CO',      'TIFF00000001',  'NEW YORK',       'NY', '10036',
     'TXN000000000017', 'M', NULL, '000000'),

    (3, '3714496353984300', '2026-03-29', '11:00:00', 'SALE', '03/29',
     '0110', '00', 'APPROVED',             'AUTH15',
     9800.00, 9800.00, '0101', 'TERMINAL',
     '5999', 'LUXURY IMPORTS',      'LUXU00000001',  'BEVERLY HILLS',  'CA', '90210',
     'TXN000000000018', 'M', NULL, '000000'),

    (3, '3714496353984300', '2026-03-30', '14:30:00', 'SALE', '03/29',
     '0110', '00', 'APPROVED',             'AUTH16',
     750.00, 750.00, '0201', 'CHIP',
     '5812', 'NOBU RESTAURANT',     'NOBU00000001',  'MIAMI',          'FL', '33139',
     'TXN000000000019', 'M', NULL, '000000'),

    (3, '3714496353984300', '2026-04-01', '09:45:00', 'SALE', '03/29',
     '0110', '52', 'MERCHANT FRAUD',       '',
     2000.00, 0.00, '0101', 'TERMINAL',
     '5999', 'SHADY ONLINE SHOP',   'SHAD00000001',  'UNKNOWN',        'XX', '00000',
     'TXN000000000020', 'D', 'F', '000000'),

    (3, '3714496353984300', '2026-04-02', '16:10:00', 'SALE', '03/29',
     '0110', '00', 'APPROVED',             'AUTH17',
     3200.00, 3200.00, '0101', 'TERMINAL',
     '7011', 'FOUR SEASONS HOTEL',  'FOUR00000001',  'NEW YORK',       'NY', '10022',
     'TXN000000000021', 'P', NULL, '000000'),

    (3, '3714496353984300', '2026-04-04', '12:00:00', 'SALE', '03/29',
     '0110', '00', 'APPROVED',             'AUTH18',
     580.00, 580.00, '0201', 'CHIP',
     '5651', 'NORDSTROM',           'NORD00000001',  'LOS ANGELES',    'CA', '90028',
     'TXN000000000022', 'P', NULL, '000000'),

    (3, '3714496353984300', '2026-04-05', '08:45:00', 'SALE', '03/29',
     '0110', '41', 'INSUFFICNT FUND',      '',
     30000.00, 0.00, '0101', 'TERMINAL',
     '5999', 'ART AUCTION HOUSE',   'AART00000001',  'CHICAGO',        'IL', '60601',
     'TXN000000000023', 'D', NULL, '000000');


-- Account 00000000004 (summary_id=4) — CLOSED account — 7 records
INSERT INTO authorization_details
    (summary_id, card_number, auth_date, auth_time, auth_type, card_expiry,
     message_type, auth_response_code, auth_response_reason, auth_code,
     transaction_amount, approved_amount, pos_entry_mode, auth_source,
     mcc_code, merchant_name, merchant_id, merchant_city, merchant_state,
     merchant_zip, transaction_id, match_status, fraud_status, processing_code)
VALUES
    (4, '6011111111111117', '2026-03-25', '09:00:00', 'SALE', '09/26',
     '0110', '00', 'APPROVED',             'AUTH19',
     100.00, 100.00, '0101', 'TERMINAL',
     '5411', 'ALDI',                'ALDI00000001',  'CHICAGO',        'IL', '60604',
     'TXN000000000024', 'M', NULL, '000000'),

    (4, '6011111111111117', '2026-03-26', '11:30:00', 'SALE', '09/26',
     '0110', '43', 'ACCOUNT CLOSED',       '',
     500.00, 0.00, '0101', 'TERMINAL',
     '5999', 'TARGET',              'TARG00000001',  'CHICAGO',        'IL', '60605',
     'TXN000000000025', 'D', NULL, '000000'),

    (4, '6011111111111117', '2026-03-27', '14:00:00', 'SALE', '09/26',
     '0110', '43', 'ACCOUNT CLOSED',       '',
     75.00, 0.00, '0201', 'CHIP',
     '5912', 'RITE AID',            'RITA00000001',  'CHICAGO',        'IL', '60606',
     'TXN000000000026', 'D', NULL, '000000'),

    (4, '6011111111111117', '2026-03-28', '10:15:00', 'SALE', '09/26',
     '0110', '43', 'ACCOUNT CLOSED',       '',
     250.00, 0.00, '0101', 'TERMINAL',
     '5812', 'MCDONALDS',           'MCDO00000001',  'CHICAGO',        'IL', '60607',
     'TXN000000000027', 'D', NULL, '000000'),

    (4, '6011111111111117', '2026-04-01', '08:30:00', 'SALE', '09/26',
     '0110', '43', 'ACCOUNT CLOSED',       '',
     180.00, 0.00, '0101', 'TERMINAL',
     '5651', 'KOHLS',               'KOHL00000001',  'EVANSTON',       'IL', '60201',
     'TXN000000000028', 'D', NULL, '000000'),

    (4, '6011111111111117', '2026-04-02', '16:00:00', 'SALE', '09/26',
     '0110', '00', 'APPROVED',             'AUTH20',
     45.00, 45.00, '0201', 'CHIP',
     '5411', 'JEWEL OSCO',          'JEWL00000001',  'CHICAGO',        'IL', '60608',
     'TXN000000000029', 'M', NULL, '000000'),

    (4, '6011111111111117', '2026-04-03', '12:45:00', 'SALE', '09/26',
     '0110', '00', 'APPROVED',             'AUTH21',
     310.00, 310.00, '0101', 'TERMINAL',
     '5734', 'RADIO SHACK',         'RADI00000001',  'CHICAGO',        'IL', '60609',
     'TXN000000000030', 'M', NULL, '000000');


-- Account 00000000005 (summary_id=5) — 7 authorization records
INSERT INTO authorization_details
    (summary_id, card_number, auth_date, auth_time, auth_type, card_expiry,
     message_type, auth_response_code, auth_response_reason, auth_code,
     transaction_amount, approved_amount, pos_entry_mode, auth_source,
     mcc_code, merchant_name, merchant_id, merchant_city, merchant_state,
     merchant_zip, transaction_id, match_status, fraud_status, processing_code)
VALUES
    (5, '3530111333300000', '2026-04-01', '07:00:00', 'SALE', '11/30',
     '0110', '00', 'APPROVED',             'AUTH22',
     8500.00, 8500.00, '0101', 'TERMINAL',
     '5999', 'BLOOMBERG LP',        'BLOO00000001',  'NEW YORK',       'NY', '10022',
     'TXN000000000031', 'M', NULL, '000000'),

    (5, '3530111333300000', '2026-04-02', '09:30:00', 'SALE', '11/30',
     '0110', '00', 'APPROVED',             'AUTH23',
     22000.00, 22000.00, '0101', 'TERMINAL',
     '7011', 'RITZ CARLTON',        'RITZ00000001',  'NEW YORK',       'NY', '10023',
     'TXN000000000032', 'M', NULL, '000000'),

    (5, '3530111333300000', '2026-04-03', '11:15:00', 'SALE', '11/30',
     '0110', '00', 'APPROVED',             'AUTH24',
     4200.00, 4200.00, '0201', 'CHIP',
     '5944', 'SOTHEBYS',            'SOTH00000001',  'NEW YORK',       'NY', '10021',
     'TXN000000000033', 'M', NULL, '000000'),

    (5, '3530111333300000', '2026-04-03', '14:00:00', 'SALE', '11/30',
     '0110', '41', 'INSUFFICNT FUND',      '',
     85000.00, 0.00, '0101', 'TERMINAL',
     '5999', 'PRIVATE JET CHARTER', 'PRIV00000001',  'TETERBORO',      'NJ', '07608',
     'TXN000000000034', 'D', NULL, '000000'),

    (5, '3530111333300000', '2026-04-04', '08:00:00', 'SALE', '11/30',
     '0110', '00', 'APPROVED',             'AUTH25',
     15000.00, 15000.00, '0101', 'TERMINAL',
     '5944', 'HARRODS',             'HARR00000001',  'LONDON',         'UK', 'SW1X7XL',
     'TXN000000000035', 'P', NULL, '000000'),

    (5, '3530111333300000', '2026-04-05', '10:00:00', 'SALE', '11/30',
     '0110', '00', 'APPROVED',             'AUTH26',
     6300.00, 6300.00, '0201', 'CHIP',
     '7011', 'SHANGRI LA HOTEL',    'SHAN00000001',  'PARIS',          'FR', '75001',
     'TXN000000000036', 'P', NULL, '000000'),

    (5, '3530111333300000', '2026-04-05', '13:00:00', 'SALE', '11/30',
     '0110', '00', 'APPROVED',             'AUTH27',
     29000.00, 29000.00, '0101', 'TERMINAL',
     '5944', 'CARTIER',             'CART00000001',  'PARIS',          'FR', '75008',
     'TXN000000000037', 'P', NULL, '000000');


-- ============================================================
-- Fraud Records (2 sample records — correspond to fraud-flagged details)
-- TXN000000000008 (detail for account 1) and TXN000000000020 (account 3)
-- ============================================================

INSERT INTO fraud_records
    (card_number, auth_timestamp, fraud_flag, fraud_report_date, match_status,
     account_id, customer_id, auth_detail_id)
VALUES
    ('4111111111111111', '2026-04-04 12:00:00', 'F', '2026-04-04',
     'D', '00000000001', '000000001', 8),
    ('3714496353984300', '2026-04-01 09:45:00', 'F', '2026-04-01',
     'D', '00000000003', '000000003', 20);
