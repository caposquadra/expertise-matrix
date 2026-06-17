import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AssessmentUpdate(BaseModel):
    self_level: int | None = Field(None, ge=1, le=3)
    manager_level: int | None = Field(None, ge=1, le=3)
    target_level: int | None = Field(None, ge=1, le=3)


class TargetUpdate(BaseModel):
    target_level: int = Field(..., ge=1, le=3)


class BulkTargetUpdate(BaseModel):
    target_level: int = Field(..., ge=1, le=3)


class AssessmentOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    skill_id: uuid.UUID
    self_level: int | None = None
    manager_level: int | None = None
    target_level: int | None = None
    updated_by: uuid.UUID | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssessmentHistoryOut(BaseModel):
    id: uuid.UUID
    field_name: str
    old_value: int | None = None
    new_value: int | None = None
    changed_by: uuid.UUID | None = None
    changed_at: datetime

    model_config = {"from_attributes": True}
