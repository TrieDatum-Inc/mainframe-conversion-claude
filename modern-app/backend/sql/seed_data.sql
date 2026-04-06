-- =============================================================================
-- CardDemo Account & Credit Card Module — Seed Data
-- Representative accounts, customers, cards, and cross-references
-- =============================================================================

-- Customers (CUSTDATA VSAM, CVCUS01Y)
INSERT INTO customers (
    customer_id, first_name, middle_name, last_name,
    address_line_1, address_line_2, address_line_3,
    state_code, country_code, zip_code,
    phone_1, phone_2, ssn, govt_issued_id,
    date_of_birth, eft_account_id, primary_card_holder, fico_score
) VALUES
    ('000000001', 'Alice',   'Marie',  'Johnson',
     '123 Main Street', 'Apt 4B', '',
     'TX', 'USA', '75001',
     '(214)555-1234', '(214)555-5678', '123456789', 'TX-DL-99881122',
     '1975-06-15', '0012345678', 'Y', 720),
    ('000000002', 'Robert',  'James',  'Smith',
     '456 Oak Avenue', '', '',
     'CA', 'USA', '90210',
     '(310)555-2345', '', '234567890', 'CA-DL-55443322',
     '1982-03-22', '0023456789', 'Y', 680),
    ('000000003', 'Maria',   'Elena',  'Garcia',
     '789 Elm Drive', 'Suite 100', '',
     'FL', 'USA', '33101',
     '(305)555-3456', '(305)555-6789', '345678901', 'FL-DL-77665544',
     '1990-11-08', '0034567890', 'Y', 760),
    ('000000004', 'David',   'Lee',    'Williams',
     '101 Pine Road', '', '',
     'NY', 'USA', '10001',
     '(212)555-4567', '', '456789012', 'NY-DL-11223344',
     '1968-09-30', '0045678901', 'Y', 640),
    ('000000005', 'Susan',   'Anne',   'Brown',
     '202 Maple Lane', 'PO Box 55', '',
     'IL', 'USA', '60601',
     '(312)555-5678', '(312)555-8901', '567890123', 'IL-DL-44556677',
     '1955-12-25', '0056789012', 'Y', 800),
    ('000000006', 'Michael', 'Thomas', 'Davis',
     '303 Cedar Court', '', '',
     'WA', 'USA', '98101',
     '(206)555-6789', '', '678901234', 'WA-DL-88990011',
     '1978-07-04', '0067890123', 'Y', 700),
    ('000000007', 'Jennifer', 'Lynn', 'Miller',
     '404 Birch Boulevard', 'Apt 12', '',
     'GA', 'USA', '30301',
     '(404)555-7890', '(404)555-0123', '789012345', 'GA-DL-22334455',
     '1995-02-14', '0078901234', 'Y', 710)
ON CONFLICT (customer_id) DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    updated_at = NOW();

-- Accounts (ACCTDATA VSAM, CVACT01Y)
INSERT INTO accounts (
    account_id, active_status,
    current_balance, credit_limit, cash_credit_limit,
    open_date, expiration_date, reissue_date,
    current_cycle_credit, current_cycle_debit,
    address_zip, group_id
) VALUES
    ('00000000001', 'Y', 1250.75,  5000.00,  1500.00,
     '2020-01-15', '2025-01-31', '2022-01-15', 500.00, 1750.75, '75001', 'GOLD01'),
    ('00000000002', 'Y', 3400.00, 10000.00,  2500.00,
     '2019-06-01', '2024-06-30', '2021-06-01', 200.00, 3600.00, '90210', 'PLAT01'),
    ('00000000003', 'Y',  875.50,  7500.00,  2000.00,
     '2021-03-20', '2026-03-31', '2023-03-20', 1000.00, 1875.50, '33101', 'GOLD01'),
    ('00000000004', 'N',    0.00,  2500.00,   500.00,
     '2018-11-10', '2023-11-30', '2020-11-10', 0.00, 0.00, '10001', 'STND01'),
    ('00000000005', 'Y', 9800.00, 25000.00,  5000.00,
     '2015-08-05', '2025-08-31', '2020-08-05', 1500.00, 11300.00, '60601', 'PREM01'),
    ('00000000006', 'Y', 2100.25,  8000.00,  2000.00,
     '2022-05-12', '2027-05-31', '2024-05-12', 300.00, 2400.25, '98101', 'GOLD01'),
    ('00000000007', 'Y',  450.00,  3000.00,   750.00,
     '2023-01-08', '2028-01-31', '2025-01-08', 0.00, 450.00, '30301', 'STND01')
ON CONFLICT (account_id) DO UPDATE SET
    active_status = EXCLUDED.active_status,
    current_balance = EXCLUDED.current_balance,
    updated_at = NOW();

-- Cards (CARDDATA VSAM, CVACT02Y)
INSERT INTO cards (card_number, account_id, cvv_code, embossed_name, expiration_date, active_status)
VALUES
    ('4111111111111001', '00000000001', '123', 'ALICE M JOHNSON',   '2025-01-01', 'Y'),
    ('4111111111111002', '00000000002', '456', 'ROBERT J SMITH',    '2024-06-01', 'Y'),
    ('4111111111111003', '00000000003', '789', 'MARIA E GARCIA',    '2026-03-01', 'Y'),
    ('4111111111111004', '00000000004', '321', 'DAVID L WILLIAMS',  '2023-11-01', 'N'),
    ('4111111111111005', '00000000005', '654', 'SUSAN A BROWN',     '2025-08-01', 'Y'),
    ('4111111111111006', '00000000006', '987', 'MICHAEL T DAVIS',   '2027-05-01', 'Y'),
    ('4111111111111007', '00000000007', '147', 'JENNIFER L MILLER', '2028-01-01', 'Y')
ON CONFLICT (card_number) DO UPDATE SET
    embossed_name = EXCLUDED.embossed_name,
    active_status = EXCLUDED.active_status,
    updated_at = NOW();

-- Card-Xref (CARDXREF VSAM, CVACT03Y)
INSERT INTO card_xref (card_number, customer_id, account_id) VALUES
    ('4111111111111001', '000000001', '00000000001'),
    ('4111111111111002', '000000002', '00000000002'),
    ('4111111111111003', '000000003', '00000000003'),
    ('4111111111111004', '000000004', '00000000004'),
    ('4111111111111005', '000000005', '00000000005'),
    ('4111111111111006', '000000006', '00000000006'),
    ('4111111111111007', '000000007', '00000000007')
ON CONFLICT (card_number) DO NOTHING;

-- =============================================================================
-- CardDemo Transaction Type Module — Seed Data
-- Matches the COBOL COBTUPDT batch reference data
-- =============================================================================

-- Transaction Types
-- These represent the 7 standard card transaction types used in CardDemo
INSERT INTO transaction_types (type_code, description) VALUES
    ('01', 'Purchase'),
    ('02', 'Payment'),
    ('03', 'Credit'),
    ('04', 'Authorization'),
    ('05', 'Refund'),
    ('06', 'Reversal'),
    ('07', 'Adjustment')
ON CONFLICT (type_code) DO UPDATE
    SET description = EXCLUDED.description,
        updated_at  = NOW();

-- Transaction Type Categories
-- Sub-categories per type; mirrors COBOL TRANSACTION_TYPE_CATEGORY rows
INSERT INTO transaction_type_categories (type_code, category_code, description) VALUES
    -- Purchase sub-categories
    ('01', 'RETL', 'Retail Purchase'),
    ('01', 'ONLN', 'Online Purchase'),
    ('01', 'RECU', 'Recurring Purchase'),
    -- Payment sub-categories
    ('02', 'ACH',  'ACH Bank Transfer'),
    ('02', 'CHK',  'Check Payment'),
    -- Credit sub-categories
    ('03', 'PROM', 'Promotional Credit'),
    ('03', 'DISC', 'Discount Credit'),
    -- Authorization sub-categories
    ('04', 'PREH', 'Pre-hold Authorization'),
    ('04', 'INCR', 'Incremental Authorization'),
    -- Refund sub-categories
    ('05', 'FULL', 'Full Refund'),
    ('05', 'PART', 'Partial Refund'),
    -- Reversal sub-categories
    ('06', 'AUTH', 'Authorization Reversal'),
    ('06', 'SALE', 'Sale Reversal'),
    -- Adjustment sub-categories
    ('07', 'FEE',  'Fee Adjustment'),
    ('07', 'INTR', 'Interest Adjustment')
ON CONFLICT (type_code, category_code) DO UPDATE
    SET description = EXCLUDED.description,
        updated_at  = NOW();
