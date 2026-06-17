import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.auth import RoleEnum


class EmployeeProfileUpdate(BaseModel):
    organization: str | None = None
    city: str | None = None
    department: str | None = None
    subdivision: str | None = None
    position: str | None = None
    specialization: str | None = None
    experience: int | None = None
    education: int | None = None
    task_complexity: int | None = None
    autonomy: int | None = None
    communication: int | None = None
    control: int | None = None
    mentoring: int | None = None
    responsibility: int | None = None
    technical_competencies: int | None = None
    notes: str | None = None

    @field_validator(
        "experience",
        "education",
        "task_complexity",
        "autonomy",
        "communication",
        "control",
        "mentoring",
        "responsibility",
        "technical_competencies",
    )
    @classmethod
    def validate_scale(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 12):
            raise ValueError("Value must be between 1 and 12")
        return v


class EmployeeProfileOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    organization: str
    city: str
    department: str
    subdivision: str
    position: str
    specialization: str
    experience: int
    education: int
    task_complexity: int
    autonomy: int
    communication: int
    control: int
    mentoring: int
    responsibility: int
    technical_competencies: int
    notes: str | None = None
    grade: float = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: RoleEnum = RoleEnum.employee
    grade: str | None = None
    team_id: uuid.UUID | None = None


class EmployeeUpdate(BaseModel):
    email: str | None = None
    password: str | None = None
    full_name: str | None = None
    role: str | None = None
    grade: str | None = None
    team_id: uuid.UUID | None = None
    is_active: bool | None = None


class EmployeeOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    grade: str | None = None
    team_id: uuid.UUID | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
