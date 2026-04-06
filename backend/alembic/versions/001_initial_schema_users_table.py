"""
Initial schema: create users table.

Revision ID: 001
Revises: (none — initial migration)
Create Date: 2026-04-06

COBOL source: USRSEC VSAM KSDS (CSUSR01Y copybook)
This migration replaces the VSAM IDCAMS DEFINE CLUSTER command for USRSEC.

Key change: SEC-USR-PWD X(8) plain text → password_hash VARCHAR(255) bcrypt.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# Revision identifiers used by Alembic
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create the users table.

    Maps VSAM IDCAMS DEFINE CLUSTER:
        DEFINE CLUSTER (NAME(USRSEC) KEYS(8 0) RECORDSIZE(80 80))

    PostgreSQL equivalent with security improvements:
    - password_hash replaces SEC-USR-PWD (bcrypt, not plain text)
    - CHECK constraint enforces user_type IN ('A', 'U')
    - Indexes on last_name and user_type for efficient queries
    """
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(8), nullable=False, comment="COBOL: SEC-USR-ID PIC X(08)"),
        sa.Column("first_name", sa.String(20), nullable=False, comment="COBOL: SEC-USR-FNAME PIC X(20)"),
        sa.Column("last_name", sa.String(20), nullable=False, comment="COBOL: SEC-USR-LNAME PIC X(20)"),
        sa.Column(
            "password_hash",
            sa.String(255),
            nullable=False,
            comment="COBOL: SEC-USR-PWD PIC X(08) — bcrypt hash; NEVER plain text",
        ),
        sa.Column(
            "user_type",
            sa.CHAR(1),
            nullable=False,
            comment="COBOL: SEC-USR-TYPE PIC X(01) — A=Admin, U=User",
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
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
        sa.CheckConstraint("user_type IN ('A', 'U')", name="chk_users_type"),
    )

    # Index for user list browsing by last name (COUSR00C display order)
    op.create_index("idx_users_last_name", "users", ["last_name"])

    # Index for role-based queries
    op.create_index("idx_users_user_type", "users", ["user_type"])

    # Trigger function for auto-updating updated_at
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
        CREATE TRIGGER trg_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """
    Drop the users table and related objects.

    Maps VSAM IDCAMS DELETE command for USRSEC cluster.
    WARNING: This drops all user data. Ensure backups exist before running.
    """
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    op.drop_index("idx_users_user_type", table_name="users")
    op.drop_index("idx_users_last_name", table_name="users")
    op.drop_table("users")
