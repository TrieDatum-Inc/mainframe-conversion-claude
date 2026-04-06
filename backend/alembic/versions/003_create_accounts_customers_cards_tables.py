"""Create accounts, customers, credit_cards, card_account_xref, account_customer_xref tables.

COBOL origin:
  accounts            → ACCTDAT VSAM KSDS (CVACT01Y copybook)
  customers           → CUSTDAT VSAM KSDS (CVCUS01Y copybook)
  credit_cards        → CARDDAT VSAM KSDS (CVACT02Y copybook)
  card_account_xref   → CARDXREF VSAM KSDS + AIX on XREF-ACCT-ID (CVACT03Y copybook)
  account_customer_xref → Derived from ACCTDAT/CUSTDAT relationship

These tables support COACTVWC, COACTUPC, COCRDLIC, COCRDSLC, COCRDUPC programs.

Revision ID: 003
Revises: 002
Create Date: 2026-04-06
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all account/customer/card tables."""

    # -----------------------------------------------------------------
    # accounts — ACCTDAT VSAM KSDS (CVACT01Y)
    # -----------------------------------------------------------------
    op.create_table(
        "accounts",
        sa.Column("account_id", sa.BigInteger, primary_key=True, nullable=False,
                  comment="ACCT-ID 9(11) — VSAM KSDS primary key"),
        sa.Column("active_status", sa.CHAR(1), nullable=False, server_default="Y",
                  comment="ACCT-ACTIVE-STATUS X(1) — Y/N"),
        sa.Column("current_balance", sa.Numeric(12, 2), nullable=False, server_default="0.00",
                  comment="ACCT-CURR-BAL S9(10)V99 COMP-3"),
        sa.Column("credit_limit", sa.Numeric(12, 2), nullable=False, server_default="0.00",
                  comment="ACCT-CREDIT-LIMIT S9(10)V99 COMP-3"),
        sa.Column("cash_credit_limit", sa.Numeric(12, 2), nullable=False, server_default="0.00",
                  comment="ACCT-CASH-CREDIT-LIMIT S9(10)V99 COMP-3"),
        sa.Column("open_date", sa.Date, nullable=True,
                  comment="ACCT-OPEN-DATE X(10) — YYYY-MM-DD"),
        sa.Column("expiration_date", sa.Date, nullable=True,
                  comment="ACCT-EXPIRAION-DATE X(10) — typo in source preserved as comment"),
        sa.Column("reissue_date", sa.Date, nullable=True,
                  comment="ACCT-REISSUE-DATE X(10)"),
        sa.Column("curr_cycle_credit", sa.Numeric(12, 2), nullable=False, server_default="0.00",
                  comment="ACCT-CURR-CYC-CREDIT S9(10)V99 COMP-3"),
        sa.Column("curr_cycle_debit", sa.Numeric(12, 2), nullable=False, server_default="0.00",
                  comment="ACCT-CURR-CYC-DEBIT S9(10)V99 COMP-3"),
        sa.Column("zip_code", sa.String(10), nullable=True,
                  comment="ACCT-ADDR-ZIP X(10)"),
        sa.Column("group_id", sa.String(10), nullable=True,
                  comment="ACCT-GROUP-ID X(10)"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint("active_status IN ('Y', 'N')", name="chk_accounts_active"),
        sa.CheckConstraint("credit_limit >= 0", name="chk_accounts_credit_limit"),
        sa.CheckConstraint("cash_credit_limit >= 0", name="chk_accounts_cash_limit"),
        sa.CheckConstraint(
            "cash_credit_limit <= credit_limit", name="chk_accounts_cash_lte_credit"
        ),
    )
    op.create_index("idx_accounts_active_status", "accounts", ["active_status"])
    op.create_index("idx_accounts_group_id", "accounts", ["group_id"])
    op.execute("""
        CREATE TRIGGER trg_accounts_updated_at
            BEFORE UPDATE ON accounts
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # -----------------------------------------------------------------
    # customers — CUSTDAT VSAM KSDS (CVCUS01Y)
    # -----------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.Integer, primary_key=True, nullable=False,
                  comment="CUST-ID 9(9) — VSAM KSDS primary key"),
        sa.Column("first_name", sa.String(25), nullable=False,
                  comment="CUST-FIRST-NAME X(25) — alpha-only validated"),
        sa.Column("middle_name", sa.String(25), nullable=True,
                  comment="CUST-MIDDLE-NAME X(25)"),
        sa.Column("last_name", sa.String(25), nullable=False,
                  comment="CUST-LAST-NAME X(25) — alpha-only validated"),
        sa.Column("street_address_1", sa.String(50), nullable=True,
                  comment="CUST-ADDR-LINE-1 X(50)"),
        sa.Column("street_address_2", sa.String(50), nullable=True,
                  comment="CUST-ADDR-LINE-2 X(50)"),
        sa.Column("city", sa.String(50), nullable=True,
                  comment="CUST-ADDR-CITY X(50)"),
        sa.Column("state_code", sa.CHAR(2), nullable=True,
                  comment="CUST-ADDR-STATE-CD X(2)"),
        sa.Column("zip_code", sa.String(10), nullable=True,
                  comment="CUST-ADDR-ZIP X(10)"),
        sa.Column("country_code", sa.CHAR(3), nullable=True,
                  comment="CUST-ADDR-COUNTRY-CD X(3)"),
        sa.Column("phone_number_1", sa.String(15), nullable=True,
                  comment="CUST-PHONE-NUM-1 X(15) — NNN-NNN-NNNN format"),
        sa.Column("phone_number_2", sa.String(15), nullable=True,
                  comment="CUST-PHONE-NUM-2 X(15)"),
        sa.Column("ssn", sa.String(11), nullable=True,
                  comment="CUST-SSN parts (3+2+4) — NNN-NN-NNNN; encrypt at rest"),
        sa.Column("date_of_birth", sa.Date, nullable=True,
                  comment="CUST-DOB-YYYY-MM-DD X(10)"),
        sa.Column("fico_score", sa.SmallInteger, nullable=True,
                  comment="CUST-FICO-CREDIT-SCORE 9(3) — CHECK 300-850"),
        sa.Column("government_id_ref", sa.String(20), nullable=True,
                  comment="CUST-GOVT-ISSUED-ID X(20)"),
        sa.Column("eft_account_id", sa.String(10), nullable=True,
                  comment="CUST-EFT-ACCOUNT-ID X(10)"),
        sa.Column("primary_card_holder_flag", sa.CHAR(1), nullable=False, server_default="Y",
                  comment="CUST-PRI-CARD-HOLDER-IND X(1) — Y/N"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "primary_card_holder_flag IN ('Y', 'N')", name="chk_customers_primary_flag"
        ),
        sa.CheckConstraint(
            "fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)",
            name="chk_customers_fico",
        ),
    )
    op.create_index("idx_customers_last_name", "customers", ["last_name"])
    op.create_index("idx_customers_ssn", "customers", ["ssn"])
    op.execute("""
        CREATE TRIGGER trg_customers_updated_at
            BEFORE UPDATE ON customers
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # -----------------------------------------------------------------
    # account_customer_xref — links accounts to customers
    # -----------------------------------------------------------------
    op.create_table(
        "account_customer_xref",
        sa.Column("account_id", sa.BigInteger, nullable=False,
                  comment="FK to accounts.account_id"),
        sa.Column("customer_id", sa.Integer, nullable=False,
                  comment="FK to customers.customer_id"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("account_id", "customer_id", name="pk_acct_cust_xref"),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.account_id"], name="fk_acctcust_account"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.customer_id"], name="fk_acctcust_customer"
        ),
    )
    op.create_index("idx_acctcust_customer", "account_customer_xref", ["customer_id"])

    # -----------------------------------------------------------------
    # credit_cards — CARDDAT VSAM KSDS (CVACT02Y)
    # -----------------------------------------------------------------
    op.create_table(
        "credit_cards",
        sa.Column("card_number", sa.CHAR(16), primary_key=True, nullable=False,
                  comment="CARD-NUM X(16) — VSAM KSDS primary key"),
        sa.Column("account_id", sa.BigInteger, nullable=False,
                  comment="CARD-ACCT-ID 9(11) — PROT in COCRDUPC"),
        sa.Column("customer_id", sa.Integer, nullable=False,
                  comment="CARD-CUST-ID 9(9)"),
        sa.Column("card_embossed_name", sa.String(50), nullable=True,
                  comment="CARD-EMBOSSED-NAME X(50) — CRDNAME on map; alpha-only validated"),
        sa.Column("active_status", sa.CHAR(1), nullable=False, server_default="Y",
                  comment="CARD-ACTIVE-STATUS X(1) — CRDSTCD on map"),
        sa.Column("expiration_date", sa.Date, nullable=True,
                  comment="Derived from EXPMON+EXPYEAR+EXPDAY on COCRDUP map"),
        sa.Column("expiration_day", sa.SmallInteger, nullable=True,
                  comment="EXPDAY — DRK PROT FSET hidden field on COCRDUP map"),
        sa.Column("cvv", sa.String(4), nullable=True,
                  comment="CVV — never shown in update screen; store encrypted"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint("active_status IN ('Y', 'N')", name="chk_cards_active"),
        sa.CheckConstraint(
            "EXTRACT(MONTH FROM expiration_date) BETWEEN 1 AND 12",
            name="chk_cards_exp_month",
        ),
        sa.CheckConstraint(
            "EXTRACT(YEAR FROM expiration_date) BETWEEN 1950 AND 2099",
            name="chk_cards_exp_year",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.account_id"], name="fk_cards_account"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.customer_id"], name="fk_cards_customer"
        ),
    )
    op.create_index("idx_cards_account_id", "credit_cards", ["account_id"])
    op.create_index("idx_cards_customer_id", "credit_cards", ["customer_id"])
    op.create_index("idx_cards_active_status", "credit_cards", ["active_status"])
    op.execute("""
        CREATE TRIGGER trg_cards_updated_at
            BEFORE UPDATE ON credit_cards
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # -----------------------------------------------------------------
    # card_account_xref — CARDXREF VSAM KSDS + AIX on XREF-ACCT-ID (CVACT03Y)
    # -----------------------------------------------------------------
    op.create_table(
        "card_account_xref",
        sa.Column("card_number", sa.CHAR(16), nullable=False,
                  comment="XREF-CARD-NUM X(16) — VSAM KSDS primary key"),
        sa.Column("customer_id", sa.Integer, nullable=False,
                  comment="XREF-CUST-ID 9(9)"),
        sa.Column("account_id", sa.BigInteger, nullable=False,
                  comment="XREF-ACCT-ID 9(11) — was VSAM AIX; now PostgreSQL index"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("card_number", name="pk_card_xref"),
        sa.ForeignKeyConstraint(
            ["card_number"], ["credit_cards.card_number"], name="fk_cardxref_card"
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.account_id"], name="fk_cardxref_account"
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"], ["customers.customer_id"], name="fk_cardxref_customer"
        ),
    )
    # Replaces VSAM AIX on XREF-ACCT-ID
    op.create_index("idx_cardxref_account", "card_account_xref", ["account_id"])
    op.create_index("idx_cardxref_customer", "card_account_xref", ["customer_id"])


def downgrade() -> None:
    """Drop all account/customer/card tables in reverse FK order."""
    op.execute("DROP TRIGGER IF EXISTS trg_cards_updated_at ON credit_cards")
    op.execute("DROP TRIGGER IF EXISTS trg_customers_updated_at ON customers")
    op.execute("DROP TRIGGER IF EXISTS trg_accounts_updated_at ON accounts")

    op.drop_index("idx_cardxref_customer", table_name="card_account_xref")
    op.drop_index("idx_cardxref_account", table_name="card_account_xref")
    op.drop_table("card_account_xref")

    op.drop_index("idx_cards_active_status", table_name="credit_cards")
    op.drop_index("idx_cards_customer_id", table_name="credit_cards")
    op.drop_index("idx_cards_account_id", table_name="credit_cards")
    op.drop_table("credit_cards")

    op.drop_index("idx_acctcust_customer", table_name="account_customer_xref")
    op.drop_table("account_customer_xref")

    op.drop_index("idx_customers_ssn", table_name="customers")
    op.drop_index("idx_customers_last_name", table_name="customers")
    op.drop_table("customers")

    op.drop_index("idx_accounts_group_id", table_name="accounts")
    op.drop_index("idx_accounts_active_status", table_name="accounts")
    op.drop_table("accounts")
