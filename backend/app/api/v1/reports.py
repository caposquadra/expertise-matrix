import uuid
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Float, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_manager_user
from app.api.v1.constants import (
    ACTIVE_REVIEW_STATUSES,
    NEXT_GRADE,
    PROMOTION_THRESHOLD,
    REVIEW_STATUSES,
)
from app.core.database import get_db
from app.models import (
    Assessment,
    AssessmentHistory,
    Employee,
    EmployeeProfile,
    Skill,
    SkillGradeTarget,
    ReviewCycle,
    ReviewAssessment,
)
from app.schemas.report import (
    ComparisonCell,
    ComparisonRow,
    EmployeeCycleInfo,
    GradeDistributionItem,
    GrowthZoneOut,
    PromotionReadyOut,
    RecentChangeItem,
    RecentDecisionOut,
    ReviewCyclesSummaryOut,
    SkillAverageItem,
    SkillCoverageItem,
    StatusCountItem,
    TeamSummaryOut,
    WeakestSkillOut,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/team-summary", response_model=TeamSummaryOut)
async def team_summary(
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_manager_user),
):
    emp_result = await db.execute(
        select(Employee).where(Employee.is_active, Employee.role == "employee")
    )
    employees = emp_result.scalars().all()
    total = len(employees)

    grade_counts: dict[str, int] = {}
    for emp in employees:
        g = emp.grade or "unspecified"
        grade_counts[g] = grade_counts.get(g, 0) + 1
    grade_dist = [
        GradeDistributionItem(grade=g, count=c) for g, c in sorted(grade_counts.items())
    ]

    emp_ids = [e.id for e in employees]

    # Average levels (only employees)
    agg = await db.execute(
        select(
            cast(func.avg(Assessment.self_level), Float),
            cast(func.avg(Assessment.manager_level), Float),
        ).where(Assessment.employee_id.in_(emp_ids))
    )
    row = agg.one()
    avg_self = round(row[0], 2) if row[0] else None
    avg_mgr = round(row[1], 2) if row[1] else None

    # Skill coverage (single grouped query)
    skills_result = await db.execute(
        select(Skill).where(Skill.is_active).order_by(Skill.sort_order)
    )
    skills = skills_result.scalars().all()

    cov_counts: dict[uuid.UUID, int] = {}
    if emp_ids:
        cov_result = await db.execute(
            select(Assessment.skill_id, func.count(Assessment.id))
            .where(
                Assessment.employee_id.in_(emp_ids),
                Assessment.manager_level.isnot(None),
            )
            .group_by(Assessment.skill_id)
        )
        cov_counts = {row[0]: row[1] for row in cov_result.all()}

    coverage = []
    for skill in skills:
        cnt = cov_counts.get(skill.id, 0)
        coverage.append(
            SkillCoverageItem(
                skill_name=skill.name,
                category=skill.category,
                employees_with_assessment=cnt,
                total_employees=total,
                coverage_percent=round(cnt / total * 100, 1) if total else 0,
            )
        )

    return TeamSummaryOut(
        total_employees=total,
        grade_distribution=grade_dist,
        avg_self_level=avg_self,
        avg_manager_level=avg_mgr,
        skill_coverage=coverage,
    )


@router.get("/growth-zones", response_model=list[GrowthZoneOut])
async def growth_zones(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_manager_user),
):
    result = await db.execute(
        select(
            Skill.name,
            Skill.category,
            cast(func.avg(Assessment.self_level), Float),
            cast(func.avg(Assessment.manager_level), Float),
        )
        .join(Assessment, Assessment.skill_id == Skill.id)
        .join(Employee, Assessment.employee_id == Employee.id)
        .where(
            Skill.is_active,
            Employee.role == "employee",
            Assessment.self_level.isnot(None),
            Assessment.manager_level.isnot(None),
        )
        .group_by(Skill.id, Skill.name, Skill.category)
        .order_by(
            func.abs(
                func.avg(Assessment.self_level) - func.avg(Assessment.manager_level)
            ).desc()
        )
        .limit(limit)
    )
    zones = []
    for name, category, avg_self, avg_mgr in result.all():
        zones.append(
            GrowthZoneOut(
                skill_name=name,
                category=category,
                avg_self_level=round(avg_self, 2),
                avg_manager_level=round(avg_mgr, 2),
                avg_gap=round(abs(avg_self - avg_mgr), 2),
            )
        )
    return zones


@router.get("/comparison")
async def compare_employees(
    employee_ids: str,
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_manager_user),
):
    ids = [e.strip() for e in employee_ids.split(",")]
    if len(ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least 2 employee_ids",
        )

    emp_result = await db.execute(select(Employee).where(Employee.id.in_(ids)))
    employees = {str(e.id): e for e in emp_result.scalars().all()}

    skills_result = await db.execute(
        select(Skill).where(Skill.is_active).order_by(Skill.sort_order)
    )
    skills = skills_result.scalars().all()

    skill_ids = [s.id for s in skills]
    ass_result = await db.execute(
        select(Assessment).where(
            Assessment.skill_id.in_(skill_ids),
            Assessment.employee_id.in_(ids),
        )
    )
    all_assessments = ass_result.scalars().all()
    skill_ass_map: dict[uuid.UUID, dict[str, Assessment]] = defaultdict(dict)
    for a in all_assessments:
        skill_ass_map[a.skill_id][str(a.employee_id)] = a

    rows = []
    for skill in skills:
        ass_map = skill_ass_map.get(skill.id, {})
        cells = []
        for eid in ids:
            emp = employees.get(eid)
            if not emp:
                continue
            assessment = ass_map.get(eid)
            cells.append(
                ComparisonCell(
                    employee_name=emp.full_name,
                    employee_id=eid,
                    self_level=assessment.self_level if assessment else None,
                    manager_level=assessment.manager_level if assessment else None,
                )
            )

        rows.append(
            ComparisonRow(
                skill_name=skill.name,
                category=skill.category,
                cells=cells,
            )
        )

    return rows


@router.get("/skill-averages", response_model=list[SkillAverageItem])
async def skill_averages(
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_manager_user),
):
    result = await db.execute(
        select(
            Skill.category,
            cast(func.avg(Assessment.self_level), Float),
            cast(func.avg(Assessment.manager_level), Float),
        )
        .join(Assessment, Assessment.skill_id == Skill.id)
        .join(Employee, Assessment.employee_id == Employee.id)
        .where(Skill.is_active, Employee.role == "employee")
        .group_by(Skill.category)
        .order_by(Skill.category)
    )
    return [
        SkillAverageItem(
            category=cat, avg_self_level=round(s, 2), avg_manager_level=round(m, 2)
        )
        for cat, s, m in result.all()
    ]


@router.get("/recent-changes", response_model=list[RecentChangeItem])
async def recent_changes(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_manager_user),
):
    result = await db.execute(
        select(
            AssessmentHistory.id,
            AssessmentHistory.field_name,
            AssessmentHistory.old_value,
            AssessmentHistory.new_value,
            Employee.full_name,
            Skill.name,
            AssessmentHistory.changed_at,
        )
        .join(Assessment, AssessmentHistory.assessment_id == Assessment.id)
        .join(Employee, AssessmentHistory.changed_by == Employee.id)
        .join(Skill, Assessment.skill_id == Skill.id)
        .where(Employee.role == "employee")
        .order_by(AssessmentHistory.changed_at.desc())
        .limit(limit)
    )
    return [
        RecentChangeItem(
            id=row[0],
            field_name=row[1],
            old_value=row[2],
            new_value=row[3],
            employee_name=row[4],
            skill_name=row[5],
            changed_at=row[6],
        )
        for row in result.all()
    ]


@router.get("/review-cycles-summary", response_model=ReviewCyclesSummaryOut)
async def review_cycles_summary(
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_manager_user),
):
    result = await db.execute(
        select(ReviewCycle.status)
        .join(ReviewCycle.employee)
        .where(Employee.role == "employee")
    )
    all_statuses = result.scalars().all()
    counts = {s: all_statuses.count(s) for s in REVIEW_STATUSES}
    total_active = sum(counts.get(s, 0) for s in ACTIVE_REVIEW_STATUSES)

    profiles_result = await db.execute(select(EmployeeProfile))
    profile_grades = {
        str(p.employee_id): round(
            (
                p.experience
                + p.education
                + p.task_complexity
                + p.autonomy
                + p.communication
                + p.control
                + p.mentoring
                + p.responsibility
                + p.technical_competencies
            )
            / 9,
            1,
        )
        for p in profiles_result.scalars().all()
    }

    now = datetime.now(timezone.utc)
    without = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.employee))
        .join(ReviewCycle.employee)
        .where(ReviewCycle.status == "draft", Employee.role == "employee")
        .order_by(ReviewCycle.created_at)
    )
    draft_cycles = without.scalars().all()
    without_self = []
    if draft_cycles:
        draft_ids = [rc.id for rc in draft_cycles]
        ra_result = await db.execute(
            select(
                ReviewAssessment.review_cycle_id,
                func.count(ReviewAssessment.id),
            )
            .where(
                ReviewAssessment.review_cycle_id.in_(draft_ids),
                ReviewAssessment.self_level.isnot(None),
            )
            .group_by(ReviewAssessment.review_cycle_id)
        )
        ra_has_self = set(row[0] for row in ra_result.all())
    else:
        ra_has_self = set()

    for rc in draft_cycles:
        if rc.employee and rc.id not in ra_has_self:
            days = (now - rc.created_at).days if rc.created_at else 0
            without_self.append(
                EmployeeCycleInfo(
                    employee_name=rc.employee.full_name,
                    employee_id=str(rc.employee_id),
                    grade=rc.employee.grade,
                    profile_grade=profile_grades.get(str(rc.employee_id)),
                    cycle_id=str(rc.id),
                    status=rc.status,
                    days_in_status=days,
                )
            )

    # Employees with no review cycle at all
    has_cycle_subq = select(ReviewCycle.employee_id).distinct()
    no_cycle_emps = await db.execute(
        select(Employee)
        .where(
            Employee.role == "employee",
            Employee.is_active,
            Employee.id.notin_(has_cycle_subq),
        )
        .order_by(Employee.full_name)
    )
    for emp in no_cycle_emps.scalars().all():
        without_self.append(
            EmployeeCycleInfo(
                employee_name=emp.full_name,
                employee_id=str(emp.id),
                grade=emp.grade,
                profile_grade=profile_grades.get(str(emp.id)),
            )
        )

    # Employees grouped by status for the active cycles display
    all_cycles = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.employee))
        .join(ReviewCycle.employee)
        .where(Employee.role == "employee")
        .order_by(ReviewCycle.updated_at.desc())
    )
    status_employees: dict[str, list[EmployeeCycleInfo]] = {}
    for rc in all_cycles.scalars().all():
        if rc.employee:
            days = (now - rc.updated_at).days if rc.updated_at else 0
            status_employees.setdefault(rc.status, []).append(
                EmployeeCycleInfo(
                    employee_name=rc.employee.full_name,
                    employee_id=str(rc.employee_id),
                    grade=rc.employee.grade,
                    profile_grade=profile_grades.get(str(rc.employee_id)),
                    cycle_id=str(rc.id),
                    status=rc.status,
                    days_in_status=days,
                )
            )

    return ReviewCyclesSummaryOut(
        status_counts=[
            StatusCountItem(status=s, count=counts.get(s, 0)) for s in REVIEW_STATUSES
        ],
        total_active=total_active,
        employees_without_self_assessment=without_self,
        status_employees=status_employees,
    )


@router.get("/weakest-skills", response_model=list[WeakestSkillOut])
async def weakest_skills(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_manager_user),
):
    # Prefer review assessment data; fall back to Assessment if no review data exists
    review_result = await db.execute(
        select(
            Skill.name,
            Skill.category,
            cast(func.avg(ReviewAssessment.manager_level), Float),
            func.count(ReviewAssessment.id),
        )
        .join(ReviewAssessment, ReviewAssessment.skill_id == Skill.id)
        .join(ReviewCycle, ReviewAssessment.review_cycle_id == ReviewCycle.id)
        .join(Employee, ReviewCycle.employee_id == Employee.id)
        .where(
            Skill.is_active,
            Employee.role == "employee",
            ReviewAssessment.manager_level.isnot(None),
        )
        .group_by(Skill.id, Skill.name, Skill.category)
        .order_by(func.avg(ReviewAssessment.manager_level).asc())
        .limit(limit)
    )
    rows = review_result.all()
    if not rows:
        result = await db.execute(
            select(
                Skill.name,
                Skill.category,
                cast(func.avg(Assessment.manager_level), Float),
                func.count(Assessment.id),
            )
            .join(Assessment, Assessment.skill_id == Skill.id)
            .join(Employee, Assessment.employee_id == Employee.id)
            .where(
                Skill.is_active,
                Employee.role == "employee",
                Assessment.manager_level.isnot(None),
            )
            .group_by(Skill.id, Skill.name, Skill.category)
            .order_by(func.avg(Assessment.manager_level).asc())
            .limit(limit)
        )
        rows = result.all()
    return [
        WeakestSkillOut(
            skill_name=name,
            category=category,
            avg_manager_level=round(avg, 2),
            assessment_count=cnt,
        )
        for name, category, avg, cnt in rows
    ]


@router.get("/recent-decisions", response_model=list[RecentDecisionOut])
async def recent_decisions(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_manager_user),
):
    result = await db.execute(
        select(ReviewCycle)
        .options(selectinload(ReviewCycle.employee))
        .join(ReviewCycle.employee)
        .where(
            ReviewCycle.final_decision.isnot(None),
            Employee.role == "employee",
        )
        .order_by(ReviewCycle.updated_at.desc())
        .limit(limit)
    )
    cycles = result.scalars().all()
    out = []
    for rc in cycles:
        out.append(
            RecentDecisionOut(
                employee_name=rc.employee.full_name if rc.employee else "—",
                employee_id=str(rc.employee_id),
                decision=rc.final_decision or "",
                current_grade=rc.current_grade,
                target_grade=rc.target_grade,
                completed_at=rc.updated_at,
            )
        )
    return out


@router.get("/promotion-ready", response_model=list[PromotionReadyOut])
async def promotion_ready(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    _: Employee = Depends(get_manager_user),
):
    grade_targets_result = await db.execute(select(SkillGradeTarget))
    grade_targets = {
        (str(t.skill_id), t.grade): t.expected_level
        for t in grade_targets_result.scalars().all()
    }

    skill_result = await db.execute(select(Skill).where(Skill.is_active))
    all_skills = list(skill_result.scalars().all())
    skill_weights = {str(s.id): s.weight for s in all_skills}

    emp_result = await db.execute(
        select(Employee).where(
            Employee.is_active, Employee.role == "employee", Employee.grade.isnot(None)
        )
    )
    employees = emp_result.scalars().all()

    emp_ids = [e.id for e in employees]
    emp_assessments: dict[uuid.UUID, list[tuple]] = defaultdict(list)
    if emp_ids:
        ass_rows = await db.execute(
            select(
                Assessment.employee_id,
                Assessment.self_level,
                Assessment.manager_level,
                Skill.weight,
            )
            .join(Skill, Skill.id == Assessment.skill_id)
            .where(Assessment.employee_id.in_(emp_ids))
        )
        for eid, sl, ml, w in ass_rows.all():
            emp_assessments[eid].append((sl, ml, w))

    def compute_target(emp: Employee) -> float:
        next_grade = NEXT_GRADE.get(emp.grade.lower()) if emp.grade else None
        if next_grade is None:
            return 0.0
        total = 0.0
        for skill in all_skills:
            expected = grade_targets.get((str(skill.id), next_grade))
            if expected is not None:
                total += expected * skill_weights.get(str(skill.id), 1)
        return total

    def compute_score(emp: Employee) -> float:
        data = emp_assessments.get(emp.id, [])
        total = 0.0
        for sl, ml, w in data:
            effective = ml if ml is not None else sl
            if effective is not None:
                total += effective * w
        return total

    all_candidates = []
    for emp in employees:
        if emp.grade is None:
            continue
        total_mgr = compute_score(emp)
        if total_mgr == 0:
            continue
        target_score = compute_target(emp)
        if target_score == 0:
            continue
        if abs(total_mgr - target_score) / target_score <= PROMOTION_THRESHOLD:
            g = emp.grade.lower()
            all_candidates.append(
                PromotionReadyOut(
                    employee_name=emp.full_name,
                    employee_id=str(emp.id),
                    current_grade=emp.grade,
                    target_grade=NEXT_GRADE.get(g, g),
                    total_score=round(total_mgr, 2),
                    target_score=round(float(target_score), 2),
                )
            )

    if not all_candidates:
        for emp in employees:
            if emp.grade is None:
                continue
            total_mgr = compute_score(emp)
            if total_mgr > 0:
                target_score = compute_target(emp)
                if target_score == 0:
                    continue
                g = emp.grade.lower()
                all_candidates.append(
                    PromotionReadyOut(
                        employee_name=emp.full_name,
                        employee_id=str(emp.id),
                        current_grade=emp.grade,
                        target_grade=NEXT_GRADE.get(g, g),
                        total_score=round(total_mgr, 2),
                        target_score=round(float(target_score), 2),
                    )
                )

    return sorted(all_candidates, key=lambda x: x.total_score, reverse=True)[:limit]
