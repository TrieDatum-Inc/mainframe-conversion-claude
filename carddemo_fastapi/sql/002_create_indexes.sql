-- ============================================================================
-- CardDemo FastAPI Migration - Index Creation Script
-- Indexes derived from VSAM alternate index definitions and query patterns
-- ============================================================================

BEGIN;

-- card_xref: alternate index CXACAIX on account ID for account-based lookups
CREATE INDEX IF NOT EXISTS idx_card_xref_acct_id
    ON card_xref (xref_acct_id);

-- cards: alternate index CARDAIX on account ID for account-based card lookups
CREATE INDEX IF NOT EXISTS idx_cards_acct_id
    ON cards (card_acct_id);

-- transactions: index on card number for card-based transaction lookups
CREATE INDEX IF NOT EXISTS idx_transactions_card_num
    ON transactions (tran_card_num);

-- transactions: index on origination timestamp for date-range queries
CREATE INDEX IF NOT EXISTS idx_transactions_orig_ts
    ON transactions (tran_orig_ts);

-- pending_auth_details: index on account ID for summary-to-detail joins
CREATE INDEX IF NOT EXISTS idx_pa_details_acct_id
    ON pending_auth_details (pa_acct_id);

-- pending_auth_details: composite index on card + date + time for auth lookups
CREATE INDEX IF NOT EXISTS idx_pa_details_card_date_time
    ON pending_auth_details (pa_card_num, pa_auth_date, pa_auth_time);

-- auth_fraud: unique descending timestamp index for fraud detection queries
CREATE UNIQUE INDEX IF NOT EXISTS idx_auth_fraud_card_ts
    ON auth_fraud (card_num, auth_ts DESC);

COMMIT;
