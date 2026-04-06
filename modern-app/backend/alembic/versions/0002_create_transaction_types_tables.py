"""Create transaction_types and transaction_type_categories tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-06

Migrates DB2 tables:
  CARDDEMO.TRANSACTION_TYPE          -> transaction_types
  CARDDEMO.TRANSACTION_TYPE_CATEGORY -> transaction_type_categories

COBOL source programs: COTRTLIC, COTRTUPC, COBTUPDT
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # transaction_types — maps to CARDDEMO.TRANSACTION_TYPE
    op.create_table(
        "transaction_types",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # TR_TYPE CHAR(2) — unique, non-blank
        sa.Column("type_code", sa.String(length=2), nullable=False),
        # TR_DESCRIPTION VARCHAR(50) — non-blank
        sa.Column("description", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(type_code)) > 0",
            name="ck_transaction_types_type_code_length",
        ),
        sa.CheckConstraint(
            "length(trim(description)) > 0",
            name="ck_transaction_types_description_nonempty",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type_code", name="uq_transaction_types_type_code"),
    )
    op.create_index(
        "ix_transaction_types_type_code",
        "transaction_types",
        ["type_code"],
        unique=True,
    )
    op.create_index(
        "idx_transaction_types_description",
        "transaction_types",
        ["description"],
        unique=False,
    )

    # transaction_type_categories — maps to CARDDEMO.TRANSACTION_TYPE_CATEGORY
    op.create_table(
        "transaction_type_categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # FK to transaction_types.type_code (CASCADE DELETE)
        sa.Column("type_code", sa.String(length=2), nullable=False),
        # TR_CAT VARCHAR(4)
        sa.Column("category_code", sa.String(length=4), nullable=False),
        # TR_CAT_DESCRIPTION VARCHAR(50)
        sa.Column("description", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(category_code)) > 0",
            name="ck_txn_cat_category_code_nonempty",
        ),
        sa.CheckConstraint(
            "length(trim(description)) > 0",
            name="ck_txn_cat_description_nonempty",
        ),
        sa.ForeignKeyConstraint(
            ["type_code"],
            ["transaction_types.type_code"],
            name="fk_txn_type_categories_type_code",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "type_code", "category_code", name="uq_txn_type_category"
        ),
    )
    op.create_index(
        "idx_txn_type_categories_type_code",
        "transaction_type_categories",
        ["type_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_txn_type_categories_type_code",
        table_name="transaction_type_categories",
    )
    op.drop_table("transaction_type_categories")
    op.drop_index(
        "idx_transaction_types_description",
        table_name="transaction_types",
    )
    op.drop_index(
        "ix_transaction_types_type_code",
        table_name="transaction_types",
    )
    op.drop_table("transaction_types")
