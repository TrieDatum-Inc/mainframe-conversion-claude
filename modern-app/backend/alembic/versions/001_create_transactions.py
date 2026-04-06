"""Create transactions and transaction_category_balances tables.

Revision ID: 001
Revises: (none)
Create Date: 2026-04-06

Converted from VSAM KSDS files:
  TRANSACT  (CVTRA05Y — TRAN-RECORD 350 bytes)
  TCATBALF  (CVTRA01Y — TRAN-CAT-BAL-RECORD 50 bytes)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # transactions
    # -----------------------------------------------------------------------
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.String(16), nullable=False),
        sa.Column("type_code", sa.String(2), nullable=False),
        sa.Column("category_code", sa.String(4), nullable=False),
        sa.Column("source", sa.String(10), nullable=False, server_default=""),
        sa.Column("description", sa.String(100), nullable=False, server_default=""),
        sa.Column("amount", sa.Numeric(11, 2), nullable=False),
        sa.Column("merchant_id", sa.String(9), nullable=False, server_default=""),
        sa.Column("merchant_name", sa.String(50), nullable=False, server_default=""),
        sa.Column("merchant_city", sa.String(50), nullable=False, server_default=""),
        sa.Column("merchant_zip", sa.String(10), nullable=False, server_default=""),
        sa.Column("card_number", sa.String(16), nullable=False),
        sa.Column("original_timestamp", sa.DateTime(), nullable=False),
        sa.Column("processing_timestamp", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id", name="uq_transaction_id"),
        sa.CheckConstraint(
            "amount >= -99999999.99 AND amount <= 99999999.99",
            name="chk_transaction_amount_range",
        ),
    )
    op.create_index("idx_transactions_transaction_id", "transactions", ["transaction_id"])
    op.create_index("idx_transactions_card_number", "transactions", ["card_number"])
    op.create_index("idx_transactions_orig_ts", "transactions", ["original_timestamp"])
    op.create_index(
        "idx_transactions_type_category",
        "transactions",
        ["type_code", "category_code"],
    )

    # -----------------------------------------------------------------------
    # transaction_category_balances
    # -----------------------------------------------------------------------
    op.create_table(
        "transaction_category_balances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.String(11), nullable=False),
        sa.Column("type_code", sa.String(2), nullable=False),
        sa.Column("category_code", sa.String(4), nullable=False),
        sa.Column("balance", sa.Numeric(11, 2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id", "type_code", "category_code", name="uq_tcat_bal"
        ),
    )
    op.create_index(
        "idx_tcatbal_account", "transaction_category_balances", ["account_id"]
    )


def downgrade() -> None:
    op.drop_table("transaction_category_balances")
    op.drop_table("transactions")
