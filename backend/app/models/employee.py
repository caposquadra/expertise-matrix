import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.ipr import IprPlan
    from app.models.review import ReviewCycle


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    employees: Mapped[list["Employee"]] = relationship(
        "Employee", back_populates="team"
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        Enum("admin", "manager", "employee", "expert", name="user_role"),
        default="employee",
    )
    grade: Mapped[str | None] = mapped_column(
        Enum("junior", "middle", "senior", name="employee_grade"), nullable=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    team: Mapped[Team | None] = relationship("Team", back_populates="employees")
    assessments: Mapped[list["Assessment"]] = relationship(
        "Assessment", back_populates="employee", foreign_keys="[Assessment.employee_id]"
    )
    ipr_plans: Mapped[list["IprPlan"]] = relationship(
        "IprPlan", back_populates="employee", foreign_keys="[IprPlan.employee_id]"
    )
    review_cycles: Mapped[list["ReviewCycle"]] = relationship(
        "ReviewCycle",
        back_populates="employee",
        foreign_keys="[ReviewCycle.employee_id]",
    )
