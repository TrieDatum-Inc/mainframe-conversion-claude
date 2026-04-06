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
