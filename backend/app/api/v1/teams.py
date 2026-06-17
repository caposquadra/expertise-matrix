import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_admin_user, get_current_user
from app.core.database import get_db
from app.models import Employee, Team

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamOut(BaseModel):
    id: str
    name: str
    description: str | None
    employee_count: int

    class Config:
        from_attributes = True


class TeamCreate(BaseModel):
    name: str
    description: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


@router.get("", response_model=list[TeamOut])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """List all teams."""
    result = await db.execute(
        select(Team).options(selectinload(Team.employees)).order_by(Team.name)
    )
    teams = result.scalars().all()
    out = []
    for t in teams:
        out.append(
            TeamOut(
                id=str(t.id),
                name=t.name,
                description=t.description,
                employee_count=len(t.employees),
            )
        )
    return out


@router.get("/{team_id}", response_model=TeamOut)
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Get a single team."""
    result = await db.execute(
        select(Team).options(selectinload(Team.employees)).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    return TeamOut(
        id=str(team.id),
        name=team.name,
        description=team.description,
        employee_count=len(team.employees),
    )


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
async def create_team(
    body: TeamCreate,
    db: AsyncSession = Depends(get_db),
    admin: Employee = Depends(get_admin_user),
):
    """Create a new team (admin only)."""
    team = Team(name=body.name, description=body.description)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    logger.info("Admin %s created team %s", admin.email, team.name)
    return TeamOut(
        id=str(team.id),
        name=team.name,
        description=team.description,
        employee_count=0,
    )


@router.patch("/{team_id}", response_model=TeamOut)
async def update_team(
    team_id: str,
    body: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Employee = Depends(get_admin_user),
):
    """Update a team (admin only)."""
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    await db.commit()
    await db.refresh(team)
    logger.info("Admin %s updated team %s", admin.email, team.name)
    return TeamOut(
        id=str(team.id),
        name=team.name,
        description=team.description,
        employee_count=len(team.employees),
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Employee = Depends(get_admin_user),
):
    """Delete a team (admin only)."""
    result = await db.execute(
        select(Team).options(selectinload(Team.employees)).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )

    if team.employees:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete team with active employees",
        )

    await db.delete(team)
    await db.commit()
    logger.info("Admin %s deleted team %s", admin.email, team.name)
