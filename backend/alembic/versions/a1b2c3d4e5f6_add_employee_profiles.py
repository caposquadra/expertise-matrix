"""Add employee_profiles table

Revision ID: a1b2c3d4e5f6
Revises: 09f2093ec28e
Create Date: 2026-06-10 16:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "09f2093ec28e"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "employee_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("organization", sa.String(255), nullable=False, server_default="ВРМ"),
        sa.Column(
            "city", sa.String(255), nullable=False, server_default="Санкт-Петербург"
        ),
        sa.Column("department", sa.String(255), nullable=False, server_default=""),
        sa.Column(
            "subdivision",
            sa.String(255),
            nullable=False,
            server_default="Отдел тестирования ВРМ",
        ),
        sa.Column("position", sa.String(255), nullable=False, server_default=""),
        sa.Column("specialization", sa.String(255), nullable=False, server_default=""),
        sa.Column("experience", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("education", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("task_complexity", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("autonomy", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("communication", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("control", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("mentoring", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("responsibility", sa.Integer(), nullable=False, server_default="8"),
        sa.Column(
            "technical_competencies", sa.Integer(), nullable=False, server_default="8"
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_employee_profiles_employee_id",
        "employee_profiles",
        ["employee_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_employee_profiles_employee_id")
    op.drop_table("employee_profiles")
