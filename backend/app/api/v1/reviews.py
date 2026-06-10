import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_manager_user
from app.core.database import get_db
from app.models import Assessment, Employee, ReviewAssessment, ReviewCycle, Skill
from app.schemas.review import (
    ReviewAssessmentOut,
    ReviewAssessmentUpdate,
    ReviewCycleCreate,
    ReviewCycleExpertReview,
    ReviewCycleFinalize,
    ReviewCycleManagerReview,
    ReviewCycleOut,
    ReviewCycleSubmit,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _require_status(cycle: ReviewCycle, expected: str):
    if cycle.status != expected:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Expected status '{expected}', got '{cycle.status}'",
        )


async def _get_cycle(db: AsyncSession, cycle_id: str) -> ReviewCycle:
    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.assessments))
        .where(ReviewCycle.id == cycle_id)
    )
    cycle = result.scalar_one_or_none()
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review cycle not found"
        )
    return cycle


# ── Employee endpoints ─────────────────────────────────────────────


@router.get("", response_model=list[ReviewCycleOut])
async def list_review_cycles(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """List review cycles for the current employee. Managers see all."""
    query = select(ReviewCycle).options(selectinload(ReviewCycle.assessments))
    if current_user.role == "employee":
        query = query.where(ReviewCycle.employee_id == current_user.id)
    elif current_user.role not in ("admin", "manager", "expert"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    query = query.order_by(ReviewCycle.created_at.desc())
    result = await db.execute(query)
    return [ReviewCycleOut.model_validate(c) for c in result.scalars().all()]


@router.post("", response_model=ReviewCycleOut, status_code=status.HTTP_201_CREATED)
async def create_review_cycle(
    body: ReviewCycleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Start a new self-assessment review cycle."""
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can start a review",
        )

    # Check no active draft cycle exists
    existing = await db.execute(
        select(ReviewCycle).where(
            ReviewCycle.employee_id == current_user.id,
            ReviewCycle.status.in_(
                ["draft", "manager_review", "interview", "decision"]
            ),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active review cycle",
        )

    cycle = ReviewCycle(
        employee_id=current_user.id,
        current_grade=current_user.grade,
        target_grade=body.target_grade,
    )
    db.add(cycle)
    await db.flush()

    # Create empty assessments for all active skills
    skills_result = await db.execute(select(Skill).where(Skill.is_active))
    for skill in skills_result.scalars().all():
        db.add(ReviewAssessment(review_cycle_id=cycle.id, skill_id=skill.id))

    await db.commit()
    await db.refresh(cycle)

    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.assessments))
        .where(ReviewCycle.id == cycle.id)
    )
    logger.info("Employee %s started review cycle %s", current_user.email, cycle.id)
    return ReviewCycleOut.model_validate(result.scalar_one())


@router.get("/{cycle_id}", response_model=ReviewCycleOut)
async def get_review_cycle(
    cycle_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get a review cycle with assessments."""
    cycle = await _get_cycle(db, cycle_id)
    if current_user.role == "employee" and str(current_user.id) != str(
        cycle.employee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return ReviewCycleOut.model_validate(cycle)


@router.put("/{cycle_id}/assessments/{skill_id}", response_model=ReviewAssessmentOut)
async def update_assessment(
    cycle_id: str,
    skill_id: str,
    body: ReviewAssessmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Update an assessment within a review cycle. Role determines which fields can be set."""
    cycle = await _get_cycle(db, cycle_id)

    if current_user.role == "employee":
        if str(current_user.id) != str(cycle.employee_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        _require_status(cycle, "draft")
    elif current_user.role in ("admin", "manager", "expert"):
        if cycle.status not in ("manager_review", "interview"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot edit in status '{cycle.status}'",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    result = await db.execute(
        select(ReviewAssessment).where(
            ReviewAssessment.review_cycle_id == cycle_id,
            ReviewAssessment.skill_id == skill_id,
        )
    )
    assessment = result.scalar_one_or_none()
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    if current_user.role == "employee":
        if body.self_level is not None:
            assessment.self_level = body.self_level
        if body.self_comment is not None:
            assessment.self_comment = body.self_comment
    elif current_user.role in ("admin", "manager"):
        if body.manager_level is not None:
            assessment.manager_level = body.manager_level
    elif current_user.role == "expert":
        if body.expert_level is not None:
            assessment.expert_level = body.expert_level

    await db.commit()
    await db.refresh(assessment)
    return ReviewAssessmentOut.model_validate(assessment)


@router.post("/{cycle_id}/submit", response_model=ReviewCycleOut)
async def submit_review(
    cycle_id: str,
    body: ReviewCycleSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Submit self-assessment to manager."""
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can submit"
        )

    cycle = await _get_cycle(db, cycle_id)
    if str(current_user.id) != str(cycle.employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    _require_status(cycle, "draft")

    # Verify at least one skill has self_level and self_comment
    has_filled = any(
        a.self_level is not None and a.self_comment and a.self_comment.strip()
        for a in cycle.assessments
    )
    if not has_filled:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one skill must have a self-assessment with a comment before submitting",
        )

    cycle.status = "manager_review"
    cycle.submitted_at = datetime.now(timezone.utc)
    await db.commit()

    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.assessments))
        .where(ReviewCycle.id == cycle.id)
    )
    logger.info("Employee %s submitted review %s", current_user.email, cycle.id)
    return ReviewCycleOut.model_validate(result.scalar_one())


# ── Manager endpoints ──────────────────────────────────────────────


@router.get("/pending/manager", response_model=list[ReviewCycleOut])
async def list_pending_manager(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """List review cycles awaiting manager review."""
    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.assessments))
        .where(ReviewCycle.status == "manager_review")
        .order_by(ReviewCycle.submitted_at)
    )
    return [ReviewCycleOut.model_validate(c) for c in result.scalars().all()]


@router.post("/{cycle_id}/manager-review", response_model=ReviewCycleOut)
async def manager_review(
    cycle_id: str,
    body: ReviewCycleManagerReview,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Send review to interview stage after manager completes their assessment."""
    cycle = await _get_cycle(db, cycle_id)
    _require_status(cycle, "manager_review")

    # Verify all skills have manager_level set
    for a in cycle.assessments:
        if a.manager_level is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="All skills must have a manager assessment before proceeding",
            )

    cycle.status = "interview"
    cycle.manager_id = current_user.id
    if body.manager_comment is not None:
        cycle.manager_comment = body.manager_comment
    await db.commit()

    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.assessments))
        .where(ReviewCycle.id == cycle.id)
    )
    logger.info(
        "Manager %s reviewed %s, sent to interview", current_user.email, cycle.id
    )
    return ReviewCycleOut.model_validate(result.scalar_one())


# ── Expert endpoints ───────────────────────────────────────────────


@router.get("/pending/interview", response_model=list[ReviewCycleOut])
async def list_pending_interview(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """List review cycles awaiting expert interview (experts and managers)."""
    if current_user.role not in ("admin", "manager", "expert"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.assessments))
        .where(ReviewCycle.status == "interview")
        .order_by(ReviewCycle.updated_at)
    )
    return [ReviewCycleOut.model_validate(c) for c in result.scalars().all()]


@router.post("/{cycle_id}/expert-review", response_model=ReviewCycleOut)
async def expert_review(
    cycle_id: str,
    body: ReviewCycleExpertReview,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Complete expert interview and send back to manager for decision."""
    if current_user.role not in ("admin", "expert"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only experts can perform interview review",
        )

    cycle = await _get_cycle(db, cycle_id)
    _require_status(cycle, "interview")

    # Verify all skills have expert_level set
    for a in cycle.assessments:
        if a.expert_level is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="All skills must have an expert assessment before completing interview",
            )

    cycle.status = "decision"
    cycle.expert_id = current_user.id
    if body.expert_comment is not None:
        cycle.expert_comment = body.expert_comment
    await db.commit()

    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.assessments))
        .where(ReviewCycle.id == cycle.id)
    )
    logger.info("Expert %s completed interview for %s", current_user.email, cycle.id)
    return ReviewCycleOut.model_validate(result.scalar_one())


# ── Final decision (manager) ───────────────────────────────────────


@router.get("/pending/decision", response_model=list[ReviewCycleOut])
async def list_pending_decision(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """List review cycles awaiting final decision."""
    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.assessments))
        .where(ReviewCycle.status == "decision")
        .order_by(ReviewCycle.updated_at)
    )
    return [ReviewCycleOut.model_validate(c) for c in result.scalars().all()]


@router.post("/{cycle_id}/finalize", response_model=ReviewCycleOut)
async def finalize_review(
    cycle_id: str,
    body: ReviewCycleFinalize,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Make a final decision: promote or reject."""
    if body.decision not in ("promoted", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Decision must be 'promoted' or 'rejected'",
        )

    cycle = await _get_cycle(db, cycle_id)
    _require_status(cycle, "decision")

    cycle.status = "completed" if body.decision == "promoted" else "rejected"
    cycle.final_decision = body.decision
    if body.comment is not None:
        cycle.final_comment = body.comment

    if body.decision == "promoted":
        result = await db.execute(
            select(Employee).where(Employee.id == cycle.employee_id)
        )
        employee = result.scalar_one_or_none()
        if employee is not None and cycle.target_grade is not None:
            employee.grade = cycle.target_grade

        for ra in cycle.assessments:
            existing = await db.execute(
                select(Assessment).where(
                    Assessment.employee_id == cycle.employee_id,
                    Assessment.skill_id == ra.skill_id,
                )
            )
            assessment = existing.scalar_one_or_none()
            if assessment is None:
                assessment = Assessment(
                    employee_id=cycle.employee_id,
                    skill_id=ra.skill_id,
                )
                db.add(assessment)
            assessment.self_level = ra.self_level
            assessment.manager_level = ra.expert_level or ra.manager_level

    await db.commit()

    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.assessments))
        .where(ReviewCycle.id == cycle.id)
    )
    logger.info(
        "Manager %s finalized review %s: %s",
        current_user.email,
        cycle.id,
        body.decision,
    )
    return ReviewCycleOut.model_validate(result.scalar_one())


@router.delete("/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review_cycle(
    cycle_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Delete a draft review cycle (employee only, must be draft)."""
    cycle = await _get_cycle(db, cycle_id)
    if current_user.role != "employee" or str(current_user.id) != str(
        cycle.employee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can delete"
        )
    _require_status(cycle, "draft")

    await db.delete(cycle)
    await db.commit()
    logger.info("Employee %s deleted review cycle %s", current_user.email, cycle.id)


@router.post("/{cycle_id}/return-to-draft", response_model=ReviewCycleOut)
async def return_review_to_draft(
    cycle_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Return a review cycle back to draft status (manager only, must be in manager_review)."""
    cycle = await _get_cycle(db, cycle_id)
    if str(current_user.id) == str(cycle.employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee cannot return their own review",
        )
    _require_status(cycle, "manager_review")

    cycle.status = "draft"
    cycle.submitted_at = None
    await db.commit()
    await db.refresh(cycle)

    logger.info(
        "Manager %s returned review cycle %s to draft", current_user.email, cycle.id
    )
    return ReviewCycleOut.model_validate(cycle)
