"""Add review tables and expert role

Revision ID: 5c1a8e4f3d2b
Revises: 394724e9b2fc
Create Date: 2026-06-06 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "5c1a8e4f3d2b"
down_revision: Union[str, None] = "394724e9b2fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE 'expert'")

    op.create_table(
        "review_cycles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "manager_review",
                "interview",
                "decision",
                "completed",
                "rejected",
                name="review_status",
            ),
            nullable=False,
        ),
        sa.Column("current_grade", sa.String(length=50), nullable=True),
        sa.Column("target_grade", sa.String(length=50), nullable=True),
        sa.Column("manager_comment", sa.Text(), nullable=True),
        sa.Column("expert_comment", sa.Text(), nullable=True),
        sa.Column(
            "final_decision",
            sa.Enum("promoted", "rejected", name="review_decision"),
            nullable=True,
        ),
        sa.Column("final_comment", sa.Text(), nullable=True),
        sa.Column("manager_id", sa.UUID(), nullable=True),
        sa.Column("expert_id", sa.UUID(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["manager_id"],
            ["employees.id"],
        ),
        sa.ForeignKeyConstraint(
            ["expert_id"],
            ["employees.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_cycles_employee_id", "review_cycles", ["employee_id"])
    op.create_index("ix_review_cycles_status", "review_cycles", ["status"])

    op.create_table(
        "review_assessments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("review_cycle_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("self_level", sa.Integer(), nullable=True),
        sa.Column("self_comment", sa.Text(), nullable=True),
        sa.Column("manager_level", sa.Integer(), nullable=True),
        sa.Column("expert_level", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["review_cycle_id"], ["review_cycles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "review_cycle_id", "skill_id", name="uq_review_cycle_skill"
        ),
    )
    op.create_index(
        "ix_review_assessments_review_cycle_id",
        "review_assessments",
        ["review_cycle_id"],
    )


def downgrade() -> None:
    op.drop_table("review_assessments")
    op.drop_table("review_cycles")
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM('admin', 'manager', 'employee')")
    op.execute(
        "ALTER TABLE employees ALTER COLUMN role TYPE user_role USING role::text::user_role"
    )
    op.execute("DROP TYPE user_role_old")
