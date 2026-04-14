"""Initial schema: users table with trigger

Revision ID: 001
Revises:
Create Date: 2026-04-14

COBOL origin: USRSEC VSAM KSDS (CSUSR01Y copybook).
  - SEC-USR-ID    X(8)  → user_id VARCHAR(8) PRIMARY KEY
  - SEC-USR-FNAME X(20) → first_name VARCHAR(20)
  - SEC-USR-LNAME X(20) → last_name VARCHAR(20)
  - SEC-USR-PWD   X(8)  → password_hash VARCHAR(255) [bcrypt; plain-text replaced]
  - SEC-USR-TYPE  X(1)  → user_type CHAR(1) CHECK IN ('A','U')
  - SEC-USR-FILLER X(23) → NOT MIGRATED (unused padding)

Security change: SEC-USR-PWD was stored as plain text and compared byte-by-byte
in COSGN00C. This migration stores only bcrypt hashes in password_hash.
Existing VSAM data must be re-hashed before populating this table.
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Trigger function: auto-update updated_at on every row modification
    # COBOL origin: Replaces manual WS-DATACHANGED-FLAG pattern used in
    #               COACTUPC and COCRDUPC to detect concurrent modifications.
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ------------------------------------------------------------------
    # users table — replaces USRSEC VSAM KSDS
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(8), nullable=False,
                  comment="SEC-USR-ID X(8) — VSAM KSDS primary key"),
        sa.Column("first_name", sa.String(20), nullable=False,
                  comment="SEC-USR-FNAME X(20)"),
        sa.Column("last_name", sa.String(20), nullable=False,
                  comment="SEC-USR-LNAME X(20)"),
        sa.Column("password_hash", sa.String(255), nullable=False,
                  comment="bcrypt hash of password; replaces SEC-USR-PWD X(8) plain text"),
        sa.Column("user_type", sa.String(1), nullable=False,
                  comment="SEC-USR-TYPE X(1): A=Admin, U=Regular"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
        sa.CheckConstraint("user_type IN ('A', 'U')", name="chk_users_type"),
    )

    op.create_index("idx_users_last_name", "users", ["last_name"])
    op.create_index("idx_users_user_type", "users", ["user_type"])

    # Trigger: auto-update updated_at
    op.execute("""
        CREATE TRIGGER trg_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users;")
    op.drop_index("idx_users_user_type", table_name="users")
    op.drop_index("idx_users_last_name", table_name="users")
    op.drop_table("users")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
