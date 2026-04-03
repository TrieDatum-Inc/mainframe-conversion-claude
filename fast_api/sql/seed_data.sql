-- Seed Data for Account Management Module
-- 5 customers, 5 accounts, 10 cards (2 per account), 10 cross-references

-- Insert customers first (no FK dependencies)
INSERT INTO customers (
    cust_id, cust_first_name, cust_middle_name, cust_last_name,
    cust_addr_line_1, cust_addr_line_2, cust_addr_line_3,
    cust_addr_state_cd, cust_addr_country_cd, cust_addr_zip,
    cust_phone_num_1, cust_phone_num_2,
    cust_ssn, cust_govt_issued_id, cust_dob,
    cust_eft_account_id, cust_pri_card_holder_ind, cust_fico_credit_score
) VALUES
(
    '000000001', 'James', 'Earl', 'Carter',
    '1600 Pennsylvania Ave NW', 'Suite 100', NULL,
    'DC', 'USA', '20500',
    '(202)456-1111', '(202)456-2222',
    '123456789', 'DL-DC-001234', '1960-03-15',
    '1234567890', 'Y', 780
),
(
    '000000002', 'Sarah', 'Ann', 'Mitchell',
    '742 Evergreen Terrace', NULL, NULL,
    'IL', 'USA', '62701',
    '(217)555-0101', '(217)555-0202',
    '234567890', 'DL-IL-002345', '1975-07-22',
    '2345678901', 'Y', 650
),
(
    '000000003', 'Robert', 'Lee', 'Johnson',
    '1 Infinite Loop', 'Building A', 'Floor 3',
    'CA', 'USA', '95014',
    '(408)555-0301', '(408)555-0302',
    '345678901', 'DL-CA-003456', '1982-11-09',
    '3456789012', 'Y', 720
),
(
    '000000004', 'Maria', NULL, 'Garcia',
    '500 Broadway', 'Apt 4B', NULL,
    'NY', 'USA', '10012',
    '(212)555-0401', NULL,
    '456789012', 'PASSPORT-456789', '1990-04-30',
    '4567890123', 'Y', 810
),
(
    '000000005', 'David', 'Michael', 'Thompson',
    '3000 Oak Street', NULL, NULL,
    'TX', 'USA', '78201',
    '(210)555-0501', '(210)555-0502',
    '567890123', 'DL-TX-005678', '1968-08-17',
    '5678901234', 'Y', 590
)
ON CONFLICT (cust_id) DO NOTHING;

-- Insert accounts (no FK dependencies)
INSERT INTO accounts (
    acct_id, acct_active_status, acct_curr_bal,
    acct_credit_limit, acct_cash_credit_limit,
    acct_open_date, acct_expiration_date, acct_reissue_date,
    acct_curr_cyc_credit, acct_curr_cyc_debit,
    acct_addr_zip, acct_group_id
) VALUES
(
    '00000000001', 'Y', 1250.75,
    10000.00, 2000.00,
    '2020-01-15', '2026-01-31', '2024-01-31',
    500.00, 1750.75,
    '20500', 'PREMIUM'
),
(
    '00000000002', 'Y', 3420.50,
    5000.00, 1000.00,
    '2019-06-01', '2025-06-30', '2023-06-30',
    200.00, 3620.50,
    '62701', 'STANDARD'
),
(
    '00000000003', 'Y', 0.00,
    15000.00, 5000.00,
    '2021-03-20', '2027-03-31', '2025-03-31',
    1200.00, 1200.00,
    '95014', 'GOLD'
),
(
    '00000000004', 'N', 8750.25,
    8000.00, 1500.00,
    '2018-09-10', '2024-09-30', '2022-09-30',
    0.00, 8750.25,
    '10012', 'STANDARD'
),
(
    '00000000005', 'Y', 550.00,
    3000.00, 500.00,
    '2022-11-05', '2028-11-30', '2026-11-30',
    100.00, 650.00,
    '78201', 'BASIC'
)
ON CONFLICT (acct_id) DO NOTHING;

-- Insert cards (depend on accounts)
INSERT INTO cards (
    card_num, card_acct_id, card_cvv_cd,
    card_embossed_name, card_expiration_date, card_active_status
) VALUES
('4111111111111001', '00000000001', '123', 'JAMES E CARTER',    '2026-01-31', 'Y'),
('4111111111111002', '00000000001', '456', 'JAMES CARTER JR',   '2026-01-31', 'Y'),
('4111111111112001', '00000000002', '789', 'SARAH A MITCHELL',  '2025-06-30', 'Y'),
('4111111111112002', '00000000002', '321', 'SARAH MITCHELL',    '2025-06-30', 'N'),
('4111111111113001', '00000000003', '654', 'ROBERT L JOHNSON',  '2027-03-31', 'Y'),
('4111111111113002', '00000000003', '987', 'R LEE JOHNSON',     '2027-03-31', 'Y'),
('4111111111114001', '00000000004', '111', 'MARIA GARCIA',      '2024-09-30', 'N'),
('4111111111114002', '00000000004', '222', 'M GARCIA',          '2024-09-30', 'N'),
('4111111111115001', '00000000005', '333', 'DAVID M THOMPSON',  '2028-11-30', 'Y'),
('4111111111115002', '00000000005', '444', 'DAVID THOMPSON',    '2028-11-30', 'Y')
ON CONFLICT (card_num) DO NOTHING;

-- Insert card cross-references (depend on customers, accounts, and cards)
-- Each record links: card_num → cust_id + acct_id
-- This replicates the CXACAIX VSAM alternate index structure
INSERT INTO card_cross_references (xref_card_num, xref_cust_id, xref_acct_id)
VALUES
('4111111111111001', '000000001', '00000000001'),
('4111111111111002', '000000001', '00000000001'),
('4111111111112001', '000000002', '00000000002'),
('4111111111112002', '000000002', '00000000002'),
('4111111111113001', '000000003', '00000000003'),
('4111111111113002', '000000003', '00000000003'),
('4111111111114001', '000000004', '00000000004'),
('4111111111114002', '000000004', '00000000004'),
('4111111111115001', '000000005', '00000000005'),
('4111111111115002', '000000005', '00000000005')
ON CONFLICT (xref_card_num) DO NOTHING;
