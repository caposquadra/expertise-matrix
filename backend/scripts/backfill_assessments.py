"""Backfill default assessments for existing employees without them."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.constants import GRADE_TARGETS
from app.models import Assessment, Employee, Skill

DATABASE_URL = os.environ["DATABASE_URL"]


async def main() -> None:
    engine = create_async_engine(DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as db:
        employees = await db.execute(select(Employee).where(Employee.is_active))
        skills_result = await db.execute(select(Skill).where(Skill.is_active))
        active_skills = skills_result.scalars().all()

        total = 0
        for emp in employees.scalars().all():
            default_level = GRADE_TARGETS.get(emp.grade.lower() if emp.grade else "")
            if default_level is None:
                continue

            existing = await db.execute(
                select(Assessment).where(Assessment.employee_id == emp.id)
            )
            existing_ids = {a.skill_id for a in existing.scalars().all()}

            for skill in active_skills:
                if skill.id not in existing_ids:
                    db.add(
                        Assessment(
                            employee_id=emp.id,
                            skill_id=skill.id,
                            self_level=default_level,
                        )
                    )
                    total += 1

        await db.commit()
        print(f"Created {total} default assessments")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
