"""Add FK indexes for performance

Revision ID: 394724e9b2fc
Revises: 0cb1459385e8
Create Date: 2026-06-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = '394724e9b2fc'
down_revision: Union[str, None] = '0cb1459385e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_assessments_employee_id', 'assessments', ['employee_id'])
    op.create_index('ix_assessments_skill_id', 'assessments', ['skill_id'])
    op.create_index('ix_assessment_history_assessment_id', 'assessment_history', ['assessment_id'])
    op.create_index('ix_ipr_plans_employee_id', 'ipr_plans', ['employee_id'])


def downgrade() -> None:
    op.drop_index('ix_assessments_employee_id', table_name='assessments')
    op.drop_index('ix_assessments_skill_id', table_name='assessments')
    op.drop_index('ix_assessment_history_assessment_id', table_name='assessment_history')
    op.drop_index('ix_ipr_plans_employee_id', table_name='ipr_plans')
