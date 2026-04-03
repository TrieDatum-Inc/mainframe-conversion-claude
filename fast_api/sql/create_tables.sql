-- CardDemo Credit Card Module - PostgreSQL Schema
CREATE TABLE IF NOT EXISTS accounts (
    acct_id             VARCHAR(11) PRIMARY KEY,
    acct_active_status  CHAR(1)         NOT NULL DEFAULT 'Y' CHECK (acct_active_status IN ('Y', 'N')),
    acct_curr_bal       NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    acct_credit_limit   NUMERIC(12, 2)  NOT NULL DEFAULT 0,
    acct_cash_credit_limit NUMERIC(12, 2) NOT NULL DEFAULT 0,
    acct_open_date      DATE,
    acct_expiration_date DATE,
    acct_reissue_date   DATE,
    acct_curr_cyc_credit NUMERIC(12, 2) NOT NULL DEFAULT 0,
    acct_curr_cyc_debit  NUMERIC(12, 2) NOT NULL DEFAULT 0,
    acct_addr_zip       VARCHAR(10),
    acct_group_id       VARCHAR(10),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS cards (
    card_num                VARCHAR(16)     PRIMARY KEY,
    card_acct_id            VARCHAR(11)     NOT NULL,
    card_cvv_cd             VARCHAR(3),
    card_embossed_name      VARCHAR(50),
    card_expiration_date    DATE,
    card_active_status      CHAR(1)         NOT NULL DEFAULT 'Y' CHECK (card_active_status IN ('Y', 'N')),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_cards_account FOREIGN KEY (card_acct_id) REFERENCES accounts (acct_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_cards_acct_id ON cards (card_acct_id);
CREATE TABLE IF NOT EXISTS card_cross_references (
    xref_card_num   VARCHAR(16) PRIMARY KEY,
    xref_cust_id    VARCHAR(9),
    xref_acct_id    VARCHAR(11),
    CONSTRAINT fk_xref_card FOREIGN KEY (xref_card_num) REFERENCES cards (card_num) ON DELETE CASCADE,
    CONSTRAINT fk_xref_account FOREIGN KEY (xref_acct_id) REFERENCES accounts (acct_id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_xref_acct_id ON card_cross_references (xref_acct_id);
CREATE INDEX IF NOT EXISTS idx_xref_cust_id ON card_cross_references (xref_cust_id);
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;
CREATE OR REPLACE TRIGGER trg_cards_updated_at BEFORE UPDATE ON cards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE OR REPLACE TRIGGER trg_accounts_updated_at BEFORE UPDATE ON accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
