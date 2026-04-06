"""Authorization module tables: authorization_summary, authorization_detail, auth_fraud_log

Revision ID: 001_authorization_tables
Revises:
Create Date: 2026-04-06

Source COBOL programs: COPAUS0C, COPAUS1C, COPAUS2C
Replaces: IMS PAUTSUM0/PAUTDTL1 segments + DB2 CARDDEMO.AUTHFRDS table
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_authorization_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create authorization tables."""

    # authorization_summary — replaces IMS PAUTSUM0 root segment
    op.create_table(
        "authorization_summary",
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "credit_limit", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column(
            "cash_limit", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0.00"
        ),
        sa.Column(
            "credit_balance",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "cash_balance",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("approved_auth_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("declined_auth_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "approved_auth_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "declined_auth_amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.account_id"], name="fk_authsum_account"
        ),
        sa.PrimaryKeyConstraint("account_id", name="pk_auth_summary"),
    )

    # authorization_detail — replaces IMS PAUTDTL1 child segment
    op.create_table(
        "authorization_detail",
        sa.Column(
            "auth_id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_id", sa.String(length=16), nullable=False),
        sa.Column("card_number", sa.CHAR(length=16), nullable=False),
        sa.Column("auth_date", sa.Date(), nullable=False),
        sa.Column("auth_time", sa.Time(), nullable=False),
        sa.Column("auth_response_code", sa.CHAR(length=2), nullable=False),
        sa.Column("auth_code", sa.String(length=6), nullable=True),
        sa.Column("transaction_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("pos_entry_mode", sa.String(length=4), nullable=True),
        sa.Column("auth_source", sa.String(length=10), nullable=True),
        sa.Column("mcc_code", sa.String(length=4), nullable=True),
        sa.Column("card_expiry_date", sa.String(length=5), nullable=True),
        sa.Column("auth_type", sa.String(length=14), nullable=True),
        sa.Column("match_status", sa.CHAR(length=1), nullable=False, server_default="P"),
        sa.Column("fraud_status", sa.CHAR(length=1), nullable=False, server_default="N"),
        sa.Column("merchant_name", sa.String(length=25), nullable=True),
        sa.Column("merchant_id", sa.String(length=15), nullable=True),
        sa.Column("merchant_city", sa.String(length=25), nullable=True),
        sa.Column("merchant_state", sa.CHAR(length=2), nullable=True),
        sa.Column("merchant_zip", sa.String(length=10), nullable=True),
        sa.Column(
            "processed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint("match_status IN ('P', 'D', 'E', 'M')", name="chk_authdet_match"),
        sa.CheckConstraint("fraud_status IN ('N', 'F', 'R')", name="chk_authdet_fraud"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["authorization_summary.account_id"],
            name="fk_authdet_summary",
        ),
        sa.PrimaryKeyConstraint("auth_id", name="pk_auth_detail"),
    )

    op.create_index("idx_authdet_account_id", "authorization_detail", ["account_id"])
    op.create_index("idx_authdet_card_number", "authorization_detail", ["card_number"])
    op.create_index(
        "idx_authdet_processed_at",
        "authorization_detail",
        [sa.text("processed_at DESC")],
    )
    op.create_index("idx_authdet_transaction_id", "authorization_detail", ["transaction_id"])
    op.create_index("idx_authdet_fraud_status", "authorization_detail", ["fraud_status"])

    # Trigger for updated_at
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_authdet_updated_at
            BEFORE UPDATE ON authorization_detail
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # auth_fraud_log — replaces DB2 CARDDEMO.AUTHFRDS
    op.create_table(
        "auth_fraud_log",
        sa.Column("log_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("auth_id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_id", sa.String(length=16), nullable=False),
        sa.Column("card_number", sa.CHAR(length=16), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("fraud_flag", sa.CHAR(length=1), nullable=False),
        sa.Column(
            "fraud_report_date",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("auth_response_code", sa.CHAR(length=2), nullable=True),
        sa.Column("auth_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("merchant_name", sa.String(length=22), nullable=True),
        sa.Column("merchant_id", sa.String(length=9), nullable=True),
        sa.Column(
            "logged_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["auth_id"], ["authorization_detail.auth_id"], name="fk_fraudlog_auth"
        ),
        sa.PrimaryKeyConstraint("log_id", name="pk_fraud_log"),
    )

    op.create_index("idx_fraudlog_transaction", "auth_fraud_log", ["transaction_id"])
    op.create_index("idx_fraudlog_account", "auth_fraud_log", ["account_id"])

    # Unique partial index — replaces COPAUS2C SQLCODE -803 constraint
    op.create_index(
        "idx_fraudlog_unique_auth",
        "auth_fraud_log",
        ["auth_id", "fraud_flag"],
        unique=True,
        postgresql_where=sa.text("fraud_flag = 'F'"),
    )


def downgrade() -> None:
    """Drop authorization tables."""
    op.execute("DROP TRIGGER IF EXISTS trg_authdet_updated_at ON authorization_detail")
    op.drop_table("auth_fraud_log")
    op.drop_table("authorization_detail")
    op.drop_table("authorization_summary")
