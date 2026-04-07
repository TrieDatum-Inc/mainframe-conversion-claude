-- =============================================================================
-- CardDemo Seed Data — Credit Cards Module
-- Derived from app/data/ASCII/ VSAM flat files
-- =============================================================================

-- Users (admin + regular)
INSERT INTO users (user_id, first_name, last_name, password_hash, user_type) VALUES
('ADMIN001', 'System',    'Administrator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCjSB8N9Q5VGj5j1C5gKIHa', 'A'),
('USER0001', 'Alice',     'Johnson',       '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCjSB8N9Q5VGj5j1C5gKIHa', 'U'),
('USER0002', 'Bob',       'Smith',         '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCjSB8N9Q5VGj5j1C5gKIHa', 'U'),
('USER0003', 'Carol',     'Williams',      '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCjSB8N9Q5VGj5j1C5gKIHa', 'U')
ON CONFLICT (user_id) DO NOTHING;

-- Accounts (from acctdata.txt — 10 records)
INSERT INTO accounts (account_id, active_status, current_balance, credit_limit, cash_credit_limit, open_date, expiration_date, reissue_date, group_id) VALUES
(1,  'Y',  19400.00,  20200.00,  10200.00, '2014-11-20', '2025-05-20', '2025-05-20', 'A000000000'),
(2,  'Y',  15800.00,  61300.00,  54480.00, '2013-06-19', '2024-08-11', '2024-08-11', 'A000000000'),
(3,  'Y',  14700.00,  49090.00,   5380.00, '2013-08-23', '2024-01-10', '2024-01-10', 'A000000000'),
(4,  'Y',   4000.00,  35030.00,  27890.00, '2012-11-17', '2023-12-16', '2023-12-16', 'A000000000'),
(5,  'Y',  34500.00,  38190.00,  24300.00, '2012-10-03', '2025-03-09', '2025-03-09', 'A000000000'),
(6,  'Y',  14700.00,  28680.00,  24790.00, '2013-03-14', '2024-07-24', '2024-07-24', 'A000000000'),
(7,  'Y',   4900.00,  19080.00,  12500.00, '2013-07-01', '2024-03-07', '2024-03-07', 'A000000000'),
(8,  'N',  50200.00,  32710.00,  18150.00, '2012-09-06', '2023-10-19', '2023-10-19', 'A000000000'),
(9,  'Y',  36200.00,  33000.00,  18980.00, '2013-06-19', '2023-12-20', '2023-12-20', 'A000000000'),
(10, 'Y',  30500.00,  46510.00,  33160.00, '2013-01-16', '2025-02-14', '2025-02-14', 'A000000000')
ON CONFLICT (account_id) DO NOTHING;

-- Customers (from custdata.txt — 10 records)
INSERT INTO customers (customer_id, first_name, middle_name, last_name,
    address_line_1, address_line_2, address_line_3,
    state_code, country_code, zip_code, phone_1, phone_2,
    ssn, government_id_ref, date_of_birth, eft_account_id, primary_card_holder, fico_score)
VALUES
(1,  'Immanuel', 'Madeline', 'Kessler',     '618 Deshaun Route',     'Apt. 802',  'Altenwerthshire',   'NC', 'USA', '12546',      '(908)119-8310', '(373)693-8684', '123-45-0001', '0000000004', '1961-06-08', '00535817', 'Y', 574),
(2,  'Enrico',   'April',    'Rosenbaum',   '4917 Myrna Flats',      'Apt. 453',  'West Bernita',      'IN', 'USA', '22770',      '(429)706-9510', '(744)950-5272', '123-45-0002', '0000000005', '1961-10-08', '00691940', 'Y', 568),
(3,  'Larry',    'Cody',     'Homenick',    '362 Esta Parks',        'Apt. 390',  'New Gladys',        'GA', 'USA', '19852-6716', '(950)396-9024', '(685)168-8826', '123-45-0003', '0000000005', '1987-11-30', '00064657', 'Y', 616),
(4,  'Delbert',  'Kaia',     'Parisian',    '638 Blanda Gateway',    'Apt. 076',  'Lake Virginie',     'MI', 'USA', '39035-0455', '(801)603-4121', '(156)074-6837', '123-45-0004', '0000000006', '1985-01-13', '00408027', 'Y', 776),
(5,  'Treva',    'Manley',   'Schowalter',  '5653 Legros Plaza',     'Apt. 968',  'Alvinaport',        'MI', 'USA', '02251-1698', '(978)775-4633', '(439)943-7644', '123-45-0005', '0000000006', '1971-09-29', '00063655', 'Y', 529),
(6,  'Layne',    'Isidro',   'Rempel',      '461 Pollich Harbors',   'Suite 231', 'Vandervortview',    'TX', 'USA', '71104-3302', '(802)561-2782', '(773)419-4810', '123-45-0006', '0000000004', '1963-04-06', '00003641', 'Y', 413),
(7,  'Carter',   'Reece',    'Veum',        '22 Josianne Cliffs',    'Apt. 181',  'Lindgrenfort',      'OH', 'USA', '38804',      '(260)427-1218', '(491)726-1745', '123-45-0007', '0000000003', '1972-04-25', '00002000', 'Y', 665),
(8,  'Maci',     'Thelma',   'Robel',       '44 Renner Point',       'Apt. 301',  'Hyattstad',         'WA', 'USA', '71302-2107', '(929)826-3060', '(447)651-8093', '123-45-0008', '0000000004', '1979-04-25', '00001207', 'Y', 612),
(9,  'Aniya',    'Toni',     'Von',         '3568 Gino Valley',      'Apt. 562',  'Wolfhaven',         'IL', 'USA', '53219',      '(321)478-9012', '(312)555-7890', '123-45-0009', '0000000005', '1966-08-15', '00005037', 'Y', 720),
(10, 'Ward',     'James',    'Jones',       '8102 Moen Shoal',       'Suite 100', 'Beahanland',        'NY', 'USA', '10001',      '(212)555-1234', '(718)555-9876', '123-45-0010', '0000000002', '1958-03-22', '00002756', 'Y', 698)
ON CONFLICT (customer_id) DO NOTHING;

-- Account-Customer cross-reference
INSERT INTO account_customer_xref (account_id, customer_id) VALUES
(1,  1), (2,  2), (3,  3), (4,  4), (5,  5),
(6,  6), (7,  7), (8,  8), (9,  9), (10, 10)
ON CONFLICT (account_id, customer_id) DO NOTHING;

-- Credit cards (from carddata.txt — 12 records)
INSERT INTO credit_cards (card_number, account_id, customer_id, card_embossed_name, expiration_date, expiration_day, active_status) VALUES
('0500024453765740', 5,  9,  'ANIYA VON',        '2023-03-09', 9,  'Y'),
('0683586198171516', 27, 2,  'WARD JONES',       '2025-07-13', 13, 'Y'),
('0923877193247330', 2,  2,  'ENRICO ROSENBAUM', '2024-08-11', 11, 'Y'),
('0927987108636232', 20, 7,  'CARTER VEUM',      '2024-03-13', 13, 'Y'),
('0982496213629795', 12, 8,  'MACI ROBEL',       '2023-07-07', 7,  'Y'),
('4185540994448062', 1,  1,  'IMMANUEL KESSLER', '2025-05-20', 20, 'Y'),
('4264892346131733', 3,  3,  'LARRY HOMENICK',   '2024-01-10', 10, 'Y'),
('4320958977897614', 4,  4,  'DELBERT PARISIAN', '2023-12-16', 16, 'Y'),
('4422516614428000', 6,  6,  'LAYNE REMPEL',     '2024-07-24', 24, 'Y'),
('4625037159926401', 7,  7,  'CARTER VEUM',      '2024-03-07', 7,  'Y'),
('4813498445797307', 8,  8,  'MACI ROBEL',       '2023-10-19', 19, 'N'),
('4916483237855543', 10, 10, 'WARD JONES',       '2025-02-14', 14, 'Y')
ON CONFLICT (card_number) DO NOTHING;

-- Card-Account-Customer cross-reference (CARDXREF VSAM KSDS)
INSERT INTO card_account_xref (card_number, customer_id, account_id) VALUES
('0500024453765740', 9,  5),
('0683586198171516', 2,  27),
('0923877193247330', 2,  2),
('0927987108636232', 7,  20),
('0982496213629795', 8,  12),
('4185540994448062', 1,  1),
('4264892346131733', 3,  3),
('4320958977897614', 4,  4),
('4422516614428000', 6,  6),
('4625037159926401', 7,  7),
('4813498445797307', 8,  8),
('4916483237855543', 10, 10)
ON CONFLICT (card_number) DO NOTHING;
