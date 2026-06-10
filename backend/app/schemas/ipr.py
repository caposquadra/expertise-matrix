import uuid
from datetime import date, datetime

from pydantic import BaseModel


class IprGoalCreate(BaseModel):
    skill_id: uuid.UUID
    current_level: int
    target_level: int
    due_date: date | None = None
    notes: str | None = None


class IprGoalUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    due_date: date | None = None
    target_level: int | None = None


class IprGoalOut(BaseModel):
    id: uuid.UUID
    ipr_plan_id: uuid.UUID
    skill_id: uuid.UUID
    current_level: int
    target_level: int
    due_date: date | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IprPlanCreate(BaseModel):
    employee_id: uuid.UUID
    title: str
    description: str | None = None


class IprPlanUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class IprPlanOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    goals: list[IprGoalOut] = []

    model_config = {"from_attributes": True}
