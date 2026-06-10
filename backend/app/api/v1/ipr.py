import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_manager_user
from app.core.database import get_db
from app.models import Employee, IprGoal, IprPlan
from app.schemas.ipr import (
    IprGoalCreate,
    IprGoalOut,
    IprGoalUpdate,
    IprPlanCreate,
    IprPlanOut,
    IprPlanUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ipr-plans", tags=["ipr"])


@router.get("", response_model=list[IprPlanOut])
async def list_ipr_plans(
    employee_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """List IPR plans. Employees see only their own; managers can filter by employee_id."""
    query = select(IprPlan).options(selectinload(IprPlan.goals))

    if employee_id:
        if (
            current_user.role not in ("admin", "manager")
            and str(current_user.id) != employee_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        query = query.where(IprPlan.employee_id == employee_id)
    elif current_user.role == "employee":
        query = query.where(IprPlan.employee_id == current_user.id)
    elif current_user.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    query = query.order_by(IprPlan.created_at.desc())
    result = await db.execute(query)
    return [IprPlanOut.model_validate(p) for p in result.scalars().all()]


@router.post("", response_model=IprPlanOut, status_code=status.HTTP_201_CREATED)
async def create_ipr_plan(
    body: IprPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Create an IPR plan for an employee (manager only)."""
    plan = IprPlan(
        employee_id=body.employee_id,
        title=body.title,
        description=body.description,
        created_by=current_user.id,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    result = await db.execute(
        select(IprPlan)
        .options(selectinload(IprPlan.goals))
        .where(IprPlan.id == plan.id)
    )
    logger.info(
        "Manager %s created IPR plan %s for employee %s",
        current_user.email,
        plan.title,
        plan.employee_id,
    )
    return IprPlanOut.model_validate(result.scalar_one())


@router.get("/{plan_id}", response_model=IprPlanOut)
async def get_ipr_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get a single IPR plan with its goals."""
    result = await db.execute(
        select(IprPlan)
        .options(selectinload(IprPlan.goals))
        .where(IprPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="IPR plan not found"
        )

    if current_user.role not in ("admin", "manager") and str(current_user.id) != str(
        plan.employee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return IprPlanOut.model_validate(plan)


@router.patch("/{plan_id}", response_model=IprPlanOut)
async def update_ipr_plan(
    plan_id: str,
    body: IprPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Update an IPR plan (manager only)."""
    result = await db.execute(
        select(IprPlan)
        .options(selectinload(IprPlan.goals))
        .where(IprPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="IPR plan not found"
        )

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    await db.commit()
    await db.refresh(plan)

    result = await db.execute(
        select(IprPlan)
        .options(selectinload(IprPlan.goals))
        .where(IprPlan.id == plan.id)
    )
    return IprPlanOut.model_validate(result.scalar_one())


@router.post(
    "/{plan_id}/goals", response_model=IprGoalOut, status_code=status.HTTP_201_CREATED
)
async def add_ipr_goal(
    plan_id: str,
    body: IprGoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Add a goal to an IPR plan (manager only)."""
    result = await db.execute(select(IprPlan).where(IprPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="IPR plan not found"
        )

    goal = IprGoal(
        ipr_plan_id=plan.id,
        skill_id=body.skill_id,
        current_level=body.current_level,
        target_level=body.target_level,
        due_date=body.due_date,
        notes=body.notes,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    logger.info("Manager %s added goal to IPR plan %s", current_user.email, plan_id)
    return IprGoalOut.model_validate(goal)


@router.patch("/goals/{goal_id}", response_model=IprGoalOut)
async def update_ipr_goal(
    goal_id: str,
    body: IprGoalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Update an IPR goal (manager only)."""
    result = await db.execute(select(IprGoal).where(IprGoal.id == goal_id))
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found"
        )

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)

    await db.commit()
    await db.refresh(goal)
    return IprGoalOut.model_validate(goal)


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ipr_goal(
    goal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_manager_user),
):
    """Delete an IPR goal (manager only)."""
    result = await db.execute(select(IprGoal).where(IprGoal.id == goal_id))
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found"
        )

    await db.delete(goal)
    await db.commit()
    logger.info("Manager %s deleted goal %s", current_user.email, goal_id)
