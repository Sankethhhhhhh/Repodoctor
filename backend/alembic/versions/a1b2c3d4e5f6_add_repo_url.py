"""add repo_url to reports

Revision ID: a1b2c3d4e5f6
Revises: 763ae5a47e25
Create Date: 2026-07-17 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "763ae5a47e25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("repo_url", sa.String(length=512), nullable=False, server_default=""))
    op.execute("UPDATE reports SET repo_url = 'https://github.com/' || repo_full_name WHERE repo_url = ''")


def downgrade() -> None:
    op.drop_column("reports", "repo_url")
