"""create_authorizations

Revision ID: 001_create_authorizations
Revises:
Create Date: 2026-04-06

Creates authorization_summaries, authorization_details, and fraud_records tables.

Converts:
- IMS DBPAUTP0/PAUTSUM0 root segment  → authorization_summaries
- IMS DBPAUTP0/PAUTDTL1 child segment → authorization_details
- DB2 CARDDEMO.AUTHFRDS table          → fraud_records
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_create_authorizations"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # authorization_summaries — maps to IMS PAUTSUM0
    op.create_table(
        "authorization_summaries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.String(11), nullable=False),
        sa.Column("customer_id", sa.String(9), nullable=False),
        sa.Column("auth_status", sa.String(1), nullable=False, server_default="A"),
        sa.Column("credit_limit", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("cash_limit", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("credit_balance", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("cash_balance", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("approved_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("declined_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("approved_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("declined_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
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
        sa.UniqueConstraint("account_id", name="uq_auth_summaries_account_id"),
        sa.CheckConstraint("auth_status IN ('A', 'C', 'I')", name="ck_auth_status"),
    )
    op.create_index("idx_auth_summaries_account_id", "authorization_summaries", ["account_id"])
    op.create_index("idx_auth_summaries_customer_id", "authorization_summaries", ["customer_id"])

    # authorization_details — maps to IMS PAUTDTL1
    op.create_table(
        "authorization_details",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "summary_id",
            sa.Integer,
            sa.ForeignKey("authorization_summaries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("card_number", sa.String(16), nullable=False),
        sa.Column("auth_date", sa.Date, nullable=False),
        sa.Column("auth_time", sa.Time, nullable=False),
        sa.Column("auth_type", sa.String(4), nullable=False, server_default=""),
        sa.Column("card_expiry", sa.String(5), nullable=False, server_default=""),
        sa.Column("message_type", sa.String(6), nullable=False, server_default=""),
        sa.Column("auth_response_code", sa.String(2), nullable=False, server_default="00"),
        sa.Column("auth_response_reason", sa.String(20), nullable=False, server_default=""),
        sa.Column("auth_code", sa.String(6), nullable=False, server_default=""),
        sa.Column("transaction_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("approved_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("pos_entry_mode", sa.String(4), nullable=False, server_default=""),
        sa.Column("auth_source", sa.String(10), nullable=False, server_default=""),
        sa.Column("mcc_code", sa.String(4), nullable=False, server_default=""),
        sa.Column("merchant_name", sa.String(25), nullable=False, server_default=""),
        sa.Column("merchant_id", sa.String(15), nullable=False, server_default=""),
        sa.Column("merchant_city", sa.String(25), nullable=False, server_default=""),
        sa.Column("merchant_state", sa.String(2), nullable=False, server_default=""),
        sa.Column("merchant_zip", sa.String(10), nullable=False, server_default=""),
        sa.Column("transaction_id", sa.String(15), nullable=False, server_default=""),
        sa.Column("match_status", sa.String(1), nullable=False, server_default="P"),
        sa.Column("fraud_status", sa.String(1), nullable=True),
        sa.Column("fraud_report_date", sa.Date, nullable=True),
        sa.Column("processing_code", sa.String(6), nullable=False, server_default=""),
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
        sa.CheckConstraint(
            "match_status IN ('P', 'D', 'E', 'M')", name="ck_match_status"
        ),
        sa.CheckConstraint(
            "fraud_status IS NULL OR fraud_status IN ('F', 'R')",
            name="ck_fraud_status",
        ),
    )
    op.create_index("idx_auth_details_summary_id", "authorization_details", ["summary_id"])
    op.create_index("idx_auth_details_card_number", "authorization_details", ["card_number"])
    op.create_index("idx_auth_details_auth_date", "authorization_details", ["auth_date"])
    op.create_index("idx_auth_details_transaction_id", "authorization_details", ["transaction_id"])
    op.create_index("idx_auth_details_match_status", "authorization_details", ["match_status"])
    op.create_index(
        "idx_auth_details_summary_date",
        "authorization_details",
        ["summary_id", "auth_date"],
    )

    # fraud_records — maps to DB2 CARDDEMO.AUTHFRDS
    op.create_table(
        "fraud_records",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("card_number", sa.String(16), nullable=False),
        sa.Column("auth_timestamp", sa.DateTime, nullable=False),
        sa.Column("fraud_flag", sa.String(1), nullable=False),
        sa.Column("fraud_report_date", sa.Date, nullable=False),
        sa.Column("match_status", sa.String(1), nullable=False, server_default="P"),
        sa.Column("account_id", sa.String(11), nullable=False),
        sa.Column("customer_id", sa.String(9), nullable=False),
        sa.Column(
            "auth_detail_id",
            sa.Integer,
            sa.ForeignKey("authorization_details.id", ondelete="SET NULL"),
            nullable=True,
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
        sa.UniqueConstraint(
            "card_number", "auth_timestamp", name="uq_fraud_card_timestamp"
        ),
        sa.CheckConstraint("fraud_flag IN ('F', 'R')", name="ck_fraud_flag"),
        sa.CheckConstraint(
            "match_status IN ('P', 'D', 'E', 'M')", name="ck_fraud_match_status"
        ),
    )
    op.create_index("idx_fraud_records_card_number", "fraud_records", ["card_number"])
    op.create_index("idx_fraud_records_account_id", "fraud_records", ["account_id"])
    op.create_index("idx_fraud_records_auth_detail_id", "fraud_records", ["auth_detail_id"])


def downgrade() -> None:
    op.drop_table("fraud_records")
    op.drop_table("authorization_details")
    op.drop_table("authorization_summaries")
