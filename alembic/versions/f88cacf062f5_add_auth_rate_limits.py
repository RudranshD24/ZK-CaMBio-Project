"""add_auth_rate_limits

Revision ID: f88cacf062f5
Revises: a536650ae477
Create Date: 2026-09-30 15:01:46.728965

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f88cacf062f5"
down_revision: str | Sequence[str] | None = "a536650ae477"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "auth_rate_limits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("identifier_type", sa.String(length=16), nullable=False),
        sa.Column("identifier_value", sa.String(length=128), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_auth_rate_limits_identifier_value"),
        "auth_rate_limits",
        ["identifier_value"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_auth_rate_limits_identifier_value"), table_name="auth_rate_limits")
    op.drop_table("auth_rate_limits")
