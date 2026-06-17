import logging
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user, require_role
from app.api.v1.constants import GRADE_TARGETS, NEXT_GRADE
from app.core.database import get_db
from app.core.security import hash_password
from app.models import Assessment, Employee, EmployeeProfile, Skill, SkillGradeTarget
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeProfileOut,
    EmployeeProfileUpdate,
    EmployeeUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/employees", tags=["employees"])


class ScoresBatchRequest(BaseModel):
    employee_ids: list[str]


class EmployeeScoreOut(BaseModel):
    current_score: int
    target_score: int | None
    total_weight: int
    assessed_weight: int
    profile_grade: float | None = None
    profile_avg: float | None = None
    position: str | None = None


def _compute_score(
    skills: list[Skill], assessments: list[Assessment], grade: str | None
) -> EmployeeScoreOut:
    skill_map = {s.id: s.weight for s in skills}
    all_weight = sum(s.weight for s in skills)
    cur_sum = 0
    assessed_weight = 0

    for a in assessments:
        w = skill_map.get(a.skill_id, 1)
        effective = a.manager_level if a.manager_level is not None else a.self_level
        if effective is not None:
            cur_sum += effective * w
            assessed_weight += w

    target = GRADE_TARGETS.get(grade) if grade else None
    return EmployeeScoreOut(
        current_score=cur_sum,
        target_score=target * all_weight if target else None,
        total_weight=all_weight,
        assessed_weight=assessed_weight,
    )


@router.get("", response_model=list[EmployeeOut])
async def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """List employees. Admins and managers see all; employees see only themselves."""
    if current_user.role in ("admin", "manager"):
        result = await db.execute(
            select(Employee).order_by(Employee.full_name).offset(skip).limit(limit)
        )
        return [EmployeeOut.model_validate(u) for u in result.scalars().all()]
    return [EmployeeOut.model_validate(current_user)]


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get a single employee by ID."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    if current_user.role not in ("admin", "manager") and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return EmployeeOut.model_validate(user)


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(
    body: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    admin: Employee = Depends(get_admin_user),
):
    """Create a new employee (admin only)."""
    result = await db.execute(select(Employee).where(Employee.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )

    user = Employee(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        grade=body.grade,
        team_id=body.team_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("Admin %s created employee %s (%s)", admin.email, user.email, user.role)
    return EmployeeOut.model_validate(user)


@router.patch("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: str,
    body: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Employee = Depends(get_admin_user),
):
    """Update an employee (admin only). Supports partial updates."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )

    update_data = body.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
        user.token_version += 1

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    logger.info("Admin %s updated employee %s", admin.email, user.email)
    return EmployeeOut.model_validate(user)


@router.get("/{employee_id}/score", response_model=EmployeeScoreOut)
async def get_employee_score(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get weighted score for an employee. Admins/managers see any; employees see own."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if emp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found"
        )
    if current_user.role not in ("admin", "manager") and current_user.id != emp.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    skills_result = await db.execute(select(Skill).where(Skill.is_active))
    skills = list(skills_result.scalars().all())

    assessments_result = await db.execute(
        select(Assessment).where(Assessment.employee_id == employee_id)
    )
    assessments = list(assessments_result.scalars().all())

    return _compute_score(skills, assessments, emp.grade)


@router.post("/scores", response_model=dict[str, EmployeeScoreOut])
async def get_bulk_scores(
    body: ScoresBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get weighted scores for multiple employees in one request."""
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    skills_result = await db.execute(select(Skill).where(Skill.is_active))
    skills = list(skills_result.scalars().all())

    employees = await db.execute(
        select(Employee).where(Employee.id.in_(body.employee_ids))
    )
    employees_map = {str(e.id): e for e in employees.scalars().all()}

    profile_result = await db.execute(
        select(EmployeeProfile).where(
            EmployeeProfile.employee_id.in_(body.employee_ids)
        )
    )
    profiles_map = {str(p.employee_id): p for p in profile_result.scalars().all()}

    grade_targets_result = await db.execute(select(SkillGradeTarget))
    grade_targets = {
        (str(t.skill_id), t.grade): t.expected_level
        for t in grade_targets_result.scalars().all()
    }

    assessments_result = await db.execute(
        select(Assessment).where(Assessment.employee_id.in_(body.employee_ids))
    )
    assessments_by_employee: dict[str, list[Assessment]] = defaultdict(list)
    for a in assessments_result.scalars().all():
        assessments_by_employee[str(a.employee_id)].append(a)

    result: dict[str, EmployeeScoreOut] = {}
    for eid in body.employee_ids:
        emp = employees_map.get(eid)
        if emp is None:
            continue
        assessments = assessments_by_employee.get(eid, [])
        score = _compute_score(skills, assessments, emp.grade)
        if emp.grade:
            next_grade = NEXT_GRADE.get(emp.grade.lower())
            target_sum = 0
            for skill in skills:
                expected = (
                    grade_targets.get((str(skill.id), next_grade))
                    if next_grade
                    else None
                )
                if expected is not None:
                    target_sum += expected * skill.weight
            if target_sum > 0:
                score.target_score = target_sum
        profile = profiles_map.get(eid)
        if profile:
            vals = [
                profile.experience,
                profile.education,
                profile.task_complexity,
                profile.autonomy,
                profile.communication,
                profile.control,
                profile.mentoring,
                profile.responsibility,
                profile.technical_competencies,
            ]
            score.profile_grade = round(sum(vals) / len(vals), 1)
            score.profile_avg = score.profile_grade
            score.position = profile.position or None
        result[eid] = score

    return result


@router.get("/{employee_id}/profile", response_model=EmployeeProfileOut | None)
async def get_employee_profile(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get extended profile for an employee. Manager sees any; employee sees own."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    if current_user.role not in ("admin", "manager") and current_user.id != emp.id:
        raise HTTPException(status_code=403, detail="Access denied")

    profile_result = await db.execute(
        select(EmployeeProfile).where(EmployeeProfile.employee_id == employee_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        return None

    values = [
        profile.experience,
        profile.education,
        profile.task_complexity,
        profile.autonomy,
        profile.communication,
        profile.control,
        profile.mentoring,
        profile.responsibility,
        profile.technical_competencies,
    ]
    grade = round(sum(values) / len(values), 1)

    out = EmployeeProfileOut.model_validate(profile)
    out.grade = grade
    return out


@router.put(
    "/{employee_id}/profile",
    response_model=EmployeeProfileOut,
)
async def update_employee_profile(
    employee_id: str,
    body: EmployeeProfileUpdate,
    db: AsyncSession = Depends(get_db),
    manager: Employee = Depends(require_role("admin", "manager")),
):
    """Create or update extended profile for an employee (manager only)."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    profile_result = await db.execute(
        select(EmployeeProfile).where(EmployeeProfile.employee_id == employee_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        profile = EmployeeProfile(employee_id=emp.id)
        db.add(profile)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    values = [
        profile.experience,
        profile.education,
        profile.task_complexity,
        profile.autonomy,
        profile.communication,
        profile.control,
        profile.mentoring,
        profile.responsibility,
        profile.technical_competencies,
    ]
    grade = round(sum(values) / len(values), 1)

    out = EmployeeProfileOut.model_validate(profile)
    out.grade = grade
    return out
