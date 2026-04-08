-- =============================================================================
-- CardDemo Batch Pipeline - Sample Data
-- Exercises key business logic paths including edge cases.
-- Run AFTER setup_tables.sql.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Reference / lookup tables
-- ---------------------------------------------------------------------------

INSERT INTO carddemo.transaction_types VALUES
  ('01', 'Purchase'),
  ('02', 'Cash Advance'),
  ('03', 'Balance Transfer'),
  ('04', 'Payment'),
  ('05', 'Interest Charge');

INSERT INTO carddemo.transaction_categories VALUES
  ('01', 1, 'Groceries'),
  ('01', 2, 'Gas / Fuel'),
  ('01', 3, 'Restaurants'),
  ('01', 4, 'Travel'),
  ('01', 5, 'Interest'),
  ('02', 1, 'ATM Withdrawal'),
  ('04', 1, 'Regular Payment');

-- Disclosure groups: DEFAULT fallback + group-specific rates
INSERT INTO carddemo.disclosure_groups VALUES
  ('DEFAULT   ', '01', 1, 18.00),
  ('DEFAULT   ', '01', 2, 21.00),
  ('DEFAULT   ', '01', 3, 15.00),
  ('DEFAULT   ', '02', 1, 24.00),
  ('GOLD      ', '01', 1, 14.99),
  ('GOLD      ', '01', 2, 18.00),
  ('PLATINUM  ', '01', 1, 12.99),
  ('PLATINUM  ', '01', 2, 15.99);

-- ---------------------------------------------------------------------------
-- Customers
-- ---------------------------------------------------------------------------

INSERT INTO carddemo.customers VALUES
  (100000001, 'John', 'A', 'Smith',
   '123 Main Street', 'Apt 4B', 'Seattle',
   'WA', 'USA', '98101-1234',
   '206-555-1234', '206-555-5678',
   123456789, 'DL-WA-12345678', '1975-06-15',
   'CHK-001234', 'Y', 750),
  (100000002, 'Jane', 'M', 'Doe',
   '456 Oak Avenue', '', 'Portland',
   'OR', 'USA', '97201-0001',
   '503-555-9876', '',
   987654321, 'DL-OR-87654321', '1982-11-23',
   'SAV-005678', 'Y', 690),
  (100000003, 'Robert', '', 'Johnson',
   '789 Pine Road', 'Suite 100', 'San Francisco',
   'CA', 'USA', '94102-2222',
   '415-555-4321', '415-555-8765',
   456789123, 'PP-US-98765432', '1960-03-08',
   'CHK-009876', 'Y', 820);

-- ---------------------------------------------------------------------------
-- Accounts
-- ---------------------------------------------------------------------------

INSERT INTO carddemo.accounts VALUES
  ('00000000001', 'Y', 1500.00, 10000.00, 2000.00,
   '2020-01-15', '2026-01-15', '2024-01-15',
   2000.00, 500.00, '98101', 'GOLD      '),
  ('00000000002', 'Y', 3200.50, 5000.00, 1000.00,
   '2019-06-01', '2025-06-01', '2023-06-01',
   1200.00, 800.00, '97201', 'DEFAULT   '),
  ('00000000003', 'Y', 250.00, 20000.00, 5000.00,
   '2015-03-20', '2027-03-20', '2025-03-20',
   5000.00, 0.00, '94102', 'PLATINUM  '),
  -- Edge case: expired account
  ('00000000004', 'Y', 0.00, 2000.00, 500.00,
   '2018-01-01', '2022-12-31', '2022-12-31',
   0.00, 0.00, '10001', 'DEFAULT   ');

-- ---------------------------------------------------------------------------
-- Card cross-reference
-- ---------------------------------------------------------------------------

INSERT INTO carddemo.card_xref VALUES
  ('4111111111111111', 100000001, 1),
  ('4222222222222222', 100000002, 2),
  ('4333333333333333', 100000003, 3),
  ('4444444444444444', 100000001, 1);   -- second card on account 1

-- ---------------------------------------------------------------------------
-- Transaction category balances (pre-existing, used by CBACT04C)
-- ---------------------------------------------------------------------------

INSERT INTO carddemo.transaction_category_balance VALUES
  (1, '01', 1, 850.00),   -- acct 1, Purchase, Groceries
  (1, '01', 2, 320.00),   -- acct 1, Purchase, Gas
  (2, '01', 1, 2000.00),  -- acct 2, Purchase, Groceries
  (2, '02', 1,  500.00),  -- acct 2, Cash Advance, ATM
  (3, '01', 3,  120.00);  -- acct 3, Purchase, Restaurants

-- ---------------------------------------------------------------------------
-- Daily transactions for CBTRN02C
-- ---------------------------------------------------------------------------

-- Valid transaction - purchase on active account within credit limit
INSERT INTO carddemo.daily_transactions VALUES
  ('TRN0000000000001', '01', 1, 'POS       ',
   'WHOLE FOODS MARKET                                                                                    ',
   75.50, 100000001, 'Whole Foods Market                                ',
   'Seattle                                           ', '98101-0001',
   '4111111111111111',
   '2024-01-15-10.30.00.000000', '2024-01-15-10.30.00.000000');

-- Valid transaction - gas purchase
INSERT INTO carddemo.daily_transactions VALUES
  ('TRN0000000000002', '01', 2, 'POS       ',
   'SHELL STATION 4521                                                                                    ',
   45.00, 100000002, 'Shell Station                                     ',
   'Portland                                          ', '97201-0002',
   '4222222222222222',
   '2024-01-15-11.00.00.000000', '2024-01-15-11.00.00.000000');

-- Valid transaction - negative amount (payment/credit)
INSERT INTO carddemo.daily_transactions VALUES
  ('TRN0000000000003', '04', 1, 'ONLINE    ',
   'PAYMENT - THANK YOU                                                                                   ',
   -200.00, 0, '                                                  ',
   '                                                  ', '          ',
   '4222222222222222',
   '2024-01-15-12.00.00.000000', '2024-01-15-12.00.00.000000');

-- REJECT: invalid card number (no xref entry)
INSERT INTO carddemo.daily_transactions VALUES
  ('TRN0000000000004', '01', 1, 'POS       ',
   'UNKNOWN MERCHANT                                                                                      ',
   50.00, 999999999, 'Unknown                                           ',
   'Unknown                                           ', '00000-0000',
   '9999999999999999',
   '2024-01-15-13.00.00.000000', '2024-01-15-13.00.00.000000');

-- REJECT: overlimit - account 2 has credit_limit=5000, curr_bal=3200.50
-- curr_cyc_credit=1200, curr_cyc_debit=800
-- temp_bal = 1200-800+4500 = 4900 > 5000? No. Try 6000:
INSERT INTO carddemo.daily_transactions VALUES
  ('TRN0000000000005', '01', 3, 'POS       ',
   'EXPENSIVE RESTAURANT                                                                                  ',
   4500.00, 200000099, 'Big Restaurant                                    ',
   'Portland                                          ', '97201-0009',
   '4222222222222222',
   '2024-01-15-14.00.00.000000', '2024-01-15-14.00.00.000000');

-- REJECT: expired account (account 4)
INSERT INTO carddemo.daily_transactions VALUES
  ('TRN0000000000006', '01', 1, 'POS       ',
   'STARBUCKS                                                                                             ',
   5.75, 300000001, 'Starbucks                                         ',
   'New York                                          ', '10001-0001',
   '4444444444444444',
   '2024-01-15-15.00.00.000000', '2024-01-15-15.00.00.000000');

-- Valid large transaction - still within limit for account 3 (limit=20000, bal=250)
INSERT INTO carddemo.daily_transactions VALUES
  ('TRN0000000000007', '01', 4, 'ONLINE    ',
   'UNITED AIRLINES BOOKING                                                                               ',
   1200.00, 400000001, 'United Airlines                                   ',
   'Chicago                                           ', '60601-0001',
   '4333333333333333',
   '2024-01-15-16.00.00.000000', '2024-01-15-16.00.00.000000');

-- ---------------------------------------------------------------------------
-- Transactions by card (for CBSTM03A/CBSTM03B pipeline)
-- ---------------------------------------------------------------------------

INSERT INTO carddemo.transactions_by_card VALUES
  ('4111111111111111', 'TRN0000000000001', '01', 1, 'POS       ',
   'WHOLE FOODS MARKET',
   75.50, 100000001, 'Whole Foods Market', 'Seattle', '98101-0001',
   '2024-01-15-10.30.00.000000', '2024-01-15-10.30.00.000000'),
  ('4111111111111111', 'TRN0000000000008', '01', 2, 'POS       ',
   'CHEVRON GAS STATION',
   38.20, 100000003, 'Chevron', 'Seattle', '98101-0005',
   '2024-01-14-08.15.00.000000', '2024-01-14-08.15.00.000000'),
  ('4222222222222222', 'TRN0000000000002', '01', 2, 'POS       ',
   'SHELL STATION 4521',
   45.00, 100000002, 'Shell Station', 'Portland', '97201-0002',
   '2024-01-15-11.00.00.000000', '2024-01-15-11.00.00.000000'),
  ('4333333333333333', 'TRN0000000000007', '01', 4, 'ONLINE    ',
   'UNITED AIRLINES BOOKING',
   1200.00, 400000001, 'United Airlines', 'Chicago', '60601-0001',
   '2024-01-15-16.00.00.000000', '2024-01-15-16.00.00.000000');

-- ---------------------------------------------------------------------------
-- Posted transactions for CBTRN03C (date range report)
-- ---------------------------------------------------------------------------

INSERT INTO carddemo.transactions VALUES
  ('TRN0000000000001', '01', 1, 'POS       ',
   'WHOLE FOODS MARKET                                                                                    ',
   75.50, 100000001, 'Whole Foods Market', 'Seattle', '98101-0001',
   '4111111111111111',
   '2024-01-15-10.30.00.000000', '2024-01-15-10.30.00.000000'),
  ('TRN0000000000002', '01', 2, 'POS       ',
   'SHELL STATION 4521                                                                                    ',
   45.00, 100000002, 'Shell Station', 'Portland', '97201-0002',
   '4222222222222222',
   '2024-01-15-11.00.00.000000', '2024-01-15-11.00.00.000000'),
  ('TRN0000000000003', '04', 1, 'ONLINE    ',
   'PAYMENT - THANK YOU                                                                                   ',
   -200.00, 0, '', '', '',
   '4222222222222222',
   '2024-01-15-12.00.00.000000', '2024-01-15-12.00.00.000000'),
  ('TRN0000000000007', '01', 4, 'ONLINE    ',
   'UNITED AIRLINES BOOKING                                                                               ',
   1200.00, 400000001, 'United Airlines', 'Chicago', '60601-0001',
   '4333333333333333',
   '2024-01-15-16.00.00.000000', '2024-01-15-16.00.00.000000'),
  -- Outside date range - should be filtered by CBTRN03C
  ('TRN0000000000009', '01', 1, 'POS       ',
   'OLD TRANSACTION                                                                                       ',
   22.00, 100000001, 'Old Merchant', 'Seattle', '98101-0001',
   '4111111111111111',
   '2023-12-01-09.00.00.000000', '2023-12-01-09.00.00.000000');
