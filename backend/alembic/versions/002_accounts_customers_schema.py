"""Accounts, customers, and account-customer cross-reference tables.

Revision ID: 002
Revises: 001
Create Date: 2026-04-14

COBOL origin — three VSAM files replaced:

1. accounts table  ← ACCTDAT VSAM KSDS (CVACT01Y copybook, 300-byte record)
   Key field: ACCT-ID 9(11) → account_id BIGINT PRIMARY KEY
   Programs accessing ACCTDAT: COACTVWC (READ), COACTUPC (READ UPDATE + REWRITE),
     COBIL00C (READ UPDATE + REWRITE), CBACT01C-04C (batch)

2. customers table ← CUSTDAT VSAM KSDS (CVCUS01Y copybook, 500-byte record)
   Key field: CUST-ID 9(9) → customer_id INTEGER PRIMARY KEY
   Programs accessing CUSTDAT: COACTVWC (READ), COACTUPC (READ UPDATE + REWRITE),
     CBCUS01C (batch)

3. account_customer_xref table ← CXACAIX (alternate index on XREF, CVACT03Y copybook)
   Replaces: EXEC CICS READ DATASET('CXACAIX') RIDFLD(acct_id) KEYLENGTH(11) GTEQ
   Navigation pattern: account_id → xref → customer_id → READ CUSTDAT

Security notes:
  - CUST-SSN: stored as plain text in VSAM; encrypted at rest recommended in production.
    The ssn column stores the formatted value (NNN-NN-NNNN). Never returned unmasked.
  - ACCT-ACTIVE-STATUS: Y/N enforced by CHECK constraint (was implicit in COBOL logic).
  - Cash credit limit <= credit limit: DB-level constraint (was validated in COACTUPC).
"""

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # accounts table — replaces ACCTDAT VSAM KSDS (CVACT01Y, 300 bytes)
    # ------------------------------------------------------------------
    op.create_table(
        "accounts",
        # ACCT-ID 9(11) → BIGINT PRIMARY KEY
        sa.Column(
            "account_id",
            sa.BigInteger(),
            nullable=False,
            comment="ACCT-ID 9(11) — VSAM KSDS primary key",
        ),
        # ACCT-ACTIVE-STATUS X(1) → CHAR(1) CHECK IN ('Y','N')
        sa.Column(
            "active_status",
            sa.String(1),
            nullable=False,
            server_default="Y",
            comment="ACCT-ACTIVE-STATUS X(1): Y=Active, N=Inactive",
        ),
        # ACCT-CURR-BAL S9(10)V99 COMP-3 → NUMERIC(12,2)
        sa.Column(
            "current_balance",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="ACCT-CURR-BAL S9(10)V99 COMP-3 — signed packed decimal",
        ),
        # ACCT-CREDIT-LIMIT S9(10)V99 COMP-3 → NUMERIC(12,2)
        sa.Column(
            "credit_limit",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="ACCT-CREDIT-LIMIT S9(10)V99 COMP-3",
        ),
        # ACCT-CASH-CREDIT-LIMIT S9(10)V99 COMP-3 → NUMERIC(12,2)
        sa.Column(
            "cash_credit_limit",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="ACCT-CASH-CREDIT-LIMIT S9(10)V99 COMP-3",
        ),
        # ACCT-OPEN-DATE X(10) → DATE
        sa.Column(
            "open_date",
            sa.Date(),
            nullable=True,
            comment="ACCT-OPEN-DATE X(10) — ISO YYYY-MM-DD",
        ),
        # ACCT-EXPIRAION-DATE X(10) → DATE (typo in COBOL source preserved as comment)
        sa.Column(
            "expiration_date",
            sa.Date(),
            nullable=True,
            comment="ACCT-EXPIRAION-DATE X(10) — note: typo preserved from COBOL source",
        ),
        # ACCT-REISSUE-DATE X(10) → DATE
        sa.Column(
            "reissue_date",
            sa.Date(),
            nullable=True,
            comment="ACCT-REISSUE-DATE X(10)",
        ),
        # ACCT-CURR-CYC-CREDIT S9(10)V99 COMP-3 → NUMERIC(12,2)
        sa.Column(
            "curr_cycle_credit",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="ACCT-CURR-CYC-CREDIT S9(10)V99 COMP-3",
        ),
        # ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3 → NUMERIC(12,2)
        sa.Column(
            "curr_cycle_debit",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0.00",
            comment="ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3",
        ),
        # ACCT-ADDR-ZIP X(10) → VARCHAR(10)
        sa.Column(
            "zip_code",
            sa.String(10),
            nullable=True,
            comment="ACCT-ADDR-ZIP X(10)",
        ),
        # ACCT-GROUP-ID X(10) → VARCHAR(10)  (AADDGRP BMS field)
        sa.Column(
            "group_id",
            sa.String(10),
            nullable=True,
            comment="ACCT-GROUP-ID X(10) — AADDGRP BMS field",
        ),
        # FILLER X(178) — NOT STORED (padding discarded)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("account_id", name="pk_accounts"),
        sa.CheckConstraint("active_status IN ('Y', 'N')", name="chk_accounts_active"),
        sa.CheckConstraint("credit_limit >= 0", name="chk_accounts_credit_limit"),
        sa.CheckConstraint("cash_credit_limit >= 0", name="chk_accounts_cash_limit"),
        sa.CheckConstraint(
            "cash_credit_limit <= credit_limit",
            name="chk_accounts_cash_lte_credit",
        ),
    )
    op.create_index("idx_accounts_active_status", "accounts", ["active_status"])
    op.create_index("idx_accounts_group_id", "accounts", ["group_id"])

    # Attach updated_at auto-update trigger to accounts
    # (trigger function created in migration 001 — NOT recreated here)
    op.execute("""
        CREATE TRIGGER trg_accounts_updated_at
        BEFORE UPDATE ON accounts
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # ------------------------------------------------------------------
    # customers table — replaces CUSTDAT VSAM KSDS (CVCUS01Y, 500 bytes)
    # ------------------------------------------------------------------
    op.create_table(
        "customers",
        # CUST-ID 9(9) → INTEGER PRIMARY KEY
        sa.Column(
            "customer_id",
            sa.Integer(),
            nullable=False,
            comment="CUST-ID 9(9) — VSAM KSDS primary key",
        ),
        # CUST-FIRST-NAME X(25) → VARCHAR(25)
        sa.Column(
            "first_name",
            sa.String(25),
            nullable=False,
            comment="CUST-FIRST-NAME X(25) — ACSFNAM BMS field",
        ),
        # CUST-MIDDLE-NAME X(25) → VARCHAR(25)
        sa.Column(
            "middle_name",
            sa.String(25),
            nullable=True,
            comment="CUST-MIDDLE-NAME X(25) — ACSMNAM BMS field",
        ),
        # CUST-LAST-NAME X(25) → VARCHAR(25)
        sa.Column(
            "last_name",
            sa.String(25),
            nullable=False,
            comment="CUST-LAST-NAME X(25) — ACSLNAM BMS field",
        ),
        # CUST-ADDR-LINE-1 X(50) → VARCHAR(50)
        sa.Column(
            "street_address_1",
            sa.String(50),
            nullable=True,
            comment="CUST-ADDR-LINE-1 X(50) — ACSADL1 BMS field",
        ),
        # CUST-ADDR-LINE-2 X(50) → VARCHAR(50)
        sa.Column(
            "street_address_2",
            sa.String(50),
            nullable=True,
            comment="CUST-ADDR-LINE-2 X(50) — ACSADL2 BMS field",
        ),
        # CUST-ADDR-CITY X(50) → VARCHAR(50)
        sa.Column(
            "city",
            sa.String(50),
            nullable=True,
            comment="CUST-ADDR-CITY X(50) — ACSCITY BMS field",
        ),
        # CUST-ADDR-STATE-CD X(2) → CHAR(2)
        sa.Column(
            "state_code",
            sa.String(2),
            nullable=True,
            comment="CUST-ADDR-STATE-CD X(2) — ACSSTTE BMS field",
        ),
        # CUST-ADDR-ZIP X(10) → VARCHAR(10)
        sa.Column(
            "zip_code",
            sa.String(10),
            nullable=True,
            comment="CUST-ADDR-ZIP X(10) — ACSZIPC BMS field",
        ),
        # CUST-ADDR-COUNTRY-CD X(3) → CHAR(3)
        sa.Column(
            "country_code",
            sa.String(3),
            nullable=True,
            comment="CUST-ADDR-COUNTRY-CD X(3) — ACSCTRY BMS field",
        ),
        # CUST-PHONE-NUM-1 X(15) → VARCHAR(15) — NNN-NNN-NNNN format
        sa.Column(
            "phone_number_1",
            sa.String(15),
            nullable=True,
            comment="CUST-PHONE-NUM-1 X(15) — ACSPHN1 BMS field; NNN-NNN-NNNN format",
        ),
        # CUST-PHONE-NUM-2 X(15) → VARCHAR(15)
        sa.Column(
            "phone_number_2",
            sa.String(15),
            nullable=True,
            comment="CUST-PHONE-NUM-2 X(15) — ACSPHN2 BMS field",
        ),
        # CUST-SSN 9(9) three-part (3+2+4) → VARCHAR(11) as NNN-NN-NNNN
        # SECURITY: encrypt at rest in production; last 4 digits only in display
        sa.Column(
            "ssn",
            sa.String(11),
            nullable=True,
            comment=(
                "CUST-SSN 9(9) stored as NNN-NN-NNNN. "
                "SECURITY: encrypt at rest in production. "
                "Never returned unmasked in any API response."
            ),
        ),
        # CUST-DOB-YYYY-MM-DD X(10) → DATE
        sa.Column(
            "date_of_birth",
            sa.Date(),
            nullable=True,
            comment="CUST-DOB-YYYY-MM-DD X(10) — ACSTDOB BMS field",
        ),
        # CUST-EFT-ACCOUNT-ID X(10) → VARCHAR(10)
        sa.Column(
            "eft_account_id",
            sa.String(10),
            nullable=True,
            comment="CUST-EFT-ACCOUNT-ID X(10) — ACSEFTC BMS field",
        ),
        # CUST-PRI-CARD-HOLDER-IND X(1) → CHAR(1) CHECK IN ('Y','N')
        sa.Column(
            "primary_card_holder_flag",
            sa.String(1),
            nullable=False,
            server_default="Y",
            comment="CUST-PRI-CARD-HOLDER-IND X(1) — ACSPFLG BMS field; Y/N",
        ),
        # CUST-FICO-CREDIT-SCORE 9(3) → SMALLINT  (300–850 range)
        sa.Column(
            "fico_score",
            sa.SmallInteger(),
            nullable=True,
            comment="CUST-FICO-CREDIT-SCORE 9(3) — ACSTFCO BMS field; 300-850 range",
        ),
        # CUST-GOVT-ISSUED-ID X(20) → VARCHAR(20)
        sa.Column(
            "government_id_ref",
            sa.String(20),
            nullable=True,
            comment="CUST-GOVT-ISSUED-ID X(20) — ACSGOVT BMS field",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("customer_id", name="pk_customers"),
        sa.CheckConstraint(
            "primary_card_holder_flag IN ('Y', 'N')",
            name="chk_customers_primary_flag",
        ),
        sa.CheckConstraint(
            "fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)",
            name="chk_customers_fico",
        ),
    )
    op.create_index("idx_customers_last_name", "customers", ["last_name"])
    op.create_index("idx_customers_ssn", "customers", ["ssn"])

    # Attach updated_at trigger to customers
    op.execute("""
        CREATE TRIGGER trg_customers_updated_at
        BEFORE UPDATE ON customers
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # ------------------------------------------------------------------
    # account_customer_xref table — replaces CXACAIX alternate index
    # COBOL origin: EXEC CICS READ DATASET('CXACAIX') RIDFLD(acct_id)
    # Navigation: account_id → xref lookup → customer_id → READ CUSTDAT
    # ------------------------------------------------------------------
    op.create_table(
        "account_customer_xref",
        sa.Column(
            "account_id",
            sa.BigInteger(),
            sa.ForeignKey("accounts.account_id", ondelete="CASCADE"),
            nullable=False,
            comment="XREF-ACCT-ID 9(11) — FK to accounts",
        ),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customers.customer_id", ondelete="CASCADE"),
            nullable=False,
            comment="XREF-CUST-ID 9(9) — FK to customers",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("account_id", "customer_id", name="pk_acct_cust_xref"),
    )
    op.create_index("idx_acctcust_customer", "account_customer_xref", ["customer_id"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.execute("DROP TRIGGER IF EXISTS trg_customers_updated_at ON customers;")
    op.execute("DROP TRIGGER IF EXISTS trg_accounts_updated_at ON accounts;")

    op.drop_index("idx_acctcust_customer", table_name="account_customer_xref")
    op.drop_table("account_customer_xref")

    op.drop_index("idx_customers_ssn", table_name="customers")
    op.drop_index("idx_customers_last_name", table_name="customers")
    op.drop_table("customers")

    op.drop_index("idx_accounts_group_id", table_name="accounts")
    op.drop_index("idx_accounts_active_status", table_name="accounts")
    op.drop_table("accounts")
