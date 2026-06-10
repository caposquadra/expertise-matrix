import uuid
from datetime import datetime

from pydantic import BaseModel


class SkillBase(BaseModel):
    name: str
    category: str
    description: str | None = None
    weight: int = 1
    sort_order: int = 0


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    weight: int | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class SkillOut(SkillBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
