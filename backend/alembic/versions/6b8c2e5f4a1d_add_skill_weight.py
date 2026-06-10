"""Add weight column to skills table

Revision ID: 6b8c2e5f4a1d
Revises: 5c1a8e4f3d2b
Create Date: 2026-06-09 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '6b8c2e5f4a1d'
down_revision: Union[str, None] = '5c1a8e4f3d2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('skills', sa.Column('weight', sa.Integer(), nullable=False, server_default='1'))
    op.alter_column('skills', 'weight', server_default=None)


def downgrade() -> None:
    op.drop_column('skills', 'weight')
