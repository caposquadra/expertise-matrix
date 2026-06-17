import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_manager_user
from app.core.database import get_db
from app.models import Assessment, AssessmentHistory, Employee
from app.schemas.assessment import (
    AssessmentHistoryOut,
    AssessmentOut,
    AssessmentUpdate,
    BulkTargetUpdate,
    TargetUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessments", tags=["assessments"])


async def _record_history(
    db: AsyncSession,
    assessment: Assessment,
    field_name: str,
    old_value: int | None,
    new_value: int | None,
    changed_by: uuid.UUID,
) -> None:
    if old_value == new_value:
        return
    entry = AssessmentHistory(
        assessment_id=assessment.id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        changed_by=changed_by,
    )
    db.add(entry)


@router.get("", response_model=list[AssessmentOut])
async def list_assessments(
    employee_id: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """List assessments. Employees see only their own; managers can filter by employee_id."""
    query = select(Assessment)
    if employee_id:
        if (
            current_user.role not in ("admin", "manager")
            and str(current_user.id) != employee_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        query = query.where(Assessment.employee_id == employee_id)
    elif current_user.role == "employee":
        query = query.where(Assessment.employee_id == current_user.id)
    elif current_user.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    result = await db.execute(query.offset(skip).limit(limit))
    return [AssessmentOut.model_validate(a) for a in result.scalars().all()]


@router.get("/matrix", response_model=list[AssessmentOut])
async def get_matrix(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Return all assessments for the matrix view (manager/admin only)."""
    result = await db.execute(select(Assessment))
    return [AssessmentOut.model_validate(a) for a in result.scalars().all()]


@router.put("/bulk-target", response_model=list[AssessmentOut])
async def bulk_set_target(
    body: BulkTargetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Set the same target_level for all skills of the current user (manager only)."""
    result = await db.execute(
        select(Assessment).where(Assessment.employee_id == current_user.id)
    )
    assessments = result.scalars().all()
    for a in assessments:
        await _record_history(
            db, a, "target_level", a.target_level, body.target_level, current_user.id
        )
        a.target_level = body.target_level
        a.updated_by = current_user.id
    await db.commit()
    for a in assessments:
        await db.refresh(a)
    return [AssessmentOut.model_validate(a) for a in assessments]


@router.put("/{skill_id}", response_model=AssessmentOut)
async def upsert_assessment(
    skill_id: str,
    body: AssessmentUpdate,
    employee_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Create or update an assessment. Employees set self_level; managers set manager_level via ?employee_id=."""
    if body.self_level is not None and body.manager_level is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Send only self_level or manager_level, not both",
        )

    target_employee_id = current_user.id
    if employee_id is not None:
        if current_user.role not in ("admin", "manager"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can specify employee_id",
            )
        target_employee_id = uuid.UUID(employee_id)

    result = await db.execute(
        select(Assessment).where(
            Assessment.employee_id == target_employee_id,
            Assessment.skill_id == skill_id,
        )
    )
    assessment = result.scalar_one_or_none()

    if assessment is None:
        assessment = Assessment(
            employee_id=target_employee_id,
            skill_id=skill_id,
        )
        db.add(assessment)
        await db.flush()

    if current_user.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can modify assessments outside review cycles",
        )

    if body.target_level is not None:
        await _record_history(
            db,
            assessment,
            "target_level",
            assessment.target_level,
            body.target_level,
            current_user.id,
        )
        assessment.target_level = body.target_level
        assessment.updated_by = current_user.id
    if body.self_level is not None:
        await _record_history(
            db,
            assessment,
            "self_level",
            assessment.self_level,
            body.self_level,
            current_user.id,
        )
        assessment.self_level = body.self_level
        assessment.updated_by = current_user.id
    if body.manager_level is not None:
        await _record_history(
            db,
            assessment,
            "manager_level",
            assessment.manager_level,
            body.manager_level,
            current_user.id,
        )
        assessment.manager_level = body.manager_level
        assessment.updated_by = current_user.id

    await db.commit()
    await db.refresh(assessment)
    return AssessmentOut.model_validate(assessment)


@router.patch("/{assessment_id}/target", response_model=AssessmentOut)
async def set_target(
    assessment_id: str,
    body: TargetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Set target_level for a specific assessment (manager only)."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    await _record_history(
        db,
        assessment,
        "target_level",
        assessment.target_level,
        body.target_level,
        current_user.id,
    )
    assessment.target_level = body.target_level
    assessment.updated_by = current_user.id

    await db.commit()
    await db.refresh(assessment)
    return AssessmentOut.model_validate(assessment)


@router.get("/{assessment_id}/history", response_model=list[AssessmentHistoryOut])
async def get_assessment_history(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get change history for an assessment."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    if current_user.role not in ("admin", "manager") and str(current_user.id) != str(
        assessment.employee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    hist_result = await db.execute(
        select(AssessmentHistory)
        .where(AssessmentHistory.assessment_id == assessment_id)
        .order_by(AssessmentHistory.changed_at.desc())
    )
    return [AssessmentHistoryOut.model_validate(h) for h in hist_result.scalars().all()]
