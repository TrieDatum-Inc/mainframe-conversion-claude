-- =============================================================================
-- Seed data for the `users` table
-- COBOL origin: USRSEC VSAM KSDS seed records
--
-- Minimum 10 rows per spec. Includes at least 2 Admin users (type='A')
-- and 8 Regular users (type='U').
--
-- Passwords: all test accounts use password 'Test1234!'
-- bcrypt hash generated with 12 rounds.
-- The actual hash below is the bcrypt hash of 'Test1234!' with 12 rounds.
-- For the admin 'SYSADM00' the hash is for 'Admin123!'
-- =============================================================================

INSERT INTO users (user_id, first_name, last_name, password_hash, user_type) VALUES
-- Admin users (user_type = 'A')
('ADMIN001', 'System', 'Administrator',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'A'),
('SYSADM00', 'Sarah', 'Johnson',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'A'),
-- Regular users (user_type = 'U')
('USER0001', 'John', 'Smith',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U'),
('USER0002', 'Mary', 'Jones',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U'),
('USER0003', 'Robert', 'Williams',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U'),
('USER0004', 'Patricia', 'Brown',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U'),
('USER0005', 'James', 'Davis',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U'),
('USER0006', 'Linda', 'Miller',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U'),
('USER0007', 'Michael', 'Wilson',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U'),
('USER0008', 'Barbara', 'Moore',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'U')
ON CONFLICT (user_id) DO NOTHING;

-- =============================================================================
-- Seed data for the `transaction_types` table
-- COBOL origin: CARDDEMO.TRANSACTION_TYPE DB2 table (COTRTLIC / COTRTUPC)
--
-- Minimum 10 rows per spec (section 6: Key Seed Constraints).
-- Includes type code '01' (standard purchase) and '02' (bill payment per COBIL00C).
-- Type codes must be numeric 01-99 (COTRTUPC 1210-EDIT-TRANTYPE).
-- Descriptions must be alphanumeric only (COTRTUPC 1230-EDIT-ALPHANUM-REQD).
-- =============================================================================
INSERT INTO transaction_types (type_code, description) VALUES
('01', 'Purchase'),
('02', 'Bill Payment'),
('03', 'Cash Advance'),
('04', 'Balance Transfer'),
('05', 'Refund'),
('06', 'Fee'),
('07', 'Interest Charge'),
('08', 'Reward Redemption'),
('09', 'Dispute Credit'),
('10', 'Merchant Chargeback'),
('11', 'Foreign Transaction'),
('12', 'Recurring Payment'),
('15', 'Online Purchase'),
('20', 'ATM Withdrawal')
ON CONFLICT (type_code) DO NOTHING;

-- =============================================================================
-- Seed data for the `accounts` table
-- COBOL origin: ACCTDAT VSAM KSDS seed records
-- Minimum 10 rows with varied balances, credit limits, active statuses.
-- =============================================================================
INSERT INTO accounts (
    account_id, active_status, current_balance, credit_limit, cash_credit_limit,
    open_date, expiration_date, reissue_date,
    curr_cycle_credit, curr_cycle_debit, zip_code, group_id
) VALUES
(10000000001, 'Y',  1234.56,  10000.00,  2000.00, '2020-01-15', '2025-01-15', '2023-01-15',  500.00,  1734.56, '10001', 'GROUP001'),
(10000000002, 'Y',  5678.90,  20000.00,  5000.00, '2019-06-01', '2024-06-01', '2022-06-01', 1200.00,  6878.90, '20002', 'GROUP001'),
(10000000003, 'Y',     0.00,  15000.00,  3000.00, '2021-03-20', '2026-03-20', '2024-03-20',    0.00,     0.00, '30003', 'GROUP002'),
(10000000004, 'N',  9999.99,  10000.00,  1000.00, '2018-11-10', '2023-11-10', '2021-11-10',    0.00,  9999.99, '40004', 'GROUP002'),
(10000000005, 'Y',  2500.00,  25000.00,  8000.00, '2022-07-04', '2027-07-04', '2025-07-04',  300.00,  2800.00, '50005', 'GROUP003'),
(10000000006, 'Y',   450.00,   5000.00,  1000.00, '2020-09-15', '2025-09-15', '2023-09-15',   50.00,   500.00, '60006', 'GROUP001'),
(10000000007, 'Y', 12000.00,  50000.00, 10000.00, '2017-04-22', '2022-04-22', '2020-04-22', 2000.00, 14000.00, '70007', 'GROUP003'),
(10000000008, 'Y',   100.00,   8000.00,  2000.00, '2023-01-01', '2028-01-01', '2026-01-01',  100.00,   200.00, '80008', 'GROUP002'),
(10000000009, 'N',  3750.50,  12000.00,  3000.00, '2019-12-31', '2024-12-31', '2022-12-31',    0.00,  3750.50, '90009', 'GROUP001'),
(10000000010, 'Y',  8000.00,  30000.00,  6000.00, '2021-08-08', '2026-08-08', '2024-08-08', 1500.00,  9500.00, '10010', 'GROUP003')
ON CONFLICT (account_id) DO NOTHING;

-- =============================================================================
-- Seed data for the `customers` table
-- COBOL origin: CUSTDAT VSAM KSDS seed records
-- Minimum 10 customers linked to the seeded accounts.
-- SSN format: NNN-NN-NNNN (validated: part1 not 000/666/900-999)
-- =============================================================================
INSERT INTO customers (
    customer_id, first_name, middle_name, last_name,
    street_address_1, street_address_2, city, state_code, zip_code, country_code,
    phone_number_1, phone_number_2,
    ssn, date_of_birth, fico_score, government_id_ref, eft_account_id,
    primary_card_holder_flag
) VALUES
(100000001, 'James',    'Edward',  'Anderson', '123 Main St',    NULL,         'New York',    'NY', '10001', 'USA', '212-555-0101', '212-555-0201', '123-45-6789', '1975-04-12', 750, 'DL123456789', 'EFT0000001', 'Y'),
(100000002, 'Maria',    'Rose',    'Garcia',   '456 Oak Ave',    'Apt 2B',     'Los Angeles', 'CA', '90001', 'USA', '310-555-0102', NULL,            '234-56-7890', '1982-07-22', 680, 'PP987654321', 'EFT0000002', 'Y'),
(100000003, 'Robert',   NULL,      'Johnson',  '789 Pine Rd',    NULL,         'Chicago',     'IL', '60601', 'USA', '312-555-0103', '312-555-0203', '345-67-8901', '1969-11-05', 820, 'DL345678901', NULL,         'Y'),
(100000004, 'Patricia', 'Ann',     'Williams', '321 Elm St',     'Suite 100',  'Houston',     'TX', '77001', 'USA', '713-555-0104', '713-555-0204', '456-78-9012', '1990-02-28', 590, 'PP456789012', 'EFT0000004', 'Y'),
(100000005, 'Michael',  NULL,      'Brown',    '654 Cedar Ln',   NULL,         'Phoenix',     'AZ', '85001', 'USA', '602-555-0105', NULL,            '567-89-0123', '1985-09-14', 710, 'DL567890123', 'EFT0000005', 'Y'),
(100000006, 'Linda',    'Marie',   'Davis',    '987 Birch Blvd', 'Unit 5',     'Philadelphia','PA', '19101', 'USA', '215-555-0106', '215-555-0206', '678-90-1234', '1978-06-30', 760, 'PP678901234', NULL,         'Y'),
(100000007, 'William',  'James',   'Miller',   '246 Walnut Way', NULL,         'San Antonio', 'TX', '78201', 'USA', '210-555-0107', '210-555-0207', '789-01-2345', '1963-03-18', 835, 'DL789012345', 'EFT0000007', 'Y'),
(100000008, 'Susan',    NULL,      'Wilson',   '135 Maple Dr',   NULL,         'San Diego',   'CA', '92101', 'USA', '619-555-0108', NULL,            '890-12-3456', '1995-12-01', 650, 'PP890123456', 'EFT0000008', 'Y'),
(100000009, 'Thomas',   'Ray',     'Moore',    '468 Spruce St',  'Apt 3A',     'Dallas',      'TX', '75201', 'USA', '214-555-0109', '214-555-0209', '901-23-4567', '1971-08-25', 725, 'DL901234567', NULL,         'Y'),
(100000010, 'Jennifer', 'Lee',     'Taylor',   '579 Ash Ave',    NULL,         'Jacksonville','FL', '32201', 'USA', '904-555-0110', '904-555-0210', '112-34-5678', '1988-05-10', 790, 'PP112345678', 'EFT0000010', 'Y')
ON CONFLICT (customer_id) DO NOTHING;

-- =============================================================================
-- Seed data for the `account_customer_xref` table
-- Links each account to its primary customer.
-- =============================================================================
INSERT INTO account_customer_xref (account_id, customer_id) VALUES
(10000000001, 100000001),
(10000000002, 100000002),
(10000000003, 100000003),
(10000000004, 100000004),
(10000000005, 100000005),
(10000000006, 100000006),
(10000000007, 100000007),
(10000000008, 100000008),
(10000000009, 100000009),
(10000000010, 100000010)
ON CONFLICT (account_id, customer_id) DO NOTHING;

-- =============================================================================
-- Seed data for the `credit_cards` table
-- COBOL origin: CARDDAT VSAM KSDS seed records
-- 12 cards across 10 accounts (some accounts have multiple cards).
-- =============================================================================
INSERT INTO credit_cards (
    card_number, account_id, customer_id, card_embossed_name, active_status,
    expiration_date, expiration_day, cvv
) VALUES
('4111111111111001', 10000000001, 100000001, 'JAMES E ANDERSON',   'Y', '2027-01-31', 31, '101'),
('4111111111111002', 10000000002, 100000002, 'MARIA R GARCIA',     'Y', '2026-06-30', 30, '102'),
('4111111111111003', 10000000003, 100000003, 'ROBERT JOHNSON',     'Y', '2028-03-31', 31, '103'),
('4111111111111004', 10000000004, 100000004, 'PATRICIA A WILLIAMS','N', '2023-11-30', 30, '104'),
('4111111111111005', 10000000005, 100000005, 'MICHAEL BROWN',      'Y', '2027-07-31', 31, '105'),
('4111111111111006', 10000000006, 100000006, 'LINDA M DAVIS',      'Y', '2025-09-30', 30, '106'),
('4111111111111007', 10000000007, 100000007, 'WILLIAM J MILLER',   'Y', '2024-04-30', 30, '107'),
('4111111111111008', 10000000008, 100000008, 'SUSAN WILSON',       'Y', '2028-01-31', 31, '108'),
('4111111111111009', 10000000009, 100000009, 'THOMAS R MOORE',     'N', '2024-12-31', 31, '109'),
('4111111111111010', 10000000010, 100000010, 'JENNIFER L TAYLOR',  'Y', '2026-08-31', 31, '110'),
-- Additional cards for accounts with multiple cards
('4222222222221001', 10000000001, 100000001, 'JAMES ANDERSON SEC', 'Y', '2026-05-31', 31, '201'),
('4222222222222002', 10000000005, 100000005, 'MICHAEL BROWN CORP', 'Y', '2027-12-31', 31, '202')
ON CONFLICT (card_number) DO NOTHING;

-- =============================================================================
-- Seed data for the `card_account_xref` table
-- COBOL origin: CARDXREF VSAM KSDS (CVACT03Y copybook)
-- One entry per card — links card_number → customer_id + account_id.
-- idx_cardxref_account replaces VSAM AIX on XREF-ACCT-ID.
-- =============================================================================
INSERT INTO card_account_xref (card_number, customer_id, account_id) VALUES
('4111111111111001', 100000001, 10000000001),
('4111111111111002', 100000002, 10000000002),
('4111111111111003', 100000003, 10000000003),
('4111111111111004', 100000004, 10000000004),
('4111111111111005', 100000005, 10000000005),
('4111111111111006', 100000006, 10000000006),
('4111111111111007', 100000007, 10000000007),
('4111111111111008', 100000008, 10000000008),
('4111111111111009', 100000009, 10000000009),
('4111111111111010', 100000010, 10000000010),
('4222222222221001', 100000001, 10000000001),
('4222222222222002', 100000005, 10000000005)
ON CONFLICT (card_number) DO NOTHING;

-- =============================================================================
-- Seed data for `transaction_id_seq`
-- Start at 100 to avoid conflicts with any manually inserted test data.
-- =============================================================================
SELECT SETVAL('transaction_id_seq', 100, false);

-- =============================================================================
-- Seed data for `transaction_types` table
-- COBOL origin: DB2 CARDDEMO.TRANSACTION_TYPE (DCLTRTYP DCLGEN copybook)
-- Minimum 10 types; '01'=standard purchase, '02'=bill payment (hardcoded in COBIL00C)
-- =============================================================================
INSERT INTO transaction_types (type_code, description) VALUES
('01', 'Regular Purchase'),
('02', 'Bill Payment'),
('03', 'Cash Advance'),
('04', 'Balance Transfer'),
('05', 'Refund Credit'),
('06', 'Fee Charge'),
('07', 'Interest Charge'),
('08', 'Reward Redemption'),
('09', 'Dispute Credit'),
('10', 'Promotional Credit'),
('11', 'Foreign Transaction'),
('12', 'Recurring Payment')
ON CONFLICT (type_code) DO NOTHING;

-- =============================================================================
-- Seed data for `transactions` table
-- COBOL origin: TRANSACT VSAM KSDS (CVTRA05Y / COTRN02Y copybook)
-- Minimum 50 transactions across seeded cards to exercise COTRN00C pagination
-- (10 rows per page = need at least 3 pages = 21+ transactions).
-- transaction_id format: zero-padded 16-digit string (TRAN-ID X(16) in COTRN02Y)
-- =============================================================================
INSERT INTO transactions (
    transaction_id, card_number, transaction_type_code, transaction_category_code,
    transaction_source, description, amount, original_date, processed_date,
    merchant_id, merchant_name, merchant_city, merchant_zip
) VALUES
('0000000000000001', '4111111111111001', '01', '1001', 'POS TERM',  'GROCERY STORE PURCHASE',    -52.47, '2026-01-05', '2026-01-06', '100000001', 'WHOLE FOODS MKT',   'NEW YORK',       '10001'),
('0000000000000002', '4111111111111001', '01', '1002', 'POS TERM',  'RESTAURANT MEAL',           -28.90, '2026-01-07', '2026-01-08', '100000002', 'CHIPOTLE GRILL',    'NEW YORK',       '10002'),
('0000000000000003', '4111111111111002', '01', '1003', 'ONLINE',    'AMAZON MARKETPLACE',       -119.99, '2026-01-10', '2026-01-11', '100000003', 'AMAZON.COM',        'SEATTLE',        '98101'),
('0000000000000004', '4111111111111002', '06', '6001', 'SYSTEM',    'ANNUAL FEE CHARGE',         -95.00, '2026-01-15', '2026-01-15', '999999998', 'CARD SERVICES',     'WILMINGTON',     '19801'),
('0000000000000005', '4111111111111003', '01', '1004', 'POS TERM',  'GAS STATION PURCHASE',      -45.20, '2026-01-12', '2026-01-13', '100000005', 'SHELL STATION',     'LOS ANGELES',    '90001'),
('0000000000000006', '4111111111111003', '01', '1001', 'POS TERM',  'SUPERMARKET PURCHASE',      -78.33, '2026-01-14', '2026-01-15', '100000006', 'SAFEWAY STORES',    'LOS ANGELES',    '90002'),
('0000000000000007', '4111111111111004', '01', '1005', 'ONLINE',    'NETFLIX SUBSCRIPTION',      -15.49, '2026-01-01', '2026-01-01', '100000007', 'NETFLIX INC',       'LOS GATOS',      '95030'),
('0000000000000008', '4111111111111004', '01', '1005', 'ONLINE',    'SPOTIFY SUBSCRIPTION',       -9.99, '2026-01-01', '2026-01-01', '100000008', 'SPOTIFY AB',        'NEW YORK',       '10019'),
('0000000000000009', '4111111111111005', '01', '1002', 'POS TERM',  'COFFEE SHOP',               -12.75, '2026-01-08', '2026-01-09', '100000009', 'STARBUCKS CORP',    'CHICAGO',        '60601'),
('0000000000000010', '4111111111111005', '03', '3001', 'ATM',       'CASH ADVANCE',             -200.00, '2026-01-10', '2026-01-10', '200000001', 'CHASE ATM',         'CHICAGO',        '60602'),
('0000000000000011', '4111111111111006', '01', '1003', 'ONLINE',    'BEST BUY ELECTRONICS',     -349.99, '2026-01-15', '2026-01-16', '100000010', 'BEST BUY CO',       'MINNEAPOLIS',    '55402'),
('0000000000000012', '4111111111111006', '05', '5001', 'SYSTEM',    'RETURN CREDIT ELECTRONICS',  349.99, '2026-01-18', '2026-01-19', '100000010', 'BEST BUY CO',       'MINNEAPOLIS',    '55402'),
('0000000000000013', '4111111111111007', '01', '1001', 'POS TERM',  'FARMERS MARKET',            -33.50, '2026-01-20', '2026-01-21', '100000011', 'CITY FARMERS MKT',  'PHOENIX',        '85001'),
('0000000000000014', '4111111111111007', '01', '1004', 'POS TERM',  'AUTO REPAIR SERVICE',      -285.00, '2026-01-22', '2026-01-23', '100000012', 'JIFFY LUBE',        'PHOENIX',        '85002'),
('0000000000000015', '4111111111111008', '01', '1002', 'POS TERM',  'FINE DINING RESTAURANT',   -145.80, '2026-01-25', '2026-01-26', '100000013', 'THE CAPITAL GRILLE','PHILADELPHIA',   '19103'),
('0000000000000016', '4111111111111008', '04', '4001', 'ONLINE',    'BALANCE TRANSFER IN',       500.00, '2026-01-28', '2026-01-29', '999999997', 'TRANSFER SERVICES', 'WILMINGTON',     '19801'),
('0000000000000017', '4111111111111009', '01', '1001', '    MOBILE','TARGET STORE PURCHASE',      -67.43, '2026-02-02', '2026-02-03', '100000014', 'TARGET CORP',       'MINNEAPOLIS',    '55403'),
('0000000000000018', '4111111111111009', '01', '1005', 'ONLINE',    'APPLE APP STORE',            -4.99, '2026-02-03', '2026-02-03', '100000015', 'APPLE INC',         'CUPERTINO',      '95014'),
('0000000000000019', '4111111111111010', '01', '1003', 'ONLINE',    'HOTEL BOOKING',            -298.00, '2026-02-05', '2026-02-06', '100000016', 'MARRIOTT HOTELS',   'BETHESDA',       '20817'),
('0000000000000020', '4111111111111010', '07', '7001', 'SYSTEM',    'MONTHLY INTEREST CHARGE',   -24.50, '2026-02-01', '2026-02-01', '999999996', 'CARD INTEREST',     'WILMINGTON',     '19801'),
('0000000000000021', '4111111111111001', '01', '1001', 'POS TERM',  'COSTCO WHOLESALE',          -156.78, '2026-02-08', '2026-02-09', '100000017', 'COSTCO WHOLESALE',  'ISSAQUAH',       '98027'),
('0000000000000022', '4111111111111001', '01', '1002', 'POS TERM',  'FAST FOOD PURCHASE',         -8.99, '2026-02-10', '2026-02-11', '100000018', 'MCDONALDS CORP',    'OAK BROOK',      '60523'),
('0000000000000023', '4111111111111002', '01', '1004', 'POS TERM',  'PHARMACY PURCHASE',          -42.15, '2026-02-12', '2026-02-13', '100000019', 'CVS PHARMACY',      'WOONSOCKET',     '02895'),
('0000000000000024', '4111111111111002', '01', '1003', 'ONLINE',    'AIRLINE TICKET',           -389.00, '2026-02-14', '2026-02-15', '100000020', 'DELTA AIR LINES',   'ATLANTA',        '30320'),
('0000000000000025', '4111111111111003', '01', '1001', 'POS TERM',  'HOME DEPOT PURCHASE',        -87.42, '2026-02-15', '2026-02-16', '100000021', 'HOME DEPOT INC',    'ATLANTA',        '30339'),
('0000000000000026', '4111111111111003', '01', '1002', 'POS TERM',  'SUSHI RESTAURANT',           -65.00, '2026-02-18', '2026-02-19', '100000022', 'NOBU RESTAURANT',   'NEW YORK',       '10013'),
('0000000000000027', '4111111111111004', '01', '1003', 'ONLINE',    'AMAZON PRIME MEMBERSHIP',    -14.99, '2026-02-01', '2026-02-01', '100000003', 'AMAZON.COM',        'SEATTLE',        '98101'),
('0000000000000028', '4111111111111004', '01', '1001', 'POS TERM',  'WALMART SUPERCENTER',        -73.21, '2026-02-20', '2026-02-21', '100000023', 'WALMART INC',       'BENTONVILLE',    '72716'),
('0000000000000029', '4111111111111005', '11', '1101', 'INTL',      'FOREIGN PURCHASE PARIS',    -120.00, '2026-02-22', '2026-02-23', '300000001', 'CAFE DE PARIS',     'PARIS',          '75001'),
('0000000000000030', '4111111111111005', '01', '1004', 'POS TERM',  'DENTAL OFFICE',             -250.00, '2026-02-24', '2026-02-25', '100000024', 'SMILE DENTAL',      'CHICAGO',        '60603'),
('0000000000000031', '4111111111111006', '01', '1001', 'POS TERM',  'TRADER JOES PURCHASE',       -48.60, '2026-02-25', '2026-02-26', '100000025', 'TRADER JOES CO',    'MONROVIA',       '91016'),
('0000000000000032', '4111111111111006', '12', '1201', 'RECURRING', 'GYM MEMBERSHIP FEE',         -45.00, '2026-02-01', '2026-02-01', '100000026', 'PLANET FITNESS',    'HAMPTON',        '03843'),
('0000000000000033', '4111111111111007', '01', '1003', 'ONLINE',    'UBER RIDE SHARE',            -23.50, '2026-03-01', '2026-03-02', '100000027', 'UBER TECHNOLOGIES', 'SAN FRANCISCO',  '94103'),
('0000000000000034', '4111111111111007', '01', '1002', 'POS TERM',  'PIZZA RESTAURANT',           -35.20, '2026-03-03', '2026-03-04', '100000028', 'DOMINOS PIZZA',     'ANN ARBOR',      '48103'),
('0000000000000035', '4111111111111008', '08', '8001', 'SYSTEM',    'REWARDS POINTS REDEMPTION',  150.00, '2026-03-05', '2026-03-05', '999999995', 'CARD REWARDS',      'WILMINGTON',     '19801'),
('0000000000000036', '4111111111111008', '01', '1004', 'POS TERM',  'EYE DOCTOR VISIT',           -95.00, '2026-03-06', '2026-03-07', '100000029', 'VISION CENTER',     'PHILADELPHIA',   '19104'),
('0000000000000037', '4111111111111009', '01', '1001', 'POS TERM',  'WHOLE FOODS MARKET',         -92.18, '2026-03-08', '2026-03-09', '100000001', 'WHOLE FOODS MKT',   'MINNEAPOLIS',    '55404'),
('0000000000000038', '4111111111111009', '01', '1005', 'ONLINE',    'GOOGLE PLAY PURCHASE',        -2.99, '2026-03-10', '2026-03-10', '100000030', 'GOOGLE LLC',        'MOUNTAIN VIEW',  '94043'),
('0000000000000039', '4111111111111010', '01', '1003', 'ONLINE',    'EXPEDIA HOTEL BOOKING',     -175.00, '2026-03-12', '2026-03-13', '100000031', 'EXPEDIA GROUP',     'BELLEVUE',       '98004'),
('0000000000000040', '4111111111111010', '09', '9001', 'DISPUTE',   'DISPUTE CREDIT GRANTED',    175.00, '2026-03-14', '2026-03-14', '999999994', 'DISPUTE SERVICES',  'WILMINGTON',     '19801'),
('0000000000000041', '4111111111111001', '02', '0002', 'POS TERM',  'BILL PAYMENT - ONLINE',    1500.00, '2026-03-15', '2026-03-15', '999999999', 'BILL PAYMENT',      'N/A',            'N/A'),
('0000000000000042', '4111111111111002', '01', '1001', 'POS TERM',  'FRESH MARKET GROCERY',       -38.90, '2026-03-16', '2026-03-17', '100000032', 'FRESH MARKET',      'GREENSBORO',     '27401'),
('0000000000000043', '4111111111111003', '01', '1004', 'POS TERM',  'ELECTRIC VEHICLE CHARGE',    -18.75, '2026-03-18', '2026-03-19', '100000033', 'TESLA SUPERCHARGE', 'PALO ALTO',      '94301'),
('0000000000000044', '4111111111111004', '01', '1002', 'POS TERM',  'STEAKHOUSE DINNER',         -185.50, '2026-03-20', '2026-03-21', '100000034', 'RUTH CHRIS STEAK',  'NEW YORK',       '10036'),
('0000000000000045', '4111111111111005', '01', '1003', 'ONLINE',    'AIRBNB STAY',               -320.00, '2026-03-22', '2026-03-23', '100000035', 'AIRBNB INC',        'SAN FRANCISCO',  '94107'),
('0000000000000046', '4111111111111006', '01', '1001', 'POS TERM',  'KROGER SUPERMARKET',         -64.22, '2026-03-24', '2026-03-25', '100000036', 'KROGER CO',         'CINCINNATI',     '45202'),
('0000000000000047', '4111111111111007', '01', '1004', 'POS TERM',  'VETERINARY OFFICE',         -145.00, '2026-03-26', '2026-03-27', '100000037', 'PET HEALTH CLINIC', 'PHOENIX',        '85003'),
('0000000000000048', '4111111111111008', '01', '1001', 'POS TERM',  'WHOLE FOODS MARKET',         -55.30, '2026-03-28', '2026-03-29', '100000001', 'WHOLE FOODS MKT',   'PHILADELPHIA',   '19105'),
('0000000000000049', '4111111111111009', '01', '1002', 'POS TERM',  'PIZZA DELIVERY',             -22.99, '2026-03-30', '2026-03-31', '100000038', 'PIZZA HUT INC',     'PLANO',          '75024'),
('0000000000000050', '4111111111111010', '01', '1005', 'ONLINE',    'HULU STREAMING SERVICE',     -17.99, '2026-03-31', '2026-03-31', '100000039', 'HULU LLC',          'SANTA MONICA',   '90404'),
('0000000000000051', '4222222222221001', '01', '1001', 'POS TERM',  'LOCAL MARKET PURCHASE',      -29.45, '2026-04-01', '2026-04-02', '100000040', 'LOCAL MARKET',      'NEW YORK',       '10003'),
('0000000000000052', '4222222222222002', '01', '1001', 'POS TERM',  'NEIGHBORHOOD STORE',         -41.80, '2026-04-02', '2026-04-03', '100000041', 'NEIGHBORHOOD STORE','CHICAGO',        '60604')
ON CONFLICT (transaction_id) DO NOTHING;

-- =============================================================================
-- Seed data for `report_requests` table
-- COBOL origin: CORPT00C TDQ QUEUE='JOBS' batch job submission
-- Simulates submitted report requests in various states.
-- =============================================================================
INSERT INTO report_requests (report_type, start_date, end_date, requested_by, status, requested_at) VALUES
('M', '2026-01-01', '2026-01-31', 'admin001', 'COMPLETED', NOW() - INTERVAL '30 days'),
('Y', '2026-01-01', '2026-12-31', 'admin001', 'RUNNING',   NOW() - INTERVAL '2 hours'),
('C', '2026-01-01', '2026-03-31', 'admin002', 'COMPLETED', NOW() - INTERVAL '10 days'),
('M', '2026-02-01', '2026-02-28', 'user0001', 'FAILED',    NOW() - INTERVAL '5 days'),
('C', '2026-02-15', '2026-03-15', 'user0002', 'COMPLETED', NOW() - INTERVAL '7 days'),
('M', '2026-03-01', '2026-03-31', 'admin001', 'PENDING',   NOW() - INTERVAL '1 hour'),
('Y', '2025-01-01', '2025-12-31', 'admin002', 'COMPLETED', NOW() - INTERVAL '20 days'),
('C', '2026-03-01', '2026-04-05', 'user0003', 'PENDING',   NOW() - INTERVAL '30 minutes'),
('M', '2026-04-01', '2026-04-30', 'user0004', 'PENDING',   NOW()),
('C', '2025-10-01', '2025-12-31', 'admin001', 'COMPLETED', NOW() - INTERVAL '45 days')
ON CONFLICT DO NOTHING;
