"""Create transactions, transaction_id_seq, and report_requests tables.

COBOL origin:
  transactions    → TRANSACT VSAM KSDS (CVTRA05Y / COTRN02Y copybook)
                    Programs: COTRN00C, COTRN01C, COTRN02C, COBIL00C
  transaction_id_seq → Replaces COTRN02C/COBIL00C STARTBR(HIGH-VALUES)+READPREV+ADD-1
                       (race condition fix: concurrent tasks could generate duplicate IDs)
  report_requests → Replaces CORPT00C TDQ QUEUE='JOBS' batch job submission
                    (new: adds status tracking that original JCL submission lacked)

Key design decisions:
  - transaction_id_seq: PostgreSQL SEQUENCE is atomic under concurrency.
    COTRN02C STARTBR/READPREV/ADD-1 was NOT atomic — two concurrent tasks
    could both read the same last TRAN-ID and generate the same new ID.
  - COTRN01C BUG FIX: READ UPDATE for display-only is documented; the modern
    READ (GET) endpoint uses plain SELECT without FOR UPDATE.
  - report_requests: stores CORPT00C date range, type, requestor, and processing
    status. Original TDQ write had no status tracking.

Revision ID: 004
Revises: 003
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create transactions, transaction_id_seq, and report_requests tables."""

    # -------------------------------------------------------------------------
    # transaction_id_seq
    # Replaces COTRN02C / COBIL00C STARTBR(HIGH-VALUES) + READPREV + ADD-1
    # -------------------------------------------------------------------------
    op.execute("CREATE SEQUENCE IF NOT EXISTS transaction_id_seq START 1")

    # -------------------------------------------------------------------------
    # transactions table
    # Source: TRANSACT VSAM KSDS (CVTRA05Y / COTRN02Y copybook)
    # -------------------------------------------------------------------------
    op.create_table(
        "transactions",
        sa.Column(
            "transaction_id",
            sa.String(16),
            nullable=False,
            comment=(
                "TRAN-ID X(16) — generated via transaction_id_seq "
                "(replaces COTRN02C STARTBR/READPREV/ADD-1 race condition)"
            ),
        ),
        sa.Column(
            "card_number",
            sa.CHAR(16),
            nullable=False,
            comment="TRAN-CARD-NUM X(16) — FK to credit_cards",
        ),
        sa.Column(
            "transaction_type_code",
            sa.String(2),
            nullable=False,
            comment=(
                "TRAN-TYPE-CD X(02) — FK to transaction_types; "
                "'02' hardcoded for bill payments (COBIL00C)"
            ),
        ),
        sa.Column(
            "transaction_category_code",
            sa.String(4),
            nullable=True,
            comment="TRAN-CAT-CD 9(04) — 4-digit numeric; '0002' for bill payments",
        ),
        sa.Column(
            "transaction_source",
            sa.String(10),
            nullable=True,
            comment="TRAN-SOURCE X(10) — 'POS TERM' hardcoded for bill payments (COBIL00C)",
        ),
        sa.Column(
            "description",
            sa.String(60),
            nullable=True,
            comment=(
                "TRAN-DESC X(24) in COTRN02Y; extended to 60 chars. "
                "Bill payments: 'BILL PAYMENT - ONLINE' (COBIL00C hardcoded)"
            ),
        ),
        sa.Column(
            "amount",
            sa.Numeric(10, 2),
            nullable=False,
            comment="TRAN-AMT S9(09)V99 — signed packed decimal; must not be zero",
        ),
        sa.Column(
            "original_date",
            sa.Date,
            nullable=True,
            comment="TRAN-ORIG-TS X(26) — 26-byte COBOL timestamp; date portion stored as DATE",
        ),
        sa.Column(
            "processed_date",
            sa.Date,
            nullable=True,
            comment="TRAN-PROC-TS X(26) — must be >= original_date",
        ),
        sa.Column(
            "merchant_id",
            sa.String(9),
            nullable=True,
            comment=(
                "TRAN-MERCHANT-ID 9(09) — 9-digit numeric as string; "
                "'999999999' synthetic for bill payments (COBIL00C)"
            ),
        ),
        sa.Column(
            "merchant_name",
            sa.String(30),
            nullable=True,
            comment="TRAN-MERCHANT-NAME X(50) — truncated to 30 in target schema",
        ),
        sa.Column(
            "merchant_city",
            sa.String(25),
            nullable=True,
            comment="TRAN-MERCHANT-CITY X(50) — truncated to 25; 'N/A' for bill payments",
        ),
        sa.Column(
            "merchant_zip",
            sa.String(10),
            nullable=True,
            comment="TRAN-MERCHANT-ZIP X(10) — 'N/A' for bill payments (COBIL00C)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("transaction_id", name="pk_transactions"),
        sa.ForeignKeyConstraint(
            ["card_number"],
            ["credit_cards.card_number"],
            name="fk_transactions_card",
        ),
        sa.ForeignKeyConstraint(
            ["transaction_type_code"],
            ["transaction_types.type_code"],
            name="fk_transactions_type",
        ),
        sa.CheckConstraint("amount != 0", name="chk_transactions_nonzero_amount"),
    )

    # Replaces VSAM browse indexes used by COTRN00C STARTBR/READNEXT
    op.create_index("idx_transactions_card_number", "transactions", ["card_number"])
    op.create_index("idx_transactions_type_code", "transactions", ["transaction_type_code"])
    op.create_index("idx_transactions_original_date", "transactions", ["original_date"])
    op.create_index("idx_transactions_processed_date", "transactions", ["processed_date"])
    op.create_index("idx_transactions_merchant_id", "transactions", ["merchant_id"])

    # updated_at trigger — replaces WS-DATACHANGED-FLAG pattern
    op.execute(
        """
        CREATE TRIGGER trg_transactions_updated_at
            BEFORE UPDATE ON transactions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """
    )

    # -------------------------------------------------------------------------
    # report_requests table
    # Source: CORPT00C TDQ QUEUE='JOBS' batch job submission
    # -------------------------------------------------------------------------
    op.create_table(
        "report_requests",
        sa.Column(
            "request_id",
            sa.BigInteger(),
            nullable=False,
            autoincrement=True,
            comment="BIGSERIAL primary key — no COBOL equivalent; added for status tracking",
        ),
        sa.Column(
            "report_type",
            sa.CHAR(1),
            nullable=False,
            comment="CORPT00C: MONTHLYI='M', YEARLYI='Y', CUSTOMI='C'",
        ),
        sa.Column(
            "start_date",
            sa.Date,
            nullable=True,
            comment=(
                "CORPT00C SDTYYY1I+SDTMMI+SDTDDI assembled as YYYYMMDD. "
                "Null = no lower bound (CORPT00C allowed blank start date)"
            ),
        ),
        sa.Column(
            "end_date",
            sa.Date,
            nullable=True,
            comment=(
                "CORPT00C EDTYYYY1I+EDTMMI+EDTDDI; "
                "if blank: CALCULATE-END-DATE → last day prior month"
            ),
        ),
        sa.Column(
            "requested_by",
            sa.String(8),
            nullable=False,
            comment="User ID from JWT sub claim (CSUSR01Y signed-on user)",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="PENDING",
            comment=(
                "Processing status: PENDING/RUNNING/COMPLETED/FAILED. "
                "CORPT00C had no status concept — this is a modern addition."
            ),
        ),
        sa.Column(
            "result_path",
            sa.String(500),
            nullable=True,
            comment="Path/URL to generated report. Replaces JCLLIB output dataset.",
        ),
        sa.Column(
            "error_message",
            sa.String(500),
            nullable=True,
            comment="Error details if FAILED. No COBOL equivalent (TDQ errors were silent).",
        ),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Timestamp when request created — when TDQ write would have occurred",
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when background processing completed. No COBOL equivalent.",
        ),
        sa.PrimaryKeyConstraint("request_id", name="pk_report_requests"),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.user_id"],
            name="fk_rptreq_user",
        ),
        sa.CheckConstraint("report_type IN ('M', 'Y', 'C')", name="chk_rptreq_type"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED')",
            name="chk_rptreq_status",
        ),
        sa.CheckConstraint(
            (
                "report_type != 'C' OR "
                "(start_date IS NOT NULL AND end_date IS NOT NULL AND end_date >= start_date)"
            ),
            name="chk_rptreq_custom_dates",
        ),
    )


def downgrade() -> None:
    """Drop transactions, report_requests tables and transaction_id_seq."""

    op.drop_table("report_requests")

    op.execute("DROP TRIGGER IF EXISTS trg_transactions_updated_at ON transactions")
    op.drop_index("idx_transactions_merchant_id", table_name="transactions")
    op.drop_index("idx_transactions_processed_date", table_name="transactions")
    op.drop_index("idx_transactions_original_date", table_name="transactions")
    op.drop_index("idx_transactions_type_code", table_name="transactions")
    op.drop_index("idx_transactions_card_number", table_name="transactions")
    op.drop_table("transactions")

    op.execute("DROP SEQUENCE IF EXISTS transaction_id_seq")
