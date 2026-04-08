-- =============================================================================
-- CardDemo Seed Data
-- Parsed from app/data/ASCII/ flat files (original VSAM data in ASCII format)
--
-- Password notes:
--   All users seeded with password 'Admin123' (bcrypt hash below)
--   Original COBOL stored plaintext in SEC-USR-PWD PIC X(08)
--   Hash: $2b$12$RX0v1cpvzt2.yV8wk8bsput3TaI5Efdpqa/qk5MT6.fCZ4C.xMR1O
-- =============================================================================

-- -------------------------------------------------------------------------
-- TRANSACTION TYPES (from trantype.txt + CARDDEMO.TRANSACTION_TYPE DB2 table)
-- Format: type_cd (2 chars), description (50 chars), filler (8 chars)
-- -------------------------------------------------------------------------
INSERT INTO transaction_types (type_cd, description) VALUES
  ('01', 'Purchase'),
  ('02', 'Payment'),
  ('03', 'Credit'),
  ('04', 'Authorization'),
  ('05', 'Refund'),
  ('06', 'Reversal'),
  ('07', 'Adjustment')
ON CONFLICT (type_cd) DO NOTHING;

-- -------------------------------------------------------------------------
-- TRANSACTION TYPE CATEGORIES (from trancatg.txt)
-- Format: type_cd(2) + cat_cd(4) + description(50) + filler(4)
-- -------------------------------------------------------------------------
INSERT INTO transaction_type_categories (type_cd, category_cd, description) VALUES
  ('01', 1, 'Regular Sales Draft'),
  ('01', 2, 'Regular Cash Advance'),
  ('01', 3, 'Convenience Check Debit'),
  ('01', 4, 'ATM Cash Advance'),
  ('01', 5, 'Interest Amount'),
  ('02', 1, 'Cash payment'),
  ('02', 2, 'Electronic payment'),
  ('02', 3, 'Check payment'),
  ('03', 1, 'Credit to Account'),
  ('03', 2, 'Credit to Purchase balance'),
  ('03', 3, 'Credit to Cash balance'),
  ('04', 1, 'Zero dollar authorization'),
  ('04', 2, 'Online purchase authorization'),
  ('04', 3, 'Travel booking authorization'),
  ('05', 1, 'Refund credit'),
  ('06', 1, 'Fraud reversal'),
  ('06', 2, 'Non-fraud reversal'),
  ('07', 1, 'Sales draft credit adjustment')
ON CONFLICT (type_cd, category_cd) DO NOTHING;

-- -------------------------------------------------------------------------
-- USERS (USRSEC VSAM — SEC-USER-DATA from CSUSR01Y.cpy)
-- SEC-USR-ID PIC X(08) — trailing spaces removed for modern usage
-- Plain-text passwords (for dev/test only):
--   ADMIN    → Admin123
--   USER0001 → User0001
--   USER0002 → User0002
--   USER0003 → User0003
--   SADM     → Sadm1234
--   COADM01  → Coadm101
-- -------------------------------------------------------------------------
INSERT INTO users (user_id, first_name, last_name, password_hash, user_type) VALUES
  ('ADMIN',    'System',   'Admin',   '$2b$12$2RECWp1oSgCHFXQTrprdJu5mQYKkQy/kuf3hdLVoE9jsGI9DDYjPC', 'A'),
  ('USER0001', 'John',     'Doe',     '$2b$12$sVQTU297miGVmxkSSr4AsOV4YiI6yM3aYzk/n/w3jXMlc0YV6WF2W', 'U'),
  ('USER0002', 'Jane',     'Smith',   '$2b$12$gJhhmgTk54V0ay1O5JoHjeGvnvkVn1/Q8Sis/3PV4dWyL6dfTNXp2', 'U'),
  ('USER0003', 'Bob',      'Johnson', '$2b$12$RNWqWNxqrQ62dZwf3tS/t.wsZFExo7Q3bPvBPRZK/YmXh7E2a.CUG', 'U'),
  ('SADM',     'Super',    'Admin',   '$2b$12$Kyh2YQJAcoZ.9ChEecAKPe4u3eAALpchVtIxP8hMbKQexBeic3QL2', 'A'),
  ('COADM01',  'Card',     'Admin',   '$2b$12$UU52kqsiO3E4wHTBb7XqYux4Qx5ExL.iN0HCf.iQATHBMpfW1NPR2', 'A')
ON CONFLICT (user_id) DO NOTHING;

-- -------------------------------------------------------------------------
-- ACCOUNTS (from acctdata.txt — 15 rows)
-- Parsed from VSAM KSDS with overpunch sign notation
-- ACCT-ID PIC 9(11), ACCT-ACTIVE-STATUS PIC X(01), monetary PIC S9(10)V99 COMP-3
-- ACCT-GROUP-ID = 'A000000000' for all records in seed data
-- -------------------------------------------------------------------------
INSERT INTO accounts (acct_id, active_status, curr_bal, credit_limit, cash_credit_limit,
                      open_date, expiration_date, reissue_date, curr_cycle_credit, curr_cycle_debit,
                      addr_zip, group_id) VALUES
  (10000000001,  'Y',  194.00,  2020.00,  1020.00, '2014-11-20', '2025-05-20', '2025-05-20', 0.00, 0.00, NULL, 'A000000000'),
  (10000000002,  'Y',  158.00,  6130.00,  5448.00, '2013-06-19', '2024-08-11', '2024-08-11', 0.00, 0.00, NULL, 'A000000000'),
  (10000000003,  'Y',  147.00,  4909.00,   538.00, '2013-08-23', '2024-01-10', '2024-01-10', 0.00, 0.00, NULL, 'A000000000'),
  (10000000004,  'Y',   40.00,  3503.00,  2789.00, '2012-11-17', '2023-12-16', '2023-12-16', 0.00, 0.00, NULL, 'A000000000'),
  (10000000005,  'Y',  345.00,  3819.00,  2430.00, '2012-10-03', '2025-03-09', '2025-03-09', 0.00, 0.00, NULL, 'A000000000'),
  (10000000006,  'Y',  218.00,  3584.00,  2948.00, '2017-12-23', '2025-10-08', '2025-10-08', 0.00, 0.00, NULL, 'A000000000'),
  (10000000007,  'Y',  193.00,  2065.00,   264.00, '2012-10-12', '2024-12-13', '2024-12-13', 0.00, 0.00, NULL, 'A000000000'),
  (10000000008,  'Y',  605.00,  6104.00,  1318.00, '2012-01-04', '2024-05-20', '2024-05-20', 0.00, 0.00, NULL, 'A000000000'),
  (10000000009,  'Y',  560.00,  8201.00,  2065.00, '2016-08-27', '2024-12-27', '2024-12-27', 0.00, 0.00, NULL, 'A000000000'),
  (10000000010, 'Y',  159.00,  5401.00,  4442.00, '2015-09-13', '2023-01-27', '2023-01-27', 0.00, 0.00, NULL, 'A000000000'),
  (10000000011, 'Y',  212.00,  4998.00,  3175.00, '2014-09-12', '2025-03-12', '2025-03-12', 0.00, 0.00, NULL, 'A000000000'),
  (10000000012, 'Y',  176.00,  4636.00,   388.00, '2009-06-17', '2023-07-07', '2023-07-07', 0.00, 0.00, NULL, 'A000000000'),
  (10000000013, 'Y',   41.00,  7542.00,  4922.00, '2017-10-01', '2024-08-04', '2024-08-04', 0.00, 0.00, NULL, 'A000000000'),
  (10000000014, 'Y',   15.00,  2254.00,   212.00, '2010-12-04', '2025-12-11', '2025-12-11', 0.00, 0.00, NULL, 'A000000000'),
  (10000000015, 'Y',  489.00,  8441.00,  3833.00, '2009-10-06', '2025-06-09', '2025-06-09', 0.00, 0.00, NULL, 'A000000000'),
  (10000000020, 'Y',  320.00,  5000.00,  2000.00, '2015-03-01', '2025-03-01', '2025-03-01', 0.00, 0.00, NULL, 'A000000000'),
  (10000000022, 'Y',  450.00,  7000.00,  3000.00, '2014-07-15', '2024-07-15', '2024-07-15', 0.00, 0.00, NULL, 'A000000000'),
  (10000000024, 'Y',   89.00,  3000.00,  1500.00, '2016-02-20', '2024-02-20', '2024-02-20', 0.00, 0.00, NULL, 'A000000000'),
  (10000000027, 'Y',  712.00,  9000.00,  4500.00, '2011-05-10', '2025-05-10', '2025-05-10', 0.00, 0.00, NULL, 'A000000000'),
  (10000000035, 'Y',  234.00,  4000.00,  2000.00, '2013-09-05', '2025-09-05', '2025-09-05', 0.00, 0.00, NULL, 'A000000000')
ON CONFLICT (acct_id) DO NOTHING;

-- -------------------------------------------------------------------------
-- CUSTOMERS (from custdata.txt — first 15 rows)
-- CUST-ID PIC 9(09), CUST-SSN PIC 9(09) [sensitive]
-- -------------------------------------------------------------------------
INSERT INTO customers (cust_id, first_name, middle_name, last_name,
                       addr_line_1, addr_line_2, addr_line_3,
                       addr_state_cd, addr_country_cd, addr_zip,
                       phone_num_1, phone_num_2, ssn, govt_issued_id, dob,
                       eft_account_id, pri_card_holder_ind, fico_credit_score) VALUES
  (1,'Immanuel','Madeline','Kessler','618 Deshaun Route','Apt. 802','Altenwerthshire','NC','USA','12546','(908)119-8310','(373)693-8684',20973888,'00000000000049368437','1961-06-08','0053581756','Y',350),
  (2,'Enrico','April','Rosenbaum','4917 Myrna Flats','Apt. 453','West Bernita','IN','USA','22770','(429)706-9510','(744)950-5272',587518382,'00000000000506210371','1961-10-08','0069194009','Y',340),
  (3,'Larry','Cody','Homenick','362 Esta Parks','Apt. 390','New Gladys','GA','USA','19852-6716','(950)396-9024','(685)168-8826',317460867,'00000000000052419303','1987-11-30','0006465789','Y',616),
  (4,'Delbert','Kaia','Parisian','638 Blanda Gateway','Apt. 076','Lake Virginie','MI','USA','39035-0455','(801)603-4121','(156)074-6837',660354258,'00000000000068579249','1985-01-13','0040802739','Y',776),
  (5,'Treva','Manley','Schowalter','5653 Legros Plaza','Apt. 968','Alvinaport','MI','USA','02251-1698','(978)775-4633','(439)943-7644',611264288,'00000000000639799754','1971-09-29','0006365573','Y',529),
  (6,'Ignacio','Emery','Douglas','3963 Yasmin Port','Suite 756','Port Josephstad','VI','USA','46713-5148','(277)743-4266','(519)010-8739',880329521,'00000000000975535496','1994-11-29','0067163009','Y',753),
  (7,'Cooper','Dennis','Mayert','6490 Zakary Locks','Apt. 765','Madieport','AL','USA','34206-2974','(698)282-4096','(458)199-0016',835138951,'00000000000959013170','1977-05-06','0024571415','Y',499),
  (8,'Kelsie','Jordyn','Dicki','0925 Welch Streets','Apt. 152','North Nanniestad','SC','USA','27610','(345)563-7159','(443)197-1271',295270759,'00000000000109746991','1964-03-25','0033132723','Y',300),
  (9,'Melvin','Regan','Ondricka','87893 Samson Flats','Apt. 135','New Braden','VI','USA','21113','(035)456-1404','(412)440-3130',842035847,'00000000000568299451','1975-11-07','0039446039','Y',699),
  (10,'Maybell','Creola','Mann','77933 Adah Dale','Suite 343','Andersonfurt','CT','USA','44803-4279','(614)594-2619','(667)057-0235',754755746,'00000000000212824755','1980-06-11','0093803568','Y',476),
  (11,'Hayden','Ressie','Pfannerstill','14895 Everette Ridges','Apt. 443','Julianneburgh','WA','USA','24984','(002)533-6980','(553)586-7718',493538586,'00000000000111190855','1986-11-03','0002650577','Y',300),
  (12,'Maci','Alan','Robel','80501 Isac Cliffs','Suite 623','Predovicton','MN','USA','78861','(584)045-5200','(610)244-0407',666114218,'00000000000902143351','1984-02-18','0061317348','Y',688),
  (13,'Mariane','Oma','Fadel','2689 Derick Mission','Suite 055','Bruenfurt','OR','USA','02322','(875)943-7287','(075)550-6435',757924569,'00000000000181377220','1999-03-09','0044807431','Y',300),
  (14,'Chelsea','Ignacio','Marks','747 Dino Lodge','Apt. 850','West Chase','RI','USA','12914-8465','(141)807-6571','(284)088-9052',655128548,'00000000000525955222','1974-11-29','0048306401','Y',300),
  (15,'Aubree','Elliot','Hermann','36365 Ledner Drives','Suite 882','Port Efrainland','DE','USA','63205-7014','(769)100-7971','(366)310-2061',33922034,'00000000000230369941','1964-12-06','0000634612','Y',681),
  (20,'Carter','Alex','Veum','1234 Main Street','Apt. 100','Springfield','IL','USA','62701','(217)555-0100','(217)555-0101',123456789,'00000000000012345678','1980-01-15','0012345678','Y',720),
  (22,'Allene','Beth','Brown','5678 Oak Avenue','Suite 200','Shelbyville','TN','USA','37160','(615)555-0200','(615)555-0201',234567890,'00000000000023456789','1975-06-20','0023456789','Y',650),
  (24,'Stefanie','Kay','Dickinson','9012 Pine Road','Apt. 300','Capital City','CA','USA','90001','(310)555-0300','(310)555-0301',345678901,'00000000000034567890','1990-11-25','0034567890','Y',710),
  (27,'Ward','James','Jones','3456 Elm Street','Suite 400','Metropolis','NY','USA','10001','(212)555-0400','(212)555-0401',456789012,'00000000000045678901','1965-03-08','0045678901','Y',800),
  (35,'Angelica','Rose','Dach','7890 Maple Drive','Apt. 500','Gotham','NJ','USA','07001','(201)555-0500','(201)555-0501',567890123,'00000000000056789012','1982-09-14','0056789012','Y',690)
ON CONFLICT (cust_id) DO NOTHING;

-- -------------------------------------------------------------------------
-- CARDS (from carddata.txt — 15 rows)
-- CARD-NUM PIC X(16), CARD-ACCT-ID PIC 9(11), CARD-CVV-CD PIC 9(03)
-- -------------------------------------------------------------------------
INSERT INTO cards (card_num, acct_id, cvv_cd, embossed_name, expiration_date, active_status) VALUES
  ('0500024453765740', 10000000015,  747, 'Aniya Von',          '2023-03-09', 'Y'),
  ('0683586198171516', 10000000027,  567, 'Ward Jones',          '2025-07-13', 'Y'),
  ('0923877193247330', 10000000002,   28, 'Enrico Rosenbaum',    '2024-08-11', 'Y'),
  ('0927987108636232', 10000000020,    3, 'Carter Veum',         '2024-03-13', 'Y'),
  ('0982496213629795', 10000000012,   75, 'Maci Robel',          '2023-07-07', 'Y'),
  ('2871968252812490', 10000000006,  775, 'Ignacio Douglas',     '2025-10-08', 'Y'),
  ('2988091353094312', 10000000004,  795, 'Delbert Parisian',    '2023-12-16', 'Y'),
  ('3260763612337560', 10000000010,  342, 'Maybell Mann',        '2023-01-27', 'Y'),
  ('2940139362300449', 10000000022,  876, 'Allene Brown',        '2025-12-28', 'Y'),
  ('2760836797107565', 10000000024,  859, 'Stefanie Dickinson',  '2025-02-11', 'Y'),
  ('1561409106491600', 10000000035,   31, 'Angelica Dach',       '2025-09-23', 'Y'),
  ('0100000011111111', 10000000001,  123, 'Immanuel Kessler',    '2025-11-01', 'Y'),
  ('0200000022222222', 10000000002,  456, 'Enrico Rosenbaum',    '2025-08-01', 'Y'),
  ('0030000003333333', 10000000003,  789, 'Larry Homenick',      '2025-01-10', 'Y'),
  ('0050000005555555', 10000000005,  321, 'Treva Schowalter',    '2025-03-09', 'Y')
ON CONFLICT (card_num) DO NOTHING;

-- -------------------------------------------------------------------------
-- CARD XREF (from cardxref.txt — matches card-to-customer-to-account)
-- XREF-CARD-NUM PIC X(16), XREF-CUST-ID PIC 9(09), XREF-ACCT-ID PIC 9(11)
-- -------------------------------------------------------------------------
INSERT INTO card_xref (card_num, cust_id, acct_id) VALUES
  ('0500024453765740', 15, 10000000015),
  ('0683586198171516', 27, 10000000027),
  ('0923877193247330',  2,  10000000002),
  ('0927987108636232', 20, 10000000020),
  ('0982496213629795', 12, 10000000012),
  ('2871968252812490',  6,  10000000006),
  ('2988091353094312',  4,  10000000004),
  ('3260763612337560', 10, 10000000010),
  ('2940139362300449', 22, 10000000022),
  ('2760836797107565', 24, 10000000024),
  ('1561409106491600', 35, 10000000035),
  ('0100000011111111',  1,  10000000001),
  ('0200000022222222',  2,  10000000002),
  ('0030000003333333',  3,  10000000003),
  ('0050000005555555',  5,  10000000005)
ON CONFLICT (card_num) DO NOTHING;

-- -------------------------------------------------------------------------
-- TRANSACTIONS (from dailytran.txt — first 15 rows)
-- TRAN-ID PIC X(16), amounts decoded from overpunch notation
-- Note: Only insert transactions where card_num exists in cards table
-- -------------------------------------------------------------------------
INSERT INTO transactions (tran_id, type_cd, cat_cd, source, description, amount,
                          merchant_id, merchant_name, merchant_city, merchant_zip,
                          card_num, acct_id, orig_ts, proc_ts) VALUES
  ('0000000001774260', '03', 1, 'OPERATOR',  'Return item at Nitzsche, Nicolas and Lowe', -919.00,  800000000, 'Nitzsche, Nicolas and Lowe',            'Fidelshire',           '53378',     '0927987108636232', 10000000020, '2022-06-10 19:27:53.000000', '2022-06-10 19:27:53.000000'),
  ('0000000010142252', '01', 1, 'POS TERM',  'Purchase at Kertzmann-Schoen',               454.66,  800000000, 'Kertzmann-Schoen',                      'East Eulahstad',       '98754-1089', NULL,                NULL,'2022-06-10 19:27:53.000000', '2022-06-10 19:27:53.000000'),
  ('0000000025430891', '01', 1, 'POS TERM',  'Purchase at Beatty-Hessel',                   94.33,  800000000, 'Beatty-Hessel',                         'Simonisport',          '52595',     '3260763612337560', 10000000010, '2022-06-10 19:27:53.000000', '2022-06-10 19:27:53.000000'),
  ('0000000030755266', '01', 1, 'POS TERM',  'Purchase at Ratke LLC',                      829.55,  800000000, 'Ratke LLC',                             'Brendenfort',          '35302-6495', NULL,                NULL,'2022-06-10 19:27:53.000000', '2022-06-10 19:27:53.000000'),
  ('0000000033688127', '01', 1, 'POS TERM',  'Purchase at Schinner-Steuber',               958.99,  800000000, 'Schinner-Steuber',                      'Schmittchester',       '50777-5535', NULL,                NULL,'2022-06-10 19:27:53.000000', '2022-06-10 19:27:53.000000'),
  ('0000000040000001', '01', 1, 'POS TERM',  'Purchase at Acme Store',                     125.50,  100000001, 'Acme Store',                            'New York',             '10001',     '0100000011111111', 10000000001, '2022-06-11 10:00:00.000000', '2022-06-11 10:00:00.000000'),
  ('0000000040000002', '02', 1, 'PAYMENT',   'Monthly Payment',                            100.00,  100000001, 'CardDemo Payment Center',               'Anytown',              '12345',     '0200000022222222', 10000000002, '2022-06-12 09:00:00.000000', '2022-06-12 09:00:00.000000'),
  ('0000000040000003', '01', 1, 'POS TERM',  'Purchase at Tech Shop',                      299.99,  100000002, 'Tech Shop',                             'San Jose',             '95101',     '0030000003333333', 10000000003, '2022-06-13 14:30:00.000000', '2022-06-13 14:30:00.000000'),
  ('0000000040000004', '05', 1, 'REFUND',    'Refund from Tech Shop',                      -49.99,  100000002, 'Tech Shop',                             'San Jose',             '95101',     '0030000003333333', 10000000003, '2022-06-14 11:00:00.000000', '2022-06-14 11:00:00.000000'),
  ('0000000040000005', '01', 2, 'ATM',       'ATM Cash Advance',                           200.00,  100000003, 'First National Bank ATM',               'Chicago',              '60601',     '0050000005555555', 10000000005, '2022-06-15 16:00:00.000000', '2022-06-15 16:00:00.000000'),
  ('0000000040000006', '01', 1, 'POS TERM',  'Purchase at Gas Station',                     45.23,  100000004, 'Sunoco Gas',                            'Houston',              '77001',     '2988091353094312', 10000000004, '2022-06-16 08:15:00.000000', '2022-06-16 08:15:00.000000'),
  ('0000000040000007', '01', 1, 'POS TERM',  'Purchase at Grocery Store',                  132.67,  100000005, 'Whole Foods Market',                    'Austin',               '78701',     '0982496213629795', 10000000012, '2022-06-17 18:45:00.000000', '2022-06-17 18:45:00.000000'),
  ('0000000040000008', '03', 1, 'CREDIT',    'Cashback Credit',                             10.00,  100000006, 'CardDemo Rewards',                      'Anytown',              '12345',     '2871968252812490', 10000000006, '2022-06-18 00:00:00.000000', '2022-06-18 00:00:00.000000'),
  ('0000000040000009', '02', 2, 'PAYMENT',   'Electronic payment',                         250.00,  100000007, 'CardDemo Payment Center',               'Anytown',              '12345',     '2940139362300449', 10000000022, '2022-06-19 09:30:00.000000', '2022-06-19 09:30:00.000000'),
  ('0000000040000010', '07', 1, 'ADJUST',    'Balance adjustment',                          -5.00,  100000008, 'CardDemo Adjustments',                  'Anytown',              '12345',     '3260763612337560', 10000000010, '2022-06-20 12:00:00.000000', '2022-06-20 12:00:00.000000')
ON CONFLICT (tran_id) DO NOTHING;

-- -------------------------------------------------------------------------
-- DISCLOSURE GROUPS (from discgrp.txt — interest rates by group/type/category)
-- DIS-ACCT-GROUP-ID PIC X(10), DIS-INT-RATE PIC S9(04)V99 (annual %)
-- -------------------------------------------------------------------------
INSERT INTO disclosure_groups (group_id, type_cd, cat_cd, interest_rate) VALUES
  ('A000000000', '01', 1, 15.00),
  ('A000000000', '01', 2, 25.00),
  ('A000000000', '01', 3, 25.00),
  ('A000000000', '01', 4, 25.00),
  ('A000000000', '02', 1,  0.00),
  ('A000000000', '02', 2,  0.00),
  ('A000000000', '02', 3,  0.00),
  ('A000000000', '03', 1,  0.00),
  ('A000000000', '03', 2,  0.00),
  ('A000000000', '03', 3,  0.00),
  ('A000000000', '04', 1, 15.00),
  ('A000000000', '04', 2, 15.00),
  ('A000000000', '04', 3, 15.00),
  ('A000000000', '05', 1, 15.00),
  ('A000000000', '06', 1, 15.00),
  ('A000000000', '06', 2, 15.00),
  ('A000000000', '07', 1, 15.00),
  ('DEFAULT',    '01', 1, 15.00),
  ('DEFAULT',    '01', 2, 25.00),
  ('DEFAULT',    '01', 3, 25.00)
ON CONFLICT (group_id, type_cd, cat_cd) DO NOTHING;

-- -------------------------------------------------------------------------
-- TRAN_CAT_BALANCES (from tcatbal.txt — balances per account/type/category)
-- Composite key: (acct_id, type_cd, cat_cd)
-- -------------------------------------------------------------------------
INSERT INTO tran_cat_balances (acct_id, type_cd, cat_cd, balance) VALUES
  (10000000001,  '01', 1, 0.00),
  (10000000002,  '01', 1, 0.00),
  (10000000003,  '01', 1, 0.00),
  (10000000004,  '01', 1, 0.00),
  (10000000005,  '01', 1, 0.00),
  (10000000006,  '01', 1, 0.00),
  (10000000007,  '01', 1, 0.00),
  (10000000008,  '01', 1, 0.00),
  (10000000009,  '01', 1, 0.00),
  (10000000010, '01', 1, 0.00),
  (10000000001,  '02', 1, 0.00),
  (10000000002,  '02', 1, 0.00),
  (10000000003,  '02', 1, 0.00),
  (10000000004,  '01', 2, 0.00),
  (10000000005,  '01', 2, 0.00)
ON CONFLICT (acct_id, type_cd, cat_cd) DO NOTHING;

-- =============================================================================
-- Phase 3: Authorization Module Seed Data
-- Sources: COPAUA0C / COPAUS0C / COPAUS1C / COPAUS2C
-- =============================================================================

-- AUTH_SUMMARIES (replaces IMS PAUTSUM0 root segment)
-- credit_balance = sum of approved amounts to date (COPAUA0C 8400-UPDATE-SUMMARY)
INSERT INTO auth_summaries
  (acct_id, cust_id, auth_status, credit_limit, cash_limit,
   credit_balance, cash_balance, approved_auth_cnt, declined_auth_cnt,
   approved_auth_amt, declined_auth_amt)
VALUES
  -- Account 1: moderate utilization, 3 approved, 1 declined
  (10000000001, 1, NULL, 2020.00, 1020.00, 350.00, 0.00, 3, 1, 350.00, 150.00),
  -- Account 2: higher utilization
  (10000000002, 2, NULL, 6130.00, 5448.00, 1200.00, 0.00, 5, 2, 1200.00, 800.00),
  -- Account 3: zero balance, no auths yet
  (10000000003, 3, NULL, 1500.00, 500.00, 0.00, 0.00, 0, 0, 0.00, 0.00),
  -- Account 4: high utilization
  (10000000004, 4, NULL, 3000.00, 1000.00, 2800.00, 0.00, 10, 3, 2800.00, 500.00),
  -- Account 5: recently closed / inactive
  (10000000005, 5, NULL, 5000.00, 2000.00, 100.00, 0.00, 1, 0, 100.00, 0.00)
ON CONFLICT (acct_id) DO NOTHING;


-- AUTH_DETAILS (replaces IMS PAUTDTL1 child segment)
-- auth_date_9c = 99999 - YYDDD, auth_time_9c = 999999999 - HHMMSSMMM
-- match_status: P=Pending, D=Declined, E=Expired, M=Matched
INSERT INTO auth_details
  (acct_id, auth_date_9c, auth_time_9c, auth_orig_date, auth_orig_time,
   card_num, auth_type, card_expiry_date, message_type, message_source,
   auth_id_code, auth_resp_code, auth_resp_reason,
   processing_code, transaction_amt, approved_amt,
   merchant_category_code, acqr_country_code, pos_entry_mode,
   merchant_id, merchant_name, merchant_city, merchant_state, merchant_zip,
   transaction_id, match_status, auth_fraud, fraud_rpt_date)
VALUES
  -- Account 1: approved grocery purchase
  (10000000001, 99500, 999000000, '260325', '091500',
   '0100000011111111', 'PUR ', '1125', '0100  ', 'POS   ',
   '091500', '00', '0000',
   0, 150.00, 150.00,
   '5411', '840', 5,
   'WALMART001     ', 'WALMART SUPERCENTER   ', 'BENTONVILLE  ', 'AR', '727160001',
   'TXN260325091500', 'M', NULL, NULL),

  -- Account 1: approved gas station
  (10000000001, 99498, 998500000, '260326', '143000',
   '0100000011111111', 'PUR ', '1125', '0100  ', 'POS   ',
   '143000', '00', '0000',
   0, 75.00, 75.00,
   '5541', '840', 5,
   'EXXON00001     ', 'EXXON MOBIL          ', 'DALLAS       ', 'TX', '752010001',
   'TXN260326143000', 'P', NULL, NULL),

  -- Account 1: declined insufficient funds
  (10000000001, 99496, 997000000, '260327', '180000',
   '0100000011111111', 'PUR ', '1125', '0100  ', 'POS   ',
   '180000', '05', '4100',
   0, 2000.00, 0.00,
   '5812', '840', 1,
   'RESTAURANT01   ', 'FANCY RESTAURANT     ', 'NEW YORK     ', 'NY', '100010001',
   'TXN260327180000', 'D', NULL, NULL),

  -- Account 1: approved online purchase, fraud reported
  (10000000001, 99494, 996000000, '260328', '220000',
   '0100000011111111', 'PUR ', '1125', '0110  ', 'ONLINE',
   '220000', '00', '0000',
   0, 125.00, 125.00,
   '5734', '840', 81,
   'AMAZON00001    ', 'AMAZON.COM           ', 'SEATTLE      ', 'WA', '981010001',
   'TXN260328220000', 'P', 'F', '03/28/26'),

  -- Account 2: approved department store
  (10000000002, 99492, 995000000, '260329', '120000',
   '0100000022222222', 'PUR ', '1224', '0100  ', 'POS   ',
   '120000', '00', '0000',
   0, 500.00, 500.00,
   '5311', '840', 5,
   'NORDSTROM01    ', 'NORDSTROM            ', 'SEATTLE      ', 'WA', '981010002',
   'TXN260329120000', 'P', NULL, NULL),

  -- Account 2: declined card not active
  (10000000002, 99490, 994500000, '260330', '090000',
   '0100000022222222', 'PUR ', '1224', '0100  ', 'POS   ',
   '090000', '05', '4200',
   0, 300.00, 0.00,
   '5999', '840', 5,
   'MISC0000001    ', 'MISC MERCHANT        ', 'CHICAGO      ', 'IL', '606010001',
   'TXN260330090000', 'D', NULL, NULL),

  -- Account 3: no authorizations yet — no rows inserted

  -- Account 4: approved hotel
  (10000000004, 99488, 993000000, '260331', '150000',
   '0100000044444444', 'PUR ', '1226', '0100  ', 'POS   ',
   '150000', '00', '0000',
   0, 450.00, 450.00,
   '7011', '840', 5,
   'HILTON000001   ', 'HILTON HOTELS        ', 'LAS VEGAS    ', 'NV', '891010001',
   'TXN260331150000', 'P', NULL, NULL),

  -- Account 4: approved airline
  (10000000004, 99486, 992000000, '260331', '163000',
   '0100000044444444', 'PUR ', '1226', '0110  ', 'ONLINE',
   '163000', '00', '0000',
   0, 800.00, 800.00,
   '4511', '840', 81,
   'DELTA00000001  ', 'DELTA AIR LINES      ', 'ATLANTA      ', 'GA', '303010001',
   'TXN260331163000', 'E', NULL, NULL),

  -- Account 4: declined over limit
  (10000000004, 99484, 991000000, '260331', '180000',
   '0100000044444444', 'PUR ', '1226', '0100  ', 'POS   ',
   '180000', '05', '4100',
   0, 1000.00, 0.00,
   '5311', '840', 5,
   'MACY000000001  ', 'MACY''S DEPARTMENT    ', 'NEW YORK     ', 'NY', '100110001',
   'TXN260331180000', 'D', NULL, NULL),

  -- Account 5: single approved transaction
  (10000000005, 99482, 990000000, '260330', '100000',
   '0100000055555555', 'PUR ', '1126', '0100  ', 'POS   ',
   '100000', '00', '0000',
   0, 100.00, 100.00,
   '5411', '840', 5,
   'KROGER0000001  ', 'KROGER GROCERY       ', 'CINCINNATI   ', 'OH', '452010001',
   'TXN260330100000', 'M', NULL, NULL)
ON CONFLICT DO NOTHING;


-- AUTH_FRAUD_RECORDS (DB2 CARDDEMO.AUTHFRDS — COPAUS2C)
-- Populated when user marks auth as fraud via COPAUS1C PF5
INSERT INTO auth_fraud_records
  (card_num, auth_ts, auth_type, card_expiry_date, message_type, message_source,
   auth_id_code, auth_resp_code, auth_resp_reason,
   processing_code, transaction_amt, approved_amt,
   merchant_category_code, acqr_country_code, pos_entry_mode,
   merchant_id, merchant_name, merchant_city, merchant_state, merchant_zip,
   transaction_id, match_status, auth_fraud, fraud_rpt_date,
   acct_id, cust_id)
VALUES
  -- Fraud-flagged online Amazon purchase (account 1)
  ('0100000011111111', '26-03-28 22.00.00000000',
   'PUR ', '1125', '0110  ', 'ONLINE',
   '220000', '00', '0000',
   0, 125.00, 125.00,
   '5734', '840', 81,
   'AMAZON00001    ', 'AMAZON.COM           ', 'SEATTLE      ', 'WA', '981010001',
   'TXN260328220000', 'P', 'F', '2026-03-28',
   10000000001, 1)
ON CONFLICT (card_num, auth_ts) DO NOTHING;

-- End of seed data
