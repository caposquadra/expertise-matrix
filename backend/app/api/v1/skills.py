import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.core.database import get_db
from app.models import Employee, Skill
from app.schemas.skill import SkillCreate, SkillOut, SkillUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[SkillOut])
async def list_skills(
    category: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_current_user),
):
    """List active skills. Optional category filter."""
    query = (
        select(Skill)
        .where(Skill.is_active)
        .order_by(Skill.sort_order, Skill.name)
        .offset(skip)
        .limit(limit)
    )
    if category:
        query = query.where(Skill.category == category)
    result = await db.execute(query)
    return [SkillOut.model_validate(s) for s in result.scalars().all()]


@router.get("/{skill_id}", response_model=SkillOut)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_current_user),
):
    """Get a single skill by ID."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found"
        )
    return SkillOut.model_validate(skill)


@router.post("", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
async def create_skill(
    body: SkillCreate,
    db: AsyncSession = Depends(get_db),
    admin: Employee = Depends(get_admin_user),
):
    """Create a new skill (admin only)."""
    skill = Skill(
        name=body.name,
        category=body.category,
        description=body.description,
        sort_order=body.sort_order,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    logger.info("Admin %s created skill %s", admin.email, skill.name)
    return SkillOut.model_validate(skill)


@router.patch("/{skill_id}", response_model=SkillOut)
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Employee = Depends(get_admin_user),
):
    """Update a skill (admin only). Supports partial updates."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found"
        )

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)

    await db.commit()
    await db.refresh(skill)
    logger.info("Admin %s updated skill %s", admin.email, skill.name)
    return SkillOut.model_validate(skill)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Employee = Depends(get_admin_user),
):
    """Soft-delete a skill (admin only). Marks is_active=False."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found"
        )

    skill.is_active = False
    await db.commit()
    logger.info("Admin %s deactivated skill %s", admin.email, skill.name)
