import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.employee import Employee


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), unique=True, nullable=False
    )
    organization: Mapped[str] = mapped_column(String(255), default="ВРМ")
    city: Mapped[str] = mapped_column(String(255), default="Санкт-Петербург")
    department: Mapped[str] = mapped_column(String(255), default="")
    subdivision: Mapped[str] = mapped_column(
        String(255), default="Отдел тестирования ВРМ"
    )
    position: Mapped[str] = mapped_column(String(255), default="")
    specialization: Mapped[str] = mapped_column(String(255), default="")
    experience: Mapped[int] = mapped_column(Integer, default=8)
    education: Mapped[int] = mapped_column(Integer, default=8)
    task_complexity: Mapped[int] = mapped_column(Integer, default=8)
    autonomy: Mapped[int] = mapped_column(Integer, default=8)
    communication: Mapped[int] = mapped_column(Integer, default=8)
    control: Mapped[int] = mapped_column(Integer, default=8)
    mentoring: Mapped[int] = mapped_column(Integer, default=8)
    responsibility: Mapped[int] = mapped_column(Integer, default=8)
    technical_competencies: Mapped[int] = mapped_column(Integer, default=8)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    employee: Mapped["Employee"] = relationship("Employee", back_populates="profile")
