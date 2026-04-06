-- =============================================================================
-- CardDemo Transaction Module - Seed Data
-- Sample transactions for development and testing
-- Card numbers and account IDs match the CardDemo sample VSAM data
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Sample transactions (10 rows)
-- transaction_id follows X(16) format, zero-padded numeric string
-- Cards belong to accounts defined in the CardDemo VSAM data files
-- ---------------------------------------------------------------------------
INSERT INTO transactions (
    transaction_id, type_code, category_code, source, description,
    amount, merchant_id, merchant_name, merchant_city, merchant_zip,
    card_number, original_timestamp, processing_timestamp
) VALUES
-- Purchases for card 4000002000000000 (account 00000001000)
('0000000000000001', '01', '0001', 'POS TERM', 'GROCERY STORE PURCHASE',
 -45.67, '123456789', 'WHOLE FOODS MARKET', 'NEW YORK', '10001',
 '4000002000000000', '2024-01-05 10:23:45', '2024-01-05 10:25:00'),

('0000000000000002', '01', '0002', 'ONLINE   ', 'ONLINE SHOPPING',
 -120.00, '234567890', 'AMAZON.COM', 'SEATTLE', '98101',
 '4000002000000000', '2024-01-07 14:30:00', '2024-01-07 14:32:00'),

('0000000000000003', '01', '0003', 'POS TERM', 'RESTAURANT DINNER',
 -78.50, '345678901', 'THE CAPITAL GRILLE', 'BOSTON', '02108',
 '4000002000000000', '2024-01-10 19:45:00', '2024-01-10 19:46:30'),

-- Payment for card 4000002000000000
('0000000000000004', '02', '0002', 'POS TERM', 'BILL PAYMENT - ONLINE',
  244.17, '999999999', 'BILL PAYMENT', 'PAYMENT', '00000',
 '4000002000000000', '2024-01-15 08:00:00', '2024-01-15 08:01:00'),

-- Purchases for card 4000003000000000 (account 00000002000)
('0000000000000005', '01', '0001', 'POS TERM', 'SUPERMARKET PURCHASE',
 -89.23, '456789012', 'TRADER JOES', 'CHICAGO', '60601',
 '4000003000000000', '2024-01-08 11:15:00', '2024-01-08 11:17:00'),

('0000000000000006', '01', '0004', 'POS TERM', 'GAS STATION',
 -55.00, '567890123', 'SHELL OIL CO', 'LOS ANGELES', '90001',
 '4000003000000000', '2024-01-12 07:30:00', '2024-01-12 07:31:00'),

('0000000000000007', '01', '0005', 'ONLINE   ', 'STREAMING SERVICE',
 -15.99, '678901234', 'NETFLIX INC', 'LOS GATOS', '95030',
 '4000003000000000', '2024-01-14 00:00:00', '2024-01-14 00:01:00'),

-- Purchases for card 4000004000000000 (account 00000003000)
('0000000000000008', '01', '0006', 'POS TERM', 'PHARMACY PURCHASE',
 -32.45, '789012345', 'CVS PHARMACY', 'DALLAS', '75201',
 '4000004000000000', '2024-01-09 16:20:00', '2024-01-09 16:21:30'),

('0000000000000009', '01', '0007', 'POS TERM', 'HARDWARE STORE',
 -210.75, '890123456', 'HOME DEPOT', 'ATLANTA', '30301',
 '4000004000000000', '2024-01-11 13:45:00', '2024-01-11 13:47:00'),

('0000000000000010', '01', '0001', 'POS TERM', 'COFFEE SHOP',
 -8.75, '901234567', 'STARBUCKS', 'MIAMI', '33101',
 '4000004000000000', '2024-01-13 08:05:00', '2024-01-13 08:06:00');

-- ---------------------------------------------------------------------------
-- Sample transaction category balances
-- Maps to VSAM KSDS TCATBALF composite key (account + type + category)
-- ---------------------------------------------------------------------------
INSERT INTO transaction_category_balances (account_id, type_code, category_code, balance)
VALUES
('00000001000', '01', '0001', -45.67),
('00000001000', '01', '0002', -120.00),
('00000001000', '01', '0003', -78.50),
('00000001000', '02', '0002',  244.17),
('00000002000', '01', '0001', -89.23),
('00000002000', '01', '0004', -55.00),
('00000002000', '01', '0005', -15.99),
('00000003000', '01', '0006', -32.45),
('00000003000', '01', '0007', -210.75),
('00000003000', '01', '0001', -8.75);
