import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.employee import Employee


class ReviewCycle(Base):
    __tablename__ = "review_cycles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "manager_review",
            "interview",
            "decision",
            "completed",
            "rejected",
            name="review_status",
        ),
        default="draft",
    )
    current_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    manager_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    expert_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_decision: Mapped[str | None] = mapped_column(
        Enum("promoted", "rejected", name="review_decision"), nullable=True
    )
    final_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )
    expert_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    employee: Mapped["Employee"] = relationship(
        "Employee", foreign_keys=[employee_id], back_populates="review_cycles"
    )
    manager: Mapped["Employee | None"] = relationship(
        "Employee", foreign_keys=[manager_id]
    )
    expert: Mapped["Employee | None"] = relationship(
        "Employee", foreign_keys=[expert_id]
    )
    assessments: Mapped[list["ReviewAssessment"]] = relationship(
        "ReviewAssessment", back_populates="review_cycle", cascade="all, delete-orphan"
    )


class ReviewAssessment(Base):
    __tablename__ = "review_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    review_cycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("review_cycles.id", ondelete="CASCADE")
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False
    )
    self_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    self_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expert_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    review_cycle: Mapped["ReviewCycle"] = relationship(
        "ReviewCycle", back_populates="assessments"
    )
