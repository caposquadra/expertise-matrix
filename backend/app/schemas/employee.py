import uuid
from datetime import datetime

from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "employee"
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
