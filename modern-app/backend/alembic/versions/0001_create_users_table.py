"""Create users table.

Revision ID: 0001
Revises:
Create Date: 2026-04-06

Maps the COBOL CSUSR01Y copybook / USRSEC VSAM KSDS to a relational table.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=8), nullable=False),
        sa.Column("first_name", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("user_type", sa.String(length=1), nullable=False, server_default="U"),
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
        sa.CheckConstraint("user_type IN ('A', 'U')", name="ck_users_user_type"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_user_id"), "users", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_user_id"), table_name="users")
    op.drop_table("users")
