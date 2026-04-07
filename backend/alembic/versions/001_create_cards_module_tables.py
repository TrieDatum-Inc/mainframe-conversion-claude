"""
Create cards module tables.

Revision ID: 001
Create Date: 2026-04-06

COBOL datasets converted:
  - USRSEC VSAM KSDS (CSUSR01Y) → users
  - ACCTDAT VSAM KSDS (CVACT01Y) → accounts
  - CUSTDAT VSAM KSDS (CVCUS01Y) → customers
  - CARDDAT VSAM KSDS (CVACT02Y) → credit_cards
  - CARDXREF VSAM KSDS (CVACT03Y) → card_account_xref
  - (new) → account_customer_xref (replaces CARDAIX AIX browse in COACTVWC)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Shared trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
        $$ LANGUAGE plpgsql
    """)

    # users
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(8), primary_key=True),
        sa.Column("first_name", sa.String(20), nullable=False),
        sa.Column("last_name", sa.String(20), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("user_type", sa.CHAR(1), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("user_type IN ('A', 'U')", name="chk_users_type"),
    )
    op.create_index("idx_users_last_name", "users", ["last_name"])
    op.execute("""
        CREATE OR REPLACE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)

    # accounts
    op.create_table(
        "accounts",
        sa.Column("account_id", sa.BigInteger, primary_key=True),
        sa.Column("active_status", sa.CHAR(1), nullable=False, server_default="Y"),
        sa.Column("current_balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("credit_limit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("cash_credit_limit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("curr_cycle_credit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("curr_cycle_debit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("open_date", sa.Date, nullable=True),
        sa.Column("expiration_date", sa.Date, nullable=True),
        sa.Column("reissue_date", sa.Date, nullable=True),
        sa.Column("group_id", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("active_status IN ('Y', 'N')", name="chk_accounts_active_status"),
        sa.CheckConstraint("credit_limit >= 0", name="chk_accounts_credit_limit_positive"),
        sa.CheckConstraint(
            "cash_credit_limit >= 0 AND cash_credit_limit <= credit_limit",
            name="chk_accounts_cash_limit_range",
        ),
    )
    op.execute("""
        CREATE OR REPLACE TRIGGER trg_accounts_updated_at
        BEFORE UPDATE ON accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)

    # customers
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.Integer, primary_key=True),
        sa.Column("first_name", sa.String(25), nullable=False),
        sa.Column("middle_name", sa.String(25), nullable=True),
        sa.Column("last_name", sa.String(25), nullable=False),
        sa.Column("address_line_1", sa.String(50), nullable=True),
        sa.Column("address_line_2", sa.String(50), nullable=True),
        sa.Column("address_line_3", sa.String(50), nullable=True),
        sa.Column("state_code", sa.CHAR(2), nullable=True),
        sa.Column("country_code", sa.CHAR(3), nullable=True),
        sa.Column("zip_code", sa.String(10), nullable=True),
        sa.Column("phone_1", sa.String(15), nullable=True),
        sa.Column("phone_2", sa.String(15), nullable=True),
        sa.Column("ssn", sa.String(11), nullable=True),
        sa.Column("government_id_ref", sa.String(20), nullable=True),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("eft_account_id", sa.String(10), nullable=True),
        sa.Column("primary_card_holder", sa.CHAR(1), nullable=False, server_default="Y"),
        sa.Column("fico_score", sa.SmallInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("primary_card_holder IN ('Y', 'N')", name="chk_customers_primary_card_holder"),
        sa.CheckConstraint(
            "fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)",
            name="chk_customers_fico_range",
        ),
    )
    op.create_index("idx_customers_last_name", "customers", ["last_name"])
    op.execute("""
        CREATE OR REPLACE TRIGGER trg_customers_updated_at
        BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)

    # account_customer_xref
    op.create_table(
        "account_customer_xref",
        sa.Column("account_id", sa.BigInteger, sa.ForeignKey("accounts.account_id"), nullable=False),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("account_id", "customer_id", name="pk_account_customer_xref"),
    )
    op.create_index("idx_acctcust_customer", "account_customer_xref", ["customer_id"])

    # credit_cards
    op.create_table(
        "credit_cards",
        sa.Column("card_number", sa.CHAR(16), primary_key=True),
        sa.Column("account_id", sa.BigInteger, sa.ForeignKey("accounts.account_id"), nullable=False),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("card_embossed_name", sa.String(50), nullable=True),
        sa.Column("expiration_date", sa.Date, nullable=True),
        sa.Column("expiration_day", sa.Integer, nullable=True),
        sa.Column("active_status", sa.CHAR(1), nullable=False, server_default="Y"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("active_status IN ('Y', 'N')", name="chk_cards_active_status"),
    )
    op.create_index("idx_cards_account", "credit_cards", ["account_id"])
    op.create_index("idx_cards_customer", "credit_cards", ["customer_id"])
    op.execute("""
        CREATE OR REPLACE TRIGGER trg_cards_updated_at
        BEFORE UPDATE ON credit_cards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)

    # card_account_xref (CARDXREF + CARDAIX replacement)
    op.create_table(
        "card_account_xref",
        sa.Column("card_number", sa.CHAR(16), sa.ForeignKey("credit_cards.card_number"), primary_key=True),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("account_id", sa.BigInteger, sa.ForeignKey("accounts.account_id"), nullable=False),
    )
    op.create_index("idx_cardxref_account", "card_account_xref", ["account_id"])
    op.create_index("idx_cardxref_customer", "card_account_xref", ["customer_id"])


def downgrade() -> None:
    op.drop_table("card_account_xref")
    op.drop_table("credit_cards")
    op.drop_table("account_customer_xref")
    op.drop_table("customers")
    op.drop_table("accounts")
    op.drop_table("users")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column CASCADE")
