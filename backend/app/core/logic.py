import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.constants import GRADE_TARGETS
from app.models import Assessment, Skill


async def fill_default_assessments(
    db: AsyncSession, employee_id: uuid.UUID, grade: str
) -> None:
    default_level = GRADE_TARGETS.get(grade.lower())
    if default_level is None:
        return
    result = await db.execute(select(Skill).where(Skill.is_active))
    skills = result.scalars().all()
    for skill in skills:
        assessment = Assessment(
            employee_id=employee_id,
            skill_id=skill.id,
            self_level=default_level,
        )
        db.add(assessment)
    await db.commit()
