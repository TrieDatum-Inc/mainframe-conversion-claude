"""Initial schema — all CardDemo tables.

Maps VSAM KSDS files, DB2 tables, and IMS databases to PostgreSQL.
Equivalent to running migrations/sql/001_create_tables.sql.

Revision ID: 001_initial
Revises: None
Create Date: 2024-01-01 00:00:00.000000

Source COBOL structures:
  accounts          <- ACCTDAT VSAM KSDS (CVACT01Y, 300 bytes)
  customers         <- CUSTDAT VSAM KSDS (CVCUS01Y, 500 bytes)
  cards             <- CARDDAT VSAM KSDS (CVACT02Y, 150 bytes)
  card_xref         <- CXACAIX VSAM AIX  (CVACT03Y, 50 bytes)
  transactions      <- TRANSACT VSAM KSDS (CVTRA05Y, 350 bytes)
  users             <- USRSEC VSAM KSDS (CSUSR01Y, 80 bytes)
  tran_cat_bal      <- TRAN-CAT-BAL-FILE (CVTRA01Y, 50 bytes)
  disclosure_groups <- DIS-GROUP-FILE    (CVTRA02Y, 50 bytes)
  transaction_types <- DB2 CARDDEMO.TRANSACTION_TYPE
  transaction_categories <- DB2 CARDDEMO.TRANSACTION_CATEGORY
  auth_summary      <- IMS PAUTSUM0 segment (CIPAUSMY)
  auth_detail       <- IMS PAUTDTL1 segment (CIPAUDTY)
  auth_fraud        <- DB2 CARDDEMO.AUTHFRDS
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── accounts (ACCTDAT VSAM KSDS / CVACT01Y) ───────────────────────────
    op.create_table(
        "accounts",
        sa.Column("acct_id", sa.BigInteger(), nullable=False),
        sa.Column("active_status", sa.CHAR(1), nullable=False, server_default="Y"),
        sa.Column("curr_bal", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("credit_limit", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("cash_credit_limit", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("open_date", sa.Date(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("reissue_date", sa.Date(), nullable=True),
        sa.Column("curr_cycle_credit", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("curr_cycle_debit", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("addr_zip", sa.String(10), nullable=True),
        sa.Column("group_id", sa.String(10), nullable=True),
        sa.PrimaryKeyConstraint("acct_id", name="pk_accounts"),
        sa.CheckConstraint("active_status IN ('Y', 'N')", name="ck_account_active_status"),
        sa.CheckConstraint("acct_id > 0", name="ck_account_id_positive"),
    )
    op.create_index("ix_accounts_group_id", "accounts", ["group_id"])

    # ── customers (CUSTDAT VSAM KSDS / CVCUS01Y) ──────────────────────────
    op.create_table(
        "customers",
        sa.Column("cust_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(25), nullable=False),
        sa.Column("middle_name", sa.String(25), nullable=True),
        sa.Column("last_name", sa.String(25), nullable=False),
        sa.Column("addr_line1", sa.String(50), nullable=True),
        sa.Column("addr_line2", sa.String(50), nullable=True),
        sa.Column("addr_line3", sa.String(50), nullable=True),
        sa.Column("addr_state_cd", sa.CHAR(2), nullable=True),
        sa.Column("addr_country_cd", sa.CHAR(3), nullable=True),
        sa.Column("addr_zip", sa.String(10), nullable=True),
        sa.Column("phone_num1", sa.String(15), nullable=True),
        sa.Column("phone_num2", sa.String(15), nullable=True),
        sa.Column("ssn", sa.Integer(), nullable=False),
        sa.Column("govt_issued_id", sa.String(20), nullable=True),
        sa.Column("dob", sa.Date(), nullable=True),
        sa.Column("eft_account_id", sa.String(10), nullable=True),
        sa.Column("pri_card_holder", sa.CHAR(1), nullable=True, server_default="Y"),
        sa.Column("fico_score", sa.SmallInteger(), nullable=True),
        sa.PrimaryKeyConstraint("cust_id", name="pk_customers"),
        sa.CheckConstraint("cust_id > 0", name="ck_customer_id_positive"),
        sa.CheckConstraint(
            "ssn >= 100000000 AND ssn <= 999999999",
            name="ck_customer_ssn_range",
        ),
        sa.CheckConstraint(
            "fico_score IS NULL OR (fico_score >= 300 AND fico_score <= 850)",
            name="ck_customer_fico_range",
        ),
        sa.CheckConstraint(
            "pri_card_holder IS NULL OR pri_card_holder IN ('Y', 'N')",
            name="ck_customer_pri_card_holder",
        ),
    )
    op.create_index("ix_customers_last_name", "customers", ["last_name"])
    op.create_index("ix_customers_ssn", "customers", ["ssn"])

    # ── cards (CARDDAT VSAM KSDS / CVACT02Y) ─────────────────────────────
    op.create_table(
        "cards",
        sa.Column("card_num", sa.String(16), nullable=False),
        sa.Column("acct_id", sa.BigInteger(), nullable=False),
        sa.Column("cvv_cd", sa.SmallInteger(), nullable=False),
        sa.Column("embossed_name", sa.String(50), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("active_status", sa.CHAR(1), nullable=False, server_default="Y"),
        sa.PrimaryKeyConstraint("card_num", name="pk_cards"),
        sa.ForeignKeyConstraint(
            ["acct_id"], ["accounts.acct_id"],
            name="fk_cards_accounts", ondelete="RESTRICT",
        ),
        sa.CheckConstraint("active_status IN ('Y', 'N')", name="ck_card_active_status"),
        sa.CheckConstraint("cvv_cd >= 0 AND cvv_cd <= 999", name="ck_card_cvv_range"),
    )
    op.create_index("ix_cards_acct_id", "cards", ["acct_id"])
    op.create_index("ix_cards_active_status", "cards", ["active_status"])

    # ── card_xref (CXACAIX VSAM AIX / CVACT03Y) ──────────────────────────
    op.create_table(
        "card_xref",
        sa.Column("card_num", sa.String(16), nullable=False),
        sa.Column("cust_id", sa.Integer(), nullable=False),
        sa.Column("acct_id", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("card_num", name="pk_card_xref"),
        sa.ForeignKeyConstraint(
            ["card_num"], ["cards.card_num"],
            name="fk_xref_cards", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["cust_id"], ["customers.cust_id"],
            name="fk_xref_customers", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["acct_id"], ["accounts.acct_id"],
            name="fk_xref_accounts", ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_card_xref_acct_id", "card_xref", ["acct_id"])
    op.create_index("ix_card_xref_cust_id", "card_xref", ["cust_id"])

    # ── transaction_types (DB2 CARDDEMO.TRANSACTION_TYPE) ─────────────────
    op.create_table(
        "transaction_types",
        sa.Column("tran_type_cd", sa.CHAR(2), nullable=False),
        sa.Column("tran_type_desc", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("tran_type_cd", name="pk_transaction_types"),
    )

    # ── transaction_categories (DB2 CARDDEMO.TRANSACTION_CATEGORY) ────────
    op.create_table(
        "transaction_categories",
        sa.Column("tran_type_cd", sa.CHAR(2), nullable=False),
        sa.Column("tran_cat_cd", sa.Integer(), nullable=False),
        sa.Column("tran_cat_desc", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint(
            "tran_type_cd", "tran_cat_cd", name="pk_transaction_categories"
        ),
    )

    # ── transactions (TRANSACT VSAM KSDS / CVTRA05Y) ─────────────────────
    op.create_table(
        "transactions",
        sa.Column("tran_id", sa.String(16), nullable=False),
        sa.Column("tran_type_cd", sa.CHAR(2), nullable=False),
        sa.Column("tran_cat_cd", sa.Integer(), nullable=False),
        sa.Column("tran_source", sa.String(10), nullable=True),
        sa.Column("tran_desc", sa.String(100), nullable=True),
        sa.Column("tran_amt", sa.Numeric(11, 2), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=True),
        sa.Column("merchant_name", sa.String(50), nullable=True),
        sa.Column("merchant_city", sa.String(50), nullable=True),
        sa.Column("merchant_zip", sa.String(10), nullable=True),
        sa.Column("card_num", sa.String(16), nullable=False),
        sa.Column("orig_ts", sa.DateTime(), nullable=True),
        sa.Column("proc_ts", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("tran_id", name="pk_transactions"),
        sa.ForeignKeyConstraint(
            ["card_num"], ["cards.card_num"],
            name="fk_transactions_cards", ondelete="RESTRICT",
        ),
        sa.CheckConstraint("tran_type_cd != ''", name="ck_transaction_type_not_empty"),
    )
    op.create_index("ix_transactions_card_num", "transactions", ["card_num"])
    op.create_index("ix_transactions_tran_type_cd", "transactions", ["tran_type_cd"])
    op.create_index("ix_transactions_orig_ts", "transactions", ["orig_ts"])

    # ── users (USRSEC VSAM KSDS / CSUSR01Y) ─────────────────────────────
    op.create_table(
        "users",
        sa.Column("usr_id", sa.String(8), nullable=False),
        sa.Column("first_name", sa.String(20), nullable=False),
        sa.Column("last_name", sa.String(20), nullable=False),
        sa.Column("pwd_hash", sa.String(72), nullable=False),
        sa.Column("usr_type", sa.CHAR(1), nullable=False, server_default="U"),
        sa.PrimaryKeyConstraint("usr_id", name="pk_users"),
        sa.CheckConstraint("usr_type IN ('A', 'U')", name="ck_user_type_valid"),
        sa.CheckConstraint(
            "length(usr_id) >= 1 AND length(usr_id) <= 8",
            name="ck_user_id_length",
        ),
    )
    op.create_index("ix_users_usr_type", "users", ["usr_type"])

    # ── tran_cat_bal (TRAN-CAT-BAL-FILE / CVTRA01Y) ─────────────────────
    op.create_table(
        "tran_cat_bal",
        sa.Column("acct_id", sa.BigInteger(), nullable=False),
        sa.Column("tran_type_cd", sa.CHAR(2), nullable=False),
        sa.Column("tran_cat_cd", sa.Integer(), nullable=False),
        sa.Column("tran_cat_bal", sa.Numeric(11, 2), nullable=False, server_default="0.00"),
        sa.PrimaryKeyConstraint(
            "acct_id", "tran_type_cd", "tran_cat_cd", name="pk_tran_cat_bal"
        ),
        sa.ForeignKeyConstraint(
            ["acct_id"], ["accounts.acct_id"],
            name="fk_tcatbal_accounts", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_tran_cat_bal_acct_id", "tran_cat_bal", ["acct_id"])

    # ── disclosure_groups (DIS-GROUP-FILE / CVTRA02Y) ────────────────────
    op.create_table(
        "disclosure_groups",
        sa.Column("acct_group_id", sa.String(10), nullable=False),
        sa.Column("tran_type_cd", sa.CHAR(2), nullable=False),
        sa.Column("tran_cat_cd", sa.Integer(), nullable=False),
        sa.Column("int_rate", sa.Numeric(6, 2), nullable=False),
        sa.PrimaryKeyConstraint(
            "acct_group_id", "tran_type_cd", "tran_cat_cd",
            name="pk_disclosure_groups",
        ),
    )

    # ── auth_summary (IMS PAUTSUM0 / CIPAUSMY) ────────────────────────────
    op.create_table(
        "auth_summary",
        sa.Column("acct_id", sa.BigInteger(), nullable=False),
        sa.Column("cust_id", sa.Integer(), nullable=False),
        sa.Column("auth_status", sa.CHAR(1), nullable=True),
        sa.Column("credit_limit", sa.Numeric(11, 2), nullable=False, server_default="0.00"),
        sa.Column("cash_limit", sa.Numeric(11, 2), nullable=False, server_default="0.00"),
        sa.Column("curr_bal", sa.Numeric(11, 2), nullable=False, server_default="0.00"),
        sa.Column("cash_bal", sa.Numeric(11, 2), nullable=False, server_default="0.00"),
        sa.Column("approved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_amt", sa.Numeric(11, 2), nullable=False, server_default="0.00"),
        sa.Column("declined_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("declined_amt", sa.Numeric(11, 2), nullable=False, server_default="0.00"),
        sa.PrimaryKeyConstraint("acct_id", name="pk_auth_summary"),
    )
    op.create_index("ix_auth_summary_cust_id", "auth_summary", ["cust_id"])

    # ── auth_detail (IMS PAUTDTL1 / CIPAUDTY) ────────────────────────────
    op.create_table(
        "auth_detail",
        sa.Column("auth_date", sa.Date(), nullable=False),
        sa.Column("auth_time", sa.Time(), nullable=False),
        sa.Column("acct_id", sa.BigInteger(), nullable=False),
        sa.Column("card_num", sa.String(16), nullable=True),
        sa.Column("tran_id", sa.String(16), nullable=True),
        sa.Column("auth_id_code", sa.String(10), nullable=True),
        sa.Column("response_code", sa.CHAR(2), nullable=True),
        sa.Column("response_reason", sa.String(25), nullable=True),
        sa.Column("approved_amt", sa.Numeric(11, 2), nullable=False, server_default="0.00"),
        sa.Column("auth_type", sa.CHAR(1), nullable=True),
        sa.Column("match_status", sa.CHAR(1), nullable=True),
        sa.Column("fraud_flag", sa.CHAR(1), nullable=False, server_default="N"),
        sa.PrimaryKeyConstraint("auth_date", "auth_time", "acct_id", name="pk_auth_detail"),
        sa.ForeignKeyConstraint(
            ["acct_id"], ["auth_summary.acct_id"],
            name="fk_auth_detail_summary", ondelete="CASCADE",
        ),
        sa.CheckConstraint("fraud_flag IN ('Y', 'N')", name="ck_auth_detail_fraud_flag"),
    )
    op.create_index("ix_auth_detail_card_num", "auth_detail", ["card_num"])
    op.create_index("ix_auth_detail_acct_id", "auth_detail", ["acct_id"])

    # ── auth_fraud (DB2 CARDDEMO.AUTHFRDS) ────────────────────────────────
    op.create_table(
        "auth_fraud",
        sa.Column(
            "fraud_id",
            sa.Integer(),
            sa.Identity(always=False),
            nullable=False,
        ),
        sa.Column("card_num", sa.String(16), nullable=False),
        sa.Column("acct_id", sa.BigInteger(), nullable=False),
        sa.Column("auth_date", sa.Date(), nullable=True),
        sa.Column("auth_time", sa.Time(), nullable=True),
        sa.Column("fraud_reason", sa.String(100), nullable=True),
        sa.Column("flagged_by", sa.String(8), nullable=True),
        sa.Column("flagged_ts", sa.DateTime(), nullable=True),
        sa.Column("fraud_status", sa.CHAR(1), nullable=True, server_default="P"),
        sa.PrimaryKeyConstraint("fraud_id", name="pk_auth_fraud"),
    )
    op.create_index("ix_auth_fraud_card_num", "auth_fraud", ["card_num"])
    op.create_index("ix_auth_fraud_acct_id", "auth_fraud", ["acct_id"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("auth_fraud")
    op.drop_table("auth_detail")
    op.drop_table("auth_summary")
    op.drop_table("disclosure_groups")
    op.drop_table("tran_cat_bal")
    op.drop_table("users")
    op.drop_table("transactions")
    op.drop_table("transaction_categories")
    op.drop_table("transaction_types")
    op.drop_table("card_xref")
    op.drop_table("cards")
    op.drop_table("customers")
    op.drop_table("accounts")
