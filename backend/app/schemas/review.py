import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewAssessmentUpdate(BaseModel):
    self_level: int | None = Field(None, ge=1, le=3)
    self_comment: str | None = None
    manager_level: int | None = Field(None, ge=1, le=3)
    expert_level: int | None = Field(None, ge=1, le=3)


class ReviewAssessmentOut(BaseModel):
    id: uuid.UUID
    review_cycle_id: uuid.UUID
    skill_id: uuid.UUID
    self_level: int | None = None
    self_comment: str | None = None
    manager_level: int | None = None
    expert_level: int | None = None
    target_level: int | None = None

    model_config = {"from_attributes": True}


class ReviewCycleCreate(BaseModel):
    target_grade: str


class ReviewCycleSubmit(BaseModel):
    pass


class ReviewCycleManagerReview(BaseModel):
    manager_comment: str | None = None


class ReviewCycleExpertReview(BaseModel):
    expert_comment: str | None = None


class ReviewCycleFinalize(BaseModel):
    decision: str  # "promoted" or "rejected"
    comment: str | None = None


class ReviewCycleOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    status: str
    current_grade: str | None = None
    target_grade: str | None = None
    manager_comment: str | None = None
    expert_comment: str | None = None
    final_decision: str | None = None
    final_comment: str | None = None
    manager_id: uuid.UUID | None = None
    expert_id: uuid.UUID | None = None
    submitted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    assessments: list[ReviewAssessmentOut] = []

    model_config = {"from_attributes": True}
