"""Create users table.

COBOL origin: USRSEC VSAM KSDS (CSUSR01Y copybook).
Replaces the flat VSAM file with a PostgreSQL relation with bcrypt password storage.

Revision ID: 001
Revises: (initial migration)
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create the users table and supporting indexes/triggers.

    Maps:
      SEC-USR-ID     X(08) → user_id VARCHAR(8) PK
      SEC-USR-PWD    X(08) → password_hash VARCHAR(255) [bcrypt]
      SEC-USR-FNAME  X(20) → first_name VARCHAR(20)
      SEC-USR-LNAME  X(20) → last_name VARCHAR(20)
      SEC-USR-TYPE   X(01) → user_type CHAR(1) CHECK IN ('A','U')
      SEC-USR-FILLER X(23) → (discarded — unused padding)
    """
    # Trigger function for updated_at auto-management
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.create_table(
        "users",
        sa.Column("user_id", sa.String(8), primary_key=True, nullable=False,
                  comment="SEC-USR-ID X(08) — VSAM KSDS primary key"),
        sa.Column("first_name", sa.String(20), nullable=False,
                  comment="SEC-USR-FNAME X(20)"),
        sa.Column("last_name", sa.String(20), nullable=False,
                  comment="SEC-USR-LNAME X(20)"),
        sa.Column("password_hash", sa.String(255), nullable=False,
                  comment="bcrypt hash — replaces plain-text SEC-USR-PWD X(08)"),
        sa.Column("user_type", sa.String(1), nullable=False,
                  comment="SEC-USR-TYPE X(01): A=Admin, U=Regular"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint("user_type IN ('A', 'U')", name="chk_users_type"),
    )

    op.create_index("idx_users_last_name", "users", ["last_name"])
    op.create_index("idx_users_user_type", "users", ["user_type"])

    # Trigger for updated_at
    op.execute("""
        CREATE TRIGGER trg_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop the users table and supporting objects."""
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users")
    op.drop_index("idx_users_user_type", table_name="users")
    op.drop_index("idx_users_last_name", table_name="users")
    op.drop_table("users")
