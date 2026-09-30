"""add_users_kdf_salt

Revision ID: c7b91d2e3f4a
Revises: f88cacf062f5
Create Date: 2026-09-30 23:15:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7b91d2e3f4a"
down_revision: str | Sequence[str] | None = "f88cacf062f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: add per-user kdf_salt column to users table."""
    op.add_column("users", sa.Column("kdf_salt", sa.String(length=64), nullable=True))


def downgrade() -> None:
    """Downgrade schema: remove kdf_salt from users table."""
    op.drop_column("users", "kdf_salt")
