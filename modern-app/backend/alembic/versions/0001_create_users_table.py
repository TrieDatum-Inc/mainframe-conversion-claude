"""Create users table.

Maps the USRSEC VSAM KSDS to PostgreSQL (CSUSR01Y copybook layout).

VSAM record layout (80 bytes):
  SEC-USR-ID    PIC X(8)   → user_id    VARCHAR(8)  PRIMARY KEY
  SEC-USR-FNAME PIC X(20)  → first_name VARCHAR(20) NOT NULL
  SEC-USR-LNAME PIC X(20)  → last_name  VARCHAR(20) NOT NULL
  SEC-USR-PWD   PIC X(8)   → password_hash VARCHAR(255) NOT NULL (bcrypt)
  SEC-USR-TYPE  PIC X(1)   → user_type  VARCHAR(1)  NOT NULL CHECK IN ('A','U')
  FILLER        PIC X(23)  → (discarded — padding to 80 bytes)

Revision ID: 0001
Revises:
Create Date: 2026-04-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the users table."""
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(8), nullable=False, comment="SEC-USR-ID X(8)"),
        sa.Column(
            "first_name",
            sa.String(20),
            nullable=False,
            comment="SEC-USR-FNAME X(20)",
        ),
        sa.Column(
            "last_name",
            sa.String(20),
            nullable=False,
            comment="SEC-USR-LNAME X(20)",
        ),
        sa.Column(
            "password_hash",
            sa.String(255),
            nullable=False,
            comment="bcrypt hash of SEC-USR-PWD X(8)",
        ),
        sa.Column(
            "user_type",
            sa.String(1),
            nullable=False,
            comment="SEC-USR-TYPE: A=Admin, U=Regular",
        ),
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
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
        sa.CheckConstraint("user_type IN ('A', 'U')", name="ck_users_user_type"),
    )
    op.create_index("ix_users_user_type", "users", ["user_type"])
    op.create_index("ix_users_last_name", "users", ["last_name"])


def downgrade() -> None:
    """Drop the users table."""
    op.drop_index("ix_users_last_name", table_name="users")
    op.drop_index("ix_users_user_type", table_name="users")
    op.drop_table("users")
