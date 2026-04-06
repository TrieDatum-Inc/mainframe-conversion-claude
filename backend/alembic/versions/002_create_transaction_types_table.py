"""Create transaction_types table.

COBOL origin: DB2 table CARDDEMO.TRANSACTION_TYPE (DCLTRTYP DCLGEN copybook).
Programs: COTRTLIC (Transaction CTLI), COTRTUPC (Transaction CTTU).

Revision ID: 002
Revises: 001
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """
    Create the transaction_types table.

    COBOL origin: Equivalent to DB2 DDL for CARDDEMO.TRANSACTION_TYPE.
    Constraints replace COBOL validation paragraphs in COTRTUPC:
      - chk_tt_type_code_numeric: 1245-EDIT-NUM-REQD (NUMERIC test)
      - chk_tt_type_code_nonzero: 1210-EDIT-TRANTYPE (non-zero check)
      - chk_tt_description_alphanum: 1230-EDIT-ALPHANUM-REQD
    """
    op.create_table(
        "transaction_types",
        sa.Column("type_code", sa.String(2), nullable=False),
        sa.Column("description", sa.String(50), nullable=False),
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
        sa.PrimaryKeyConstraint("type_code", name="pk_transaction_types"),
        sa.CheckConstraint(
            "type_code ~ '^[0-9]{1,2}$'",
            name="chk_tt_type_code_numeric",
        ),
        sa.CheckConstraint(
            "type_code::INTEGER > 0",
            name="chk_tt_type_code_nonzero",
        ),
        sa.CheckConstraint(
            "description ~ '^[A-Za-z0-9 ]+$'",
            name="chk_tt_description_alphanum",
        ),
    )

    # Trigger: auto-update updated_at (replaces COTRTLIC WS-DATACHANGED-FLAG)
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_tt_updated_at
            BEFORE UPDATE ON transaction_types
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop the transaction_types table and trigger."""
    op.execute("DROP TRIGGER IF EXISTS trg_tt_updated_at ON transaction_types;")
    op.drop_table("transaction_types")
