"""Create accounts, customers, cards, and card_xref tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-06

Migrates VSAM KSDS files:
  ACCTDATA (CVACT01Y, ACCT-ID 9(11))    -> accounts
  CUSTDATA (CVCUS01Y, CUST-ID 9(9))     -> customers
  CARDDATA (CVACT02Y, CARD-NUM X(16))   -> cards
  CARDXREF (CVACT03Y, XREF-CARD-NUM X(16)) -> card_xref

Alternate indexes replicated as PostgreSQL indexes:
  CARDAIX  (CARD-ACCT-ID)   -> idx_cards_account_id
  CXACAIX  (XREF-ACCT-ID)   -> idx_card_xref_account_id

COBOL source programs: COACTVWC, COACTUPC, COCRDLIC, COCRDSLC, COCRDUPC
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create accounts, customers, cards, card_xref tables."""

    # accounts — ACCTDATA VSAM KSDS (CVACT01Y)
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.String(11), nullable=False),
        sa.Column("active_status", sa.String(1), nullable=False, server_default="Y"),
        sa.Column("current_balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("credit_limit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("cash_credit_limit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("open_date", sa.Date(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("reissue_date", sa.Date(), nullable=True),
        sa.Column("current_cycle_credit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("current_cycle_debit", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("address_zip", sa.String(10), nullable=True),
        sa.Column("group_id", sa.String(10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_accounts"),
        sa.UniqueConstraint("account_id", name="uq_accounts_account_id"),
        sa.CheckConstraint("active_status IN ('Y', 'N')", name="ck_accounts_active_status"),
        sa.CheckConstraint("credit_limit >= 0", name="ck_accounts_credit_limit_nonneg"),
        sa.CheckConstraint(
            "cash_credit_limit >= 0", name="ck_accounts_cash_credit_limit_nonneg"
        ),
    )
    op.create_index("idx_accounts_account_id", "accounts", ["account_id"])
    op.create_index("idx_accounts_active_status", "accounts", ["active_status"])

    # customers — CUSTDATA VSAM KSDS (CVCUS01Y)
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.String(9), nullable=False),
        sa.Column("first_name", sa.String(25), nullable=False, server_default=""),
        sa.Column("middle_name", sa.String(25), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(25), nullable=False, server_default=""),
        sa.Column("address_line_1", sa.String(50), nullable=False, server_default=""),
        sa.Column("address_line_2", sa.String(50), nullable=False, server_default=""),
        sa.Column("address_line_3", sa.String(50), nullable=False, server_default=""),
        sa.Column("state_code", sa.String(2), nullable=False, server_default=""),
        sa.Column("country_code", sa.String(3), nullable=False, server_default="USA"),
        sa.Column("zip_code", sa.String(10), nullable=False, server_default=""),
        sa.Column("phone_1", sa.String(15), nullable=False, server_default=""),
        sa.Column("phone_2", sa.String(15), nullable=False, server_default=""),
        sa.Column("ssn", sa.String(9), nullable=False, server_default=""),
        sa.Column("govt_issued_id", sa.String(20), nullable=False, server_default=""),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("eft_account_id", sa.String(10), nullable=False, server_default=""),
        sa.Column("primary_card_holder", sa.String(1), nullable=False, server_default="Y"),
        sa.Column("fico_score", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_customers"),
        sa.UniqueConstraint("customer_id", name="uq_customers_customer_id"),
        sa.CheckConstraint(
            "primary_card_holder IN ('Y', 'N')",
            name="ck_customers_primary_card_holder",
        ),
        sa.CheckConstraint(
            "fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)",
            name="ck_customers_fico_range",
        ),
    )
    op.create_index("idx_customers_customer_id", "customers", ["customer_id"])
    op.create_index("idx_customers_last_name", "customers", ["last_name"])

    # cards — CARDDATA VSAM KSDS (CVACT02Y)
    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("card_number", sa.String(16), nullable=False),
        sa.Column("account_id", sa.String(11), nullable=False),
        sa.Column("cvv_code", sa.String(3), nullable=False, server_default=""),
        sa.Column("embossed_name", sa.String(50), nullable=False, server_default=""),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("active_status", sa.String(1), nullable=False, server_default="Y"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cards"),
        sa.UniqueConstraint("card_number", name="uq_cards_card_number"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.account_id"],
            name="fk_cards_account_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("active_status IN ('Y', 'N')", name="ck_cards_active_status"),
    )
    # Replicates CARDAIX alternate index (cards browseable by account)
    op.create_index("idx_cards_card_number", "cards", ["card_number"])
    op.create_index("idx_cards_account_id", "cards", ["account_id"])

    # card_xref — CARDXREF VSAM KSDS (CVACT03Y)
    op.create_table(
        "card_xref",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("card_number", sa.String(16), nullable=False),
        sa.Column("customer_id", sa.String(9), nullable=False),
        sa.Column("account_id", sa.String(11), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_card_xref"),
        sa.UniqueConstraint("card_number", name="uq_card_xref_card_number"),
        sa.ForeignKeyConstraint(
            ["card_number"],
            ["cards.card_number"],
            name="fk_card_xref_card_number",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.customer_id"],
            name="fk_card_xref_customer_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.account_id"],
            name="fk_card_xref_account_id",
            ondelete="CASCADE",
        ),
    )
    # Replicates CXACAIX alternate index (xref lookup by account)
    op.create_index("idx_card_xref_account_id", "card_xref", ["account_id"])
    op.create_index("idx_card_xref_customer_id", "card_xref", ["customer_id"])
    op.create_index("idx_card_xref_card_number", "card_xref", ["card_number"])


def downgrade() -> None:
    """Drop accounts, customers, cards, card_xref tables."""
    op.drop_table("card_xref")
    op.drop_table("cards")
    op.drop_table("customers")
    op.drop_table("accounts")
